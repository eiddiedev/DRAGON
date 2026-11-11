from pathlib import Path
import json,struct,hashlib

def positions(path):
 b=Path(path).read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);raw=b[28+n:];matches=[]
 for node in j['nodes']:
  if node.get('name')!='clock_face_receiver.001':continue
  vals=[]
  for p in j['meshes'][node['mesh']]['primitives']:
   a=j['accessors'][p['attributes']['POSITION']];v=j['bufferViews'][a['bufferView']];offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',12)
   vals += [tuple(round(x,6) for x in struct.unpack_from('<3f',raw,offset+i*stride)) for i in range(a['count'])]
  matches=sorted(vals)
 assert matches,path
 return matches
old=positions('assets/castle_sample_v3/clock/clocktower-sample-v2.glb');new=positions('assets/castle_smooth_v7/facade/clock/clocktower-smooth-v7.glb');d={'renderer_name':'clock_face_receiver.001','old_vertices':len(old),'new_vertices':len(new),'exact_rounded_positions_equal':old==new,'old_sha256':hashlib.sha256(repr(old).encode()).hexdigest(),'new_sha256':hashlib.sha256(repr(new).encode()).hexdigest()};assert old==new,d
Path('assets/castle_smooth_v7/facade/clock/dial-preservation-audit.json').write_text(json.dumps(d,indent=2));print(d)
