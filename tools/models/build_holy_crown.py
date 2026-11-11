"""Redistribute the accepted six-face leaves around the actual new trunk, same two draw groups."""
import trimesh,numpy as np,struct,json
from pathlib import Path
rng=np.random.default_rng(111108)
trunk=next(iter(trimesh.load('assets/tripo/approved_batch/tree_trunk_source.glb',force='scene').geometry.values())).vertices*23.9307251-[0,1.3,0]
# Broad, overlapping domed crown fitted to the user's widened trunk.
centers=[[-1.5,15.8,0]]
for i in range(6):
 t=2*np.pi*i/6
 centers.append([-1.5+3.8*np.cos(t),14.6+.35*np.sin(t*3),5.2*np.sin(t)])
for i in range(10):
 t=2*np.pi*i/10
 centers.append([-1.5+6.8*np.cos(t),11.5+.7*np.cos(t*3),9.3*np.sin(t)])
centers.extend([[-1.5,8.6,-11.0],[-1.5,8.6,11.0]])
centers=np.array(centers)
Path('assets/holy_refine/crown-centers.json').write_text(json.dumps(centers.tolist()))
for part in [3,4]:
 old=next(iter(trimesh.load(f'assets/holy_refine/holy_canopy{part}_refined.glb',force='scene').geometry.values()))
 vs=[];fs=[];uv=[]
 for i in range(4500):
  group=i%len(centers)
  # Layered leaf clusters: compact interiors plus irregular outer tips, no flat canopy sheet.
  direction=rng.normal(size=3);direction/=np.linalg.norm(direction)
  offset=direction*rng.random()**.42*np.array([3.6,3.0,3.9])
  c=centers[group]+offset
  length=rng.uniform(.42,.68);width=length*rng.uniform(.36,.52)
  ring=np.array([[-length,0,0],[-.38*length,0,.85*width],[.4*length,0,.65*width],[length,0,0],[.35*length,0,-.68*width],[-.35*length,0,-.8*width]])
  leaf=np.vstack(([0,width*.22,0],ring))
  rotation=trimesh.transformations.euler_matrix(rng.uniform(-.85,.85),rng.uniform(0,6.283),rng.uniform(-.8,.8))[:3,:3]
  start=len(vs);vs.extend(leaf@rotation.T+c)
  for k in range(6):fs.append([start,start+1+k,start+1+(k+1)%6])
  tex=old.visual.uv[rng.integers(len(old.visual.uv))];uv.extend([tex]*7)
 mesh=trimesh.Trimesh(vs,fs,process=False);mesh.visual=trimesh.visual.texture.TextureVisuals(uv=uv,material=old.visual.material)
 p=Path(f'assets/holy_refine/holy_canopy{part}_crown.glb');mesh.export(p)
 b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+n]);d['nodes']=[{'name':f'holy_canopy{part}','mesh':0}];d['scenes']=[{'nodes':[0]}];j=json.dumps(d,separators=(',',':')).encode();j+=b' '*((-len(j))%4);rest=b[20+n:];p.write_bytes(struct.pack('<III',0x46546c67,2,20+len(j)+len(rest))+struct.pack('<II',len(j),0x4e4f534a)+j+rest)
 print(p,len(mesh.faces),mesh.bounds.tolist())
