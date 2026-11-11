import json,zipfile,sys
from pathlib import Path
O=Path(__file__).parent;p=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0'
with zipfile.ZipFile(O/'before-recovered-install.data') as z:entries={n:z.read(n) for n in z.namelist()}
d=json.loads(entries['SerializePcgData.json'])
with zipfile.ZipFile(O/'scene-STAGED-UNTESTED.data') as z:s=json.loads(z.read('SerializePcgData.json'))
changed={n['id']:n for n in s['nodeTransformDatas']}
for n in d['nodeTransformDatas']:
 if n['id']==-1372397970:
  n.update(changed[n['id']])
  for b in n['runtimeScriptBindings']:
   d['runtimeScripts'][b['scriptId']]=s['runtimeScripts'][b['scriptId']]
entries['SerializePcgData.json']=json.dumps(d,ensure_ascii=False).encode()
with zipfile.ZipFile(p/'scene.data','w',zipfile.ZIP_DEFLATED) as z:
 for n,b in entries.items():z.writestr(n,b)
(p/'scripts/modules/world_main.lua').write_text(d['runtimeScripts']['a87ebe50-812d-4151-a056-727a118aecbd']['content'])
print('Only horse bindings installed for isolation')
