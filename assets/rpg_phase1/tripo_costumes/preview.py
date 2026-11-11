from cli import run,D
import json,sys
R=json.loads((D/'runtime.json').read_text())['data']['runtimeId']
def call(label,*args):return run(label,['runtime',*args,'--runtime-id',R])
def click(label,x,y):return call(label,'input','mouse',f'click:{x},{y}')
k=sys.argv[1]
if len(sys.argv)>2:click('reopen-'+k,.049,.187)
click('choose-'+k,.363,{'mage':.525,'ranged':.625,'melee':.415}[k]);click('sign-'+k,.637,.72)
call('front-camera-'+k,'js','eval','--file',str(D.parent/'front_view.js'))
call('wait-'+k,'input','keys','wait:500')
print(call('status-'+k,'lua','eval','return GetStatus()','--script','dragon_rpg.lua'))
print(call('shot-'+k,'screenshot','--out',str(D/(k+'-worn.png'))))
