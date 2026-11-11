#!/usr/bin/env python3
"""Apply to the saved, closed live project; preserve all unrelated nodes."""
import copy, datetime, json, math, pathlib, random, shutil, zipfile
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1]
P=pathlib.Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0'
b=ROOT/'backups'/('before-spawn-vegetation-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
shutil.copytree(P,b)
f=P/'scene.data'
with zipfile.ZipFile(f) as z: entries=[(i,z.read(i)) for i in z.infolist()]
d=json.loads(next(raw for i,raw in entries if i.filename=='SerializePcgData.json'))
H=np.frombuffer(next(raw for i,raw in entries if i.filename.startswith('HeightMap_')),'<f4').reshape(257,257)*256
ns=d['nodeTransformDatas']; before=copy.deepcopy(ns); by={n['id']:n for n in ns}; names={n['nodeName']:n for n in ns}
def ground(x,z):
 i,j=int(x),int(z);a,b=x-i,z-j
 return float((1-b)*((1-a)*H[j,i]+a*H[j,i+1])+b*((1-a)*H[j+1,i]+a*H[j+1,i+1]))
changed=set(); tree_names=[]
for n in ns:
 if n['nodeName'].startswith('pl_tree_') or n['nodeName']=='松树01':
  if n['isActive']:tree_names.append(n['nodeName'])
  for c in ns:
   if c['parentId']==n['id'] and c['nodeName']=='Leaves':
    c['physicsColliderData']['enableCollision']=False;changed.add(c['id'])
# Native billboard vegetation already supports wind and player interaction.
rng=random.Random(20261110);new=[];uid=1900000000
exclusions=[(121,57,3.0),(96,30,4.5),(84,66,6),(62,62,6)]
def add(tpl,name,x,z,sx,sy,color):
 global uid
 while uid in by:uid+=1
 n=copy.deepcopy(names[tpl]);n.update(id=uid,nodeName=name,parentId=0,isActive=True);uid+=1
 a=rng.uniform(0,math.pi);n['rot']={'x':0.,'y':math.sin(a),'z':0.,'w':math.cos(a)}
 n['pos']={'x':round(x,4),'y':round(ground(x,z)-.035,4),'z':round(z,4)}
 n['scale']={'x':sx,'y':sy,'z':sx};n['physicsColliderData']['enableCollision']=False
 n['appearanceData'].update(color=dict(zip('rgba',color)),castShadows=False)
 new.append(n)
# Overlapping short clumps cover the spawn lawn, instead of isolated tufts.
for z in np.arange(32,75,1.15):
 for x in np.arange(107,153,1.15):
  if ((x-130)/24)**2+((z-51)/24)**2>1:continue
  x+=rng.uniform(-.18,.18);z1=z+rng.uniform(-.18,.18)
  if any(math.hypot(x-a,z1-b)<r for a,b,r in exclusions):continue
  if ground(x,z1)<30 or math.hypot(ground(x+.3,z1)-ground(x-.3,z1),ground(x,z1+.3)-ground(x,z1-.3))>.5:continue
  add('青草01',f'spawn_grass_{len(new)}',x,z1,rng.uniform(3.2,3.9),rng.uniform(.85,1.35),(.68,.78,.56,1.))
low=len(new)
# Silver plume field behind the north-facing spawn, from the lawn to southern slope.
for z in np.arange(9,40,1.05):
 for x in np.arange(101,162,1.05):
  if ((x-131)/32)**2+((z-24)/18)**2>1:continue
  x+=rng.uniform(-.22,.22);z1=z+rng.uniform(-.22,.22)
  if any(math.hypot(x-a,z1-b)<r for a,b,r in exclusions):continue
  if ground(x,z1)<29.5:continue
  if math.hypot(ground(x+.3,z1)-ground(x-.3,z1),ground(x,z1+.3)-ground(x,z1-.3))>.55:continue
  add('狼尾草02',f'spawn_reed_{len(new)-low}',x,z1,rng.uniform(1.65,2.05),rng.uniform(1.65,2.25),(.86,.87,.76,1.))
ns.extend(new)
for n in before:
 if n['id'] not in changed:assert by[n['id']]==n
assert all(not n['physicsColliderData']['enableCollision'] for n in new)
t=f.with_suffix('.tmp')
with zipfile.ZipFile(t,'w') as z:
 for i,raw in entries:z.writestr(i,json.dumps(d,ensure_ascii=False).encode() if i.filename=='SerializePcgData.json' else raw)
t.replace(f)
out=ROOT/'assets/vegetation_v14';out.mkdir(exist_ok=True)
report={'backup':str(b),'leaves_collision_disabled':len(changed),'short_grass':low,'silver_plumes':len(new)-low,'unchanged_existing_nodes':len(before)-len(changed),'tree_names':tree_names}
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print({k:v for k,v in report.items() if k!='tree_names'})
