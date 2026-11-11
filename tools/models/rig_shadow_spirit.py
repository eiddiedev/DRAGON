"""Build a lightweight spectral rig while preserving the approved mesh and materials."""
from pathlib import Path
import bpy, math, json
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'assets/tripo/approved_batch'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(OUT/'shadow_spirit_source.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
# Source faces +X, lateral axis Y, up Z. Coordinates are in model units.
bones=[('Root',(0,0,.44),(0,0,.53),None),('Chest',(0,0,.49),(0,0,.68),'Root'),('Head',(0,0,.68),(0,0,.92),'Chest'),('Tail_01',(0,0,.49),(0,-.06,.31),'Root'),('Tail_02',(0,-.06,.31),(0,-.05,.14),'Tail_01'),('Tail_03',(0,-.05,.14),(0,.09,.08),'Tail_02')]
for side,sign in [('L',-1),('R',1)]:
 bones.extend([(f'UpperArm_{side}',(0,sign*.13,.63),(0,sign*.28,.46),'Chest'),(f'Forearm_{side}',(0,sign*.28,.46),(.01,sign*.41,.34),f'UpperArm_{side}'),(f'Hand_{side}',(.01,sign*.41,.34),(.01,sign*.49,.26),f'Forearm_{side}'),(f'Cape_{side}',(-.06,sign*.13,.59),(-.06,sign*.14,.39),'Chest')])
data=bpy.data.armatures.new('ShadowSpiritSkeleton');arm=bpy.data.objects.new('ShadowSpiritRig',data);bpy.context.collection.objects.link(arm);bpy.context.view_layer.objects.active=arm;arm.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
for name,h,t,parent in bones:
 b=data.edit_bones.new(name);b.head=h;b.tail=t
 if parent:b.parent=data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def dist(p,h,t):
 h,t=Vector(h),Vector(t);v=t-h;q=max(0,min(1,(p-h).dot(v)/v.length_squared));return (p-h-q*v).length
bd={n:(h,t) for n,h,t,_ in bones}
for mesh in meshes:
 groups={n:mesh.vertex_groups.new(name=n) for n in bd}
 for v in mesh.data.vertices:
  p=mesh.matrix_world@v.co;x,y,z=p;side='R' if y>=0 else 'L'
  arm_mix=smooth(.16,.25,abs(y))*(1-smooth(.65,.74,z))*max(smooth(.23,.33,z),smooth(.27,.34,abs(y)))
  core_names=['Chest','Tail_01','Tail_02','Tail_03',f'Cape_{side}']
  core={n:1/(dist(p,*bd[n])+.025)**4 for n in core_names};total=sum(core.values());weights={n:w/total*(1-arm_mix) for n,w in core.items()}
  names=[f'UpperArm_{side}',f'Forearm_{side}',f'Hand_{side}'];aw={n:1/(dist(p,*bd[n])+.025)**4 for n in names};total=sum(aw.values())
  for n,w in aw.items():weights[n]=w/total*arm_mix
  head_mix=smooth(.63,.75,z)
  weights={n:w*(1-head_mix) for n,w in weights.items()};weights['Head']=head_mix
  kept=sorted(weights.items(),key=lambda t:t[1],reverse=True)[:4];s=sum(w for _,w in kept)
  for n,w in kept:
   if w>0:groups[n].add([v.index],w/s,'REPLACE')
 mod=mesh.modifiers.new('Spectral Skin','ARMATURE');mod.object=arm;mesh.parent=arm
scene=bpy.context.scene;scene.render.fps=30
arm.animation_data_create();actions=[]
for name,seconds,amp in [('Idle',4.0,1.0),('FloatMove',2.4,1.2)]:
 action=bpy.data.actions.new(name);arm.animation_data.action=action;frames=round(seconds*30)
 for f in range(frames+1):
  phase=2*math.pi*f/frames
  for p in arm.pose.bones:p.rotation_mode='XYZ';p.location=(0,0,0);p.rotation_euler=(0,0,0)
  # Root local Y is world Z.
  arm.pose.bones['Root'].location.y=.018*math.sin(phase)
  arm.pose.bones['Chest'].rotation_euler.y=.025*math.sin(phase)
  arm.pose.bones['Head'].rotation_euler.y=.025*math.sin(phase-.5)
  for i,n in enumerate(['Tail_01','Tail_02','Tail_03']):arm.pose.bones[n].rotation_euler.z=amp*.055*math.sin(phase-i*.65)
  for side,sign in [('L',-1),('R',1)]:
   arm.pose.bones[f'UpperArm_{side}'].rotation_euler.z=sign*amp*.04*math.sin(phase-.4)
   arm.pose.bones[f'Forearm_{side}'].rotation_euler.z=sign*amp*.03*math.sin(phase-.9)
   arm.pose.bones[f'Hand_{side}'].rotation_euler.z=sign*.035*math.sin(phase-1.2)
   arm.pose.bones[f'Cape_{side}'].rotation_euler.x=amp*.04*math.sin(phase-sign*.5)
  for p in arm.pose.bones:
   p.keyframe_insert('location',frame=f);p.keyframe_insert('rotation_euler',frame=f)
 track=arm.animation_data.nla_tracks.new();track.name=name;track.strips.new(name,0,action);track.mute=True;actions.append(action)
arm.animation_data.action=actions[0];scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'shadow_spirit_rig_edit.blend'))
bpy.ops.export_scene.gltf(filepath=str(OUT/'shadow_spirit_rigged.glb'),export_format='GLB',export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_frame_range=False)
print('RIG_COMPLETE',len(bones),[a.name for a in actions])
