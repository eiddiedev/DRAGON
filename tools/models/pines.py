# 用法：Blender --background --python pines.py -- <贴图> <输出目录>（先跑 pines_place.py）
# 大片松林：每棵树 4 张交叉面片，法线朝外做成蓬松感；按区域分成几个模型，便于视锥剔除。
import json
import math
import os
import random
import sys

import bpy
from mathutils import Vector

TEX, OUT = sys.argv[sys.argv.index('--') + 1:][:2]
trees = json.load(open(os.path.join(OUT, 'trees.json')))
rnd = random.Random(13)
# 分区：按 x、z 四等分
chunks = {}
for t in trees:
    chunks.setdefault((int(t[0] // 128), int(t[1] // 128)), []).append(t)
places = []
for (cx, cz), ts in chunks.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ox, oz = (cx + .5) * 128, (cz + .5) * 128
    verts, faces, uvs, norms = [], [], [], []
    for (x, z, h) in ts:
        k = rnd.randrange(4)
        hgt = rnd.uniform(6.5, 13.5)
        wid = hgt * rnd.uniform(.46, .58)
        a0 = rnd.uniform(0, math.pi)
        px, py, pz = x - ox, z - oz, h - .35
        for i in range(4):
            a = a0 + i * math.pi / 4
            dx, dy = math.cos(a) * wid / 2, math.sin(a) * wid / 2
            n = len(verts)
            verts += [(px - dx, py - dy, pz), (px + dx, py + dy, pz), (px + dx, py + dy, pz + hgt), (px - dx, py - dy, pz + hgt)]
            faces.append((n, n + 1, n + 2, n + 3))
            u0, u1 = k / 4 + .002, (k + 1) / 4 - .002
            uvs.append(((u0, 0), (u1, 0), (u1, 1), (u0, 1)))
            for (vx, vy, up) in ((-dx, -dy, -.15), (dx, dy, -.15), (dx, dy, 1), (-dx, -dy, 1)):
                v = Vector((vx / (wid / 2), vy / (wid / 2), up)).normalized()
                norms.append(tuple(v))
    me = bpy.data.meshes.new('f')
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name='UV')
    for p, q in zip(me.polygons, uvs):
        for li, c in zip(p.loop_indices, q):
            uv.data[li].uv = c
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.update()
    me.normals_split_custom_set(norms)
    ob = bpy.data.objects.new('f', me)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    m = bpy.data.materials.new('pine')
    m.use_nodes = True
    m.blend_method = 'CLIP'
    m.alpha_threshold = .42
    m.use_backface_culling = False
    pb = m.node_tree.nodes['Principled BSDF']
    pb.inputs['Roughness'].default_value = .95
    pb.inputs['Specular IOR Level'].default_value = 0
    tx = m.node_tree.nodes.new('ShaderNodeTexImage')
    tx.image = bpy.data.images.load(TEX)
    m.node_tree.links.new(tx.outputs['Color'], pb.inputs['Base Color'])
    m.node_tree.links.new(tx.outputs['Alpha'], pb.inputs['Alpha'])
    me.materials.append(m)
    name = f'pines_{cx}_{cz}'
    path_ = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=path_, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_normals=True, export_image_format='AUTO')
    print('BUILT', name, 'trees', len(ts), 'tris', len(faces) * 2, 'MB', round(os.path.getsize(path_) / 1e6, 2), flush=True)
    places.append(dict(name=name, x=ox, z=oz, n=len(ts)))
json.dump(places, open(os.path.join(OUT, 'pines.json'), 'w'), indent=1)
