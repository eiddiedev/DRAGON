# 龙眠之境统一画风工具包：所有静态建筑都走这里，保证配色、零件、贴图绘制方式一致。
# 规格对照编辑器 AI 模型：一个主材质 + 一张烘好的底色贴图；发光件单独一个材质。
import math
import os
import random

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

rnd = random.Random(21)
GLOWS = dict(glass='#FFD36B', brew='#7CFFA0', p_red='#FF4F6A', p_blue='#55B4FF', p_white='#F2F7FF', p_pink='#FF8FDC', star='#FFE27A', leaf1='#FFF3B8', leaf2='#FFFBE3', leaf3='#FFE89A')


def reset():
    global scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.view_settings.view_transform = 'Standard'
    return scene


def srgb(h):
    def f(c):
        c /= 255
        return c / 12.92 if c < .04045 else ((c + .055) / 1.055) ** 2.4
    return tuple(f(int(h[i:i + 2], 16)) for i in (1, 3, 5)) + (1.0,)


C = {k: srgb(v) for k, v in dict(
    roof_red='#D9553B', roof_red2='#BF4430', roof_red3='#EA7350', beam='#6B3F27',
    plaster='#F2DFB4', plaster2='#E8CC96', stone='#B7B0AC', stone2='#928C94', stone3='#D4CCC0',
    wood='#8A5230', wood2='#B9743C', wood3='#6B3C24', roof='#7C4FC9', roof2='#6238AE', roof3='#9A6EE0',
    gold='#F5BE45', iron='#3C3A48', cloth='#E0584C', cloth2='#FBEFD2', floor='#B8813F', green='#7CC24A',
).items()}


def _island(start):
    out, stack = [], [start]
    start.tag = True
    while stack:
        v = stack.pop()
        out.append(v)
        for e in v.link_edges:
            o = e.other_vert(v)
            if not o.tag:
                o.tag = True
                stack.append(o)
    for v in out:
        v.tag = False
    return out


class Mesh:
    def __init__(self):
        self.bm = bmesh.new()
        self.col = self.bm.loops.layers.color.new('Col')

    def paint(self, verts, c):
        for f in {f for v in verts for f in v.link_faces}:
            if isinstance(c, str):  # 发光件：c 是材质名
                f.material_index = list(GLOWS).index(c)
                continue
            for l in f.loops:
                l[self.col] = c

    def rbox(self, size, loc, c, rot=(0, 0, 0), cuts=1, taper=1.0, jitter=0.0):
        """圆角块：所有东西都用它，就不会出现硬方块。"""
        vs = bmesh.ops.create_cube(self.bm, size=1)['verts']
        if cuts:
            edges = list({e for v in vs for e in v.link_edges})
            r = bmesh.ops.subdivide_edges(self.bm, edges=edges, cuts=cuts, use_grid_fill=True, smooth=.0)
            vs = [g for g in r['geom'] if isinstance(g, bmesh.types.BMVert)]
        vs = _island(vs[0])  # 沿边走一遍拿到全部顶点；bmesh 内存池会复用空位，不能按下标切
        R = rot if isinstance(rot, Matrix) else Euler(rot).to_matrix()
        m = max(size)
        half = Vector(size) / 2
        rad = min(min(size) * .45, .35) if cuts else 0
        inner = Vector((half.x - rad, half.y - rad, half.z - rad))
        for v in vs:
            p = v.co * 2  # -1..1
            w = Vector((p.x * half.x, p.y * half.y, p.z * half.z))
            cl = Vector((max(-inner.x, min(inner.x, w.x)), max(-inner.y, min(inner.y, w.y)), max(-inner.z, min(inner.z, w.z))))
            d = w - cl
            if rad and d.length > 1e-6:
                w = cl + d.normalized() * rad
            if p.z > 0 and taper != 1.0:
                w.x *= taper
                w.y *= taper
            if jitter:
                w += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * jitter * max(size)
            v.co = R @ w + Vector(loc)
        self.paint(vs, c)

    def lathe(self, prof, c, seg=32, center=(0, 0), bend=None, close=False):
        """prof: [(半径, 高度)...]，bend: 按高度返回水平偏移的函数。"""
        rows = []
        for r, z in prof:
            ox, oy = bend(z) if bend else (0, 0)
            rows.append([self.bm.verts.new((center[0] + ox + math.cos(i / seg * math.tau) * r, center[1] + oy + math.sin(i / seg * math.tau) * r, z)) for i in range(seg)])
        faces = []
        for a, b in zip(rows, rows[1:] + (rows[:1] if close else [])):
            for i in range(seg):
                faces.append(self.bm.faces.new((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i])))
        vs = [v for r in rows for v in r]
        self.paint(vs, c)
        return vs

    def prism(self, w, y0, y1, z0, rise, c, cx=0.0):
        """三角形山墙：底宽 w，立在 z0，高 rise，沿 Y 有厚度。"""
        pts = [(cx - w / 2, z0), (cx + w / 2, z0), (cx, z0 + rise)]
        f = [self.bm.verts.new((x, y0, z)) for x, z in pts]
        k = [self.bm.verts.new((x, y1, z)) for x, z in pts]
        self.bm.faces.new(f)
        self.bm.faces.new(k[::-1])
        for i in range(3):
            j = (i + 1) % 3
            self.bm.faces.new((f[i], k[i], k[j], f[j]))
        self.paint(f + k, c)

    def tube(self, pts, radii, c, seg=10, flat=1.0, c_fn=None):
        """沿折线扫出一条圆管（龙身）。pts 是世界点，radii 每点半径；flat<1 压扁竖直方向。"""
        rings = []
        n = len(pts)
        for i, p in enumerate(pts):
            p = Vector(p)
            t = (Vector(pts[min(i + 1, n - 1)]) - Vector(pts[max(i - 1, 0)])).normalized()
            side = t.cross(Vector((0, 0, 1)))
            if side.length < 1e-3:
                side = Vector((1, 0, 0))
            side.normalize()
            up = side.cross(t).normalized()
            ring = []
            for s in range(seg):
                a_ = s / seg * math.tau
                ring.append(self.bm.verts.new(p + side * math.cos(a_) * radii[i] + up * math.sin(a_) * radii[i] * flat))
            rings.append(ring)
        for i, (r0, r1) in enumerate(zip(rings, rings[1:])):
            for s in range(seg):
                f = self.bm.faces.new((r0[s], r0[(s + 1) % seg], r1[(s + 1) % seg], r1[s]))
                col = c_fn(i, s) if c_fn else c
                for l in f.loops:
                    l[self.col] = col
        self.bm.faces.new(rings[0])
        self.bm.faces.new(rings[-1][::-1])
        for f in (self.bm.faces[-1], self.bm.faces[-2]) if False else ():
            pass

    def sphere(self, r, loc, c, seg=12, scale=(1, 1, 1)):
        vs = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=max(6, seg // 2 + 2), radius=r)['verts']
        for v in vs:
            v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2])) + Vector(loc)
        self.paint(vs, c)

    def cyl(self, r1, r2, h, loc, c, seg=16, rot=(0, 0, 0), caps=True):
        vs = bmesh.ops.create_cone(self.bm, cap_ends=caps, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=h)['verts']
        R = Euler(rot).to_matrix()
        for v in vs:
            v.co = R @ v.co + Vector(loc)
        self.paint(vs, c)

    def to_object(self, name):
        me = bpy.data.meshes.new(name)
        self.bm.normal_update()
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        self.bm.to_mesh(me)
        self.bm.free()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob


def cut(target, cutters):
    """布尔挖洞并移除挖刀。"""
    for h in cutters:
        b = target.modifiers.new(h.name, 'BOOLEAN')
        b.object = h
        b.operation = 'DIFFERENCE'
        b.solver = 'EXACT'
    bpy.context.view_layer.objects.active = target
    for mod in list(target.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    for h in cutters:
        bpy.data.objects.remove(h)
    target.data.update()


def arch_cutter(x, y, w, h, z0, a, depth=3.0, name='c'):
    obs = []
    for part in ('box', 'arc'):
        m = Mesh()
        if part == 'box':
            m.rbox((w, depth, h - w / 2), (0, 0, (h - w / 2) / 2), C['iron'], cuts=0)
        else:
            m.cyl(w / 2, w / 2, depth, (0, 0, h - w / 2), C['iron'], 20, (math.pi / 2, 0, 0))
        ob = m.to_object(name + part)
        ob.location = (x, y, z0)
        ob.rotation_euler = (0, 0, a)
        obs.append(ob)
    return obs


def finish(main_objs, glow_mesh, name, outdir, tex_size=1024):
    """合并、烘贴图、导出 GLB。返回 (main, glow) 供预览。"""
    os.makedirs(outdir, exist_ok=True)
    scene = bpy.context.scene
    bpy.ops.object.select_all(action='DESELECT')
    for o in main_objs:
        o.select_set(True)
    main = main_objs[0]
    bpy.context.view_layer.objects.active = main
    bpy.ops.object.join()
    main.data.polygons.foreach_set('use_smooth', [True] * len(main.data.polygons))
    main.data.set_sharp_from_angle(angle=math.radians(38))
    main.data.update()

    paint = bpy.data.materials.new('paint')
    paint.use_nodes = True
    nt = paint.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    em = nodes.new('ShaderNodeEmission')
    attr = nodes.new('ShaderNodeVertexColor')
    attr.layer_name = 'Col'
    geo = nodes.new('ShaderNodeNewGeometry')
    ao_w = nodes.new('ShaderNodeAmbientOcclusion')
    ao_w.inputs['Distance'].default_value = 1.6
    ao_w.samples = 16
    ao_n = nodes.new('ShaderNodeAmbientOcclusion')
    ao_n.inputs['Distance'].default_value = .22
    ao_n.samples = 16
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = .9
    noise.inputs['Detail'].default_value = 4
    crest = nodes.new('ShaderNodeValToRGB')
    crest.color_ramp.elements[0].position = .52
    crest.color_ramp.elements[1].position = .62
    blotch = nodes.new('ShaderNodeValToRGB')
    blotch.color_ramp.elements[0].position = .3
    blotch.color_ramp.elements[0].color = (.88, .86, .92, 1)
    blotch.color_ramp.elements[1].position = .72
    blotch.color_ramp.elements[1].color = (1.1, 1.07, 1.0, 1)
    m1 = nodes.new('ShaderNodeMix')  # 斑驳
    m1.data_type = 'RGBA'
    m1.blend_type = 'MULTIPLY'
    m1.inputs[0].default_value = 1
    m2 = nodes.new('ShaderNodeMix')  # 大范围 AO，暗部偏紫不偏黑
    m2.data_type = 'RGBA'
    m2.blend_type = 'MULTIPLY'
    m3 = nodes.new('ShaderNodeMix')  # 缝隙线
    m3.data_type = 'RGBA'
    m3.blend_type = 'MULTIPLY'
    m4 = nodes.new('ShaderNodeMix')  # 边缘提亮
    m4.data_type = 'RGBA'
    m4.blend_type = 'SCREEN'
    inv_w = nodes.new('ShaderNodeMath')
    inv_w.operation = 'SUBTRACT'
    inv_w.inputs[0].default_value = 1
    inv_n = nodes.new('ShaderNodeMath')
    inv_n.operation = 'SUBTRACT'
    inv_n.inputs[0].default_value = 1
    scale_w = nodes.new('ShaderNodeMath')
    scale_w.operation = 'MULTIPLY'
    scale_w.inputs[1].default_value = .38
    scale_n = nodes.new('ShaderNodeMath')
    scale_n.operation = 'MULTIPLY'
    scale_n.inputs[1].default_value = .8
    scale_e = nodes.new('ShaderNodeMath')
    scale_e.operation = 'MULTIPLY'
    scale_e.inputs[1].default_value = .10
    links.new(noise.outputs['Fac'], blotch.inputs['Fac'])
    links.new(attr.outputs['Color'], m1.inputs[6])
    links.new(blotch.outputs['Color'], m1.inputs[7])
    links.new(ao_w.outputs['AO'], inv_w.inputs[1])
    links.new(inv_w.outputs[0], scale_w.inputs[0])
    links.new(scale_w.outputs[0], m2.inputs[0])
    links.new(m1.outputs[2], m2.inputs[6])
    m2.inputs[7].default_value = (.60, .46, .62, 1)
    links.new(ao_n.outputs['AO'], inv_n.inputs[1])
    links.new(inv_n.outputs[0], scale_n.inputs[0])
    links.new(scale_n.outputs[0], m3.inputs[0])
    links.new(m2.outputs[2], m3.inputs[6])
    m3.inputs[7].default_value = (.42, .28, .32, 1)
    links.new(geo.outputs['Pointiness'], crest.inputs['Fac'])
    links.new(crest.outputs['Color'], scale_e.inputs[0])
    links.new(scale_e.outputs[0], m4.inputs[0])
    links.new(m3.outputs[2], m4.inputs[6])
    m4.inputs[7].default_value = (1, .96, .85, 1)
    links.new(m4.outputs[2], em.inputs['Color'])
    links.new(em.outputs[0], out.inputs['Surface'])

    img = bpy.data.images.new(name + '_albedo', tex_size, tex_size)
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = img
    nodes.active = tex
    main.data.materials.clear()
    main.data.materials.append(paint)
    bpy.ops.object.select_all(action='DESELECT')
    main.select_set(True)
    bpy.context.view_layer.objects.active = main
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=.003)
    bpy.ops.object.mode_set(mode='OBJECT')
    scene.cycles.samples = 24
    scene.cycles.bake_type = 'EMIT'
    bpy.ops.object.bake(type='EMIT', margin=6, use_clear=True)
    final = bpy.data.materials.new(name + '_paint')
    final.use_nodes = True
    pb = final.node_tree.nodes['Principled BSDF']
    pb.inputs['Roughness'].default_value = .9
    t2 = final.node_tree.nodes.new('ShaderNodeTexImage')
    t2.image = img
    final.node_tree.links.new(t2.outputs['Color'], pb.inputs['Base Color'])
    main.data.materials.clear()
    main.data.materials.append(final)
    while main.data.color_attributes:
        main.data.color_attributes.remove(main.data.color_attributes[0])
    objs = [main]
    glow_ob = None
    if glow_mesh is not None and len(glow_mesh.bm.verts):
        glow_ob = glow_mesh.to_object('glow')
        for k, hexv in GLOWS.items():
            m = bpy.data.materials.new(k)
            m.use_nodes = True
            b = m.node_tree.nodes['Principled BSDF']
            c = srgb(hexv)
            b.inputs['Base Color'].default_value = c
            b.inputs['Emission Color'].default_value = c
            b.inputs['Emission Strength'].default_value = 1.4
            glow_ob.data.materials.append(m)
        glow_ob.data.polygons.foreach_set('use_smooth', [True] * len(glow_ob.data.polygons))
        glow_ob.data.update()
        while glow_ob.data.color_attributes:
            glow_ob.data.color_attributes.remove(glow_ob.data.color_attributes[0])
        objs.append(glow_ob)
    tris = 0
    for o in objs:
        o.data.calc_loop_triangles()
        tris += len(o.data.loop_triangles)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    path = os.path.join(outdir, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                              export_image_format='JPEG', export_jpeg_quality=88)
    print('BUILT', name, 'tris', tris, 'MB', round(os.path.getsize(path) / 1e6, 2))
    return objs


def preview_setup():
    scene = bpy.context.scene
    scene.cycles.samples = 40
    gm = bmesh.new()
    bmesh.ops.create_grid(gm, x_segments=1, y_segments=1, size=120)
    me = bpy.data.meshes.new('g')
    gm.to_mesh(me)
    gm.free()
    go = bpy.data.objects.new('ground', me)
    mt = bpy.data.materials.new('grass')
    mt.use_nodes = True
    mt.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = srgb('#86B84E')
    me.materials.append(mt)
    scene.collection.objects.link(go)
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 2.2
    sun.data.color = (1, .94, .84)
    sun.data.angle = math.radians(5)
    sun.rotation_euler = Euler((math.radians(52), 0, math.radians(-35)))
    scene.collection.objects.link(sun)
    w = bpy.data.worlds.new('w')
    w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = srgb('#BFDDF5')
    w.node_tree.nodes['Background'].inputs[1].default_value = .75
    scene.world = w
    cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    return cam


def shot(cam, path, loc, target, lens=38, res=(1000, 700)):
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = res
    cam.data.lens = lens
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
