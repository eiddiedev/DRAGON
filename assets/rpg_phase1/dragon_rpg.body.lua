-- 职业签约与原生战斗按钮；原型和正式开场共用同一入口。
---@displayName 龙眠职业与武器操作
---@start
---@var PreviewMode:boolean=false
---@name 独立验证模式
---@end
local U=CS.UnityEngine
local V2=U.Vector2
local V3=U.Vector3
local Scope=require("official.core.runtime_scope")
local Log=require("official.core.logger")
local scope=Scope.from(self)
local log=Log.create("dragon-rpg")
local rules,outfits,weapons,fx
local actor,profile,context
local root,canvas,contract,toggle,toggleLabel,confirmLabel,statusLabel
local backdrop,previewButton
local font,nativeStyle
local selection,contractCallback,respec=false,nil,false
local ready=false
local held=false
local attackPressed=false
local ringSprite,ringTexture
local getRing
local detailLabel
local ink=U.Color(.18,.13,.086,1)
local cinnabar=U.Color(.61,.17,.12,1)
local skillPressed=false
local native={}
local hidden={}
local pending={}
local uiRefs={}
local external={menu=false,mounted=false,dead=false}
local openedPreview=false

local function toast(message)CS.DouyinUtility.Toast(message)end
local function rect(parent,name,w,h,x,y,anchor)
 local go=U.GameObject(name);go.transform:SetParent(parent,false)
 local rt=go:AddComponent(typeof(U.RectTransform));rt.anchorMin=anchor or V2(.5,.5);rt.anchorMax=rt.anchorMin
 rt.sizeDelta=V2(w,h);rt.anchoredPosition=V2(x,y);return go,rt
end
local function label(parent,name,value,size,w,h,x,y)
 local go=rect(parent,name,w,h,x,y);local t=go:AddComponent(typeof(U.UI.Text))
 t.font=font;t.fontSize=size;t.text=value;t.color=U.Color.white;t.alignment=U.TextAnchor.MiddleCenter;t.raycastTarget=false
 return t
end
local function makeButton(parent,name,value,w,h,x,y,callback,anchor)
 local go=rect(parent,name,w,h,x,y,anchor);local im=go:AddComponent(typeof(U.UI.Image))
 im.color=U.Color(1,1,1,.035)
 if nativeStyle then im.sprite=nativeStyle;im.type=U.UI.Image.Type.Sliced end
 local b=go:AddComponent(typeof(U.UI.Button));b.targetGraphic=im
 local t=label(go.transform,"Label",value,26,w-10,h-4,0,0)
 b.onClick:AddListener(callback)
 return b,t
end
local function sourceFont()
 for _,name in ipairs({"CustomMain","CustomSub","Jump","HoldHands"})do
  local btn=CS.DouyinUIService.GetInteractionButton(CS.UIType[name])
  if btn then
   local t=btn:GetComponentInChildren(typeof(U.UI.Text),true)
   if t and t.font then font=t.font end
   if name=="CustomMain"and btn.image then nativeStyle=btn.image.sprite end
  end
 end
 local fonts=U.Resources.FindObjectsOfTypeAll(typeof(U.Font))
 for i=0,fonts.Length-1 do if fonts[i].name=="NotoSansSC-Medium"then font=fonts[i];break end end
 nativeStyle=nil -- CustomMain's default sprite is an unrelated platform placeholder.
 return font~=nil
end
local function buildUI()
 if root then return true end
 if not sourceFont()then return false end
 root=U.GameObject("DragonRPGControls");canvas=root:AddComponent(typeof(U.Canvas));canvas.renderMode=U.RenderMode.ScreenSpaceOverlay;canvas.sortingOrder=220
 local scaler=root:AddComponent(typeof(U.UI.CanvasScaler));scaler.uiScaleMode=U.UI.CanvasScaler.ScaleMode.ScaleWithScreenSize;scaler.referenceResolution=V2(1920,1080);scaler.matchWidthOrHeight=1
 root:AddComponent(typeof(U.UI.GraphicRaycaster))
 toggle,toggleLabel=makeButton(root.transform,"WeaponMenu","武器",92,92,-108,350,function()
  if context and context.mode=="combat"then SetMode("explore")else SetMode("combat")end
 end,V2(1,0))
 toggle.image.sprite=getRing();toggle.image.color=U.Color.white;toggleLabel.fontSize=23
 toggle.gameObject:SetActive(false)
 local drt
 backdrop,drt=rect(root.transform,"ContractBackdrop",0,0,0,0);drt.anchorMin=V2.zero;drt.anchorMax=V2.one;drt.offsetMin=V2.zero;drt.offsetMax=V2.zero
 backdrop:AddComponent(typeof(U.UI.Image)).color=U.Color(0,0,0,.38);backdrop:SetActive(false)
 contract=rect(root.transform,"ClassContract",1200,800,0,0)
 local book=scope:GetGameObjectByPath("ContractBook")
 local renderer=book and book:GetComponentInChildren(typeof(U.Renderer),true)
 local texture=nil
 if renderer then for _,key in ipairs({"_BaseTex","_BaseMap","_MainTex"})do if renderer.sharedMaterial:HasProperty(key)then texture=texture or renderer.sharedMaterial:GetTexture(key)end end;book:SetActive(false)end
 local background=contract:AddComponent(typeof(U.UI.RawImage));background.texture=texture;background.color=U.Color.white
 local title=label(contract.transform,"Title","守 夜 人 誓 约",39,470,70,-275,275);title.color=cinnabar
 local hint=label(contract.transform,"Hint","以此名立誓，守护龙的长梦。",22,460,55,-275,210);hint.color=ink
 local names={"melee","mage","ranged"}
 local descriptions={melee="剑誓 · 骑士\n\n身披铠甲，直面暗夜。\n以利刃驱散影灵，以护盾守住同伴。\n\n近战 · 破晓守护",mage="星誓 · 法师\n\n将散落的星火聚于掌心。\n用法杖唤醒魔力，让群星划破黑夜。\n\n远程 · 星火爆裂",ranged="风誓 · 游侠\n\n披林间的风，循月色而行。\n拉弓追逐游影，让箭羽回应誓言。\n\n远程 · 月羽连射"}
 detailLabel=label(contract.transform,"OathText","三条道路，同一个誓言。\n\n在左页选定职业，\n在此签下你的名字。",27,450,410,280,60);detailLabel.color=ink
 for i,kind in ipairs(names)do
  local c=rules.GetClasses()[kind]
  local button,text=makeButton(contract.transform,"Class_"..kind,({"剑誓  /  骑士","星誓  /  法师","风誓  /  游侠"})[i],420,88,-275,90-(i-1)*112,function()
   selection=kind
   for k,v in pairs(uiRefs)do v.image.color=k==kind and U.Color(.61,.17,.12,.13)or U.Color(1,1,1,0)end
   detailLabel.text=descriptions[kind];confirmLabel.text="立下誓约 · "..c.name
  end)
  button.image.color=U.Color(1,1,1,0);text.fontSize=29;text.color=ink;uiRefs[kind]=button
 end
 local confirm
 confirm,confirmLabel=makeButton(contract.transform,"SignContract","选择职业后签约",390,74,280,-240,function()
  if not selection then toast("请先选择职业");return end
  local ok,why=rules.SelectClass(profile,selection,external.inBattle)
  if not ok then toast(why);return end
  context.class=profile.class
  contract:SetActive(false);backdrop:SetActive(false);if previewButton then previewButton.gameObject:SetActive(true)end;context.menu=false;ready=true
  local callback=contractCallback;contractCallback=nil
  if callback then callback(profile.class)else actor:Immobilize(false)end
  log:info("class contracted",profile.class)
 end)
 confirm.image.color=U.Color(.61,.17,.12,.14);confirmLabel.color=cinnabar
 statusLabel=label(contract.transform,"Status","日后可在萤光古树下，重新立誓。",19,460,60,-275,-280);statusLabel.color=U.Color(.42,.34,.25,1)
 contract:SetActive(false)
 if PreviewMode then local btn,txt=makeButton(root.transform,"PreviewClassSwitch","誓约",86,86,100,-205,function()OpenContract(true,nil)end,V2(0,1));btn.image.sprite=getRing();btn.image.color=U.Color.white;txt.fontSize=22;previewButton=btn end
 return true
end
getRing=function()
 if ringSprite then return ringSprite end
 ringTexture=U.Texture2D(96,96,U.TextureFormat.RGBA32,false)
 local pixels=CS.System.Array.CreateInstance(typeof(U.Color),96*96)
 for y=0,95 do for x=0,95 do
  local d=math.sqrt((x-47.5)^2+(y-47.5)^2)
  pixels[y*96+x]=d>46 and U.Color.clear or(d>42 and U.Color(1,1,1,.9)or U.Color(1,1,1,.035))
 end end
 ringTexture:SetPixels(pixels);ringTexture:Apply()
 ringSprite=U.Sprite.Create(ringTexture,U.Rect(0,0,96,96),V2(.5,.5),100)
 return ringSprite
end
local function clearSlots()
 held=false;attackPressed=false;skillPressed=false;pending={}
 for _,v in ipairs(native)do
  if v.trigger then v.trigger.triggers:Clear()end
  if v.button then
   v.button.gameObject:SetActive(false)
   if v.old then
    v.button.image.sprite=v.old.sprite;v.button.image.color=v.old.color
    local rt=v.button.transform;rt.localPosition=v.old.position;rt.sizeDelta=v.old.size
    if v.label then v.label.text=v.old.text;v.label.color=v.old.color;v.label.font=v.old.font;v.label.fontSize=v.old.fontSize;v.label.alignment=v.old.alignment;v.label.rectTransform.localPosition=v.old.labelPosition;v.label.rectTransform.sizeDelta=v.old.labelSize end
   end
  end
 end
 native={}
 for _,v in ipairs(hidden)do
  if v.group then
   v.group.alpha=v.alpha;v.group.blocksRaycasts=v.ray;v.group.interactable=v.interact
   if v.added then U.Object.Destroy(v.group)end
  end
 end
 hidden={}
end
local function hideExplore()
 for _,name in ipairs({"Jump","HoldHands","StopHoldHands"})do
  local btn=CS.DouyinUIService.GetInteractionButton(CS.HandType.Right,CS.UIType[name])
  if btn then
   local group=btn.gameObject:GetComponent(typeof(U.CanvasGroup));local added=group==nil
   if not group then group=btn.gameObject:AddComponent(typeof(U.CanvasGroup))end
   hidden[#hidden+1]={group=group,added=added,alpha=group.alpha,ray=group.blocksRaycasts,interact=group.interactable}
   group.alpha=0;group.blocksRaycasts=false;group.interactable=false
  end
 end
end
local function bindSlot(kind,text,down,up,targetType)
 local btn=CS.DouyinUIService.GetInteractionButton(kind);if not btn then return nil end
 local trigger=btn.gameObject:GetComponent(typeof(U.EventSystems.EventTrigger))
 if not trigger then trigger=btn.gameObject:AddComponent(typeof(U.EventSystems.EventTrigger))end
 trigger.triggers:Clear()
 for _,event in ipairs({{U.EventSystems.EventTriggerType.PointerDown,down},{U.EventSystems.EventTriggerType.PointerUp,up},{U.EventSystems.EventTriggerType.PointerExit,up}})do
  local e=U.EventSystems.EventTrigger.Entry();e.eventID=event[1];e.callback:AddListener(event[2]);trigger.triggers:Add(e)
 end
 local t=btn:GetComponentInChildren(typeof(U.UI.Text),true)
 local rt=btn.transform
 local old={sprite=btn.image.sprite,color=btn.image.color,position=rt.localPosition,size=rt.sizeDelta}
 if t then
  old.text=t.text;old.color=t.color;old.font=t.font;old.fontSize=t.fontSize;old.alignment=t.alignment;old.labelPosition=t.rectTransform.localPosition;old.labelSize=t.rectTransform.sizeDelta
  t.gameObject:SetActive(true);t.color=U.Color.white;t.text=text;t.font=font;t.fontSize=25;t.alignment=U.TextAnchor.MiddleCenter;t.rectTransform.localPosition=V3.zero;t.rectTransform.sizeDelta=V2(120,65)
 end
 btn.image.sprite=getRing();btn.image.color=U.Color.white
 local target=CS.DouyinUIService.GetInteractionButton(CS.HandType.Right,targetType)
 if target then rt.position=target.transform.position;rt.sizeDelta=target.transform.sizeDelta end
 btn.gameObject:SetActive(true)
 local entry={button=btn,trigger=trigger,label=t,old=old};native[#native+1]=entry;return entry
end
function SetMode(mode)
 if not context or not actor then return false end
 if mode~="combat"and mode~="explore"then return false end
 if mode==context.mode then return true end
 if mode=="combat"then
  if not profile.class then OpenContract(false,nil);return false end
  if not ready or context.menu or external.menu or external.mounted or actor:IsSitting()or actor:IsFlying()or external.dead then return false end
  if not weapons.Equip(actor,profile.class)then toast("武器正在准备，请稍候");return false end
  -- Only take the native global slots when they are free.
  for _,kind in ipairs({CS.UIType.CustomMain,CS.UIType.CustomSub})do
   local b=CS.DouyinUIService.GetInteractionButton(kind)
   if not b or b.gameObject.activeSelf then weapons.Unequip(actor);toast("请先结束当前操作");return false end
  end
  bindSlot(CS.UIType.CustomMain,"普攻",function()held=true;attackPressed=true end,function()held=false end,CS.UIType.Jump)
  bindSlot(CS.UIType.CustomSub,"技能",function()skillPressed=true end,function()end,CS.UIType.HoldHands)
  hideExplore();context.mode="combat";toggleLabel.text="收起"
 else
  clearSlots();context.mode="explore";weapons.Unequip(actor);fx.Clear();toggleLabel.text="武器"
 end
 return true
end
function OpenContract(change,callback)
 if not rules or not actor or not buildUI()then return false end
 if external.inBattle then toast("战斗结束后才能重新签约");return false end
 SetMode("explore");context.menu=true;ready=false;respec=change;selection=nil;contractCallback=callback
 confirmLabel.text="选择职业后签约";contract:SetActive(true);backdrop:SetActive(true);if previewButton then previewButton.gameObject:SetActive(false)end;actor:Immobilize(true)
 return true
end
function SetContext(value)
 for k,v in pairs(value or {})do external[k]=v end
 if external.menu or external.mounted or external.dead then SetMode("explore")end
end
function SetExplorationReady(value)ready=value==true end
function SetProfile(value)
 if not value or value.schema~=1 then return false end
 profile=value;if context then context.class=value.class end;return true
end
function GetProfile()return profile end
function GetStatus()
 return {mode=context and context.mode,class=profile and profile.class,ready=ready,sequence=context and context.sequence,contract=contract and contract.activeSelf,
  nativeSlots=#native,pending=#pending,held=held,outfit=actor and outfits and outfits.GetOutfitStatus(actor),
  weapon=actor and weapons and weapons.GetRigStatus(actor)}
end
local function act(kind)
 local action=rules.TryAction(context,kind,U.Time.time);if not action then return end
 local d=actor.rotation*V3.forward;local p=actor.position;local target=V3(p.x+d.x*action.range,p.y+.8,p.z+d.z*action.range)
 if weapons.Attack(actor,profile.class,kind=="skill"and"skill1"or"attack",target)then
  action.origin=V3(p.x,p.y+.8,p.z);action.direction=d;pending[#pending+1]=action
 end
end
function FixedUpdate()
 if not context or not actor or context.mode~="combat"then return end
 context.mounted=external.mounted or actor:IsSitting();context.flying=actor:IsFlying();context.dead=external.dead;context.menu=external.menu or(contract and contract.activeSelf)
 if not rules.CanUse(context)then SetMode("explore");return end
 if skillPressed then skillPressed=false;act("skill")elseif held or attackPressed then attackPressed=false;act("attack")end
end
function Update()
 if not scope then return end
 if not rules then rules=scope:GetScript("dragon_rules.lua");outfits=scope:GetScript("dragon_outfits.lua");weapons=scope:GetScript("dragon_weapons.lua");fx=scope:GetScript("dragon_fx.lua")end
 if not rules or not outfits or not weapons or not fx then rules=nil;return end
 actor=CS.DouyinActorService.GetLocalActor();if not actor then return end
 if not profile then profile=rules.NewProfile();context={mode="explore",class=nil}end
 if not buildUI()then return end
 if PreviewMode and not openedPreview then openedPreview=OpenContract(false,nil)end
 if profile.class then outfits.Equip(actor,profile.class)end
 local available=ready and not context.menu and not external.menu and not external.mounted and not external.dead and not actor:IsSitting()and not actor:IsFlying()
 toggle.gameObject:SetActive(available)
 local safe=U.Screen.safeArea;local scale=1080/U.Screen.height
 local rt=toggle.transform
 rt.anchoredPosition=V2(-(U.Screen.width-safe.xMax)*scale-108,(safe.yMin)*scale+(context.mode=="combat"and 550 or 450))
 if not available and context.mode=="combat"then SetMode("explore")end
 if context.mode=="combat"then
  for _,v in ipairs(hidden)do v.group.alpha=0;v.group.blocksRaycasts=false end
  local left=math.max(0,(context.skillUntil or 0)-U.Time.time)
  if native[2]and native[2].label then native[2].label.text=left>0 and string.format("%.1f",left)or "技能" end
 end
 for i=#pending,1,-1 do local a=pending[i]
  if U.Time.time>=a.hitAt then fx.Play(a.class,a.kind,a.origin,a.direction);table.remove(pending,i)end
 end
end
function OnApplicationFocus(focused)if not focused then held=false;attackPressed=false;skillPressed=false end end
function OnDisable()
 clearSlots();if actor and weapons then weapons.Unequip(actor)end
 if actor and contract and contract.activeSelf then actor:Immobilize(false)end
 if root then root:SetActive(false)end
end
function OnDestroy()
 OnDisable();if actor and outfits then outfits.Unequip(actor)end
 if root then U.Object.Destroy(root);root=nil end
 if ringSprite then U.Object.Destroy(ringSprite);U.Object.Destroy(ringTexture);ringSprite=nil;ringTexture=nil end
end
