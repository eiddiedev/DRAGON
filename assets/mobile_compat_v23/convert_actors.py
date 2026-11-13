import json,subprocess,pathlib,struct
D=pathlib.Path('assets/mobile_compat_v23');roots=json.loads((D/'actor-originals.json').read_text());cli='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world';base=['--workspace-id','workspace_m293a9tg','--instance','1d1aa98e-dab4-4b8d-97c0-4ba4d2070f76','--prefab','mobile_actors_v23','--json'];out=[]
def call(args,file):
 r=subprocess.run([cli]+args+base,capture_output=True,text=True,timeout=180);(D/file).write_text(r.stdout);d=json.loads(r.stdout);assert d.get('ok'),d;return d['data']
for name,uri in dict((n['resource']['glbSliceData']['sourceUri'],n['basic']['nodeName'])for n in roots).items():
 uri,name=name,uri;name='sheep'if name.startswith('sheep_')else name
 if name=='tripo_horse':out.append({'name':name,'oldUri':uri,'newUri':'hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/uyduwywgnj13xzsn.glb'});continue
 key='model-'+name.replace('_','-')
 d=call(['authoring','resource','model','import',key,'--uri',uri],name+'-source-import.json')
 root=pathlib.Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9/ai-sessions/workspace_m293a9tg/wprefabs/mobile_actors_v23/assets/models')/key
 files=list(root.glob('topology/*.glb'))+list(root.glob('static/*.glb'));assert files,(d,root)
 b=files[0].read_bytes();l=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+l]);clips=g.pop('animations',[]);j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);tail=b[20+l:];f=D/(name+'-geometry.glb');f.write_bytes(struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail)
 target='model-mobile-'+name.replace('_','-')
 call(['authoring','resource','model','import',target,'--glb',str(f.resolve())],name+'-geometry-import.json');a=call(['authoring','resource','archive',target,'--kind','model'],name+'-geometry-archive.json');out.append({'name':name,'oldUri':uri,'newUri':a['uri'],'clipsRemoved':len(clips)})
 print(name,'converted',len(clips),'clips separated',flush=True);(D/'actor-uris.json').write_text(json.dumps(out,indent=2))
(D/'actor-uris.json').write_text(json.dumps(out,indent=2))
