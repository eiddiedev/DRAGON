from pathlib import Path
import json,zipfile,shutil,time,copy
P=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0';O=Path(__file__).parent
shutil.copy2(P/'scene.data',O/f'before-{int(time.time())}.data')
with zipfile.ZipFile(P/'scene.data') as z:e={n:z.read(n) for n in z.namelist()}
d=json.loads(e['SerializePcgData.json']);original=copy.deepcopy({n['id']:n['basic'] for n in d['nodeTransformDatas']})
A=P/'ai-sessions/workspace_vrztdtlb/wprefabs/tripo_scene_v1/scripts'
for v in d['runtimeScripts'].values():
 name=v.get('referencePath','').split('/')[-1]
 if name in ['tripo_sheep_motion.lua','scene_sheep_sound.lua','horse_seat_v1.lua','scene_vehicle_boat.lua']:v['content']=(A/name).read_text();(P/'scripts'/v['referencePath']).write_text(v['content'])
d['runtimeScripts']['a87ebe50-812d-4151-a056-727a118aecbd']['content']=Path('assets/interactions_v1/main-sheep-tree-staged.lua').read_text()
(P/'scripts/modules/world_main.lua').write_text(d['runtimeScripts']['a87ebe50-812d-4151-a056-727a118aecbd']['content'])
assets={a['name'].replace('_complete',''):a for a in json.loads((O/'import-complete.json').read_text())['data']['assets']}
template=next(n for n in d['nodeTransformDatas'] if n['basic']['nodeName']=='holy_canopy3')
existing={n['basic']['nodeName'] for n in d['nodeTransformDatas']}
for i in range(5,19):
 name='holy_canopy'+str(i)
 if name not in existing:
  n=copy.deepcopy(template);n['id']=-1900000100-i;assert n['id'] not in original;n['basic']['nodeName']=name;d['nodeTransformDatas'].append(n)
for n in d['nodeTransformDatas']:
 name=n['basic']['nodeName']
 if name in assets:
  a=assets[name];uri=a['resource']['uri'];n['basic']['scale']=a['scale'];n['editor']['assetData']={'uri':uri,'assetID':a['id']};n['resource']['aigcModelData']['uri']=uri;n['resource']['glbSliceData']['sourceUri']=uri
 else:assert n['basic']==original[n['id']]
e['SerializePcgData.json']=json.dumps(d,ensure_ascii=False).encode()
with zipfile.ZipFile(P/'scene.data','w',zipfile.ZIP_DEFLATED) as z:
 for n,b in e.items():z.writestr(n,b)
print('Installed two canopies, sheep motion/audio, main music fade/glow. Other transforms preserved.')
