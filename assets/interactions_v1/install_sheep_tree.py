from pathlib import Path
import json,zipfile,shutil,time,copy
P=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0'
O=Path(__file__).parent
backup=O/('before-sheep-tree-'+str(int(time.time()))+'.data');shutil.copy2(P/'scene.data',backup)
with zipfile.ZipFile(P/'scene.data') as z:e={n:z.read(n) for n in z.namelist()}
d=json.loads(e['SerializePcgData.json']);basic=copy.deepcopy({n['id']:n['basic'] for n in d['nodeTransformDatas']})
A=P/'ai-sessions/workspace_vrztdtlb/wprefabs/tripo_scene_v1/scripts'
for name in ['horse_seat_v1.lua','tripo_sheep_motion.lua','scene_mushroom.lua','scene_vehicle_boat.lua']:
 content=(A/name).read_text();matches=[v for v in d['runtimeScripts'].values() if v.get('referencePath','').split('/')[-1]==name];assert len(matches)==1,name
 matches[0]['content']=content;(P/'scripts'/matches[0]['referencePath']).write_text(content)
main=next(v for k,v in d['runtimeScripts'].items() if 'a87ebe50-812d-4151-a056-727a118aecbd' in str(k)+str(v.get('id')))
main['content']=(O/'main-sheep-tree-staged.lua').read_text()
(P/'scripts/modules/world_main.lua').write_text(main['content'])
with zipfile.ZipFile(P/'ai-sessions/workspace_vrztdtlb/wprefabs/tripo_scene_v1/package/prefab.wprefab') as z:b=json.loads(z.read('SerializePcgData.json'))
built={n['basic']['nodeName']:n for n in b['nodeTransformDatas']}
count=0
for n in d['nodeTransformDatas']:
 name=n['basic']['nodeName']
 if name in ['sheep_'+str(i) for i in range(9)]:
  n['physics']['physicsColliderData']=built[name]['physics']['physicsColliderData'];count+=1
assert count==9
assert basic=={n['id']:n['basic'] for n in d['nodeTransformDatas']}
e['SerializePcgData.json']=json.dumps(d,ensure_ascii=False).encode()
with zipfile.ZipFile(P/'scene.data','w',zipfile.ZIP_DEFLATED) as z:
 for n,v in e.items():z.writestr(n,v)
print('Installed sheep/tree + jump restore; preserved all transforms. Backup:',backup)
