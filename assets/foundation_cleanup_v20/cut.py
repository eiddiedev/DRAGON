import sys,json,math,trimesh,numpy as np
sys.path.insert(0,'tools/models')
from glbw import Geo
m=trimesh.load('assets/refit_v12/village_bases.glb',force='mesh',process=False);tri=m.triangles
moves=json.load(open('assets/refit_v12/placement-plan.json'))['moves'];starts=[]
for n in moves:
 if not n['name'].startswith(('house_','hs_house_')):continue
 xmin,xmax,zmin,zmax={'a':(-2.8,2.8,-4.9,3.2),'b':(-4.5,4.5,-5,3.2),'c':(-3.1,4.9,-4.9,3.2)}[n['name'].split('house_')[1][0]]
 x,y,z=[n['after'][k]for k in ['x','y','z']];yaw=math.pi-2*math.atan2(n['before_rot']['y'],n['before_rot']['w']);co,si=math.cos(yaw),math.sin(yaw);lo=n['ground_range'][0];g=Geo([[(0,'#242731'),(1,'#73767b')]])
 corners=[np.array([x+lx*co-lz*si-128,z+lx*si+lz*co-128,y-.045])for lx,lz in [(xmin-.15,zmin-.15),(xmax+.15,zmin-.15),(xmax+.15,zmax+.15),(xmin-.15,zmax+.15)]]
 for j,a in enumerate(corners):
  b=corners[(j+1)%4];aa=a.copy();bb=b.copy();aa[2]=lo-.4;bb[2]=lo-.4;g.quad(a,aa,bb,b,.5,0)
 g.quad(*corners,.68,0)
 p=np.array(g.P);p=p[:,[0,2,1]];p[:,2]*=-1;p=p.reshape(-1,3,3)
 found=[i for i in range(len(tri)-len(p)+1)if np.allclose(tri[i:i+len(p)],p,atol=1e-4)]
 assert len(found)==1,(n['name'],found)
 starts.append((found[0],n['name']))
starts.sort();keep=np.ones(len(tri),bool)
for j,(start,name)in enumerate(starts):
 end=starts[j+1][0]if j+1<len(starts)else len(tri)
 if name in ['hs_house_b_1','hs_house_c_1']:keep[start:end]=False;print(name,start,end)
m.update_faces(keep);m.remove_unreferenced_vertices();m.export('assets/foundation_cleanup_v20/village_bases_clean.glb');print('preserved',keep.sum(),'removed',(~keep).sum())
