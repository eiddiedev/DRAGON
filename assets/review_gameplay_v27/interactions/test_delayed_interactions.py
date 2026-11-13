"""Execute actual candidate Lua functions under delayed-load fixtures (no editor).

These prove control-flow recovery and budgets, not C-end rendering/native UI delivery.
"""
from pathlib import Path
from lupa import LuaRuntime

HERE=Path(__file__).resolve().parent
explore=(HERE/'dragon_exploration.lua').read_text()
progress=(HERE/'dragon_progress.lua').read_text()

def vm():
    return LuaRuntime(unpack_returned_tuples=True)

def chunk(start,end):
    return explore[explore.index(start):explore.index(end,explore.index(start))]

for source in (explore,progress):
    result=vm().eval('load')(source)
    assert not isinstance(result,tuple), result

# The initial 30 unsuccessful checks cannot permanently poison a shared scope.
resolver=chunk('local getDependency','\nlocal progress,rules')
lua=vm()
lua.execute('''
CS={UnityEngine={Time={realtimeSinceStartup=0}}}
local calls=0
local module={ready=true}
local resolver=function(_,name)calls=calls+1;if CS.UnityEngine.Time.realtimeSinceStartup>=75 then return module end end
local scope={GetScript=resolver}
''' + resolver + '''
for second=0,74 do
 CS.UnityEngine.Time.realtimeSinceStartup=second
 for frame=1,60 do assert(getDependency('late.lua')==nil)end
 assert(scope.GetScript==resolver) -- private memo must not replace shared resolver
end
assert(calls<=40 and calls>=30)
CS.UnityEngine.Time.realtimeSinceStartup=75
local recovered
for second=75,80 do CS.UnityEngine.Time.realtimeSinceStartup=second;recovered=getDependency('late.lua');if recovered then break end end
assert(recovered==module)
local before=calls
for frame=1,120 do assert(getDependency('late.lua')==module)end
assert(calls==before)
assert(GetDependencyDiagnostics().failures['late.lua']==nil)
ReleaseMobileDependencies()
assert(next(GetDependencyDiagnostics().attempts)==nil)
''')

# Model objects can arrive after the book, fixed-position targets, and 30 seconds.
discovery=chunk('local function targetPosition(t)','local function nearby(t)')+chunk('local function objectAlive(go)','local function handleNativeClick(index)')
lua=vm()
lua.execute('''
local vmt={}
local function V(x,y,z)return setmetatable({x=x,y=y,z=z},vmt)end
vmt.__add=function(a,b)return V(a.x+b.x,a.y+b.y,a.z+b.z)end
vmt.__mul=function(a,b)return V(a.x*b,a.y*b,a.z*b)end
V=setmetatable({down={x=0,y=-1,z=0}},{__call=function(_,x,y,z)return setmetatable({x=x,y=y,z=z},vmt)end})
local U={Time={realtimeSinceStartup=0},GameObject={},Transform={},Physics={},QueryTriggerInteraction={Ignore=1}}
U.Physics.RaycastAll=function()return{Length=0}end
function typeof(x)return x end
local objects={};local calls=0
U.GameObject.Find=function(name)calls=calls+1;return objects[name]end
local function object(name)
 local go={name=name,scene={IsValid=function()return true end}}
 go.transform={position=V(1,2,3),localScale=V(1,1,1),lossyScale=V(1,1,1)}
 function go.transform:TransformPoint(p)return self.position+p end
 function go:SetActive(active)self.active=active end
 return go
end
local targets,eggs={},{}
local discovery=nil
local witchPlaced=false
local eggStage=2
''' + discovery + '''
local function tick(t)
 U.Time.realtimeSinceStartup=t;local before=calls;refreshDiscovery();assert(calls-before<=8)
end
for n=0,300 do tick(n*.25)end
assert(discovery.registered>0) -- flower/lore entries exist but cannot stop future checks
assert(discovery.byName['tripo_witch'].go==nil)
local count=#targets
local identities={};for i,t in ipairs(targets)do identities[i]=t end
for _,name in ipairs({'holy_tree3','tripo_witch','camp','mush','mush_12','sheep_0','tripo_camp_stele'})do objects[name]=object(name)end
for n=301,352 do tick(n*.25)end
for _,name in ipairs({'holy_tree3','tripo_witch','camp','mush','mush_12','sheep_0','tripo_camp_stele'})do assert(discovery.byName[name].go==objects[name],name)end
assert(#targets==count)
for i,t in ipairs(targets)do assert(t==identities[i])end
-- A model replaced after initial registration is re-acquired, without duplicating UI targets.
local prior=objects.camp;prior.scene.IsValid=function()return false end
objects.camp=object('camp')
for n=353,380 do tick(n*.25)end
assert(discovery.byName.camp.go==objects.camp and objects.camp~=prior)
assert(#targets==count)
-- Late inactive egg stages are looked up only in the loaded egg's own parent.
objects.altar3=object('altar3')
local list={Length=4}
for i=0,3 do
 local go=object('tripo_egg_stage_'..i);go.transform.name=go.name;go.transform.gameObject=go
 list[i]=go.transform
 if i==0 then objects[go.name]=go end
end
local parent={GetComponentsInChildren=function()return list end}
list[0].parent=parent
for n=381,440 do tick(n*.25)end
for i=0,3 do assert(eggs[i]and eggs[i].go==list[i].gameObject)end
assert(eggStage==-1) -- current personal stage must re-apply to newly loaded visuals
assert(discovery.eggTarget.position~=nil)
''')

# Native queued click keeps the same owner while incremental refresh runs.
clicks=chunk('local function handleNativeClick(index)','\nfunction GetStatus()')
lua=vm()
lua.execute('''
local U={Time={unscaledTime=10,frameCount=1}}
local current={kind='tree'}
local nativeTarget=current
local nativeExplore={}
local nativePotion=nil
local queuedNative=nil
local lastNativeClick=-10
local calls=0
local function interact()calls=calls+1 end
local function drinkMystery()error('not expected')end
''' + clicks + '''
queueNativeClick(1);queueNativeClick(1)
assert(queuedNative and queuedNative.target==current)
U.Time.frameCount=2
local click=queuedNative;queuedNative=nil
if click.target==nativeTarget and click.target==current then handleNativeClick(click.index)end
assert(calls==1)
handleNativeClick(1);assert(calls==1) -- debounce duplicate platform dispatch
U.Time.unscaledTime=11
queueNativeClick(1);assert(queuedNative)
''')

# Re-contract must still support repeated open/close and rollback after a failed open.
clear=chunk('local function clearNativeInteraction()','local witchPlaced=')
contract=chunk('function OpenContract(respec,continuation)','---------------------------------------------------------------- 誓约之书')
lua=vm()
lua.execute('''
local mode,contractSession,contractRpg,nativeExplore,nativePotion,nativeTarget
local removes,opens,continuations=0,0,0
local blocked=false
local actor={locked=false,Immobilize=function(self,value)self.locked=value end}
local main={SetExplorationMenu=function(v)mainMenu=v;actor.locked=v end}
local self={RemoveInteractorButton=function(_,button)assert(button);removes=removes+1 end}
local rpg={}
local getDependency=function()return rpg end
local function unavailable()return blocked end
local function toast(_)end
''' + clear + contract + '''
local callback
rpg.OpenContract=function(_,cb)opens=opens+1;callback=cb;return true end
for i=1,5 do
 nativeExplore={};nativeTarget={}
 assert(OpenContract(true,function()continuations=continuations+1 end))
 assert(mode=='class' and contractSession and nativeExplore==nil)
 assert(not OpenContract(true,nil))
 local previous=callback;callback();previous()
 assert(mode==nil and contractSession==nil and not mainMenu and not actor.locked)
 assert(continuations==i)
end
assert(opens==5 and removes==5)
for _,behavior in ipairs({'false','error'})do
 rpg.OpenContract=function()if behavior=='error'then error('not ready')end;return false end
 nativeExplore={};nativeTarget={}
 assert(not OpenContract(true,nil))
 assert(mode==nil and contractSession==nil and not mainMenu and not actor.locked)
end
''')

# A half-built UI canvas isn't mistaken for a ready book on the next update.
ui=chunk('local function buildUI()','-- Stable target records')
lua=vm()
lua.execute('''
local U={Time={realtimeSinceStartup=0},Object={Destroy=function(go)go.destroyed=true end}}
local uiReady=false
local nextUiAttempt=0
local root,dim,book,roast,reader,buffHud
local attempts=0
local partial
local function buildUIInner()
 attempts=attempts+1;root={};partial=root
 if attempts==1 then error('atlas not ready')end
 return true
end
''' +ui+ '''
assert(not buildUI());assert(root==nil and partial.destroyed and not uiReady)
assert(not buildUI());assert(attempts==1)
U.Time.realtimeSinceStartup=1
assert(buildUI()and uiReady and root)
assert(buildUI()and attempts==2)
''')
print('PASS: syntax; 75s late dependency recovery; shared resolver untouched; late witch/tree/camp/mushroom/sheep registration; <=8 exact-name queries/tick; stable targets; replaced objects; inactive egg stages; native dispatch debounce; 5 re-contracts; partial UI retry')

# A cosmetic effect error cannot strand the mystery-potion native button busy.
potion=chunk('local function drinkMystery()','local function beginHatch()')
lua=vm()
lua.execute('''
local U={Time={time=10}}
local potionBusy=false
local nextPotionAt=0
local current={kind='witch'}
local applies=0
local restores=0
local function unavailable()return false end
local function nearby()return true end
local function submit(_,args,callback)callback(false);return true end
local function applyPotion()applies=applies+1;if applies==1 then error('effect unavailable')end end
local function restorePotion()restores=restores+1 end
local function restoreBuff()end
local function toast(_)end
''' +potion+'''
drinkMystery();assert(not potionBusy and restores==1 and applies==1)
U.Time.time=12
drinkMystery();assert(not potionBusy and applies==2)
''')
print('PASS: potion effect failure releases button and permits the next request')

# All seven same-scope scripts must preserve the official method (including colon/self).
base=HERE.parents[2]/'editor_project/project_lapv8fm0/scripts/modules/imported/prefab_20'
for name in ('dragon_rpg.lua','dragon_weapons.lua','dragon_outfits.lua','dragon_combat.lua','dragon_daycycle.lua'):
    candidate=(HERE/name).read_text()
    original=(base/name).read_text()
    assert not isinstance(vm().eval('load')(candidate),tuple),name
    assert 'target.GetScript=function' not in candidate,name
    assert 'attempts[name] or 0)>=30' not in candidate,name
    old_marker=' ReleaseMobileDependencies=function()memo={};attempts={};nextAt={};failures={} end\nend\n'
    original_tail=original.split(old_marker,1)[1]
    owner='runtimeScope' if name in ('dragon_weapons.lua','dragon_outfits.lua') else 'scope'
    expected=original_tail.replace(owner+':GetScript(', 'getDependency(')
    if name=='dragon_daycycle.lua':
        expected=expected.replace("if not main then main=getDependency('dragon_world_bridge.lua');exploration=getDependency('dragon_exploration.lua')end", "if not main then main=getDependency('dragon_world_bridge.lua')end\n if not exploration then exploration=getDependency('dragon_exploration.lua')end")
    if name=='dragon_rpg.lua':
        cancel=candidate[candidate.index('function CancelContract()'):candidate.index('function OpenContract(change,callback,parent)')]
        expected=expected.replace('function IsContractOpen()return contract~=nil and contract.activeInHierarchy end\n', 'function IsContractOpen()return contract~=nil and contract.activeInHierarchy end\n'+cancel)
        expected=expected.replace('function OnDisable()\n if nativeTrial','function OnDisable()\n CancelContract()\n if nativeTrial')
        helper=candidate[candidate.index('-- One screen-space layout for all combat controls'):candidate.index('function SetMode(mode)')]
        expected=expected.replace('function SetMode(mode)',helper+'function SetMode(mode)',1)
        expected=expected.replace('hideExplore();context.mode="combat";toggleLabel.text="";setIcon(toggle,"exit",C15.iconSize or 60)','hideExplore();context.mode="combat";toggleLabel.text="";setIcon(toggle,"exit",C15.iconSize or 60);layoutCombatControls()')
        expected=expected.replace('if context.mode=="combat"then rt.anchoredPosition=V2(-(U.Screen.width-safe.xMax)*scale-74,(safe.yMin)*scale+392)','if context.mode=="combat"then layoutCombatControls()')
        old_native='''  for i=1,2 do
   if not combatAnchors[i]then local go,rt=rect(root.transform,"CombatAnchor"..i,i==1 and 216 or 136,i==1 and 216 or 136,i==1 and -215 or -235,i==1 and 185 or 422,V2(1,0));combatAnchors[i]=rt end
   local slot=native[i];if slot then slot.button.transform.position=combatAnchors[i].position;slot.button.transform.sizeDelta=combatAnchors[i].sizeDelta*(combatAnchors[i].lossyScale.x/slot.button.transform.parent.lossyScale.x) end
  end
'''
        expected=expected.replace(old_native,'')
        expected=expected.replace('nativeSlots=#native,skills=', 'combatLayout=C15.combatLayout,nativeSlots=#native,skills=')

    actual=candidate.split(' dependencyMemo={};dependencyAttempts={};dependencyNextAt={};dependencyFailures={}\nend\n',1)[1]
    assert actual==expected,name+' changed beyond private dependency calls/daycycle readiness'
    helper=candidate[candidate.index('local getDependency'):candidate.index('\nend\n',candidate.index('local function ReleaseMobileDependencies()'))+5]
    lua=vm()
    lua.execute('''
CS={UnityEngine={Time={realtimeSinceStartup=0}}}
local calls=0
local target={marker='official-scope'}
local module={}
local originalMethod=function(self,name)
 assert(self==target and name=='late.lua')
 calls=calls+1
 if CS.UnityEngine.Time.realtimeSinceStartup>=75 then return module end
end
target.GetScript=originalMethod
local scope=target
local runtimeScope=target
''' +helper+'''
for second=0,74 do CS.UnityEngine.Time.realtimeSinceStartup=second;getDependency('late.lua')end
assert(target.GetScript==originalMethod)
CS.UnityEngine.Time.realtimeSinceStartup=80
assert(getDependency('late.lua')==module)
assert(calls<=41)
''')

# A bridge that resolves first must not prevent daycycle discovering exploration later.
day=(HERE/'dragon_daycycle.lua').read_text()
start=day.index('function Update()')+len('function Update()')
init=day[start:day.index('\n if net and ',start)]
lua=vm()
lua.execute('''
local main,exploration
local elapsed=0
local queries=0
local function getDependency(name)
 if name=='dragon_world_bridge.lua' then return {bridge=true}end
 queries=queries+1
 if elapsed>=75 then return {IsBattleActive=function()return true end}end
end
local function updateInitialization()
''' +init+'''
end
updateInitialization();assert(main and not exploration)
elapsed=75;updateInitialization();assert(exploration and exploration.IsBattleActive())
assert(queries==2)
''')
print('PASS: all 7 script resolvers are private; original colon/self preserved; >30s recovery; 5 additional script bodies/cloning/combat unchanged; delayed daycycle battle guard')

# Open -> disable -> enable must leave every exploration modal hidden and unlocked.
life=explore[explore.index('function OnEnable()'):explore.index('function OnDestroy()')]
contract=chunk('function OpenContract(respec,continuation)','---------------------------------------------------------------- 誓约之书')
clear=chunk('local function clearNativeInteraction()','local witchPlaced=')
rpg=(HERE/'dragon_rpg.lua').read_text()
rpg_cancel=rpg[rpg.index('function CancelContract()'):rpg.index('function OpenContract(change,callback,parent)')]
lua=vm()
lua.execute('''
local function go()
 return{activeSelf=false,SetActive=function(self,v)self.activeSelf=v;self.activeInHierarchy=v end}
end
local actor={locked=false,Immobilize=function(self,v)self.locked=v end}
local mode,contractSession,contractRpg,nativeExplore,nativePotion,nativeTarget,current,queuedNative,callback
local root,dim=go(),go()
local book,roast,reader,buffHud={go=go()},{go=go()},{go=go()},{go=go()}
local uiReady=true
local lastScan=1
local self={RemoveInteractorButton=function()end}
local main={SetExplorationMenu=function(v)mainMenu=v;actor.locked=v end}
local function restorePotion()end
local function restoreBuff()end
local function unavailable()return false end
local function toast(_)end
local continued=0
local rpg={}
local savedCallback
rpg.OpenContract=function(_,cb)savedCallback=cb;rpg.open=true;return true end
rpg.CancelContract=function()rpg.open=false;savedCallback=nil;return true end
rpg.IsContractOpen=function()return rpg.open end
local getDependency=function()return rpg end
''' +clear+contract+life+'''
for _,kind in ipairs({'tasks','cook','lore'})do
 mode=kind;root:SetActive(true);dim:SetActive(true);book.go:SetActive(true);roast.go:SetActive(true);reader.go:SetActive(true);buffHud.go:SetActive(true)
 main.SetExplorationMenu(true);nativeExplore={};nativeTarget={};current=nativeTarget
 OnDisable();OnEnable()
 assert(root.activeSelf and mode==nil and not mainMenu and not actor.locked)
 assert(not dim.activeSelf and not book.go.activeSelf and not roast.go.activeSelf and not reader.go.activeSelf and not buffHud.go.activeSelf)
 assert(nativeTarget==nil and nativeExplore==nil and current==nil)
end
assert(OpenContract(true,function()continued=continued+1 end))
local stale=savedCallback
assert(rpg.open and actor.locked)
OnDisable();OnEnable()
assert(not rpg.open and savedCallback==nil and contractSession==nil and mode==nil and not actor.locked)
stale();assert(continued==0) -- interrupted class continuation is invalidated
assert(OpenContract(true,function()continued=continued+1 end))
savedCallback();assert(continued==1)
''')
lua=vm()
lua.execute('''
local function go()return{activeSelf=true,SetActive=function(self,v)self.activeSelf=v end}end
local contract,backdrop=go(),go()
local context={menu=true}
local profile={class='mage'}
local ready=false
local actor={locked=true,Immobilize=function(self,v)self.locked=v end}
local called=0
local contractCallback=function()called=called+1 end
local selection='mage'
local signPending=true
''' +rpg_cancel+'''
assert(CancelContract())
assert(not contract.activeSelf and not backdrop.activeSelf and not context.menu and not actor.locked)
assert(contractCallback==nil and selection==nil and not signPending and called==0 and ready)
assert(not CancelContract())
''')
print('PASS: tasks/cook/lore/class open-disable-enable leaves no modal overlay; interrupted class callback discarded; re-contract succeeds afterwards')
