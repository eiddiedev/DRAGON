import trimesh,numpy as np,json
m=trimesh.load('assets/castle_refit_v1/exterior/gothic_wall.glb').to_mesh();c=m.triangles_center;n=m.face_normals
mask=(abs(c[:,0])<2.301)&(c[:,2]>17.001)&(c[:,2]<20.999)&(c[:,1]<73)&(n[:,1]>.1)
r={}
for label,extra in [('full_width',np.ones(len(c),bool)),('central_4m',abs(c[:,0])<2),('central_3m',abs(c[:,0])<1.5)]:
 ix=np.where(mask&extra)[0];ns=n[ix];long=np.abs(ns[:,2]/ns[:,1]);cross=np.abs(ns[:,0]/ns[:,1]);total=np.sqrt(long**2+cross**2)
 r[label]={'max_longitudinal_degrees':float(np.degrees(np.arctan(long.max()))),'max_cross_degrees':float(np.degrees(np.arctan(cross.max()))),'max_combined_degrees':float(np.degrees(np.arctan(total.max()))),'worst_combined_world_xyz':[float(c[ix[total.argmax()],0]+127),float(c[ix[total.argmax()],1]),float(176-c[ix[total.argmax()],2])]}
open('assets/castle_refit_v1/exterior/ramp-slope-v8.json','w').write(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
