from cli import run,D
import json
R=json.loads((D/'runtime.json').read_text())['data']['runtimeId']
print(run('rollback-stop',['runtime','stop','--runtime-id',R]),flush=True)
print(run('rollback-author',['authoring','prefab','import',str(D.parent/'dragon-rpg-ui-preview.wprefab'),'--prefab','dragon_rpg_restored','--workspace-id','workspace_jcb1a5xe']),flush=True)
print(run('rollback-remove',['scene','remove','-1318693746','--request-id','dragon-tripo-rejected-remove-v2']),flush=True)
print(run('rollback-import',['scene','import','--uri','hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/vystl1mv2kcc88ua.wprefab','--request-id','dragon-costume-restore-original']),flush=True)
print(run('runtime',['runtime','start']),flush=True)
