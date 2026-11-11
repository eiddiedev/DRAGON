"""Additive facade sample. No original geometry or collision is modified.
Blender -b -t 4 --python tools/models/castle_smooth_facade.py
Source coordinates east,north,up; world=(127+x,z,176+y).
"""
import bpy,bmesh,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'assets/castle_smooth_v7/facade';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'tools/models'));import kit
kit.reset();scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=6
STONE=[kit.srgb(c) for c in ['#98929D','#A39BA5','#918B98','#A099A3','#96909C']];TRIM=[kit.srgb(c) for c in ['#C1B6B8','#AEA4AF','#C7BDBE']];GOLD=kit.srgb('#A88B60');SLATE=kit.srgb('#55566D')
class LinearMesh(kit.Mesh):
 def __init__(self):
  self.bm=bmesh.new();self.col=self.bm.loops.layers.float_color.new('Col')
field=LinearMesh();orn=LinearMesh();doorfill=LinearMesh()
def box(m,size,loc,col):m.rbox(size,loc,col,cuts=0)
def beam(m,a,b,w,col):
 a,b=Vector(a),Vector(b);v=b-a;rot=v.to_track_quat('Z','Y').to_euler();m.rbox((w,w,v.length),(a+b)/2,col,rot,cuts=0)
def poly(m,points,front,back,col):
 vs=[m.bm.verts.new((x,y,z)) for y in [front,back] for x,z in points];n=len(points)
 for ids in [list(range(n))[::-1],list(range(n,2*n))]+[[i,(i+1)%n,(i+1)%n+n,i+n] for i in range(n)]:m.bm.faces.new([vs[i] for i in ids])
 m.paint(vs,col)
def clip_halfplane(points,a,b,inside=True):
 out=[]
 def signed(p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
 for p,q in zip(points,points[1:]+points[:1]):
  vp,vq=signed(p),signed(q);ip=vp>=-1e-9 if inside else vp<=1e-9;iq=vq>=-1e-9 if inside else vq<=1e-9
  if ip:out.append(p)
  if ip!=iq and abs(vp-vq)>1e-12:
   t=vp/(vp-vq);out.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
 clean=[]
 for p in out:
  if not clean or math.dist(p,clean[-1])>1e-7:clean.append(p)
 if len(clean)>1 and math.dist(clean[0],clean[-1])<1e-7:clean.pop()
 return clean
# True existing door profile: 4m jamb to spring76, pointed curve to78.
# The 0.015m clearance sits outside the original arch, never inside it.
hole=[(-1.915,71),(1.915,71),(1.915,76)]
hole += [(1.915*(1-k/14),76+2*math.sqrt(k/14)+.012) for k in range(1,15)]
hole += [(-1.915*(1-k/14),76+2*math.sqrt(k/14)+.012) for k in range(13,-1,-1)]
def subtract_door(rect):
 remaining=rect;pieces=[]
 for a,b in zip(hole,hole[1:]+hole[:1]):
  if len(remaining)<3:break
  exterior=clip_halfplane(remaining,a,b,False)
  if len(exterior)>=3:pieces.append(exterior)
  remaining=clip_halfplane(remaining,a,b,True)
 return pieces
# Continuous field, no mortar gaps or per-brick geometry/color.
def subtract_convex(polygon,hole):
 remaining=polygon;pieces=[]
 for a,b in zip(hole,hole[1:]+hole[:1]):
  if len(remaining)<3:break
  exterior=clip_halfplane(remaining,a,b,False)
  if len(exterior)>=3:pieces.append(exterior)
  remaining=clip_halfplane(remaining,a,b,True)
 return pieces
def cut_all(polys,holes):
 for h in holes:polys=[piece for p in polys for piece in subtract_convex(p,h)]
 return polys
outline=[(-7,72),(7,72),(7,89),(0,100),(-7,89)]
rose=[(3.14*math.cos(i*math.tau/80),83.5+3.14*math.sin(i*math.tau/80)) for i in range(80)]
high=[(-.95,90.5),(.95,90.5),(.95,96.4),(-.95,96.4)]
for p in cut_all([outline],[hole,rose,high]):
 vs=[field.bm.verts.new((x,-8.53,z)) for x,z in p];field.bm.faces.new(vs);field.paint(vs,STONE[0])
# Plinth and stepped string courses, exact door gap.
for s in [-1,1]:
 for zz,hh,dep in [(72.15,.24,.24),(72.43,.13,.18),(78.3,.14,.16),(88.8,.16,.24),(89.05,.10,.30)]:
  if zz<78.5:box(orn,(4.82,dep,hh),(s*4.53,-8.61,zz),TRIM[1])
  else:box(orn,(7,dep,hh),(s*3.5,-8.61,zz),TRIM[1])
# New skin follows existing castle_refit_exterior.door_arch exactly.
# Only front depth differs; no physical structure/collider is changed.
for layer in range(3):
 grow=layer*.22;ri=1.9+grow;ro=ri+.22;front=-8.74-layer*.095
 for side in [-1,1]:
  for k in range(6):
   box(orn,(.21,.22,4/6-.016),(side*(ri+.105),front+.11,72+(k+.5)*4/6),TRIM[(k+layer)%3])
  for k in range(14):
   a=(k+.015)/14;b=(k+.985)/14
   def inner(t):return (side*ri*(1-t),76+(2+grow*.45)*math.sqrt(t))
   def outer(t):return (side*ro*(1-t),76+(2.22+grow*.45)*math.sqrt(t))
   poly(orn,[inner(a),inner(b),outer(b),outer(a)],front,front+.22,TRIM[(layer+k)%3])
# Matching jamb-height pilasters; original X footprint retained.
for side in [-1,1]:
 for k in [0,1]:
  x=side*(2.78+k*.30);y=-8.7
  orn.cyl(.10,.10,3.55,(x,y,74.15),TRIM[1],12)
  for z,r,h in [(72.38,.16,.20),(75.80,.18,.16),(75.97,.22,.16)]:orn.cyl(r,r,h,(x,y,z),TRIM[0],8)
  for a in range(4):
   ang=a*math.pi/2;beam(orn,(x,y,75.65),(x+.14*math.cos(ang),y+.14*math.sin(ang),75.91),.055,TRIM[0])
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
# Open coating normals must preserve winding; kit's closed-volume recalculation flips isolated faces.
def open_object(m,name):
 m.bm.normal_update();me=bpy.data.meshes.new(name);m.bm.to_mesh(me);m.bm.free();ob=bpy.data.objects.new(name,me);scene.collection.objects.link(ob);return ob
# Flat coplanar pieces share one continuous stone appearance; no bevel seams.
receivers=[]
for m,name in [(field,'entrance_masonry'),(orn,'entrance_carved_trim')]:
 ob=open_object(m,name) if name=='entrance_masonry' else m.to_object(name);receivers.append(ob)
 for f in ob.data.polygons:f.use_smooth=False
# Additional side/rear external-only skin. Actual old bricks extend .035m.
coat=LinearMesh();coat_uv=coat.bm.loops.layers.uv.new('UVMap');panel_index=0
def panel(cx,cy,yaw,n,outline,holes=[]):
 global panel_index
 col,row=panel_index%4,panel_index//4;panel_index+=1
 umin,umax=min(p[0] for p in outline),max(p[0] for p in outline);zmin,zmax=min(p[1] for p in outline),max(p[1] for p in outline)
 for p in cut_all([outline],holes):
  vv=[coat.bm.verts.new((cx+math.cos(yaw)*u+math.sin(yaw)*n,cy+math.sin(yaw)*u-math.cos(yaw)*n,z)) for u,z in p];f=coat.bm.faces.new(vv)
  for loop,(u,z) in zip(f.loops,p):loop[coat_uv].uv=((col+.02+.96*(u-umin)/(umax-umin))/4,(row+.02+.96*(z-zmin)/(zmax-zmin))/3)
  coat.paint(vv,STONE[0])
def rect(a,b,z0,z1):return [(a,z0),(b,z0),(b,z1),(a,z1)]
def lancet_hole(u,z,w,h):
 return [(u-w/2-.04,z-.03),(u+w/2+.04,z-.03),(u+w/2+.04,z+h-w*.35),(u,z+h+.08),(u-w/2-.04,z+h-w*.35)]
for side in [-1,1]:
 # Wall at X +/-7; local u north and normal east or west.
 yaw=-math.pi/2 if side<0 else math.pi/2
 holes=[]
 for wy in [11.5,7.5,-3.5,-7.0]:
  u=wy/(1 if side>0 else -1)
  holes.append(lancet_hole(u,79.6,1.5,6.6))
  if wy!=-7:holes.append(lancet_hole(u,74.4,1,3.4))
 for a,b,h in [(-7.6,-6.2,4),(1.5,4.5,4.4)]:
  u1,u2=sorted([a/(1 if side>0 else -1),b/(1 if side>0 else -1)]);holes.append(rect(u1-.02,u2+.02,71.9,72+h+.02))
 panel(side*7,0,yaw,.055,rect(-14 if side<0 else -8,8 if side<0 else 14,72,89),holes)
 # Wing end wall and triangular gable. Normal actually outward unlike original source's inward yaw.
 yaw=math.pi/2 if side>0 else -math.pi/2
 # Source wing end wall is solid; decorative windows face inward, not exterior holes.
 panel(side*13.4,3,yaw,.055,rect(-4,4,72,87))
 # Gable wall occupies an outward .7m thickness; coating at .725 keeps original volume.
 panel(side*13.4,3,yaw,.725,[(-4,87),(4,87),(0,94.5)])
 # Wing north/south side walls have no new holes; only finish the existing surfaces.
 for sy in [-1,1]:panel(side*10.2,3+sy*4,0 if sy<0 else math.pi,.035,rect(-3.2,3.2,72,87))
# Rear gable above existing polygonal apse, not the shared internal lower wall.
panel(0,14,math.pi,.055,[(-7,89),(7,89),(0,100)])
ob=open_object(coat,'main_side_rear_smooth');receivers.append(ob)
# Actual diffuse transport into atlas; original castle is occluder only.
materials={}
for ob in receivers:
 mat=bpy.data.materials.new(ob.name+'_SOURCE');mat.use_nodes=True;nt=mat.node_tree;pb=nt.nodes.get('Principled BSDF');pb.inputs['Roughness'].default_value=.86
 attr=nt.nodes.new('ShaderNodeVertexColor');attr.layer_name='Col';noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=6;noise.inputs['Detail'].default_value=2
 ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.9,.89,.92,1);ramp.color_ramp.elements[1].color=(1,1,1,1);nt.links.new(noise.outputs['Fac'],ramp.inputs[0])
 mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.35;nt.links.new(attr.outputs['Color'],mix.inputs[1]);nt.links.new(ramp.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],pb.inputs['Base Color']);ob.data.materials.append(mat);materials[ob.name]=mat
 if ob.name=='entrance_masonry':
  uv=ob.data.uv_layers.new(name='UVMap')
  for lp in ob.data.loops:
   v=ob.data.vertices[lp.vertex_index].co;uv.data[lp.index].uv=((v.x+7)/14,(v.z-72)/28)
 elif ob.name=='entrance_carved_trim':
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(60),island_margin=.003);bpy.ops.object.mode_set(mode='OBJECT')
occluders=[]
for name in ['gothic_main','gothic_towers','gothic_wall']:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/castle_refit_v1/exterior'/f'{name}.glb'));occluders.extend(set(bpy.data.objects)-before)
world=bpy.data.worlds.new('neutral_soft_environment');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.65,.68,1);world.node_tree.nodes['Background'].inputs[1].default_value=.85;scene.world=world
# Same neutral approximation and established local fixtures as clock sample.
for spec in json.loads((ROOT/'assets/castle_refit_v1/interior/lighting-plan.json').read_text())['lights']:
 ld=bpy.data.lights.new(spec['name'],'POINT');ld.energy=spec['energy_watts']*2.4;ld.color=spec['color'];ld.shadow_soft_size=spec['radius'];lo=bpy.data.objects.new(spec['name'],ld);scene.collection.objects.link(lo);lo.location=spec['position_blender']
assert all(f.normal.y<-.99 for f in receivers[0].data.polygons), 'inconsistent outward entrance normals'
for ob in receivers:ob.data.calc_loop_triangles()
print('SAMPLE TRIANGLES',[(o.name,len(o.data.loop_triangles)) for o in receivers],flush=True)
assert sum(len(o.data.loop_triangles) for o in receivers)<=25000
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=40;scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=4
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'entrance-source.blend'))
previous_receipt=json.loads((OUT/'receipt.json').read_text()) if (OUT/'receipt.json').exists() else {}
report={'source':str(Path(__file__).resolve()),'coordinates':'world=(127+x,z,176+y); glTF=(x,z,-y)','collision':False,'revision':'v7-continuous-stone-same-v4-arch','door_profile':'castle_refit_exterior.door_arch: spring76,baseinnerhalfwidth1.9,baseapex78,grow.22','source_color_fix':'FLOAT_COLOR stores original linear values; no byte sRGB conversion','passes':['COLOR','DIRECT','INDIRECT'],'samples':40,'diffuse_bounces':4,'environment':'neutral approximation (.65,.65,.68)*.85; existing fixtures x2.4, not reconstructed actual skybox','occluders':['existing gothic_main','existing gothic_towers','existing gothic_wall'],'outputs':{}}
for ob in receivers:
 mat=materials[ob.name];nt=mat.node_tree;size=2048
 if ob.name in ('entrance_carved_trim','entrance_masonry'):
  im=bpy.data.images.load(str(OUT/(ob.name+'-GI.png')));final=bpy.data.materials.new(ob.name+'_GI_COLOR');final.use_nodes=True;pb=final.node_tree.nodes.get('Principled BSDF');tx=final.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im;final.node_tree.links.new(tx.outputs['Color'],pb.inputs['Base Color']);ob['final_material']=final.name;continue
 im=bpy.data.images.new(ob.name+'_GI',size,size);tex=nt.nodes.new('ShaderNodeTexImage');tex.image=im;nt.nodes.active=tex
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.bake(type='DIFFUSE',pass_filter={'COLOR','DIRECT','INDIRECT'},margin=6,use_clear=True);im.filepath_raw=str(OUT/(ob.name+'-GI.png'));im.file_format='PNG';im.save()
 diag=bpy.data.images.new(ob.name+'_indirect',128,128);tex.image=diag;bpy.ops.object.bake(type='DIFFUSE',pass_filter={'INDIRECT'},margin=2,use_clear=True);diag.filepath_raw=str(OUT/(ob.name+'-indirect.png'));diag.file_format='PNG';diag.save();tex.image=im
 final=bpy.data.materials.new(ob.name+'_GI_COLOR');final.use_nodes=True;pb=final.node_tree.nodes.get('Principled BSDF');pb.inputs['Roughness'].default_value=.86;tx=final.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im;final.node_tree.links.new(tx.outputs['Color'],pb.inputs['Base Color'])
 dup=ob.copy();dup.data=ob.data.copy();scene.collection.objects.link(dup);dup.data.materials.clear();dup.data.materials.append(final)
 for a in list(dup.data.color_attributes):dup.data.color_attributes.remove(a)
 bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup;path=OUT/(ob.name+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_image_format='JPEG',export_jpeg_quality=94)
 dup.data.calc_loop_triangles();verts=[dup.matrix_world@v.co for v in dup.data.vertices];mn=[min(v[i] for v in verts) for i in range(3)];mx=[max(v[i] for v in verts) for i in range(3)];tris=len(dup.data.loop_triangles);assert tris<=25000,(ob.name,tris)
 report['outputs'][ob.name]={'file':str(path),'material':final.name,'triangles':tris,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bounds_gltf':[[mn[0],mn[2],-mx[1]],[mx[0],mx[2],-mn[1]]],'normalization_scale':max(b-a for a,b in zip(mn,mx)),'vertex_colors':False,'texture_size':size};bpy.data.objects.remove(dup,do_unlink=True);ob['final_material']=final.name
for frozen in ['entrance_carved_trim','entrance_masonry']:report['outputs'][frozen]=previous_receipt['outputs'][frozen]
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
kit.shot(cam,str(OUT/'portal-close.png'),(0,-13.8,76),(0,-8,77.0),18,(1500,1100))
kit.shot(cam,str(OUT/'side-rear.png'),(35,32,94),(0,7,85),42,(1500,1100))
print('ENTRANCE SAMPLE READY',json.dumps(report))
