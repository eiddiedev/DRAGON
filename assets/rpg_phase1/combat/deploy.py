from cli import run,D
import json,sys
version=sys.argv[1];old=sys.argv[2];runtime=sys.argv[3];A=['--workspace-id','workspace_jcb1a5xe']
print(run('validate-'+version,['authoring','prefab','validate','dragon_rpg_restored',*A]),flush=True)
print(run('build-'+version,['authoring','prefab','build','dragon_rpg_restored',*A]),flush=True)
a=run('archive-'+version,['authoring','result','archive','dragon_rpg_restored','--name','龙眠职业战斗验证',*A]);print(a['uri'],flush=True)
run('stop-'+version,['runtime','stop','--runtime-id',runtime]);print(run('remove-'+version,['scene','remove',old,'--request-id','dragon-combat-remove-'+version]),flush=True)
print(run('import-'+version,['scene','import','--uri',a['uri'],'--request-id','dragon-combat-import-'+version]),flush=True)
print(run('runtime',['runtime','start']),flush=True)
