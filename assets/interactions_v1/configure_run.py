import json,copy
from pathlib import Path
O=Path(__file__).parent
v=json.loads((O/'horse-anim-before.json').read_text())['data']['result']['items'][0]['values']
a=json.loads((O/'import-horse-run-final.json').read_text())['data']['assets'][0]
v['animationAssets'][0]['assetData']={'uri':a['resource']['uri'],'assetID':a['id']}
v['animationAssets'][0]['clips'].append({'animationIndex':3,'animationName':'Run','loop':True})
c=json.loads(v['animationSet']['controllers'][0]['json']);nodes=c['graph']['nodes'];nodes['state:External/1']['speed']=1.6;nodes['state:External/2']['speed']=1.35
for index,name,rate in [(3,'Run',1),(4,'RunFast',1.4)]:
 n=copy.deepcopy(nodes['state:External/2']);n['id']=f'state:External/{index}';n['name']=name;n['speed']=rate;n['motion']['clipName']='Run';nodes[n['id']]=n;c['graph']['stateMachines']['sm:External']['childNodes'].append(n['id'])
v['animationSet']['controllers'][0]['json']=json.dumps(c,separators=(',',':'))
(O/'horse-running-config.json').write_text(json.dumps(v,ensure_ascii=False))
(O/'configure-run.js').write_text('await scene.components.set('+json.dumps({'nodes':['n1'],'type':'ugcAnimatorData','values':v})+');return {configured:true,states:["Idle","Walk","Trot","Run","RunFast"]};')
P=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0';A=P/'ai-sessions/workspace_vrztdtlb/wprefabs/tripo_scene_v1/scripts'
for p in [Path('scripts/scene_vehicle.lua'),A/'horse_seat_v1.lua',P/'scripts/horse_seat_v1.lua']:
 s=p.read_text().replace("play(speed>.2 and (speed>3.4 and 'Trot' or 'Walk') or 'Idle')", "play(speed<.2 and 'Idle' or speed<2.4 and 'Walk' or speed<5.5 and 'Trot' or speed<8 and 'Run' or 'RunFast')");p.write_text(s)
