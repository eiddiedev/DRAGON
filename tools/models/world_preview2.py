# 用法：Blender --background --python world_preview2.py -- <输出 png> <相机x,y,z> <目标x,y,z> <lens> <day|night> [宽x高]
# 把新地形、哥特城堡、发光树和花海放进世界坐标渲染（Blender: x 东, y 北, z 高）。
import glob
import json
import math
import os
import sys

import bpy
from mathutils import Euler, Vector

a = sys.argv[sys.argv.index('--') + 1:]
out = a[0]
cl = tuple(map(float, a[1].split(',')))
tg = tuple(map(float, a[2].split(',')))
lens = float(a[3])
mode = a[4]
res = tuple(map(int, a[5].split('x'))) if len(a) > 5 else (1280, 800)
R = '/Users/bytedance/Documents/ChatGPT/DRAGON/assets'
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
s.render.engine = 'CYCLES'
s.cycles.device = 'CPU'
s.cycles.samples = 24
s.view_settings.view_transform = 'Standard'
s.render.resolution_x, s.render.resolution_y = res


def imp(path, x, y, z=0):
    if not os.path.exists(path):
        print('missing', path)
        return
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    for o in set(bpy.data.objects) - before:
        if o.parent is None:
            o.location = (x, y, z)


for t in json.load(open(R + '/terrain/world/manifest.json')):
    imp(f"{R}/terrain/world/{t['name']}.glb", t['x0'] + 32, t['z0'] + 32)
for n in ('main', 'towers', 'wall'):
    imp(f'{R}/gothic/gothic_{n}.glb', 127, 176)
place = R + '/night/placements.json'
if os.path.exists(place):
    for p in json.load(open(place)):
        imp(f"{R}/night/{p['name']}.glb", p['x'], p['z'], p['y'])
sea = bpy.data.meshes.new('sea')
sea.from_pydata([(-400, -400, 27), (700, -400, 27), (700, 700, 27), (-400, 700, 27)], [], [(0, 1, 2, 3)])
so = bpy.data.objects.new('sea', sea)
s.collection.objects.link(so)
m = bpy.data.materials.new('w')
m.use_nodes = True
b = m.node_tree.nodes['Principled BSDF']
b.inputs['Base Color'].default_value = (.03, .16, .26, 1) if mode == 'night' else (.05, .36, .5, 1)
b.inputs['Roughness'].default_value = .25
sea.materials.append(m)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
sun.rotation_euler = Vector((-.663, -.383, .643)).to_track_quat('Z', 'Y').to_euler()
s.collection.objects.link(sun)
w = bpy.data.worlds.new('w')
w.use_nodes = True
s.world = w
bg = w.node_tree.nodes['Background']
if mode == 'night':
    sun.data.energy, sun.data.color = .9, (.62, .72, 1)
    bg.inputs[0].default_value, bg.inputs[1].default_value = (.20, .15, .50, 1), .55
else:
    sun.data.energy, sun.data.color = 3.0, (1, .95, .86)
    bg.inputs[0].default_value, bg.inputs[1].default_value = (.55, .75, .98, 1), .9
c = bpy.data.objects.new('c', bpy.data.cameras.new('c'))
s.collection.objects.link(c)
s.camera = c
c.data.lens = lens
c.location = cl
c.rotation_euler = (Vector(tg) - Vector(cl)).to_track_quat('-Z', 'Y').to_euler()
s.render.filepath = out
bpy.ops.render.render(write_still=True)
