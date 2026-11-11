from scenario import call,click,R
from cli import CLI,I,D
import subprocess,time
click('v9-select',.363,.415);click('v9-sign',.637,.72);click('v9-toggle',.947,.585)
p=subprocess.Popen([CLI,'runtime','input','mouse','down:.856,.81','wait:3000','--runtime-id',R,'--instance',I,'--json'],stdout=subprocess.PIPE,text=True)
time.sleep(.45)
for i in range(3):call('v9-arc-'+str(i),'screenshot','--out',str(D/('v9-arc-'+str(i)+'.png')))
p.communicate(timeout=20)
call('v9-wait','input','keys','wait:700')
click('v9-begin',.049,.30);call('v9-start-wait','input','keys','wait:2800')
click('v9-guard',.781,.673);call('v9-guard-wait','input','keys','wait:1100');click('v9-spin',.852,.612);call('v9-spin-wait','input','keys','wait:1100');click('v9-judge',.93,.696)
p=subprocess.Popen([CLI,'runtime','input','mouse','down:.856,.81','wait:3000','--runtime-id',R,'--instance',I,'--json'],stdout=subprocess.PIPE,text=True)
call('v9-battle-image','screenshot','--out',str(D/'v9-battle.png'));p.communicate(timeout=20)
print(call('v9-battle-status','lua','eval','return GetStatus()','--script','dragon_combat.lua'),flush=True)
print(call('v9-battle-fx','lua','eval','return GetStatus()','--script','dragon_fx.lua'),flush=True)
# Release combat by native retreat if still active; contract handles explore state.
status=call('v9-battle-check','lua','eval','return IsParticipating()','--script','dragon_combat.lua')['result']
if status:click('v9-retreat',.049,.30)
click('v9-mage-book',.049,.187);click('v9-mage-select',.363,.525);click('v9-mage-sign',.637,.72);click('v9-mage-toggle',.947,.585)
call('v9-mage-ready','input','keys','wait:1500')
# Cooldowns persist through switching: wait until each is ready, then capture after click starts.
for i,(x,y,delay)in enumerate([(.781,.673,.30),(.852,.612,.20),(.93,.696,.65)],1):
 call('v9-cdwait'+str(i),'input','keys','wait:3000')
 p=subprocess.Popen([CLI,'runtime','input','mouse',f'click:{x},{y}','--runtime-id',R,'--instance',I,'--json'],stdout=subprocess.PIPE,text=True)
 time.sleep(delay)
 for j in range(2):call('v9-mage-image'+str(i)+str(j),'screenshot','--out',str(D/('v9-mage-'+str(i)+'-'+str(j)+'.png')))
 p.communicate(timeout=15)
print(call('v9-mage-state','lua','eval','return GetStatus()','--script','dragon_rpg.lua'),flush=True)
print(call('v9-mage-fx','lua','eval','return GetStatus()','--script','dragon_fx.lua'),flush=True)
