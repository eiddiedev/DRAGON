from pathlib import Path
import zipfile,json,collections,hashlib,struct,io
OUT=Path(__file__).parent
p=Path('/Users/bytedance/Downloads/world_dev_unity_143126706-t0z0-PROD.zip');z=zipfile.ZipFile(p);names=set(z.namelist());d=json.loads(z.read('SerializePcgData.json'))
main=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-55a43370-8734-4825-92a8-b0de824a45e2')
local=json.loads(zipfile.ZipFile(main/'scene.data').read('SerializePcgData.json'))
result={'file':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'zipBytes':p.stat().st_size,'uncompressedBytes':sum(f.file_size for f in z.infolist()),'entries':len(names),'counts':dict(collections.Counter(Path(n).suffix for n in names)),'crcFailure':z.testzip(),'streaming':d.get('isOpenStreamingLoad'),'nodes':len(d['nodeTransformDatas']),'scripts':len(d['runtimeScripts'])}
byext=collections.defaultdict(lambda:{'bytes':0,'compressedBytes':0,'count':0})
for f in z.infolist():
 x=byext[Path(f.filename).suffix];x['bytes']+=f.file_size;x['compressedBytes']+=f.compress_size;x['count']+=1
result['sizeByType']=dict(byext)
refs=collections.defaultdict(list)
for r in d['resourceRefs']:
 path=r.get('pathOrUrl','')
 kind='bundled'if path in names else 'builtin'if path.startswith('Assets/')else 'remote'if path.startswith(('http:','https:','hamlet-ugc/'))else 'other'
 refs[kind].append({'id':r['id'],'path':path})
result['references']=dict(refs)
comparisons=[]
for key,s in d['runtimeScripts'].items():
 content=s.get('content','');name=s.get('referenceName')or key
 row={'key':key,'name':name,'bytes':len(content.encode()),'sha256':hashlib.sha256(content.encode()).hexdigest()}
 other=local['runtimeScripts'].get(key)
 if other:
  row['sameAsSaved']=content==other.get('content','')
  row['savedSha256']=hashlib.sha256(other.get('content','').encode()).hexdigest()
 if 'dragon_world_bridge.lua' in name or key=='4325a686-5236-4f81-972a-e9d055389cac':
  (OUT/'review-bridge.lua').write_text(content)
  row['hasV25ExplicitTextureDependency']='---@var TextureSource_ui_book:'in content
  row['markers']=[l[:350]for l in content.splitlines()if '书页资源准备超时'in l or 'build=\'v2'in l]
 comparisons.append(row)
result['scriptComparison']=comparisons
# Validate GLB container + direct external image/buffer dependencies without extracting.
models=[]
for name in sorted(names):
 if not name.endswith('.glb'):continue
 raw=z.read(name);magic,version,total=struct.unpack('<III',raw[:12]);n,kind=struct.unpack('<II',raw[12:20]);g=json.loads(raw[20:20+n])
 external=[x['uri']for k in ['buffers','images']for x in g.get(k,[])if x.get('uri')and not x['uri'].startswith('data:')]
 models.append({'path':name,'validHeader':magic==0x46546c67 and total==len(raw) and version==2,'images':len(g.get('images',[])),'animations':len(g.get('animations',[])),'external':external})
result['glb']={'count':len(models),'invalid':[m for m in models if not m['validHeader']],'externalReferences':[m for m in models if m['external']],'embeddedImages':sum(m['images']for m in models)}
(OUT/'review-package-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in result.items()if k not in ['scriptComparison','references']},ensure_ascii=False,indent=2));print('REF_COUNTS',{k:len(v)for k,v in refs.items()});print('NONLOCAL_REFS',json.dumps({k:v for k,v in refs.items()if k not in ['bundled','builtin']},ensure_ascii=False));print('BRIDGE',[x for x in comparisons if 'hasV25ExplicitTextureDependency'in x]);print('DIFFERENT_SCRIPTS',[(x['name'],x.get('sameAsSaved'))for x in comparisons if x.get('sameAsSaved') is not True])
