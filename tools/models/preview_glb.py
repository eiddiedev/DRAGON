# 用法：Blender --background --python preview_glb.py -- <glb> <输出前缀> <时间秒,逗号分隔> <机位文件.json> [带地形:ox,oz,x0,x1,z0,z1]
# 离线渲染 GLB 的预览图，带动画，可选把真实地形一起放进去。
import json, math, os, sys
import bpy
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, prefix, times, cams = a[0], a[1], [float(x) for x in a[2].split(',')], json.load(open(a[3]))
bpy.ops.wm.read_factory_settings(use_empty=True)
for g_ in glb.split(','):
    bpy.ops.import_scene.gltf(filepath=g_)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = cams[0].get('samples', 24) if cams else 24
scene.cycles.use_denoising = False
scene.view_settings.view_transform = 'Standard'
if len(a) > 4:
    ox, oz, x0, x1, z0, z1 = [float(x) for x in a[4].split(',')]
    H = np.load('/Users/a1234/Documents/awesomeWRLD/assets/terrain/v3/base_heights.npy')
    verts, faces = [], []
    xs = range(int(x0), int(x1)); zs = range(int(z0), int(z1))
    w = len(xs)
    for z in zs:
        for x in xs:
            verts.append((x - ox, z - oz, float(H[z, x])))
    for j in range(len(zs) - 1):
        for i in range(w - 1):
            faces.append((j * w + i, j * w + i + 1, (j + 1) * w + i + 1, (j + 1) * w + i))
    me = bpy.data.meshes.new('t'); me.from_pydata(verts, [], faces); me.update()
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    ob = bpy.data.objects.new('t', me); scene.collection.objects.link(ob)
    m = bpy.data.materials.new('s'); m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.72, .74, .8, 1)
    me.materials.append(m)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.data.energy = 2.4
sun.rotation_euler = (math.radians(55), 0, math.radians(-30))
scene.collection.objects.link(sun)
wd = bpy.data.worlds.new('w'); wd.use_nodes = True
wd.node_tree.nodes['Background'].inputs[0].default_value = (.62, .72, .86, 1)
wd.node_tree.nodes['Background'].inputs[1].default_value = .9
scene.world = wd
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); scene.collection.objects.link(cam); scene.camera = cam
cam.data.clip_end = 5000
fps = scene.render.fps
for t in times:
    scene.frame_set(int(round(t * fps)))
    for c in cams:
        scene.render.resolution_x, scene.render.resolution_y = c.get('res', [1000, 700])
        cam.data.lens = c.get('lens', 40)
        cam.location = c['loc']
        cam.rotation_euler = (Vector(c['at']) - Vector(c['loc'])).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = f"{prefix}_{c['name']}_{t:g}.png"
        bpy.ops.render.render(write_still=True)
print('DONE')
