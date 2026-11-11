from cli import run,D
import json
R=json.loads((D/'runtime.json').read_text())['data']['runtimeId'];run('stop-v1',['runtime','stop','--runtime-id',R]);run('remove-v1',['scene','remove','1776202034','--request-id','dragon-tripo-v2-remove-v1']);uri=json.loads((D/'archive-v2.json').read_text())['data']['uri'];print(run('import-v2',['scene','import','--uri',uri,'--request-id','dragon-tripo-v2-import']));print(run('runtime',['runtime','start']))
