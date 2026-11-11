"""Apply only with project saved and closed. Keep 25 existing grass clumps."""
from pathlib import Path
import zipfile,json,random,math,shutil,datetime
import numpy as np
p=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data'
with zipfile.ZipFile(p) as z:entries=[(i,z.read(i)) for i in z.infolist()]
d=json.loads(next(v for i,v in entries if i.filename=='SerializePcgData.json'))
ns=[n for n in d['nodeTransformDatas'] if n['nodeName'].startswith('golden_sample_')];assert len(ns)==25
H=np.frombuffer(next(v for i,v in entries if i.filename.startswith('HeightMap_')),'<f4').reshape(257,257)*256
r=random.Random(1826);points=[]
for n in ns:
 for attempt in range(10000):
  x=r.uniform(118.8,123.5);z=r.uniform(37.8,42.6)
  if ((x-121.15)/2.65)**2+((z-40.2)/2.6)**2>1:continue
  if any((x-a)**2+(z-b)**2<.64**2 for a,b in points):continue
  break
 else:raise RuntimeError('Unable to place sample')
 points.append((x,z));ix,iz=int(x),int(z);a,b=x-ix,z-iz
 y=float((H[iz,ix]*(1-a)+H[iz,ix+1]*a)*(1-b)+(H[iz+1,ix]*(1-a)+H[iz+1,ix+1]*a)*b)
 assert y>38
 n['pos']={'x':x,'y':y-.025,'z':z};yaw=r.uniform(-math.pi,math.pi);n['rot']={'x':0,'y':math.sin(yaw/2),'z':0,'w':math.cos(yaw/2)}
 width=r.uniform(.95,1.18);n['scale']={'x':width,'y':r.uniform(.78,1.18),'z':width}
backup=Path('backups')/('before-grass-scatter-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.data');shutil.copy2(p,backup)
with zipfile.ZipFile(p.with_suffix('.tmp'),'w',zipfile.ZIP_DEFLATED) as z:
 for i,v in entries:z.writestr(i,json.dumps(d,ensure_ascii=False).encode() if i.filename=='SerializePcgData.json' else v)
p.with_suffix('.tmp').replace(p)
print('Scattered 25 clumps, full-circle headings, no new nodes:',backup)
