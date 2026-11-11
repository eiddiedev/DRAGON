import json,subprocess,time
from pathlib import Path
O=Path(__file__).parent;rid=json.loads((O/'runtime.json').read_text())['data']['runtimeId'];C='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world'
def run(code):
 p=subprocess.run([C,'runtime','lua','eval',code,'--script','a87ebe50-812d-4151-a056-727a118aecbd','--instance','55c37f10-22fb-496a-930a-07e79637a6cd','--runtime-id',rid,'--json'],capture_output=True,text=True);j=json.loads(p.stdout);assert j['ok'],j;return j['data']['result']
caps=json.loads((O/'caps.json').read_text())['data']['result'];results={}
for name in ['mush_17','mush']:
 p=caps[name];run(f'local u=CS.UnityEngine;local a=DouyinActorService.GetLocalActor();a:Teleport(u.Vector3({p["x"]},{p["y"]+.45},{p["z"]}));return true')
 samples=[]
 for i in range(9):
  samples.append(run('local u=CS.UnityEngine;local a=DouyinActorService.GetLocalActor();local g=u.GameObject.Find("'+name+'");local src=g:GetComponent(typeof(u.AudioSource));return {y=a.position.y,jump=a.jumpHeight,sound=src and src.isPlaying or false}'))
 results[name]={'capY':p['y'],'samples':samples,'maxRise':max(s['y'] for s in samples)-p['y']}
 print(name,results[name],flush=True)
(O/'bounce-results.json').write_text(json.dumps(results,indent=2))
