"""Install a 25-clump sample ONLY with project saved and closed after importing reed_v18."""
from pathlib import Path
import zipfile,json,shutil,datetime,copy,math,random,re
import numpy as np
ROOT=Path(__file__).resolve().parents[1];p=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0';f=p/'scene.data'
with zipfile.ZipFile(f) as z:es=[(i,z.read(i)) for i in z.infolist()]
d=json.loads(next(v for i,v in es if i.filename=='SerializePcgData.json'));old=d['nodeTransformDatas'];tpl=next(n for n in old if n['nodeName']=='reed_v18')
assert not any(n['parentId']==tpl['id'] for n in old)
backup=ROOT/'backups'/('before-grass-v18-sample-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));shutil.copytree(p,backup)
H=np.frombuffer(next(v for i,v in es if i.filename.startswith('HeightMap_')),'<f4').reshape(257,257)*256
rng=random.Random(1616);patches=[];ids={n['id'] for n in old}
def height(x,z):
 ix,iz=int(x),int(z);a,b=x-ix,z-iz
 return float((H[iz,ix]*(1-a)+H[iz,ix+1]*a)*(1-b)+(H[iz+1,ix]*(1-a)+H[iz+1,ix+1]*a)*b)
for j in range(5):
 for i in range(5):
  x=119+i*1.05+rng.uniform(-.12,.12);z=38+j*1.05+rng.uniform(-.12,.12);y=height(x,z)
  assert y>38,'Do not populate the pit'
  n=copy.deepcopy(tpl);uid=1880000000+len(patches);assert uid not in ids
  n.update(id=uid,nodeName=f'golden_sample_{len(patches)}',parentId=0,isActive=True)
  n['pos']={'x':x,'y':y-.025,'z':z};a=rng.uniform(-.35,.35);n['rot']={'x':0,'y':math.sin(a/2),'z':0,'w':math.cos(a/2)};n['scale']={'x':1.1,'y':rng.uniform(.78,1.18),'z':1.1};n['physicsColliderData']['enableCollision']=False;patches.append(n)
# Remove low-grass clumps whose visible footprint overlaps the actual sample.
removed=[];ns=[]
for n in old:
 if n['id']==tpl['id']:continue
 if n['nodeName'].startswith('pl_grass_'):
  q=n['pos'];r=max(n['scale']['x'],n['scale']['z'])*.5+1.5
  if any((q['x']-g['pos']['x'])**2+(q['z']-g['pos']['z'])**2<r*r for g in patches):removed.append(n);continue
 ns.append(n)
ns.extend(patches);d['nodeTransformDatas']=ns
with zipfile.ZipFile(f.with_suffix('.tmp'),'w',zipfile.ZIP_DEFLATED) as z:
 for i,v in es:z.writestr(i,json.dumps(d,ensure_ascii=False).encode() if i.filename=='SerializePcgData.json' else v)
f.with_suffix('.tmp').replace(f)
for path in ['scripts/world_main_v5.lua','scripts/world_main.lua']:
 q=ROOT/path;s=q.read_text();names='{'+','.join(json.dumps(n['nodeName']) for n in patches)+'}'
 s,count=re.subn(r'UI.reeds=\{names=\{[^\n]*?\},items=', 'UI.reeds={names='+names+',items=',s,count=1);assert count==1;q.write_text(s)
(ROOT/'assets/reeds_v18/placement.json').write_text(json.dumps({'backup':str(backup),'patches':patches,'removed_low_grass':removed},ensure_ascii=False,indent=2))
print('Sample:',len(patches),'removed overlapping low grass:',len(removed),'pit high grass: 0')
