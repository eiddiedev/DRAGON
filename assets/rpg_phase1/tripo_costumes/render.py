import bpy,sys,math,json
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:];src=Path(args[0]);out=Path(args[1]);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(src))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render];pts=[o.matrix_world@Vector(p) for o in objects for p in o.bound_box];lo=Vector([min(p[i]for p in pts)for i in range(3)]);hi=Vector([max(p[i]for p in pts)for i in range(3)]);center=(lo+hi)*.5
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.render.resolution_x=900;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('NeutralStudio');scene.world.color=(.28,.28,.28)
for pos,energy,size in [((2,-3,4),200,3),((-3,-1,2),120,3),((0,3,3),160,2)]:
 bpy.ops.object.light_add(type='AREA',location=pos);l=bpy.context.object;l.data.energy=energy;l.data.shape='DISK';l.data.size=size;l.rotation_euler=(center-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=(hi.z-lo.z)*1.18;scene.camera=cam
for view,pos in [('front',(0,-3,.6)),('back',(1,3,.7))]:
 cam.location=center+Vector(pos);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/(view+'.png'));bpy.ops.render.render(write_still=True)
report={'bounds':[list(lo),list(hi)],'meshes':[{'name':o.name,'vertices':len(o.data.vertices),'faces':len(o.data.polygons)}for o in objects]};(out/'geometry.json').write_text(json.dumps(report,indent=2))
