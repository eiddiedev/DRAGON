#!/usr/bin/env python3
"""Run only after importing reed_v15 into the scene and saving/closing project."""
import pathlib,zipfile,json,copy,random,math,shutil,datetime
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[1];p=pathlib.Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0';f=p/'scene.data'
with zipfile.ZipFile(f) as z:es=[(i,z.read(i)) for i in z.infolist()]
d=json.loads(next(v for i,v in es if i.filename=='SerializePcgData.json'));H=np.frombuffer(next(v for i,v in es if i.filename.startswith('HeightMap_')),'<f4').reshape(257,257)*256
original=d['nodeTransformDatas'];tpl=next(n for n in original if n['nodeName']=='reed_v15');assert not any(n['parentId']==tpl['id'] for n in original),'Inspect imported hierarchy before replacing'
backup=ROOT/'backups'/('before-golden-grass-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));shutil.copytree(p,backup)
ns=[n for n in original if not n['nodeName'].startswith('spawn_reed_') and n['id']!=tpl['id']];ids={n['id'] for n in ns};uid=1850000000;rng=random.Random(1515);manifest=[];occupied=set()
candidates=[n for n in original if n['nodeName'].startswith('spawn_reed_dense_')];rng.shuffle(candidates)
for old in candidates:
 x,z=old['pos']['x'],old['pos']['z'];key=(int(x/1.5),int(z/1.5))
 if key in occupied:continue
 occupied.add(key)
 n=copy.deepcopy(tpl)
 while uid in ids:uid+=1
 name=f'golden_grass_{len(manifest)}';n.update(id=uid,nodeName=name,parentId=0,isActive=True);uid+=1
 n['pos']=copy.deepcopy(old['pos']);a=rng.uniform(-.4,.4);n['rot']={'x':0.,'y':math.sin(a/2),'z':0.,'w':math.cos(a/2)}
 # The skinned GLB has meter-space vertices; imported animated assets retain meter scale.
 n['scale']={'x':1.15,'y':rng.uniform(.9,1.2),'z':1.15};n['physicsColliderData']['enableCollision']=False
 ns.append(n);manifest.append({'name':name,'pos':n['pos']})
assert 0<len(manifest)<1200,len(manifest)
d['nodeTransformDatas']=ns
with zipfile.ZipFile(f.with_suffix('.tmp'),'w') as z:
 for i,v in es:z.writestr(i,json.dumps(d,ensure_ascii=False).encode() if i.filename=='SerializePcgData.json' else v)
f.with_suffix('.tmp').replace(f)
(ROOT/'assets/reeds_v15/placement.json').write_text(json.dumps({'backup':str(backup),'template':tpl,'patches':manifest},ensure_ascii=False,indent=2))
src=ROOT/'scripts/world_main_v5.lua';s=src.read_text();marker='UI.L = {';assert s.count(marker)==1
block=(ROOT/'scripts/reed_contact.lua').read_text().replace('__REED_NAMES__','{'+','.join(json.dumps(n['name']) for n in manifest)+'}')
s=s.replace(marker,block+'\n'+marker,1);anchor='    updatePortals(actor)';assert s.count(anchor)==1
s=s.replace(anchor,anchor+'\n    if not UI.reeds.failed then\n        local ok,err=pcall(UI.updateReeds,actor)\n        if not ok then UI.reeds.failed=true;report("reeds failed "..tostring(err)) end\n    end')
from lupa import LuaRuntime
assert LuaRuntime().eval('function(s) local f,e=load(s);return e end')(s) is None
src.write_text(s);(ROOT/'scripts/world_main.lua').write_text(s)
print('Installed patches',len(manifest),'model triangles total',len(manifest)*904,'backup',backup)
