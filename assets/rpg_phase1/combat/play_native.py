from scenario import call,click
from cli import D
click('mage-pick',.363,.525);click('mage-sign',.637,.72);click('mage-start',.049,.30)
call('ready-wait','input','keys','wait:2100')
click('mage-blast',.781,.673)
for i in range(6):click('mage-attack-'+str(i),.856,.81)
print(call('active-models','js','eval','--file',str(D/'inspect_battle.js')))
print(call('mage-damage','lua','eval','return GetStatus()','--script','dragon_combat.lua'))
print(call('mage-combat-shot','screenshot','--out',str(D/'mage-combat-action.png')))
