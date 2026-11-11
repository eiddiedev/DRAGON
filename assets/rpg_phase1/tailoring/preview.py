import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from test_cli import run
D=Path(__file__).resolve().parent
R=json.loads((D.parent/'tailored-v3-reload.json').read_text())['runtimeId']
def call(label,*args):return run(label,['runtime',*args,'--runtime-id',R])
def click(label,x,y):return call(label,'input','mouse',f'click:{x},{y}')
kind=sys.argv[1]
if len(sys.argv)>2:click('v3-reopen-'+kind,.049,.187)
y={'ranged':.625,'mage':.525,'melee':.415}[kind]
click('v3-select-'+kind,.363,y);click('v3-sign-'+kind,.637,.72)
call('v3-front-'+kind,'js','eval','--file',str(D.parent/'front_view.js'))
call('v3-wait-'+kind,'input','keys','wait:450')
print(call('v3-status-'+kind,'lua','eval','return GetStatus()','--script','dragon_rpg.lua'))
print(call('v3-shot-'+kind,'screenshot','--out',str(D/(kind+'-v3.png'))))
