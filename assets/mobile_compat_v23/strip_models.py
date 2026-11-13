from pathlib import Path
import json,struct
A=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9/ai-sessions/workspace_m293a9tg/wprefabs/dragon_fx_mobile_v22/assets/models')
wanted={'26rjifpwxdaw6ipb.glb':'wheat-high','wm0n7vp6egn81bmc.glb':'wheat-low','4v0jxixve0v72ii7.glb':'wheat-single','89es4kwvpzvk7dfj.glb':'shadow'}
out=[]
for p in A.glob('*/package/resource.json'):
 r=json.loads(p.read_text());name=wanted.get(r['uri'].split('/')[-1]);
 if not name:continue
 b=(p.parent/'model.glb').read_bytes();length=struct.unpack_from('<I',b,12)[0];d=json.loads(b[20:20+length]);clips=d.pop('animations',[])
 j=json.dumps(d,separators=(',',':')).encode();j+=b' '*((-len(j))%4);tail=b[20+length:]
 result=struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail
 f=Path('assets/mobile_compat_v23')/(name+'-geometry.glb');f.write_bytes(result)
 out.append({'name':name,'oldUri':r['uri'],'file':str(f.resolve()),'removedEmbeddedClips':len(clips),'binaryGeometrySkinTexturesUnchanged':True})
Path('assets/mobile_compat_v23/model-conversion.json').write_text(json.dumps(out,indent=2));print(out)
