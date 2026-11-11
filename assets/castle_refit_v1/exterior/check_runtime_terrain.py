import json,trimesh,numpy as np
from pathlib import Path
p=Path('assets/castle_refit_v1');samples=json.loads((p/'terrain-runtime-check.json').read_text())['data']['result']
m=trimesh.load(p/'exterior/gothic_wall.glb').to_mesh();t=m.triangles;c=m.triangles_center;t=t[(c[:,1]<73)&(m.face_normals[:,1]>.1)];xz=t[:,:,[0,2]];a=xz[:,1]-xz[:,0];b=xz[:,2]-xz[:,0];den=a[:,0]*b[:,1]-b[:,0]*a[:,1];valid=abs(den)>1e-7;den[~valid]=1
out=[]
for s in samples:
 if not (124.7<=s['x']<=129.3 and 155<=s['z']<=159):continue
 if s['x'] <124.7+.30*max(0.,min(1.,156-s['z']))-.001:continue
 q=np.array([s['x']-127,176-s['z']]);v=q-xz[:,0];u=(v[:,0]*b[:,1]-b[:,0]*v[:,1])/den;w=(a[:,0]*v[:,1]-v[:,0]*a[:,1])/den;ok=valid&(u>=-1e-5)&(w>=-1e-5)&(u+w<=1.00001);heights=(t[:,0,1]+u*(t[:,1,1]-t[:,0,1])+w*(t[:,2,1]-t[:,0,1]))[ok];assert len(heights)
 height=float(heights.max());ground=next(x['y'] for x in s['hits'] if x['name']=='地形块');out.append({'world_x':s['x'],'world_z':s['z'],'runtime_terrain_y':ground,'fixed_mesh_y':height,'clearance':height-ground})
assert all(x['clearance']>.10 for x in out)
(p/'exterior/runtime-terrain-comparison-v8.json').write_text(json.dumps({'coordinate_contract':'world_x=127+Blender_x; world_z=176+Blender_y=176-GLB_z; verified against actual main-west runtime bounds','samples':out},indent=2));print([x for x in out if x['world_z']==155]);print('validated',len(out),'samples')
