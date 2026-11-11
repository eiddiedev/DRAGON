from cli import run,D
import json,sys
R=json.loads((D/'runtime.json').read_text())['data']['runtimeId']
def call(label,*args):return run(label,['runtime',*args,'--runtime-id',R])
def click(label,x,y):return call(label,'input','mouse',f'click:{x},{y}')
if __name__=='__main__':
 k=sys.argv[1]
 if len(sys.argv)>2:click('reopen-'+k,.049,.187)
 click('choose-'+k,.363,{'mage':.525,'ranged':.625,'melee':.415}[k]);click('sign-'+k,.637,.72)
 call('status-'+k,'lua','eval','return GetStatus()','--script','dragon_rpg.lua')
 click('begin-'+k,.049,.30)
 call('wait-'+k,'input','keys','wait:2500')
 print(call('battle-'+k,'lua','eval','return GetStatus()','--script','dragon_combat.lua'))
 print(call('shot-'+k,'screenshot','--out',str(D/(k+'-battle.png'))))
