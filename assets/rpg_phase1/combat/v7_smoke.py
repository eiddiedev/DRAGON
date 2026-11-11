from cli import CLI,I,D
from scenario import call,click,R
import subprocess,time,json
print('start',call('v7-fx-ready','lua','eval','return GetStatus()','--script','dragon_fx.lua'),flush=True)
p=subprocess.Popen([CLI,'runtime','input','mouse','down:0.856,0.81','wait:3000','--runtime-id',R,'--instance',I,'--json'],stdout=subprocess.PIPE,text=True)
print(call('v7-audio-probe','js','eval','--file',str(D/'v7_probe.js')),flush=True)
print(call('v7-swing-image','screenshot','--out',str(D/'v7-swing.png')),flush=True)
p.communicate(timeout=20)
for i,(x,y)in enumerate([(.781,.673),(.852,.612),(.93,.696)],1):
 click('v7-skill'+str(i),x,y);call('v7-skill-wait'+str(i),'input','keys','wait:300');print(call('v7-skill-state'+str(i),'lua','eval','return GetStatus()','--script','dragon_rpg.lua'),flush=True);call('v7-gap'+str(i),'input','keys','wait:1100')
print('fx',call('v7-audio-end','lua','eval','return GetStatus()','--script','dragon_fx.lua'),flush=True)
click('v7-begin',.049,.30);call('v7-begin-wait','input','keys','wait:3000');print(call('v7-enemy-probe','js','eval','--file',str(D/'v7_probe.js')),flush=True)
print(call('v7-enemy-image','screenshot','--out',str(D/'v7-enemy.png')),flush=True)
print(call('v7-enemy-status','lua','eval','return GetStatus()','--script','dragon_combat.lua'),flush=True)
