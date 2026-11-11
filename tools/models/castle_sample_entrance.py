"""Additive facade sample. No original geometry or collision is modified.
Blender -b -t 6 --python tools/models/castle_sample_entrance.py
Source coordinates east,north,up; world=(127+x,z,176+y).
"""
import bpy,bmesh,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'assets/castle_sample_v3/entrance';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'tools/models'));import kit
kit.reset();scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=6
STONE=[kit.srgb(c) for c in ['#98929D','#A39BA5','#918B98','#A099A3','#96909C']];TRIM=[kit.srgb(c) for c in ['#C1B6B8','#AEA4AF','#C7BDBE']];GOLD=kit.srgb('#A88B60');SLATE=kit.srgb('#55566D')
field=kit.Mesh();orn=kit.Mesh()
def box(m,size,loc,col):m.rbox(size,loc,col,cuts=0)
def beam(m,a,b,w,col):
 a,b=Vector(a),Vector(b);v=b-a;rot=v.to_track_quat('Z','Y').to_euler();m.rbox((w,w,v.length),(a+b)/2,col,rot,cuts=0)
def poly(m,points,front,back,col):
 vs=[m.bm.verts.new((x,y,z)) for y in [front,back] for x,z in points];n=len(points)
 for ids in [list(range(n))[::-1],list(range(n,2*n))]+[[i,(i+1)%n,(i+1)%n+n,i+n] for i in range(n)]:m.bm.faces.new([vs[i] for i in ids])
 m.paint(vs,col)
# Staggered masonry behind the new mouldings. Avoid expanded glass bounding regions.
rowh=.70
for row in range(40):
 za=72+row*rowh;zb=min(100,za+rowh)
 if za>=100:continue
 half=7 if za<=89 else max(0,7*(1-(za-89)/11))
 for j in range(-8,8):
  xa=max(-half,j*1.0+(row%2)*.5);xb=min(half,j*1.0+1+(row%2)*.5)
  if xb-xa<.17:continue
  # Keep full true doorway open. Portal layered mouldings cover neighboring masonry gaps.
  if xa<2.08 and xb>-2.08 and za<78.2:continue
  # Circle expanded to preserve the rose glass and original leading.
  nearx=max(xa,min(0,xb));nearz=max(za,min(83.5,zb))
  if nearx**2+(nearz-83.5)**2<3.14**2:continue
  if xa<.95 and xb>-.95 and za<96.4 and zb>90.5:continue
  col=STONE[(row*3+j)%len(STONE)]
  if zb>89:
   points=[(xa+.012,za+.012),(xb-.012,za+.012),(xb-.012,zb-.012),(xa+.012,zb-.012)]
   # Clip each stone to both exact sloping roof-edge planes; no staircase holes.
   for sign in [-1,1]:
    clipped=[]
    for a,b in zip(points,points[1:]+points[:1]):
     va=sign*a[0]+7/11*a[1]-7/11*100;vb=sign*b[0]+7/11*b[1]-7/11*100
     if va<=0:clipped.append(a)
     if (va<=0)!=(vb<=0):
      t=va/(va-vb);clipped.append(tuple(a[k]+t*(b[k]-a[k]) for k in [0,1]))
    points=clipped
   if len(points)>=3:poly(field,points,-8.53,-8.41,col)
  else:box(field,(xb-xa-.024,.12,zb-za-.024),((xa+xb)/2,-8.47,(za+zb)/2),col)
# Plinth and stepped string courses, exact door gap.
for s in [-1,1]:
 for zz,hh,dep in [(72.15,.24,.24),(72.43,.13,.18),(78.3,.14,.16),(88.8,.16,.24),(89.05,.10,.30)]:
  if zz<78.5:box(orn,(4.82,dep,hh),(s*4.53,-8.61,zz),TRIM[1])
  else:box(orn,(7,dep,hh),(s*3.5,-8.61,zz),TRIM[1])
# Nested portal: 3 molded jambs stay outside the original 3.8m clear width.
for layer in range(3):
 ri=1.97+layer*.23;ro=ri+.19;front=-8.74-layer*.095
 for side in [-1,1]:
  for k in range(9):
   box(orn,(.19,.22,6/9-.016),(side*(ri+.095),front+.11,72+(k+.5)*6/9),TRIM[(k+layer)%3])
  # Shaped voussoirs, pointed spring above the true opening top.
  for k in range(16):
   t0=(k+.016)/16;t1=(k+.984)/16
   def pt(t,r,extra=0):return (side*r*(1-t),78+1.75*math.sqrt(t)+extra)
   poly(orn,[pt(t0,ri),pt(t1,ri),pt(t1,ro,.19),pt(t0,ro,.19)],front,front+.22,TRIM[(layer+k)%3])
# Four slender carved column shafts outside jamb and small sculptural capitals.
for side in [-1,1]:
 for k in [0,1]:
  x=side*(2.78+k*.30);y=-8.7
  orn.cyl(.10,.10,5.5,(x,y,75.12),TRIM[1],12)
  for z,r,h in [(72.38,.16,.20),(77.80,.18,.16),(77.97,.22,.16)]:orn.cyl(r,r,h,(x,y,z),TRIM[0],8)
  for a in range(4):
   ang=a*math.pi/2;beam(orn,(x,y,77.65),(x+.14*math.cos(ang),y+.14*math.sin(ang),77.91),.055,TRIM[0])
# Rose surround: broad chamfered radial voussoirs hide regular masonry termination.
for layer,(ri,ro,y) in enumerate([(3.08,3.29,-8.65),(3.29,3.64,-8.60),(3.64,3.82,-8.54)]):
 for k in range(56):
  a=(k+.025)*math.tau/56;b=(k+.975)*math.tau/56
  poly(orn,[(ri*math.cos(a),83.5+ri*math.sin(a)),(ro*math.cos(a),83.5+ro*math.sin(a)),(ro*math.cos(b),83.5+ro*math.sin(b)),(ri*math.cos(b),83.5+ri*math.sin(b))],y-.12,y+.10,TRIM[(k+layer)%3])
# Restrained new rose tracery stays inside existing leading; glass remains largely visible.
for k in range(8):
 a=k*math.tau/8
 beam(orn,(.42*math.cos(a),-8.34,83.5+.42*math.sin(a)),(2.96*math.cos(a),-8.34,83.5+2.96*math.sin(a)),.055,TRIM[1])
for ri,ro in [(.35,.44),(1.38,1.45)]:
 for k in range(40):
  a=k*math.tau/40;b=(k+1)*math.tau/40
  poly(orn,[(ri*math.cos(a),83.5+ri*math.sin(a)),(ro*math.cos(a),83.5+ro*math.sin(a)),(ro*math.cos(b),83.5+ro*math.sin(b)),(ri*math.cos(b),83.5+ri*math.sin(b))],-8.38,-8.29,TRIM[1])
# High lancet surround leaves its glass rectangle and pointed head untouched.
for side in [-1,1]:
 for k in range(7):box(orn,(.40,.22,.64),(side*1.10,-8.54,90.7+(k+.5)*.66),TRIM[k%3])
 beam(orn,(side*1.1,-8.54,95.35),(0,-8.54,97.0),.29,TRIM[0])
box(orn,(2.75,.32,.17),(0,-8.57,90.55),TRIM[0])
# Layered gable edge with little geometric crockets: no new roof mass.
for side in [-1,1]:
 for off,w in [(0,.20),(.23,.12)]:beam(orn,(side*(7+off),-8.59,89),(side*off,-8.59,100),w,TRIM[1 if off else 0])
 for t in [.18,.36,.54,.72]:
  x=side*7*(1-t);z=89+11*t
  orn.cyl(.10,.02,.42,(x,-8.63,z+.22),TRIM[0],6)
# Make a modest, real chamfer rather than flat cube edges.
receivers=[]
for m,name,width in [(field,'entrance_masonry',.022),(orn,'entrance_carved_trim',.012)]:
 ob=m.to_object(name);bpy.context.view_layer.objects.active=ob
 # kit's byte-color paint receives linear RGB; undo the implicit second sRGB decode.
 for datum in ob.data.color_attributes['Col'].data:datum.color=datum.color_srgb
 mod=ob.modifiers.new('stone_edge_chamfer','BEVEL');mod.width=width;mod.segments=1;mod.affect='EDGES'
 if name=='entrance_masonry':bpy.ops.object.modifier_apply(modifier=mod.name)
 else:ob.modifiers.remove(mod)
 receivers.append(ob)
 # Smooth only extremely small curved facets? Flat normal bevels preserve stone form.
 for face in ob.data.polygons:face.use_smooth=False
# Actual diffuse transport into atlas; original castle is occluder only.
materials={}
for ob in receivers:
 mat=bpy.data.materials.new(ob.name+'_SOURCE');mat.use_nodes=True;nt=mat.node_tree;pb=nt.nodes.get('Principled BSDF');pb.inputs['Roughness'].default_value=.86
 attr=nt.nodes.new('ShaderNodeVertexColor');attr.layer_name='Col';noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=6;noise.inputs['Detail'].default_value=2
 ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.9,.89,.92,1);ramp.color_ramp.elements[1].color=(1,1,1,1);nt.links.new(noise.outputs['Fac'],ramp.inputs[0])
 mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.35;nt.links.new(attr.outputs['Color'],mix.inputs[1]);nt.links.new(ramp.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],pb.inputs['Base Color']);ob.data.materials.append(mat);materials[ob.name]=mat
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(60),island_margin=.003);bpy.ops.object.mode_set(mode='OBJECT')
occluders=[]
for name in ['gothic_main','gothic_towers','gothic_wall']:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/castle_refit_v1/exterior'/f'{name}.glb'));occluders.extend(set(bpy.data.objects)-before)
world=bpy.data.worlds.new('neutral_soft_environment');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.65,.68,1);world.node_tree.nodes['Background'].inputs[1].default_value=.85;scene.world=world
# Same neutral approximation and established local fixtures as clock sample.
for spec in json.loads((ROOT/'assets/castle_refit_v1/interior/lighting-plan.json').read_text())['lights']:
 ld=bpy.data.lights.new(spec['name'],'POINT');ld.energy=spec['energy_watts']*2.4;ld.color=spec['color'];ld.shadow_soft_size=spec['radius'];lo=bpy.data.objects.new(spec['name'],ld);scene.collection.objects.link(lo);lo.location=spec['position_blender']
for ob in receivers:ob.data.calc_loop_triangles()
print('SAMPLE TRIANGLES',[(o.name,len(o.data.loop_triangles)) for o in receivers],flush=True)
assert sum(len(o.data.loop_triangles) for o in receivers)<=25000
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=40;scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=4
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'entrance-source.blend'))
report={'source':str(Path(__file__).resolve()),'coordinates':'world=(127+x,z,176+y); glTF=(x,z,-y)','collision':False,'source_color_fix':'BYTE_COLOR color_srgb reassigned to linear color to undo kit double decode','passes':['COLOR','DIRECT','INDIRECT'],'samples':40,'diffuse_bounces':4,'environment':'neutral approximation (.65,.65,.68)*.85; existing fixtures x2.4, not reconstructed actual skybox','occluders':['existing gothic_main','existing gothic_towers','existing gothic_wall'],'outputs':{}}
for ob in receivers:
 mat=materials[ob.name];nt=mat.node_tree;size=2048;im=bpy.data.images.new(ob.name+'_GI',size,size);tex=nt.nodes.new('ShaderNodeTexImage');tex.image=im;nt.nodes.active=tex
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.bake(type='DIFFUSE',pass_filter={'COLOR','DIRECT','INDIRECT'},margin=6,use_clear=True);im.filepath_raw=str(OUT/(ob.name+'-GI.png'));im.file_format='PNG';im.save()
 diag=bpy.data.images.new(ob.name+'_indirect',128,128);tex.image=diag;bpy.ops.object.bake(type='DIFFUSE',pass_filter={'INDIRECT'},margin=2,use_clear=True);diag.filepath_raw=str(OUT/(ob.name+'-indirect.png'));diag.file_format='PNG';diag.save();tex.image=im
 final=bpy.data.materials.new(ob.name+'_GI_COLOR');final.use_nodes=True;pb=final.node_tree.nodes.get('Principled BSDF');pb.inputs['Roughness'].default_value=.86;tx=final.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im;final.node_tree.links.new(tx.outputs['Color'],pb.inputs['Base Color'])
 dup=ob.copy();dup.data=ob.data.copy();scene.collection.objects.link(dup);dup.data.materials.clear();dup.data.materials.append(final)
 for a in list(dup.data.color_attributes):dup.data.color_attributes.remove(a)
 bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup;path=OUT/(ob.name+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_image_format='JPEG',export_jpeg_quality=94)
 dup.data.calc_loop_triangles();verts=[dup.matrix_world@v.co for v in dup.data.vertices];mn=[min(v[i] for v in verts) for i in range(3)];mx=[max(v[i] for v in verts) for i in range(3)];tris=len(dup.data.loop_triangles);assert tris<=25000,(ob.name,tris)
 report['outputs'][ob.name]={'file':str(path),'material':final.name,'triangles':tris,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bounds_gltf':[[mn[0],mn[2],-mx[1]],[mx[0],mx[2],-mn[1]]],'normalization_scale':max(b-a for a,b in zip(mn,mx)),'vertex_colors':False,'texture_size':size};bpy.data.objects.remove(dup,do_unlink=True);ob['final_material']=final.name
for ob in receivers:ob.data.materials[0]=bpy.data.materials[ob['final_material']]
(OUT/'receipt.json').write_text(json.dumps(report,indent=2))
for im in bpy.data.images:
 if im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'entrance-baked.blend'))
# Actual artifact render in old castle context; use emission preview for already baked surfaces.
for ob in receivers:
 mat=ob.data.materials[0];nt=mat.node_tree;out=nt.nodes.get('Material Output');em=nt.nodes.new('ShaderNodeEmission');tx=next(n for n in nt.nodes if n.type=='TEX_IMAGE');nt.links.new(tx.outputs['Color'],em.inputs['Color']);nt.links.new(em.outputs[0],out.inputs['Surface'])
cam=kit.preview_setup();scene.world=world;scene.cycles.samples=24;scene.view_settings.view_transform='Standard';scene.view_settings.look='Medium High Contrast';scene.view_settings.exposure=0
# Gate omitted only from facade-study view; it otherwise obscures the entire facade.
for ob in occluders:
 if ob.type=='MESH' and 'gothic_wall' in ob.name:ob.hide_render=True
# Context nodes have generic names, use wide courtyard-internal view instead.
kit.shot(cam,str(OUT/'facade-whole.png'),(0,-14,85.5),(0,-8,86.5),9,(1300,1500))
kit.shot(cam,str(OUT/'portal-close.png'),(0,-13.8,76),(0,-8,77.0),18,(1500,1100))
print('ENTRANCE SAMPLE READY',json.dumps(report))
