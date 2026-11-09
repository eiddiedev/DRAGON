# 用法：Blender --background --python world_terrain_export_v4.py -- <数据目录> [manifest 文件]
# 一个地块拆成多张子网格，每张有自己的材质和 1024 贴图（引擎把每张贴图压到 1024）。
# 原点在地块中心、海拔 0；Blender 的 +Y 是地图北边。法线统一从整块高度算，子块接缝不会有明暗线。
import json
import os
import sys

import bpy
import numpy as np

args = sys.argv[sys.argv.index('--') + 1:]
OUT = args[0]
MAN = args[1] if len(args) > 1 else 'manifest.json'
TILE = 64.0
for t in json.load(open(os.path.join(OUT, MAN))):
    name = t['name']
    d = os.path.join(OUT, name)
    hm = np.load(os.path.join(d, 'heights.npy'))
    SEG = hm.shape[0] - 1
    subs = t['subs']
    step = SEG // subs
    bpy.ops.wm.read_factory_settings(use_empty=True)
    cell = TILE / SEG
    gr, gc = np.gradient(hm, cell)  # 行向南为正，列向东为正
    nx, ny, nz = -gc, gr, np.ones_like(hm)  # Blender：x 东 y 北 z 上；行向南，所以 dh/dy=-gr
    ln = np.sqrt(nx * nx + ny * ny + 1)
    nx, ny, nz = nx / ln, ny / ln, nz / ln
    for iz in range(subs):      # iz 从南往北
        for ix in range(subs):
            r0 = SEG - (iz + 1) * step
            c0 = ix * step
            verts, faces, uvs, norms = [], [], [], []
            for r in range(step + 1):
                for c in range(step + 1):
                    R, C = r0 + r, c0 + c
                    verts.append((C / SEG * TILE - TILE / 2, (1 - R / SEG) * TILE - TILE / 2, float(hm[R, C])))
            for r in range(step):
                for c in range(step):
                    a = r * (step + 1) + c
                    faces.append((a, a + step + 1, a + step + 2, a + 1))
            me = bpy.data.meshes.new(f's{ix}{iz}')
            me.from_pydata(verts, [], faces)
            uv = me.uv_layers.new(name='UV')
            ht = .5 / 1024
            for p in me.polygons:
                for li in p.loop_indices:
                    v = me.loops[li].vertex_index
                    r, c = v // (step + 1), v % (step + 1)
                    uv.data[li].uv = (ht + c / step * (1 - 2 * ht), 1 - ht - r / step * (1 - 2 * ht))
                    R, C = r0 + r, c0 + c
                    norms.append((float(nx[R, C]), float(ny[R, C]), float(nz[R, C])))
            me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
            me.update()
            me.normals_split_custom_set(norms)
            ob = bpy.data.objects.new(f's{ix}{iz}', me)
            bpy.context.scene.collection.objects.link(ob)
            m = bpy.data.materials.new(f'm{ix}{iz}')
            m.use_nodes = True
            pb = m.node_tree.nodes['Principled BSDF']
            pb.inputs['Roughness'].default_value = .95
            pb.inputs['Specular IOR Level'].default_value = .1
            tx = m.node_tree.nodes.new('ShaderNodeTexImage')
            tx.image = bpy.data.images.load(os.path.join(d, f'alb_{ix}_{iz}.jpg'))
            tx.extension = 'EXTEND'
            m.node_tree.links.new(tx.outputs['Color'], pb.inputs['Base Color'])
            me.materials.append(m)
            ob.select_set(True)
    path = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_normals=True,
                              export_image_format='JPEG', export_jpeg_quality=88)
    print('BUILT', name, 'tris', SEG * SEG * 2, 'subs', subs, 'MB', round(os.path.getsize(path) / 1e6, 2), flush=True)
