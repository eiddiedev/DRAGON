"""Layered grass study: static short colour layer + detailed flexible long blades."""
import bpy,math,random,json,numpy as np
from pathlib import Path
from mathutils import Vector
O=Path('/Users/bytedance/Documents/ChatGPT/DRAGON/assets/reeds_v17');O.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);r=random.Random(1701)
verts=[];uvs=[];faces=[];flex=[]
def blade(x,y,angle,h,reach,w,segments,variant,mobile):
 start=len(verts);side=Vector((-math.sin(angle),math.cos(angle),0));curl=r.uniform(-.15,.15)
 for i in range(segments+1):
  t=i/segments;profile=math.sin(math.pi*(t*.94+.025))**.65*(1-t)**.35
  if i==segments:profile=0
  c=Vector((x+math.cos(angle)*reach*t*t+.18*t*t,y+math.sin(angle)*reach*t*t+curl*t*t,h*math.sin(t*1.9)))
  for j in ([-1,0,1] if mobile else [-1,1]):
   verts.append(tuple(c+side*w*profile*j+Vector((0,0,w*profile*.12 if j==0 else 0))))
   uvs.append(((variant+(j+1)*.5*.88+.06)/8,.02+.96*t));flex.append(mobile)
 for i in range(segments):
  if mobile:
   for j in range(2):
    a=start+i*3+j;faces.append((a,a+1,a+4,a+3))
  else:
   a=start+i*2;faces.append((a,a+1,a+3,a+2))
# Different heights within each tuft; roots deliberately irregular, no level canopy.
for k in range(8):
 a=k*2.399;rad=.76*math.sqrt((k+.5)/8);x,y=rad*math.cos(a),rad*math.sin(a)
 for j in range(2):
  h=r.uniform(.7,1.55)*(1 if k%3 else .78)
  blade(x,y,a+j*2.5+r.uniform(-.4,.4),h,r.uniform(.55,1.15),r.uniform(.027,.047),6,r.randrange(8),True)
 for j in range(5):
  blade(x+r.uniform(-.15,.15),y+r.uniform(-.15,.15),a+j*1.257,r.uniform(.16,.42),r.uniform(.55,.85),r.uniform(.10,.16),2,r.randrange(4),False)
# Two fine stems with tapered heads; many tiny polygons would not read at gameplay distance.
for k in range(2):
 x,y=(-.35+k*.65,.1);h=1.1+k*.22;start=len(verts)
 for t,rad in [(0,.008),(.65,.006),(.84,.017),(1,.001)]:
  for j in range(3):
   a=j*math.tau/3;verts.append((x+.3*t*t+rad*math.cos(a),y+rad*math.sin(a),h*t));uvs.append((.94,.1+t*.85));flex.append(True)
 for i in range(3):
  for j in range(3):
   a=start+i*3+j;b=start+i*3+(j+1)%3;faces.append((a,b,b+3,a+3))
me=bpy.data.meshes.new('layered_grass');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('grass_layered',me);bpy.context.collection.objects.link(ob)
uv=me.uv_layers.new(name='blade_uv')
for poly in me.polygons:
 poly.use_smooth=True
 for li in poly.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
# 512px shared atlas: base-to-tip gradient, fine longitudinal veins, weathering flecks.
N=512;yy,xx=np.mgrid[0:N,0:N];t=yy/(N-1);u=(xx%64)/63;variant=xx//64
rng=np.random.default_rng(17);noise=rng.random((N,N))
vein=.035*np.sin(u*math.pi*42+np.sin(t*16)*.2)+.018*np.sin(u*math.pi*94)
rib=.10*np.exp(-((u-.5)/.025)**2);edge=-.08*(np.abs(u-.5)*2)**5
base=.72+.23*t+.045*np.sin(t*12+variant)+vein+rib+edge+(noise-.5)*.035
base*=1-.14*np.exp(-t*8);base-=.06*(np.sin(t*105+u*13+variant)> .985)
cols=np.array([[.43,.39,.22],[.49,.43,.25],[.55,.46,.27],[.61,.5,.3],[.65,.53,.31],[.7,.58,.36],[.75,.64,.4],[.8,.69,.45]])
pix=np.ones((N,N,4),dtype=np.float32);pix[:,:,:3]=cols[variant]*base[:,:,None]
im=bpy.data.images.new('grass_blade_atlas',width=N,height=N);im.pixels.foreach_set(pix.ravel());im.filepath_raw=str(O/'grass_blade_atlas.png');im.file_format='PNG';im.save();im.pack()
m=bpy.data.materials.new('grass_blade_detail');m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.76
tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);me.materials.append(m)
armdata=bpy.data.armatures.new('grass_bones');arm=bpy.data.objects.new('grass_rig',armdata);bpy.context.collection.objects.link(arm);arm.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for name,z0,z1,parent in [('root',0,.1,None),('reed_lower',.1,.55,'root'),('reed_upper',.55,1.4,'reed_lower')]:
 b=armdata.edit_bones.new(name);b.head=(0,0,z0);b.tail=(0,0,z1)
 if parent:b.parent=armdata.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT');ob.parent=arm;mod=ob.modifiers.new('GrassSkin','ARMATURE');mod.object=arm
vg={n:ob.vertex_groups.new(name=n) for n in ['root','reed_lower','reed_upper']}
for i,v in enumerate(me.vertices):
 z=v.co.z;lo=max(0,min(1,z/.5)) if flex[i] else 0;hi=max(0,min(1,(z-.45)/.8))
 for n,w in {'root':1-lo,'reed_lower':lo*(1-hi),'reed_upper':lo*hi}.items():
  if w>0:vg[n].add([i],w,'REPLACE')
for fr,angle in [(1,0),(31,.04),(61,0),(91,-.04),(121,0)]:
 for name,factor in [('reed_lower',1),('reed_upper',1.3)]:
  b=arm.pose.bones[name];b.rotation_mode='XYZ';b.rotation_euler=(angle*factor,angle*.4,0);b.keyframe_insert('rotation_euler',frame=fr)
arm.animation_data.action.name='wind';bpy.context.scene.frame_set(1);bpy.context.scene.frame_end=121
bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(O/'reed_v17.glb'),export_format='GLB',export_animations=True,export_skins=True)
me.calc_loop_triangles();report={'triangles':len(me.loop_triangles),'high_blades':16,'short_blades':40,'bones':3,'texture':512,'bytes':(O/'reed_v17.glb').stat().st_size};(O/'model-report.json').write_text(json.dumps(report,indent=2));print(report)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'reed_v17.blend'))
