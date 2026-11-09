# 用法：Blender --background --python grass.py -- <输出目录> <贴图>
# 三种草片：grass_a 纯草、grass_b 草夹小花、grass_c 紫花。原点在中心地面，世界坐标由摆放脚本决定。
import math
import os
import random
import sys

import bpy

OUT, TEX = sys.argv[sys.argv.index('--') + 1:][:2]
PATCH = 6.4   # 直径（米）。原来 4.2 米；做大以后边界才不明显
VARIANTS = {
    'grass_a': dict(band=0, cards=620, w=(.55, 1.0), h=(.26, .52)),
    'grass_b': dict(band=1, cards=620, w=(.55, 1.0), h=(.25, .48)),
    'grass_c': dict(band=2, cards=760, w=(.45, .85), h=(.24, .42)),
}
rnd = random.Random(3)
for name, v in VARIANTS.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    verts, faces, uvs = [], [], []
    for i in range(v['cards']):
        r = PATCH / 2 * rnd.random() ** .62   # 中间密、边缘稀，相邻草片的接缝才看不出来
        a = rnd.uniform(0, math.tau)
        cx, cy = r * math.cos(a), r * math.sin(a)
        ang = rnd.uniform(0, math.tau)
        edge = 1 - .8 * (r / (PATCH / 2)) ** 3   # 边缘的草矮下去，草片之间没有硬边
        w, h = rnd.uniform(*v['w']), rnd.uniform(*v['h']) * edge
        dx, dy = math.cos(ang) * w / 2, math.sin(ang) * w / 2
        n = len(verts)
        verts += [(cx - dx, cy - dy, -.06), (cx + dx, cy + dy, -.06), (cx + dx, cy + dy, h), (cx - dx, cy - dy, h)]
        faces.append((n, n + 1, n + 2, n + 3))
        # 在所在那一条上随机截一段
        bw = w * .34
        u0 = rnd.uniform(0, 1 - bw)
        top = 1 - v['band'] / 3
        bot = top - 1 / 3
        uvs.append(((u0, bot + .002), (u0 + bw, bot + .002), (u0 + bw, top - .002), (u0, top - .002)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name='UV')
    for p, q in zip(me.polygons, uvs):
        for li, c in zip(p.loop_indices, q):
            uv.data[li].uv = c
    # 法线朝上，草不会一面亮一面黑
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.select_set(True)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.blend_method = 'CLIP'
    m.alpha_threshold = .4
    m.use_backface_culling = False
    pb = m.node_tree.nodes['Principled BSDF']
    pb.inputs['Roughness'].default_value = .9
    pb.inputs['Specular IOR Level'].default_value = 0
    tx = m.node_tree.nodes.new('ShaderNodeTexImage')
    tx.image = bpy.data.images.load(TEX)
    m.node_tree.links.new(tx.outputs['Color'], pb.inputs['Base Color'])
    m.node_tree.links.new(tx.outputs['Alpha'], pb.inputs['Alpha'])
    me.materials.append(m)
    path = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True, export_image_format='AUTO')
    print('BUILT', name, 'tris', len(faces) * 2, 'MB', round(os.path.getsize(path) / 1e6, 2), flush=True)
