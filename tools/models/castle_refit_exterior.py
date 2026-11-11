"""Refine the existing gothic.py castle, preserving shell coordinates and openings.
Blender -b -t 6 --python tools/models/castle_refit_exterior.py -- assets/castle_refit_v1/exterior [part]
The source geometry remains in Blender x/y, z sea-level (72m); GLB exports Y-up.
"""
import sys, os, math, json
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import kit
# Load definitions ONLY; existing original source remains untouched.
src=(ROOT/'gothic.py').read_text();src=src[:src.index('PARTS = dict(')]
ns={'__file__':str(ROOT/'gothic.py'),'__name__':'castle_source'}
exec(compile(src,str(ROOT/'gothic.py'),'exec'),ns)
C=kit.C;Mesh=kit.Mesh;T=72.;PI=math.pi
C.update({k:kit.srgb(v) for k,v in dict(w1='#484650',w2='#575460',w3='#6A6470',w4='#514D5B',band='#77707A',sl1='#35384C',sl2='#2F3244',sl3='#42455D',gold1='#A98952',floor='#494650',iron='#282732').items()})
kit.GLOWS.update(glass='#FFCD83',p_blue='#8C79B7',p_pink='#B984BD',star='#FFD28C')

def stones(P,cx,cy,yaw,width,z0,z1,n=0,count=40):
    # A shallow staggered masonry skin: recessed mortar remains original shell.
    # Surface projects only .035m, behind existing window glazing and jambs.
    rows=max(1,int((z1-z0)/.70));h=(z1-z0)/rows
    for row in range(rows):
        zz=z0+(row+.5)*h
        stride=1.25;u=-width/2+(0.0 if row%2 else -.625)
        while u<width/2:
            a=max(u,-width/2+.025);b=min(u+stride,width/2-.025)
            if b-a>.15:
                x,y=ns['at'](cx,cy,yaw,(a+b)/2,n+.012)
                col=C[('w1','w2','w4','w2','w3')[(row*7+int(u*13))%5]]
                P.rbox((b-a-.035,.046,h-.035),(x,y,zz),col,ns['rot'](yaw),cuts=0)
            u+=stride

old_lancet=ns['lancet']
def lancet(P,G,cx,cy,yaw,u,z,w,h,n=0,glow='glass'):
    old_lancet(P,G,cx,cy,yaw,u,z,w,h,n,glow)
    # Projected sill and segmented surrounding jamb, stone sized to window.
    x,y=ns['at'](cx,cy,yaw,u,n+.12)
    P.rbox((w+.58,.38,.16),(x,y,z-.13),C['band'],ns['rot'](yaw),cuts=0)
    for s in (-1,1):
        for k in range(max(3,int((h-w*.6)/.65))):
            zh=(h-w*.6)/max(3,int((h-w*.6)/.65))
            xx,yy=ns['at'](cx,cy,yaw,u+s*(w/2+.12),n+.14)
            P.rbox((.26,.25,zh-.028),(xx,yy,z+(k+.5)*zh),C['w2' if k%2 else 'w3'],ns['rot'](yaw),cuts=0)

old_roof=ns['gable_roof']
def gable_roof(P,cx,cy,yaw,z,w,length,rise,over=.5):
    half=w/2+over;slope=math.atan2(rise,half);run=math.hypot(half,rise)
    rows=max(6,int(run/.72));cols=max(3,int((length+2*over)/.85))
    for sx in (-1,1):
        for r in range(rows):
            d=run*((r+.5)/rows-.5);ux=sx*(half/2-math.cos(slope)*d);zz=z+rise/2+math.sin(slope)*d
            for j in range(cols):
                v=-(length+2*over)/2+(j+.5)*(length+2*over)/cols
                px=cx+math.cos(yaw)*ux-math.sin(yaw)*v;py=cy+math.sin(yaw)*ux+math.cos(yaw)*v
                P.rbox((run/rows*1.10,(length+2*over)/cols-.018,.16),(px,py,zz),C[('sl1','sl2','sl1','sl3','sl2')[(r+j*3)%5]],ns['rot'](yaw,(0,sx*slope,0)),cuts=0)
    P.rbox((.38,length+over*2+.2,.32),(cx,cy,z+rise+.1),C['band'],ns['rot'](yaw),cuts=0)
    for i in range(max(2,int(length/3.2))):
        v=-length/2+(i+.5)*length/max(2,int(length/3.2))
        P.cyl(.11,.01,.95,(cx-math.sin(yaw)*v,cy+math.cos(yaw)*v,z+rise+.65),C['gold1'],4)

def door_arch(P,y0):
    for lay in range(3):
        grow=lay*.22;ri=1.9+grow;ro=ri+.22
        depth=.18+lay*.09;front=y0-.28-lay*.055
        for side in (-1,1):
            P.rbox((.21,depth,4.0),(side*(ri+.105),front+depth/2,T+2),C['w3' if lay%2==0 else 'band'],cuts=0)
            for k in range(14):
                a=(k+.015)/14;b=(k+.985)/14
                points=[]
                for yy in (front,front+depth):
                    points += [(side*ri*(1-a),yy,T+4+(2+grow*.45)*math.sqrt(a)),(side*ri*(1-b),yy,T+4+(2+grow*.45)*math.sqrt(b)),(side*ro*(1-b),yy,T+4+(2.22+grow*.45)*math.sqrt(b)),(side*ro*(1-a),yy,T+4+(2.22+grow*.45)*math.sqrt(a))]
                vs=[P.bm.verts.new(v) for v in points]
                for f in [(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]:P.bm.faces.new([vs[i] for i in f])
                P.paint(vs,C['w3' if (lay+k)%3 else 'band'])

old_gable=ns['gable_wall']
def gable_wall(P,cx,cy,yaw,n,z,w,rise,c='w1',t=.7):
    old_gable(P,cx,cy,yaw,n,z,w,rise,c,t)
    rows=int(rise/.7)
    for row in range(rows):
        zz=(row+.5)*rise/rows;ww=w*(1-(zz+.34)/rise)
        if ww>.25:stones(P,cx,cy,yaw,ww,z+zz-.32,z+zz+.32,n,1)

# Replace only old jagged arch blocks; opening and all structural walls remain intact.
part_source=src[src.index('def part_main():'):src.index('def part_towers():')]
a=part_source.index('    # 尖拱门的层层门券');b=part_source.index('    rose(P, G, 0, y0',a)
part_source=part_source[:a]+'    door_arch(P,y0)\n'+part_source[b:]
# Replace the formerly floating thin courtyard road with solid footing; keep route.
wall_source=src[src.index('def part_wall():'):]
wall_source=wall_source.replace("P.rbox((4.6, 10.5, .14), (0, -13.6, T + .06), C['w4'], cuts=0)","P.rbox((4.6, 9.10, 3.74), (0, -12.45, 70.37), C['w4'], cuts=0)")
wall_source=wall_source.replace("        P.rbox((3.0, 3.0, top + 5 - base), (x, gy, (top + 5 + base) / 2), C['w1'], cuts=0)","        if sx == -1:\n            P.rbox((3.0, 3.0, top+5-T), (x,gy,(top+5+T)/2), C['w1'], cuts=0)\n            P.rbox((3.0, 2.0, T-base), (x,gy+.5,(T+base)/2), C['w1'], cuts=0)\n        else:\n            P.rbox((3.0, 3.0, top + 5 - base), (x, gy, (top + 5 + base) / 2), C['w1'], cuts=0)")
exec(compile(wall_source,'refined_wall','exec'),ns)
ns['door_arch']=door_arch
exec(compile(part_source,'refined_main','exec'),ns)
original_finish=kit.finish
OUT=Path(ns['outdir']);OUT.mkdir(parents=True,exist_ok=True)
report=json.loads((OUT/'geometry-report.json').read_text()) if (OUT/'geometry-report.json').exists() else {}
def finish(objs,G,name,outdir,tex_size=2048):
    P=Mesh()
    if name=='gothic_main':
        # Front facade lower stone courses, separately either side of 3.8m doorway.
        for s in (-1,1):
            stones(P,s*4.45,-8,0,4.95,T,T+6,0)
        # Gentle paved threshold reaches floor surface72.22 without a high step.
        # Full doorway width; slopes from courtyard72.13 to room72.22 over .9m.
        verts=[(-1.62,-8.85,72.115),(1.62,-8.85,72.115),(1.62,-7.95,72.221),(-1.62,-7.95,72.221)]
        vs=[P.bm.verts.new(v) for v in verts];P.bm.faces.new(vs);P.paint(vs,C['floor'])
        # Dark stone skirting and molding on interior wall sections, preserving all door gaps.
        for s in (-1,1):
            for a,b in [(-5.9,1.2),(4.8,14)]:
                for z,h,d in [(72.34,.20,.16),(73.04,.10,.12)]:P.rbox((d,b-a,h),(s*6.12,(a+b)/2,z),C['band'],cuts=0)
        # Faceted pier collar bands; capitals read from entrance and upper gallery.
        for s in (-1,1):
            for y in (-5.,-1.,3.,7.,11.):
                for z,r,h in [(72.77,.66,.16),(73.08,.60,.12),(84.58,.62,.18),(84.88,.71,.22)]:P.cyl(r,r,h,(s*4,y,z),C['band'],12)
    if name=='gothic_wall':
        # Keep the original flat road at72.24; no terrain-conforming approach.
        # Existing guardian statues sit at world (123/131,72.25,166).
        # Give each a real masonry plinth grounded in the hillside, linked to road.
        for side in (-1,1):
            cx=side*4.0;cy=-10.0
            P.rbox((3.6,2.5,2.25),(cx,cy,71.125),C['w4'],cuts=0)
            for zz in [70.35,70.85,71.35,71.85]:
                for sy in (-1,1):
                    for k in range(4):P.rbox((.87,.055,.46),(cx-1.35+k*.9,cy+sy*1.26,zz),C['w2' if k%2 else 'band'],cuts=0)
                for sx in (-1,1):
                    for k in range(3):P.rbox((.055,.80,.46),(cx+sx*1.81,cy-.83+k*.83,zz),C['w2' if k%2 else 'band'],cuts=0)
            P.rbox((3.66,2.56,.13),(cx,cy,72.185),C['band'],cuts=0)
        # User override: keep the original flat approach. Remove the entire
        # added terrain-conforming ramp, including tapered front and paving.
        # The original road ends at worldZ159; only overhanging added surface
        # is removed. No terrain deformation or replacement stair geometry.
    if len(P.bm.verts):objs.append(P.to_object('architectural_details'))
    result=original_finish(objs,G,name,outdir,tex_size=2048)
    # Preserve editable unbaked asset. Texture currently has material detail and AO only.
    for im in bpy.data.images:
        if im.has_data and im.size[0]>0: im.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'-unlit.blend')))
    bounds=[v for o in result for v in [o.matrix_world@Vector(c) for c in o.bound_box]]
    mn=[min(v[i] for v in bounds) for i in range(3)];mx=[max(v[i] for v in bounds) for i in range(3)]
    report[name]={'blender_bounds':[mn,mx],'unity_bounds':[[mn[0],mn[2],-mx[1]],[mx[0],mx[2],-mn[1]]],'normalization_scale':max(mx[i]-mn[i] for i in range(3)),'triangles':sum(len(o.data.loop_triangles) for o in result),'bytes':(OUT/(name+'.glb')).stat().st_size,'lighting_bake':'AO/albedo only; final assembly GI not yet baked'}
    (OUT/'geometry-report.json').write_text(json.dumps(report,indent=2))
    return result
ns.update(stones=stones,lancet=lancet,gable_roof=gable_roof,gable_wall=gable_wall,finish=finish)
only=ns['only']
for name in ['gothic_main','gothic_towers','gothic_wall']:
    if only and name not in only:continue
    cam=ns['part_'+{'gothic_main':'main','gothic_towers':'towers','gothic_wall':'wall'}[name]]()
    kit.shot(cam,str(OUT/(name+'.png')),(20,-64,T+21),(0,1,T+20),40,(1200,1000))
print('REFIT COMPLETE',json.dumps(report))

if '--gi' in only:
    import numpy as np
    kit.reset();scene=bpy.context.scene
    objects={};root=OUT
    for name in ['gothic_main','gothic_towers','gothic_wall']:
        before=set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str((root/(name+'.glb')).resolve()))
        objects[name]=[o for o in set(bpy.data.objects)-before if o.type=='MESH']
    # Interior furnishing source supplied by parallel interior task, used only as blockers.
    interior=Path('assets/castle_refit_v1/interior/castle_rooms.glb')
    if interior.exists():bpy.ops.import_scene.gltf(filepath=str(interior.resolve()))
    world=bpy.data.worlds.new('neutral_overcast_GI');world.use_nodes=True
    world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.65,.68,1)
    world.node_tree.nodes['Background'].inputs[1].default_value=.85;scene.world=world
    scene.cycles.samples=48;scene.cycles.max_bounces=6;scene.cycles.diffuse_bounces=4
    # Same actual fixture distribution as the interior GI resource pass.
    lighting=json.loads(Path('assets/castle_refit_v1/interior/lighting-plan.json').read_text())
    for spec in lighting['lights']:
        ob=bpy.data.objects.new(spec['name'],bpy.data.lights.new(spec['name'],'POINT'));scene.collection.objects.link(ob)
        ob.location=spec['position_blender'];ob.data.energy=spec['energy_watts']*2.4;ob.data.color=spec['color'];ob.data.shadow_soft_size=spec['radius']
    for name,pos,target,energy,size in [('library_window',(-12.6,3.1,76),(-9,3.1,73),90,2),('dining_window',(12.6,3.1,76),(9,3.1,73),90,2),('hall_front',(0,-7.5,83.5),(0,3,75),150,3),('hall_rear',(0,13,81.5),(0,4,74),120,3)]:
        d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.color=(.49,.52,1);d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    scene.render.bake.use_pass_direct=True;scene.render.bake.use_pass_indirect=True;scene.render.bake.use_pass_color=True
    bpy.ops.wm.save_as_mainfile(filepath=str((root/'assembly-GI-source.blend').resolve()))
    outputs=json.loads((root/'GI-report.json').read_text())['targets'] if (root/'GI-report.json').exists() else {}
    for name,obs in objects.items():
        if '--wall-only' in only and name!='gothic_wall':continue
        if '--main-wall' in only and name=='gothic_towers':continue
        targets=[o for o in obs if any('paint' in m.name for m in o.data.materials)]
        if len(targets)!=1:raise RuntimeError((name,[o.name for o in targets]))
        ob=targets[0];mat=ob.data.materials[0];nt=mat.node_tree
        image=bpy.data.images.new(name+'_GI',2048,2048)
        tex=nt.nodes.new('ShaderNodeTexImage');tex.image=image;nt.nodes.active=tex
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
        bpy.ops.object.bake(type='DIFFUSE',pass_filter={'COLOR','DIRECT','INDIRECT'},margin=6,use_clear=True)
        image.filepath_raw=str((root/(name+'-GI.png')).resolve());image.file_format='PNG';image.save()
        # Separate isolated indirect-only diagnostic at 256, without changing actual output.
        diag=bpy.data.images.new(name+'_indirect_evidence',256,256);tex.image=diag
        bpy.ops.object.bake(type='DIFFUSE',pass_filter={'INDIRECT'},margin=2,use_clear=True)
        arr=np.array(diag.pixels[:]).reshape(-1,4);positive=arr[:,:3][arr[:,3]>.5]
        indirect={'max':float(positive.max()),'mean':float(positive.mean()),'nonzero_fraction':float((positive.max(axis=1)>1e-5).mean())}
        diag.filepath_raw=str((root/(name+'-indirect-evidence.png')).resolve());diag.file_format='PNG';diag.save()
        tex.image=image
        # Export own receiver with baked texture, then restore source for following bakes.
        final=bpy.data.materials.new(name+'_GI_PBR');final.use_nodes=True;pb=final.node_tree.nodes.get('Principled BSDF');pb.inputs['Roughness'].default_value=.9
        t=final.node_tree.nodes.new('ShaderNodeTexImage');t.image=image;final.node_tree.links.new(t.outputs['Color'],pb.inputs['Base Color'])
        ob.data.materials[0]=final
        bpy.ops.object.select_all(action='DESELECT')
        for o in obs:o.select_set(True)
        output=root/(name+'-GI.glb')
        bpy.ops.export_scene.gltf(filepath=str(output.resolve()),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_image_format='JPEG',export_jpeg_quality=92)
        ob.data.materials[0]=mat
        outputs[name]={'output':str(output),'bytes':output.stat().st_size,'indirect':indirect,'source':str(root/(name+'.glb'))}
        (root/'GI-report.json').write_text(json.dumps({'targets':outputs,'lighting_source':'interior/lighting-plan.json 25 point fixtures ×2.4 plus 4 stained-window AREA lights', 'cycles_samples':48,'diffuse_bounces':4,'max_bounces':6,'passes':['COLOR','DIRECT','INDIRECT'],'sky':'neutral overcast approximation (.65,.65,.68) strength .85, no directional sun; PBR retains dynamic scene response','interior_occluders':str(interior) if interior.exists() else 'none; shell and own columns only','exclusions':'glow meshes keep original emission; dynamic furniture and actors excluded'},indent=2))
    # Final preview uses baked PBR under neutral lighting; no baked image feeds another bake.
    for name,obs in objects.items():
        for o in obs:
            if o.type=='MESH' and any('paint' in m.name for m in o.data.materials):
                final=bpy.data.materials.get(name+'_GI_PBR')
                if final is None:
                    final=bpy.data.materials.new(name+'_GI_PBR');final.use_nodes=True;t=final.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str((root/(name+'-GI.png')).resolve()));final.node_tree.links.new(t.outputs['Color'],final.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
                o.data.materials[0]=final
    cam=kit.preview_setup();scene=bpy.context.scene;scene.world=world
    # preview_setup adds sun for display; use low value to avoid concealing texture/detail.
    for o in scene.objects:
        if o.type=='LIGHT' and o.data.type=='SUN':o.data.energy=.6
    kit.shot(cam,str(root/'castle-assembled-GI.png'),(48,-112,111),(0,0,103),42,(1500,1300))
    kit.shot(cam,str(root/'entrance-GI.png'),(0,-17,74.4),(0,-7.9,75.3),24,(1400,1000))
    print('GI COMPLETE',json.dumps(outputs))

if '--split' in only:
    import bmesh
    split_report={}
    for name in ['gothic_main','gothic_towers']:
        for side in ['west','east']:
            kit.reset();bpy.ops.import_scene.gltf(filepath=str((OUT/(name+'-GI.glb')).resolve()))
            obs=[o for o in bpy.context.scene.objects if o.type=='MESH'];kept=[]
            for ob in obs:
                bm=bmesh.new();bm.from_mesh(ob.data)
                faces=[f for f in bm.faces if (f.calc_center_median().x>=0)==(side=='west')]
                bmesh.ops.delete(bm,geom=faces,context='FACES')
                loose=[v for v in bm.verts if not v.link_faces]
                if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
                bm.to_mesh(ob.data);bm.free();ob.data.update()
                if len(ob.data.polygons):kept.append(ob)
                else:bpy.data.objects.remove(ob,do_unlink=True)
            bpy.ops.object.select_all(action='DESELECT')
            for o in kept:o.select_set(True)
            label=name+'-'+side;out=OUT/(label+'-GI.glb')
            bpy.ops.export_scene.gltf(filepath=str(out.resolve()),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_image_format='JPEG',export_jpeg_quality=92)
            verts=[o.matrix_world@v.co for o in kept for v in o.data.vertices]
            mn=[min(v[i] for v in verts) for i in range(3)];mx=[max(v[i] for v in verts) for i in range(3)]
            for o in kept:o.data.calc_loop_triangles()
            count=sum(len(o.data.loop_triangles) for o in kept)
            assert count<29000,(label,count)
            split_report[label]={'path':str(out),'triangles':count,'bytes':out.stat().st_size,'unity_bounds':[[mn[0],mn[2],-mx[1]],[mx[0],mx[2],-mn[1]]],'normalization_scale':max(mx[i]-mn[i] for i in range(3)),'source':str(OUT/(name+'-GI.glb')),'placement':'original scene coordinate convention; same world root127,0,176; no recenter; UV/materials retained'}
    (OUT/'split-report.json').write_text(json.dumps(split_report,indent=2));print('SPLIT COMPLETE',json.dumps(split_report))

if '--rear-window' in only:
    kit.reset();bpy.ops.import_scene.gltf(filepath=str((OUT/'gothic_main-GI.glb').resolve()))
    changed=0
    for ob in list(bpy.context.scene.objects):
        if ob.type!='MESH' or not ob.name.startswith('glow'):continue
        mats=[]
        for label,col in [('rear_violet','#827199'),('rear_amber','#AD875B')]:
            mat=bpy.data.materials.new(label);mat.use_nodes=True;pb=mat.node_tree.nodes['Principled BSDF'];rgba=kit.srgb(col);pb.inputs['Base Color'].default_value=rgba;pb.inputs['Emission Color'].default_value=rgba;pb.inputs['Emission Strength'].default_value=.18;pb.inputs['Roughness'].default_value=.75;ob.data.materials.append(mat);mats.append(len(ob.data.materials)-1)
        for face in ob.data.polygons:
            c=ob.matrix_world@face.center
            if abs(c.y-13.1)<.12 and abs(c.x)<3.1 and 79.4<c.z<85.6:
                angle=math.atan2(c.z-82.5,c.x);face.material_index=mats[int((angle+math.pi)/math.pi*4)%2];changed+=1
    frame=Mesh()
    # Real narrow stone/metal tracery sits in front of the old rear opening.
    for k in range(16):
        a=(k+.5)*math.tau/16
        frame.rbox((math.tau*3.01/16*.99,.10,.12),(3.01*math.cos(a),13.005,82.5+3.01*math.sin(a)),kit.srgb('#756573'),(0,-a-math.pi/2,0),cuts=0)
    for k in range(8):
        a=k*math.tau/8
        frame.rbox((3.0,.085,.045),(1.5*math.cos(a),12.995,82.5+1.5*math.sin(a)),kit.srgb('#756573'),(0,-a,0),cuts=0)
    o=frame.to_object('rear_rose_tracery');mat=bpy.data.materials.new('rear_rose_dark_frame');mat.use_nodes=True;pb=mat.node_tree.nodes['Principled BSDF'];pb.inputs['Base Color'].default_value=kit.srgb('#756573');pb.inputs['Roughness'].default_value=.8;o.data.materials.append(mat)
    while o.data.color_attributes:o.data.color_attributes.remove(o.data.color_attributes[0])
    bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str((OUT/'gothic_main-GI.glb').resolve()),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_image_format='JPEG',export_jpeg_quality=92)
    (OUT/'rear-window-fix.json').write_text(json.dumps({'changed_glow_faces':changed,'radius_preserved':3,'center_blender':[0,13.1,82.5],'emission_strength':.18,'geometry_delta_tris':288,'lighting_note':'local decorative glass reduction; previously baked structural GI remains, no new light added'},indent=2));print('REAR WINDOW',changed)
