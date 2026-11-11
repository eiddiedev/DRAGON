from scenario import call,click
from cli import D
click('v2-pick',.363,.625);click('v2-sign',.637,.72);click('v2-start',.049,.30)
call('v2-ready','input','keys','wait:2100')
click('v2-skill',.781,.673)
print(call('v2-down','input','mouse','down:0.856,0.81'),flush=True)
call('v2-wait','input','keys','wait:1800')
print(call('v2-up','input','mouse','up:0.856,0.81'),flush=True)
print(call('v2-models','js','eval','--file',str(D/'inspect_battle.js')),flush=True)
print(call('v2-state','lua','eval','return GetStatus()','--script','dragon_combat.lua'),flush=True)
print(call('v2-shot','screenshot','--out',str(D/'ranger-action-v2.png')),flush=True)
