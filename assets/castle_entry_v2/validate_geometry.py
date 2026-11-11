import json,struct,math
from pathlib import Path
import trimesh,numpy as np
p=Path('assets/castle_entry_v2');m=trimesh.load(p/'entry_collision.glb').to_mesh();t=m.triangles;n=m.face_normals;t=t[n[:,1]>.5];xz=t[:,:,[0,2]];a=xz[:,1]-xz[:,0];b=xz[:,2]-xz[:,0];den=a[:,0]*b[:,1]-b[:,0]*a[:,1];valid=abs(den)>1e-9;den[~valid]=1

def height(wx,wz):
 q=np.array([wx-127,176-wz]);v=q-xz[:,0];u=(v[:,0]*b[:,1]-b[:,0]*v[:,1])/den;w=(a[:,0]*v[:,1]-v[:,0]*a[:,1])/den;ok=valid&(u>=-1e-5)&(w>=-1e-5)&(u+w<=1.00001)
 assert ok.any(),(wx,wz)
 return float((t[:,0,1]+u*(t[:,1,1]-t[:,0,1])+w*(t[:,2,1]-t[:,0,1]))[ok].max())
points=[]
for z in np.linspace(155.3,159,75):
 for x in [124.8,127,129.2]:
  yy=height(x,z);expected=70.8+(z-155.7)*1.44/3.3;assert abs(yy-expected)<.001;points.append((float(x),float(z),yy))
for x,z in [(117.5,162.5),(123,166),(131,166),(115,166),(139,166),(124.69,159.5),(129.31,159.5)]:
 yy=height(x,z);assert abs(yy-72.24)<.001;points.append((x,z,yy))
# No collider spans the existing center road, avoiding coplanar duplicate surfaces.
for z in [160,163,167]:
 try:height(127,z)
 except AssertionError:pass
 else:raise AssertionError('overlapped central road')
checks=[]
for f in sorted(p.glob('entry_*.glb')):
 raw=f.read_bytes();length=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+length]);ps=[q for mm in g['meshes'] for q in mm['primitives']];assert not any('COLOR_0' in q['attributes'] for q in ps);count=sum(g['accessors'][q['indices']]['count']//3 for q in ps);assert count<30000;checks.append({'file':f.name,'triangles':count,'vertex_color':False})
r={'ramp_sample_count':225,'incline_degrees':math.degrees(math.atan(1.44/3.3)),'all_ramp_points_match_planar_grade':True,'forecourt_test_points':points[-7:],'sundial_point_stone_y':height(117.5,162.5),'central_road_overlap':False,'glbs':checks}
(p/'validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
