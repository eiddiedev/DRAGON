from pathlib import Path
import json,struct,hashlib,numpy as np,trimesh
P=Path(__file__).parent;out={};samples=[]
# Real old clear profile, with 3cm audit margin from the stone face.
for y in np.arange(72.25,77.96,.075):
 if y<=76:w=1.9
 else:
  # Conservative inverse of original inner arch (sqrt), safely inside chordal curve.
  w=1.9*(1-((y-76)/2)**2)
 for x in np.arange(-w+.04,w-.035,.075):samples.append((x,y))
samples=np.array(samples)
for name in ['entrance_masonry','entrance_carved_trim']:
 p=P/(name+'.glb');mesh=trimesh.load(p).to_geometry();tri=mesh.vertices[mesh.faces][:,:,:2];a=tri[:,0];v0=tri[:,1]-a;v1=tri[:,2]-a;det=v0[:,0]*v1[:,1]-v0[:,1]*v1[:,0];valid=np.abs(det)>1e-10;tri=tri[valid];a=a[valid];v0=v0[valid];v1=v1[valid];det=det[valid];mn=tri.min(1);mx=tri.max(1);hits=[]
 for point in samples:
  cand=np.all(point>=mn,axis=1)&np.all(point<=mx,axis=1)
  if not cand.any():continue
  q=point-a[cand];u=(q[:,0]*v1[cand,1]-q[:,1]*v1[cand,0])/det[cand];v=(v0[cand,0]*q[:,1]-v0[cand,1]*q[:,0])/det[cand]
  if np.any((u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)):hits.append(point.tolist())
 raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);colors=any('COLOR_0' in pr['attributes'] for m in g['meshes'] for pr in m['primitives']);assert not colors
 out[name]={'triangles':len(mesh.faces),'bounds':mesh.bounds.tolist(),'clear_profile_samples':len(samples),'newly_blocked_samples':hits,'vertex_color':colors,'sha256':hashlib.sha256(raw).hexdigest()}
 assert not hits,(name,hits[:5])
out['scope']='Tests actual original pointed-arch silhouette: halfwidth1.9 below spring76, sqrt arch to78. Original colliders preserved by parent; new overlay collision disabled.'
(P/'export-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
