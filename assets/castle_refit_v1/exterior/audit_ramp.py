import trimesh,numpy as np,zipfile,json
m=trimesh.load('assets/castle_refit_v1/exterior/gothic_wall.glb').to_mesh();ts=m.triangles;c=m.triangles_center;ts=ts[(c[:,1]<73)&(m.face_normals[:,1]>.1)];xz=ts[:,:,[0,2]];zf=zipfile.ZipFile('assets/castle_refit_v1/scene-before.data');h=np.frombuffer(zf.read(next(n for n in zf.namelist() if n.startswith('HeightMap_'))),'<f4').reshape(257,257)*256;worst=(100,None);count=0
for x in np.linspace(-2.29,2.29,35):
 for z in np.linspace(17.01,20.99,61):
  if x < -2.3+.30*max(0.,min(1.,z-20))+.001:continue
  p=np.array([x,z]);v0=xz[:,1]-xz[:,0];v1=xz[:,2]-xz[:,0];v2=p-xz[:,0];den=v0[:,0]*v1[:,1]-v1[:,0]*v0[:,1];den[abs(den)<1e-7]=1e-7;u=(v2[:,0]*v1[:,1]-v1[:,0]*v2[:,1])/den;v=(v0[:,0]*v2[:,1]-v2[:,0]*v0[:,1])/den;ok=(u>=-1e-5)&(v>=-1e-5)&(u+v<=1.00001)
  assert ok.any(),(x,z)
  height=(ts[:,0,1]+u*(ts[:,1,1]-ts[:,0,1])+v*(ts[:,2,1]-ts[:,0,1]))[ok].max();wx,wz=127+x,176-z;i,j=int(wx),int(wz);a,b=wx-i,wz-j;terrain=(h[j,i]*(1-a)+h[j,i+1]*a)*(1-b)+(h[j+1,i]*(1-a)+h[j+1,i+1]*a)*b
  if height-terrain<worst[0]:worst=(float(height-terrain),(float(x),float(z),float(height),float(terrain)))
  count+=1
r={'sample_count':count,'minimum_clearance':worst[0],'worst_sample_glb_x_z_height_terrain':worst[1],'no_holes':True};assert worst[0]>.07,r;open('assets/castle_refit_v1/exterior/ramp-audit.json','w').write(json.dumps(r,indent=2));print(r)
