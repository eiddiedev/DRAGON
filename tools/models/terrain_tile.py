# 用法：Blender --background --python terrain_tile.py -- <数据目录> <x0> <z0> <size> <名称>
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Euler, Vector

args = sys.argv[sys.argv.index('--') + 1:]
d, X0, Z0, SIZE, name = args[0], float(args[1]), float(args[2]), float(args[3]), args[4]
hm = np.load(os.path.join(d, 'heights.npy'))
SEG = hm.shape[0] - 1
bpy.ops.wm.read_factory_settings(use_empty=True)
verts, faces, uvs = [], [], []
for r in range(SEG + 1):  # r=0 是北边
    for c in range(SEG + 1):
        # Blender: x 东, y 北, z 上；模型原点放在地块中心、海拔 0
        verts.append((c / SEG * SIZE - SIZE / 2, (1 - r / SEG) * SIZE - SIZE / 2, float(hm[r, c])))
for r in range(SEG):
    for c in range(SEG):
        a = r * (SEG + 1) + c
        faces.append((a, a + SEG + 1, a + SEG + 2, a + 1))
me = bpy.data.meshes.new(name)
me.from_pydata(verts, [], faces)
uv = me.uv_layers.new(name='UV')
for p in me.polygons:
    for li in p.loop_indices:
        v = me.loops[li].vertex_index
        r, c = v // (SEG + 1), v % (SEG + 1)
        uv.data[li].uv = (c / SEG, 1 - r / SEG)
me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
me.update()
ob = bpy.data.objects.new(name, me)
bpy.context.scene.collection.objects.link(ob)
img = bpy.data.images.load(os.path.join(d, 'albedo.png'))
m = bpy.data.materials.new(name + '_mat')
m.use_nodes = True
pb = m.node_tree.nodes['Principled BSDF']
pb.inputs['Roughness'].default_value = .95
t = m.node_tree.nodes.new('ShaderNodeTexImage')
t.image = img
m.node_tree.links.new(t.outputs['Color'], pb.inputs['Base Color'])
me.materials.append(m)
ob.select_set(True)
path = os.path.join(d, name + '.glb')
bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                          export_image_format='JPEG', export_jpeg_quality=85)
print('BUILT', name, 'tris', SEG * SEG * 2, 'MB', round(os.path.getsize(path) / 1e6, 2))
