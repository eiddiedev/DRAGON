"""Import approved local assets once through the official asset CLI; keep receipts."""
import json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'assets/tripo/scene_install';C='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world';I=json.loads((O/'instance.json').read_text())['data']['instanceId'];M=json.loads((R/'assets/tripo/approved_batch/manifest.json').read_text())
for e in M['entries']:
 receipt=O/('import-'+e['id']+'.json')
 if e['id']=='horse_unridden_v4':receipt.write_text((O/'import-horse.json').read_text());continue
 if receipt.exists() and json.loads(receipt.read_text()).get('ok'):continue
 p=R/e.get('refined_file',e['source_file'])
 if e['id']=='sheep_clumped_v4':p=R/'assets/tripo/approved_batch/sheep_scene_ready.glb'
 result=subprocess.run([C,'asset','import',str(p),'--instance',I,'--json'],capture_output=True,text=True)
 receipt.write_text(result.stdout);d=json.loads(result.stdout)
 print(e['id'],d.get('ok'),d.get('data',{}).get('successCount'),flush=True)
 if result.returncode or not d.get('ok') or d.get('data',{}).get('successCount')!=1:raise RuntimeError(result.stdout+result.stderr)
print('IMPORTS_DONE',flush=True)
