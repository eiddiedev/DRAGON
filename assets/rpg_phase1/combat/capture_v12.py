from scenario import call,click,R
from cli import CLI,I,D
import subprocess,time
click('v12-ranger',.363,.625);click('v12-sign',.637,.72);click('v12-begin',.049,.30)
call('v12-ready','input','keys','wait:2200')
p=subprocess.Popen([CLI,'runtime','input','mouse','down:0.906,0.843 wait:3000','--runtime-id',R,'--instance',I,'--json'],stdout=subprocess.DEVNULL)
time.sleep(.9)
print(call('v12-shot','screenshot','--out',str(D/'v12-shot.png')))
p.wait()
print(call('v12-state','lua','eval','return GetStatus()','--script','dragon_combat.lua'))
print(call('v12-fx','lua','eval','return GetStatus()','--script','dragon_fx.lua'))
print(call('v12-hurt','screenshot','--out',str(D/'v12-hurt.png')))
