import trimesh,numpy as np,struct,json
from pathlib import Path
rng=np.random.default_rng(1110)
leaf=next(iter(trimesh.load('assets/tripo/approved_batch/tree_single_leaf_source.glb',force='scene').geometry.values()))
raw=leaf.vertices-leaf.vertices.mean(axis=0);values,axes=np.linalg.eigh(np.cov(raw.T));base=np.column_stack((raw@axes[:,1],raw@axes[:,0],raw@axes[:,2]))
base[:,1]*=-1
trunk=next(iter(trimesh.load('assets/tripo/approved_batch/tree_trunk_source.glb',force='scene').geometry.values())).vertices*23.9307251-[0,1.3,0]
mask=(trunk[:,1]>6)&(np.linalg.norm(trunk[:,[0,2]],axis=1)>3.3);candidates=trunk[mask]
centers=[candidates[np.argmax(candidates[:,1])]]
for i in range(31):
 dist=np.min([np.linalg.norm(candidates-c,axis=1) for c in centers],axis=0);centers.append(candidates[np.argmax(dist)])
for part in range(3,19):
 vs=[];fs=[];uv=[]
 for i in range(64):
  c=centers[rng.integers(len(centers))]+rng.normal(size=3)*[1.25,.8,1.25]+[0,.6,0]
  yaw=rng.uniform(0,np.pi*2);pitch=rng.uniform(-.8,.8);roll=rng.uniform(-.5,.5)
  rotation=trimesh.transformations.euler_matrix(pitch,yaw,roll)[:3,:3]
  v=base@rotation.T*rng.uniform(1.7,2.45)+c
  offset=len(vs);vs.extend(v);fs.extend(leaf.faces+offset);uv.extend(leaf.visual.uv)
 m=trimesh.Trimesh(vs,fs,process=False);m.visual=trimesh.visual.texture.TextureVisuals(uv=uv,material=leaf.visual.material)
 p=Path(f'assets/holy_refine/holy_canopy{part}_complete.glb');m.export(p)
 b=p.read_bytes();n=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+n]);d['nodes']=[{'name':f'holy_canopy{part}','mesh':0}];d['scenes']=[{'nodes':[0]}];j=json.dumps(d,separators=(',',':')).encode();j+=b' '*((-len(j))%4);rest=b[20+n:];p.write_bytes(struct.pack('<III',0x46546c67,2,20+len(j)+len(rest))+struct.pack('<II',len(j),0x4e4f534a)+j+rest)
 print(part,len(leaf.faces),'faces/leaf',len(m.faces),'faces',max(m.extents),p.stat().st_size)
