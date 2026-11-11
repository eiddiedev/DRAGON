# 用法：Blender --background --python world_preview.py -- <输出 png> <相机x,y,z> <目标x,y,z> <lens>
# 把地形块和城堡 GLB 一起放进世界坐标渲染（Blender: x 东, y 北, z 高）。
import bpy, glob, json, math, os, sys
from mathutils import Euler, Vector
a = sys.argv[sys.argv.index('--') + 1:]
out = a[0]; cl = tuple(map(float, a[1].split(','))); tg = tuple(map(float, a[2].split(','))); lens = float(a[3])
R = '/Users/bytedance/Documents/ChatGPT/DRAGON/assets'
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene; s.render.engine = 'CYCLES'; s.cycles.device = 'CPU'; s.cycles.samples = 32
s.view_settings.view_transform = 'Standard'; s.render.resolution_x, s.render.resolution_y = 1280, 720
def imp(path, x, y, z=0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    for o in set(bpy.data.objects) - before:
        if o.parent is None:
            o.location = (x, y, z)
for t in json.load(open(R + '/terrain/world/manifest.json')):
    imp(f"{R}/terrain/world/{t['name']}.glb", t['x0'] + 32, t['z0'] + 32)
for n in ('walls', 'keep', 'library', 'towers'):
    imp(f'{R}/castle/castle_{n}.glb', 127, 173)
sea = bpy.data.meshes.new('sea'); sea.from_pydata([(-300,-300,27),(600,-300,27),(600,600,27),(-300,600,27)],[],[(0,1,2,3)])
so = bpy.data.objects.new('sea', sea); s.collection.objects.link(so)
m = bpy.data.materials.new('w'); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value = (.05,.32,.42,1); b.inputs['Roughness'].default_value = .25; sea.materials.append(m)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun','SUN')); sun.data.energy = 2.0; sun.data.color = (1,.95,.86); sun.data.angle = math.radians(5)
sun.rotation_euler = Euler((math.radians(40), 0, math.radians(90-30))); s.collection.objects.link(sun)
w = bpy.data.worlds.new('w'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.55,.75,.95,1); w.node_tree.nodes['Background'].inputs[1].default_value = .9; s.world = w
c = bpy.data.objects.new('c', bpy.data.cameras.new('c')); s.collection.objects.link(c); s.camera = c
c.data.lens = lens; c.location = cl; c.rotation_euler = (Vector(tg) - Vector(cl)).to_track_quat('-Z','Y').to_euler()
s.render.filepath = out; bpy.ops.render.render(write_still=True)
