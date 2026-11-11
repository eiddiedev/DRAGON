import json,subprocess
from pathlib import Path
O=Path(__file__).resolve().parents[1]/'assets/castle_entry_v2';C='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world';I=json.loads((O/'instance.json').read_text())['data']['instanceId']
def call(args,receipt,author=False):
 tail=[]
 if '--' in args:
  ix=args.index('--');tail=args[ix:];args=args[:ix]
 r=subprocess.run([C,*args,*(['--workspace-id','workspace_vrztdtlb'] if author else []),'--instance',I,'--json',*tail],capture_output=True,text=True);(O/receipt).write_text(r.stdout);d=json.loads(r.stdout)
 if not d.get('ok'):raise RuntimeError(r.stdout)
 print(receipt,'ok',flush=True);return d
