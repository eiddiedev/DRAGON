import trimesh,numpy as np
from pathlib import Path
out=Path('assets/holy_refine')
for index in [3,4]:
 s=trimesh.load(f'assets/veg3d/v8/holy_canopy{index}.glb',force='scene');g=next(iter(s.geometry.values()));uv=g.visual.uv
 vertices=[];faces=[];uvs=[]
 for j in range(0,len(g.faces)//2,3):
  ids=g.faces[j*2:j*2+2].reshape(-1);pts=g.vertices[ids];c=pts.mean(axis=0);c=c*np.array([.55,.43,.55])+[0,3,0]
  a,b,t=g.vertices[g.faces[j*2]];u=(t-a)/2;v=b-(a+t)/2
  n=np.cross(u,v);n/=max(np.linalg.norm(n),1e-6)
  # Six-sided, pointed leaf, raised midrib and asymmetric folded halves.
  ring=[-u,-u*.38+v*.85,u*.4+v*.65,u,u*.35-v*.68,-u*.35-v*.8]
  base=len(vertices);vertices.append(c+n*np.linalg.norm(u)*.16);vertices.extend(c+p for p in ring)
  tex=uv[ids].mean(axis=0);uvs.extend([tex]*7)
  for k in range(6):faces.append([base,base+1+k,base+1+(k+1)%6])
 m=trimesh.Trimesh(vertices,faces,process=False);m.visual=trimesh.visual.texture.TextureVisuals(uv=uvs,material=g.visual.material)
 m.export(out/f'holy_canopy{index}_refined.glb');print(index,len(m.faces),m.bounds.tolist(),'scale',max(m.extents))
