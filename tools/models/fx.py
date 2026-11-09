# 用法：Blender --background --python fx.py -- <目录>
# 火焰、光柱、火星/萤火虫。全部发光、半透明、无碰撞，由脚本驱动。
import math
import os
import random
import sys

import bpy

D = sys.argv[sys.argv.index('--') + 1]
rnd = random.Random(5)


def make(name, verts, faces, uvs, tex, power=2.0):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name='UV')
    for p, q in zip(me.polygons, uvs):
        for li, c in zip(p.loop_indices, q):
            uv.data[li].uv = c
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.blend_method = 'BLEND'
    m.use_backface_culling = False
    pb = m.node_tree.nodes['Principled BSDF']
    tx = m.node_tree.nodes.new('ShaderNodeTexImage')
    tx.image = bpy.data.images.load(os.path.join(D, tex))
    m.node_tree.links.new(tx.outputs['Color'], pb.inputs['Base Color'])
    m.node_tree.links.new(tx.outputs['Color'], pb.inputs['Emission Color'])
    pb.inputs['Emission Strength'].default_value = power
    m.node_tree.links.new(tx.outputs['Alpha'], pb.inputs['Alpha'])
    me.materials.append(m)
    p = os.path.join(D, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=p, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_image_format='AUTO')
    print('BUILT', name, len(faces) * 2, round(os.path.getsize(p) / 1e6, 2), flush=True)


# 火焰：三张交叉面片，高 2，底在 0
v, f, u = [], [], []
for i in range(3):
    a = i * math.pi / 3
    dx, dy = math.cos(a), math.sin(a)
    n = len(v)
    v += [(-dx, -dy, 0), (dx, dy, 0), (dx, dy, 2), (-dx, -dy, 2)]
    f.append((n, n + 1, n + 2, n + 3))
    u.append(((0, 0), (1, 0), (1, 1), (0, 1)))
make('fire_fx', v, f, u, 'flame.png', 2.5)
# 光柱：12 边圆筒，上细下粗
v, f, u = [], [], []
SEG = 12
for i in range(SEG):
    a0, a1 = i / SEG * math.tau, (i + 1) / SEG * math.tau
    r0, r1 = .5, .24
    n = len(v)
    v += [(math.cos(a0) * r0, math.sin(a0) * r0, 0), (math.cos(a1) * r0, math.sin(a1) * r0, 0), (math.cos(a1) * r1, math.sin(a1) * r1, 8), (math.cos(a0) * r1, math.sin(a0) * r1, 8)]
    f.append((n, n + 1, n + 2, n + 3))
    u.append(((i / SEG, 0), ((i + 1) / SEG, 0), ((i + 1) / SEG, 1), (i / SEG, 1)))
make('beam_fx', v, f, u, 'beam.png', 3)
# 火星 / 萤火虫：一团小亮片，半径 1
v, f, u = [], [], []
for i in range(70):
    th, ph = rnd.uniform(0, math.tau), rnd.uniform(0, math.pi)
    rr = rnd.uniform(.1, 1)
    cx, cy, cz = rr * math.sin(ph) * math.cos(th), rr * math.sin(ph) * math.sin(th), rnd.uniform(0, 1.8)
    s = rnd.uniform(.025, .05)
    a = rnd.uniform(0, math.pi)
    dx, dy = math.cos(a) * s, math.sin(a) * s
    n = len(v)
    v += [(cx - dx, cy - dy, cz - s), (cx + dx, cy + dy, cz - s), (cx + dx, cy + dy, cz + s), (cx - dx, cy - dy, cz + s)]
    f.append((n, n + 1, n + 2, n + 3))
    u.append(((0, 0), (1, 0), (1, 1), (0, 1)))
make('spark_fx', v, f, u, 'spark.png', 3)
