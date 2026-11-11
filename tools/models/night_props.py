# 用法：Blender --background --python night_props.py -- <输出目录> [部件名...]
# 氛围道具：发光圣树、花海、山路路灯、森林、墓园、时之晷。
# 除圣树和时之晷外，都用世界坐标建在一个模型里（原点 128,128，高度用绝对海拔），一个模型摆一次就全到位。
# 高度读 assets/terrain/world/base_heights.npy。写 placements.json。
import json
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
from kit import C, Mesh, finish, preview_setup, shot, srgb
from mathutils import Vector

args = sys.argv[sys.argv.index('--') + 1:]
outdir = args[0]
only = set(args[1:])
os.makedirs(outdir, exist_ok=True)
ROOT = '/Users/bytedance/Documents/ChatGPT/DRAGON/assets'
H = np.load(f'{ROOT}/terrain/world/base_heights.npy')
PATH = json.load(open(f'{ROOT}/terrain/world/path.json'))
SEA = 27.0
OX, OY = 128.0, 128.0
TREE = (153.0, 71.0)
SPAWN = (130.0, 48.0)
PLACE = os.path.join(outdir, 'placements.json')
placements = {p['name']: p for p in json.load(open(PLACE))} if os.path.exists(PLACE) else {}
C.update({k: srgb(v) for k, v in dict(
    bark='#3B2A28', bark2='#513A33', bark3='#2A1F20', root='#463230',
    pine='#1B4A2A', pine2='#256035', pine3='#123A20', dead='#2B2426', dead2='#3A2F30',
    grave='#6E6C72', grave2='#85838A', grave3='#55535A', pump='#D66A1F', pump2='#B5531A', stem='#3E5A26',
    lamp='#262430', lamp2='#3A3744', wst='#BFB6A6',
).items()})
RIVER = [(77, 253), (77, 236), (80, 219), (74, 192), (79, 173), (88, 152), (98, 136), (108, 124), (125, 116), (141, 118), (154, 110), (168, 110), (187, 103)]


def G(x, y):
    x = min(max(x, 0), 255.99)
    y = min(max(y, 0), 255.99)
    x0, y0 = int(x), int(y)
    fx, fy = x - x0, y - y0
    return float(H[y0, x0] * (1 - fx) * (1 - fy) + H[y0, x0 + 1] * fx * (1 - fy) + H[y0 + 1, x0] * (1 - fx) * fy + H[y0 + 1, x0 + 1] * fx * fy)


def slope(x, y):
    return math.degrees(math.atan(math.hypot(G(x + 1, y) - G(x - 1, y), G(x, y + 1) - G(x, y - 1)) / 2))


def seg_dist(x, y, pts):
    best = 1e9
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        dx, dy = bx - ax, by - ay
        t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy + 1e-9)))
        best = min(best, math.hypot(x - ax - t * dx, y - ay - t * dy))
    return best


ROADS = [[(p[0], p[1]) for p in PATH[::3]], [(130, 52), (135, 66), (149, 79), (159, 90), (162, 96)], [(162, 127), (167, 134), (171, 141)]]


def road_dist(x, y):
    return min(seg_dist(x, y, r) for r in ROADS)


def place(name, x, y, z):
    placements[name] = dict(name=name, x=float(x), y=float(y), z=float(z))


def diamond(mesh, center, u, v, c):
    """一片菱形叶子：两个三角形。"""
    p = Vector(center)
    vs = [mesh.bm.verts.new(p + u), mesh.bm.verts.new(p + v), mesh.bm.verts.new(p - u), mesh.bm.verts.new(p - v)]
    mesh.bm.faces.new(vs)
    mesh.paint(vs, c)


def holy_tree():
    """原创的发光大树：弯曲的深色主干，宽展的树冠，垂下成串的金白光叶。"""
    kit.reset()
    rnd = random.Random(508)
    P, Gl = Mesh(), Mesh()
    ends = []

    def limb(start, direction, length, radius, depth):
        pts, radii = [Vector(start)], [radius]
        d = Vector(direction).normalized()
        n = 6 if depth == 0 else 4
        for i in range(n):
            d = (d + Vector((rnd.uniform(-.28, .28), rnd.uniform(-.28, .28), rnd.uniform(-.1, .12)))).normalized()
            pts.append(pts[-1] + d * length / n)
            radii.append(radius * (1 - (i + 1) / n * .62))
        P.tube([tuple(p) for p in pts], radii, C[rnd.choice(('bark', 'bark2'))], seg=(8 if depth <= 1 else 4))
        if depth < 3:
            for k in range(3 if depth < 2 else 2):
                o = rnd.randint(n // 2, n)
                a = rnd.uniform(0, math.tau)
                sideways = Vector((math.cos(a), math.sin(a), rnd.uniform(.05, .45)))
                nd = (d * .55 + sideways).normalized()
                limb(pts[o], nd, length * rnd.uniform(.5, .7), radii[o] * .72, depth + 1)
        else:
            ends.append(pts[-1])

    # 主干：下粗上细，略微扭转
    trunk_pts, trunk_r = [], []
    for i in range(9):
        t = i / 8
        ang = t * 1.2
        trunk_pts.append((math.cos(ang) * t * 1.3, math.sin(ang) * t * 1.3, t * 13.5 - .8))
        trunk_r.append(3.0 * (1 - t) ** 1.7 + 1.25)
    P.tube(trunk_pts, trunk_r, C['bark'], seg=14)
    # 树根，抓着地面
    for i in range(9):
        a = i / 9 * math.tau + rnd.uniform(-.2, .2)
        L = rnd.uniform(4.5, 7.5)
        pts = [(math.cos(a) * 1.8, math.sin(a) * 1.8, 2.2), (math.cos(a) * L * .45, math.sin(a) * L * .45, .75), (math.cos(a + .2) * L, math.sin(a + .2) * L, -.5)]
        P.tube(pts, [1.0, .62, .18], C['root'], seg=6)
    # 树干上发光的纹路
    for k in range(5):
        pts, radii = [], []
        ph = k / 5 * math.tau
        for i in range(10):
            t = i / 9
            ang = t * 1.2 + ph + t * 2.2
            cx, cy = math.cos(t * 1.2) * t * 1.3, math.sin(t * 1.2) * t * 1.3
            rr = (3.0 * (1 - t) ** 1.7 + 1.25) * 1.03
            pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr, t * 12.5))
            radii.append(.035 + .03 * math.sin(t * 3.1))
        Gl.tube(pts, radii, C['iron'], seg=3)
    # 把树干纹路都设成发光材质（tube 不走 paint）
    Gl.bm.faces.ensure_lookup_table()
    for f in Gl.bm.faces:
        f.material_index = list(kit.GLOWS).index('leaf1')
    top = Vector(trunk_pts[-1])
    for i in range(6):
        a = i / 6 * math.tau + rnd.uniform(-.25, .25)
        limb(top, (math.cos(a), math.sin(a), rnd.uniform(.6, 1.0)), rnd.uniform(8.5, 11), 1.05, 1)
    print('branch ends', len(ends))
    # 树冠：一团团蓬松的光云，外面再撒双面碎叶，不留空洞
    tones = ('leaf1', 'leaf1', 'leaf2', 'leaf3')

    def leaf(c, s, tone):
        u = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-.5, .5))).normalized() * s
        v = u.cross(Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)))).normalized() * s * .62
        diamond(Gl, c, u, v, tone)
        diamond(Gl, c, v, u, tone)  # 反面

    for e in ends:
        for _ in range(60):
            off = Vector((rnd.gauss(0, 2.3), rnd.gauss(0, 2.3), rnd.gauss(0, 1.25)))
            leaf(e + off, rnd.uniform(.2, .4), rnd.choice(tones))
    # 垂下来的光叶串
    for e in rnd.sample(ends, min(len(ends), 30)):
        L = rnd.uniform(3.5, 8)
        n = int(L / .42)
        ox, oy = rnd.uniform(-2.2, 2.2), rnd.uniform(-2.2, 2.2)
        for i in range(n):
            t = i / n
            c = e + Vector((ox + math.sin(t * 2.4) * .3, oy, -t * L))
            leaf(c, .2 * (1 - t * .45), 'leaf2' if i % 3 == 0 else 'leaf1')
    json.dump([list(e) for e in ends], open(os.path.join(outdir, 'tree_ends.json'), 'w'))
    main = P.to_object('main')
    finish([main], Gl, 'holy_tree', outdir, tex_size=1024)
    place('holy_tree', TREE[0], G(*TREE) - .1, TREE[1])
    cam = preview_setup()
    shot(cam, os.path.join(outdir, 'holy_tree.png'), (22, -32, 12), (0, 0, 16), 34, (800, 800))


def holy_canopy():
    """树冠的发光云：带透明贴图的交叉面片，和树共用原点。"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rnd = random.Random(77)
    ends = [Vector(e) for e in json.load(open(os.path.join(outdir, 'tree_ends.json')))]
    verts, faces, uvs = [], [], []

    def card(c, size):
        u = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, .35))).normalized()
        v = u.cross(Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1)))).normalized()
        u, v = u * size, v * size * .72
        pts = [c - u - v, c + u - v, c + u + v, c - u + v]
        uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
        for order in (pts, pts[::-1]):
            i = len(verts)
            verts.extend(tuple(p) for p in order)
            uvs.extend(uv if order is pts else uv[::-1])
            faces.append((i, i + 1, i + 2, i + 3))

    for e in ends:
        for _ in range(9):
            card(e + Vector((rnd.gauss(0, 1.9), rnd.gauss(0, 1.9), rnd.gauss(0, 1.0))), rnd.uniform(2.2, 3.8))
    me = bpy.data.meshes.new('holy_canopy')
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name='UV')
    for p in me.polygons:
        for li in p.loop_indices:
            uv.data[li].uv = uvs[me.loops[li].vertex_index]
    m = bpy.data.materials.new('holy_canopy')
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(os.path.join(outdir, 'leaf_atlas.png'))
    nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    nt.links.new(t.outputs['Color'], b.inputs['Emission Color'])
    nt.links.new(t.outputs['Alpha'], b.inputs['Alpha'])
    b.inputs['Emission Strength'].default_value = .8
    m.blend_method = 'BLEND'
    me.materials.append(m)
    ob = bpy.data.objects.new('main', me)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    path = os.path.join(outdir, 'holy_canopy.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_image_format='AUTO')
    print('BUILT holy_canopy tris', sum(len(f) - 2 for f in faces), 'MB', round(os.path.getsize(path) / 1e6, 2), flush=True)
    place('holy_canopy', TREE[0], G(*TREE) - .1, TREE[1])


def flat_export(name, faces_by_mat, mats, origin):
    """一个网格 + 一个材质 + 一张调色板贴图（编辑器对多材质模型的缩放有问题）。mats: [(颜色, 发光强度)]"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    W = 64
    img = bpy.data.images.new(name + '_pal', W * len(mats), W, alpha=False)
    em = bpy.data.images.new(name + '_em', W * len(mats), W, alpha=False)
    px, ex = [], []
    for row in range(W):
        for hexc, e in mats:
            r, g, b_, _ = srgb(hexc)
            for _i in range(W):
                px += [r, g, b_, 1.0]
                ex += [r * e, g * e, b_ * e, 1.0]
    img.pixels = px
    em.pixels = ex
    for im, fn in ((img, 'pal'), (em, 'em')):
        im.filepath_raw = os.path.join(outdir, f'{name}_{fn}.png')
        im.file_format = 'PNG'
        im.save()
    verts, faces, uvs = [], [], []
    for mi, flist in enumerate(faces_by_mat):
        u = (mi + .5) / len(mats)
        for pts in flist:
            start = len(verts)
            verts += pts
            uvs += [(u, .5)] * len(pts)
            faces.append(tuple(range(start, start + len(pts))))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name='UV')
    for p in me.polygons:
        for li in p.loop_indices:
            uv.data[li].uv = uvs[me.loops[li].vertex_index]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    t1 = nt.nodes.new('ShaderNodeTexImage')
    t1.image = img
    t2 = nt.nodes.new('ShaderNodeTexImage')
    t2.image = em
    nt.links.new(t1.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(t2.outputs['Color'], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = .85
    m.use_backface_culling = False
    me.materials.append(m)
    ob = bpy.data.objects.new('main', me)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    path = os.path.join(outdir, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
    print('BUILT', name, 'tris', sum(len(p) - 2 for fl in faces_by_mat for p in fl), 'MB', round(os.path.getsize(path) / 1e6, 2), flush=True)
    place(name, origin[0], 0.0, origin[1])


def flower_clump(name, seed, cards):
    """花丛：几片交叉的竖直面片贴花带，地上一片花毯。面数极低，靠透明贴图出效果。"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    rnd = random.Random(seed)
    BAND = .36  # 贴图上面 36% 是花带（v 从 1-BAND 到 1）
    verts, faces, uvs = [], [], []

    def quad(pts, uv):
        i = len(verts)
        verts.extend(pts)
        uvs.extend(uv)
        faces.append((i, i + 1, i + 2, i + 3))
        i = len(verts)
        verts.extend(pts[::-1])
        uvs.extend(uv[::-1])
        faces.append((i, i + 1, i + 2, i + 3))

    for _ in range(cards):
        ang = rnd.uniform(0, math.pi)
        L = rnd.uniform(2.2, 3.2)
        H_ = rnd.uniform(1.05, 1.3)
        ox, oy = rnd.uniform(-3.4, 3.4), rnd.uniform(-3.4, 3.4)
        ux, uy = math.cos(ang) * L / 2, math.sin(ang) * L / 2
        u1 = L * .3  # 贴图横向 614 像素/米，和纵向一致，花才不变形
        u0 = rnd.uniform(0, 1 - u1)
        u1 = u0 + u1
        v0, v1 = 1 - BAND, 1.0
        quad([(ox - ux, oy - uy, -.02), (ox + ux, oy + uy, -.02), (ox + ux, oy + uy, H_), (ox - ux, oy - uy, H_)],
             [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    # 地面花毯（圆形部分在贴图下方）
    R = 5.0
    bv = (1 - BAND) / 2
    h = (1 - BAND) / 2
    hu = h
    i = len(verts)
    for a_, b_ in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        verts.append((a_ * R, b_ * R, .1))
        uvs.append((.5 + a_ * hu, bv + b_ * h))
    faces.append((i, i + 1, i + 2, i + 3))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name='UV')
    for p in me.polygons:
        for li in p.loop_indices:
            uv.data[li].uv = uvs[me.loops[li].vertex_index]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(os.path.join(outdir, 'flower_atlas.png'))
    nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(t.outputs['Alpha'], bsdf.inputs['Alpha'])
    nt.links.new(t.outputs['Color'], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = .3
    bsdf.inputs['Roughness'].default_value = .9
    m.blend_method = 'BLEND'
    me.materials.append(m)
    ob = bpy.data.objects.new('main', me)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    path = os.path.join(outdir, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_image_format='AUTO')
    print('BUILT', name, 'tris', sum(len(f) - 2 for f in faces), 'MB', round(os.path.getsize(path) / 1e6, 2), flush=True)


def firework(name, core, tip):
    """烟花：从中心放射的光条，半径 5 米。脚本放大它、再隐藏。"""
    rnd = random.Random(sum(map(ord, name)))
    mats = [(core, 1.8), (tip, 2.2)]
    faces = [[], []]
    for _ in range(170):
        z_ = rnd.uniform(-1, 1)
        a = rnd.uniform(0, math.tau)
        r2 = math.sqrt(1 - z_ * z_)
        d = Vector((r2 * math.cos(a), r2 * math.sin(a), z_))
        side = d.cross(Vector((.3, .7, .2))).normalized() * .05
        R = 5 * rnd.uniform(.72, 1)
        p0, p1 = d * R * .55, d * R
        faces[0].append([tuple(p0), tuple(p1 + side), tuple(p1 - side)])
        faces[0].append([tuple(p0), tuple(p1 - side), tuple(p1 + side)])
        tipv = d.cross(side).normalized() * .12
        faces[1].append([tuple(p1 + side * 3), tuple(p1 + tipv), tuple(p1 - side * 3), tuple(p1 - tipv)])
        faces[1].append([tuple(p1 - tipv), tuple(p1 - side * 3), tuple(p1 + tipv), tuple(p1 + side * 3)])
    flat_export(name, faces, mats, (0.0, 0.0))
    placements.pop(name, None)


def bat():
    """蝙蝠：V 形双翼。脚本让它绕城堡飞，并翻转翼尖高度来扇动。翼展 1 米。"""
    mats = [('#141018', 0)]
    faces = [[]]
    for s in (-1, 1):
        ring = [(s * .04, .16, 0), (s * .22, .12, .08), (s * .5, .05, .2), (s * .36, -.05, .1), (s * .24, -.02, .06), (s * .16, -.1, .03), (s * .04, -.14, 0)]
        for tri in ((0, 1, 6), (1, 5, 6), (1, 2, 3), (1, 3, 4), (1, 4, 5)):
            f = [ring[i] for i in tri]
            faces[0].append(f)
            faces[0].append(f[::-1])
    faces[0].append([(-.04, .2, 0), (.04, .2, 0), (.04, -.16, 0), (-.04, -.16, 0)])
    faces[0].append([(-.04, -.16, 0), (.04, -.16, 0), (.04, .2, 0), (-.04, .2, 0)])
    flat_export('bat', faces, mats, (0.0, 0.0))
    placements.pop('bat', None)


def path_lamps():
    """沿路的灯柱和串灯：夜里路线一眼可见。世界坐标。"""
    kit.reset()
    rnd = random.Random(31)
    P, Gl = Mesh(), Mesh()
    lamps = []

    def add_line(pts, every, side_flip=True):
        acc, last = 0.0, None
        s = 1
        for i in range(1, len(pts)):
            ax, ay = pts[i - 1]
            bx, by = pts[i]
            L = math.hypot(bx - ax, by - ay)
            acc += L
            if acc >= every:
                acc = 0
                nx, ny = -(by - ay) / (L + 1e-6), (bx - ax) / (L + 1e-6)
                x, y = bx + nx * 2.7 * s, by + ny * 2.7 * s
                lamps.append((x, y))
                if side_flip:
                    s = -s

    add_line([(p[0], p[1]) for p in PATH], 11.0)
    add_line(ROADS[1], 12.0)
    add_line(ROADS[2], 9.0, False)
    print('lamps', len(lamps))
    tops = []
    for x, y in lamps:
        g = G(x, y)
        ox, oy = x - OX, y - OY
        P.cyl(.1, .07, 3.3, (ox, oy, g + 1.6), C['lamp'], 6)
        P.rbox((.42, .42, .22), (ox, oy, g + .1), C['lamp2'], cuts=0)
        P.rbox((.5, .1, .06), (ox, oy, g + 3.25), C['lamp'], cuts=0)
        P.cyl(.26, .03, .34, (ox, oy, g + 3.98), C['lamp'], 4, (0, 0, math.pi / 4))
        Gl.rbox((.32, .32, .5), (ox, oy, g + 3.55), 'glass', cuts=0)
        tops.append((ox, oy, g + 3.3))
    # 灯柱之间的串灯
    for (ax, ay, az), (bx, by, bz) in zip(tops, tops[1:]):
        L = math.hypot(ax - bx, ay - by)
        if L > 16:
            continue
        n = int(L / 1.1)
        for i in range(1, n):
            t = i / n
            sag = math.sin(t * math.pi) * L * .07
            x, y, z = ax + (bx - ax) * t, ay + (by - ay) * t, az + (bz - az) * t - sag
            Gl.rbox((.13, .13, .13), (x, y, z), 'star' if i % 2 else 'glass', cuts=0)
    main = P.to_object('main')
    finish([main], Gl, 'path_lamps', outdir, tex_size=512)
    place('path_lamps', OX, 0.0, OY)


def pine(P, rnd, ox, oy, g, h):
    P.cyl(h * .03, h * .016, h * .35, (ox, oy, g + h * .16), C['bark3'], 5)
    tiers = 4
    for i in range(tiers):
        t = i / tiers
        r = h * (.27 - t * .19) * rnd.uniform(.92, 1.08)
        zb = g + h * (.18 + t * .68)
        P.cyl(r, r * .12, h * .34, (ox, oy, zb + h * .16), C[rnd.choice(('pine', 'pine2', 'pine3'))], 7, (0, 0, rnd.uniform(0, 3)))


def dead_tree(P, rnd, ox, oy, g, h):
    def limb(s, d, L, r, depth):
        pts, radii = [Vector(s)], [r]
        d = Vector(d).normalized()
        for i in range(3):
            d = (d + Vector((rnd.uniform(-.5, .5), rnd.uniform(-.5, .5), rnd.uniform(-.2, .3)))).normalized()
            pts.append(pts[-1] + d * L / 3)
            radii.append(r * (1 - (i + 1) / 3 * .72))
        P.tube([tuple(p) for p in pts], radii, C[rnd.choice(('dead', 'dead2'))], seg=4 if depth < 2 else 3)
        if depth < 3:
            for k in range(2 if depth else 3):
                a = rnd.uniform(0, math.tau)
                limb(pts[rnd.randint(1, 3)], (math.cos(a), math.sin(a), rnd.uniform(.1, .8)), L * rnd.uniform(.5, .72), radii[2] * .9, depth + 1)
    limb((ox, oy, g - .3), (rnd.uniform(-.2, .2), rnd.uniform(-.2, .2), 1), h * .55, h * .042, 0)


def forest():
    """森林：松树成片，山脚和路边穿插枯树。世界坐标。"""
    kit.reset()
    rnd = random.Random(909)
    P, Gl = Mesh(), Mesh()
    zones = [(14, 92, 18, 120, 44), (20, 62, 130, 196, 24), (176, 214, 168, 196, 14), (92, 170, 196, 212, 10), (170, 205, 20, 54, 12)]
    spots = []

    def ok(x, y, need=7.0):
        g = G(x, y)
        if g < SEA + 2.5 or slope(x, y) > 30 or road_dist(x, y) < 6 or seg_dist(x, y, RIVER) < 6:
            return False
        if math.hypot(x - TREE[0], y - TREE[1]) < 30 or math.hypot(x - SPAWN[0], y - SPAWN[1]) < 28:
            return False
        if math.hypot(x - 127, y - 176) < 24:
            return False
        if abs(x - 171) < 12 and abs(y - 146) < 12:
            return False
        return all(math.hypot(x - a, y - b) >= need for a, b in spots)

    n = 0
    for x0, x1, y0, y1, want in zones:
        for _ in range(want * 12):
            if want <= 0:
                break
            x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
            if not ok(x, y):
                continue
            spots.append((x, y))
            pine(P, rnd, x - OX, y - OY, G(x, y), rnd.uniform(9, 17))
            want -= 1
            n += 1
    # 小山的草坡上点缀几棵小松树，打破轮廓
    for _ in range(26):
        a = rnd.uniform(.0, math.tau)
        d = rnd.uniform(29, 45)
        x, y = 127 + math.cos(a) * d, 176 + math.sin(a) * d
        if road_dist(x, y) < 4.5 or seg_dist(x, y, RIVER) < 7 or slope(x, y) > 55 or math.hypot(x - 125, y - 135) < 7:
            continue
        pine(P, rnd, x - OX, y - OY, G(x, y) - .2, rnd.uniform(5, 9))
        n += 1
    print('pines', n)
    d = 0
    for x0, x1, y0, y1, want in [(90, 128, 118, 134, 3), (60, 100, 90, 130, 5), (150, 170, 118, 132, 2), (170, 196, 120, 150, 3)]:
        for _ in range(want * 14):
            if want <= 0:
                break
            x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
            if not ok(x, y, 5):
                continue
            spots.append((x, y))
            dead_tree(P, rnd, x - OX, y - OY, G(x, y), rnd.uniform(8, 13))
            want -= 1
            d += 1
    print('dead trees', d)
    main = P.to_object('main')
    finish([main], Gl, 'forest', outdir, tex_size=1024)
    place('forest', OX, 0.0, OY)


def graveyard():
    """山脚西侧的小墓园：墓碑（不用十字形）、铁栅栏、枯树、南瓜灯。世界坐标。"""
    kit.reset()
    rnd = random.Random(404)
    P, Gl = Mesh(), Mesh()
    CX, CY = 76.0, 110.0
    spots = []
    for _ in range(300):
        x, y = CX + rnd.uniform(-13, 13), CY + rnd.uniform(-10, 10)
        if slope(x, y) > 20 or any(math.hypot(x - a, y - b) < 2.6 for a, b in spots):
            continue
        spots.append((x, y))
        if len(spots) >= 20:
            break
    for x, y in spots:
        g = G(x, y)
        ox, oy = x - OX, y - OY
        yaw = rnd.uniform(-.25, .25)
        c = C[rnd.choice(('grave', 'grave2', 'grave3'))]
        kind = rnd.randrange(3)
        w, h = rnd.uniform(.8, 1.15), rnd.uniform(1.2, 1.9)
        tilt = (rnd.uniform(-.08, .08), rnd.uniform(-.08, .08), yaw)
        P.rbox((w * 1.35, .55, .28), (ox, oy, g + .1), C['grave3'], (0, 0, yaw), cuts=0)
        if kind == 0:
            P.rbox((w, .22, h), (ox, oy, g + h / 2), c, tilt, cuts=1)
            P.cyl(w / 2, w / 2, .22, (ox, oy, g + h), c, 12, (math.pi / 2, 0, yaw))
        elif kind == 1:
            P.rbox((w, .24, h), (ox, oy, g + h / 2), c, tilt, cuts=0)
            P.rbox((w * .71, .24, w * .71), (ox, oy, g + h), c, (0, math.pi / 4, yaw), cuts=0)
        else:
            P.rbox((w * .55, w * .55, h * 1.25), (ox, oy, g + h * .62), c, tilt, cuts=0)
            P.cyl(w * .42, .03, h * .55, (ox, oy, g + h * 1.5), c, 4, (0, 0, math.pi / 4))
    # 南瓜灯
    for _ in range(9):
        x, y = CX + rnd.uniform(-13, 13), CY + rnd.uniform(-10, 10)
        if slope(x, y) > 22:
            continue
        g = G(x, y)
        ox, oy = x - OX, y - OY
        r = rnd.uniform(.42, .68)
        for k in range(6):
            a = k / 6 * math.tau
            P.sphere(r * .62, (ox + math.cos(a) * r * .42, oy + math.sin(a) * r * .42, g + r * .62), C['pump' if k % 2 else 'pump2'], 8, (1, 1, .95))
        P.cyl(.08, .05, .28, (ox, oy, g + r * 1.35), C['stem'], 5)
        for s in (-1, 1):
            Gl.rbox((r * .24, .05, r * .24), (ox + s * r * .3, oy - r * .98, g + r * .78), 'p_white' if False else 'glass', (0, math.pi / 4, 0), cuts=0)
        Gl.rbox((r * .6, .05, r * .14), (ox, oy - r * .98, g + r * .42), 'glass', cuts=0)
    # 铁栅栏
    gw, gh = 15.0, 12.0
    for side, (ax, ay, bx, by) in enumerate(((-gw, -gh, gw, -gh), (gw, -gh, gw, gh), (gw, gh, -gw, gh), (-gw, gh, -gw, -gh))):
        L = math.hypot(bx - ax, by - ay)
        n = int(L / .9)
        for i in range(n + 1):
            t = i / n
            x, y = CX + ax + (bx - ax) * t, CY + ay + (by - ay) * t
            if side == 0 and abs(x - CX) < 2:
                continue
            g = G(x, y)
            ox, oy = x - OX, y - OY
            P.rbox((.08, .08, 1.8), (ox, oy, g + .85), C['iron'], cuts=0)
            P.cyl(.09, .01, .3, (ox, oy, g + 1.9), C['iron'], 4)
            if i < n:
                x2, y2 = CX + ax + (bx - ax) * (i + 1) / n, CY + ay + (by - ay) * (i + 1) / n
                g2 = G(x2, y2)
                ang = math.atan2(y2 - y, x2 - x)
                P.rbox((L / n, .06, .06), ((ox + x2 - OX) / 2, (oy + y2 - OY) / 2, (g + g2) / 2 + 1.5), C['iron'], (0, 0, ang), cuts=0)
    for _ in range(3):
        dead_tree(P, rnd, CX + rnd.uniform(-11, 11) - OX, CY + rnd.uniform(-8, 8) - OY, G(CX, CY) - .2, rnd.uniform(8, 11))
    main = P.to_object('main')
    finish([main], Gl, 'graveyard', outdir, tex_size=1024)
    place('graveyard', OX, 0.0, OY)


def time_dial():
    """时之晷：踩上去切换昼夜的石台。城堡庭院和出生点各放一个。原点在地面中心。"""
    kit.reset()
    P, Gl = Mesh(), Mesh()
    P.lathe([(.02, .42), (2.1, .42), (2.25, .3), (2.25, 0), (2.5, -.3), (.02, -.3)], C['wst'], 24)
    P.lathe([(1.8, .43), (1.86, .5), (1.92, .43)], C['gold'], 24)
    Gl.lathe([(1.55, .44), (.02, .44)], 'p_white', 24)
    for i in range(12):
        a = i / 12 * math.tau
        Gl.rbox((.5 if i % 3 == 0 else .3, .1, .03), (math.cos(a) * 1.2, math.sin(a) * 1.2, .47), 'star', (0, 0, a), cuts=0)
    # 中央细针和日月
    P.cyl(.1, .04, 1.3, (0, 0, 1.05), C['gold'], 8)
    Gl.sphere(.2, (0, 0, 1.8), 'star', 10)
    P.rbox((.1, .1, .1), (0, 0, .46), C['gold'], cuts=0)
    main = P.to_object('main')
    finish([main], Gl, 'time_dial', outdir, tex_size=512)
    place('time_dial', 121.0, G(121, 57), 57.0)
    cam = preview_setup()
    shot(cam, os.path.join(outdir, 'time_dial.png'), (5, -6, 4), (0, 0, 1), 34, (600, 500))


PARTS = dict(holy_tree=holy_tree, holy_canopy=holy_canopy, flower_clump_a=lambda: flower_clump('flower_clump_a', 5, 11), flower_clump_b=lambda: flower_clump('flower_clump_b', 6, 10), flower_clump_c=lambda: flower_clump('flower_clump_c', 7, 8),
             firework_gold=lambda: firework('firework_gold', '#FFD36B', '#FFF6D0'), firework_pink=lambda: firework('firework_pink', '#FF7FC8', '#FFE3F4'), firework_blue=lambda: firework('firework_blue', '#6FB7FF', '#E6F5FF'), bat=bat,
             path_lamps=path_lamps, forest=forest, graveyard=graveyard, time_dial=time_dial)
for name, fn in PARTS.items():
    if only and name not in only:
        continue
    fn()
    json.dump(list(placements.values()), open(PLACE, 'w'), indent=1)
print('DONE')
