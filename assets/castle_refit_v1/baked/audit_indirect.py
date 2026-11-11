"""Diagnostic only: prove indirect light arrives on the actual library receiver."""
import bpy,json
from pathlib import Path
import numpy as np
O=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(O/'final-source.blend'))
s=bpy.context.scene;s.cycles.samples=32
o=bpy.data.objects['castle_gi_library'];im=bpy.data.images.new('library_indirect_diagnostic',width=256,height=256,alpha=False)
for m in o.data.materials:
 for n in m.node_tree.nodes:n.select=False
 t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;t.select=True;m.node_tree.nodes.active=t
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.object.bake(type='DIFFUSE',pass_filter={'INDIRECT'},use_clear=True)
im.filepath_raw=str(O/'library-indirect-diagnostic.png');im.file_format='PNG';im.save()
a=np.asarray(im.pixels[:]).reshape(-1,4)[:,:3]
result={'pass':'DIFFUSE INDIRECT only','max_linear':float(a.max()),'mean_linear':float(a.mean()),'nonzero_pixel_fraction':float((a.max(axis=1)>.00001).mean()),'diffuse_bounces':s.cycles.diffuse_bounces,'source':'final-source.blend','note':'Diagnostic only, not a replacement albedo texture'}
assert result['max_linear']>.001 and result['nonzero_pixel_fraction']>.1,result
(O/'indirect-audit.json').write_text(json.dumps(result,indent=2));print(result)
