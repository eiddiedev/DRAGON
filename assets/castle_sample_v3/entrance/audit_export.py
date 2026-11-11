from pathlib import Path
import json,struct,hashlib,numpy as np,trimesh
P=Path(__file__).parent;out={}
for name in ['entrance_masonry','entrance_carved_trim']:
 p=P/(name+'.glb');scene=trimesh.load(p);mesh=scene.to_geometry();tri=mesh.vertices[mesh.faces];mn=tri.min(1);mx=tri.max(1)
 # glTF x horizontal,y elevation. Any triangle touching clear doorway rectangle is rejected.
 touches=(mn[:,0]<1.85)&(mx[:,0]>-1.85)&(mn[:,1]<77.95)&(mx[:,1]>72.25)
 raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);colors=any('COLOR_0' in pr['attributes'] for m in g['meshes'] for pr in m['primitives']);assert not colors;assert not touches.any(),(name,int(touches.sum()))
 out[name]={'triangles':len(mesh.faces),'bounds':mesh.bounds.tolist(),'doorway_intersecting_triangles':int(touches.sum()),'vertex_color':colors,'sha256':hashlib.sha256(raw).hexdigest()}
out['scope']='Visual-only additive sample; tests preserved interior clear doorwayx±1.85/elevation72.25..77.95; collider remains disabled by parent assembly.'
(P/'export-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
