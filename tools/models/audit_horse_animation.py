import bpy,json,math
from pathlib import Path
R=Path('/Users/bytedance/Documents/ChatGPT/DRAGON/assets/tripo/approved_batch')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'horse_refined_v1.glb'))
a=next(o for o in bpy.data.objects if o.type=='ARMATURE');m=next(o for o in bpy.data.objects if o.type=='MESH' and o.find_armature()==a)
for t in a.animation_data.nla_tracks:t.mute=True
feet=[('LF','tripo::0_Left_Limb_2',.75),('RF','bone_16',.25),('LH','tripo::1_Left_Limb_3',0),('RH','tripo::0_Right_Limb_2',.5)]
# Bottom vertices of each hoof selected in bind pose coordinates.
sets={}
for lab,b,phase in feet:
 pos=a.data.bones[b].head_local
 ids=[v.index for v in m.data.vertices if (m.matrix_world@v.co).z<.035 and ((m.matrix_world@v.co)-pos).xy.length<.065]
 sets[lab]=ids
report={}
for act in bpy.data.actions:
 a.animation_data.action=act;start,end=act.frame_range;positions=[];bottoms=[];scales=[]
 for f in [start+(end-start)*i/96 for i in range(97)]:
  bpy.context.scene.frame_set(math.floor(f),subframe=f-math.floor(f));dg=bpy.context.evaluated_depsgraph_get();em=m.evaluated_get(dg).to_mesh()
  coords=[m.matrix_world@v.co for v in em.vertices];positions.append(coords)
  bottoms.append({lab:min(coords[i].z for i in ids) for lab,ids in sets.items()})
  scales.extend(abs(c-1) for p in a.pose.bones for c in p.scale)
  m.evaluated_get(dg).to_mesh_clear()
 delta=max((x-y).length for x,y in zip(positions[0],positions[-1]))
 report[act.name]={'duration_s':(end-start)/bpy.context.scene.render.fps,'loop_max_vertex_delta':delta,'max_bone_scale_deviation':max(scales),'hoof_min_z':{lab:min(v[lab] for v in bottoms) for lab,_,_ in feet},'hoof_max_z':{lab:max(v[lab] for v in bottoms) for lab,_,_ in feet}}
(R/'horse_animation_qa.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
