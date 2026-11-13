import json
from pathlib import Path
R=Path(__file__).parent
def result(n):
 d=json.loads((R/n).read_text());assert d['ok'] and d['data']['ok'],d;return d['data']['result']
a=result('main-added-initial.json');b=result('main-battle-active-verified.json');l=result('main-library-after.json')
v=b['combat']['visuals'];assert v['expected']==v['owned']==v['visible']==4 and v['setupFailures']==v['healthFailures']==v['animationFailures']==0
assert len(b['shadows'])==4 and all(not x['cubeChildren'] and x['healthCanvas'] for x in b['shadows'])
assert l['mode']=='lore' and l['lore']==1 and l['targetId']==1
names=['CustomMainButton','CustomSubButton','Skill2','Skill3','WeaponMenu']
buttons={x['name']:x['rectNormalizedTopLeft'] for x in b['buttons'] if x['name'] in names};assert len(buttons)==5
for i,n in enumerate(names):
 for m in names[i+1:]:
  x,y=buttons[n],buttons[m]
  assert max(x[0],y[0])>=min(x[2],y[2]) or max(x[1],y[1])>=min(x[3],y[3]),(n,m)
wind=[x for x in a['objects'] if x['name']=='windmill_rotor_pivot' and x['active']];assert len(wind)==1
w=next(x for x in a['windmillAfter'] if x['id']==wind[0]['id']);assert w['rot']!=wind[0]['rot']
bridge=a['dragon_world_bridge.lua'];assert bridge['altar']['placed']==[True]*4 and bridge['altar']['lit']==[False]*4
assert bridge['quality']['renderScale']==1 and not bridge['quality']['qualityModified']
assert sorted(x['name'] for x in a['objects'] if x['active'] and x['name'].startswith('sheep_'))==['sheep_0','sheep_2','sheep_3','sheep_5']
assert not [x for x in a['objects'] if x['active'] and x['name'].startswith('cl_')]
out={'environment':'official project, offscreen local preview; NOT phone review','runtimeId':'83f02c80-5459-4cf6-a411-ab0c5f18bf94','shadowModels':4,'shadowCubeChildren':0,'shadowHealthCanvas':4,'shadowInitializationErrors':0,'combatButtonsNonOverlapping':names,'windmillRotationChangedOver12Frames':True,'altarInitiallyDark':True,'altarAnchorsLoaded':4,'activeSheep':4,'activeCloudPatches':0,'renderScale':1,'forcedQualityDowngrade':False,'nativeManuscriptClickOpenedPage':1,'phoneReviewVerified':False,'waterFixed':False}
(R/'main-runtime-verification.json').write_text(json.dumps(out,indent=2,ensure_ascii=False));print(json.dumps(out,ensure_ascii=False))
