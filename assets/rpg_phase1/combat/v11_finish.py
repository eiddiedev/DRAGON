from scenario import call,click
from cli import D
import json
# All inputs are native; one input batch avoids tool latency between actions.
for kind,y in [('mage',.525),('ranged',.625),('melee',.415)]:
 click('v11-book-'+kind,.049,.187);click('v11-pick-'+kind,.363,y);click('v11-sign-'+kind,.637,.72)
 # The previous class cannot reset cooldowns. Let the longest expire.
 for i in range(5):call('v11-cd-'+kind+str(i),'input','keys','wait:3000')
 commands=['click:.049,.30','wait:3000','click:.781,.673','wait:1100','click:.852,.612','wait:1300','click:.93,.696','wait:1300','down:.856,.81','wait:3000']
 call('v11-fight-'+kind,'input','mouse',*commands)
 status=call('v11-result-'+kind,'lua','eval','return GetStatus()','--script','dragon_combat.lua')['result']
 if status['phase']=='active':
  call('v11-extra-'+kind,'input','mouse','down:.856,.81','wait:3000')
  status=call('v11-final-'+kind,'lua','eval','return GetStatus()','--script','dragon_combat.lua')['result']
 print(kind,status,flush=True)
 call('v11-result-pic-'+kind,'screenshot','--out',str(D/('v11-result-'+kind+'.png')))
 if status['phase']=='active':click('v11-retreat-'+kind,.049,.30)
print('profile',call('v11-profile-final','lua','eval','return GetProfile()','--script','dragon_rpg.lua'),flush=True)
print('fx',call('v11-fx-final','lua','eval','return GetStatus()','--script','dragon_fx.lua'),flush=True)
