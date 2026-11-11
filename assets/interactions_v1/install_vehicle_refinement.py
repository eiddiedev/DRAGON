from pathlib import Path
import json,zipfile,shutil,time
P=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0'
O=Path(__file__).parent
backup=O/('before-vehicle-refinement-'+str(int(time.time()))+'.data');shutil.copy2(P/'scene.data',backup)
with zipfile.ZipFile(P/'scene.data') as z:e={n:z.read(n) for n in z.namelist()}
d=json.loads(e['SerializePcgData.json']);basic={n['id']:n['basic'] for n in d['nodeTransformDatas']}
A=P/'ai-sessions/workspace_vrztdtlb/wprefabs/tripo_scene_v1/scripts'
for n in ['horse_seat_v1.lua','scene_vehicle_boat.lua']:
 content=(A/n).read_text();matches=[v for v in d['runtimeScripts'].values() if v.get('referencePath')==n];assert len(matches)==1
 matches[0]['content']=content;(P/'scripts'/n).write_text(content)
with zipfile.ZipFile(P/'ai-sessions/workspace_vrztdtlb/wprefabs/tripo_scene_v1/package/prefab.wprefab') as z:built=json.loads(z.read('SerializePcgData.json'))
horse=next(n for n in built['nodeTransformDatas'] if n['basic']['nodeName']=='tripo_horse')
for n in d['nodeTransformDatas']:
 if n['basic']['nodeName']=='tripo_horse':n['animation']=horse['animation']
 if n['basic']['nodeName'] in ['sailboat_0','sailboat_1','sailboat_2']:
  tr=n['physics']['triggerData'][0];tr['center']={'x':3.2,'y':.7,'z':-2};tr['size']={'x':3.2,'y':4,'z':4}
assert basic=={n['id']:n['basic'] for n in d['nodeTransformDatas']}
e['SerializePcgData.json']=json.dumps(d,ensure_ascii=False).encode()
with zipfile.ZipFile(P/'scene.data','w',zipfile.ZIP_DEFLATED) as z:
 for n,b in e.items():z.writestr(n,b)
shutil.copy2(P/'scene.data',O/'vehicles-refined-unverified.data')
print('Updated two existing script definitions and three boarding triggers; all basic transforms preserved. Backup:',backup)
