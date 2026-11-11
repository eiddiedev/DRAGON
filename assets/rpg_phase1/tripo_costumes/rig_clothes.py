import bpy,sys,json,math,bmesh,shutil
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];kind=args[0];res=Path(args[1]);D=Path('/Users/bytedance/Documents/ChatGPT/DRAGON/assets/rpg_phase1/tripo_costumes');work=res/'blender';work.mkdir(exist_ok=True)
source=res/'topology/model.glb'
if not (work/'source.glb').exists():shutil.copy2(source,work/'source.glb')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(work/'source.glb'));obs=[o for o in bpy.context.scene.objects if o.type=='MESH']
for ob in obs:
 bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);ob.select_set(False)
# These source landmarks were chosen from each generated mesh's front/back view, not a generic human auto-rig.
configs={
 'mage':dict(hip=.49,chest=.64,neck=.74,shoulder=(.12,0,.65),elbow=(.23,0,.585),wrist=(.315,0,.53),knee=(.10,0,.27),foot=(.10,0,.045),cut=.322,hat=.80,depth=.65),
 'ranger':dict(hip=.49,chest=.65,neck=.75,shoulder=(.13,0,.67),elbow=(.265,0,.60),wrist=(.365,0,.54),knee=(.12,0,.20),foot=(.12,0,.045),cut=.371,hat=.73,depth=.65),
 'warrior':dict(hip=.28,chest=.68,neck=.95,shoulder=(.24,0,.77),elbow=(.36,0,.52),wrist=(.405,0,.29),knee=(.15,0,.03),foot=(.15,0,-.3),cut=.46,hat=2,depth=.52)}
c=configs[kind];rest=json.loads((D/'avatar-rest-rig.json').read_text());target={k:Vector((-v['position']['x'],-v['position']['z'],v['position']['y']))for k,v in rest.items()}
src={'Hips':Vector((0,0,c['hip'])),'Spine':Vector((0,0,(c['hip']+c['chest'])*.5)),'Chest':Vector((0,0,c['chest'])),'UpperChest':Vector((0,0,c['chest']+.04)),'Neck':Vector((0,0,c['neck'])),'Head':Vector((0,0,c['neck']+.03))}
for side,sign in [('Left',1),('Right',-1)]:
 for n,key in [('UpperArm','shoulder'),('LowerArm','elbow'),('Hand','wrist'),('LowerLeg','knee'),('Foot','foot')]:
  p=Vector(c[key]);p.x*=sign;src[side+n]=p
 src[side+'UpperLeg']=Vector((sign*.10,0,c['hip']-.025))
ends={'Hips':'Spine','Spine':'Chest','Chest':'UpperChest','UpperChest':'Neck','Neck':'Head'}
for side in ['Left','Right']:
 ends.update({side+'UpperArm':side+'LowerArm',side+'LowerArm':side+'Hand',side+'UpperLeg':side+'LowerLeg',side+'LowerLeg':side+'Foot'})
# Remove generated bare hands beyond the visible cuff. Keep mage cuffs, ranger bracers and armour gauntlets.
removed=0
for ob in obs:
 bm=bmesh.new();bm.from_mesh(ob.data);bad=[]
 uv=bm.loops.layers.uv.active
 image=next((n.image for n in ob.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image and ('base' in n.image.name.lower()or 'color' in n.image.name.lower())),None)
 if image is None:image=next((n.image for n in ob.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None)
 pixels=list(image.pixels)if image else [];iw,ih=image.size if image else (0,0)
 for f in bm.faces:
  q=f.calc_center_median()
  skin=False
  if uv and image and kind in ['mage','ranger'] and abs(q.x)>c['cut']-.07 and .43<q.z<.63:
   co=sum((loop[uv].uv for loop in f.loops),Vector((0,0)))/len(f.loops);ix=int(co.x*iw)%iw;iy=int(co.y*ih)%ih;pix=(iy*iw+ix)*4;rr,gg,bb=pixels[pix:pix+3];skin=rr>.42 and gg>.22 and rr>gg*1.12 and rr>bb*1.28
  if skin:bad.append(f)
  elif kind in ['mage','ranger'] and abs(q.x)>c['cut'] and .43<q.z<.61:bad.append(f)
  elif kind=='ranger' and abs(q.x)<.065 and .72<q.z<.81 and q.y<-.035:bad.append(f)
  elif kind=='warrior' and abs(q.x)>.32 and q.z<.19:bad.append(f)
 removed+=len(bad);bmesh.ops.delete(bm,geom=bad,context='FACES');bm.to_mesh(ob.data);bm.free()
armdata=bpy.data.armatures.new('DragonOutfitSkeleton');arm=bpy.data.objects.new('DragonOutfitRig',armdata);bpy.context.collection.objects.link(arm);bpy.context.view_layer.objects.active=arm;arm.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for name,p in target.items():
 b=armdata.edit_bones.new(name);b.head=p;b.tail=target[ends[name]] if name in ends else p+Vector((0,0,.025))
 if (b.tail-b.head).length<.005:b.tail=b.head+Vector((0,0,.025))
 # Flat skeleton allows direct world-space humanoid retargeting without double transforms.
bpy.ops.object.mode_set(mode='OBJECT');arm.select_set(False)
def weights(p):
 if kind=='mage' and p.z>c['hat']:return {'Head':1}
 if kind=='ranger' and p.z>.73:
  t=max(0,min(1,(p.z-.73)/.09));return {'Neck':1-t,'Head':t}
 if p.z<c['hip']-.06:
  if kind=='mage':return {'Hips':1} # robe is cloth, not trousers; never split its centre between opposite legs
  if p.y>.055:return {'Hips':1} # cape follows pelvis; leg poses must not drag the back cloth sideways
  side='Left' if p.x>0 else 'Right'
  knee=c['knee'][2];t=max(0,min(1,(p.z-knee)/.08+.5))
  return {side+'UpperLeg':t,side+'LowerLeg':1-t}
 if abs(p.x)>c['shoulder'][0]*.82 and c['elbow'][2]-.13<p.z<c['shoulder'][2]+.055 and p.y<.11:
  side='Left' if p.x>0 else 'Right';e=c['elbow'][0];span=.045
  t=max(0,min(1,(abs(p.x)-e)/span+.5));return {side+'UpperArm':1-t,side+'LowerArm':t}
 levels=[('Hips',c['hip']),('Spine',(c['hip']+c['chest'])*.5),('Chest',c['chest']),('UpperChest',c['chest']+.04),('Neck',c['neck'])]
 if p.z<=levels[0][1]:return {'Hips':1}
 for (n,a),(m,b)in zip(levels,levels[1:]):
  if p.z<=b:
   t=max(0,min(1,(p.z-a)/(b-a)));return {n:1-t,m:t}
 return {'Neck':1}
def fitted(p,n):
 if kind=='ranger' and p.z>.73:
  return Vector((p.x*1.18,p.y*1.25-.025,.50+(p.z-.73)*1.48))
 if n=='Head':return Vector((p.x*.90,p.y*.90,.75+(p.z-.81)*.90))
 if kind=='mage'and n=='Hips'and p.z<c['hip']:
  return Vector((p.x*.82,p.y*.90,.32+(p.z-c['hip'])*.60))
 a=src[n];b=target[n];q=p-a
 if n in ends:
  va=src[ends[n]]-a;vb=target[ends[n]]-b
  rot=va.rotation_difference(vb);length=vb.length/va.length
  # Preserve garment thickness while matching the much shorter chibi limbs.
  axis=va.normalized();along=axis*q.dot(axis);cross=q-along
  return b+rot@(along*length+cross*(.94 if kind!='warrior'else .58))
 return b+q*(.94 if kind!='warrior'else .58)
report={'kind':kind,'removedFaces':removed,'weightsMax':2,'bones':len(target),'meshes':[]}
for ob in obs:
 groups={n:ob.vertex_groups.new(name=n)for n in target}
 for v in ob.data.vertices:
  w=weights(v.co);pos=Vector();total=sum(w.values())
  for name,value in w.items():
   if value>1e-6:pos+=fitted(v.co,name)*value/total;groups[name].add([v.index],value/total,'REPLACE')
  v.co=pos
 ob.data.update();mod=ob.modifiers.new('OutfitSkin','ARMATURE');mod.object=arm;ob.parent=arm
 report['meshes'].append({'vertices':len(ob.data.vertices),'faces':len(ob.data.polygons)})
# Store a reversible mother file, no generated baked animation.
bpy.ops.wm.save_as_mainfile(filepath=str(work/'rig.blend'))
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True)
for ob in obs:ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(work/'rigged.glb'),export_format='GLB',use_selection=True,export_skins=True,export_animations=False)
(work/'fit-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
