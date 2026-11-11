"""Accepted clock-sample style expanded only to remaining castle towers.
Independent additive visual GLBs; never edits original models, instances or collision.
Blender -b -t 6 --python tools/models/castle_expand_towers.py
"""
import bpy,bmesh,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent));import kit
OUT=Path('assets/castle_expand_v5/towers');OUT.mkdir(parents=True,exist_ok=True)
class LinearMesh(kit.Mesh):
 def __init__(self):self.bm=bmesh.new();self.col=self.bm.loops.layers.float_color.new('Col');self.outward=[]
 def to_object(self,name):
  self.bm.normal_update();bmesh.ops.recalc_face_normals(self.bm,faces=list(self.bm.faces));flips=0
  for face,cx,cy in self.outward:
   c=face.calc_center_median();radial=Vector((c.x-cx,c.y-cy,0))
   if face.normal.dot(radial)<0:face.normal_flip();flips+=1
  self.bm.normal_update()
  assert all(f.normal.dot(Vector((f.calc_center_median().x-cx,f.calc_center_median().y-cy,0)))>0 for f,cx,cy in self.outward)
  me=bpy.data.meshes.new(name);self.bm.to_mesh(me);self.bm.free();ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob);ob['open_faces_checked']=len(self.outward);ob['open_faces_corrected']=flips;return ob
STONE=[kit.srgb(h) for h in ['#98929D','#A19BA4','#918D99','#ABA2AA']]
TRIM=kit.srgb('#C1B6B8');SLATE=[kit.srgb(h) for h in ['#55566D','#595B70','#53566B','#5D5E73']];GOLD=kit.srgb('#C3A36A');DARK=kit.srgb('#6B6475');TAU=math.tau
kit.reset();scene=bpy.context.scene

def at(cx,cy,u,n,z,yaw):return(cx+math.cos(yaw)*u+math.sin(yaw)*n,cy+math.sin(yaw)*u-math.cos(yaw)*n,z)
def hexa(P,coords,col):
 vs=[P.bm.verts.new(v) for v in coords]
 for ix in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:P.bm.faces.new([vs[i] for i in ix])
 P.paint(vs,col)
def panel(P,cx,cy,u,z,w,h,yaw,col,back,front,c=.025):
 if w<.055 or h<.055:return
 c=min(c,w*.2,h*.2)
 lo=[(u-w/2,z-h/2),(u+w/2,z-h/2),(u+w/2,z+h/2),(u-w/2,z+h/2)]
 hi=[(u-w/2+c,z-h/2+c),(u+w/2-c,z-h/2+c),(u+w/2-c,z+h/2-c),(u-w/2+c,z+h/2-c)]
 hexa(P,[at(cx,cy,x,back,zz,yaw) for x,zz in lo]+[at(cx,cy,x,front,zz,yaw) for x,zz in hi],col)
def ring(P,cx,cy,z,prof,col,segments=16,phase=0,square=False):
 rings=[]
 for r,dz in prof:
  if square:
   c=.13;xy=[(-r+c,-r),(r-c,-r),(r,-r+c),(r,r-c),(r-c,r),(-r+c,r),(-r,r-c),(-r,-r+c)]
  else:xy=[(r*math.cos(i*TAU/segments+phase),r*math.sin(i*TAU/segments+phase)) for i in range(segments)]
  rings.append([P.bm.verts.new((cx+x,cy+y,z+dz)) for x,y in xy])
 n=len(rings[0])
 for a,b in zip(rings,rings[1:]+rings[:1]):
  for i in range(n):j=(i+1)%n;P.bm.faces.new([a[i],a[j],b[j],b[i]])
 P.paint([v for rr in rings for v in rr],col)
def band(P,cx,cy,z,r,square=False,segments=16,phase=0):
 ring(P,cx,cy,z,[(r-.04,-.17),(r+.045,-.10),(r+.06,.10),(r-.02,.17),(r-.22,.17),(r-.22,-.17)],TRIM,segments,phase,square)
def window(P,cx,cy,yaw,u,z,w,h,n,rect=False):
 spring=h-w*.6 if not rect else h
 for s in [-1,1]:
  count=max(2,int(spring/1.25))
  for k in range(count):panel(P,cx,cy,u+s*(w/2+.12),z+(k+.5)*spring/count,.20,spring/count-.018,yaw,TRIM,n+.13,n+.30,.025)
 panel(P,cx,cy,u,z-.14,w+.70,.24,yaw,TRIM,n+.10,n+.35,.045)
 if rect:panel(P,cx,cy,u,z+h+.12,w+.55,.22,yaw,TRIM,n+.1,n+.30,.03)
 else:
  for s in [-1,1]:
   for k in range(5):
    pts=[]
    for t in [k/5,(k+1)/5]:pts.append((u+s*(w/2+.02)*(1-t),z+spring+(w*.6+.02)*math.sqrt(t)))
    for t in [(k+1)/5,k/5]:pts.append((u+s*(w/2+.24)*(1-t),z+spring+(w*.6+.23)*math.sqrt(t)))
    hexa(P,[at(cx,cy,x,nn,zz,yaw) for nn in [n+.13,n+.30] for x,zz in pts],TRIM)
 panel(P,cx,cy,u,z+spring/2,.070,spring,yaw,GOLD,n+.14,n+.31,.012)
 if not rect:panel(P,cx,cy,u,z+spring*.62,w*.97,.07,yaw,GOLD,n+.14,n+.31,.012)
def subtract(spans,a,b):
 out=[]
 for lo,hi in spans:
  if hi<=a or lo>=b:out.append((lo,hi));continue
  if lo<a:out.append((lo,a))
  if hi>b:out.append((b,hi))
 return out

def square_skin(P,cx,cy,z,h,w,windows,room_side=None):
 rows=max(6,int(h));dz=h/rows
 for face,yaw in enumerate([0,math.pi/2,math.pi,-math.pi/2]):
  for row in range(rows):
   za=z+.16+row*dz;zb=min(z+h-.15,za+dz)
   if room_side and abs(math.sin(yaw))>.5 and math.sin(yaw)*room_side>0 and za<z+4.45:continue
   spans=[(-w/2,w/2)]
   for wu,wz,ww,wh in windows:
    if zb>wz-.28 and za<wz+wh+.24:spans=subtract(spans,wu-ww/2-.28,wu+ww/2+.28)
   for lo,hi in spans:
    q=-w/2-1.1+(row%2)*.55
    while q<hi:
     a=max(lo,q);b=min(hi,q+1.1)
     if b-a>.075:panel(P,cx,cy,(a+b)/2,(za+zb)/2,b-a-.022,zb-za-.022,yaw,STONE[(row*3+int(q*17)+face)%4],w/2+.03,w/2+.125)
     q+=1.1
  for wu,wz,ww,wh in windows:
   if room_side and abs(math.sin(yaw))>.5 and math.sin(yaw)*room_side>0 and wz<z+4.45:continue
   window(P,cx,cy,yaw,wu,wz,ww,wh,w/2)

def roof(P,cx,cy,z,r,h,rows=None,cols=24,ridges=True):
 rows=rows or max(8,int(h/.80))
 def rr(t):return r*(1-t)**1.08+.025+.12*(1-t)+.018
 for row in range(rows):
  t0=row/rows;t1=(row+1)/rows;z0=z+h*t0;z1=z+h*t1;r0=rr(t0);r1=rr(t1)
  for j in range(cols):
   a0=(j+.012)*TAU/cols;a1=(j+.988)*TAU/cols
   vv=[(cx+r0*math.cos(a0),cy+r0*math.sin(a0),z0),(cx+r0*math.cos(a1),cy+r0*math.sin(a1),z0),(cx+r1*math.cos(a1),cy+r1*math.sin(a1),z1+.022),(cx+r1*math.cos(a0),cy+r1*math.sin(a0),z1+.022),(cx+(r0+.018)*math.cos(a0),cy+(r0+.018)*math.sin(a0),z0-.035),(cx+(r0+.018)*math.cos(a1),cy+(r0+.018)*math.sin(a1),z0-.035)]
   vs=[P.bm.verts.new(v) for v in vv];fa=P.bm.faces.new(vs[:4]);fb=P.bm.faces.new([vs[0],vs[4],vs[5],vs[1]]);P.outward.extend([(fa,cx,cy),(fb,cx,cy)]);P.paint(vs,SLATE[((j*17+row*31)^(j*row*7))%4])
 if ridges:
  for j in range(8):
   a=j*TAU/8;ts=[0,.25,.50,.75,1];pts=[(cx+(rr(t)+.018)*math.cos(a),cy+(rr(t)+.018)*math.sin(a),z+h*t) for t in ts];P.tube(pts,[.025,.023,.020,.017,.012],GOLD,seg=4)
 ring(P,cx,cy,z+.16,[(r*1.10+.01,-.17),(r*1.10+.02,-.08),(r+.08,.16),(r-.04,.16),(r-.04,-.17)],GOLD,16)
 P.sphere(max(r*.1,.2)+.006,(cx,cy,z+h+.05),GOLD,seg=8)
 P.cyl(.104,.012,2.60,(cx,cy,z+h+1.30),GOLD,6)

def cylinder_skin(P,cx,cy,z,h,r0,r1,windows=(),rows=18,cols=16,rect_frames=False):
 for row in range(rows):
  za=z+row*h/rows;zb=z+(row+1)*h/rows;ra=r0+(r1-r0)*row/rows;rb=r0+(r1-r0)*(row+1)/rows
  holes=[]
  for yaw,wz,ww,wh,n in windows:
   if zb>wz-.27 and za<wz+wh+.23:
    a=(yaw-math.pi/2)%TAU;half=math.asin(min(.9,(ww/2+.28)/n))
    holes.extend([(a-half+k*TAU,a+half+k*TAU) for k in [-1,0,1]])
  for col in range(cols):
   a0=col*TAU/cols+.005;a1=(col+1)*TAU/cols-.005;spans=[(a0,a1)]
   for ha,hb in holes:spans=subtract(spans,ha,hb)
   for aa,bb in spans:
    if bb-aa<.025:continue
    lo=[(aa,za+.015,ra+.025),(bb,za+.015,ra+.025),(bb,zb-.015,rb+.025),(aa,zb-.015,rb+.025)]
    hi=[(aa+.004,za+.04,ra+.085),(bb-.004,za+.04,ra+.085),(bb-.004,zb-.04,rb+.085),(aa+.004,zb-.04,rb+.085)]
    hexa(P,[(cx+r*math.cos(a),cy+r*math.sin(a),zz) for a,zz,r in lo+hi],STONE[(row*3+col)%4])
 for yaw,wz,ww,wh,n in windows:window(P,cx,cy,yaw,0,wz,ww,wh,n,rect=rect_frames)

def pinnacle(P,x,y,z,r,h):
 # Existing four-sided stone cap with matching phase; chamfered base sleeves.
 for yaw in [0,math.pi/2,math.pi,-math.pi/2]:
  nr=max(2,int(h*.3/.9))
  for k in range(nr):panel(P,x,y,0,z+(k+.5)*h*.3/nr,r*2,h*.3/nr-.02,yaw,TRIM,r-.005,r+.04,.025)
 # Linear pyramid from original square-cone radius1.25r, top atz+1.02h.
 rings=[];rows=max(4,int(h*.72/.85))
 for j in range(rows):
  t0=j/rows;t1=(j+1)/rows;ra=r*1.25*(1-t0)+.025;rb=r*1.25*(1-t1)+.025
  for k in range(4):
   aa=(k+.0)*TAU/4+math.pi/4;bb=(k+1)*TAU/4+math.pi/4
   vs=[P.bm.verts.new((x+rr*math.cos(a),y+rr*math.sin(a),zz)) for a,zz,rr in [(aa,z+h*.3+h*.72*t0,ra),(bb,z+h*.3+h*.72*t0,ra),(bb,z+h*.3+h*.72*t1,rb),(aa,z+h*.3+h*.72*t1,rb)]];ff=P.bm.faces.new(vs);P.outward.append((ff,x,y));P.paint(vs,TRIM if j%3 else STONE[3])
 P.sphere(r*.28+.007,(x,y,z+h),GOLD,seg=6)
def auxiliary(P,cx,cy,z,h,w):
 for sx in [-1,1]:
  for sy in [-1,1]:
   pinnacle(P,cx+sx*w*.5,cy+sy*w*.5,z+h+.4,w*.09,w*1.25)
   x=cx+sx*(w/2+.55);y=cy+sy*(w/2+.55);base=z+h*.5;rr=w*.12;nh=h*.36
   # Original needle windows are broad glowing rectangular strip facing south/north.
   wins=[(0,base+nh*.74,rr*.7,nh*.16,rr),(math.pi,base+nh*.74,rr*.7,nh*.16,rr)]
   cylinder_skin(P,x,y,base,nh,rr,rr*.92,wins,rows=6,cols=8,rect_frames=True)
   for k in [1,2,3]:band(P,x,y,base+nh*k/3,rr*1.16,segments=8)
   roof(P,x,y,base+nh,rr*1.18,w*.95,rows=7,cols=12,ridges=False)

def right_tower():
 P=LinearMesh();cx,cy,z,h,w=9.3,-8.,72.,23.,4.6
 wh=h/3*.62;wins=[(0,z+h*(i+.22)/3,w*.2,wh) for i in range(3)]
 square_skin(P,cx,cy,z,h,w,wins,room_side=-1)
 for sx in [-1,1]:
  for sy in [-1,1]:
   for lv in range(3):
    s=w*.19*(1-lv*.18);center=w/2+s*.22;outer=center+s/2
    for k in range(7):
     zz=z+h*lv/3+(k+.5)*h/21
     for yaw,u in [(0 if sy==-1 else math.pi,sx*center*(1 if sy==-1 else -1)),(math.pi/2 if sx==1 else -math.pi/2,sy*center*(1 if sx==1 else -1))]:panel(P,cx,cy,u,zz,s+.025,h/21-.025,yaw,TRIM,outer-.005,outer+.045,.04)
 for k in [1,2,3]:band(P,cx,cy,z+h*k/3,w/2+.225,square=True)
 band(P,cx,cy,z+h+.25,w/2+.45,square=True)
 for yaw in [0,math.pi/2,math.pi,-math.pi/2]:
  for i in range(4):panel(P,cx,cy,(i+.5)/4*w-w/2,z+h+.95,w/4*.55,1.1,yaw,STONE[1],w/2+.365,w/2+.42,.035)
 roof(P,cx,cy,z+h+.4,w*.43,19)
 auxiliary(P,cx,cy,z,h,w)
 return P.to_object('expand_right_tower')
def center_tower():
 P=LinearMesh();cx,cy=0.,3.
 square_skin(P,cx,cy,94,12,9,[(u,95,1.25,8) for u in [-2.6,0,2.6]])
 for z in [94,100,106]:band(P,cx,cy,z,4.75,square=True)
 band(P,cx,cy,106.25,5.0,square=True)
 # Octagonal lantern; preserve its eight rectangular glow slots.
 wins=[]
 for i in range(8):
  a=(i+.5)*TAU/8;wins.append((a+math.pi/2,108.0,.95,3.8,3.82))
 # Cylinder shell alone; rectangular frames supplied below (avoid pointed-window copies).
 rawwindows=[(yaw,z,w,h,n) for yaw,z,w,h,n in wins]
 # Build masked cladding without automatic frames by temporarily collecting returned frame call.
 global window
 saved_window=window;window=lambda *a,**k:None
 cylinder_skin(P,cx,cy,106.4,7.,4.1,3.7,rawwindows,rows=7,cols=24)
 window=saved_window
 for yaw,z,w,h,n in wins:window(P,cx,cy,yaw,0,z,w,h,n,rect=True)
 for i in range(8):
  a=i*TAU/8;x=cx+math.cos(a)*3.95;y=cy+math.sin(a)*3.95
  for yaw in [0,math.pi/2,math.pi,-math.pi/2]:
   for j in range(7):panel(P,x,y,0,106.2+(j+.5)*7.4/7,.51,7.4/7-.018,yaw,TRIM,.245,.29,.025)
 band(P,cx,cy,113.6,4.5,segments=8,phase=math.pi/8)
 for sx in [-1,1]:
  for sy in [-1,1]:pinnacle(P,cx+sx*4.6,cy+sy*4.6,106.4,.6,12.)
 roof(P,cx,cy,113.7,3.2,23)
 return P.to_object('expand_central_tower')
def rear_towers():
 P=LinearMesh()
 for sx in [-1,1]:
  cx,cy=sx*11.,13.5;wins=[]
  for k in [1,2,3]:
   band(P,cx,cy,72+k*5.5,2.08,segments=10,phase=math.pi/10)
   for a in [0,2.1,4.2]:wins.append((a+(k%2)*1.,72+k*5.5+1.,.62,2.6,1.76))
  cylinder_skin(P,cx,cy,72,22,1.9,1.7,wins,rows=18,cols=16)
  roof(P,cx,cy,94,2.05,17,rows=21,cols=20)
 return P.to_object('expand_rear_towers')
left=LinearMesh();auxiliary(left,-9.5,-8.,72.,27.,5.)
receivers=[right_tower(),center_tower(),rear_towers(),left.to_object('expand_clock_auxiliary')]
geometry={}
for ob in receivers:
 ob.data.calc_loop_triangles();geometry[ob.name]=len(ob.data.loop_triangles)
print('GEOMETRY',json.dumps(geometry),flush=True)
assert all(n<30000 for n in geometry.values()),geometry
assert sum(geometry.values())<=70000,geometry
# Correct FLOAT_COLOR: verify requested linear stone value survives storage.
color_error=min(sum((d.color[i]-STONE[0][i])**2 for i in range(3)) for d in receivers[0].data.color_attributes['Col'].data);assert color_error<1e-10,color_error
for ob in receivers:
 mat=bpy.data.materials.new(ob.name+'_source');mat.use_nodes=True;nt=mat.node_tree;pb=nt.nodes['Principled BSDF'];pb.inputs['Roughness'].default_value=.85;attr=nt.nodes.new('ShaderNodeVertexColor');attr.layer_name='Col';nt.links.new(attr.outputs['Color'],pb.inputs['Base Color']);ob.data.materials.append(mat)
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(55),island_margin=.003);bpy.ops.object.mode_set(mode='OBJECT')
# Original castle and accepted sample mothers retained as source reflectors/occluders.
for name in ['gothic_main','gothic_towers','gothic_wall']:
 bpy.ops.import_scene.gltf(filepath=str(Path('assets/castle_refit_v1/exterior',name+'.glb').resolve()))
for path,prefixes in [(Path('assets/castle_sample_v3/clock/clock-source.blend'),('clocktower_skin_receiver','clock_face_receiver')),(Path('assets/castle_sample_v3/entrance/entrance-source.blend'),('entrance_',))]:
 if path.exists():
  with bpy.data.libraries.load(str(path.resolve()),link=False) as (a,b):b.objects=[n for n in a.objects if any(n.startswith(p) for p in prefixes)]
  for ob in b.objects:
   if ob:scene.collection.objects.link(ob)
interior=Path('assets/castle_refit_v1/interior/castle_rooms.glb')
if interior.exists():bpy.ops.import_scene.gltf(filepath=str(interior.resolve()))
world=bpy.data.worlds.new('accepted_sample_neutral_approximation');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.65,.68,1);world.node_tree.nodes['Background'].inputs[1].default_value=.85;scene.world=world
for spec in json.loads(Path('assets/castle_refit_v1/interior/lighting-plan.json').read_text())['lights']:
 d=bpy.data.lights.new(spec['name'],'POINT');d.energy=spec['energy_watts']*2.4;d.color=spec['color'];d.shadow_soft_size=spec['radius'];ob=bpy.data.objects.new(spec['name'],d);scene.collection.objects.link(ob);ob.location=spec['position_blender']
scene.cycles.samples=48;scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=4
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/'towers-source.blend').resolve()))
report={'scope':'remaining rightfront/central/rear towers and leftclock auxiliary needles; additive visual only; no collision','coordinates':'world=(127+BlenderX,BlenderZ,176+BlenderY); root127,0,176; no recenter','lighting':{'passes':['COLOR','DIRECT','INDIRECT'],'samples':48,'max_bounces':6,'diffuse_bounces':4,'environment':'same accepted neutral(.65,.65,.68)*.85 approximation, not source skybox reconstruction','fixtures':'existing lighting-plan ×2.4','occluders':'original fullcastle+interior+accepted sample source objects'},'palette':['#98929D','#A19BA4','#918D99','#ABA2AA','#C1B6B8','#55566D','#595B70','#53566B','#5D5E73'],'color_storage':'FLOAT_COLOR linear; no double sRGB','color_squared_error':color_error,'open_face_normal_audit':{o.name:{'checked':o['open_faces_checked'],'flipped_outward':o['open_faces_corrected']} for o in receivers},'outputs':{}}
for ob in receivers:
 mat=ob.data.materials[0];nt=mat.node_tree;size=1024 if ob.name=='expand_clock_auxiliary' else 2048;im=bpy.data.images.new(ob.name+'_GI',size,size);tx=nt.nodes.new('ShaderNodeTexImage');tx.image=im;nt.nodes.active=tx
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.bake(type='DIFFUSE',pass_filter={'COLOR','DIRECT','INDIRECT'},margin=6,use_clear=True);im.filepath_raw=str((OUT/(ob.name+'-GI.png')).resolve());im.file_format='PNG';im.save()
 diag=bpy.data.images.new(ob.name+'_indirect',128,128);tx.image=diag;bpy.ops.object.bake(type='DIFFUSE',pass_filter={'INDIRECT'},margin=2,use_clear=True);diag.filepath_raw=str((OUT/(ob.name+'-indirect.png')).resolve());diag.file_format='PNG';diag.save();pix=np.array(diag.pixels[:]).reshape(-1,4);valid=pix[pix[:,3]>.5,:3];stats={'mean':float(valid.mean()),'max':float(valid.max()),'nonzero_fraction':float((valid.max(axis=1)>1e-5).mean())};tx.image=im
 final=bpy.data.materials.new(ob.name+'_GI_PBR');final.use_nodes=True;pb=final.node_tree.nodes['Principled BSDF'];pb.inputs['Roughness'].default_value=.85;t=final.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;final.node_tree.links.new(t.outputs['Color'],pb.inputs['Base Color']);ob['final_material']=final.name
 dup=ob.copy();dup.data=ob.data.copy();dup.name=ob.name+'_GI';scene.collection.objects.link(dup)
 for attr in list(dup.data.color_attributes):dup.data.color_attributes.remove(attr)
 dup.data.materials[0]=final;bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
 out=OUT/(ob.name+'.glb');bpy.ops.export_scene.gltf(filepath=str(out.resolve()),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_image_format='JPEG',export_jpeg_quality=94)
 vv=[dup.matrix_world@v.co for v in dup.data.vertices];mn=[min(v[i] for v in vv) for i in range(3)];mx=[max(v[i] for v in vv) for i in range(3)];report['outputs'][ob.name]={'file':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'triangles':geometry[ob.name],'scale':max(b-a for a,b in zip(mn,mx)),'glb_bounds':[[mn[0],mn[2],-mx[1]],[mx[0],mx[2],-mn[1]]],'node':dup.name,'material':final.name,'texture_size':size,'vertex_colors':False,'indirect_evidence':stats};bpy.data.objects.remove(dup,do_unlink=True)
 (OUT/'receipt.json').write_text(json.dumps(report,indent=2));print('READY',ob.name,flush=True)
for ob in receivers:ob.data.materials[0]=bpy.data.materials[ob['final_material']]
for im in bpy.data.images:
 if im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/'towers-baked.blend').resolve()))
# Preview same fixed-GI display used by parent. Accepted sample source remains context only.
for ob in receivers:
 mat=ob.data.materials[0].copy();nt=mat.node_tree;tex=next(n for n in nt.nodes if n.type=='TEX_IMAGE');out=nt.nodes['Material Output'];em=nt.nodes.new('ShaderNodeEmission');nt.links.new(tex.outputs['Color'],em.inputs['Color']);nt.links.new(em.outputs[0],out.inputs['Surface']);ob.data.materials[0]=mat
cam=kit.preview_setup();scene.world=world;scene.cycles.samples=24
kit.shot(cam,str(OUT/'towers-front.png'),(48,-92,114),(0,1,103),40,(1500,1500))
kit.shot(cam,str(OUT/'towers-rear.png'),(-47,70,113),(0,5,101),42,(1500,1500))
kit.shot(cam,str(OUT/'central-close.png'),(17,-29,116),(0,3,111),48,(1300,1400))
print('TOWERS DONE',json.dumps(report),flush=True)
