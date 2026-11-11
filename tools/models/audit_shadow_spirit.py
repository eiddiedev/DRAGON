"""Reload the exported skin; audit weights, loop closure, and surface stretching."""
import bpy,json,math
from pathlib import Path
R=Path(__file__).resolve().parents[2]/'assets/tripo/approved_batch'
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'shadow_spirit_rigged.glb'))
a=next(o for o in bpy.data.objects if o.type=='ARMATURE');m=next(o for o in bpy.data.objects if o.type=='MESH' and o.find_armature()==a)
for tr in a.animation_data.nla_tracks:tr.mute=True
edges=[(e.vertices[0],e.vertices[1],(m.data.vertices[e.vertices[0]].co-m.data.vertices[e.vertices[1]].co).length) for e in m.data.edges]
report={'bones':len(a.data.bones),'weight_sum_error':max(abs(sum(g.weight for g in v.groups)-1) for v in m.data.vertices),'max_influences':max(len(v.groups) for v in m.data.vertices),'clips':{}}
for act in bpy.data.actions:
 a.animation_data.action=act;start,end=act.frame_range;first=None;stretch=0;maxmovement=0
 for i in range(49):
  f=start+(end-start)*i/48;bpy.context.scene.frame_set(math.floor(f),subframe=f%1);dg=bpy.context.evaluated_depsgraph_get();ob=m.evaluated_get(dg);em=ob.to_mesh();vs=[v.co.copy() for v in em.vertices]
  if first is None:first=vs
  maxmovement=max(maxmovement,max((v-w).length for v,w in zip(vs,first)))
  worst=max((abs((vs[u]-vs[v]).length/d-1),u,v,d) for u,v,d in edges if d>.001)
  if worst[0]>stretch:
   stretch=worst[0];detail={'vertices':[list(m.data.vertices[k].co) for k in worst[1:3]],'length':worst[3],'frame':f}
  ob.to_mesh_clear()
 report['clips'][act.name]={'duration_s':(end-start)/bpy.context.scene.render.fps,'loop_vertex_error':max((v-w).length for v,w in zip(vs,first)),'max_edge_length_change_ratio':stretch,'max_vertex_movement':maxmovement,'worst_edge':detail}
(R/'shadow_spirit_qa.json').write_text(json.dumps(report,indent=2));print(json.dumps(report));assert report['weight_sum_error']<1e-5;assert report['max_influences']<=4;assert all(c['loop_vertex_error']<1e-5 for c in report['clips'].values())
