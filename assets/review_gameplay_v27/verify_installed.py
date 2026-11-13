from pathlib import Path
import zipfile,json,hashlib,re
R=Path(__file__).parent
P=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-55a43370-8734-4825-92a8-b0de824a45e2')
def read(p):
 with zipfile.ZipFile(p)as z:return json.loads(z.read('SerializePcgData.json')),{n:hashlib.sha256(z.read(n)).hexdigest()for n in z.namelist()if n!='SerializePcgData.json'}
a,pa=read(R/'official-backup/scene-v26.data');b,pb=read(P/'scene.data')
old={n['id']:n for n in a['nodeTransformDatas']};new={n['id']:n for n in b['nodeTransformDatas']}
removed=set(map(int,json.loads((R/'main-replaced-roots.json').read_text())['rootIDs']))|{-535980144}
while True:
 q={i for i,n in old.items()if n['basic']['parentId']in removed};d=q-removed
 if not d:break
 removed|=d
unchanged=[i for i in old if i not in removed]
missing=[i for i in unchanged if i not in new]
changed=[{'id':i,'name':old[i]['basic']['nodeName']}for i in unchanged if i in new and old[i]!=new[i]]
by={}
for n in new.values():by.setdefault(n['basic']['nodeName'],[]).append(n)
spawnRemap=[]
for i in list(missing):
 n=old[i]
 if n['basic'].get('tag')=='BornPoint':
  peers=[v for v in new.values()if v['basic'].get('tag')=='BornPoint']
  assert len(peers)==1 and {k:v for k,v in n.items()if k!='id'}=={k:v for k,v in peers[0].items()if k!='id'}
  assert b['spawnPointData']==[{'id':peers[0]['id']}]
  spawnRemap.append({'before':i,'after':peers[0]['id']});missing.remove(i)
assert not missing,missing
def equivalent(x,y,path=()):
 if type(x) is not type(y):return False
 if isinstance(x,dict):return x.keys()==y.keys() and all(equivalent(x[k],y[k],path+(k,)) for k in x)
 if isinstance(x,list):return len(x)==len(y) and all(equivalent(v,w,path+(i,)) for i,(v,w) in enumerate(zip(x,y)))
 if isinstance(x,float):return abs(x-y)<=1e-5
 return x==y

def is_bat_bone(i):
 n=old[i]
 if n['basic']['nodeName'] not in {'body','wL1','wR1','wL2','wR2'}:return False
 seen=set()
 while n['basic']['parentId'] in old and n['id'] not in seen:
  seen.add(n['id']);n=old[n['basic']['parentId']]
  if re.fullmatch(r'bat_[0-9]',n['basic']['nodeName']):return True
 return False

animationPoseAdvances=[];unexpected=[]
for item in changed:
 i=item['id'];x=old[i];y=new[i]
 if equivalent(x,y):continue
 if is_bat_bone(i):
  x=json.loads(json.dumps(x));y=json.loads(json.dumps(y))
  for k in ('pos','rot'):x['basic'].pop(k,None);y['basic'].pop(k,None)
  if equivalent(x,y):animationPoseAdvances.append(item);continue
 unexpected.append(item)
assert not unexpected,unexpected[:10]
assert pa==pb,'Terrain or native payload bytes changed'
assert not any(re.fullmatch(r'cl_\d+',n)for n in by)
assert sorted(n for n in by if re.fullmatch(r'sheep_\d+',n))==['sheep_0','sheep_2','sheep_3','sheep_5']
for name in ['beam_'+str(i)for i in range(4)]+['runeg_'+str(i)for i in range(3)]:
 assert len(by[name])==1 and not by[name][0]['basic']['isActive'],name
for name in ['windmill','dragon_v8_live','horse', 'sheep_0','sheep_2','sheep_3','sheep_5']:
 matches=[n for n in old.values()if n['basic']['nodeName']==name]
 if not matches:continue
 assert len(by.get(name,[]))==1,name
 for k in ('pos','rot','scale'):
  av=matches[0]['basic'][k];bv=by[name][0]['basic'][k]
  assert max(abs(av[c]-bv[c])for c in av)<.0001,(name,k,av,bv)
scripts=b['runtimeScripts'];bodies={v.get('referenceName',''):v['content']for v in scripts.values()}
checks={'dragon_world_bridge.lua':['v27-progress-altar','review-v27-roaming-pitch','authored rotor ready'], 'dragon_combat.lua':['review-v27: each successfully spawned model'],'dragon_exploration.lua':['GetLoreTargets'], 'dragon_rpg.lua':['computeCombatLayout'], 'scene_vehicle_boat.lua':['function OnDisable']}
for name,strings in checks.items():
 content=bodies.get(name)or next((v['content']for v in scripts.values()if name in v.get('referencePath','')),None)
 assert content,name
 for s in strings:assert s in content,(name,s)
out={'sha256':hashlib.sha256((P/'scene.data').read_bytes()).hexdigest(),'bytes':(P/'scene.data').stat().st_size,'nodesBefore':len(old),'nodesAfter':len(new),'unaffectedNodesVerified':len(unchanged),'unchangedPayloads':len(pa),'sheep':['sheep_0','sheep_2','sheep_3','sheep_5'],'clouds':0,'altarVisualsInitiallyInactive':7,'scripts':len(scripts),'scriptMarkers':checks,'spawnIdRemapOnly':spawnRemap,'batBoneAnimationPoseAdvances':animationPoseAdvances,'status':'passed'}
(R/'main-install-verification.json').write_text(json.dumps(out,indent=2,ensure_ascii=False));print(json.dumps(out,ensure_ascii=False))
