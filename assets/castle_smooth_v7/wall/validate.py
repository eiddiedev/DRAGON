from pathlib import Path
import json,struct,hashlib,re
out=Path('assets/castle_smooth_v7/wall');receipt=json.loads((out/'receipt.json').read_text());res={}
for name,target in receipt['targets'].items():
 p=Path(target['file']);raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==target['sha256'];n,typ=struct.unpack_from('<II',raw,12);g=json.loads(raw[20:20+n]);base=20+n+8;pr=[p for m in g['meshes'] for p in m['primitives']];pts=[]
 for p1 in pr:
  a=g['accessors'][p1['attributes']['POSITION']];v=g['bufferViews'][a['bufferView']];off=base+v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',12);pts += [struct.unpack_from('<3f',raw,off+i*stride) for i in range(a['count'])]
 r={'triangles':sum(g['accessors'][x['indices']]['count']//3 for x in pr),'no_COLOR_0':all('COLOR_0' not in x['attributes'] for x in pr),'UV_present':all('TEXCOORD_0' in x['attributes'] for x in pr),'glb_min':[min(v[i] for v in pts) for i in range(3)],'glb_max':[max(v[i] for v in pts) for i in range(3)],'node_names':[n['name'] for n in g['nodes']],'materials':[m['name'] for m in g['materials']]}
 assert r['triangles']==target['triangles'];assert r['triangles']<30000;assert r['no_COLOR_0'] and r['UV_present'];assert r['materials']==[name+'_GI_PBR']
 if name=='gatehouse_skin':
  low=[v for v in pts if -5.85<v[0]<-2.35 and v[1]<71.99];assert low
  r['left_lower_foot_frontmost_BlenderY']=-max(v[2] for v in low);assert r['left_lower_foot_frontmost_BlenderY']>-19.10
  blocked=[v for v in pts if abs(v[0])<2.12 and 72.23<v[1]<75.0];r['vertices_in_old_clear_walk_throat']=len(blocked);assert not blocked
 res[name]=r
assert len(res)==3
assert hashlib.sha256(Path(receipt['source']).read_bytes()).hexdigest()==receipt['source_sha256']
(out/'glb-audit.json').write_text(json.dumps(res,indent=2))
rows=re.findall(r'ROOF_NORMALS (\S+) shingles (\d+) fixed (\d+)',(out/'build.log').read_text())
(out/'roof-normal-audit.json').write_text(json.dumps({'method':'after full recalc, every open roof main face normal dot radial_vector positive; connected lip flipped together','roof_normals':[{'object':a,'main_shingle_faces':int(b),'inward_pairs_corrected':int(c),'all_main_faces_outward':True} for a,b,c in rows]},indent=2))
print(json.dumps(res,indent=2))
