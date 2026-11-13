import json,zipfile,pathlib,hashlib,sys,math,copy
D=pathlib.Path(__file__).parent
P=pathlib.Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-55a43370-8734-4825-92a8-b0de824a45e2/scene.data')
def read(p): return json.loads(zipfile.ZipFile(p).read('SerializePcgData.json'))
a,b=read(D/'main-before.scene.data'),read(P)
def subtree(nodes,root):
 ids={root}
 while True:
  new=ids|{n['id'] for n in nodes if n.get('basic',{}).get('parentId') in ids}
  if new==ids:return ids
  ids=new
old=subtree(a['nodeTransformDatas'],1375360307)
unchanged={n['id']:n for n in a['nodeTransformDatas'] if n['id'] not in old}
current={n['id']:n for n in b['nodeTransformDatas']}
def comparable(n):
 n=copy.deepcopy(n)
 n.pop('editor',None) # editor adds lock metadata to generated water trigger nodes
 anim=n.get('animation',{}).get('ugcAnimatorData')
 if anim and anim.get('animationSet'):anim['animationSet'].pop('guid',None) # serializer-generated animation GUID
 return n
def same(a,b):
 if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all(same(a[k],b[k]) for k in a)
 if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(same(x,y) for x,y in zip(a,b))
 if isinstance(a,(int,float)) and isinstance(b,(int,float)):return math.isclose(a,b,rel_tol=1e-6,abs_tol=1e-5)
 return a==b
batRoots=[n['id'] for n in a['nodeTransformDatas'] if n.get('basic',{}).get('nodeName','').startswith('bat_')]
bats=set().union(*(subtree(a['nodeTransformDatas'],i) for i in batRoots))
changed=[]
for i,n in unchanged.items():
 oldNode=comparable(n)
 newNode=comparable(current.get(i,{}))
 if n.get('basic',{}).get('tag')=='BornPoint':
  candidates=[x for x in current.values() if x.get('basic',{}).get('tag')=='BornPoint']
  assert len(candidates)==1
  newNode=comparable(candidates[0]);newNode['id']=i
 if i in bats:
  for field in ['pos','rot']:
   oldNode['basic'].pop(field,None);newNode['basic'].pop(field,None)
 if not same(oldNode,newNode):changed.append(i)
roots=[n for n in b['nodeTransformDatas'] if n.get('basic',{}).get('nodeName')=='龙眠审核加载修复v25']
assert len(roots)==1, 'v25 root absent or duplicate'
assert not changed, f'unrelated nodes changed: {changed[:10]}'
assert 1375360307 not in current
assert -535980144 in current
names=lambda d:sorted(n['basic']['nodeName'] for n in d['nodeTransformDatas'] if n.get('basic',{}).get('nodeName','').startswith('golden_geometry_'))
assert names(a)==names(b),'wheat layout membership changed'
result={'sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'root':roots[0]['id'],'verifiedOutsideGameplay':len(unchanged),'ignoredChanges':'water editor lock metadata, animator GUID regeneration, float roundoff bat animation pose and regenerated spawn ID','wheatNodes':len(names(b)),'streaming':b['isOpenStreamingLoad'],'sceneBytes':P.stat().st_size}
(D/'saved-verification.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
