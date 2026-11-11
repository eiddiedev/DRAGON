import json,subprocess,sys
from pathlib import Path
O=Path(__file__).resolve().parents[1]/'assets/castle_refit_v1'
C='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world'
I=json.loads((O/'instance.json').read_text())['data']['instanceId']
for name,file in zip(sys.argv[1::2],sys.argv[2::2]):
 receipt=O/('import-'+name+'.json')
 if receipt.exists() and json.loads(receipt.read_text()).get('ok'):continue
 r=subprocess.run([C,'asset','import',str(Path(file).resolve()),'--instance',I,'--json'],capture_output=True,text=True)
 receipt.write_text(r.stdout);d=json.loads(r.stdout);print(name,r.stdout,flush=True)
 if not d.get('ok'):raise RuntimeError(r.stdout)
