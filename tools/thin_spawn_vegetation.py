#!/usr/bin/env python3
"""Thin the v14 addition and feather the grass/plume transition, project closed."""
import pathlib,zipfile,json,random,math,shutil,datetime
import numpy as np
P=pathlib.Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0'
f=P/'scene.data';b=pathlib.Path('backups')/('before-thin-grass-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));shutil.copytree(P,b)
with zipfile.ZipFile(f) as z:entries=[(i,z.read(i)) for i in z.infolist()]
d=json.loads(next(raw for i,raw in entries if i.filename=='SerializePcgData.json'));H=np.frombuffer(next(raw for i,raw in entries if i.filename.startswith('HeightMap_')),'<f4').reshape(257,257)*256
rng=random.Random(1414);ns=d['nodeTransformDatas'];out=[];counts={'grass':0,'reed':0};cells=set()
for n in ns:
 name=n['nodeName']
 if not name.startswith(('spawn_grass_','spawn_reed_')):out.append(n);continue
 reed=name.startswith('spawn_reed_');x,z=n['pos']['x'],n['pos']['z']
 # Stratified thinning leaves irregular patches with breathing room.
 key=(reed,int(x/2.1),int(z/2.1))
 if key in cells or rng.random()>.46:continue
 cells.add(key)
 if reed:
  # Spread the northern third across the lawn edge, with density fading north.
  if z>29:z+=rng.uniform(0,9)
  if z>37 and rng.random()<(z-37)/14:continue
  n['scale']['x']*=.7;n['scale']['z']*=.7
  n['scale']['y']*=max(.42,.72-max(0,z-31)*.018)
  n['pos']['z']=round(z,4)
  i,j=int(x),int(z);a,c=x-i,z-j
  n['pos']['y']=float((1-c)*((1-a)*H[j,i]+a*H[j,i+1])+c*((1-a)*H[j+1,i]+a*H[j+1,i+1]))-.035
 else:
  # Irregular scalloped edge; short grass interleaves with the tall plumes.
  edge=35+3*math.sin(x*.24)+2*math.sin(x*.63)
  if z<edge and rng.random()>.3:continue
 counts['reed' if reed else 'grass']+=1;out.append(n)
d['nodeTransformDatas']=out
t=f.with_suffix('.tmp')
with zipfile.ZipFile(t,'w') as z:
 for i,raw in entries:z.writestr(i,json.dumps(d,ensure_ascii=False).encode() if i.filename=='SerializePcgData.json' else raw)
t.replace(f)
r=pathlib.Path('assets/vegetation_v14/report.json');v=json.loads(r.read_text());v.update(thinned_counts=counts,thinning_backup=str(b.resolve()),capacity_before_thinning=1891);r.write_text(json.dumps(v,ensure_ascii=False,indent=2));print(counts)
