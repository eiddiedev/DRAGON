"""Render named clips from the working dragon .blend for deformation review."""
import bpy
import sys
import math
from pathlib import Path
from mathutils import Vector

folder=Path(sys.argv[sys.argv.index('--')+1]).resolve()
bpy.ops.wm.open_mainfile(filepath=str(folder/'dragon_rig.blend'))
scene=bpy.context.scene;arm=bpy.data.objects['dragon_rig']
scene.render.engine='CYCLES';scene.cycles.samples=20
scene.render.resolution_x=1100;scene.render.resolution_y=850;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
world=bpy.data.worlds.new('Studio');world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.35,.43,.55,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.65
scene.world=world
bpy.ops.mesh.primitive_plane_add(size=160,location=(0,0,-.12))
floor=bpy.context.object;floor.name='Preview ground'
mat=bpy.data.materials.new('Ground');mat.diffuse_color=(.12,.15,.18,1)
floor.data.materials.append(mat)
light=bpy.data.objects.new('Key',bpy.data.lights.new('Key','AREA'));scene.collection.objects.link(light)
light.location=(25,-35,55);light.data.energy=45000;light.data.shape='DISK';light.data.size=35
light.rotation_euler=(Vector((0,-10,12))-light.location).to_track_quat('-Z','Y').to_euler()
fill=bpy.data.objects.new('Rim',bpy.data.lights.new('Rim','AREA'));scene.collection.objects.link(fill)
fill.location=(-25,10,35);fill.data.energy=30000;fill.data.size=25
fill.rotation_euler=(Vector((0,0,12))-fill.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));scene.collection.objects.link(cam);scene.camera=cam
cam.location=(48,-76,38);cam.data.type='ORTHO';cam.data.ortho_scale=65
cam.rotation_euler=(Vector((0,-4,12))-cam.location).to_track_quat('-Z','Y').to_euler()
for clip,frame in [('perch',45),('perch',135),('idle',45),('takeoff',30),('fly',10),('fly',31),('land',40),('land',69),('land',80)]:
    arm.animation_data.action=bpy.data.actions[clip]
    scene.frame_set(frame)
    scene.render.filepath=str(folder/f'pose_{clip}_{frame}.png')
    bpy.ops.render.render(write_still=True)
print('POSE_PREVIEWS_DONE')
