---@id e79a8125-027b-4798-aad1-11f54f74364e
---@sourceScriptId b7f50548-eed8-4fc5-ad43-18b78409376e
---@referenceName dragon_exploration.lua
---@displayName 龙眠探索主线
local U=CS.UnityEngine
local V=U.Vector3
local V2=U.Vector2
local scope=require('official.core.runtime_scope').from(self)
-- mobile-v23: resolve each dependency at most once a second, at most 30 attempts.
do
 local target=scope
 local original=target.GetScript
 local memo,attempts,nextAt={},{},{}
 local failures={}
 target.GetScript=function(_,name)
  if memo[name] then return memo[name] end
  local now=CS.UnityEngine.Time.realtimeSinceStartup
  if (attempts[name] or 0)>=30 or now<(nextAt[name] or 0) then return nil end
  attempts[name]=(attempts[name] or 0)+1;nextAt[name]=now+1
  local ok,value=pcall(original,target,name)
  if ok and value then memo[name]=value;return value end
  if attempts[name]==30 then failures[name]=tostring(value or 'not loaded');print('[mobile-v23] dependency failed: '..name..' '..failures[name]) end
  return nil
 end
 function GetDependencyDiagnostics() return {build='mobile-v23',attempts=attempts,failures=failures} end
 local destroy=OnDestroy
 -- Installed after lifecycle definitions below; clears references on scene exit.
 ReleaseMobileDependencies=function()memo={};attempts={};nextAt={};failures={} end
end

local progress,rules,cycle,main,actor
local K=nil
local root,dim,book,content,roast,reader
local mode=nil
local targets={}
local current=nil
local hatchStart=nil
local potion=nil
local buff=nil
local callback=nil
local pendingClass=nil
local lastScan=-100
local lastPosition=nil
local eggs={}
local eggStage=-1
local firstReady=false
local nativeExplore,nativeTarget,nativePotion
local potionBusy=false
local nextPotionAt=0
local lastNativeClick=-10
local contractSession=nil
local contractRpg=nil
local queuedNative=nil
local function clearNativeInteraction()
 if nativeExplore then self:RemoveInteractorButton(nativeExplore);nativeExplore=nil end
 if nativePotion then self:RemoveInteractorButton(nativePotion);nativePotion=nil end
 nativeTarget=nil
end
local witchPlaced=false
local altarPlaced=false
local R={}                 -- 烤蘑菇面板的状态
local lore={got={},n=0}
local buffHud=nil
local LORE_TOTAL=8
local function toast(s)CS.DouyinUtility.Toast(s or '')end
local function battleScript()return scope:GetScript('dragon_combat.lua')end

function IsBattleActive()local b=battleScript();return b and b.IsParticipating()or false end
function GetLoreCount()return lore.n end
local function mounted()return actor and(actor:IsSitting()or actor:IsFlying()or(main and main.IsMounted()))end
local function unavailable()return not actor or mounted()or IsBattleActive()end

local function clearContent()
 if content then U.Object.Destroy(content)end
 local go,rt=K.node(book.rt,'PageControls',false);rt.sizeDelta=V2(10,10);content=go
 return rt
end
function Close()
 if mode=='class'and callback then return end
 if dim then dim:SetActive(false)end
 if book then book.go:SetActive(false)end
 if roast then roast.go:SetActive(false)end
 if reader then reader.go:SetActive(false)end
 if mode then K.play('close')end
 mode=nil
 if main then main.SetExplorationMenu(false)end
end
local function open(kind)
 if unavailable()then toast('请先结束战斗或骑乘');return false end
 mode=kind;dim:SetActive(true)
 book.go:SetActive(kind=='tasks');roast.go:SetActive(kind=='cook');reader.go:SetActive(kind=='lore')
 if main then main.SetExplorationMenu(true)end
 return true
end
local function submit(kind,args,fn)
 local ok,why=progress.Submit(kind,args,function(success,msg,repeated)
  toast(msg);if success and fn then fn(repeated)end
 end)
 if not ok then toast(why)end;return ok,why
end
local function nearby(t)
 if not actor or not t then return false end
 local p=t.go and t.go.transform.position or t.position
 if t.kind=='witch' and p then
  local hits=U.Physics.RaycastAll(actor.position+V(0,1,0),(p+V(0,1,0))-(actor.position+V(0,1,0)),V.Distance(actor.position,p),-1,U.QueryTriggerInteraction.Ignore)
  for i=0,hits.Length-1 do local tr=hits[i].transform
   while tr do if tr.name=='witch_shop_v2' then return false end;tr=tr.parent end
  end
 end
 return p and math.abs(actor.position.y-p.y)<(t.height or 4)and V.Distance(actor.position,p)<t.radius
end

---------------------------------------------------------------- 药水与蘑菇的临时效果
local function restoreBuff()
 if not buff then return end
 if actor then actor.speed=buff.speed end
 buff=nil
end
local function restorePotion()
 if not potion then return end
 if actor then actor.speed=potion.speed;actor.scale=potion.scale end
 if potion.light then U.Object.Destroy(potion.light)end
 if potion.sheep then U.Object.Destroy(potion.sheep);if actor then actor:SetVisible(true)end end
 if potion.hidden then for _,entry in ipairs(potion.hidden)do if entry.r then entry.r.enabled=entry.enabled end end end
 potion=nil
end
-- 熟蘑菇：二十秒脚步轻快；生蘑菇：十秒天旋地转、脚步发飘
local function applyBuff(kind)
 restoreBuff();restorePotion()
 if not actor then return end
 buff={kind=kind,untilTime=U.Time.time+(kind=='speed'and 20 or 10),speed=actor.speed}
 if kind=='speed'then
  actor.speed=buff.speed*1.7
  local fx=scope:GetScript('dragon_fx.lua');if fx then pcall(function()fx.Area('ranged','skill1',actor.position+V(0,.4,0),1)end)end
 else
  actor.speed=buff.speed*.7
  if main then main.SetDizzy(10)end
 end
end
local function applyPotion(kind)
 restorePotion();restoreBuff();if unavailable()then return end
 potion={kind=kind,untilTime=U.Time.time+10,speed=actor.speed,scale=actor.scale}
 local fx=scope:GetScript('dragon_fx.lua');if fx then fx.Area('mage','skill1',actor.position+V(0,.5,0),1)end
 if kind=='wind'then actor.speed=potion.speed*1.8
 elseif kind=='grow'then actor.scale=potion.scale*3.5
 elseif kind=='shrink'then actor.scale=math.max(.3,potion.scale*.6)
 elseif kind=='sheep'then
  local source=U.GameObject.Find('sheep_0')
  if source then
   -- Clone the complete hierarchy so skinned renderers keep their cloned bones.
   local clone=U.Object.Instantiate(source);clone.name='PotionSheepAppearance';clone:SetActive(true)
   local behaviors=clone:GetComponentsInChildren(typeof(CS.DouyinScript),true);for i=0,behaviors.Length-1 do behaviors[i].enabled=false end
   clone.transform:SetParent(nil,true);clone.transform.position=actor.position
   local colliders=clone:GetComponentsInChildren(typeof(U.Collider),true);for i=0,colliders.Length-1 do colliders[i].enabled=false end
   local bodies=clone:GetComponentsInChildren(typeof(U.Rigidbody),true);for i=0,bodies.Length-1 do bodies[i].isKinematic=true;bodies[i].useGravity=false end
   local renderers=clone:GetComponentsInChildren(typeof(U.Renderer),true)
   if renderers.Length>0 then
    for i=0,renderers.Length-1 do renderers[i].enabled=true end
    potion.sheep=clone;potion.sheepRotation=U.Quaternion.Euler(0,180,0);potion.hidden={}
    local original=actor.gameObject:GetComponentsInChildren(typeof(U.Renderer),true)
    for i=0,original.Length-1 do local r=original[i];potion.hidden[#potion.hidden+1]={r=r,enabled=r.enabled};r.enabled=false end
   else U.Object.Destroy(clone);toast('变身暂时未准备好');restorePotion();return end
  else toast('变身暂时未准备好');restorePotion();return end
 elseif kind=='glow'then
  local go=U.GameObject('PotionFirefly');local light=go:AddComponent(typeof(U.Light));light.type=U.LightType.Point;light.color=U.Color(.6,1,.24,1);light.range=3;light.intensity=1.5;light.shadows=U.LightShadows.None;potion.light=go
 end
end
function ClearPotion()restorePotion();restoreBuff()end
function OpenContract(respec,continuation)
 -- Stable dependency: do not rescan the whole resource after every UI close.
 if not contractRpg then contractRpg=scope:GetScript('dragon_rpg.lua')end
 local rpg=contractRpg
 -- Reconcile the owner with the actual shared page, including interrupted closes.
 if rpg and rpg.IsContractOpen and not rpg.IsContractOpen()then
  contractSession=nil
  if mode=='class'then mode=nil end
 end
 if mode or contractSession or unavailable()or not rpg then return false,'gate: mode='..tostring(mode)..' session='..tostring(contractSession~=nil)..' unavailable='..tostring(unavailable())..' rpg='..tostring(rpg~=nil) end
 -- A contract owns the interaction until it closes. Recreate the native
 -- entry afterwards instead of retaining the button used to open it.
 local session={}
 contractSession=session;mode='class'
 clearNativeInteraction()
 if main then main.SetExplorationMenu(true)end
 local function finish()
  if contractSession~=session then return end
  contractSession=nil;mode=nil
  clearNativeInteraction()
  if main then main.SetExplorationMenu(false)end
  if actor then actor:Immobilize(false)end
 end
 local ok,opened=pcall(function()
  return rpg.OpenContract(respec,function()
   if contractSession~=session then return end
   finish()
   if continuation then continuation()end
  end)
 end)
 if not ok or not opened then
  finish()
  if not ok then toast('誓约之书暂时未能打开，请重试')end
  return false,'open: '..tostring(ok)..' '..tostring(opened)
 end
 return true
end

---------------------------------------------------------------- 誓约之书（主线任务面板）
function OpenTasks()
 if not root or mode then return end
 local p=progress.GetProfile();if not p then return end
 if not open('tasks')then return end
 local rt=clearContent()
 local bw=book.w
 local lx,rx=-.2207*bw,.2207*bw
 local idx=rules.ObjectiveIndex(p);local steps=rules.Steps(p)
 K.img(rt,'q_title',nil,nil,lx,292)
 local o=K.img(rt,'q_obj_'..idx,nil,nil,lx,128);o.rt.pivot=V2(.5,.5)
 for i=1,6 do
  local y=-22-(i-1)*48
  local s=K.img(rt,'q_step_'..i,nil,nil,0,0);s.rt.pivot=V2(0,.5);s.rt.anchoredPosition=V2(lx-170,y)
  if steps[i]then K.img(rt,'q_check',36,nil,lx-200,y+2);s.ri.color=U.Color(1,1,1,.55)
  elseif (i==idx-1)or(idx==7 and i==6)or(idx==1 and i==1)then K.img(rt,'q_now',nil,nil,lx-200,y)end
 end
 K.img(rt,'q_offer',nil,nil,rx,300)
 local rows={{'moon',p.deposited.moon,30},{'ember',p.deposited.ember,3},{'dew',p.deposited.stardew,1}}
 for i,v in ipairs(rows)do
  local y=228-(i-1)*72
  K.img(rt,'it_'..v[1],52,52,rx-215,y)
  local nm=K.img(rt,'nm_it_'..v[1],nil,nil,0,0);nm.rt.pivot=V2(0,.5);nm.rt.anchoredPosition=V2(rx-180,y)
  local bg=K.img(rt,'bar_bg',210,16,rx+20,y-2)
  local w=210*math.max(0,math.min(1,v[2]/v[3]))
  if w>2 then local f=K.img(rt,'bar_fill',w,16,rx+20-105+w/2,y-2)end
  local n=K.num(rt,'i',.9,rx+240,y,1);n.set(v[2]..'/'..v[3])
 end
 K.img(rt,'q_bag',nil,nil,rx,-2)
 local bag={{'mush',p.mushroom},{'flower',p.flower},{'wool',p.wool},{'moon',p.moon},{'ember',p.ember},{'dew',p.stardew}}
 for i,v in ipairs(bag)do
  local col,row=(i-1)%3,math.floor((i-1)/3)
  local x,y=rx-185+col*178,-72-row*84
  K.img(rt,'it_'..v[1],48,48,x-30,y)
  local nm=K.img(rt,'nm_it_'..v[1],nil,nil,0,0);nm.rt.pivot=V2(0,.5);nm.rt.anchoredPosition=V2(x-2,y+16);nm.rt.localScale=V(.8,.8,1)
  local n=K.num(rt,'i',.72,x+2,y-16,-1);n.set(tostring(math.min(v[2],99999)))
 end
 local lh=K.img(rt,'q_lorehead',nil,nil,rx-60,-262)
 local ln=K.num(rt,'i',.9,rx+120,-262,0);ln.set(lore.n..'/'..LORE_TOTAL)
 K.img(rt,'q_hint',nil,nil,rx,-312)
end

---------------------------------------------------------------- 篝火烤蘑菇：蘑菇串来回晃，晃进金色火区时按「出锅」
local function roastReset()
 R.zoneX=-230+math.random()*460
 R.zoneW=150-math.min(60,(R.streak or 0)*14)
 R.zone.rt.sizeDelta=V2(R.zoneW,60);R.zone.rt.anchoredPosition=V2(R.zoneX,0)
 R.speed=(560+math.random()*140+math.min(260,(R.streak or 0)*60))*.50
 R.phase=math.random()*4;R.locked=nil
 R.result.go:SetActive(false)
end
local function roastPress()
 if mode~='cook'or R.locked then return end
 if not current or current.kind~='camp'or not nearby(current)then toast('离篝火太远了');Close();return end
 local hit=math.abs(R.x-R.zoneX)<=R.zoneW*.5
 local ok=submit('roast',{hit=hit},function()
  R.locked=U.Time.unscaledTime
  K.set(R.result,hit and 'roast_ok'or 'roast_bad',1);R.result.go:SetActive(true)
  K.play(hit and 'card'or 'stamp')
  if hit then R.streak=(R.streak or 0)+1 else R.streak=0 end
  applyBuff(hit and 'speed'or 'dizzy')
 end)
 if not ok then R.locked=nil end
end
local function cook()
 if not open('cook')then return end
 R.streak=0;roastReset()
end
local function updateRoast()
 if mode~='cook'then return end
 local t=U.Time.unscaledTime
 if R.locked then
  -- 出锅后停一下给结果，再换一串
  local a=t-R.locked
  local s=1+.25*math.max(0,1-a*4)
  R.result.rt.localScale=V(s,s,1)
  if a>1.3 then roastReset()end
  return
 end
 R.phase=R.phase+U.Time.unscaledDeltaTime*R.speed/340
 -- 三角波来回，两头稍微停顿
 local u=R.phase%2;if u>1 then u=2-u end
 u=u*u*(3-2*u)
 R.x=-340+680*u
 R.cursor.rt.anchoredPosition=V2(R.x,70+math.sin(t*9)*3)
 local inZone=math.abs(R.x-R.zoneX)<=R.zoneW*.5
 R.zone.ri.color=inZone and U.Color(1,1,1,1)or U.Color(1,1,1,.8)
 local pulse=1+.04*math.sin(t*6)
 R.btn.rt.localScale=V(pulse,pulse,1)
 if U.Input.GetKeyDown('space')then roastPress()end
end

---------------------------------------------------------------- 手稿与碑文
local function readLore(id)
 if not open('lore')then return end
 local L=K.L.lore;local t=K.tex.lore
 local col,row=(id-1)%L.cols,math.floor((id-1)/L.cols)
 reader.text.ri.uvRect=U.Rect(col*L.w/t.width,1-(row+1)*L.h/t.height,L.w/t.width,L.h/t.height)
 K.play('open')
 if not lore.got[id]then
  lore.got[id]=true;lore.n=lore.n+1
  if main then main.ShowNote('lore',nil,lore.n,LORE_TOTAL)end
 end
end

local function witch()
 if unavailable()or not current or current.kind~='witch'or not nearby(current)then return end
 submit('stardew',{})
end
local function drinkMystery()
 if potionBusy or U.Time.time<nextPotionAt or unavailable()or not current or current.kind~='witch'or not nearby(current)then return end
 potionBusy=true
 local kind=({'grow','shrink','sheep'})[math.random(1,3)]
 local ok=submit('brew',{potion=kind},function(repeated)
  if not repeated then applyPotion(kind);nextPotionAt=U.Time.time+1 end
  potionBusy=false
 end)
 if not ok then potionBusy=false end
end
local function beginHatch()
 if hatchStart then return end;hatchStart=U.Time.time
 toast('月辉、火种与星露渗进了蛋壳……')
end
local function interact()
 if unavailable()or not current or not nearby(current)then return end
 local kind=current.kind
 if kind=='tree'then OpenContract(true,nil)
 elseif kind=='witch'then witch()
 elseif kind=='camp'then cook()
 elseif kind=='lore'then readLore(current.id)
 elseif kind=='egg'then local p=progress.GetProfile()
  if p.pact then toast('龙魂已经归位。点左侧的龙印，唤墨曜降临')
  elseif p.hatchReady then beginHatch()
  else submit('deposit',{},function()if progress.GetProfile().hatchReady and not progress.GetProfile().pact then beginHatch()end end)end
 elseif kind=='bed'then if main then main.ReplayPrologue()end
 else submit('gather',{material=kind,isDay=cycle.IsDay()})end
end
local function buildUI()
 if root then return true end
 K=main.GetKit();if not K then return false end
 root=U.GameObject('DragonExplorationControls');local canvas=root:AddComponent(typeof(U.Canvas));canvas.renderMode=U.RenderMode.ScreenSpaceOverlay;canvas.sortingOrder=930
 local scaler=root:AddComponent(typeof(U.UI.CanvasScaler));scaler.uiScaleMode=U.UI.CanvasScaler.ScaleMode.ScaleWithScreenSize;scaler.referenceResolution=V2(1920,1080);scaler.matchWidthOrHeight=1;root:AddComponent(typeof(U.UI.GraphicRaycaster))
 -- 压暗的底，同时挡住下面的摇杆
 local dgo,drt=K.node(root.transform,'Dim',true);local dimg=dgo:AddComponent(typeof(U.UI.Image));dimg.color=U.Color(.02,.015,.03,.72);dim=dgo
 local dbtn=dgo:AddComponent(typeof(U.UI.Button));dbtn.targetGraphic=dimg;dbtn.transition=U.UI.Selectable.Transition.None
 dbtn.onClick:AddListener(function()if mode=='lore'then Close()end end)
 dim:SetActive(false)
 -- 誓约之书：用世界里那本古书
 local bh=860;local bw=bh*K.bookAspect
 book=K.raw(root.transform,K.bookTex,nil,bw,bh,0,6);book.w=bw;book.go.name='QuestBook';book.ri.raycastTarget=true
 K.button(book.rt,'btn_x',100,bw/2-36,bh/2-44,Close)
 book.go:SetActive(false)
 -- 烤蘑菇
 roast=K.img(root.transform,'roast_bg',nil,nil,0,0);roast.go.name='CampfirePanel';roast.ri.raycastTarget=true
 K.img(roast.rt,'roast_title',nil,nil,0,168)
 K.img(roast.rt,'roast_hint',nil,nil,0,-52)
 K.img(roast.rt,'roast_hint2',nil,nil,0,-90)
 R.bar=K.img(roast.rt,'roast_bar',nil,nil,0,22)
 R.zone=K.img(R.bar.rt,'roast_zone',150,60,0,0)
 R.cursor=K.img(roast.rt,'roast_cursor',72,nil,0,70)
 R.btn=K.button(roast.rt,'roast_btn',150,330,-150,roastPress);R.btn.go.name='RoastServe'
 R.result=K.img(roast.rt,'roast_ok',nil,nil,-60,-158)
 K.button(roast.rt,'btn_x',92,412,196,Close)
 R.x=0;R.zoneX=0;R.zoneW=150
 roast.go:SetActive(false)
 -- 手稿 / 碑文
 reader=K.img(root.transform,'lore_bg',700,nil,0,10);reader.go.name='LoreReader'
 reader.text=K.raw(reader.rt,K.tex.lore,nil,700*560/640,700*560/640*720/560,0,0)
 local hint=K.img(reader.rt,'hint_read',nil,nil,0,-reader.h/2-30)
 reader.go:SetActive(false)
 -- 蘑菇效果的小提示（屏幕下方正中）
 local bgo,brt=K.node(root.transform,'BuffStatus',false);brt.anchorMin=V2(.5,0);brt.anchorMax=V2(.5,0);brt.anchoredPosition=V2(0,210)
 buffHud={go=bgo,label=K.img(brt,'buff_speed',nil,nil,-30,0)};buffHud.num=K.num(brt,'w',.9,70,0,0);bgo:SetActive(false)
 return true
end
local function discover()
 targets={}
 if not altarPlaced then
  local altar=U.GameObject.Find('altar3')
  if altar then
   local p=altar.transform.position;local y=p.y+.4
   local hits=U.Physics.RaycastAll(V(p.x,p.y+20,p.z),V.down,25,-1,U.QueryTriggerInteraction.Ignore)
   for i=0,hits.Length-1 do local h=hits[i];if h.point.y>y and h.point.y<p.y+5 and h.normal.y>.6 then y=h.point.y end end
   local all=U.Resources.FindObjectsOfTypeAll(typeof(U.Transform))
   for i=0,all.Length-1 do local t=all[i];if string.match(t.name,'^tripo_egg_stage_[0-3]$')and t.gameObject.scene:IsValid()then t.position=V(p.x,y+.08,p.z)end end
   local rune=U.GameObject.Find('rune_0');if rune then local stone=U.Object.Instantiate(rune);stone.name='DragonPactMemorial';stone.transform.position=V(127,73.22,193.2);stone.transform.localScale=rune.transform.lossyScale*.55 end
   altarPlaced=true
  end
 end
 if not witchPlaced then
  local house=U.GameObject.Find('witch_shop_v2');local witch=U.GameObject.Find('tripo_witch')
  local staff=U.GameObject.Find('tripo_witch_staff');if staff then staff:SetActive(false)end
  local bottle=U.GameObject.Find('tripo_potion');if house and bottle then bottle.transform.position=house.transform.position+V(1,.65,.5)end
  if house and witch then witch.transform.position=house.transform.position+V(0,.15,0);witchPlaced=true end
 end
 local function add(name,kind,radius,caption,id)
  local go=U.GameObject.Find(name);if go then targets[#targets+1]={go=go,kind=kind,radius=radius,label=caption,id=id}end
  return go~=nil
 end
 add('holy_tree3','tree',9,'古树 · 重新立誓');add('tripo_witch','witch',2.8,'女巫 · 调制');add('camp','camp',4,'篝火 · 烤蘑菇')
 local egg=U.GameObject.Find('tripo_egg_stage_0');if egg then targets[#targets+1]={position=egg.transform.position,kind='egg',radius=5,height=5,label='龙魂之卵 · 供奉'}end
 for i=0,35 do add(i==0 and 'mush'or 'mush_'..i,'mushroom',3.5,'采集蘑菇')end
 for i=0,8 do add('sheep_'..i,'wool',3,'取羊毛')end
 -- Flowers are terrain decoration; one bounded collection patch avoids per-blade scripts.
 targets[#targets+1]={position=V(150,40,62),kind='flower',radius=9,height=6,label='采集月见花'}
 targets[#targets+1]={position=V(127,80.5,193),kind='bed',radius=3,height=2,label='重读序章'}
 -- 手稿与碑文：书库三处、营地石碑、祭坛三柱、圣所契碑
 targets[#targets+1]={position=V(115.4,73.3,177),kind='lore',id=1,radius=1.9,height=3,label='翻阅手稿'}
 targets[#targets+1]={position=V(115.4,73.3,181),kind='lore',id=2,radius=1.9,height=3,label='翻阅手稿'}
 targets[#targets+1]={position=V(117.6,73.5,179),kind='lore',id=3,radius=1.5,height=3,label='读桌上的信'}
 if not add('tripo_camp_stele','lore',3,'读石碑',4)then targets[#targets+1]={position=V(64.7,43.5,65),kind='lore',id=4,radius=3,label='读石碑'}end
 for i=0,2 do
  if not add('rune_'..i,'lore',3.6,'读柱上的铭文',5+i)then local q=({{48,138},{58.4,156},{37.6,156}})[i+1];targets[#targets+1]={position=V(q[1],52,q[2]),kind='lore',id=5+i,radius=3.6,height=6,label='读柱上的铭文'}end
 end
 targets[#targets+1]={position=V(127,73.3,193.2),kind='lore',id=8,radius=2.4,height=3,label='读契碑'}
 local all=U.Resources.FindObjectsOfTypeAll(typeof(U.Transform))
 for j=0,all.Length-1 do local t=all[j];local i=tonumber(string.match(t.name,'^tripo_egg_stage_(%d)$'))
  if i and i<=3 and t.gameObject.scene.IsValid and t.gameObject.scene:IsValid()then eggs[i]={go=t.gameObject,scale=t.localScale}end
 end
end
local function handleNativeClick(index)
 if not nativeExplore or not nativeTarget or nativeTarget~=current then return end
 local now=U.Time.unscaledTime
 if now-lastNativeClick<.25 then return end
 lastNativeClick=now
 if index==1 then interact()elseif index==2 and nativePotion then drinkMystery()end
end
local function queueNativeClick(index)
 -- Keep the native button alive until the engine has completed click dispatch.
 if queuedNative or not nativeTarget or nativeTarget~=current then return end
 queuedNative={index=index,target=nativeTarget,frame=U.Time.frameCount}
end
function OnInteractorButtonClick(index)queueNativeClick(index)end

function GetStatus()return{loaded=progress and progress.IsLoaded(),mode=mode,target=current and current.kind,targets=#targets,potion=potion and potion.kind,buff=buff and buff.kind,eggStage=eggStage,lore=lore.n,bridge=main~=nil,roastX=R.x,roastZone=R.zoneX,roastW=R.zoneW}end
function DebugOpen(kind,id)if kind=='cook'then cook()elseif kind=='lore'then readLore(id or 1)elseif kind=='tasks'then OpenTasks()elseif kind=='serve'then roastPress()elseif kind=='buff'then applyBuff(id)end end
function Update()
 if not progress then progress=scope:GetScript('dragon_progress.lua');rules=scope:GetScript('dragon_progress_rules.lua');cycle=scope:GetScript('dragon_daycycle.lua');main=scope:GetScript('dragon_world_bridge.lua')end
 if not progress or not rules or not cycle or not main then progress=nil;return end
 if not R.registered then R.registered=true;main.RegisterScript('explore',{OpenTasks=OpenTasks,IsBattleActive=IsBattleActive,GetLoreCount=GetLoreCount})end
 actor=CS.DouyinActorService.GetLocalActor();if not actor or not buildUI()then return end
 if U.Time.time-lastScan>5 then lastScan=U.Time.time;if #targets==0 then discover()end end
 local p=progress.GetProfile()
 if not p then return end
 if queuedNative and U.Time.frameCount>queuedNative.frame then
  local click=queuedNative;queuedNative=nil
  if click.target==nativeTarget and click.target==current then handleNativeClick(click.index)end
 end
 local world=main.GetExplorationState();local available=world=='play'and not unavailable()
 current=nil;local best=1e9
 for _,t in ipairs(targets)do if nearby(t)then local pos=t.go and t.go.transform.position or t.position;local d=V.Distance(actor.position,pos);if d<best then current=t;best=d end end end
 local wanted=available and not mode and current or nil
 if wanted~=nativeTarget then
  clearNativeInteraction()
  nativeTarget=wanted
  if wanted then
   nativeExplore=self:AddInteractorButton();nativeExplore.onClick:AddListener(function()queueNativeClick(1)end)
   if wanted.kind=='witch'then nativePotion=self:AddInteractorButton();nativePotion.onClick:AddListener(function()queueNativeClick(2)end) end
  end
 end
 if nativeExplore and wanted then local label=nativeExplore:GetComponentInChildren(typeof(U.UI.Text),true);if label then label.text=wanted.kind=='witch'and '调制星露'or wanted.label end end
 if nativePotion then local label=nativePotion:GetComponentInChildren(typeof(U.UI.Text),true);if label then label.text='饮用神秘药水'end end
 if pendingClass then main.ApplySavedClass(pendingClass);pendingClass=nil end
 if not firstReady then firstReady=true;main.ApplySavedClass(p.class)end
 local stage=rules.EggStage(p)
 if stage~=eggStage then for i,e in pairs(eggs)do e.go:SetActive(i==stage)end;eggStage=stage end
 if hatchStart then
  -- 蛋抖三秒，然后龙魂离壳
  local age=U.Time.time-hatchStart;local e=eggs[2];if e then e.go.transform.localScale=e.scale*(1+.03*math.sin(age*14)*math.min(1,age))end
  if age>3 and not progress.GetStatus().pending then
   if e then e.go.transform.localScale=e.scale end
   hatchStart=nil
   submit('hatch',{},function()if main then main.DragonAwaken()end end)
  end
 end
 updateRoast()
 if buff then
  if U.Time.time>=buff.untilTime or mounted()then restoreBuff()end
 end
 if buffHud then
  buffHud.go:SetActive(buff~=nil and not mode)
  if buff then
   if buffHud.kind~=buff.kind then buffHud.kind=buff.kind;K.set(buffHud.label,buff.kind=='speed'and 'buff_speed'or 'buff_dizzy',1)end
   buffHud.num.set(tostring(math.max(0,math.ceil(buff.untilTime-U.Time.time))))
  end
 end
 if potion then
  local moved=lastPosition and V.Distance(actor.position,lastPosition)>8
  if U.Time.time>=potion.untilTime or unavailable()or moved then restorePotion()
  elseif potion.sheep then
   for _,entry in ipairs(potion.hidden)do if entry.r then entry.r.enabled=false end end
   potion.sheep.transform.position=actor.position;potion.sheep.transform.rotation=actor.rotation*potion.sheepRotation
 elseif potion.light then potion.light.transform.position=actor.position+V(math.sin(U.Time.time*2)*.6,1.2,math.cos(U.Time.time*2)*.6)end
 end
 lastPosition=actor.position
 if mode and unavailable()then callback=nil;hatchStart=nil;Close()end
end
function OnApplicationFocus(focused)if not focused then restorePotion()end end
function OnDisable()queuedNative=nil;contractSession=nil;mode=nil;clearNativeInteraction();restorePotion();restoreBuff();callback=nil;if root then root:SetActive(false)end;if main then main.SetExplorationMenu(false)end end
function OnDestroy()OnDisable();if root then U.Object.Destroy(root)end end

do local previous=OnDestroy;function OnDestroy()if previous then previous()end;ReleaseMobileDependencies()end end
