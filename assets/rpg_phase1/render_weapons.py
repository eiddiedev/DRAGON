import bpy,sys,math
from mathutils import Vector
from pathlib import Path
base=Path('/Users/bytedance/Documents/ChatGPT/DRAGON')
for name in ['sword','staff','bow']:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(base/'assets/tripo/approved_batch'/f'{name}_source.glb'))
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=8;s.render.resolution_x=600;s.render.resolution_y=600;s.render.resolution_percentage=100
 verts=[ob.matrix_world@Vector(c) for ob in s.objects if ob.type=='MESH' for c in ob.bound_box];lo=Vector(tuple(min(v[i] for v in verts) for i in range(3)));hi=Vector(tuple(max(v[i] for v in verts) for i in range(3)));at=(lo+hi)*.5
 bpy.ops.object.camera_add(location=at+Vector((2,-3,1.5)));cam=bpy.context.object;cam.rotation_euler=(at-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.25;s.camera=cam
 bpy.ops.object.light_add(type='SUN',location=(3,-4,6));bpy.context.object.data.energy=3;bpy.context.object.rotation_euler=(.4,-.5,-.6)
 s.world=bpy.data.worlds.new("World");s.world.color=(.5,.5,.5);s.render.filepath=str(base/'assets/rpg_phase1'/f'{name}-source.png');bpy.ops.render.render(write_still=True)
