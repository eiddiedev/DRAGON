from pathlib import Path
from test_cli import run
import json
D=Path(__file__).parent
RID=json.loads((D/'final-preview-reload.json').read_text())['runtimeId']
def cmd(label,*args):return run(label,['runtime',*args,'--runtime-id',RID])
def click(label,x,y):return cmd(label,'input','mouse',f'click:{x},{y}')
if __name__=='__main__':
 import sys
 kind=sys.argv[1]
 if kind=='mage':
  click('pick-mage',.5,.47);click('sign-mage',.5,.6);click('equip-mage',.947,.583)
 elif kind=='ranged':
  click('respec-bow',.5,.106);click('pick-bow',.63,.47);click('sign-bow',.5,.6);click('equip-bow',.947,.583)
 cmd(kind+'-front-camera','js','eval','--file',str(D/'front_view.js'))
 print(cmd(kind+'-status','lua','eval','return GetStatus()','--script','dragon_rpg.lua'))
 print(cmd(kind+'-front','screenshot','--out',str((D/(kind+'-front.png')).resolve())))
