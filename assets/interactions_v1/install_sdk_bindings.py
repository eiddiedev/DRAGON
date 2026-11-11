from pathlib import Path
import json,zipfile,shutil
O=Path(__file__).parent;P=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0'
with zipfile.ZipFile(O/'scene-STAGED-UNTESTED.data') as z:e={n:z.read(n) for n in z.namelist()}
d=json.loads(e['SerializePcgData.json'])
with zipfile.ZipFile(P/'ai-sessions/workspace_vrztdtlb/wprefabs/tripo_scene_v1/package/prefab.wprefab') as z:s=json.loads(z.read('SerializePcgData.json'))
shutil.copy2(P/'scene.data',O/'horse-working-before-all.data')
ids={v['referenceName']:k for k,v in s['runtimeScripts'].items() if v.get('referenceName')}
oldids={k for k,v in d['runtimeScripts'].items() if (v.get('referencePath') or '').startswith('modules/scene_')}
for n in d['nodeTransformDatas']:
 bs=n.get('runtimeScriptBindings',[])
 for b in bs:
  if b['scriptId'] in oldids:
   name=d['runtimeScripts'][b['scriptId']]['referenceName']
   if name=='scene_vehicle_horse.lua':name='horse_seat_v1.lua'
   b['scriptId']=ids[name];b.pop('enabled',None)
   if not any(x['scriptId']=='d6f83b17-d36c-4840-ae2a-b896be27b101' for x in bs):bs.insert(0,{'scriptId':'d6f83b17-d36c-4840-ae2a-b896be27b101','scriptType':1,'paramsJson':'{}'})
for k in oldids:d['runtimeScripts'].pop(k)
for name in ['horse_seat_v1.lua','scene_vehicle_boat.lua','scene_vehicle_carpet.lua','scene_dial.lua','scene_mushroom.lua','scene_sheep_sound.lua']:
 k=ids[name];d['runtimeScripts'][k]=s['runtimeScripts'][k];(P/'scripts'/s['runtimeScripts'][k]['referencePath']).write_text(s['runtimeScripts'][k]['content'])
k='a87ebe50-812d-4151-a056-727a118aecbd';m=d['runtimeScripts'][k]['content']
m=m.replace("local bus=require('modules.scene_interaction_bus')","local request=UnityEngine.Shader.GetGlobalFloat('_DragonDialRequest')").replace('bus.dialRequests>0','request>0').replace('bus.dialRequests=0;',"UnityEngine.Shader.SetGlobalFloat('_DragonDialRequest',0);")
a=m.index('-- Insert after UI.clip is declared');b=m.index('\nfunction OnDestroy()',a);m=m[:a]+m[b:];m=m.replace('    UI.prepareInteractionAudio()\n','')
d['runtimeScripts'][k]['content']=m;(P/'scripts/modules/world_main.lua').write_text(m)
e['SerializePcgData.json']=json.dumps(d,ensure_ascii=False).encode()
with zipfile.ZipFile(P/'scene.data','w',zipfile.ZIP_DEFLATED) as z:
 for n,b in e.items():z.writestr(n,b)
shutil.copy2(P/'scene.data',O/'all-sdk-installed.data')
print('22 targets with SDK-generated identities, bootstrap and physical source files')
