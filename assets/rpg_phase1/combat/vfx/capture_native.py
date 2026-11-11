import sys,subprocess,json,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));from cli import CLI,I,D
from scenario import call,click,R
kind=sys.argv[1]
if kind=='melee':pass
else:
 click('fx-open-contract-'+kind,.049,.187);click('fx-select-'+kind,.363,.525 if kind=='mage'else .625);click('fx-sign-'+kind,.637,.72);click('fx-toggle-'+kind,.947,.585)
p=subprocess.Popen([CLI,'runtime','input','mouse','down:0.856,0.81','wait:3000','--runtime-id',R,'--instance',I,'--json'],stdout=subprocess.PIPE,text=True)
for i in range(3):
 time.sleep(.2)
 print(call(f'fx-{kind}-shot-{i}','screenshot','--out',str(D/f'vfx/{kind}-{i}.png')),flush=True)
print(p.communicate(timeout=15)[0],flush=True)
print(call('fx-count-'+kind,'lua','eval','return GetStatus()','--script','dragon_fx.lua'),flush=True)
