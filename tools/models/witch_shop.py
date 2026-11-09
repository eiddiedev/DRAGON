# 用法：Blender --background --python witch_shop.py -- <输出目录>
# 女巫药水铺：可走进去的空心圆塔 + 歪尖帽屋顶。单位是米，原点在门前地面中心的塔心。
# 尺寸：内径约 8 米，门高 2.6 米，室内净高 5 米；东侧外摆药水摊。
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

outdir = sys.argv[sys.argv.index('--') + 1]
os.makedirs(outdir, exist_ok=True)
rnd = random.Random(11)
bpy.ops.wm.read_factory_settings(use_empty=True)

PALETTE = {
    'stone': (.46, .43, .38), 'stone_d': (.30, .28, .27), 'plaster': (.80, .68, .46), 'wood': (.20, .10, .05),
    'wood_l': (.40, .22, .09), 'roof': (.24, .10, .46), 'roof_d': (.15, .06, .34), 'gold': (.90, .66, .20),
    'iron': (.11, .11, .13), 'cloth': (.72, .24, .24), 'cloth2': (.92, .85, .70),
}
GLOW = {'glass': (1.0, .78, .32), 'brew': (.35, 1.0, .55), 'p_red': (1.0, .22, .30), 'p_blue': (.25, .60, 1.0),
        'p_white': (.92, .95, 1.0), 'p_pink': (1.0, .50, .85), 'star': (1.0, .88, .40)}
mats = {}


def mat(name):
    if name in mats:
        return mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    if name in GLOW:
        c = GLOW[name]
        b.inputs['Base Color'].default_value = (*c, 1)
        b.inputs['Emission Color'].default_value = (*c, 1)
        b.inputs['Emission Strength'].default_value = 1.6
    else:
        b.inputs['Base Color'].default_value = (*PALETTE[name], 1)
        b.inputs['Roughness'].default_value = .85
    mats[name] = m
    return m


class Part:
    """一组同类几何，最后合成一个物体。"""

    def __init__(self, name):
        self.name, self.bm, self.slots = name, bmesh.new(), []

    def _slot(self, m):
        if m not in self.slots:
            self.slots.append(m)
        return self.slots.index(m)

    def box(self, size, loc, m, rot=(0, 0, 0), taper=1.0):
        r = bmesh.ops.create_cube(self.bm, size=1)['verts']
        for v in r:
            k = taper if v.co.z > 0 else 1.0
            v.co = Vector((v.co.x * size[0] * k, v.co.y * size[1] * k, v.co.z * size[2]))
            v.co = Euler(rot).to_matrix() @ v.co + Vector(loc)
        self._tag(r, m)

    def cyl(self, r1, r2, h, loc, m, seg=12, rot=(0, 0, 0), caps=True):
        vs = bmesh.ops.create_cone(self.bm, cap_ends=caps, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=h)['verts']
        for v in vs:
            v.co = Euler(rot).to_matrix() @ v.co + Vector(loc)
        self._tag(vs, m)

    def sphere(self, r, loc, m, seg=10, scale=(1, 1, 1)):
        vs = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=max(6, seg // 2 + 1), radius=r)['verts']
        for v in vs:
            v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2])) + Vector(loc)
        self._tag(vs, m)

    def _tag(self, verts, m):
        i = self._slot(m)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = i

    def build(self):
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for s in self.slots:
            me.materials.append(mat(s))
        ob = bpy.data.objects.new(self.name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob


R_IN, THICK, WALL_H = 4.0, .55, 5.4
R_MID = R_IN + THICK / 2
SEG = 24
DOOR = 0  # 第 0 段正对南面（-Y），是门
WINDOWS = {4, 8, 16, 20}


def seg_angle(i):
    return -math.pi / 2 + i / SEG * math.tau


seg_w = 2 * (R_IN + THICK) * math.tan(math.pi / SEG) + .03
wall = Part('wall')
door_segs = {0, 1, SEG - 1}
for i in range(SEG):
    a = seg_angle(i)
    x, y = math.cos(a) * R_MID, math.sin(a) * R_MID
    rz = a + math.pi / 2
    if i in door_segs:
        # 门洞：只保留门楣以上
        wall.box((seg_w, THICK, WALL_H - 3.0), (x, y, 3.0 + (WALL_H - 3.0) / 2), 'plaster', (0, 0, rz))
    elif i in WINDOWS:
        wall.box((seg_w, THICK, 2.0), (x, y, 1.0), 'plaster', (0, 0, rz))
        wall.box((seg_w, THICK, WALL_H - 3.6), (x, y, 3.6 + (WALL_H - 3.6) / 2), 'plaster', (0, 0, rz))
        wall.box((seg_w * .92, .08, 1.6), (x, y, 2.8), 'glass', (0, 0, rz))
        wall.box((.10, .16, 1.6), (x, y, 2.8), 'wood', (0, 0, rz))
        wall.box((seg_w * .92, .16, .10), (x, y, 2.8), 'wood', (0, 0, rz))
    else:
        wall.box((seg_w, THICK, WALL_H), (x, y, WALL_H / 2), 'plaster', (0, 0, rz))
    # 墙根和墙角的露石，让圆塔不那么光
    for _ in range(3):
        h = rnd.uniform(.25, .5)
        z = rnd.choice((rnd.uniform(.2, 1.2), rnd.uniform(3.6, 5.0)))
        if i in door_segs and z < 3.2:
            continue
        o = R_IN + THICK + .02
        wall.box((seg_w * rnd.uniform(.35, .7), .16, h), (math.cos(a + rnd.uniform(-.09, .09)) * o, math.sin(a + rnd.uniform(-.09, .09)) * o, z), 'stone', (0, 0, rz))
# 墙基、顶部出挑的木带
base = Part('base')
base.cyl(R_IN + THICK + .35, R_IN + THICK + .2, .5, (0, 0, .15), 'stone_d', SEG, caps=False)
# 门框、门板（向外半开）、门灯
dw = 2.05
oy = -(R_IN + THICK)
for sx in (-1, 1):
    wall.box((.34, .75, 3.1), (sx * (dw / 2 + .17), oy + .2, 1.55), 'stone_d')
wall.box((dw + .7, .75, .4), (0, oy + .2, 3.2), 'stone_d')
wall.box((.12, 1.6, 2.75), (dw / 2 + .55, oy - .7, 1.4), 'wood_l', (0, 0, math.radians(14)))
for z in (.7, 2.2):
    wall.box((.14, 1.62, .12), (dw / 2 + .55, oy - .7, z), 'iron', (0, 0, math.radians(14)))
wall.box((.5, .5, .55), (-(dw / 2 + .85), oy - .3, 3.0), 'glass')
wall.box((.6, .6, .1), (-(dw / 2 + .85), oy - .3, 3.32), 'iron')

# 歪尖帽屋顶：一圈圈叠的瓦，越往上越细，并向东北弯
roof = Part('roof')
roof.cyl(R_IN + THICK + .35, R_IN + THICK + .35, .22, (0, 0, WALL_H + .05), 'wood', SEG)
RINGS = 15
Hroof = 8.6
bend = Vector((1.5, 1.0, 0))
for k in range(RINGS):
    t0, t1 = k / RINGS, (k + 1) / RINGS
    r0 = (1 - t0) ** 1.25 * (R_IN + THICK + 1.1) + .05
    r1 = (1 - t1) ** 1.25 * (R_IN + THICK + 1.1) + .05
    c0 = bend * t0 ** 2.4 + Vector((0, 0, WALL_H + .1 + t0 * Hroof))
    c1 = bend * t1 ** 2.4 + Vector((0, 0, WALL_H + .1 + t1 * Hroof))
    m = 'roof_d' if k % 2 else 'roof'
    roof.cyl(r0, r1 * 1.05, (c1 - c0).z + .12, ((c0 + c1) / 2).to_tuple(), m, max(10, 26 - k))
tip = bend + Vector((0, 0, WALL_H + .1 + Hroof))
roof.cyl(.28, .02, .7, (tip.x + .12, tip.y + .08, tip.z + .25), 'gold', 8, (0, math.radians(14), 0))
roof.sphere(.32, (tip.x + .22, tip.y + .14, tip.z + .75), 'star', 8)
# 帽带与星星
c = bend * .35 ** 2.4 + Vector((0, 0, WALL_H + .1 + .35 * Hroof))
r = (.65) ** 1.25 * (R_IN + THICK + 1.1) + .05
roof.cyl(r + .08, r - .12, .55, c.to_tuple(), 'gold', 22)
# 烟囱
roof.box((1.05, 1.05, 2.8), (-2.7, 2.4, WALL_H + 2.0), 'stone_d')
roof.box((1.3, 1.3, .24), (-2.7, 2.4, WALL_H + 3.45), 'iron')

# ---------- 室内
inner = Part('interior')
inner.cyl(R_IN + .05, R_IN + .05, .12, (0, 0, .06), 'wood_l', SEG)
for x in range(-3, 4):
    inner.box((.05, 8.0 * math.sqrt(max(0, 1 - (x / 4.2) ** 2)), .02), (x * 1.0, 0, .125), 'wood')
# 房梁
for a in (0, math.pi / 2):
    inner.box((R_IN * 2, .28, .28), (0, 0, 5.1), 'wood', (0, 0, a))
# 中央坩埚（龙蛋孵化点）
inner.cyl(1.05, 1.2, .35, (0, 1.0, .3), 'stone_d', 14)
inner.sphere(.92, (0, 1.0, 1.05), 'iron', 14, (1, 1, .82))
inner.cyl(.8, .8, .06, (0, 1.0, 1.65), 'brew', 14)
inner.cyl(.94, .94, .14, (0, 1.0, 1.66), 'iron', 18, caps=False)
for a in range(3):
    t = a / 3 * math.tau
    inner.cyl(.1, .07, .55, (math.cos(t) * .7, 1.0 + math.sin(t) * .7, .3), 'iron', 6)
for dx, dz in ((-.3, 2.0), (.28, 2.35), (0, 2.75)):
    inner.sphere(.13, (dx, 1.0, dz), 'brew', 6)
# 北墙架子和瓶子
for z in (1.3, 2.3, 3.3):
    inner.box((4.2, .55, .1), (0, R_IN - .48, z), 'wood')
for sx in (-2.2, 2.2):
    inner.box((.14, .6, 3.2), (sx, R_IN - .48, 2.0), 'wood')
bottles = ['p_red', 'p_blue', 'p_white', 'p_pink', 'gold', 'brew']
for z in (1.3, 2.3, 3.3):
    for i in range(7):
        x = -1.8 + i * .6
        c_ = rnd.choice(bottles)
        h = rnd.uniform(.22, .38)
        inner.cyl(.11, .11, h, (x, R_IN - .48, z + .05 + h / 2), c_, 8)
        inner.cyl(.05, .05, .14, (x, R_IN - .48, z + .05 + h + .07), 'iron', 6)
# 西墙一张书桌 + 飘着的书
inner.box((.9, 2.2, .1), (-R_IN + .9, -.2, 1.05), 'wood_l')
for y in (-1.1, .7):
    inner.box((.12, .12, 1.0), (-R_IN + .9, y, .55), 'wood')
for i, (y, z, rz) in enumerate(((-.6, 1.2, .3), (.2, 1.17, -.2), (-.1, 1.95, .9))):
    inner.box((.55, .42, .09), (-R_IN + .95, y, z), ['cloth', 'roof', 'gold'][i], (.2 if i == 2 else 0, 0, rz))

# ---------- 东侧药水摊（四瓶可喝的药水就在这里）
stall = Part('stall')
SX = R_IN + THICK + 2.1
stall.box((3.4, 1.35, .14), (SX + .1, -2.4, 1.15), 'wood_l')
stall.box((3.2, 1.2, 1.1), (SX + .1, -2.4, .55), 'wood')
for i, x in enumerate((-.9, 0, .9)):
    stall.box((.09, 1.24, 1.0), (SX + .1 + x, -2.4, .55), 'wood_l')
for sx in (-1.6, 1.7):
    stall.box((.14, .14, 3.2), (SX + .1 + sx, -3.0, 1.6), 'wood')
    stall.box((.14, .14, 3.7), (SX + .1 + sx, -1.7, 1.85), 'wood')
for i in range(7):
    w = 3.9 / 7
    x = SX + .1 - 1.95 + w * (i + .5)
    stall.box((w, 1.85, .09), (x, -2.35, 3.3), 'cloth' if i % 2 else 'cloth2', (math.radians(-15), 0, 0))
for i, c_ in enumerate(('p_red', 'p_blue', 'p_white', 'p_pink')):
    x = SX + .1 - 1.1 + i * .73
    stall.sphere(.2, (x, -2.5, 1.42), c_, 10)
    stall.cyl(.07, .05, .22, (x, -2.5, 1.68), c_, 8)
    stall.cyl(.07, .07, .08, (x, -2.5, 1.82), 'wood_l', 6)
    stall.box((.42, .42, .05), (x, -2.5, 1.24), 'gold')

parts = {p.name: p.build() for p in (wall, base, roof, inner, stall)}
tris = 0
for o in parts.values():
    o.data.calc_loop_triangles()
    tris += len(o.data.loop_triangles)
print('TRIANGLES', tris)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.join(outdir, 'witch_shop.glb'), export_format='GLB', use_selection=True,
                          export_apply=True, export_yup=True)
print('GLB_MB', round(os.path.getsize(os.path.join(outdir, 'witch_shop.glb')) / 1e6, 2))

# ---------- 预览
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.view_settings.view_transform = 'Standard'
scene.cycles.samples = 48
scene.cycles.device = 'CPU'
scene.render.resolution_x, scene.render.resolution_y = 1000, 760
ground = bpy.data.meshes.new('g')
gb = bmesh.new()
bmesh.ops.create_grid(gb, x_segments=1, y_segments=1, size=60)
gb.to_mesh(ground)
gb.free()
g_ob = bpy.data.objects.new('ground', ground)
gm = bpy.data.materials.new('grass')
gm.use_nodes = True
gm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.22, .42, .10, 1)
ground.materials.append(gm)
scene.collection.objects.link(g_ob)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 2.6
sun.data.color = (1, .91, .78)
sun.data.angle = math.radians(4)
sun.rotation_euler = Euler((math.radians(55), 0, math.radians(-40)))
scene.collection.objects.link(sun)
w = bpy.data.worlds.new('w')
w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (.58, .76, .95, 1)
w.node_tree.nodes['Background'].inputs[1].default_value = .55
scene.world = w
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam'))
scene.collection.objects.link(cam)
scene.camera = cam


def shot(fn, loc, target, lens=35):
    cam.data.lens = lens
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = os.path.join(outdir, fn)
    bpy.ops.render.render(write_still=True)


# 预览里加一个 1.2 米高的小人做比例
fig = Part('fig')
fig.sphere(.34, (2.5, -7.0, .95), 'cloth', 10)
fig.cyl(.3, .22, .65, (2.5, -7.0, .32), 'iron', 10)
fig.build()
shot('witch_shop_front.png', (9, -21, 7), (1.2, 0, 6), 40)
parts['roof'].hide_render = True
parts['wall'].hide_render = True
shot('witch_shop_cutaway.png', (6, -13, 13), (.5, .5, 1.2), 34)
