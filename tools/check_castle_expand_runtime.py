"""Focused runtime checks after the new visual package is imported."""
import json
from castle_expand_runtime_cli import call, O

data = call(['runtime','targets'],'targets.json')['data']
targets = data.get('targets',[]) if isinstance(data,dict) else data
binding = next(t['bindingKey'] for t in targets
               if t['scriptId']=='a87ebe50-812d-4151-a056-727a118aecbd')
display = [t for t in targets if t['referenceName']=='castle_expand_display.lua']
assert len(display)==1, display
state=call(['runtime','lua','eval','return GetDisplayState()',
            '--binding='+display[0]['bindingKey']], 'display-state-final.json')['data']['result']
assert state['materials']>=7 and state['unsupported']==0, state
call(['runtime','lua','eval',
      'local a=DouyinActorService.GetLocalActor();a:Teleport(CS.UnityEngine.Vector3(127,70.9,155.3),CS.UnityEngine.Quaternion.identity);DouyinCameraService.SetYaw(0);DouyinCameraService.SetPitch(6);return true',
      '--binding='+binding], 'native-start.json')
call(['runtime','js','eval','await awaitFrames(25);return true;'],'native-settle.json')
call(['runtime','screenshot','--out',str(O/'final-native-stairs.png')],'native-stairs-shot.json')
call(['runtime','input','keys','W:4500'],'walk-final.json')
walk=call(['runtime','lua','eval',
           'local p=DouyinActorService.GetLocalActor().position;return {x=p.x,y=p.y,z=p.z}',
           '--binding='+binding],'walk-final-position.json')['data']['result']
assert walk['z']>170 and abs(walk['y']-72.24)<.025, walk
call(['runtime','screenshot','--out',str(O/'final-native-hall.png')],'native-hall-shot.json')
print(json.dumps({'display':state,'walk':walk},ensure_ascii=False))
