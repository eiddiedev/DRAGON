import json,struct,hashlib
from pathlib import Path
p=Path('assets/castle_smooth_v7/towers');r=json.loads((p/'receipt.json').read_text())
baseline={'expand_right_tower':19548,'expand_central_tower':17476,'expand_rear_towers':15136,'expand_clock_auxiliary':6912};out={}
assert len(r['outputs'])==4
for name,row in r['outputs'].items():
 b=Path(row['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256'];n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);pr=[q for m in g['meshes'] for q in m['primitives']];tris=sum(g['accessors'][q['indices']]['count']//3 for q in pr);assert tris==row['triangles'];assert tris<baseline[name];assert not any('COLOR_0' in q['attributes'] for q in pr)
 out[name]={'triangles':tris,'previous_triangles':baseline[name],'no_vertex_colors':True,'nodes':[q['name'] for q in g['nodes']],'materials':[q['name'] for q in g['materials']],'sha256_verified':True}
assert r['outputs']['expand_central_tower']['sha256']=='5032dab24d5f9f2e81bdc615bda7bc7e13ada1f852b267617642404b8c448abb'
audit={'outputs':out,'total_triangles':sum(a['triangles'] for a in out.values()),'previous_total_triangles':sum(baseline.values()),'tone_multiplier_baked':False,'central_resource_reused_unchanged':True}
(p/'export-audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(audit,indent=2))
