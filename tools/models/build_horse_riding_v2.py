"""Correct Tripo quadruped hierarchy and bake deliberate in-place gait clips.
Run in Blender. Retains original mesh, UVs, textures and skin weights.
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/bytedance/Documents/ChatGPT/DRAGON')
OUT=ROOT/'assets/tripo/approved_batch'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(OUT/'horse_rigged_walk.glb'))
arm=next(o for o in bpy.data.objects if o.type=='ARMATURE')
arm.animation_data_clear()
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
bpy.context.view_layer.objects.active=arm;arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
arm.data.edit_bones['bone_22'].parent=arm.data.edit_bones['tripo::Spine_1']
bpy.ops.object.mode_set(mode='OBJECT')
# ankle-driving bone, hoof bone, phase offset (four-beat walking order)
LEGS=[('LF','tripo::0_Left_Limb_1','tripo::0_Left_Limb_2',.75),('RF','bone_15','bone_16',.25),('LH','tripo::1_Left_Limb_2','tripo::1_Left_Limb_3',0),('RH','tripo::0_Right_Limb_1','tripo::0_Right_Limb_2',.5)]
controls=[]
for label,end,foot,phase in LEGS:
 target=bpy.data.objects.new('target_'+label,None);bpy.context.collection.objects.link(target)
 target.location=arm.data.bones[foot].head_local
 c=arm.pose.bones[end].constraints.new('IK');c.target=target;c.chain_count=3;c.use_stretch=False;c.iterations=80
 controls.append((label,end,foot,phase,target,c))
for p in arm.pose.bones:p.rotation_mode='QUATERNION';p.ik_stretch=0
scene=bpy.context.scene;scene.render.fps=30
reports={};clips=[]
for name,duration,stride,lift in [('Idle',3.2,0,0),('Walk',1.0,.28,.06),('Trot',.65,.40,.10),('Run',.50,.48,.13)]:
 N=round(duration*30);samples=[];errors=[]
 for frame in range(N+1):
  for p in arm.pose.bones:p.matrix_basis.identity()
  phase=frame/N
  root=arm.pose.bones['tripo::Root']
  # Small whole-body breathing; no large vertical bounce.
  body_z=-.018 + (.0015*math.sin(2*math.pi*phase) if name=='Idle' else (.014*math.sin(2*math.pi*phase) if name=='Run' else .004*math.cos(4*math.pi*phase)))
  body_matrix=root.bone.matrix_local.copy()
  body_matrix.translation.z+=body_z
  root.matrix=body_matrix
  bpy.context.view_layer.update()
  for label,end,foot,offset,target,c in controls:
   if name=='Trot':offset=0 if label in ('LF','RH') else .5
   if name=='Run':offset={'LF':.12,'RF':0,'LH':.54,'RH':.65}[label]
   u=(phase+offset)%1;stance=.66 if name=='Walk' else .34 if name=='Run' else .5
   if not stride:dy=dz=0
   elif u<stance:dy=stride*(.5-u/stance);dz=0
   else:
    t=(u-stance)/(1-stance);smooth=t*t*(3-2*t)
    dy=stride*(-.5+smooth);dz=lift*math.sin(math.pi*t)**1.3
   target.location=arm.data.bones[foot].head_local+Vector((0,dy,dz))
  bpy.context.view_layer.update()
  for label,end,foot,offset,target,c in controls:
   p=arm.pose.bones[foot];m=arm.data.bones[foot].matrix_local.copy();m.translation=p.matrix.translation;p.matrix=m
  bpy.context.view_layer.update()
  matrices={p.name:p.matrix.copy() for p in arm.pose.bones}
  samples.append(matrices)
  errors.append(max((arm.pose.bones[foot].head-target.location).length for _,_,foot,_,target,_ in controls))
 for *_,c in controls:c.mute=True
 arm.animation_data_create();act=bpy.data.actions.new(name);arm.animation_data.action=act
 for frame,matrices in enumerate(samples):
  scene.frame_set(frame)
  for p in arm.pose.bones:
   p.matrix=matrices[p.name]
   bpy.context.view_layer.update()
   p.keyframe_insert('location',frame=frame);p.keyframe_insert('rotation_quaternion',frame=frame);p.keyframe_insert('scale',frame=frame)
 reports[name]={'duration_s':duration,'max_ankle_target_error':max(errors),'stride_model_units':stride,'ground_speed_model_units_per_s':stride/((.66 if name=='Walk' else .56)*duration) if stride else 0}
 track=arm.animation_data.nla_tracks.new();track.name=name;strip=track.strips.new(name,0,act);track.mute=True
 clips.append(act);arm.animation_data.action=None
 for *_,c in controls:c.mute=False
for *_,target,c in controls:
 for p in arm.pose.bones:
  if c in list(p.constraints):p.constraints.remove(c)
 bpy.data.objects.remove(target,do_unlink=True)
arm.animation_data.action=clips[1]
scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'horse_riding_v2.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'horse_riding_v2.glb'),export_format='GLB',export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_frame_range=False)
(OUT/'horse_riding_v2_report.json').write_text(json.dumps(reports,indent=2))
print(json.dumps(reports))
