"""One-time replacement of the prior refit assembly through public Scene commands."""
import json
from castle_cli import call,O
from castle_runtime_cli import call as runtime_call
runtime_call(['runtime','stop'],'runtime-stop-gate-corrected.json')
call(['scene','remove','1400991546','--request-id','castle-gate-coordinate-remove-v3'],'remove-gate-corrected.json')
a=json.loads((O/'archive-gate-corrected.json').read_text())['data']
call(['scene','import','--uri',a['uri'],'--name','龙眠城堡精修','--position','0,0,0','--request-id','castle-gate-coordinate-import-v3'],'import-scene-gate-corrected.json')
call(['scene','save','--request-id','castle-gate-coordinate-save-v3'],'save-gate-corrected.json')
call(['runtime','start'],'runtime.json')
call(['runtime','lua','targets'],'targets.json')
