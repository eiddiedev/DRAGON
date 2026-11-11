from scenario import call,click,R
from cli import D,CLI,I
import subprocess,time,json
for ci,kind in enumerate(['melee','mage','ranged']):
 if ci:click('v8-book-'+kind,.049,.187)
 click('v8-class-'+kind,.363,{'melee':.415,'mage':.525,'ranged':.625}[kind]);click('v8-sign-'+kind,.637,.72);click('v8-toggle-'+kind,.947,.585)
 print(kind,call('v8-rig-'+kind,'lua','eval','return GetStatus()','--script','dragon_rpg.lua'),flush=True)
 call('v8-icons-'+kind,'screenshot','--out',str(D/('v8-'+kind+'-ui.png')))
 p=subprocess.Popen([CLI,'runtime','input','mouse','down:.856,.81','wait:1500','--runtime-id',R,'--instance',I,'--json'],stdout=subprocess.PIPE,text=True)
 call('v8-attack-image-'+kind,'screenshot','--out',str(D/('v8-'+kind+'-attack.png')));p.communicate(timeout=20)
 for i,(x,y)in enumerate([(.781,.673),(.852,.612),(.93,.696)],1):
  click('v8-skill-'+kind+str(i),x,y)
  call('v8-skill-image-'+kind+str(i),'screenshot','--out',str(D/('v8-'+kind+'-skill'+str(i)+'.png')))
  call('v8-gap-'+kind+str(i),'input','keys','wait:1300')
 print('skills',call('v8-skills-'+kind,'lua','eval','return GetStatus()','--script','dragon_rpg.lua'),flush=True)
 print('FX',call('v8-fx-'+kind,'lua','eval','return GetStatus()','--script','dragon_fx.lua'),flush=True)
print('done',flush=True)
