import bpy,math,json
from mathutils import Vector
from pathlib import Path
R=Path('/Users/bytedance/Documents/ChatGPT/DRAGON/assets/tripo/approved_batch');O=R.parent.parent/'interactions_v1'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'horse_riding_v2.glb'))
a=next(o for o in bpy.data.objects if o.type=='ARMATURE')
for t in a.animation_data.nla_tracks:t.mute=True
a.animation_data.action=next(x for x in bpy.data.actions if x.name.startswith('Run'))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='TEXTURE';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.background_type='WORLD';sc.world=bpy.data.worlds.new('PreviewWorld');sc.world.color=(.15,.15,.15);sc.render.resolution_x=600;sc.render.resolution_y=500;sc.render.resolution_percentage=100
bpy.ops.object.camera_add(location=(2.8,-1.5,1.3));c=bpy.context.object;c.rotation_euler=(Vector((0,0,.5))-c.location).to_track_quat('-Z','Y').to_euler();c.data.type='ORTHO';c.data.ortho_scale=1.5;sc.camera=c
for f in [0,4,8,12]:
 sc.frame_set(f);sc.render.filepath=str(O/f'horse-run-{f}.png');bpy.ops.render.render(write_still=True)
