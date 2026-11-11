---@id 155ddca2-0f15-4648-a2c3-1b64028fc9a6
---@sourceScriptId b7f50548-eed8-4fc5-ad43-18b78409376e
---@referenceName dragon_exploration.lua
---@displayName 龙眠探索主线
local U=CS.UnityEngine
local V=U.Vector3
local V2=U.Vector2
local scope=require('official.core.runtime_scope').from(self)
local progress,rules,cycle,main,actor
local root,panel,title,body,notice,nearButton,nearLabel,taskButton,font,content,bar,marker
local mode=nil
local selected={}
local targets={}
local current=nil
local cooking=nil
local hatchStart=nil
local potion=nil
local callback=nil
local pendingClass=nil
local lastScan=-100
local lastPosition=nil
local sprites={}
local resources={}
local eggs={}
local eggStage=-1
local firstReady=false
local nativeExplore,nativeTarget
local witchPlaced=false
local ink=U.Color(.20,.14,.09,1)
local labels={mushroom='蘑菇',flower='月见花',wool='羊毛',charred='焦蘑菇',wind='疾风',grow='变大',shrink='变小',glow='萤火',sheep='变羊'}
local function toast(s)CS.DouyinUtility.Toast(s or '')end
local function battleScript()return scope:GetScript('dragon_combat.lua')end

function IsBattleActive()local b=battleScript();return b and b.IsActive()or false end
local function mounted()return actor and(actor:IsSitting()or actor:IsFlying()or(main and main.IsMounted()))end
local function unavailable()return not actor or mounted()or IsBattleActive()end
local function rect(parent,name,w,h,x,y,anchor)
 local go=U.GameObject(name);go.transform:SetParent(parent,false);local rt=go:AddComponent(typeof(U.RectTransform));rt.anchorMin=anchor or V2(.5,.5);rt.anchorMax=rt.anchorMin;rt.sizeDelta=V2(w,h);rt.anchoredPosition=V2(x,y);return go
end
local function text(parent,name,value,size,w,h,x,y,color)
 local go=rect(parent,name,w,h,x,y);local t=go:AddComponent(typeof(U.UI.Text));t.font=font;t.fontSize=size;t.text=value;t.color=color or ink;t.alignment=U.TextAnchor.MiddleCenter;t.raycastTarget=false;return t
end
local shapes={book={{8,12,30,16},{30,16,54,12},{54,12,54,49},{54,49,32,54},{32,54,8,49},{8,49,8,12},{32,17,32,54},{13,23,25,26},{13,31,25,34},{39,25,49,22},{39,34,49,31}},leaf={{12,51,25,27},{25,27,53,10},{53,10,47,41},{47,41,31,50},{31,50,12,51},{22,40,40,25}},potion={{25,7,39,7},{25,7,25,23},{39,7,39,23},{25,23,14,40},{14,40,17,53},{17,53,47,53},{47,53,50,40},{50,40,39,23},{19,38,45,38}},star={{32,5,38,25},{38,25,57,32},{57,32,38,39},{38,39,32,59},{32,59,25,39},{25,39,7,32},{7,32,25,25},{25,25,32,5}}}
local function icon(key)
 if sprites[key]then return sprites[key]end
 local t=U.Texture2D(64,64,U.TextureFormat.RGBA32,false);t.filterMode=U.FilterMode.Bilinear
 for y=0,63 do for x=0,63 do local a=0
  for _,l in ipairs(shapes[key]or shapes.star)do local dx,dy=l[3]-l[1],l[4]-l[2];local k=math.max(0,math.min(1,((x-l[1])*dx+(y-l[2])*dy)/(dx*dx+dy*dy)));local d=math.sqrt((x-l[1]-dx*k)^2+(y-l[2]-dy*k)^2);a=math.max(a,math.max(0,math.min(1,2.3-d)))end
  t:SetPixel(x,63-y,U.Color(1,1,1,a))
 end end;t:Apply();local s=U.Sprite.Create(t,U.Rect(0,0,64,64),V2(.5,.5),100);sprites[key]=s;resources[#resources+1]=s;resources[#resources+1]=t;return s
end
local function button(parent,name,value,x,y,w,h,fn)
 local go=rect(parent,name,w,h,x,y);local im=go:AddComponent(typeof(U.UI.Image));im.color=U.Color(.45,.28,.12,.025)
 local b=go:AddComponent(typeof(U.UI.Button));b.targetGraphic=im;b.onClick:AddListener(fn);local t=text(go.transform,'Label',value,23,w-12,h-6,0,0);return b,t
end
local function clearContent()
 if content then U.Object.Destroy(content)end;content=rect(panel.transform,'PageControls',1000,620,0,0);bar=nil;marker=nil
end
function Close()
 if mode=='class'and callback then return end
 if cooking then return end
 if panel then panel:SetActive(false)end;mode=nil;selected={}
 if main then main.SetExplorationMenu(false)end
end
local function show(kind,heading,description)
 if unavailable()then toast('请先结束战斗或骑乘');return false end
 clearContent();mode=kind;panel:SetActive(true);title.text=heading;body.text=description
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
local function restorePotion()
 if not potion then return end
 if actor then actor.speed=potion.speed;actor.scale=potion.scale end
 if potion.light then U.Object.Destroy(potion.light)end
 if potion.sheep then U.Object.Destroy(potion.sheep);actor:SetVisible(true)end
 if potion.hidden then for _,entry in ipairs(potion.hidden)do if entry.r then entry.r.enabled=entry.enabled end end end
 potion=nil
end
local function applyPotion(kind)
 restorePotion();if unavailable()then return end
 potion={kind=kind,untilTime=U.Time.time+10,speed=actor.speed,scale=actor.scale}
 if kind=='wind'then actor.speed=potion.speed*1.8
 elseif kind=='grow'then actor.scale=math.min(1.9,potion.scale*1.5)
 elseif kind=='shrink'then actor.scale=math.max(.3,potion.scale*.6)
 elseif kind=='sheep'then
  local source=U.GameObject.Find('sheep_0');local mesh=source and source:GetComponentInChildren(typeof(U.Renderer),true)
  if mesh then
   local clone=U.Object.Instantiate(mesh.gameObject);clone.name='PotionSheepAppearance'
   local colliders=clone:GetComponentsInChildren(typeof(U.Collider),true);for i=0,colliders.Length-1 do U.Object.Destroy(colliders[i])end
   clone.transform.localScale=mesh.transform.lossyScale
   potion.sheep=clone;potion.sheepRotation=mesh.transform.rotation;potion.hidden={}
   local renderers=actor.gameObject:GetComponentsInChildren(typeof(U.Renderer),true)
   for i=0,renderers.Length-1 do local r=renderers[i];potion.hidden[#potion.hidden+1]={r=r,enabled=r.enabled};r.enabled=false end
  end
 elseif kind=='glow'then
  local go=U.GameObject('PotionFirefly');local light=go:AddComponent(typeof(U.Light));light.type=U.LightType.Point;light.color=U.Color(.6,1,.24,1);light.range=3;light.intensity=1.5;light.shadows=U.LightShadows.None;potion.light=go
 end
end
function ClearPotion()restorePotion()end
function OpenContract(respec,continuation)
 local rpg=scope:GetScript('dragon_rpg.lua')
 if unavailable()or not rpg then return false end
 return rpg.OpenContract(respec,function()
  if actor then actor:Immobilize(false)end
  if continuation then continuation()end
 end)
end

local function openTasks()
 local p=progress.GetProfile();if not p then return end
 local objective,destination=rules.Objective(p)
 if show('tasks','墨曜的长梦','第一章 · 守夜人的誓约\n\n'..objective..'\n\n前往  '..destination)then
  local art=rect(content.transform,'DragonEtching',330,250,-260,-155);local im=art:AddComponent(typeof(U.UI.RawImage));im.texture=main.GetInkTexture('oath');im.uvRect=U.Rect(0,0,1/3,.5);im.raycastTarget=false
  text(content.transform,'OfferingTitle','龙 蛋 供 奉',27,420,50,265,265)
  local rows={{'月辉',p.deposited.moon,30},{'火种',p.deposited.ember,3},{'星露',p.deposited.stardew,1}}
  for i,v in ipairs(rows)do
   text(content.transform,'Offer'..i,v[1]..'    '..v[2]..' / '..v[3],23,390,40,265,210-(i-1)*75)
   local tr=rect(content.transform,'Track'..i,330,3,265,184-(i-1)*75);tr:AddComponent(typeof(U.UI.Image)).color=U.Color(.36,.25,.14,.2)
   local fill=rect(tr.transform,'InkProgress',330*v[2]/v[3],3,-165+165*v[2]/v[3],0);fill:AddComponent(typeof(U.UI.Image)).color=U.Color(.36,.25,.14,.75)
  end
  text(content.transform,'BagHeading','随 身 材 料',25,420,40,265,-55)
  text(content.transform,'BagCounts','蘑菇  '..p.mushroom..'    月见花  '..p.flower..'    羊毛  '..p.wool..'\n\n月辉  '..p.moon..'    火种  '..p.ember..'    星露  '..p.stardew,21,400,120,265,-135)
  button(content.transform,'OpenPotions','〔 打开药水袋 〕',265,-240,300,52,function()OpenPotions()end)
 end
end

function OpenPotions()
 local p=progress.GetProfile();if not p then return end
 show('potions','女巫的药水袋','效果持续十秒；战斗、骑乘或传送会解除。')
 for i,k in ipairs({'wind','grow','shrink','glow','sheep'})do
  button(content.transform,'Drink_'..k,labels[k]..' ×'..p.potions[k],265,150-(i-1)*75,350,56,function()
   if unavailable()then return end
   submit('drink',{potion=k},function()applyPotion(k);Close()end)
  end)
 end
end
local function witch()
 selected={};show('witch','女巫的配方','星露：蘑菇3 ＋ 月见花3 ＋ 羊毛1\n怪药水：选两份采集材料，或一份焦蘑菇。')
 button(content.transform,'BrewStardew','调制星露',0,100,430,64,function()if nearby(current)then submit('stardew',{})else Close()end end)
 local selectionLabel=text(content.transform,'Selection','尚未选择材料',22,800,50,0,-105)
 for i,k in ipairs({'mushroom','flower','wool','charred'})do
  button(content.transform,'Ingredient_'..k,labels[k],-330+(i-1)*220,5,200,60,function()
   if k=='charred'then selected={charred=1}else
    if selected.charred then selected={}end;local n=0;for _,v in pairs(selected)do n=n+v end;if n>=2 then selected={}end;selected[k]=(selected[k]or 0)+1
   end
   local s={};for _,key in ipairs({'mushroom','flower','wool','charred'})do if selected[key]then s[#s+1]=labels[key]..' '..selected[key]end end;selectionLabel.text=table.concat(s,' ＋ ')
  end)
 end
 button(content.transform,'BrewPotion','调制随机药水',0,-190,430,64,function()
  if not nearby(current)then Close();return end
  local kind=({'wind','grow','shrink','glow','sheep'})[math.random(1,5)];submit('brew',{materials=selected,potion=kind},function()selected={};selectionLabel.text='药水已放入背包'end)
 end)
end
local function finishCook()
 if not cooking or cooking.starting or cooking.finishing then return end
 cooking.finishing=true
 submit('cookFinish',{token=cooking.token},function()cooking=nil;Close()end)
end
local function cook()
 show('cook','篝火烤蘑菇','按住下方按钮烤制，在金色区间松手。\n每串消耗一份蘑菇；每二十秒可烤一串。')
 local track=rect(content.transform,'RoastTrack',600,28,0,25);track:AddComponent(typeof(U.UI.Image)).color=U.Color(.22,.16,.10,.25)
 local gold=rect(track.transform,'PerfectZone',78,28,69,0);gold:AddComponent(typeof(U.UI.Image)).color=U.Color(.85,.62,.18,1)
 marker=rect(track.transform,'HeatPointer',8,42,-300,0);marker:AddComponent(typeof(U.UI.Image)).color=U.Color(.62,.16,.10,1)
 local b=button(content.transform,'HoldRoast','按住烤制 · 松手出锅',0,-100,450,90,function()end)
 local tr=b.gameObject:AddComponent(typeof(U.EventSystems.EventTrigger))
 local function event(id,fn)local e=U.EventSystems.EventTrigger.Entry();e.eventID=id;e.callback:AddListener(fn);tr.triggers:Add(e)end
 event(U.EventSystems.EventTriggerType.PointerDown,function()
  if cooking or not nearby(current)then return end
  local duration=4.5+math.random()*.8;cooking={starting=true,duration=duration,released=false}
  local ok,token=submit('cookStart',{duration=duration},function()
   if not cooking then return end;cooking.starting=false;cooking.at=CS.DouyinUtility.GetServerUnixTime();local p=progress.GetProfile();cooking.at=p.cook.at;cooking.token=p.cook.token
   if cooking.released then finishCook()end
  end)
  if ok then cooking.token=token else cooking=nil end
 end)
 event(U.EventSystems.EventTriggerType.PointerUp,function()if cooking then cooking.released=true;finishCook()end end)
 event(U.EventSystems.EventTriggerType.PointerExit,function()if cooking then cooking.released=true;finishCook()end end)
end
local function beginHatch()
 if hatchStart then return end;hatchStart=U.Time.time;show('hatch','龙魂苏醒','月辉、篝火与星露交织。\n墨曜终于听见了你的名字。')
end
local function interact()
 if unavailable()or not current or not nearby(current)then return end
 local kind=current.kind
 if kind=='tree'then OpenContract(true,nil)
 elseif kind=='witch'then witch()
 elseif kind=='camp'then cook()
 elseif kind=='egg'then local p=progress.GetProfile();if p.hatchReady and not p.pact then beginHatch()else submit('deposit',{},function()if progress.GetProfile().hatchReady and not progress.GetProfile().pact then beginHatch()end end)end
 elseif kind=='bed'then if main then main.ReplayPrologue()end
 else submit('gather',{material=kind,isDay=cycle.IsDay()})end
end
local function buildUI()
 if root then return true end
 local fonts=U.Resources.FindObjectsOfTypeAll(typeof(U.Font));for i=0,fonts.Length-1 do if fonts[i].name=='NotoSansSC-Medium'then font=fonts[i];break end end
 if not font then return false end
 root=U.GameObject('DragonExplorationControls');local canvas=root:AddComponent(typeof(U.Canvas));canvas.renderMode=U.RenderMode.ScreenSpaceOverlay;canvas.sortingOrder=230
 local scaler=root:AddComponent(typeof(U.UI.CanvasScaler));scaler.uiScaleMode=U.UI.CanvasScaler.ScaleMode.ScaleWithScreenSize;scaler.referenceResolution=V2(1920,1080);scaler.matchWidthOrHeight=1;root:AddComponent(typeof(U.UI.GraphicRaycaster))
 panel=rect(root.transform,'QuestBook',1100,740,0,0)
 -- Reuse the world's book page texture, rather than an unrelated new UI skin.
 local tex=main and main.GetBookTexture();if tex then local im=panel:AddComponent(typeof(U.UI.RawImage));im.texture=tex;im.color=U.Color.white else panel:AddComponent(typeof(U.UI.Image)).color=U.Color(.91,.85,.72,1)end
 title=text(panel.transform,'Heading','',30,430,65,-260,270);body=text(panel.transform,'Description','',22,410,400,-260,25);body.alignment=U.TextAnchor.UpperLeft
 button(panel.transform,'Close','收起',425,-305,150,55,Close);panel:SetActive(false)
 taskButton=button(root.transform,'QuestEntry','',0,0,72,72,openTasks);taskButton.transform.anchorMin=V2(0,1);taskButton.transform.anchorMax=V2(0,1);taskButton.transform.anchoredPosition=V2(86,-320);taskButton.image.color=U.Color.white;taskButton.image.sprite=icon('book')
 nearButton,nearLabel=button(root.transform,'ExploreInteract','',0,0,310,72,interact);nearButton.transform.anchorMin=V2(1,.5);nearButton.transform.anchorMax=V2(1,.5);nearButton.transform.anchoredPosition=V2(-230,40);nearButton.image.color=U.Color(1,1,1,.15);nearLabel.color=U.Color.white;nearButton.gameObject:SetActive(false)
 notice=text(root.transform,'ProgressStatus','',18,650,50,0,460,U.Color(1,1,1,.9))
 return true
end
local function discover()
 targets={}
 if not witchPlaced then
  local house=U.GameObject.Find('witch_shop_v2');local witch=U.GameObject.Find('tripo_witch')
  if house and witch then witch.transform.position=house.transform.position+V(0,.15,0);witchPlaced=true end
 end
 local function add(name,kind,radius,caption)
  local go=U.GameObject.Find(name);if go then targets[#targets+1]={go=go,kind=kind,radius=radius,label=caption}end
 end
 add('holy_tree3','tree',9,'古树 · 重新签约');add('tripo_witch','witch',2.8,'女巫 · 调制');add('camp','camp',4,'篝火 · 烤蘑菇')
 local egg=U.GameObject.Find('tripo_egg_stage_0');if egg then targets[#targets+1]={position=egg.transform.position,kind='egg',radius=5,height=5,label='龙蛋 · 供奉'}end
 for i=0,35 do add(i==0 and 'mush'or 'mush_'..i,'mushroom',3.5,'采集蘑菇')end
 for i=0,8 do add('sheep_'..i,'wool',3,'取羊毛')end
 -- Flowers are terrain decoration; one bounded collection patch avoids per-blade scripts.
 targets[#targets+1]={position=V(150,40,62),kind='flower',radius=9,height=6,label='采集月见花'}
 targets[#targets+1]={position=V(127,80.5,193),kind='bed',radius=3,height=2,label='重读序章'}
 local all=U.Resources.FindObjectsOfTypeAll(typeof(U.Transform))
 for j=0,all.Length-1 do local t=all[j];local i=tonumber(string.match(t.name,'^tripo_egg_stage_(%d)$'))
  if i and i<=3 and t.gameObject.scene.IsValid and t.gameObject.scene:IsValid()then eggs[i]={go=t.gameObject,scale=t.localScale}end
 end
end
function GetStatus()return{loaded=progress and progress.IsLoaded(),mode=mode,target=current and current.kind,targets=#targets,potion=potion and potion.kind,eggStage=eggStage,cooking=cooking~=nil,bridge=main~=nil}end
function Update()
 if not progress then progress=scope:GetScript('dragon_progress.lua');rules=scope:GetScript('dragon_progress_rules.lua');cycle=scope:GetScript('dragon_daycycle.lua');main=scope:GetScript('dragon_world_bridge.lua')end
 if not progress or not rules or not cycle or not main then progress=nil;return end
 actor=CS.DouyinActorService.GetLocalActor();if not actor or not buildUI()then return end
 if U.Time.time-lastScan>5 then lastScan=U.Time.time;if #targets==0 then discover()end end
 local p=progress.GetProfile();notice.text="";notice.gameObject:SetActive(false)
 if not p then taskButton.gameObject:SetActive(false);nearButton.gameObject:SetActive(false);return end
 local world=main.GetExplorationState();local available=world=='play'and not unavailable()
 taskButton.gameObject:SetActive(available and not mode)
 current=nil;local best=1e9
 for _,t in ipairs(targets)do if nearby(t)then local pos=t.go and t.go.transform.position or t.position;local d=V.Distance(actor.position,pos);if d<best then current=t;best=d end end end
 nearButton.gameObject:SetActive(false)
 local wanted=available and not mode and current or nil
 if wanted~=nativeTarget then
  if nativeExplore then self:RemoveInteractorButton(nativeExplore);nativeExplore=nil end
  nativeTarget=wanted
  if wanted then nativeExplore=self:AddInteractorButton();if nativeExplore then nativeExplore.onClick:AddListener(interact)end end
 end
 if nativeExplore and wanted then local label=nativeExplore:GetComponentInChildren(typeof(U.UI.Text),true);if label then label.text=wanted.label end end
 if pendingClass then main.ApplySavedClass(pendingClass);pendingClass=nil end
 if not firstReady then firstReady=true;main.ApplySavedClass(p.class)end
 local stage=rules.EggStage(p)
 if stage~=eggStage then for i,e in pairs(eggs)do e.go:SetActive(i==stage)end;eggStage=stage end
 if hatchStart then
  local age=U.Time.time-hatchStart;local e=eggs[2];if e then e.go.transform.localScale=e.scale*(1+.025*math.sin(age*9))end
  if age>3 and not progress.GetStatus().pending then
   if e then e.go.transform.localScale=e.scale end
   submit('hatch',{},function()hatchStart=nil;Close()end)
  end
 end
 if cooking and not cooking.starting and marker then
  local t=CS.DouyinUtility.GetServerUnixTime()+CS.DouyinUtility.GetServerTime().Millisecond/1000
  marker.transform.anchoredPosition=V2(-300+600*math.min(1,(t-cooking.at)/cooking.duration),0)
  if t-cooking.at>cooking.duration*1.15 then finishCook()end
 end
 if potion then
  local moved=lastPosition and V.Distance(actor.position,lastPosition)>8
  if U.Time.time>=potion.untilTime or unavailable()or moved then restorePotion()
  elseif potion.sheep then
   actor:SetVisible(false);for _,entry in ipairs(potion.hidden)do if entry.r then entry.r.enabled=false end end
   potion.sheep.transform.position=actor.position;potion.sheep.transform.rotation=actor.rotation*potion.sheepRotation
 elseif potion.light then potion.light.transform.position=actor.position+V(math.sin(U.Time.time*2)*.6,1.2,math.cos(U.Time.time*2)*.6)end
 end
 lastPosition=actor.position
 if mode and unavailable()then callback=nil;cooking=nil;hatchStart=nil;Close()end
end
function OnApplicationFocus(focused)if not focused then restorePotion();if cooking then cooking.released=true;finishCook()end end end
function OnDisable()if nativeExplore then self:RemoveInteractorButton(nativeExplore);nativeExplore=nil;nativeTarget=nil end;restorePotion();callback=nil;cooking=nil;if root then root:SetActive(false)end;if main then main.SetExplorationMenu(false)end end
function OnDestroy()OnDisable();if root then U.Object.Destroy(root)end;for _,r in ipairs(resources)do U.Object.Destroy(r)end end
