from cli import run,D
import json,shutil
R=json.loads((D/'runtime.json').read_text())['data']['runtimeId']
shutil.copy2(D/'ranged-worn.png',D/'restored-original-ranger.png')
print(run('rollback-final-stop',['runtime','stop','--runtime-id',R]),flush=True)
print(run('rollback-final-save',['scene','save','--request-id','dragon-original-costume-rollback-save-20261111']),flush=True)
