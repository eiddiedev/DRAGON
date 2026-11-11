"""Blender: sculptural low-poly reeds, opaque geometry, rooted two-stage bend rig."""
import bpy,math,random,json
from pathlib import Path
from mathutils import Vector
O=Path('/Users/bytedance/Documents/ChatGPT/DRAGON/assets/reeds_v15');O.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);rng=random.Random(15)
v=[];f=[];colors=[]
def face(ids,c):f.append(ids);colors.append(c)
def tube(points,radii,c,sides=3):
 start=len(v)
 for p,r in zip(points,radii):
  for j in range(sides):v.append(tuple(Vector(p)+Vector((r*math.cos(j*math.tau/sides),r*math.sin(j*math.tau/sides),0))))
 for k in range(len(points)-1):
  for j in range(sides):
   a=start+k*sides+j;b=start+k*sides+(j+1)%sides;c0=a+sides;d=b+sides
   face((a,b,d,c0),c)
def spear(a,b,width,c):
 # Folded, volumetric four-sided tapered leaflet or seed branch, no alpha cards.
 a,b=Vector(a),Vector(b);axis=(b-a).normalized();side=axis.cross(Vector((0,0,1)))
 if side.length<.01:side=Vector((1,0,0))
 side.normalize();up=axis.cross(side).normalized();mid=a+(b-a)*.45;s=len(v)
 v.extend([tuple(a),tuple(mid+side*width),tuple(mid+up*width*.32),tuple(mid-side*width),tuple(mid-up*width*.32),tuple(b)])
 for j,k in [(1,2),(2,3),(3,4),(4,1)]:face((s,s+j,s+k),c);face((s+5,s+k,s+j),c)
# Eight rooted tufts, each with six curved, folded blades.
for k in range(8):
 angle=k*2.399;rad=.74*math.sqrt((k+.5)/8);x,y=rad*math.cos(angle),rad*math.sin(angle)
 for j in range(5):
  a=angle+j*1.257+rng.uniform(-.35,.35);h=rng.uniform(.7,1.25);reach=rng.uniform(.5,.85);w=rng.uniform(.012,.024)
  start=len(v);side=Vector((-math.sin(a),math.cos(a),0))
  for t,width in [(0,.2),(.25,.9),(.5,1),(.75,.65),(1,0)]:
   center=Vector((x+math.cos(a)*reach*t*t+.26*t*t,y+math.sin(a)*reach*t*t,h*(t-.22*t*t)))
   for off in [-1,0,1]:v.append(tuple(center+side*w*width*off+Vector((0,0,w*width*.25 if off==0 else 0))))
  for seg in range(4):
   for off in range(2):face((start+seg*3+off,start+seg*3+off+1,start+(seg+1)*3+off+1,start+(seg+1)*3+off),2+(k+j)%4)
 if k%2==0:
  h=rng.uniform(1.05,1.4)
  def p(t):return Vector((x+.36*t*t,y+.08*t*t,h*(t-.13*t*t)))
  tube([p(t) for t in [0,.4,.75,1]],[.008,.006,.004,.0015],1)
  for j in range(6):
   t=.82+j*.028;a=angle+j*2.4;start=p(t);end=start+Vector((math.cos(a)*.055,math.sin(a)*.055,.065))
   spear(start,end,.008,5+j%2)
me=bpy.data.meshes.new('reed_geometry');me.from_pydata(v,[],f);me.update();
for poly in me.polygons:poly.use_smooth=True
ob=bpy.data.objects.new('reed_clump',me);bpy.context.collection.objects.link(ob)
uv=me.uv_layers.new(name='palette');palette=[(.26,.21,.105,1),(.38,.29,.14,1),(.44,.34,.17,1),(.56,.43,.22,1),(.64,.51,.29,1),(.72,.6,.38,1),(.8,.7,.47,1)]
im=bpy.data.images.new('reed_palette',width=7,height=1);im.pixels=[c for col in palette for c in col];im.pack()
mat=bpy.data.materials.new('reed_opaque');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.88
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;tex.interpolation='Closest';mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);me.materials.append(mat)
for poly,idx in zip(me.polygons,colors):
 for li in poly.loop_indices:uv.data[li].uv=((idx+.5)/7,.5)
armdata=bpy.data.armatures.new('reed_bones');arm=bpy.data.objects.new('reed_rig',armdata);bpy.context.collection.objects.link(arm);arm.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for name,z0,z1,parent in [('root',0,.1,None),('reed_lower',.1,.45,'root'),('reed_upper',.45,1.1,'reed_lower')]:
 b=armdata.edit_bones.new(name);b.head=(0,0,z0);b.tail=(0,0,z1)
 if parent:b.parent=armdata.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT');ob.parent=arm;mod=ob.modifiers.new('ReedSkin','ARMATURE');mod.object=arm
vg={n:ob.vertex_groups.new(name=n) for n in ['root','reed_lower','reed_upper']}
for i,vertex in enumerate(me.vertices):
 z=vertex.co.z;lo=max(0,min(1,z/.4));hi=max(0,min(1,(z-.35)/.6))
 weights={'root':1-lo,'reed_lower':lo*(1-hi),'reed_upper':lo*hi}
 for n,w in weights.items():
  if w>0:vg[n].add([i],w,'REPLACE')
for frame,ang in [(1,0),(31,.04),(61,0),(91,-.04),(121,0)]:
 for name,fac in [('reed_lower',1),('reed_upper',1.3)]:
  bone=arm.pose.bones[name];bone.rotation_mode='XYZ';bone.rotation_euler=(ang*fac,ang*.4,0);bone.keyframe_insert('rotation_euler',frame=frame)
arm.animation_data.action.name='wind';bpy.context.scene.frame_end=121;bpy.context.scene.render.fps=30;bpy.context.scene.frame_set(1)
bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(O/'reed_v15.glb'),export_format='GLB',export_animations=True,export_skins=True,export_force_sampling=True)
me.calc_loop_triangles();report={'triangles':len(me.loop_triangles),'stems':8,'materials':1,'bones':3,'bytes':(O/'reed_v15.glb').stat().st_size};(O/'model-report.json').write_text(json.dumps(report,indent=2));print(report)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'reed_v15.blend'))
(O/'cameras.json').write_text(json.dumps([{'name':'front','loc':[3,-4,2.5],'at':[0,0,1],'res':[800,800]}]))
