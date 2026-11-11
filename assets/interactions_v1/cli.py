import subprocess,json,sys
from pathlib import Path
C='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world'
O=Path(__file__).parent
I='55c37f10-22fb-496a-930a-07e79637a6cd'
a=sys.argv[1:];out=a.pop(0)
args=[C,*a,'--instance',I,'--json']
if (O/'runtime.json').exists() and a[:2]!=['runtime','start']:
 r=json.loads((O/'runtime.json').read_text());args+=['--runtime-id',r.get('data',r)['runtimeId']]
p=subprocess.run(args,capture_output=True,text=True);(O/out).write_text(p.stdout);print(p.stdout[:16000]);print(p.stderr);sys.exit(p.returncode)
