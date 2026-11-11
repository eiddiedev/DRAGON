from scenario import call,click,R
from cli import CLI,I,D
import subprocess,time
click('v13-choose',.363,.625);click('v13-sign',.637,.72)
# Static actual asset previews isolate both projectile materials without changing battle state.
for key,offset in [('ArrowEffect',-1.5),('BoltEffect',1.5)]:
 print(call('v13-preview-'+key,'lua','eval',f"local U=CS.UnityEngine;local a=CS.DouyinActorService.GetLocalActor();local E=require('official.effect.playback');local h,why=E.create(self,{key},a.position+U.Camera.main.transform.right*{offset}+U.Vector3(0,1,0),{{rotation=U.Quaternion.identity,scale=1}});return {{ok=h~=nil,reason=why}}",'--script','dragon_fx.lua'),flush=True)
print(call('v13-material-shot','screenshot','--out',str(D/'v13-materials.png')),flush=True)
click('v13-begin',.049,.30);call('v13-ready','input','keys','wait:2200')
p=subprocess.Popen([CLI,'runtime','input','mouse','down:.906,.843','wait:3000','--runtime-id',R,'--instance',I,'--json'],stdout=subprocess.DEVNULL)
time.sleep(.6);print(call('v13-native-shot','screenshot','--out',str(D/'v13-native.png')),flush=True);p.wait()
for i,xy in enumerate([( .906,.667),(.834,.694),(.81,.843)]):
 click('v13-skill'+str(i),*xy);call('v13-skillwait'+str(i),'input','keys','wait:1300')
print(call('v13-battle','lua','eval','return GetStatus()','--script','dragon_combat.lua'),flush=True)
print(call('v13-fx','lua','eval','return GetStatus()','--script','dragon_fx.lua'),flush=True)
print(call('v13-feedback-shot','screenshot','--out',str(D/'v13-feedback.png')),flush=True)
