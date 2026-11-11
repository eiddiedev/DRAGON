"""Import frozen, audited GLBs through the official asset importer."""
import hashlib, json, sys
from pathlib import Path
from castle_expand_cli import call, O

kind=sys.argv[1]
assert kind in ('towers','wall')
report=json.loads((O/kind/'receipt.json').read_text())
outputs=report.get('outputs',report.get('targets'))
records=list(outputs.values()) if isinstance(outputs,dict) else outputs
paths=[]
for r in records:
    p=Path(r['file'])
    assert p.is_file()
    assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
    assert r['triangles']<=30000
    assert not r['vertex_colors']
    paths.append(str(p.resolve()))
receipt=call(['asset','import',*paths],f'import-{kind}.json')
assert not receipt['data']['failedFiles']
assert receipt['data']['successCount']==len(paths)
for asset,record in zip(receipt['data']['assets'],records):
    match=next(r for r in records if Path(r['file']).stem==asset['name'])
    assert int(asset['faceCount'])==match['triangles'],asset
    assert abs(asset['scale']['x']-match.get('scale',match.get('normalization_scale')))<.002,asset
print('Imported',kind,'capacity points',sum(float(a['capacity']) for a in receipt['data']['assets'])/1000)
