from pathlib import Path
BASE=Path(__file__).resolve().parents[3]
SOURCE=BASE/'editor_project/project_lapv8fm0/scripts/modules/imported/prefab_20'
OUT=Path(__file__).resolve().parent
resolver='''-- review-v27: private cache. Never replace the shared runtime-scope resolver.
local getDependency
local dependencyMemo,dependencyAttempts,dependencyNextAt,dependencyFailures={},{},{},{}
getDependency=function(name)
 if dependencyMemo[name] then return dependencyMemo[name] end
 local now=CS.UnityEngine.Time.realtimeSinceStartup
 if now<(dependencyNextAt[name] or 0) then return nil end
 local attempt=(dependencyAttempts[name] or 0)+1
 dependencyAttempts[name]=attempt
 -- Fast initial readiness checks, then bounded slow recovery for streamed resources.
 dependencyNextAt[name]=now+(attempt<30 and 1 or 5)
 local ok,value=pcall(function()return scope:GetScript(name)end)
 if ok and value then
  dependencyMemo[name]=value;dependencyFailures[name]=nil
  if attempt>=30 then print('[review-v27] dependency recovered: '..name) end
  return value
 end
 dependencyFailures[name]=tostring(value or 'not loaded')
 if attempt==30 then print('[review-v27] dependency waiting: '..name..' '..dependencyFailures[name]) end
 return nil
end
function GetDependencyDiagnostics()return{build='review-v27',attempts=dependencyAttempts,failures=dependencyFailures}end
local function ReleaseMobileDependencies()
 dependencyMemo={};dependencyAttempts={};dependencyNextAt={};dependencyFailures={}
end
'''
for name in ('dragon_exploration.lua','dragon_progress.lua'):
 text=(SOURCE/name).read_text()
 start=text.index('-- mobile-v23: resolve each dependency')
 end=text.index('\nlocal progress,rules' if name=='dragon_exploration.lua' else '\nlocal rules,profile',start)
 text=text[:start]+resolver+text[end:]
 # Calls below the resolver use the private memo; keep its underlying official call intact.
 split=text.index('\nlocal progress,rules' if name=='dragon_exploration.lua' else '\nlocal rules,profile')
 text=text[:split]+text[split:].replace('scope:GetScript(', 'getDependency(')
 (OUT/name).write_text(text)

p=OUT/'dragon_exploration.lua';s=p.read_text()
s=s.replace('local lastScan=-100','local lastScan=-100\nlocal uiReady=false\nlocal nextUiAttempt=0\nlocal discovery=nil')
s=s.replace("local function open(kind)\n", "local function open(kind)\n if not uiReady then toast('页面资源仍在准备，请稍后重试');return false end\n")
s=s.replace("if kind=='tree'then OpenContract(true,nil)", "if kind=='tree'then local ok,why=OpenContract(true,nil);if not ok then toast('誓约之书正在准备，请稍后重试');print('[review-v27] contract: '..tostring(why))end")
s=s.replace('local function buildUI()\n if root then return true end', 'local function buildUIInner()\n if uiReady then return true end')
start=s.index('local function discover()')
end=s.index('local function handleNativeClick(index)',start)
s=s[:start]+'''local function buildUI()
 if uiReady then return true end
 if U.Time.realtimeSinceStartup<nextUiAttempt then return false end
 nextUiAttempt=U.Time.realtimeSinceStartup+1
 local ok,result=pcall(buildUIInner)
 if ok and result then uiReady=true;return true end
 -- A failed construction must not leave a half-built canvas marked as ready.
 if root then U.Object.Destroy(root)end
 root=nil;dim=nil;book=nil;roast=nil;reader=nil;buffHud=nil
 if not ok then print('[review-v27] exploration UI waiting: '..tostring(result))end
 return false
end

-- Stable target records preserve the native button/click owner across late loads.
-- Only exact gameplay names are queried, in bounded batches. No global resource scans.
local function objectAlive(go)
 if not go then return false end
 local ok,live=pcall(function()return go.transform~=nil and go.scene:IsValid()end)
 return ok and live
end
local function initDiscovery()
 if discovery then return end
 discovery={refs={},byName={},cursor=1,registered=0,missing=0,nextEggScan=0,memorialPlaced=false,bottlePlaced=false,staffHidden=false}
 local function ref(name)
  local r=discovery.byName[name]
  if not r then r={name=name,attempts=0,nextAt=0};discovery.byName[name]=r;discovery.refs[#discovery.refs+1]=r end
  return r
 end
 local function add(name,kind,radius,label,id,position,height)
  local t={kind=kind,radius=radius,label=label,id=id,position=position,height=height}
  if name then t.ref=ref(name) end
  targets[#targets+1]=t;return t
 end
 add('holy_tree3','tree',9,'古树 · 重新立誓')
 add('tripo_witch','witch',2.8,'女巫 · 调制')
 add('camp','camp',4,'篝火 · 烤蘑菇')
 discovery.eggTarget=add(nil,'egg',5,'龙魂之卵 · 供奉',nil,nil,5)
 for i=0,35 do add(i==0 and 'mush'or'mush_'..i,'mushroom',3.5,'采集蘑菇')end
 for i=0,8 do add('sheep_'..i,'wool',3,'取羊毛')end
 add(nil,'flower',9,'采集月见花',nil,V(150,40,62),6)
 add(nil,'bed',3,'重读序章',nil,V(127,80.5,193),2)
 add(nil,'lore',1.9,'翻阅手稿',1,V(115.4,73.3,177),3)
 add(nil,'lore',1.9,'翻阅手稿',2,V(115.4,73.3,181),3)
 add(nil,'lore',1.5,'读桌上的信',3,V(117.6,73.5,179),3)
 add('tripo_camp_stele','lore',3,'读石碑',4,V(64.7,43.5,65))
 for i=0,2 do local q=({{48,138},{58.4,156},{37.6,156}})[i+1]
  add('rune_'..i,'lore',3.6,'读柱上的铭文',5+i,V(q[1],52,q[2]),6)
 end
 add(nil,'lore',2.4,'读契碑',8,V(127,73.3,193.2),3)
 for _,name in ipairs({'altar3','witch_shop_v2','tripo_witch_staff','tripo_potion'})do ref(name)end
 for i=0,3 do ref('tripo_egg_stage_'..i)end
end
local function refreshDiscovery()
 initDiscovery()
 local now=U.Time.realtimeSinceStartup
 local refs=discovery.refs
 local queries=0
 for _=1,#refs do
  local r=refs[discovery.cursor];discovery.cursor=discovery.cursor%#refs+1
  if r.go and not objectAlive(r.go)then r.go=nil;r.nextAt=0 end
  if not r.go and now>=r.nextAt then
   r.attempts=r.attempts+1;r.nextAt=now+(r.attempts<3 and 2 or 10)
   r.go=U.GameObject.Find(r.name)
   queries=queries+1
   if queries>=8 then break end
  end
 end
 local function get(name)local r=discovery.byName[name];return r and r.go end
 local house,witch=get('witch_shop_v2'),get('tripo_witch')
 local staff,bottle=get('tripo_witch_staff'),get('tripo_potion')
 if staff and not discovery.staffHidden then staff:SetActive(false);discovery.staffHidden=true end
 if house and bottle and not discovery.bottlePlaced then bottle.transform.position=house.transform.position+V(1,.65,.5);discovery.bottlePlaced=true end
 if house and witch and not witchPlaced then witch.transform.position=house.transform.position+V(0,.15,0);witchPlaced=true end
 local eggAnchor=nil
 local allEggs=true
 for i=0,3 do
  local go=get('tripo_egg_stage_'..i)
  if go then eggAnchor=eggAnchor or go else allEggs=false end
 end
 -- Inactive egg stages are siblings of the live stage in the saved world.
 -- A local parent traversal (only until all four arrive) includes inactive siblings.
 if eggAnchor and not allEggs and now>=discovery.nextEggScan then
  discovery.nextEggScan=now+10
  local parent=eggAnchor.transform.parent
  if parent then
   local list=parent:GetComponentsInChildren(typeof(U.Transform),true)
   for i=0,list.Length-1 do local tr=list[i]
    local r=discovery.byName[tr.name]
    if r and string.match(tr.name,'^tripo_egg_stage_[0-3]$')then r.go=tr.gameObject end
   end
  end
 end
 local altar=get('altar3')
 if altar and not discovery.altarPosition then
  local p=altar.transform.position;local y=p.y+.4
  local hits=U.Physics.RaycastAll(V(p.x,p.y+20,p.z),V.down,25,-1,U.QueryTriggerInteraction.Ignore)
  for i=0,hits.Length-1 do local h=hits[i];if h.point.y>y and h.point.y<p.y+5 and h.normal.y>.6 then y=h.point.y end end
  discovery.altarPosition=V(p.x,y+.08,p.z)
 end
 local changedEggs=false
 for i=0,3 do local go=get('tripo_egg_stage_'..i)
  if go and (not eggs[i]or eggs[i].go~=go)then
   if discovery.altarPosition then go.transform.position=discovery.altarPosition end
   eggs[i]={go=go,scale=go.transform.localScale,placed=discovery.altarPosition~=nil};changedEggs=true
  elseif go and discovery.altarPosition and not eggs[i].placed then
   go.transform.position=discovery.altarPosition;eggs[i].placed=true
  end
 end
 if changedEggs then eggStage=-1 end
 discovery.eggTarget.position=discovery.altarPosition or (eggAnchor and eggAnchor.transform.position)
 local rune=get('rune_0')
 if rune and not discovery.memorialPlaced then
  local stone=U.Object.Instantiate(rune);stone.name='DragonPactMemorial'
  stone.transform.position=V(127,73.22,193.2);stone.transform.localScale=rune.transform.lossyScale*.55
  discovery.memorialPlaced=true
 end
 discovery.registered=0;discovery.missing=0
 for _,t in ipairs(targets)do
  if t.ref then t.go=t.ref.go end
  if t.go or t.position then discovery.registered=discovery.registered+1 else discovery.missing=discovery.missing+1 end
 end
end
''' +s[end:]
s=s.replace("actor=CS.DouyinActorService.GetLocalActor();if not actor or not buildUI()then return end\n if U.Time.time-lastScan>5 then lastScan=U.Time.time;if #targets==0 then discover()end end", "actor=CS.DouyinActorService.GetLocalActor();if not actor then return end\n buildUI() -- Native collection/witch/tree interactions do not wait for book atlases.\n if U.Time.realtimeSinceStartup-lastScan>=.25 then lastScan=U.Time.realtimeSinceStartup;refreshDiscovery()end")
s=s.replace('targets=#targets,potion=', 'targets=discovery and discovery.registered or 0,missingTargets=discovery and discovery.missing or 0,uiReady=uiReady,potion=')
s=s.replace('function OnApplicationFocus(focused)', "function OnEnable()if root and uiReady then root:SetActive(true)end;lastScan=-100 end\nfunction OnApplicationFocus(focused)")
# Reject out-of-range witch before doing line-of-sight raycasts.
s=s.replace("local p=t.go and t.go.transform.position or t.position\n if t.kind=='witch' and p then", "local p=t.go and t.go.transform.position or t.position\n if not p or math.abs(actor.position.y-p.y)>=(t.height or 4)or V.Distance(actor.position,p)>=t.radius then return false end\n if t.kind=='witch' then")
s=s.replace("return p and math.abs(actor.position.y-p.y)<(t.height or 4)and V.Distance(actor.position,p)<t.radius", "return true")
s=s.replace("local fx=getDependency('dragon_fx.lua');if fx then fx.Area('mage','skill1',actor.position+V(0,.5,0),1)end", "local fx=getDependency('dragon_fx.lua');if fx then pcall(function()fx.Area('mage','skill1',actor.position+V(0,.5,0),1)end)end")
s=s.replace("if not repeated then applyPotion(kind);nextPotionAt=U.Time.time+1 end\n  potionBusy=false", "potionBusy=false -- Callback errors must not permanently lock the native potion button.\n  if not repeated then\n   nextPotionAt=U.Time.time+1\n   local applied,why=pcall(applyPotion,kind)\n   if not applied then restorePotion();restoreBuff();toast('药水暂时未准备好，请稍后重试');print('[review-v27] potion: '..tostring(why))end\n  end")
p.write_text(s)
print('Wrote',OUT)

# Other scripts sharing the same runtime scope must not install a capped resolver.
# Keep cloning, animation, and combat rules byte-for-byte unchanged below the helper.
for name in ('dragon_rpg.lua','dragon_weapons.lua','dragon_outfits.lua','dragon_combat.lua','dragon_daycycle.lua'):
 text=(SOURCE/name).read_text()
 start=text.index('-- mobile-v23: resolve each dependency')
 marker=' ReleaseMobileDependencies=function()memo={};attempts={};nextAt={};failures={} end\nend\n'
 end=text.index(marker,start)+len(marker)
 owner='runtimeScope' if name in ('dragon_weapons.lua','dragon_outfits.lua') else 'scope'
 helper=resolver.replace('return scope:GetScript(name)','return '+owner+':GetScript(name)')
 tail=text[end:].replace(owner+':GetScript(', 'getDependency(')
 if name=='dragon_daycycle.lua':
  before="if not main then main=getDependency('dragon_world_bridge.lua');exploration=getDependency('dragon_exploration.lua')end"
  after="if not main then main=getDependency('dragon_world_bridge.lua')end\n if not exploration then exploration=getDependency('dragon_exploration.lua')end"
  assert before in tail
  tail=tail.replace(before,after)
 (OUT/name).write_text(text[:start]+helper+tail)

# Lifecycle cleanup: a hidden root does not clear activeSelf on its modal children.
p=OUT/'dragon_exploration.lua';s=p.read_text()
old="function OnDisable()queuedNative=nil;contractSession=nil;mode=nil;clearNativeInteraction();restorePotion();restoreBuff();callback=nil;if root then root:SetActive(false)end;if main then main.SetExplorationMenu(false)end end"
new="""function OnDisable()
 -- Invalidate the completion token before closing the RPG-owned class page.
 local ownedContract=contractSession~=nil or mode=='class'
 queuedNative=nil;contractSession=nil;callback=nil;mode=nil;current=nil
 if ownedContract and contractRpg and contractRpg.CancelContract then pcall(contractRpg.CancelContract)end
 clearNativeInteraction();restorePotion();restoreBuff()
 if dim then dim:SetActive(false)end
 if book then book.go:SetActive(false)end
 if roast then roast.go:SetActive(false)end
 if reader then reader.go:SetActive(false)end
 if buffHud then buffHud.go:SetActive(false)end
 if root then root:SetActive(false)end
 if main then main.SetExplorationMenu(false)end
 if ownedContract and actor then actor:Immobilize(false)end
end"""
assert old in s;s=s.replace(old,new);p.write_text(s)

p=OUT/'dragon_rpg.lua';s=p.read_text()
old='function IsContractOpen()return contract~=nil and contract.activeInHierarchy end'
new="""function IsContractOpen()return contract~=nil and contract.activeInHierarchy end
function CancelContract()
 -- Cancellation is not signing: discard the continuation rather than invoke it.
 local wasOpen=contract and contract.activeSelf
 contractCallback=nil;selection=nil;signPending=false
 if contract then contract:SetActive(false)end
 if backdrop then backdrop:SetActive(false)end
 if context then context.menu=false end
 if wasOpen then ready=profile~=nil and profile.class~=nil end
 if wasOpen and actor then actor:Immobilize(false)end
 return wasOpen==true
end"""
assert old in s;s=s.replace(old,new)
s=s.replace('function OnDisable()\n if nativeTrial', 'function OnDisable()\n CancelContract()\n if nativeTrial')
p.write_text(s)

# Reapply tested responsive controls and lore binding follow-up after rebuilding v27 base.
import subprocess
subprocess.run(['patch','--batch','-p0','-i',str(OUT/'followup-ui-lore.patch')],cwd=OUT,check=True)
