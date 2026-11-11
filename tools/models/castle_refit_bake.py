"""Bake existing castle-room geometry with shell/furnishings present (Cycles GI).
Blender --background --python castle_refit_bake.py -- [trial|final]
Source coordinates: east,north,up, absolute floor 72.22; no live scene writes.
"""
import bpy,bmesh,json,math,sys,time,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[2];O=R/'assets/castle_refit_v1/baked';O.mkdir(parents=True,exist_ok=True)
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'trial'
samples=16 if mode=='trial' else 48;res=512 if mode=='trial' else 2048
bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=samples;s.cycles.max_bounces=6;s.cycles.diffuse_bounces=4;s.cycles.use_denoising=False;s.render.bake.margin=8
s.world=bpy.data.worlds.new('TwilightApproximation');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.25,.4,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.12
s.view_settings.view_transform='Standard';s.view_settings.look='Medium High Contrast' if 'Medium High Contrast' in [] else 'None';s.view_settings.exposure=0;s.view_settings.gamma=1
def imp(path):
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));obs=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
 for o in obs:
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 return obs
room=imp(R/'assets/castle_refit_v1/interior/castle_rooms.glb')[0]
glow=imp(R/'assets/castle_refit_v1/interior/castle_rooms_glow.glb')
shell=[]
for name in ['gothic_main','gothic_towers','gothic_wall']:shell+=imp(R/f'assets/castle_refit_v1/exterior/{name}.glb')
# Current existing Tripo furniture is a caster, not a new baked replacement.
plan=json.loads((R/'assets/tripo/scene_install/placement-plan.json').read_text());bounds=json.loads((R/'assets/tripo/scene_install/model-bounds.json').read_text())
casters=[]
for p in plan['placements']:
 if p['asset'] not in ['castle_throne','castle_bookshelf','castle_armor']:continue
 obs=imp(Path(bounds[p['asset']]['path']));theta=2*math.atan2(p['rot']['y'],p['rot']['w']);mat=Matrix.Translation((p['pos']['x']-127,p['pos']['z']-176,p['pos']['y']))@Matrix.Rotation(math.pi-theta,4,'Z')@Matrix.Scale(p['scale']['x'],4)
 for o in obs:o.matrix_world=mat@o.matrix_world;o.name=p['name'];casters.append(o)
lp=json.loads((R/'assets/castle_refit_v1/interior/lighting-plan.json').read_text())
lp['lights'] += [{'name':'reading_candle_a','position_blender':[-10.3,3.6,73.5],'energy_watts':65,'color':[1,.65,.35],'radius':.45},{'name':'reading_candle_b','position_blender':[-9.72,2.35,73.5],'energy_watts':65,'color':[1,.65,.35],'radius':.45}]
for spec in lp['lights']:
 spec['energy_watts'] *= 2.4
 d=bpy.data.lights.new(spec['name'],'POINT');d.energy=spec['energy_watts'];d.color=spec['color'];d.shadow_soft_size=spec['radius'];o=bpy.data.objects.new(spec['name'],d);s.collection.objects.link(o);o.location=spec['position_blender']
# Modest soft inward window lighting, a planned night-time stained glass approximation.
for name,pos,target,energy,size in [('library_window',(-12.6,3.1,76),(-9,3.1,73),90,2),('dining_window',(12.6,3.1,76),(9,3.1,73),90,2),('hall_front',(0,-7.5,83.5),(0,3,75),150,3),('hall_rear',(0,13,81.5),(0,4,74),120,3)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=energy;d.color=(.49,.52,1);d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def region(v):
 x,y,z=v
 if y>=14:return 'bedchamber' if z>=76.19 else 'sanctuary'
 if x<-6.8:return 'armory' if y<-4 else 'library'
 if x>6.8:return 'kitchen' if y<-4 else 'dining'
 return 'hall_rear' if y>4 else 'hall_front'
# Split by source face centroid; keep coordinates unchanged and preserve source UV.
receivers=[]
for reg in ['hall_front','hall_rear','library','dining','armory','kitchen','sanctuary','bedchamber']:
 o=room.copy();o.data=room.data.copy();s.collection.objects.link(o);o.name='castle_gi_'+reg
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if region(f.calc_center_median())!=reg],context='FACES');bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.to_mesh(o.data);bm.free()
 if not len(o.data.polygons):bpy.data.objects.remove(o,do_unlink=True);continue
 o.data.materials[0]=o.data.materials[0].copy();m=o.data.materials[0];o.data.uv_layers.active.name='SourceUV'
 for n in m.node_tree.nodes:
  if n.type=='TEX_IMAGE':uv=m.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='SourceUV';m.node_tree.links.new(uv.outputs[0],n.inputs['Vector'])
 o.data.uv_layers.new(name='BakeUV');o.data.uv_layers.active_index=1;o.data.uv_layers['BakeUV'].active_render=True
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(65),island_margin=.002);bpy.ops.object.mode_set(mode='OBJECT');receivers.append(o)
bpy.data.objects.remove(room,do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(O/(mode+'-source.blend')))
outputs=[];start=time.time()
for o in receivers:
 if mode=='trial' and not o.name.endswith('library'):continue
 size=res if o.name.endswith(('hall_front','hall_rear','library','dining')) else (512 if mode=='trial' else 1024)
 im=bpy.data.images.new(o.name+'_'+mode,width=size,height=size,alpha=False);im.colorspace_settings.name='sRGB'
 for m in o.data.materials:
  for n in m.node_tree.nodes:n.select=False
  t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;t.select=True;m.node_tree.nodes.active=t
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;st=time.time();bpy.ops.object.bake(type='DIFFUSE',pass_filter={'COLOR','DIRECT','INDIRECT'},use_clear=True)
 im.filepath_raw=str(O/(im.name+'.png'));im.file_format='PNG';im.save();outputs.append({'object':o.name,'image':im.filepath_raw,'resolution':size,'seconds':time.time()-st})
 print('BAKED',o.name,time.time()-st,flush=True)
 # Store images but do not replace caster materials until every batch is baked.
 o['baked_image']=im.name
for o in receivers:
 if 'baked_image' not in o:continue
 im=bpy.data.images[o['baked_image']];m=bpy.data.materials.new(o.name+'_baked');m.use_nodes=True;p=m.node_tree.nodes['Principled BSDF'];p.inputs['Roughness'].default_value=.85;t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color']);o.data.materials.clear();o.data.materials.append(m)
 for f in o.data.polygons:f.material_index=0
 o.data.uv_layers.remove(o.data.uv_layers['SourceUV']);o.data.uv_layers.active_index=0;o.data.uv_layers[0].active_render=True
if mode=='final':
 bpy.ops.object.select_all(action='DESELECT')
 for o in receivers:o.select_set(True)
 bpy.context.view_layer.objects.active=receivers[0];bpy.ops.export_scene.gltf(filepath=str(O/'castle_rooms_gi.glb'),export_format='GLB',use_selection=True,export_yup=True,export_cameras=False,export_lights=False)
# Render using baked emission for receiver appearance, avoiding accidental second lighting.
for o in receivers:
 if 'baked_image' not in o:continue
 m=o.data.materials[0];n=m.node_tree.nodes;n.clear();t=n.new('ShaderNodeTexImage');t.image=bpy.data.images[o['baked_image']];e=n.new('ShaderNodeEmission');e.inputs['Strength'].default_value=1;out=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(t.outputs['Color'],e.inputs['Color']);m.node_tree.links.new(e.outputs[0],out.inputs[0])
s.render.resolution_x=1200;s.render.resolution_y=850;s.render.resolution_percentage=100;s.cycles.samples=32;s.cycles.use_denoising=True
for label,pos,target,lens in [('library',(-7.4,.5,74),(-11.9,3.3,74.2),23),('hall',(0,-6.8,74),(0,10,76),20),('dining',(7.4,.2,74),(11.3,3.2,74.2),23)]:
 if mode=='trial' and label!='library':continue
 d=bpy.data.cameras.new(label);c=bpy.data.objects.new(label,d);s.collection.objects.link(c);c.location=pos;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_start=.05;s.camera=c;s.render.filepath=str(O/(mode+'-'+label+'.png'));bpy.ops.render.render(write_still=True)
report={'status':'baked_not_runtime_verified','mode':mode,'seconds':time.time()-start,'samples':samples,'bounces':6,'diffuse_bounces':4,'passes':['COLOR','DIRECT','INDIRECT'],'world':'Designed approximate twilight constant ambient .12, not reconstructed original sky; no fixed solar shadows','lights':lp['lights'],'outputs':outputs,'receivers':[o.name for o in receivers],'excluded':['Emissive flames and stained glass retain original material','Tripo throne/bookshelves/armor are casters and retain PBR runtime material'],'source_coordinates':'Blender east north up absolute elevation; GLTF east up -north','runtime_display':'Use verified EnvLit GI emission display on castle_gi_* renderers only; must verify shader and material count'}
(O/(mode+'-report.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(O/(mode+'-preview.blend')));print('DONE',json.dumps(report),flush=True)
