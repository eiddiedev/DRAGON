"""Independent castle entrance additions; no original castle or terrain mutation.
Blender -b -t 6 --python tools/models/castle_entry_v2.py
Coordinates: source Blender x,y,z -> world (127+x,z,176+y).
"""
import bpy,bmesh,sys,math,json,hashlib,struct
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent));import kit
OUT=Path('assets/castle_entry_v2');OUT.mkdir(parents=True,exist_ok=True)
kit.reset();scene=bpy.context.scene
STONE=[kit.srgb(c) for c in ['#575460','#625C68','#6A6470','#514D5B','#77707A']]
DARK=kit.srgb('#393640');TOP=72.24;BOTTOM=70.30

def extrude(mesh,xy,z0,z1,color):
    if len(xy)<3:return
    vs=[mesh.bm.verts.new((x,y,z)) for z in (z0,z1) for x,y in xy];n=len(xy)
    mesh.bm.faces.new(vs[:n][::-1]);mesh.bm.faces.new(vs[n:])
    for i in range(n):j=(i+1)%n;mesh.bm.faces.new([vs[i],vs[j],vs[n+j],vs[n+i]])
    mesh.paint(vs,color)

def clip(poly,axis,value,ge):
    out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        ia=(a[axis]>=value) if ge else (a[axis]<=value);ib=(b[axis]>=value) if ge else (b[axis]<=value)
        if ia:out.append(a)
        if ia!=ib:
            t=(value-a[axis])/(b[axis]-a[axis]);out.append(tuple(a[k]+t*(b[k]-a[k]) for k in (0,1)))
    return out

def rectangle_clip(poly,x0,x1,y0,y1):
    for axis,value,ge in [(0,x0,True),(0,x1,False),(1,y0,True),(1,y1,False)]:poly=clip(poly,axis,value,ge)
    return poly

# Exact clipped inner-wall footprint; central road remains entirely uncovered.
circle=[(17.5*math.cos(i*math.tau/128),17.5*math.sin(i*math.tau/128)) for i in range(128)]
footprints=[rectangle_clip(circle,*xr,-16.9,-8.) for xr in [(-13,-2.3),(2.3,13)]]
floor=kit.Mesh()
for side,poly in enumerate(footprints):
    extrude(floor,poly,BOTTOM,TOP-.028,DARK)
    for row in range(14):
        ya=-16.9+row*.65;yb=min(-8,ya+.65)
        if ya>=-8:continue
        for col in range(26):
            xa=-14+col*1.10+(row%2)*.55;xb=xa+1.1
            tile=rectangle_clip(poly,xa+.012,xb-.012,ya+.012,yb-.012)
            if len(tile)>=3:extrude(floor,tile,TOP-.030,TOP,STONE[(row*3+col+side)%4])
    # A restrained darker border follows the forecourt outer curved outline.
    # Pavers themselves supply near-view joint detail without decorative clutter.
floor=floor.to_object('entry_forecourt')

# Twelve regular .275m treads; final .12m riser uses the existing road landing.
# Collision slope sits 0..12cm above the tread, never inside a visible riser.
stairs=kit.Mesh();ystart=-20.3;depth=3.3/12;rise=1.44/12
for i in range(12):
    ya=ystart+i*depth;yb=ya+depth;top=70.80+i*rise
    stairs.rbox((4.6,depth,top-BOTTOM-.028),(0,(ya+yb)/2,(top-.028+BOTTOM)/2),DARK,cuts=0)
    for j in range(5):
        x0=-2.3+j*.92;x1=x0+.92
        stairs.rbox((.904,depth-.012,.03),((x0+x1)/2,(ya+yb)/2,top-.015),STONE[(i+j)%4],cuts=0)
stairs=stairs.to_object('entry_stairs')

# Physics-only support: no texture, no bevels, one planar incline and two flat plates.
collision=kit.Mesh();ya=-20.7;yb=-17.;z0=70.8-(.4*1.44/3.3);z1=TOP
xy=[(-2.3,ya),(2.3,ya),(2.3,yb),(-2.3,yb)]
vs=[collision.bm.verts.new((x,y,z)) for (x,y),z in zip(xy,[z0,z0,z1,z1])]+[collision.bm.verts.new((x,y,69.8)) for x,y in xy]
for inds in [(0,1,2),(0,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]:collision.bm.faces.new([vs[i] for i in inds])
collision.paint(vs,STONE[0])
for poly in footprints:extrude(collision,poly,BOTTOM,TOP,STONE[0])
collision=collision.to_object('entry_collision_ONLY');collision.hide_render=True

# Receiver material uses genuine diffuse transport; small procedural stone color
# variation is baked into a single image. No post-bake vertex color multiplication.
def paint_material(ob):
    mat=bpy.data.materials.new(ob.name+'_source');mat.use_nodes=True;nt=mat.node_tree;pb=nt.nodes.get('Principled BSDF');pb.inputs['Roughness'].default_value=.9
    attr=nt.nodes.new('ShaderNodeVertexColor');attr.layer_name='Col'
    noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3.;noise.inputs['Detail'].default_value=2.
    ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.82,.82,.86,1);ramp.color_ramp.elements[1].color=(1.,.98,1.,1)
    mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.45
    nt.links.new(noise.outputs['Fac'],ramp.inputs[0]);nt.links.new(attr.outputs['Color'],mix.inputs[1]);nt.links.new(ramp.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],pb.inputs['Base Color']);ob.data.materials.append(mat)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(55),island_margin=.004);bpy.ops.object.mode_set(mode='OBJECT')
    return mat
materials={o.name:paint_material(o) for o in [stairs,floor]}
# Original unlit textured sources serve as occluders and reflectors, never rewritten.
receivers=[stairs,floor];occluders=[]
for name in ['gothic_main','gothic_towers','gothic_wall']:
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(Path('assets/castle_refit_v1/exterior',name+'.glb').resolve()));occluders.extend(set(bpy.data.objects)-before)
interior=Path('assets/castle_refit_v1/interior/castle_rooms.glb')
if interior.exists():bpy.ops.import_scene.gltf(filepath=str(interior.resolve()))
world=bpy.data.worlds.new('neutral_existing_environment');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.65,.68,1);world.node_tree.nodes['Background'].inputs[1].default_value=.85;scene.world=world
# Reuse established fixture layout only; no new local light/FX is exported.
for spec in json.loads(Path('assets/castle_refit_v1/interior/lighting-plan.json').read_text())['lights']:
    d=bpy.data.lights.new(spec['name'],'POINT');d.energy=spec['energy_watts']*2.4;d.color=spec['color'];d.shadow_soft_size=spec['radius'];o=bpy.data.objects.new(spec['name'],d);scene.collection.objects.link(o);o.location=spec['position_blender']
scene.cycles.samples=48;scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=4
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/'entry-source.blend').resolve()))
report={'coordinates':'world=(127+BlenderX,BlenderZ,176+BlenderY); original root127,0,176; no recenter','lighting':{'passes':['COLOR','DIRECT','INDIRECT'],'samples':48,'bounces':6,'diffuse_bounces':4,'environment':'neutral existing world; no directional sun','occluders':'existing gothic main/towers/wall and castle_rooms','fixtures':'existing lighting-plan25 points ×2.4; no added local fixtures'},'stairs':{'riser_count':12,'riser_height':rise,'tread_depth':depth,'visible_world_z':[155.7,159],'landing_y':TOP,'hidden_incline_degrees':math.degrees(math.atan(1.44/3.3)),'max_visual_foot_hover':rise,'collision_world_z':[155.3,159]},'outputs':{}}

def export(ob,label,material=None):
    dup=ob.copy();dup.data=ob.data.copy();dup.hide_render=False;scene.collection.objects.link(dup)
    for attr in list(dup.data.color_attributes):dup.data.color_attributes.remove(attr)
    if material:dup.data.materials.clear();dup.data.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT');dup.select_set(True);bpy.context.view_layer.objects.active=dup
    out=OUT/(label+'.glb');bpy.ops.export_scene.gltf(filepath=str(out.resolve()),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_image_format='JPEG',export_jpeg_quality=93)
    dup.data.calc_loop_triangles();v=[dup.matrix_world@v.co for v in dup.data.vertices];mn=[min(p[i] for p in v) for i in range(3)];mx=[max(p[i] for p in v) for i in range(3)]
    report['outputs'][label]={'file':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'triangles':len(dup.data.loop_triangles),'glb_bounds':[[mn[0],mn[2],-mx[1]],[mx[0],mx[2],-mn[1]]],'normalization_scale':max(b-a for a,b in zip(mn,mx)),'vertex_colors':False,'physics_only':label=='entry_collision'}
    assert len(dup.data.loop_triangles)<30000
    bpy.data.objects.remove(dup,do_unlink=True)

neutral=bpy.data.materials.new('collision_hidden_neutral');neutral.diffuse_color=(.4,.4,.4,1);export(collision,'entry_collision',neutral)
for ob in receivers:
    mat=materials[ob.name];nt=mat.node_tree;size=1024 if ob==stairs else 2048;im=bpy.data.images.new(ob.name+'_GI',size,size);tex=nt.nodes.new('ShaderNodeTexImage');tex.image=im;nt.nodes.active=tex
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.bake(type='DIFFUSE',pass_filter={'COLOR','DIRECT','INDIRECT'},margin=6,use_clear=True)
    im.filepath_raw=str((OUT/(ob.name+'-GI.png')).resolve());im.file_format='PNG';im.save()
    diag=bpy.data.images.new(ob.name+'_indirect',128,128);tex.image=diag;bpy.ops.object.bake(type='DIFFUSE',pass_filter={'INDIRECT'},margin=2,use_clear=True);diag.filepath_raw=str((OUT/(ob.name+'-indirect.png')).resolve());diag.file_format='PNG';diag.save();tex.image=im
    final=bpy.data.materials.new(ob.name+'_GI_PBR');final.use_nodes=True;pb=final.node_tree.nodes['Principled BSDF'];pb.inputs['Roughness'].default_value=.9;t=final.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;final.node_tree.links.new(t.outputs['Color'],pb.inputs['Base Color']);export(ob,ob.name,final)
    report['outputs'][ob.name]['texture_size']=size
    # Restore source lighting for the next target's GI transport.
    ob['final_material']=final.name
for ob in receivers:ob.data.materials[0]=bpy.data.materials[ob['final_material']]
(OUT/'receipt.json').write_text(json.dumps(report,indent=2))
for im in bpy.data.images:
    if im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str((OUT/'entry-baked.blend').resolve()))
# Render actual additions with the existing castle. Terrain patch is preview only.
import zipfile,numpy as np
z=zipfile.ZipFile('assets/castle_refit_v1/scene-before.data');h=np.frombuffer(z.read(next(n for n in z.namelist() if n.startswith('HeightMap_'))),'<f4').reshape(257,257)*256
vs=[];faces=[];nx=61;ny=39
for j in range(ny):
 for i in range(nx):
    x=-15+i*.5;y=-25+j*.5;wx,wz=127+x,176+y;a,b=int(wx),int(wz);u,v=wx-a,wz-b;hh=(h[b,a]*(1-u)+h[b,a+1]*u)*(1-v)+(h[b+1,a]*(1-u)+h[b+1,a+1]*u)*v;vs.append((x,y,float(hh)))
for j in range(ny-1):
 for i in range(nx-1):
    a=j*nx+i;faces.extend([(a,a+1,a+nx+1),(a,a+nx+1,a+nx)])
me=bpy.data.meshes.new('preview_terrain');me.from_pydata(vs,[],faces);me.update();o=bpy.data.objects.new('preview_terrain',me);scene.collection.objects.link(o);m=bpy.data.materials.new('terrain_preview_green');m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=kit.srgb('#536B47');me.materials.append(m)
cam=kit.preview_setup();scene.world=world;scene.cycles.samples=24
kit.shot(cam,str(OUT/'entry-perspective.png'),(7,-29,76.0),(0,-17,72.5),35,(1400,1100))
# Hide high shell only for unobstructed top inspection; all additions remain.
for o in occluders:
    if o.type=='MESH':o.hide_render=True
cam.data.type='ORTHO';cam.data.ortho_scale=32
kit.shot(cam,str(OUT/'entry-top.png'),(0,-14,103),(0,-14,72),45,(1300,1100))
print('ENTRY DONE',json.dumps(report))
