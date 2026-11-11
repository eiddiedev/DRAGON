import subprocess,json,sys
from pathlib import Path
O=Path(__file__).parent;r=json.loads((O/'runtime.json').read_text())['data']['runtimeId'];args=sys.argv[1:];out=args.pop(0)
p=subprocess.run(['/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world',*args,'--instance','55c37f10-22fb-496a-930a-07e79637a6cd','--runtime-id',r,'--json'],capture_output=True,text=True);(O/out).write_text(p.stdout);print(p.stdout[:5000]);print(p.stderr);sys.exit(p.returncode)
