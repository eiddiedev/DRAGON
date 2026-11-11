import json
from castle_entry_cli import call,O
status=call(['runtime','status'],'runtime-before-install.json')
if status['data']['status']!='not_started':
 call(['runtime','stop','--runtime-id',status['data']['runtimeId']],'runtime-stop-before-install.json')
a=json.loads((O/'archive.json').read_text())['data']
call(['scene','import','--uri',a['uri'],'--name','城堡入口石阶与前庭','--position','0,0,0','--request-id','castle-entry-v2-add-stairs-forecourt'],'scene-import.json')
call(['scene','remove','--request-id','castle-entry-v2-remove-castle-dial','--','-1084074086'],'scene-remove-dial.json')
call(['scene','save','--request-id','castle-entry-v2-initial-save'],'save-initial.json')
call(['runtime','start'],'runtime.json')
call(['runtime','lua','targets'],'targets.json')
