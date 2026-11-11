"""One-time replacement of the prior refit assembly through public Scene commands."""
import json
from castle_cli import call,O
from castle_runtime_cli import call as runtime_call
runtime_call(['runtime','stop'],'runtime-stop-gate-flat.json')
call(['scene','remove','669552679','--request-id','castle-gate-flat-remove-v4'],'remove-gate-flat.json')
a=json.loads((O/'archive-gate-flat.json').read_text())['data']
call(['scene','import','--uri',a['uri'],'--name','龙眠城堡精修','--position','0,0,0','--request-id','castle-gate-flat-import-v4'],'import-scene-gate-flat.json')
call(['scene','save','--request-id','castle-gate-flat-save-v4'],'save-gate-flat.json')
call(['runtime','start'],'runtime.json')
call(['runtime','lua','targets'],'targets.json')
