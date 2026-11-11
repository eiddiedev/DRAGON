import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'assets/tripo/scene_install';C='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world';I=json.loads((O/'instance.json').read_text())['data']['instanceId'];W=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0/ai-sessions/workspace_vrztdtlb';op=json.loads((O/'anim-operation.json').read_text())['data']['operationId']
node,label,default=sys.argv[1:4]
def run(args,name):
 r=subprocess.run([C,*args,'--instance',I,'--json'],capture_output=True,text=True);(O/name).write_text(r.stdout);d=json.loads(r.stdout)
 if r.returncode or not d.get('ok'):raise RuntimeError(r.stdout+r.stderr)
 if d.get('data',{}).get('status') not in [None,'completed']:raise RuntimeError(r.stdout)
 return d
base=['authoring','skill','run'];common=['--workspace',str(W),'--prefab','tripo_scene_v1','--operation-id',op]
d=run(base+['inspect-instance-animations',*common,'--execution-id',label+'-inspect','--argv',json.dumps(['--config',json.dumps({'prefabId':'tripo_scene_v1','nodeHandle':node})])],label+'-inspect.json');clips=json.loads(d['data']['stdout'])['animations']
config={'prefabId':'tripo_scene_v1','nodeHandle':node,'localClips':[{'name':c['name'],'loop':True} for c in clips],'options':{'defaultStateName':default}}
output='wprefabs/tripo_scene_v1/.tmp/scene-execute/'+label+'-anim.js'
d=run(base+['generate-animation-config',*common,'--execution-id',label+'-generate','--argv',json.dumps(['--config',json.dumps(config),'--output',output])],label+'-generate.json')
d=run(['authoring','prefab','execute','tripo_scene_v1','--file',str(W/output),'--workspace-id','workspace_vrztdtlb'],label+'-anim-saved.json');print(label,'configured',default)
