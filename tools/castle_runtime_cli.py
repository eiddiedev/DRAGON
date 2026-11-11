"""Scoped runtime checks for the imported assets."""
import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'assets/castle_refit_v1';C='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world';I=json.loads((O/'instance.json').read_text())['data']['instanceId'];RID=json.loads((O/'runtime.json').read_text())['data']['runtimeId']
def call(args,receipt):
 r=subprocess.run([C,*args,'--instance',I,'--runtime-id',RID,'--json'],capture_output=True,text=True);(O/receipt).write_text(r.stdout);d=json.loads(r.stdout)
 if r.returncode or not d.get('ok'):raise RuntimeError(r.stdout+r.stderr)
 return d
if __name__=='__main__':
 if sys.argv[1]=='enter':
  call(['runtime','input','mouse','click:0.5,0.7'],'enter-title.json');call(['runtime','js','eval','await awaitFrames(25);return true;'],'enter-wait.json');call(['runtime','input','mouse','click:0.91,0.075'],'enter-book.json');call(['runtime','input','keys','W:300'],'enter-walk.json')
 elif sys.argv[1]=='view':
  label,x,y,z,yaw=sys.argv[2:];ts=json.loads((O/'targets.json').read_text())['data'];ts=ts.get('targets',[]) if isinstance(ts,dict) else ts;binding=next(t['bindingKey'] for t in ts if t['scriptId']=='a87ebe50-812d-4151-a056-727a118aecbd')
  code=f'local a=DouyinActorService.GetLocalActor();a:Teleport(CS.UnityEngine.Vector3({x},{y},{z}),CS.UnityEngine.Quaternion.Euler(CS.UnityEngine.Vector3(0,{yaw},0)));DouyinCameraService.SetYaw({yaw});DouyinCameraService.SetPitch(6);return true'
  call(['runtime','lua','eval',code,'--binding='+binding],label+'-pose.json');call(['runtime','js','eval','await awaitFrames(25);return true;'],label+'-wait.json');call(['runtime','screenshot','--out',str(O/(label+'.png'))],label+'-screenshot.json')
 elif sys.argv[1]=='js':print(call(['runtime','js','eval','--file',sys.argv[2]],sys.argv[3]))
