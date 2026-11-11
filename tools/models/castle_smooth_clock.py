"""Left clock tower additive visual sample. No original source/scene mutation.
Blender -b -t 6 --python tools/models/castle_sample_clock.py
Original absolute coordinates retained: world=(127+bx,bz,176+by).
"""
import bpy,bmesh,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent));import kit
OUT=Path('assets/castle_smooth_v7/facade/clock');OUT.mkdir(parents=True,exist_ok=True)
class LinearMesh(kit.Mesh):
    def __init__(self):
        self.bm=bmesh.new()
        self.col=self.bm.loops.layers.float_color.new('Col')
kit.reset();scene=bpy.context.scene;CX,CY=-9.5,-8.;P=LinearMesh();D=LinearMesh()
STONE=[kit.srgb(h) for h in ['#98929D','#A19BA4','#918D99','#ABA2AA']]
TRIM=kit.srgb('#C1B6B8');DEEP=kit.srgb('#6B6475');SLATE=[kit.srgb(h) for h in ['#55566D','#595B70','#53566B','#5D5E73']];GOLD=kit.srgb('#C3A36A');GOLDLIGHT=kit.srgb('#D8BD86');DIAL=kit.srgb('#D8CEBC');INK=kit.srgb('#38394D')

def at(u,n,z,yaw):return (CX+math.cos(yaw)*u+math.sin(yaw)*n,CY+math.sin(yaw)*u-math.cos(yaw)*n,z)
def poly(mesh,xy,yfront,yback,col):
    # X/Z polygon, outward toward world south. Recalculated normals on final mesh.
    vs=[mesh.bm.verts.new((x,y,z)) for y in (yback,yfront) for x,z in xy];n=len(xy)
    mesh.bm.faces.new(vs[:n][::-1]);mesh.bm.faces.new(vs[n:])
    for i in range(n):j=(i+1)%n;mesh.bm.faces.new([vs[i],vs[j],vs[n+j],vs[n+i]])
    mesh.paint(vs,col)
def panel(mesh,u,z,w,h,yaw,col,back=2.53,front=2.625,chamfer=.025):
    if w<.06 or h<.06:return
    backpts=[(u-w/2,z-h/2),(u+w/2,z-h/2),(u+w/2,z+h/2),(u-w/2,z+h/2)]
    c=min(chamfer,w*.2,h*.2);frontpts=[(u-w/2+c,z-h/2+c),(u+w/2-c,z-h/2+c),(u+w/2-c,z+h/2-c),(u-w/2+c,z+h/2-c)]
    vs=[mesh.bm.verts.new(at(x,back,zz,yaw)) for x,zz in backpts]+[mesh.bm.verts.new(at(x,front,zz,yaw)) for x,zz in frontpts]
    for ix in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:mesh.bm.faces.new([vs[i] for i in ix])
    mesh.paint(vs,col)
def square_ring(z,profile):
    rings=[]
    for r,dz in profile:
        c=.13;xy=[(-r+c,-r),(r-c,-r),(r,-r+c),(r,r-c),(r-c,r),(-r+c,r),(-r,r-c),(-r,-r+c)]
        rings.append([P.bm.verts.new((CX+x,CY+y,z+dz)) for x,y in xy])
    for a,b in zip(rings,rings[1:]+rings[:1]):
        for i in range(8):j=(i+1)%8;P.bm.faces.new([a[i],a[j],b[j],b[i]])
    P.paint([v for rr in rings for v in rr],TRIM)

# Fine chamfered ashlar over original exterior only. Aperture cutouts retain all glow.
win_z=[73.98,82.98,91.98];WH=5.58
for face,yaw in enumerate([0,math.pi/2,math.pi,-math.pi/2]):
    breaks=sorted(set([72.30,98.8,76.42]+[z-.20 for z in win_z]+[z+WH+.20 for z in win_z]))
    for za,zb in zip(breaks,breaks[1:]):
        if za<72.30 or zb>98.8:continue
        if face==1 and za<76.42:continue
        mid=(za+zb)/2;spans=[(-2.5,2.5)]
        if any(z-.20<mid<z+WH+.20 for z in win_z):spans=[(-2.5,-.83),(.83,2.5)]
        for a,b in spans:panel(P,(a+b)/2,mid,b-a,zb-za,yaw,STONE[0],2.53,2.625,0)
    # Beveled lintel/sill surrounds and pointed arch voussoirs.
    for wz in win_z:
        if face==1 and wz<76.42:continue
        for side in [-1,1]:
            for k in range(4):panel(P,side*.66,wz+(k+.5)*4.98/4,.21,4.98/4-.018,yaw,TRIM,2.65,2.82,.026)
        panel(P,0,wz-.15,1.72,.25,yaw,TRIM,2.60,2.90,.055)
        # Two shallow curved arch arms; inner edge clears original luminous diamond.
        for side in [-1,1]:
            for k in range(6):
                pts=[]
                for t in [k/6,(k+1)/6]:
                    pts.append((side*.55*(1-t),wz+4.98+.62*math.sqrt(t)))
                for t in [(k+1)/6,k/6]:pts.append((side*.79*(1-t),wz+4.98+.87*math.sqrt(t)))
                vs=[P.bm.verts.new(at(u,n,z,yaw)) for n in [2.65,2.83] for u,z in pts]
                for ix in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:P.bm.faces.new([vs[i] for i in ix])
                P.paint(vs,TRIM)
        panel(P,0,wz+2.45,.075,4.90,yaw,GOLD,2.72,2.84,.015)
        panel(P,0,wz+3.087,1.05,.07,yaw,GOLD,2.72,2.84,.012)

# Quoin sleeves follow each original stepped corner footprint, rather than enlarging tower.
for sx in [-1,1]:
 for sy in [-1,1]:
  for level in range(3):
    s=.95*(1-level*.18);center=2.5+s*.22;outer=center+s/2
    z=72+level*9+4.5
    for yaw,u in [(0 if sy==-1 else math.pi,sx*center*(1 if sy==-1 else -1)),(math.pi/2 if sx==1 else -math.pi/2,sy*center*(1 if sx==1 else -1))]:
        panel(P,u,z,s+.025,9.0,yaw,STONE[0],outer-.008,outer+.045,0)
for z in [78.75,85.5,92.25,99.0]:square_ring(z,[(2.71,-.23),(2.82,-.14),(2.84,.09),(2.77,.22),(2.54,.22),(2.54,-.23)])
square_ring(99.25,[(2.91,-.24),(3.0,-.10),(3.02,.13),(2.95,.29),(2.55,.29),(2.55,-.24)])
for yaw in [0,math.pi/2,math.pi,-math.pi/2]:
 for i in range(4):
    u=(i+.5)/4*5-2.5;panel(P,u,99.95,.70,1.08,yaw,STONE[1],2.865,2.92,.035)
    panel(P,u,100.51,.79,.16,yaw,TRIM,2.85,2.99,.035)

# Individual overlapping slate shingles, 28 courses; old cone and gold ribs sit beneath.
for row in range(28):
 t0=row/28;t1=(row+1)/28;z0=99.4+21*t0;z1=99.4+21*t1
 r0=2.15*(1-t0)**1.08+.025+.12*(1-t0)+.018;r1=2.15*(1-t1)**1.08+.025+.12*(1-t1)+.018
 for j in range(24):
    a0=(j+.012)*math.tau/24;a1=(j+.988)*math.tau/24
    vv=[(CX+r0*math.cos(a0),CY+r0*math.sin(a0),z0),(CX+r0*math.cos(a1),CY+r0*math.sin(a1),z0),(CX+r1*math.cos(a1),CY+r1*math.sin(a1),z1+.025),(CX+r1*math.cos(a0),CY+r1*math.sin(a0),z1+.025),(CX+(r0+.018)*math.cos(a0),CY+(r0+.018)*math.sin(a0),z0-.04),(CX+(r0+.018)*math.cos(a1),CY+(r0+.018)*math.sin(a1),z0-.04)]
    vs=[P.bm.verts.new(v) for v in vv];P.bm.faces.new(vs[:4]);P.bm.faces.new([vs[0],vs[4],vs[5],vs[1]]);P.paint(vs,SLATE[((j*17+row*31)^(j*row*7))%4])

# Opaque clock replacement over the entire original glowing clock. Two atlases keep numerals readable.
D.cyl(2.22,2.22,.12,(CX,-11.0,91),TRIM,48,(math.pi/2,0,0))
D.cyl(1.91,1.91,.035,(CX,-11.083,91),DIAL,48,(math.pi/2,0,0))
def dial_ring(profile,col):
    rings=[]
    for r,y in profile:rings.append([D.bm.verts.new((CX+math.sin(i*math.tau/48)*r,y,91+math.cos(i*math.tau/48)*r)) for i in range(48)])
    for a,b in zip(rings,rings[1:]+rings[:1]):
        for i in range(48):j=(i+1)%48;D.bm.faces.new([a[i],a[j],b[j],b[i]])
    D.paint([v for rr in rings for v in rr],col)
dial_ring([(2.22,-11.04),(2.24,-11.10),(2.19,-11.15),(2.02,-11.15),(1.96,-11.10),(1.96,-11.04)],TRIM)
dial_ring([(1.98,-11.12),(1.97,-11.17),(1.91,-11.17),(1.90,-11.12)],GOLD)
dial_ring([(1.20,-11.105),(1.20,-11.125),(1.175,-11.125),(1.175,-11.105)],GOLD)
for i in range(60):
    a=i*math.tau/60;r=1.81;L=.17 if i%5==0 else .07;W=.040 if i%5==0 else .018
    pts=[]
    for tangent,radial in [(-W/2,-L/2),(W/2,-L/2),(W/2,L/2),(-W/2,L/2)]:pts.append((CX+math.sin(a)*(r+radial)+math.cos(a)*tangent,91+math.cos(a)*(r+radial)-math.sin(a)*tangent))
    vs=[D.bm.verts.new((x,-11.134,z)) for x,z in pts];D.bm.faces.new(vs);D.paint(vs,INK)
# Raised diamond hands, 10:10; visual only, no changes to gameplay time.
for a,L,W in [(math.radians(-55),1.06,.12),(math.radians(60),1.47,.09)]:
    pts=[]
    for tangent,radial in [(0,-.23),(-W,.25),(0,L),(W,.25)]:pts.append((CX+math.sin(a)*radial+math.cos(a)*tangent,91+math.cos(a)*radial-math.sin(a)*tangent))
    poly(D,pts,-11.205,-11.165,INK)
D.cyl(.13,.13,.06,(CX,-11.205,91),GOLDLIGHT,24,(math.pi/2,0,0))
for i in range(12):
 a=i*math.tau/12;D.cyl(.046,.046,.014,(CX+2.1*math.sin(a),-11.17,91+2.1*math.cos(a)),GOLD,8,(math.pi/2,0,0))
skin=P.to_object('clocktower_skin_receiver');dial=D.to_object('clock_face_receiver')
# Small, crisp actual Roman-number geometry on the dial.
font_path=Path('/System/Library/Fonts/Supplemental/Times New Roman.ttf');font=bpy.data.fonts.load(str(font_path)) if font_path.exists() else None
text_obs=[]
for i,s in enumerate(['XII','I','II','III','IV','V','VI','VII','VIII','IX','X','XI']):
 a=i*math.tau/12;cu=bpy.data.curves.new('roman_'+s,'FONT');cu.body=s;cu.align_x='CENTER';cu.align_y='CENTER';cu.size=.31;cu.extrude=0.0;cu.resolution_u=2
 if font:cu.font=font
 ob=bpy.data.objects.new('roman_'+s,cu);scene.collection.objects.link(ob);ob.location=(CX+1.53*math.sin(a),-11.15,91+1.53*math.cos(a));ob.rotation_euler=(math.pi/2,0,0)
 bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob=bpy.context.object
 attr=ob.data.color_attributes.new(name='Col',type='FLOAT_COLOR',domain='CORNER')
 for c in attr.data:c.color=INK
 ob.select_set(False);text_obs.append(ob)
bpy.ops.object.select_all(action='DESELECT');dial.select_set(True)
for ob in text_obs:ob.select_set(True)
bpy.context.view_layer.objects.active=dial;bpy.ops.object.join()
receivers=[skin,dial]
color_error=min(sum((d.color[i]-STONE[0][i])**2 for i in range(3)) for d in skin.data.color_attributes['Col'].data)
assert color_error<1e-10,color_error
(OUT/'color-space-audit.json').write_text(json.dumps({'source_hex':'#98929D','expected_linear_rgb':STONE[0][:3],'storage':'FLOAT_COLOR from BMesh float_color; linear values retained directly','closest_stored_squared_error':color_error,'no_double_srgb_decode':True},indent=2))
for ob in receivers:
 ob.data.calc_loop_triangles();print('GEOMETRY',ob.name,len(ob.data.loop_triangles))
assert sum(len(ob.data.loop_triangles) for ob in receivers)<22000

# Genuine Cycles diffuse color/direct/indirect bake; no AO substitute.
for ob in receivers:
 mat=bpy.data.materials.new(ob.name+'_source_material');mat.use_nodes=True;nt=mat.node_tree;pb=nt.nodes['Principled BSDF'];pb.inputs['Roughness'].default_value=.85
 attr=nt.nodes.new('ShaderNodeVertexColor');attr.layer_name='Col';nt.links.new(attr.outputs['Color'],pb.inputs['Base Color']);ob.data.materials.clear();ob.data.materials.append(mat)
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(55),island_margin=.003);bpy.ops.object.mode_set(mode='OBJECT')
occluders=[]
for name in ['gothic_main','gothic_towers','gothic_wall']:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(Path('assets/castle_refit_v1/exterior',name+'.glb').resolve()));occluders.extend(set(bpy.data.objects)-before)
interior=Path('assets/castle_refit_v1/interior/castle_rooms.glb')
if interior.exists():bpy.ops.import_scene.gltf(filepath=str(interior.resolve()))
world=bpy.data.worlds.new('sample_approximate_neutral_environment');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.65,.68,1);world.node_tree.nodes['Background'].inputs[1].default_value=.85;scene.world=world
for spec in json.loads(Path('assets/castle_refit_v1/interior/lighting-plan.json').read_text())['lights']:
 d=bpy.data.lights.new(spec['name'],'POINT');d.energy=spec['energy_watts']*2.4;d.color=spec['color'];d.shadow_soft_size=spec['radius'];ob=bpy.data.objects.new(spec['name'],d);scene.collection.objects.link(ob);ob.location=spec['position_blender']
scene.cycles.samples=48;scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=4
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/'clock-source.blend').resolve()))
report={'scope':'only LEFT clock tower additive visual skin; no collisions; original castle untouched','coordinate_contract':'world=(127+bx,bz,176+by); root127,0,176; do not recenter','lighting':{'approximation':'neutral World(.65,.65,.68)*.85, existing fixtures×2.4; NOT reconstruction of original skybox','actual_environment_reference':'parent environment-before: sunpitch40 yaw60 #a8c2ff .95, ambient#6b6b9e','cycles_samples':48,'max_bounces':6,'diffuse_bounces':4,'passes':['COLOR','DIRECT','INDIRECT'],'occluders':'existing fullcastle sources+castle_rooms'},'targets':{}}
import numpy as np
for ob in receivers:
 source=ob.data.materials[0];nt=source.node_tree;size=2048 if ob==skin else 1024;im=bpy.data.images.new(ob.name+'_GI',size,size);tx=nt.nodes.new('ShaderNodeTexImage');tx.image=im;nt.nodes.active=tx
 bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.bake(type='DIFFUSE',pass_filter={'COLOR','DIRECT','INDIRECT'},margin=6,use_clear=True);im.filepath_raw=str((OUT/(ob.name+'-GI.png')).resolve());im.file_format='PNG';im.save()
 diag=bpy.data.images.new(ob.name+'_indirect',128,128);tx.image=diag;bpy.ops.object.bake(type='DIFFUSE',pass_filter={'INDIRECT'},margin=2,use_clear=True);diag.filepath_raw=str((OUT/(ob.name+'-indirect.png')).resolve());diag.file_format='PNG';diag.save();pixels=np.array(diag.pixels[:]).reshape(-1,4);valid=pixels[pixels[:,3]>.5,:3];stats={'max':float(valid.max()),'mean':float(valid.mean()),'nonzero_fraction':float((valid.max(axis=1)>1e-5).mean())};tx.image=im
 final=bpy.data.materials.new(ob.name+'_GI_PBR');final.use_nodes=True;pb=final.node_tree.nodes['Principled BSDF'];pb.inputs['Roughness'].default_value=.85;t=final.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;final.node_tree.links.new(t.outputs['Color'],pb.inputs['Base Color']);ob['final_material']=final.name
 report['targets'][ob.name]={'material':final.name,'texture_size':size,'indirect_evidence':stats,'triangles':len(ob.data.loop_triangles)}
# Export copies without COLOR_0 and with GI carried in BaseColor for parent's fixed GI shader.
exports=[]
for ob in receivers:
 dup=ob.copy();dup.data=ob.data.copy();scene.collection.objects.link(dup)
 for attr in list(dup.data.color_attributes):dup.data.color_attributes.remove(attr)
 dup.data.materials[0]=bpy.data.materials[ob['final_material']];exports.append(dup)
bpy.ops.object.select_all(action='DESELECT')
for ob in exports:ob.select_set(True)
output=OUT/'clocktower-smooth-v7.glb';bpy.ops.export_scene.gltf(filepath=str(output.resolve()),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_image_format='JPEG',export_jpeg_quality=94)
verts=[ob.matrix_world@v.co for ob in exports for v in ob.data.vertices];mn=[min(v[i] for v in verts) for i in range(3)];mx=[max(v[i] for v in verts) for i in range(3)]
report.update(file=str(output),bytes=output.stat().st_size,sha256=hashlib.sha256(output.read_bytes()).hexdigest(),normalization_scale=max(b-a for a,b in zip(mn,mx)),glb_bounds=[[mn[0],mn[2],-mx[1]],[mx[0],mx[2],-mn[1]]],triangles=sum(len(ob.data.loop_triangles) for ob in receivers),vertex_colors=False)
report['glb_nodes']=[ob.name for ob in exports];report['glb_materials']=[ob.data.materials[0].name for ob in exports];report['color_space_audit']='color-space-audit.json'
(OUT/'receipt.json').write_text(json.dumps(report,indent=2))
for ob in exports:bpy.data.objects.remove(ob,do_unlink=True)
for ob in receivers:ob.data.materials[0]=bpy.data.materials[ob['final_material']]
for im in bpy.data.images:
 if im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/'clock-baked.blend').resolve()))
# Preview fixed GI display using emission to avoid multiplying lighting twice.
for ob in receivers:
 mat=ob.data.materials[0].copy();nt=mat.node_tree;tex=next(n for n in nt.nodes if n.type=='TEX_IMAGE');out=nt.nodes.get('Material Output');em=nt.nodes.new('ShaderNodeEmission');nt.links.new(tex.outputs['Color'],em.inputs['Color']);nt.links.new(em.outputs[0],out.inputs['Surface']);ob.data.materials[0]=mat
cam=kit.preview_setup();scene.world=world;scene.cycles.samples=24
kit.shot(cam,str(OUT/'clocktower-context.png'),(-38,-62,106),(-6,-5,99),42,(1400,1500))
kit.shot(cam,str(OUT/'clocktower-close.png'),(-16,-30,94),(CX,-10.8,91.5),60,(1300,1300))
print('CLOCK DONE',json.dumps(report))
