import bpy,json,os,hashlib
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(O/'castle_rooms_gi.glb'))
ims=[]
for im in bpy.data.images:
 if im.source=='FILE' and im.size[0]>0:
  before=list(im.size)
  if im.packed_file:im.unpack(method='REMOVE')
  im.scale(before[0]//2,before[1]//2);im.filepath_raw=str(O/(im.name+'-runtime.png'));im.file_format='PNG';im.save();im.reload();ims.append({'name':im.name,'master':before,'runtime':list(im.size)})
meshes=[o for o in bpy.data.objects if o.type=='MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
dest=O/'castle_rooms_gi-runtime.glb'
bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,export_yup=True,export_cameras=False,export_lights=False)
pts=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
lo=[min(v[i] for v in pts) for i in range(3)];hi=[max(v[i] for v in pts) for i in range(3)]
report={'runtime_glb':str(dest),'bytes':dest.stat().st_size,'master_bytes':(O/'castle_rooms_gi.glb').stat().st_size,'images':ims,'rgba8_mips_mib':sum(x['runtime'][0]*x['runtime'][1]*4*4/3 for x in ims)/1024**2,'blender_bounds':[lo,hi],'normalization_scale':max(hi[i]-lo[i] for i in range(3)),'triangles':sum(len(o.data.loop_triangles) for o in meshes),'renderer_names':[o.name for o in meshes],'note':'Same exact baked GI, half-resolution runtime texture pack; saved separately from 2K/1K master.'}
for o in meshes:o.data.calc_loop_triangles()
report['triangles']=sum(len(o.data.loop_triangles) for o in meshes)
(O/'runtime-report.json').write_text(json.dumps(report,indent=2));print(report)
