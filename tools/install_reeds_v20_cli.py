"""Remove only verified replaced grass through public CLI, never patch live files."""
import json,zipfile,subprocess
from pathlib import Path
out=Path('assets/reeds_v20');old=json.loads((out/'previous-layout.json').read_text());new=json.loads((out/'layout.json').read_text())
p=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data'
with zipfile.ZipFile(p) as z:d=json.loads(z.read('SerializePcgData.json'))
byid={n['id']:n for n in d['nodeTransformDatas']}
for n in old:assert byid[n['id']]['basic']['nodeName']==n['nodeName']
low=[]
for n in d['nodeTransformDatas']:
 b=n['basic']
 if not b['nodeName'].startswith('pl_grass_'):continue
 q=b['pos'];radius=1.2+min(1.3,max(b['scale']['x'],b['scale']['z'])*.5)
 if any((q['x']-g['pos']['x'])**2+(q['z']-g['pos']['z'])**2<radius**2 for g in new):low.append(n)
ids=[str(n['id']) for n in old+low];(out/'removed.json').write_text(json.dumps({'old_ids':ids[:150],'low_grass':low},indent=2))
cli='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world'
for start in range(0,len(ids),64):
 r=subprocess.run([cli,'scene','remove',*ids[start:start+64],'--request-id',f'grass-v20-remove-batch-{start}-20261110','--instance','8076003f-3d59-48fd-8225-60d26d83df30','--json'],capture_output=True,text=True)
 (out/f'remove-result-{start}.json').write_text(r.stdout);print(r.stdout,r.stderr)
 if r.returncode:raise SystemExit(r.returncode)
