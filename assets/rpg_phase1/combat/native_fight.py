from scenario import call,click
from cli import D
import sys,math
kind=sys.argv[1]
click('pick-'+kind,.363,{'mage':.525,'melee':.415,'ranged':.625}[kind]);click('sign-'+kind,.637,.72);click('fight-'+kind,.049,.30)
call('ready-'+kind,'input','keys','wait:2000')
click('skill-'+kind,.781,.673)
print(call('models-'+kind,'js','eval','--file',str(D/'inspect_battle.js')),flush=True)
for step in range(7):
 result=call(f'{kind}-status-{step}','lua','eval','return GetStatus()','--script','dragon_combat.lua')['result'];print(step,result,flush=True)
 if result['phase']not in ['active','ready']:break
 # Normal native inputs: turn by camera then a short walk, then hold attack.
 q=call(f'{kind}-aim-{step}','js','eval', '''const a=CS.DouyinActorService.GetLocalActor();const bs=await lua.bindings();const b=bs.find(x=>x.referenceName==='dragon_combat.lua');return {x:a.position.x,z:a.position.z};''') if False else None
 if step==0:call('action-shot-'+kind,'screenshot','--out',str(D/(kind+'-action.png')))
 call(f'{kind}-hold-{step}','input','mouse','down:0.856,0.81','wait:1000')
 if step==3:click('skill2-'+kind,.781,.673)
print(call('final-'+kind,'lua','eval','return GetStatus()','--script','dragon_rpg.lua'),flush=True)
call('final-shot-'+kind,'screenshot','--out',str(D/(kind+'-result.png')))
