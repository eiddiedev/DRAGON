"""Install already-imported v12 assets. Run only with the project closed."""
from pathlib import Path
import copy, json, os, shutil, zipfile
from datetime import datetime
ROOT=Path(__file__).resolve().parents[2]
project=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0'
scene=project/'scene.data'
with zipfile.ZipFile(scene) as z:entries=[(i,z.read(i.filename)) for i in z.infolist()]
data=json.loads(next(raw for i,raw in entries if i.filename=='SerializePcgData.json'))
nodes=data['nodeTransformDatas']
def named(name):
 matches=[n for n in nodes if n['nodeName']==name and n['parentId']==0]
 assert len(matches)==1,(name,len(matches))
 return matches[0]
old_dragon,new_dragon=named('dragon_v8_live'),named('dragon_v12')
old_peak,new_peak=named('dragon_peak'),named('dragon_peak_v12')
for n in (old_dragon,new_dragon,old_peak,new_peak):
 assert not any(c['parentId']==n['id'] for c in nodes),('unexpected serialized children',n['nodeName'])
backup=ROOT/'backups'/('before-v12-install-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
shutil.copytree(project,backup)
for key in ('aigcModelData','assetData'):
 old_dragon[key]=copy.deepcopy(new_dragon[key])
for key in ('aigcModelData','assetData','glbSliceData','appearanceData','physicsColliderData','scale'):
 old_peak[key]=copy.deepcopy(new_peak[key])
assert old_peak['physicsColliderData']['enableCollision']
assert abs(old_peak['scale']['x']-89.9166641)<.01
nodes.remove(new_dragon);nodes.remove(new_peak)
tmp=scene.with_suffix('.data.tmp')
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
 for info,raw in entries:
  if info.filename=='SerializePcgData.json':raw=json.dumps(data,ensure_ascii=False,separators=(',',':')).encode()
  z.writestr(info,raw)
os.replace(tmp,scene)
print('Installed v12 resources preserving all other scene nodes; backup:',backup)
