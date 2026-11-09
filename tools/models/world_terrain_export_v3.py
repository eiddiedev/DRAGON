# 用法：Blender --background --python world_terrain_export.py -- <数据目录>
# 把每块地形导出成 GLB。原点在地块中心、海拔 0；Blender 的 +Y 是地图北边。
import json
import os
import sys

import bpy
import numpy as np

OUT = sys.argv[sys.argv.index('--') + 1]
TILE = 64.0
MAN = sys.argv[sys.argv.index('--') + 2] if len(sys.argv) > sys.argv.index('--') + 2 else 'manifest.json'
for t in json.load(open(os.path.join(OUT, MAN))):
    name = t['name']
    d = os.path.join(OUT, name)
    hm = np.load(os.path.join(d, 'heights.npy'))
    SEG = hm.shape[0] - 1
    bpy.ops.wm.read_factory_settings(use_empty=True)
    verts = [(c / SEG * TILE - TILE / 2, (1 - r / SEG) * TILE - TILE / 2, float(hm[r, c])) for r in range(SEG + 1) for c in range(SEG + 1)]
    faces = []
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
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    pb = m.node_tree.nodes['Principled BSDF']
    pb.inputs['Roughness'].default_value = .95
    tx = m.node_tree.nodes.new('ShaderNodeTexImage')
    tx.image = bpy.data.images.load(os.path.join(d, 'albedo.png'))
    m.node_tree.links.new(tx.outputs['Color'], pb.inputs['Base Color'])
    np_ = os.path.join(d, 'normal.png')
    if os.path.exists(np_):
        nt = m.node_tree.nodes.new('ShaderNodeTexImage')
        nt.image = bpy.data.images.load(np_)
        nt.image.colorspace_settings.name = 'Non-Color'
        nm = m.node_tree.nodes.new('ShaderNodeNormalMap')
        m.node_tree.links.new(nt.outputs['Color'], nm.inputs['Color'])
        m.node_tree.links.new(nm.outputs['Normal'], pb.inputs['Normal'])
    me.materials.append(m)
    ob.select_set(True)
    path = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                              export_image_format='JPEG', export_jpeg_quality=85, export_tangents=True)
    print('BUILT', name, 'tris', SEG * SEG * 2, 'MB', round(os.path.getsize(path) / 1e6, 2), flush=True)
