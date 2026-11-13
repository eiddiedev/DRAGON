"""Execute actual ReceiveRequest/Begin and combat rules without editor instances."""
import json
from pathlib import Path
from lupa import LuaRuntime

ROOT=Path(__file__).resolve().parent
BASE=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects')
AUTHOR=BASE/'project-8f93f84d-13f4-4ca1-95b2-42eafc8c27a5/ai-sessions/workspace_amfuq048/wprefabs/gameplay_v27/scripts'
OLD=BASE/'project-55a43370-8734-4825-92a8-b0de824a45e2/scripts/modules/imported/prefab_20/dragon_combat.lua'
SOURCES={'candidate':(ROOT/'dragon_combat.lua').read_text(),'author':(AUTHOR/'dragon_combat.lua').read_text()}
RULES=(AUTHOR/'dragon_combat_rules.lua').read_text()
CHECKS=[]


def section(source,a,b):
    return source[source.index(a):source.index(b,source.index(a))]


def fixture(source):
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute(RULES)
    lua.execute('''
engine={New=New,Classes=Classes,Join=Join,Boundary=Boundary,Step=Step,Request=Request}
U={Time={time=0}}
V=setmetatable({Distance=function(a,b)return math.sqrt((a.x-b.x)^2+(a.y-b.y)^2+(a.z-b.z)^2)end},{__call=function(_,x,y,z)return{x=x,y=y,z=z}end})
actor={actorID=1,position=V(-11,0,0),IsSitting=function()return false end,IsFlying=function()return false end}
CS={DouyinActorService={GetActorById=function()return actor end}}
json={decode=function()return incoming end}
ArenaRadius=10;serial=0;pending={};requestCount=0;publishCount=0
state={phase='defeat',members={},enemies={}}
function authority()return true end
function localActor()return actor end
function id(a)return tostring(a.actorID)end
function IsNight()return not daytime end
function center()return V(0,0,0)end
function active()return state and(state.phase=='ready'or state.phase=='active')end
function publish()publishCount=publishCount+1 end
function shadowSource()return true end
function request(packet)incoming=packet;requestCount=requestCount+1;ReceiveRequest('packet');return true end
rpg={GetProfile=function()return {class='melee'}end,SetMode=function()return true end}
''')
    lua.execute(section(source,'function ReceiveRequest(raw)','function Configure('))
    lua.execute(section(source,'function Begin(duel)','function SendAction('))
    retry=section(source,' for key,p in pairs(pending)do',' if playing then')
    lua.execute('''function tick()
 U.Time.time=U.Time.time+.03
 if active()then engine.Step(state,.03,{['1']={x=actor.position.x,z=actor.position.z}})end
 local m=state and state.members['1']
 '''+retry+'''end''')
    return lua


old=fixture(OLD.read_text())
old.execute('began=Begin(false);for i=1,110 do tick()end')
assert old.eval("began and serial>1 and state.phase=='defeat' and next(state.members)==nil and #state.enemies==0")
CHECKS.append('v26 reproduction: outside-one-meter visible entry creates repeated empty defeat epochs')

for name,source in SOURCES.items():
    function=section(source,'function ReceiveRequest(raw)','function Configure(')
    assert 'engine.Join(state,q.id,q.class,{x=a.position.x,z=a.position.z})' not in function
    assert function.count('local jx,jz=engine.Boundary(state,a.position.x,a.position.z)')==2
    CHECKS.append(name+': ordinary join now uses existing boundary just like duel')
    lua=fixture(source)
    lua.execute('began=Begin(false);for i=1,75 do tick()end')
    assert lua.eval("began and serial==1 and requestCount==1 and pending.join==nil and state.members['1']~=nil and state.phase=='active' and #state.enemies==4")
    assert lua.eval("state.members['1'].x==-9.5 and state.radius==10")
    CHECKS.append(name+': radius+1 entry joins at radius-0.5, one epoch/request, four enemies')
    lua.execute("state.phase='defeat';actor.position=V(-11,0,0);began=Begin(false);for i=1,75 do tick()end")
    assert lua.eval("began and serial==2 and requestCount==2 and pending.join==nil and state.phase=='active' and #state.enemies==4")
    CHECKS.append(name+': second defeat/rechallenge stays one new epoch and four enemies')
    lua=fixture(source);lua.execute('actor.position=V(-12,0,0);began=Begin(false);tick()')
    assert lua.eval("began and serial==1 and requestCount==1 and state.members['1']~=nil")
    CHECKS.append(name+': existing radius+2 interaction edge still works')
    lua=fixture(source);lua.execute('actor.position=V(-12.01,0,0);began=Begin(false)')
    assert lua.eval('not began and serial==0 and requestCount==0')
    CHECKS.append(name+': beyond radius+2 remains rejected without new epoch')
    lua=fixture(source);lua.execute('actor.position=V(1,0,0);began=Begin(false);tick()')
    assert lua.eval("began and state.members['1'].x==1 and state.members['1'].z==0")
    CHECKS.append(name+': already-inside player position unchanged')
    lua=fixture(source);lua.execute('daytime=true;began=Begin(false)')
    assert lua.eval('not began and serial==0 and requestCount==0')
    CHECKS.append(name+': nighttime requirement unchanged')
    compiled=LuaRuntime(unpack_returned_tuples=True).eval('load')(source,name)
    assert not isinstance(compiled,tuple),str(compiled)
    CHECKS.append(name+': full combat script compiles')

assert 'review-v27: each successfully spawned model' in SOURCES['author']
assert 'review-v27: each successfully spawned model' not in SOURCES['candidate']
CHECKS.append('author enemy fix retained; legacy candidate only received narrow join edit')
result={'passed':len(CHECKS),'checks':CHECKS,'author':str(AUTHOR/'dragon_combat.lua'),'runtimeVerified':False}
(ROOT/'test-rechallenge-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
