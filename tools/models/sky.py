# 用法：Blender --background --python sky.py -- <贴图目录> <输出目录>
# 天空模型：穹顶（内表面）、三层云雾漩涡圆盘、月亮圆盘。材质用发光贴图，不受夜间光照影响。
# 圆盘立在 XZ 平面，正反两面都有，原点在圆心。
import math
import os
import sys

import bpy

TEX, OUT = sys.argv[sys.argv.index('--') + 1:][:2]
os.makedirs(OUT, exist_ok=True)


def material(name, image_file, alpha):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    pb = m.node_tree.nodes['Principled BSDF']
    tx = m.node_tree.nodes.new('ShaderNodeTexImage')
    tx.image = bpy.data.images.load(os.path.join(TEX, image_file))
    links = m.node_tree.links
    links.new(tx.outputs['Color'], pb.inputs['Base Color'])
    links.new(tx.outputs['Color'], pb.inputs['Emission Color'])
    pb.inputs['Emission Strength'].default_value = 1.0
    pb.inputs['Roughness'].default_value = 1.0
    if alpha:
        links.new(tx.outputs['Alpha'], pb.inputs['Alpha'])
        m.blend_method = 'BLEND'
    return m


def export(name, verts, faces, uvs, mat):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name='UV')
    for p in me.polygons:
        for li in p.loop_indices:
            uv.data[li].uv = uvs[me.loops[li].vertex_index]
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(mat())
    ob.select_set(True)
    path = os.path.join(OUT, name + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True,
                              export_image_format='AUTO')
    print('BUILT', name, 'tris', sum(len(f) - 2 for f in faces), 'MB', round(os.path.getsize(path) / 1e6, 2), flush=True)


def dome(name='sky_dome2', image='sky_dome.jpg'):
    """单位球（半径 1），法线朝内。u=0.5 对着 +Y，v=1 是天顶。"""
    nu, nv = 72, 36
    verts, uvs, faces = [], [], []
    for j in range(nv + 1):
        el = math.pi * (j / nv - .5)
        for i in range(nu + 1):
            u = i / nu
            az = (u - .5) * 2 * math.pi
            verts.append((math.cos(el) * math.sin(az), math.cos(el) * math.cos(az), math.sin(el)))
            uvs.append((u, j / nv))
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            b, c, d = a + 1, a + nu + 2, a + nu + 1
            faces.append((a, b, c, d))  # 从球内看是逆时针
    export(name, verts, faces, uvs, lambda: material(name, image, False))


def disc(name, image_file, seg=48):
    """半径 1 的圆盘，正反两面。"""
    verts, uvs, faces = [(0.0, 0.0, 0.0)], [(.5, .5)], []
    for i in range(seg):
        t = i / seg * 2 * math.pi
        x, z = math.cos(t), math.sin(t)
        verts.append((x, 0.0, z))
        uvs.append((.5 + x / 2, .5 + z / 2))
    for i in range(seg):
        a, b = 1 + i, 1 + (i + 1) % seg
        faces.append((0, a, b))
        faces.append((0, b, a))
    export(name, verts, faces, uvs, lambda: material(name, image_file, True))


only = sys.argv[sys.argv.index('--') + 3:]
if not only or 'sky_dome2' in only:
    dome()
if not only or 'sky_day' in only:
    dome('sky_day', 'sky_day.jpg')
for layer in 'abc':
    if not only or 'sky_swirl_' + layer in only:
        disc('sky_swirl_' + layer, 'sky_swirl_' + layer + '.png')
if not only or 'sky_moon2' in only:
    disc('sky_moon2', 'sky_moon.png', 48)
