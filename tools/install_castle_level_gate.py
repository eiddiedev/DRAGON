"""One-time replacement of the prior refit assembly through public Scene commands."""
import json
from castle_cli import call,O
from castle_runtime_cli import call as runtime_call
runtime_call(['runtime','stop'],'runtime-stop-gate-level.json')
call(['scene','remove','2102757258','--request-id','castle-gate-level-remove-v5'],'remove-gate-level.json')
a=json.loads((O/'archive-gate-level.json').read_text())['data']
call(['scene','import','--uri',a['uri'],'--name','龙眠城堡精修','--position','0,0,0','--request-id','castle-gate-level-import-v5'],'import-scene-gate-level.json')
call(['scene','save','--request-id','castle-gate-level-save-v5'],'save-gate-level.json')
call(['runtime','start'],'runtime.json')
call(['runtime','lua','targets'],'targets.json')
