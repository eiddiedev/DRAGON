"""Prepare a Tripo gate for the editor; preserve source and UVs, cap triangles."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
source=Path(args[0]).resolve();out=Path(args[1]).resolve();out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(source))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in meshes:
 o.select_set(True)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.object.join();ob=bpy.context.object;ob.name='rift_gate_h25'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
# Tripo gate front faces +X; rotate it to Blender -Y (glTF +Z).
from mathutils import Matrix
ob.data.transform(Matrix.Rotation(-math.pi/2,4,'Z'))
def tris():
 ob.data.calc_loop_triangles();return len(ob.data.loop_triangles)
initial=tris()
if initial>14900:
 mod=ob.modifiers.new('Game triangle budget','DECIMATE');mod.ratio=14800/initial;mod.use_collapse_triangulate=True
 bpy.ops.object.modifier_apply(modifier=mod.name)
lo=Vector(tuple(min(v.co[i] for v in ob.data.vertices) for i in range(3)))
hi=Vector(tuple(max(v.co[i] for v in ob.data.vertices) for i in range(3)))
scale=8/(hi.z-lo.z);center=Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,lo.z))
for v in ob.data.vertices:v.co=(v.co-center)*scale
textures=[]
for mat in ob.data.materials:
 if not mat or not mat.use_nodes:continue
 bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if bs:
  for link in list(bs.inputs['Normal'].links):mat.node_tree.links.remove(link)
  bs.inputs['Roughness'].default_value=.82
 for node in mat.node_tree.nodes:
  if node.type=='TEX_IMAGE' and node.image:
   im=node.image
   if max(im.size)>1024:im.scale(1024,1024)
   textures.append({'name':im.name,'size':list(im.size)})
assert tris()<=15000,tris()
bpy.ops.export_scene.gltf(filepath=str(out/'rift_gate_h25.glb'),export_format='GLB',use_selection=True,export_animations=False)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'rift_gate_h25.blend'))
report={'source':str(source),'source_triangles':initial,'output_triangles':tris(),'height_m':8,'source_bounds':[list(lo),list(hi)],'textures':textures,'estimated_capacity':math.ceil(tris()/1000),'actual_editor_capacity':None}
(out/'mesh-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
