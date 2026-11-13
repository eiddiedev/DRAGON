"""Execute actual Start/collider code and check the saved formal ownership tree.
Does not open an editor, edit a project, or claim Consumer swimming is fixed.
"""
from pathlib import Path
from lupa import LuaRuntime
import json,zipfile
HERE=Path(__file__).resolve().parent
SOURCE=(HERE/'dragon_outfits.lua').read_text()
PROJECT=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-55a43370-8734-4825-92a8-b0de824a45e2')
with zipfile.ZipFile(PROJECT/'scene.data') as archive:
    data=json.loads(archive.read('SerializePcgData.json'))
nodes={n['id']:n for n in data['nodeTransformDatas']}
def descendants(root):
    result=set()
    for n in nodes.values():
        visited=set();current=n
        while current and current['id'] not in visited:
            visited.add(current['id'])
            if current['id']==root:
                result.add(n['id']);break
            current=nodes.get(current['basic']['parentId'])
    return result
outfit_id=next(k for k,v in data['runtimeScripts'].items() if v.get('referenceName')=='dragon_outfits.lua')
owner=next(n for n in nodes.values() if any(b['scriptId']==outfit_id for b in n.get('runtimeScriptBindings',[])))
root_ids=descendants(owner['id'])
classwear=next(nodes[k] for k in root_ids if nodes[k]['basic']['nodeName']=='ClasswearRoot' and nodes[k]['basic']['parentId']==owner['id'])
source=next(nodes[k] for k in root_ids if nodes[k]['basic']['nodeName']=='SourceSets' and nodes[k]['basic']['parentId']==classwear['id'])
allowed=descendants(source['id'])
assert allowed < root_ids
assert {'WarriorSet','ArcherSet','MageSet'} <= {nodes[k]['basic']['nodeName'] for k in allowed}
for expected in ('DragonSword','DragonStaff','DragonBow','ShadowSpiritSource','ContractBook','golden_geometry_150'):
    target=next(k for k in root_ids if nodes[k]['basic']['nodeName']==expected)
    assert target not in allowed,expected
water_ids={n['id'] for n in nodes.values() if n['basic']['nodeName'] in ('海洋','PCGRiverEditor','__DouyinWaterArea2Triggers')}
assert not root_ids.intersection(water_ids)
assert not allowed.intersection(water_ids)

def chunk(start,end):
    pos=SOURCE.index(start);return SOURCE[pos:SOURCE.index(end,pos)]
vm=LuaRuntime(unpack_returned_tuples=True)
assert not isinstance(vm.eval('load')(SOURCE),tuple)
helpers=chunk('local function disableCollidersOn(gameObject)','local function spawnClone(entry, className)')
start=chunk('local nextInitAttempt=-1','\nfunction OnEnable()')
vm.execute('''
local started=false
local Time={time=0}
local Collider={}
local function typeof(t)return t end
local function isAlive(v)return v~=nil end
local sourceColliders={Length=3,[0]={enabled=true},[1]={enabled=true},[2]={enabled=true}}
local unrelated={Length=5,[0]={enabled=true},[1]={enabled=false},[2]={enabled=true},[3]={enabled=true},[4]={enabled=true}}
local rootQueries,sourceQueries=0,0
local root={transform={}}
function root:GetComponentsInChildren()rootQueries=rootQueries+1;return unrelated end
local sourceGo={}
function sourceGo:GetComponentsInChildren()sourceQueries=sourceQueries+1;return sourceColliders end
local sourceSets={gameObject=sourceGo}
local runtimeScope={GetResourceRoot=function()return root end,GetTransformByPath=function()return sourceSets end,GetGameObjectByPath=function()return {}end}
local resourceRoot,resourceRootTransform
local SOURCE_SETS_PATH='ClasswearRoot/SourceSets'
local PROTOTYPE_PARK={}
local CLASS_SOURCE={melee='ClasswearRoot/SourceSets/WarriorSet',ranged='ClasswearRoot/SourceSets/ArcherSet',mage='ClasswearRoot/SourceSets/MageSet'}
local hostCalls,refreshCalls=0,0
local function registerWithHost()hostCalls=hostCalls+1 end
local function refreshActors()refreshCalls=refreshCalls+1 end
'''+helpers+start+'''
Start()
assert(started and sourceSets.localPosition==PROTOTYPE_PARK)
assert(rootQueries==0 and sourceQueries==1)
for i=0,2 do assert(sourceColliders[i].enabled==false)end
for i=0,4 do assert(unrelated[i].enabled==(i~=1))end
assert(hostCalls==1 and refreshCalls==1)
Time.time=3;Start();assert(sourceQueries==1 and rootQueries==0)
-- Clone cleanup is still limited to the exact clone object supplied by spawnClone.
local cloneCollider={enabled=true}
local clone={GetComponentsInChildren=function()return{Length=1,[0]=cloneCollider}end}
disableCollisions(clone)
assert(not cloneCollider.enabled and rootQueries==0)
''')
print(f'PASS: actual Lua Start/clone ownership; saved DragonRPG subtree={len(root_ids)}, costume subtree={len(allowed)}, unrelated={len(root_ids-allowed)}, water nodes={len(water_ids)} untouched')
