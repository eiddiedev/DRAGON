"""Expand the approved geometry to all 150 existing grass groups, project closed."""
from pathlib import Path
import json,zipfile,shutil,datetime,copy
ROOT=Path(__file__).resolve().parents[1];p=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0';f=p/'scene.data'
with zipfile.ZipFile(f) as z:entries=[(i,z.read(i)) for i in z.infolist()]
d=json.loads(next(v for i,v in entries if i.filename=='SerializePcgData.json'));old=copy.deepcopy(d['nodeTransformDatas'])
tpl=next(n for n in old if n['nodeName']=='golden_geometry_0');patches=[n for n in old if n['nodeName'].startswith(('golden_geometry_','golden_sample_'))];assert len(patches)==150
backup=ROOT/'backups'/('before-v19-expand-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'));shutil.copytree(p,backup)
removed=[];changed=[];ns=[]
for n in d['nodeTransformDatas']:
 if n['nodeName'].startswith('golden_sample_'):
  changed.append(n['id']);n['nodeName']=n['nodeName'].replace('golden_sample_','golden_geometry_')
  for k in ['aigcModelData','assetData']:n[k]=copy.deepcopy(tpl[k])
  n['physicsColliderData']['enableCollision']=False
 if n['nodeName'].startswith('pl_grass_'):
  q=n['pos'];radius=1.4+min(1.5,max(n['scale']['x'],n['scale']['z'])*.5)
  if any((q['x']-g['pos']['x'])**2+(q['z']-g['pos']['z'])**2<radius**2 for g in patches):removed.append(n);continue
 ns.append(n)
d['nodeTransformDatas']=ns;byid={n['id']:n for n in ns}
for n in old:
 if n['id'] not in changed and n not in removed:assert byid[n['id']]==n
assert not any(n['nodeName'].startswith('golden_sample_') for n in ns)
with zipfile.ZipFile(f.with_suffix('.tmp'),'w',zipfile.ZIP_DEFLATED) as z:
 for i,v in entries:z.writestr(i,json.dumps(d,ensure_ascii=False).encode() if i.filename=='SerializePcgData.json' else v)
f.with_suffix('.tmp').replace(f)
for rel in ['scripts/world_main.lua','scripts/world_main_v5.lua']:
 q=ROOT/rel;q.write_text(q.read_text().replace('"golden_sample_','"golden_geometry_'))
(ROOT/'assets/reeds_v19/expansion.json').write_text(json.dumps({'backup':str(backup),'converted':len(changed),'removed_low_grass':removed,'total':150},ensure_ascii=False,indent=2))
print('Converted',len(changed),'removed green clumps',len(removed),'total150; unrelated nodes unchanged')
