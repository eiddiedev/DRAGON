from scenario import call,click
from cli import D,run
import json
click('final-pick',.363,.415);click('final-sign',.637,.72);click('final-begin',.049,.30)
call('final-ready','input','keys','wait:2000')
call('final-attack1','input','mouse','down:0.856,0.81','wait:2500')
click('final-shield',.781,.673)
call('final-attack2','input','mouse','down:0.856,0.81','wait:3000')
call('final-attack3','input','mouse','down:0.856,0.81','wait:3000')
r=call('final-outcome','lua','eval','return GetStatus()','--script','dragon_combat.lua')['result'];print(r,flush=True)
if r['phase']=='active':
 call('final-attack4','input','mouse','down:0.856,0.81','wait:2000')
 r=call('final-outcome2','lua','eval','return GetStatus()','--script','dragon_combat.lua')['result'];print(r,flush=True)
p=call('final-profile','lua','eval','return GetProfile()','--script','dragon_rpg.lua')['result'];print(p,flush=True)
call('final-settle','input','keys','wait:1500')
p2=call('final-profile-again','lua','eval','return GetProfile()','--script','dragon_rpg.lua')['result'];print({'unchanged':p==p2},flush=True)
print(call('final-clean','verifyNoTempHooks'),flush=True)
call('final-result-shot','screenshot','--out',str(D/'vfx/final-victory.png'))
print(call('final-stop','stop'),flush=True)
print(run('final-save',['scene','save','--request-id','dragon-rpg-particle-combat-save-20261111']),flush=True)
print(run('final-reopen',['runtime','start']),flush=True)
(D/'runtime.json').write_text((D/'final-reopen.json').read_text())
