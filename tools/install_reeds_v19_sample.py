"""Replace the first 25 grass groups; run only after saving and closing the project."""
from pathlib import Path
import zipfile,json,copy,shutil,datetime
ROOT=Path(__file__).resolve().parents[1]
p=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0'
f=p/'scene.data'
with zipfile.ZipFile(f) as z: entries=[(i,z.read(i)) for i in z.infolist()]
d=json.loads(next(v for i,v in entries if i.filename=='SerializePcgData.json'))
old=copy.deepcopy(d['nodeTransformDatas']);tpl=next(n for n in old if n['nodeName']=='reed_v19')
targets={f'golden_sample_{i}' for i in range(25)}
assert len([n for n in old if n['nodeName'] in targets])==25
assert not any(n['parentId']==tpl['id'] for n in old)
backup=ROOT/'backups'/('before-v19-sample-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
shutil.copytree(p,backup)
for n in d['nodeTransformDatas']:
 if n['nodeName'] in targets:
  n['aigcModelData']=copy.deepcopy(tpl['aigcModelData']);n['assetData']=copy.deepcopy(tpl['assetData'])
  n['nodeName']=n['nodeName'].replace('golden_sample_','golden_geometry_')
  n['physicsColliderData']['enableCollision']=False
new=[n for n in d['nodeTransformDatas'] if n['id']!=tpl['id']];d['nodeTransformDatas']=new
byid={n['id']:n for n in new}
for n in old:
 if n['nodeName'] not in targets and n['id']!=tpl['id']:assert byid[n['id']]==n
with zipfile.ZipFile(f.with_suffix('.tmp'),'w',zipfile.ZIP_DEFLATED) as z:
 for i,v in entries:z.writestr(i,json.dumps(d,ensure_ascii=False).encode() if i.filename=='SerializePcgData.json' else v)
f.with_suffix('.tmp').replace(f)
(ROOT/'assets/reeds_v19/installation.json').write_text(json.dumps({'backup':str(backup),'replaced':25,'remaining_cards':125},indent=2))
for rel in ['scripts/world_main_v5.lua','scripts/world_main.lua']:
 path=ROOT/rel;s=path.read_text()
 for i in range(25):s=s.replace('"golden_sample_'+str(i)+'"','"golden_geometry_'+str(i)+'"')
 path.write_text(s)
print('Replaced 25, retained other node dictionaries exactly; backup',backup)
