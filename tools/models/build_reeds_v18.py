"""Bent grass sheets with a shared detailed atlas; low fill fixed, tall layer skinned."""
import bpy,math,json,struct,random
from pathlib import Path
from mathutils import Vector
O=Path('/Users/bytedance/Documents/ChatGPT/DRAGON/assets/reeds_v18');bpy.ops.wm.read_factory_settings(use_empty=True)
v=[];uvs=[];f=[];flex=[]
def sheet(a,width,height,x,y,variant,mobile):
 start=len(v);steps=4 if mobile else 2
 u0,u1=(.01,.49) if variant==0 else (.51,.99)
 v0,v1=(.36,.99) if mobile else (.012,.315)
 for i in range(steps+1):
  t=i/steps
  for j in range(3):
   u=j/2;s=(u-.5)*width
   # Cup cross section and curved upper silhouette: never a camera-facing billboard.
   local=Vector((s,.16*width*(u-.5)**2+.25*t*t,height*t))
   v.append((x+math.cos(a)*local.x-math.sin(a)*local.y,y+math.sin(a)*local.x+math.cos(a)*local.y,local.z));uvs.append((u0+(u1-u0)*u,v0+(v1-v0)*t));flex.append(mobile)
 for i in range(steps):
  for j in range(2):
   n=start+i*3+j;f.append((n,n+1,n+4,n+3))
for i,(h,x,y) in enumerate([(1.4,-.18,.08),(1.08,.18,-.1),(.82,0,.15)]):sheet(i*math.pi/3+.2,1.25,h,x,y,i%2,True)
for i,(h,x,y) in enumerate([(.38,-.25,0),(.52,.2,.15),(.29,0,-.25)]):sheet(i*math.pi/3,1.9,h,x,y,i%2,False)
me=bpy.data.meshes.new('layered_curved_grass');me.from_pydata(v,[],f);me.update();ob=bpy.data.objects.new('grass_layered',me);bpy.context.collection.objects.link(ob);uv=me.uv_layers.new(name='atlas_uv')
for poly in me.polygons:
 poly.use_smooth=True
 for li in poly.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
im=bpy.data.images.load(str(O/'grass_atlas.png'));im.pack();m=bpy.data.materials.new('grass_cutout');m.use_nodes=True;m.surface_render_method='DITHERED';m.use_backface_culling=False
bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.8
tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);m.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha']);me.materials.append(m)
armdata=bpy.data.armatures.new('grass_bones');arm=bpy.data.objects.new('grass_rig',armdata);bpy.context.collection.objects.link(arm);arm.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for name,z0,z1,parent in [('root',0,.1,None),('reed_lower',.1,.55,'root'),('reed_upper',.55,1.4,'reed_lower')]:
 b=armdata.edit_bones.new(name);b.head=(0,0,z0);b.tail=(0,0,z1)
 if parent:b.parent=armdata.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT');ob.parent=arm;mod=ob.modifiers.new('GrassSkin','ARMATURE');mod.object=arm
vg={n:ob.vertex_groups.new(name=n) for n in ['root','reed_lower','reed_upper']}
for i,vtx in enumerate(me.vertices):
 z=vtx.co.z;lo=max(0,min(1,z/.5)) if flex[i] else 0;hi=max(0,min(1,(z-.45)/.8))
 for n,w in {'root':1-lo,'reed_lower':lo*(1-hi),'reed_upper':lo*hi}.items():
  if w>0:vg[n].add([i],w,'REPLACE')
for fr,angle in [(1,0),(31,.04),(61,0),(91,-.04),(121,0)]:
 for name,factor in [('reed_lower',1),('reed_upper',1.3)]:
  b=arm.pose.bones[name];b.rotation_mode='XYZ';b.rotation_euler=(angle*factor,angle*.4,0);b.keyframe_insert('rotation_euler',frame=fr)
arm.animation_data.action.name='wind';bpy.context.scene.frame_set(1);bpy.context.scene.frame_end=121
bpy.ops.object.select_all(action='SELECT');path=O/'reed_v18.glb';bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',export_animations=True,export_skins=True)
b=path.read_bytes();jn=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+jn]);
for mat in d['materials']:mat['alphaMode']='MASK';mat['alphaCutoff']=.35;mat['doubleSided']=True
raw=json.dumps(d,separators=(',',':')).encode();raw+=b' '*((-len(raw))%4);tail=b[20+jn:];path.write_bytes(struct.pack('<III',0x46546c67,2,20+len(raw)+len(tail))+struct.pack('<II',len(raw),0x4e4f534a)+raw+tail)
me.calc_loop_triangles();report={'triangles':len(me.loop_triangles),'low_layers':3,'high_layers':3,'bones':3,'bytes':path.stat().st_size};(O/'model-report.json').write_text(json.dumps(report,indent=2));print(report);bpy.ops.wm.save_as_mainfile(filepath=str(O/'reed_v18.blend'))
