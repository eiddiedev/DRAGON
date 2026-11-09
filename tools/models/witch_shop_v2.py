# 用法：Blender --background --python witch_shop_v2.py -- <输出目录>
# 女巫药水铺 v2：向编辑器 AI 模型的画风靠拢。
# 规格照编辑器模型：一个主材质 + 一张烘好的底色贴图（颜色、块面渐变、缝隙暗部、边缘提亮都画进贴图）。
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

outdir = sys.argv[sys.argv.index('--') + 1]
os.makedirs(outdir, exist_ok=True)
rnd = random.Random(21)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.view_settings.view_transform = 'Standard'


def srgb(h):
    def f(c):
        c /= 255
        return c / 12.92 if c < .04045 else ((c + .055) / 1.055) ** 2.4
    return tuple(f(int(h[i:i + 2], 16)) for i in (1, 3, 5)) + (1.0,)


C = {k: srgb(v) for k, v in dict(
    plaster='#F2DFB4', plaster2='#E8CC96', stone='#B7B0AC', stone2='#928C94', stone3='#D4CCC0',
    wood='#8A5230', wood2='#B9743C', wood3='#6B3C24', roof='#7C4FC9', roof2='#6238AE', roof3='#9A6EE0',
    gold='#F5BE45', iron='#3C3A48', cloth='#E0584C', cloth2='#FBEFD2', floor='#B8813F', green='#7CC24A',
).items()}
GLOWS = dict(glass='#FFD36B', brew='#7CFFA0', p_red='#FF4F6A', p_blue='#55B4FF', p_white='#F2F7FF', p_pink='#FF8FDC', star='#FFE27A')


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
        scene.collection.objects.link(ob)
        return ob


R_IN, THICK, WALL_H = 4.0, .55, 5.6
R_OUT = R_IN + THICK
DOOR_W, DOOR_H = 2.3, 3.1
oy = -R_OUT

# ---------- 墙体：管状实体，门和窗是布尔挖出来的拱洞，所以真的是空心
M = Mesh()
prof_out = [(R_OUT + .28, 0), (R_OUT + .08, .7), (R_OUT, 1.6), (R_OUT - .05, 3.8), (R_OUT + .02, WALL_H)]
prof_in = [(R_IN, WALL_H), (R_IN, 0)]
vs = M.lathe(prof_out + prof_in, C['plaster'], seg=48, close=True)
wall = M.to_object('wall_raw')


def cutter(name, x, y, w, h, z0, a):
    obs = []
    for part in ('box', 'arc'):
        m = Mesh()
        if part == 'box':
            m.rbox((w, 2.6, h - w / 2), (0, 0, (h - w / 2) / 2), C['iron'], cuts=0)
        else:
            m.cyl(w / 2, w / 2, 2.6, (0, 0, h - w / 2), C['iron'], 24, (math.pi / 2, 0, 0))
        ob = m.to_object(name + part)
        ob.location = (x, y, z0)
        ob.rotation_euler = (0, 0, a)
        obs.append(ob)
    return obs


holes = cutter('c_door', 0, oy, DOOR_W, DOOR_H, -.1, 0)
win_angles = [math.radians(d) for d in (-20, 62, 118, 200)]
for i, a in enumerate(win_angles):
    holes += cutter(f'c_w{i}', math.cos(a) * R_OUT, math.sin(a) * R_OUT, 1.15, 1.9, 2.1, a + math.pi / 2)
for h in holes:
    b = wall.modifiers.new(h.name, 'BOOLEAN')
    b.object = h
    b.operation = 'DIFFERENCE'
    b.solver = 'EXACT'
bpy.context.view_layer.objects.active = wall
for mod in list(wall.modifiers):
    bpy.ops.object.modifier_apply(modifier=mod.name)
for h in holes:
    bpy.data.objects.remove(h)
wall.data.update()
print('WALL_FACES', len(wall.data.polygons))
print('DOOR_RAY', wall.ray_cast((0, -8, 1.5), (0, 1, 0)))

P = Mesh()  # 主体的其余部分
G = Mesh()  # 发光件，单独一个材质

# 墙根、门框周围的圆石头
for k in range(70):
    a = rnd.uniform(0, math.tau)
    z = rnd.choice((.25, .55, .95, 1.3)) + rnd.uniform(-.1, .1)
    if abs(math.atan2(math.sin(a + math.pi / 2), math.cos(a + math.pi / 2))) < .34:
        continue
    r = R_OUT + .14 - z * .06
    s = rnd.uniform(.5, 1.0)
    P.rbox((s * 1.0, .34, s * .55), (math.cos(a) * r, math.sin(a) * r, z), C[rnd.choice(('stone', 'stone2', 'stone3'))], (0, 0, a + math.pi / 2), jitter=.02)
# 拱形门框：一圈大石块
N = 11
for i in range(N):
    t = i / (N - 1) * math.pi
    rr = DOOR_W / 2 + .3
    x, z = -math.cos(t) * rr, DOOR_H - DOOR_W / 2 + math.sin(t) * rr
    P.rbox((.68, .95, .52), (x, oy + .05, z), C['stone3' if i % 2 else 'stone'], (0, -t + math.pi / 2, 0), jitter=.01)
for sx in (-1, 1):
    for i, z in enumerate((.3, .95, 1.55)):
        P.rbox((.78, .98, .62), (sx * (DOOR_W / 2 + .3), oy + .05, z), C['stone2' if i % 2 else 'stone'], jitter=.01)
# 半开的拱门板
door_a = math.radians(62)
dx0, dy0 = DOOR_W / 2, oy - .1
for i in range(5):
    w = DOOR_W / 5
    h = (DOOR_H - DOOR_W / 2) + math.sqrt(max(0, (DOOR_W / 2) ** 2 - (-DOOR_W / 2 + (i + .5) * w) ** 2)) - .1
    d = (i + .5) * w
    P.rbox((w * .96, .13, h), (dx0 + d * math.cos(door_a), dy0 - d * math.sin(door_a), h / 2 + .03), C['wood2' if i % 2 else 'wood'], (0, 0, -door_a))
for z in (.8, 2.3):
    d = DOOR_W / 2
    P.rbox((DOOR_W * .9, .17, .13), (dx0 + d * math.cos(door_a), dy0 - d * math.sin(door_a), z), C['iron'], (0, 0, -door_a))
# 窗框和窗格
for a in win_angles:
    rz = a + math.pi / 2
    r = R_OUT + .02
    cx, cy = math.cos(a) * r, math.sin(a) * r
    for sx in (-1, 1):
        ox, oy2 = math.cos(rz) * sx * .67, math.sin(rz) * sx * .67
        P.rbox((.2, .34, 1.45), (cx + ox, cy + oy2, 2.75), C['wood'], (0, 0, rz))
    P.rbox((1.55, .46, .2), (cx, cy, 2.04), C['wood2'], (0, 0, rz))
    P.rbox((.1, .14, 1.8), (cx - math.cos(a) * .1, cy - math.sin(a) * .1, 3.0), C['wood3'], (0, 0, rz))
    P.rbox((1.16, .14, .1), (cx - math.cos(a) * .1, cy - math.sin(a) * .1, 2.95), C['wood3'], (0, 0, rz))
# 檐下木带
P.lathe([(R_OUT + .2, WALL_H - .15), (R_OUT + .28, WALL_H + .05), (R_OUT + .2, WALL_H + .25), (R_IN, WALL_H + .25)], C['wood'], 40)
P.lathe([(R_IN + .02, WALL_H + .25), (.02, WALL_H + .25)], C['wood3'], 32)  # 天花板

# ---------- 歪尖帽屋顶：底下一层弯曲的壳，上面铺一片片圆瓦
BR = R_OUT + 1.35
RH = 10.0


def bend(z):
    t = max(0, (z - WALL_H) / RH)
    return (2.3 * t ** 2.6, 1.3 * t ** 2.6)


def roof_r(t):
    return BR * (1 - t) ** 1.45 + .06


prof = [(roof_r(i / 30), WALL_H + .1 + i / 30 * RH) for i in range(31)]
P.lathe([(BR + .06, WALL_H - .05)] + prof, C['roof'], 36, bend=bend)
for t, rr in ((.56, .05), (.7, .05), (.84, .04)):
    z = WALL_H + .1 + t * RH
    ox, oy2 = bend(z)
    P.lathe([(roof_r(t) + .02, z - .1), (roof_r(t) + rr, z), (roof_r(t) + .02, z + .1)], C['roof2'], 20, center=(ox, oy2))

rows = 15
for k in range(rows):
    t = k / rows
    if t > .40:  # 帽带以上是光滑的帽尖，卡通且省面
        break
    z = WALL_H + .1 + t * RH * .94
    r = roof_r(t) + .07
    ox, oy2 = bend(z)
    n = max(7, int(r * math.tau / 1.05))
    w = r * math.tau / n * 1.12
    slope = math.atan2(roof_r(t) - roof_r(t + .05), .05 * RH)
    for i in range(n):
        a = (i + (k % 2) * .5) / n * math.tau + rnd.uniform(-.015, .015)
        col = C[rnd.choice(('roof', 'roof', 'roof2', 'roof3'))]
        h = RH / rows * 1.45 * rnd.uniform(.94, 1.06)
        loc = (ox + math.cos(a) * r, oy2 + math.sin(a) * r, z + rnd.uniform(-.03, .03))
        P.rbox((w, .16, h), loc, col, Matrix.Rotation(a + math.pi / 2, 3, 'Z') @ Matrix.Rotation(-slope, 3, 'X'), cuts=1, taper=.92)
# 帽带与金扣
tb = .42
zb = WALL_H + .1 + tb * RH
ob, oby = bend(zb)
rb = roof_r(tb)
P.lathe([(rb + .32, zb - .42), (rb + .42, zb - .3), (rb + .32, zb + .3), (rb + .12, zb + .42)], C['iron'], 28, center=(ob, oby))
a = -math.pi / 2 + .25
P.rbox((1.0, .22, .9), (ob + math.cos(a) * (rb + .42), oby + math.sin(a) * (rb + .42), zb - .05), C['gold'], (0, 0, a + math.pi / 2))
P.rbox((.5, .3, .42), (ob + math.cos(a) * (rb + .46), oby + math.sin(a) * (rb + .46), zb - .05), C['iron'], (0, 0, a + math.pi / 2))
tx, ty = bend(WALL_H + .1 + RH)
G.sphere(.42, (tx + .14, ty + .08, WALL_H + 11.0), 'star', 12)
# 歪烟囱
for i, (ox, z) in enumerate(((0, WALL_H + 1.3), (.08, WALL_H + 2.2), (.2, WALL_H + 3.0))):
    P.rbox((1.25 - i * .08, 1.25 - i * .08, 1.1), (-3.2 + ox, 2.6, z), C['stone' if i % 2 else 'stone2'], (0, 0, .05 * i), jitter=.015)
P.rbox((1.6, 1.6, .32), (-3.0, 2.6, WALL_H + 3.7), C['iron'])
# 门灯
P.rbox((.1, .9, .1), (-(DOOR_W / 2 + .95), oy - .35, 3.55), C['iron'])
G.sphere(.32, (-(DOOR_W / 2 + .95), oy - .75, 3.15), 'glass', 12)
P.rbox((.5, .5, .1), (-(DOOR_W / 2 + .95), oy - .75, 3.5), C['iron'])

# ---------- 室内
P.lathe([(R_IN + .02, .14), (.02, .14)], C['floor'], 40)
for x in range(-4, 4):
    L = 2 * math.sqrt(max(.1, (R_IN - .05) ** 2 - (x + .5) ** 2))
    P.rbox((.93, L, .1), (x + .5, 0, .13), C[rnd.choice(('floor', 'wood2', 'floor'))], cuts=1)
for a in (0, math.pi / 2):
    P.rbox((R_IN * 2, .36, .36), (0, 0, WALL_H - .3), C['wood3'], (0, 0, a))
# 坩埚
P.cyl(1.2, 1.35, .3, (0, 1.0, .3), C['stone2'], 20)
P.sphere(1.0, (0, 1.0, 1.2), C['iron'], 18, (1, 1, .85))
P.lathe([(.98, 1.82), (1.08, 1.88), (1.04, 2.0), (.88, 1.92)], C['iron'], 22, center=(0, 1.0))
G.cyl(.92, .92, .05, (0, 1.0, 1.9), 'brew', 22)
for dx, dz in ((-.35, 2.2), (.3, 2.6), (.05, 3.05)):
    G.sphere(.16, (dx, 1.0, dz), 'brew', 8)
for a in range(3):
    t = a / 3 * math.tau
    P.rbox((.22, .22, .7), (math.cos(t) * .72, 1.0 + math.sin(t) * .72, .4), C['iron'])
# 北墙药水架
for z in (1.3, 2.3, 3.3):
    P.rbox((4.4, .65, .14), (0, R_IN - .55, z), C['wood2'])
for sx in (-2.25, 2.25):
    P.rbox((.2, .68, 3.4), (sx, R_IN - .55, 1.9), C['wood'])
names = ['p_red', 'p_blue', 'p_white', 'p_pink', 'brew']
for z in (1.3, 2.3, 3.3):
    for i in range(6):
        x = -1.65 + i * .66
        c_ = rnd.choice(names)
        s = rnd.uniform(.14, .2)
        G.sphere(s, (x, R_IN - .55, z + .07 + s), c_, 8)
        P.cyl(.06, .05, .16, (x, R_IN - .55, z + .07 + s * 2 + .05), C['wood2'], 6)
# 西墙书桌和书
P.rbox((1.1, 2.5, .16), (-R_IN + 1.0, -.2, 1.1), C['wood2'])
for y in (-1.2, .8):
    P.rbox((.22, .22, 1.05), (-R_IN + 1.0, y, .58), C['wood'])
for i, (y, z, rz) in enumerate(((-.7, 1.28, .3), (.2, 1.26, -.2), (-.2, 2.1, .8))):
    P.rbox((.62, .46, .13), (-R_IN + 1.05, y, z), C[['cloth', 'roof', 'gold'][i]], (.25 if i == 2 else 0, 0, rz), cuts=1)

# ---------- 东侧药水摊
SX = R_OUT + 2.3
P.rbox((3.6, 1.5, .2), (SX, -2.4, 1.2), C['wood2'])
P.rbox((3.3, 1.25, 1.1), (SX, -2.4, .58), C['wood'])
for x in (-1.1, 0, 1.1):
    P.rbox((.14, 1.32, 1.0), (SX + x, -2.4, .58), C['wood3'])
for sx in (-1.75, 1.75):
    P.rbox((.24, .24, 3.2), (SX + sx, -3.1, 1.6), C['wood'])
    P.rbox((.24, .24, 3.7), (SX + sx, -1.7, 1.85), C['wood'])
for i in range(7):
    w = 4.2 / 7
    x = SX - 2.1 + w * (i + .5)
    c_ = C['cloth'] if i % 2 else C['cloth2']
    P.rbox((w * 1.0, 1.95, .13), (x, -2.4, 3.35), c_, (math.radians(16), 0, 0))
    P.sphere(w * .5, (x, -3.33, 3.09), c_, 10, (1, .24, .55))  # 荷叶边
for i, c_ in enumerate(('p_red', 'p_blue', 'p_white', 'p_pink')):
    x = SX - 1.15 + i * .77
    P.cyl(.28, .3, .08, (x, -2.5, 1.33), C['gold'], 12)
    G.sphere(.22, (x, -2.5, 1.59), c_, 12)
    G.cyl(.08, .07, .2, (x, -2.5, 1.85), c_, 8)
    P.cyl(.09, .08, .1, (x, -2.5, 1.98), C['wood2'], 8)

main = P.to_object('main')
bpy.ops.object.select_all(action='DESELECT')
wall.select_set(True)
main.select_set(True)
bpy.context.view_layer.objects.active = main
bpy.ops.object.join()
main.data.polygons.foreach_set('use_smooth', [True] * len(main.data.polygons))
main.data.set_sharp_from_angle(angle=math.radians(38))
main.data.update()

# ---------- 把颜色、渐变、缝隙、边缘提亮烘成一张贴图
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
scale_w.inputs[1].default_value = .55
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

img = bpy.data.images.new('witch_shop_albedo', 2048, 2048)
tex = nodes.new('ShaderNodeTexImage')
tex.image = img
nodes.active = tex
main.data.materials.clear()
main.data.materials.append(paint)

bpy.context.view_layer.objects.active = main
main.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=math.radians(50), island_margin=.003)
bpy.ops.object.mode_set(mode='OBJECT')
scene.cycles.samples = 24
scene.cycles.bake_type = 'EMIT'
bpy.ops.object.bake(type='EMIT', margin=8, use_clear=True)
img.filepath_raw = os.path.join(outdir, 'witch_shop_v2_albedo.png')
img.file_format = 'PNG'
img.save()

# 换成导出用的材质
final = bpy.data.materials.new('witch_shop_paint')
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

# ---------- 发光件
glows = {k: bpy.data.materials.new(k) for k in GLOWS}
for k, m in glows.items():
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    c = srgb(GLOWS[k])
    b.inputs['Base Color'].default_value = c
    b.inputs['Emission Color'].default_value = c
    b.inputs['Emission Strength'].default_value = 1.4
# 窗玻璃
for a in win_angles:
    r = R_OUT - .25
    G.rbox((1.1, .08, 1.85), (math.cos(a) * r, math.sin(a) * r, 3.0), 'glass', (0, 0, a + math.pi / 2), cuts=0)
glow_ob = G.to_object('glow')
for k in GLOWS:
    glow_ob.data.materials.append(glows[k])
glow_ob.data.polygons.foreach_set('use_smooth', [True] * len(glow_ob.data.polygons))
glow_ob.data.update()
while glow_ob.data.color_attributes:
    glow_ob.data.color_attributes.remove(glow_ob.data.color_attributes[0])

tris = 0
for o in (main, glow_ob):
    o.data.calc_loop_triangles()
    tris += len(o.data.loop_triangles)
print('TRIANGLES', tris)
bpy.ops.object.select_all(action='DESELECT')
main.select_set(True)
glow_ob.select_set(True)
path = os.path.join(outdir, 'witch_shop_v2.glb')
bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                          export_image_format='JPEG', export_jpeg_quality=88)
print('GLB_MB', round(os.path.getsize(path) / 1e6, 2))

# ---------- 预览：用接近编辑器的明亮漫射光
scene.cycles.samples = 48
scene.render.resolution_x, scene.render.resolution_y = 1000, 800
gm = bmesh.new()
bmesh.ops.create_grid(gm, x_segments=1, y_segments=1, size=80)
gme = bpy.data.meshes.new('g')
gm.to_mesh(gme)
gm.free()
go = bpy.data.objects.new('ground', gme)
gmat = bpy.data.materials.new('grass')
gmat.use_nodes = True
gmat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = srgb('#86B84E')
gme.materials.append(gmat)
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


def shot(fn, loc, target, lens=38):
    cam.data.lens = lens
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(outdir, fn)
    bpy.ops.render.render(write_still=True)


shot('witch_shop_v2_front.png', (11, -25, 7.5), (1.2, 0, 7))
shot('witch_shop_v2_door.png', (3.2, -13, 2.2), (.6, -2, 2.5), 30)
