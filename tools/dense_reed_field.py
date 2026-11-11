#!/usr/bin/env python3
"""Dense continuous plume core, feathered boundary; no low-grass edits. Run closed."""
import pathlib,zipfile,json,copy,random,math,shutil,datetime
import numpy as np
p=pathlib.Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0';f=p/'scene.data'
backup=pathlib.Path('backups')/('before-dense-reeds-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));shutil.copytree(p,backup)
with zipfile.ZipFile(f) as z:es=[(i,z.read(i)) for i in z.infolist()]
d=json.loads(next(v for i,v in es if i.filename=='SerializePcgData.json'));H=np.frombuffer(next(v for i,v in es if i.filename.startswith('HeightMap_')),'<f4').reshape(257,257)*256
original=d['nodeTransformDatas'];tpl=next(n for n in original if n['nodeName']=='狼尾草02');ns=[n for n in original if not n['nodeName'].startswith('spawn_reed_')];ids={n['id'] for n in ns};rng=random.Random(1433);uid=1870000000;count=0
for z0 in np.arange(6,48,.68):
 for x0 in np.arange(98,164,.68):
  x=x0+rng.uniform(-.15,.15);z=z0+rng.uniform(-.15,.15)
  r=math.sqrt(((x-131)/30)**2+((z-25)/18)**2)
  edge=r+.035*math.sin(x*.8)+.025*math.sin(z*.9)
  if edge>1.15:continue
  density=1 if edge<.8 else max(0,(1.15-edge)/.35)**1.5
  if rng.random()>density:continue
  i,j=int(x),int(z);a,b=x-i,z-j
  y=float((1-b)*((1-a)*H[j,i]+a*H[j,i+1])+b*((1-a)*H[j+1,i]+a*H[j+1,i+1]))
  if y<29.5 or math.hypot(x-96,z-30)<4.5:continue
  while uid in ids:uid+=1
  n=copy.deepcopy(tpl);n.update(id=uid,nodeName=f'spawn_reed_dense_{count}',parentId=0,isActive=True);uid+=1;count+=1
  n['pos']={'x':x,'y':y-.035,'z':z};ang=rng.uniform(0,math.pi);n['rot']={'x':0.,'y':math.sin(ang),'z':0.,'w':math.cos(ang)}
  width=rng.uniform(1.25,1.55);height=rng.uniform(1.05,1.4)*(1-max(0,edge-.8)*.7)
  n['scale']={'x':width,'y':height,'z':width};n['physicsColliderData']['enableCollision']=False
  n['appearanceData'].update(color={'r':.86,'g':.87,'b':.76,'a':1.},castShadows=False);ns.append(n)
d['nodeTransformDatas']=ns
with zipfile.ZipFile(f.with_suffix('.tmp'),'w') as z:
 for i,v in es:z.writestr(i,json.dumps(d,ensure_ascii=False).encode() if i.filename=='SerializePcgData.json' else v)
f.with_suffix('.tmp').replace(f)
print('Dense reeds:',count,'backup:',backup)
