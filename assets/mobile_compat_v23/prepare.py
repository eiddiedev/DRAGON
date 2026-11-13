import struct,json
from pathlib import Path
r=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9/ai-sessions/workspace_m293a9tg/wprefabs/mobile_fixture/assets/models/model-horse-original/topology/model.glb')
b=r.read_bytes();l=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+l]);d.pop('animations',None)
j=json.dumps(d,separators=(',',':')).encode();j+=b' '*((-len(j))%4);tail=b[20+l:];out=struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail
Path('assets/mobile_compat_v23/horse-no-animation.glb').write_bytes(out)
assert d['skins'] and b[20+l:]==out[20+len(j):]
print('Preserved all skin/geometry/texture bytes; only animations removed for isolated diagnosis')
