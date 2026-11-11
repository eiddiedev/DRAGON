"""Expand approved grass to 150 clumps. Run only with project saved/closed."""
from pathlib import Path
import zipfile,json,random,math,shutil,datetime,copy,re
import numpy as np
ROOT=Path(__file__).resolve().parents[1];project=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0';p=project/'scene.data'
with zipfile.ZipFile(p) as z:entries=[(i,z.read(i)) for i in z.infolist()]
d=json.loads(next(v for i,v in entries if i.filename=='SerializePcgData.json'));old=d['nodeTransformDatas'];patches=[n for n in old if n['nodeName'].startswith('golden_sample_')];assert len(patches)==25
H=np.frombuffer(next(v for i,v in entries if i.filename.startswith('HeightMap_')),'<f4').reshape(257,257)*256
r=random.Random(1850);points=[(n['pos']['x'],n['pos']['z']) for n in patches];ids={n['id'] for n in old}
def height(x,z):
 ix,iz=int(x),int(z);a,b=x-ix,z-iz
 return float((H[iz,ix]*(1-a)+H[iz,ix+1]*a)*(1-b)+(H[iz+1,ix]*(1-a)+H[iz+1,ix+1]*a)*b)
for k in range(25,150):
 for attempt in range(20000):
  x=r.uniform(108,137);z=r.uniform(33.5,45.5)
  # Three overlapping lobes, wavy boundary; decreasing height/density at edges.
  edge=min(((x-cx)/rx)**2+((z-cz)/rz)**2 for cx,cz,rx,rz in [(118,40.2,10,5),(128,39,8,4.8),(111.5,41,4,3)])
  if edge>1+.1*math.sin(x*1.2):continue
  y=height(x,z)
  if y<38 or z<34:continue # leave rear depression bare
  if max(abs(height(x+.6,z)-y),abs(height(x,z+.6)-y))>.5:continue
  if (x-130)**2+(z-48)**2<5.5**2:continue # keep spawn access clear
  if (x-121)**2+(z-57)**2<5**2:continue
  spacing=.92 if edge<.62 else 1.22
  if any((x-a)**2+(z-b)**2<spacing**2 for a,b in points):continue
  if edge>.7 and r.random()<.25:continue
  break
 else:raise RuntimeError('Insufficient usable plateau')
 n=copy.deepcopy(patches[0]);uid=1880010000+k;assert uid not in ids
 n.update(id=uid,nodeName=f'golden_sample_{k}',parentId=0,isActive=True)
 n['pos']={'x':x,'y':y-.025,'z':z};yaw=r.uniform(-math.pi,math.pi);n['rot']={'x':0,'y':math.sin(yaw/2),'z':0,'w':math.cos(yaw/2)}
 width=r.uniform(1,1.25);n['scale']={'x':width,'y':r.uniform(.76,1.2)*(1-.28*max(0,(edge-.65)/.45)),'z':width}
 patches.append(n);points.append((x,z))
ns=[];removed=[]
for n in old:
 if n['nodeName'].startswith('golden_sample_'):continue
 if n['nodeName'].startswith('pl_grass_') and any((n['pos']['x']-x)**2+(n['pos']['z']-z)**2<1.5**2 for x,z in points):removed.append(n);continue
 ns.append(n)
ns+=patches;d['nodeTransformDatas']=ns
backup=ROOT/'backups'/('before-grass-expand-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));shutil.copytree(project,backup)
with zipfile.ZipFile(p.with_suffix('.tmp'),'w',zipfile.ZIP_DEFLATED) as z:
 for i,v in entries:z.writestr(i,json.dumps(d,ensure_ascii=False).encode() if i.filename=='SerializePcgData.json' else v)
p.with_suffix('.tmp').replace(p)
for name in ['world_main.lua','world_main_v5.lua']:
 q=ROOT/'scripts'/name;s=q.read_text();names='{'+','.join(json.dumps(n['nodeName']) for n in patches)+'}'
 s,count=re.subn(r'UI.reeds=\{names=\{[^\n]*?\},items=', 'UI.reeds={names='+names+',items=',s,count=1);assert count==1;q.write_text(s)
(ROOT/'assets/reeds_v18/expansion.json').write_text(json.dumps({'backup':str(backup),'patches':patches,'removed_low_grass':removed},ensure_ascii=False,indent=2))
print('Total grass:',len(patches),'removed duplicated low grass:',len(removed),'pit grass:0')
