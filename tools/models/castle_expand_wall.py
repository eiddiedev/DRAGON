"""V5 additive ring wall / gatehouse skin. Existing geometry/collisions unchanged.
Blender -b -t 6 --python tools/models/castle_expand_wall.py
World=(127+BlenderX, BlenderZ, 176+BlenderY). No recentering.
"""
import bpy,bmesh,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent));import kit
OUT=Path('assets/castle_expand_v5/wall');OUT.mkdir(parents=True,exist_ok=True)
class LinearMesh(kit.Mesh):
 def __init__(self):
  self.bm=bmesh.new();self.col=self.bm.loops.layers.float_color.new('Col');self.roofpairs=[]
 def to_object(self,name):
  # Disconnected open shingles have no closed volume from which recalc can
  # infer orientation. After general recalc, fix every shingle radially outward.
  self.bm.normal_update();bmesh.ops.recalc_face_normals(self.bm,faces=list(self.bm.faces))
  fixed=0
  for front,lip,cx,cy in self.roofpairs:
   c=front.calc_center_median();rad=Vector((c.x-cx,c.y-cy,0))
   if front.normal.dot(rad)<0:front.normal_flip();lip.normal_flip();fixed+=1
   assert front.normal.dot(rad)>0
  print('ROOF_NORMALS',name,'shingles',len(self.roofpairs),'fixed',fixed,flush=True)
  me=bpy.data.meshes.new(name);self.bm.to_mesh(me);self.bm.free();ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob);return ob
kit.reset();scene=bpy.context.scene
STONE=[kit.srgb(h) for h in ['#98929D','#A19BA4','#918D99','#ABA2AA']]
TRIM=kit.srgb('#C1B6B8');DEEP=kit.srgb('#6B6475');GOLD=kit.srgb('#C3A36A')
SLATE=[kit.srgb(h) for h in ['#55566D','#595B70','#53566B','#5D5E73']]
RING=LinearMesh();TURRETS=LinearMesh();GATE=LinearMesh()
def at(cx,cy,yaw,u,n,z):return (cx+math.cos(yaw)*u+math.sin(yaw)*n,cy+math.sin(yaw)*u-math.cos(yaw)*n,z)
def solid(mesh,back,front,col):
 vs=[mesh.bm.verts.new(v) for v in back+front];N=len(back)
 mesh.bm.faces.new(vs[:N][::-1]);mesh.bm.faces.new(vs[N:])
 for i in range(N):j=(i+1)%N;mesh.bm.faces.new([vs[i],vs[j],vs[N+j],vs[N+i]])
 mesh.paint(vs,col)
def panel(mesh,cx,cy,yaw,u,z,w,h,col,back,front,ch=.025,tilt=0):
 if w<.04 or h<.04:return
 c=min(ch,w*.2,h*.2)
 def pos(x,zz,n):
  xx=u+x*math.cos(tilt)-zz*math.sin(tilt);z1=z+x*math.sin(tilt)+zz*math.cos(tilt)
  return at(cx,cy,yaw,xx,n,z1)
 a=[(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]
 b=[(-w/2+c,-h/2+c),(w/2-c,-h/2+c),(w/2-c,h/2-c),(-w/2+c,h/2-c)]
 solid(mesh,[pos(x,z,back) for x,z in a],[pos(x,z,front) for x,z in b],col)
def courses(mesh,cx,cy,yaw,width,z0,z1,n,rows,cols,seed=0,holes=()):
 step=width/cols
 for row in range(rows):
  za=z0+(z1-z0)*row/rows;zb=z0+(z1-z0)*(row+1)/rows
  spans=[(-width/2,width/2)]
  for ha,hb,hz0,hz1 in holes:
   if zb<=hz0 or za>=hz1:continue
   new=[]
   for a,b in spans:
    if ha>a:new.append((a,min(ha,b)))
    if hb<b:new.append((max(hb,a),b))
   spans=[(a,b) for a,b in new if b>a]
  for a,b in spans:
   u=-width/2-step+(row%2)*step*.5
   while u<b:
    lo=max(a,u);hi=min(b,u+step)
    if hi-lo>.055:panel(mesh,cx,cy,yaw,(lo+hi)/2,(za+zb)/2,hi-lo-.018,zb-za-.020,STONE[((row*31+int(u*71)+seed*17)^int(u*row*13))%4],n,n+.085)
    u+=step
def band(mesh,cx,cy,yaw,width,z,n,depth=.16):
 for dz,h,nn,d in [(-.13,.10,n,.03),(0,.17,n+.025,depth),(.13,.08,n,.08)]:
  panel(mesh,cx,cy,yaw,0,z+dz,width,h,TRIM,nn,nn+d,.025)
def round_band(mesh,cx,cy,z,r,seg=16):
 profile=[(r-.07,-.16),(r+.04,-.10),(r+.06,.08),(r-.01,.16),(r-.09,.16),(r-.09,-.16)]
 rings=[[mesh.bm.verts.new((cx+rr*math.cos(i*math.tau/seg),cy+rr*math.sin(i*math.tau/seg),z+dz)) for i in range(seg)] for rr,dz in profile]
 for a,b in zip(rings,rings[1:]+rings[:1]):
  for i in range(seg):j=(i+1)%seg;mesh.bm.faces.new([a[i],a[j],b[j],b[i]])
 mesh.paint([v for a in rings for v in a],TRIM)
def roof(mesh,cx,cy,z,r,h,rows,cols,ribs=True):
 for row in range(rows):
  t0=row/rows;t1=(row+1)/rows;z0=z+h*t0;z1=z+h*t1
  r0=r*(1-t0)**1.08+.025+.11*(1-t0)+.018;r1=r*(1-t1)**1.08+.025+.11*(1-t1)+.018
  for j in range(cols):
   a=(j+.012)*math.tau/cols;b=(j+.988)*math.tau/cols
   vv=[(cx+r0*math.cos(a),cy+r0*math.sin(a),z0),(cx+r0*math.cos(b),cy+r0*math.sin(b),z0),(cx+r1*math.cos(b),cy+r1*math.sin(b),z1+.02),(cx+r1*math.cos(a),cy+r1*math.sin(a),z1+.02),(cx+(r0+.017)*math.cos(a),cy+(r0+.017)*math.sin(a),z0-.035),(cx+(r0+.017)*math.cos(b),cy+(r0+.017)*math.sin(b),z0-.035)]
   vs=[mesh.bm.verts.new(v) for v in vv];f1=mesh.bm.faces.new(vs[:4]);f2=mesh.bm.faces.new([vs[0],vs[4],vs[5],vs[1]]);mesh.roofpairs.append((f1,f2,cx,cy));mesh.paint(vs,SLATE[((j*17+row*31)^(j*row*7))%4])
 if ribs:
  for k in range(8):
   a=k*math.tau/8
   pts=[]
   for j in range(9):
    t=j/8;rr=r*(1-t)**1.08+.025+.13*(1-t)+.021;pts.append((cx+rr*math.cos(a),cy+rr*math.sin(a),z+h*t))
   mesh.tube(pts,[.028]*len(pts),GOLD,seg=3)
def window_frame(mesh,cx,cy,yaw,z,w,h,n):
 straight=h-w*.6
 for s in [-1,1]:
  for k in range(4):panel(mesh,cx,cy,yaw,s*(w/2+.13),z+(k+.5)*straight/4,.20,straight/4-.018,TRIM,n,n+.16)
  # Match the original luminous diamond, retain its full silhouette.
  for k in range(4):
   t0=k/4;t1=(k+1)/4
   pts=[(s*w*.55*(1-t0),z+straight+w*.55*t0),(s*w*.55*(1-t1),z+straight+w*.55*t1),(s*(w*.55+.20)*(1-t1),z+straight+(w*.55+.20)*t1),(s*(w*.55+.20)*(1-t0),z+straight+(w*.55+.20)*t0)]
   solid(mesh,[at(cx,cy,yaw,u,n,zz) for u,zz in pts],[at(cx,cy,yaw,u,n+.16,zz) for u,zz in pts],TRIM)
 panel(mesh,cx,cy,yaw,0,z-.10,w+.65,.19,TRIM,n,n+.22,.035)
 panel(mesh,cx,cy,yaw,0,z+straight/2,.045,straight,GOLD,n+.06,n+.13,.008)

# Existing 16-edge wall, two southern edges intentionally omitted for entrance.
R=18.6;verts=[(math.cos(i/16*math.tau)*R,math.sin(i/16*math.tau)*R) for i in range(16)]
indices=[];turret_centers=[]
for i in range(16):
 mid=(i+.5)/16*math.tau
 if abs(((mid-3*math.pi/2+math.pi)%math.tau)-math.pi)<math.pi/16*1.6:continue
 indices.append(i);a=verts[i];b=verts[(i+1)%16];cx=(a[0]+b[0])/2;cy=(a[1]+b[1])/2;L=math.hypot(b[0]-a[0],b[1]-a[1]);yaw=math.atan2(b[1]-a[1],b[0]-a[0])+math.pi
 for side in [0,1]:
  ya=yaw+side*math.pi
  courses(RING,cx,cy,ya,L+.40,68.51,76.79,.768,9,6,i+side)
  band(RING,cx,cy,ya,L+.57,76.98,.91,.10)
  band(RING,cx,cy,ya,L+.42,71.25,.79,.075)
 for k in range(5):
  u=(k+.5)/5*L-L/2;x,y,_=at(cx,cy,yaw,u,.6,0)
  for side in [0,1]:
   panel(RING,x,y,yaw+side*math.pi,0,77.60,L/5*.55+.015,.99,STONE[(i+k)%4],.175,.235,.035)
  # Stone coping sits above existing merlons; side faces remain original.
  RING.rbox((L/5*.55+.10,.49,.12),(x,y,78.15),TRIM,(0,0,yaw),cuts=0)
 if i%3==0:turret_centers.append((a[0]*1.03,a[1]*1.03,i))

# Tapered ten-sided small towers: exact original footprint and five locations.
for cx,cy,i in turret_centers:
 wyaw=math.atan2(cy,cx)+math.pi/2
 for f in range(10):
  # Source bmesh ten-sided cylinder vertices are at18+36k degrees: normals36k.
  ang=f*math.tau/10;ya=ang+math.pi/2
  for row in range(12):
   za=68.5+row;zb=za+1;rr=1.35-(1.35-1.2)*(row+.5)/12;n=rr*math.cos(math.pi/10)+.014;w=2*rr*math.sin(math.pi/10)
   diff=abs(((ang-math.atan2(cy,cx)+math.pi)%math.tau)-math.pi)
   if zb>76.35 and za<79.37 and diff<.55:continue
   panel(TURRETS,cx,cy,ya,0,(za+zb)/2,w-.015,.977,STONE[(i*11+f*3+row*7)%4],n,n+.075)
 for zz,rr in [(71.25,1.40),(75.0,1.34),(80.5,1.52)]:round_band(TURRETS,cx,cy,zz,rr,10)
 window_frame(TURRETS,cx,cy,wyaw,76.5,.5,2.5,1.35)
 roof(TURRETS,cx,cy,80.6,1.6,10,17,16,True)

# South gate: split lower left foot exactly where existing cliff-facing recess is.
for sx in [-1,1]:
 cx=sx*4.1;cy=-18.5
 for side,ya in enumerate([0,math.pi/2,math.pi,-math.pi/2]):
  holes=[(-.61,.61,77.00,80.55)] if side==0 else []
  if sx==-1:
   courses(GATE,cx,cy,ya,3.0,72,81.80,1.51,10,3,side+sx,holes)
   # Lower block depth2 and center-18.0; never extended under the upper overhang.
   wid=3. if side in [0,2] else 2.;n=1.01 if side in [0,2] else 1.51
   courses(GATE,cx,-18.,ya,wid,68.51,71.98,n,4,3,side+sx)
  else:courses(GATE,cx,cy,ya,3.,68.51,81.80,1.51,14,3,side+sx,holes)
  band(GATE,cx,cy,ya,3.08,76.45,1.60,.13)
  band(GATE,cx,cy,ya,3.48,82.0,1.76,.11)
  if side!=0:band(GATE,cx,cy,ya,3.08,72.25,1.59,.08)
 window_frame(GATE,cx,cy,0,77.2,.8,3.,1.69)
 # Retain/refine three old blind lancets below the window, rather than mask them.
 for j in range(3):
  u=(j-1)*2.6/3;w=2.6/3
  for s in [-1,1]:panel(GATE,cx,cy,0,u+s*w*.39,74.02,.105,2.05,TRIM,1.69,1.80,.018)
  for s in [-1,1]:panel(GATE,cx,cy,0,u+s*w*.19,75.04,.095,.52,TRIM,1.69,1.82,.015,tilt=-s*.65)
 band(GATE,cx,cy,0,2.85,75.35,1.72,.13)
 roof(GATE,cx,cy,82.2,1.75,13.,22,20,True)

# Gate bridge front/back and exactly matched old seven-block arch face.
for side in [0,1]:
 yaw=side*math.pi
 courses(GATE,0,-18.5,yaw,4.99,78.41,82.30,1.211,5,5,21+side)
 band(GATE,0,-18.5,yaw,5.08,82.39,1.23,.14)
 # Inset heraldic shield and restrained vertical relief; no new opening/collision.
 pts=[(-.64,81.50),(.64,81.50),(.56,80.60),(0,80.07),(-.56,80.60)]
 solid(GATE,[at(0,-18.5,yaw,u,1.32,z) for u,z in pts],[at(0,-18.5,yaw,u,1.42,z) for u,z in pts],TRIM)
 pts=[(-.46,81.34),(.46,81.34),(.40,80.68),(0,80.30),(-.40,80.68)]
 solid(GATE,[at(0,-18.5,yaw,u,1.43,z) for u,z in pts],[at(0,-18.5,yaw,u,1.46,z) for u,z in pts],SLATE[1])
 panel(GATE,0,-18.5,yaw,0,80.92,.075,.78,GOLD,1.46,1.50,.009)
 panel(GATE,0,-18.5,yaw,0,81.05,.49,.065,GOLD,1.46,1.50,.009)
 for s in [-1,1]:
  for k in range(7):
   a=k/6*math.pi/2*.78;ox=2.4-3*(1-math.cos(a));oz=75.4+3*math.sin(a)
   # Same .5 x .62 box outline and X/Z rotation as old gate voussoirs.
   panel(GATE,0,-18.5,yaw,s*ox,oz,.5,.62,TRIM,1.255,1.34,.035,tilt=s*a)
for j in range(5):
 x=-2+j
 for side in [0,1]:panel(GATE,x,-19.55,side*math.pi,0,82.9,.60,1.,STONE[j%4],.205,.27,.035)
 GATE.rbox((.72,.55,.13),(x,-19.55,83.465),TRIM,cuts=0)

receivers=[RING.to_object('ring_wall_skin'),TURRETS.to_object('wall_turrets_skin'),GATE.to_object('gatehouse_skin')]
for ob in receivers:ob.data.calc_loop_triangles();print('GEOMETRY',ob.name,len(ob.data.loop_triangles),flush=True)
assert all(len(ob.data.loop_triangles)<30000 for ob in receivers)
assert sum(len(ob.data.loop_triangles) for ob in receivers)<65000
color_error=min(sum((d.color[i]-STONE[0][i])**2 for i in range(3)) for d in receivers[0].data.color_attributes['Col'].data)
assert color_error<1e-10,color_error
audit={'untouched_original_assets':True,'visual_only_no_collision':True,'ring_edge_indices':indices,'skipped_gate_edges':[11,12],'small_tower_centers':turret_centers,'left_gate_lower_foot':{'center':[-4.1,-18.,70.25],'original_size':[3.,2.,3.5],'upper_center_y':-18.5,'upper_base':72},'gate_arch':'14 original .5x.62 block fronts at same source x,z and tilt; depth skin only','glow_apertures':'existing front lancets retained, no replacement emission geometry','original_road_stair_terrain':'not edited or included','COLOR_0':'FLOAT_COLOR source; removed on export','linear_color_error':color_error}
(OUT/'geometry-audit.json').write_text(json.dumps(audit,indent=2))

# Same real diffuse COLOR+DIRECT+INDIRECT bake recipe as approved clock sample.
for ob in receivers:
 mat=bpy.data.materials.new(ob.name+'_source');mat.use_nodes=True;nt=mat.node_tree;pb=nt.nodes['Principled BSDF'];pb.inputs['Roughness'].default_value=.85
 attr=nt.nodes.new('ShaderNodeVertexColor');attr.layer_name='Col';nt.links.new(attr.outputs['Color'],pb.inputs['Base Color']);ob.data.materials.clear();ob.data.materials.append(mat)
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(55),island_margin=.002);bpy.ops.object.mode_set(mode='OBJECT')
for name in ['gothic_main','gothic_towers','gothic_wall']:
 bpy.ops.import_scene.gltf(filepath=str(Path('assets/castle_refit_v1/exterior',name+'.glb').resolve()))
interior=Path('assets/castle_refit_v1/interior/castle_rooms.glb')
if interior.exists():bpy.ops.import_scene.gltf(filepath=str(interior.resolve()))
world=bpy.data.worlds.new('v5_approximate_neutral_environment');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.65,.68,1);world.node_tree.nodes['Background'].inputs[1].default_value=.85;scene.world=world
for spec in json.loads(Path('assets/castle_refit_v1/interior/lighting-plan.json').read_text())['lights']:
 d=bpy.data.lights.new(spec['name'],'POINT');d.energy=spec['energy_watts']*2.4;d.color=spec['color'];d.shadow_soft_size=spec['radius'];ob=bpy.data.objects.new(spec['name'],d);scene.collection.objects.link(ob);ob.location=spec['position_blender']
scene.cycles.samples=48;scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=4
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/'wall-source.blend').resolve()))
report={'scope':'ring wall, five small round towers, southern gatehouse additive visual skins only','coordinate_contract':'world=(127+bx,bz,176+by); root127,0,176; no recenter','source':str(Path(__file__)),'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'lighting':{'approximation':'neutral World(.65,.65,.68)*.85, existing fixtures x2.4; NOT reconstruction of runtime skybox','cycles_samples':48,'max_bounces':6,'diffuse_bounces':4,'passes':['COLOR','DIRECT','INDIRECT'],'occluders':'existing full castle sources plus castle_rooms'},'targets':{}}
import numpy as np
for ob in receivers:
 source=ob.data.materials[0];nt=source.node_tree;im=bpy.data.images.new(ob.name+'_GI',2048,2048);tx=nt.nodes.new('ShaderNodeTexImage');tx.image=im;nt.nodes.active=tx
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.bake(type='DIFFUSE',pass_filter={'COLOR','DIRECT','INDIRECT'},margin=6,use_clear=True);im.filepath_raw=str((OUT/(ob.name+'-GI.png')).resolve());im.file_format='PNG';im.save()
 diag=bpy.data.images.new(ob.name+'_indirect',128,128);tx.image=diag;bpy.ops.object.bake(type='DIFFUSE',pass_filter={'INDIRECT'},margin=2,use_clear=True);diag.filepath_raw=str((OUT/(ob.name+'-indirect.png')).resolve());diag.file_format='PNG';diag.save();pixels=np.array(diag.pixels[:]).reshape(-1,4);valid=pixels[pixels[:,3]>.5,:3];stats={'max':float(valid.max()),'mean':float(valid.mean()),'nonzero_fraction':float((valid.max(axis=1)>1e-5).mean())};tx.image=im
 final=bpy.data.materials.new(ob.name+'_GI_PBR');final.use_nodes=True;pb=final.node_tree.nodes['Principled BSDF'];pb.inputs['Roughness'].default_value=.85;t=final.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;final.node_tree.links.new(t.outputs['Color'],pb.inputs['Base Color']);ob['final_material']=final.name
 dup=ob.copy();dup.data=ob.data.copy();scene.collection.objects.link(dup)
 for attr in list(dup.data.color_attributes):dup.data.color_attributes.remove(attr)
 dup.data.materials[0]=final;bpy.ops.object.select_all(action='DESELECT');dup.select_set(True)
 output=OUT/(ob.name+'.glb');bpy.ops.export_scene.gltf(filepath=str(output.resolve()),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_image_format='JPEG',export_jpeg_quality=94)
 verts1=[ob.matrix_world@v.co for v in ob.data.vertices];mn=[min(v[i] for v in verts1) for i in range(3)];mx=[max(v[i] for v in verts1) for i in range(3)]
 report['targets'][ob.name]={'material':final.name,'texture_size':2048,'indirect_evidence':stats,'triangles':len(ob.data.loop_triangles),'file':str(output),'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'normalization_scale':max(b-a for a,b in zip(mn,mx)),'glb_bounds':[[mn[0],mn[2],-mx[1]],[mx[0],mx[2],-mn[1]]],'blender_bounds':[mn,mx],'vertex_colors':False,'node':dup.name}
 bpy.data.objects.remove(dup,do_unlink=True)
 (OUT/'receipt.json').write_text(json.dumps(report,indent=2));print('EXPORTED',ob.name,flush=True)
for ob in receivers:ob.data.materials[0]=bpy.data.materials[ob['final_material']]
for im in bpy.data.images:
 if im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/'wall-baked.blend').resolve()))
for ob in receivers:
 mat=ob.data.materials[0].copy();nt=mat.node_tree;tex=next(n for n in nt.nodes if n.type=='TEX_IMAGE');out=nt.nodes.get('Material Output');em=nt.nodes.new('ShaderNodeEmission');nt.links.new(tex.outputs['Color'],em.inputs['Color']);nt.links.new(em.outputs[0],out.inputs['Surface']);ob.data.materials[0]=mat
cam=kit.preview_setup();scene.world=world;scene.cycles.samples=24
kit.shot(cam,str(OUT/'gatehouse-context.png'),(-14,-46,85),(0,-18.2,80),45,(1500,1250))
kit.shot(cam,str(OUT/'ring-wall-context.png'),(47,-50,105),(0,0,79),40,(1600,1250))
print('DONE',json.dumps(report),flush=True)
