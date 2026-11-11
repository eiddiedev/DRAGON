"""Focused runtime checks after the new visual package is imported."""
import json
from castle_smooth_runtime_cli import call, O

data = call(['runtime','targets'],'targets.json')['data']
targets = data.get('targets',[]) if isinstance(data,dict) else data
binding = next(t['bindingKey'] for t in targets
               if t['scriptId']=='a87ebe50-812d-4151-a056-727a118aecbd')
display = [t for t in targets if t['referenceName']=='castle_smooth_display.lua']
assert len(display)==2,display
states=[]
for j,t in enumerate(display):
 state=call(['runtime','lua','eval','return GetDisplayState()','--binding='+t['bindingKey']],f'display-state-{j}.json')['data']['result']
 assert state['unsupported']==0,state
 states.append(state)
assert sorted(s['materials'] for s in states)==[5,7],states
tone=next(t for t in targets if t['referenceName']=='castle_tone.lua')
state=call(['runtime','lua','eval','return GetToneState()','--binding='+tone['bindingKey']],'tone-state.json')['data']['result']
assert state['exteriorMaterials']==12 and state['interiorMaterials']==8 and state['lights']==12,state
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
print(json.dumps({'display':states,'tone':state,'walk':walk},ensure_ascii=False))
