# 用法：Blender --background --python detail_quad.py -- <目录>
# 只是一张小方片，用来把细节贴图带进工程；脚本运行时取走贴图，方片本身隐藏。
import os
import sys

import bpy

D = sys.argv[sys.argv.index('--') + 1]
for name in ('detail_grass', 'detail_rock'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-.5, -.5, 0), (.5, -.5, 0), (.5, .5, 0), (-.5, .5, 0)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name='UV')
    for li, c in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = c
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    pb = m.node_tree.nodes['Principled BSDF']
    tx = m.node_tree.nodes.new('ShaderNodeTexImage')
    tx.image = bpy.data.images.load(os.path.join(D, name + '.png'))
    m.node_tree.links.new(tx.outputs['Color'], pb.inputs['Base Color'])
    me.materials.append(m)
    p = os.path.join(D, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=p, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_image_format='JPEG', export_jpeg_quality=92)
    print('BUILT', name, round(os.path.getsize(p) / 1e6, 2), flush=True)
