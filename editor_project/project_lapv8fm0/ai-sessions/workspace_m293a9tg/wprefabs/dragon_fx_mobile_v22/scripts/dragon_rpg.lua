---@id bd0f4571-9e3d-4e07-a976-86b831fddd77
---@referenceName dragon_rpg.lua
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

local log=Log.create("dragon-rpg")
local rules,outfits,weapons,fx,battle,combatRules
local progress,signPending
local actor,profile,context
local root,canvas,contract,toggle,toggleLabel,confirmLabel,statusLabel
local backdrop,previewButton
local font,nativeStyle
local selection,contractCallback,respec=false,nil,false
local ready=false
local resumeAfterMount=false
local resumeRetry=0
local held=false
local attackPressed=false
local ringSprite,ringTexture
local getRing
local skillButtons={}
local combatAnchors={}
local hpFill,hpText,hpRoot,hurtFlash
local damagePool={}
local hurtAt=-10
local icons={}
local iconAssets={}
local function installIcons()
 local shapes={
 crossbow={{12,12,52,52},{21,43,43,21},{11,33,17,19},{17,19,31,11},{11,33,31,11},{43,21,53,11},{53,11,45,13},{53,11,51,19}},
 prism={{32,5,51,27},{51,27,42,54},{42,54,22,54},{22,54,13,27},{13,27,32,5},{32,5,26,30},{26,30,42,54},{13,27,51,27}},
 mortar={{14,41,21,49},{21,49,52,18},{52,18,44,10},{44,10,14,41},{11,53,53,53},{21,43,21,53},{44,32,48,53},{44,10,52,18}},
 slow={{17,10,47,10},{17,54,47,54},{20,10,22,23},{22,23,42,41},{42,41,44,54},{44,10,42,23},{42,23,22,41},{22,41,20,54},{25,47,39,47}},
 barrier={{10,52,10,13},{10,13,20,13},{20,13,20,23},{20,23,27,23},{27,23,27,13},{27,13,37,13},{37,13,37,23},{37,23,44,23},{44,23,44,13},{44,13,54,13},{54,13,54,52},{10,52,54,52},{32,32,32,48}},
 economy={{13,22,32,13},{32,13,51,22},{51,22,32,31},{32,31,13,22},{13,22,13,45},{13,45,32,54},{32,54,51,45},{51,45,51,22},{13,34,32,43},{32,43,51,34}},
 }
 shapes.sword={{12,51,23,40},{17,35,29,47},{24,39,51,12},{51,12,45,29},{45,29,29,43},{51,12,34,18},{34,18,20,35}}
 shapes.recover={{15,42,18,49},{18,49,27,54},{27,54,39,54},{39,54,49,46},{49,46,53,34},{53,34,49,22},{49,22,39,14},{39,14,27,13},{27,13,17,18},{17,18,11,27},{11,27,11,14},{11,27,25,27},{28,35,32,31},{32,31,36,35},{36,35,32,43},{32,43,28,35}}
 shapes.bow={{17,8,35,15},{35,15,44,32},{44,32,35,49},{35,49,17,56},{17,8,17,56},{8,32,55,32},{48,25,55,32},{55,32,48,39}}
 shapes.volley={{12,49,42,19},{42,19,32,19},{42,19,42,29},{22,56,52,26},{52,26,42,26},{52,26,52,36},{5,38,35,8},{35,8,25,8},{35,8,35,18}}
 shapes.pierce={{7,50,56,7},{56,7,43,9},{56,7,52,21},{12,17,12,35},{25,28,25,46},{38,39,38,57}}
 shapes.nova={{32,6,38,24},{38,24,58,32},{58,32,38,39},{38,39,32,58},{32,58,25,39},{25,39,6,32},{6,32,25,24},{25,24,32,6},{9,9,17,17},{48,48,56,56},{8,56,16,48},{48,16,56,8}}
 shapes.spin={{16,48,48,16},{12,38,26,52},{14,20,25,10},{25,10,45,10},{45,10,54,23},{54,23,44,21},{54,23,53,13}}
 shapes.shield={{32,7,51,15},{51,15,48,39},{48,39,32,56},{32,56,16,39},{16,39,13,15},{13,15,32,7},{23,30,29,36},{29,36,42,23}}
 shapes.dash={{36,7,17,35},{17,35,31,35},{31,35,26,57},{26,57,49,27},{49,27,35,27},{35,27,36,7}}
 shapes.pin={{32,55,15,28},{15,28,17,16},{17,16,27,9},{27,9,40,10},{40,10,49,20},{49,20,48,30},{48,30,32,55},{27,21,37,21},{37,21,37,31},{37,31,27,31},{27,31,27,21}}
 shapes.eye={{8,32,23,19},{23,19,41,19},{41,19,56,32},{56,32,41,45},{41,45,23,45},{23,45,8,32},{27,27,37,27},{37,27,37,37},{37,37,27,37},{27,37,27,27}}
 shapes.gear={{23,11,41,11},{41,11,53,23},{53,23,53,41},{53,41,41,53},{41,53,23,53},{23,53,11,41},{11,41,11,23},{11,23,23,11},{25,25,39,25},{39,25,39,39},{39,39,25,39},{25,39,25,25}}
 shapes.frost={{32,5,32,59},{9,19,55,45},{9,45,55,19},{24,10,32,18},{32,18,40,10},{24,54,32,46},{32,46,40,54},{11,29,19,25},{19,25,19,15},{45,49,45,39},{45,39,55,35}}
 shapes.meteor={{13,40,17,52},{17,52,29,55},{29,55,40,44},{40,44,37,33},{37,33,26,29},{26,29,13,40},{26,29,43,9},{37,33,55,13},{42,23,52,6},{21,42,27,47}}
 shapes.rain={{13,9,13,45},{8,39,13,45},{13,45,18,39},{32,18,32,56},{27,50,32,56},{32,56,37,50},{51,7,51,44},{46,38,51,44},{51,44,56,38}}
 shapes.judgement={{12,51,23,40},{17,35,29,47},{24,39,45,18},{45,18,40,31},{40,31,29,43},{45,18,31,23},{45,5,45,11},{53,14,59,14},{53,6,57,2}}
 shapes.book={{9,12,31,18},{31,18,55,12},{9,12,9,49},{9,49,31,55},{31,55,55,49},{55,49,55,12},{31,18,31,55}}
 shapes.exit={{25,12,12,12},{12,12,12,52},{12,52,25,52},{25,32,55,32},{45,22,55,32},{55,32,45,42}}
 local function sprite(key,lines,circle)
  local tex=U.Texture2D(64,64,U.TextureFormat.RGBA32,false);tex.filterMode=U.FilterMode.Bilinear
  for y=0,63 do for x=0,63 do
   local alpha=0
   if circle then local r=math.sqrt((x-31.5)^2+(y-31.5)^2);alpha=r<29 and .13 or 0;alpha=math.max(alpha,math.max(0,1-math.abs(r-29)/1.3)*.75)
   else for _,l in ipairs(lines)do local dx,dy=l[3]-l[1],l[4]-l[2];local t=math.max(0,math.min(1,((x-l[1])*dx+(y-l[2])*dy)/(dx*dx+dy*dy)));local d=math.sqrt((x-l[1]-t*dx)^2+(y-l[2]-t*dy)^2);alpha=math.max(alpha,math.max(0,math.min(1,2.2-d)))end end
   tex:SetPixel(x,63-y,U.Color(1,1,1,alpha))
  end end
  tex:Apply();local sp=U.Sprite.Create(tex,U.Rect(0,0,64,64),U.Vector2(.5,.5),100)
  icons[key]=sp;iconAssets[#iconAssets+1]=tex;iconAssets[#iconAssets+1]=sp
 end
 sprite("quiet_circle",{},true)
 for k,lines in pairs(shapes)do sprite(k,lines,false)end
end

local battleButton,battleLabel,battleHUD
local K=nil
local C15={}          -- v15 界面状态（放进表里，少占局部变量）
local nativeTrial
local detailLabel
local ink=U.Color(.18,.13,.086,1)
local cinnabar=U.Color(.61,.17,.12,1)
local skillPressed=false
local skillPressedAt=0
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
local function setIcon(button,key,size)
 local tr=button.transform:Find("ActionGlyph");local go=tr and tr.gameObject
 if not go then go=rect(button.transform,"ActionGlyph",size,size,0,0);go:AddComponent(typeof(U.UI.Image))end
 local grt=go:GetComponent(typeof(U.RectTransform));grt.sizeDelta=V2(size,size)
 local im=go:GetComponent(typeof(U.UI.Image));im.sprite=(K and K.L.atlas['ic_'..key]and K.sprite('ic_'..key))or icons[key]or icons.sword;im.color=U.Color.white;im.raycastTarget=false;im.preserveAspect=true
 return im
end
function ShowDamage(position,amount,hurt)
 if not root or not amount or amount<=0 then return end
 local entry=nil
 for _,v in ipairs(damagePool)do if not v.active then entry=v;break end end
 if not entry and #damagePool<32 then
  local t=label(root.transform,"DamageNumber", "",32,140,55,0,0)
  local outline=t.gameObject:AddComponent(typeof(U.UI.Outline));outline.effectColor=U.Color(.06,.02,.08,.9);outline.effectDistance=V2(2,-2)
  entry={text=t};damagePool[#damagePool+1]=entry
 end
 if not entry then return end
 entry.active=true;entry.at=U.Time.time;entry.position=position+V3(0,1,0);entry.hurt=hurt;entry.text.text=(hurt and "−"or "")..tostring(amount);entry.text.gameObject:SetActive(true)
 if hurt then hurtAt=U.Time.time end
end
local function updateFeedback()
 if not hpRoot then
  hpRoot=rect(root.transform,"PlayerHealth",300,58,245,-78,V2(0,1))
  local track=rect(hpRoot.transform,"Track",280,16,0,-10);track:AddComponent(typeof(U.UI.Image)).color=U.Color(.04,.03,.07,.7)
  local fill,rt=rect(track.transform,"Fill",276,12,0,0,V2(0,.5));rt.pivot=V2(0,.5);rt.anchoredPosition=V2(2,0);hpFill=fill:AddComponent(typeof(U.UI.Image));hpFill.color=U.Color(.25,.88,.66,1)
  hpText=label(hpRoot.transform,"HealthValue","",22,300,30,0,16)
 end
 local st=battle and battle.GetStatus();local visible=ready and not context.menu and st and st.hp~=nil and battle.IsParticipating()
 hpRoot:SetActive(visible==true)
 if visible then hpFill.rectTransform.sizeDelta=V2(276*math.max(0,st.hp/st.maxHP),12);hpText.text=st.duel and("心火  "..st.hp.." / "..st.maxHP..(st.foeHp and("      对手  "..st.foeHp.." / "..st.foeMax)or""))or("心火  "..st.hp.." / "..st.maxHP.."   第 "..(st.stage or 1).." / 3 幕");hpFill.color=U.Time.time-hurtAt<.3 and U.Color(1,.2,.2,1)or U.Color(.25,.88,.66,1)end
 -- 对决提示：等人、开打、胜负
 if K and st then
  if not C15.banner then C15.banner=K.img(root.transform,'lbl_duel_wait',nil,nil,0,300);C15.banner.go:SetActive(false)end
  local key=nil
  if st.duel and st.phase~=C15.phase then C15.phase=st.phase;C15.phaseAt=U.Time.time end
  if not st.duel then C15.phase=nil end
  local age=U.Time.time-(C15.phaseAt or 0)
  if st.duel and st.member then
   if st.phase=='ready'and st.members<2 then key='lbl_duel_wait'
   elseif st.phase=='active'and age<1.6 then key='lbl_duel_go'
   elseif st.phase=='victory'and age<3.5 then key=st.winner==st.me and 'lbl_duel_win'or 'lbl_duel_lose'end
  end
  C15.banner.go:SetActive(key~=nil)
  if key then
   if C15.bannerKey~=key then C15.bannerKey=key;K.set(C15.banner,key,1);if key=='lbl_duel_go'or key=='lbl_duel_win'then K.play('start',.6)end end
   local sc=key=='lbl_duel_wait'and 1 or(1+.5*math.max(0,1-age*3))
   C15.banner.rt.localScale=V3(sc,sc,1)
  else C15.bannerKey=nil end
 end
 for _,v in ipairs(damagePool)do if v.active then
  local q=(U.Time.time-v.at)/.85;local camera=U.Camera.main
  if q>=1 or not camera then v.active=false;v.text.gameObject:SetActive(false)
  else local point=camera:WorldToViewportPoint(v.position);v.text.gameObject:SetActive(point.z>0)
   v.text.rectTransform.anchoredPosition=V2((point.x-.5)*1080*U.Screen.width/U.Screen.height,(point.y-.5)*1080+q*65)
   v.text.color=v.hurt and U.Color(1,.25,.2,math.min(1,(1-q)/.3))or U.Color(1,.88,.47,math.min(1,(1-q)/.3));v.text.transform.localScale=V3.one*(1+.2*math.sin(math.min(1,q/.22)*math.pi))
  end
 end end
end
local function buildUI()
 if root then return true end
 if not sourceFont()then return false end
 local bridge15=scope:GetScript('dragon_world_bridge.lua');K=bridge15 and bridge15.GetKit()
 if not K then return false end
 installIcons()
 root=U.GameObject("DragonRPGControls");canvas=root:AddComponent(typeof(U.Canvas));canvas.renderMode=U.RenderMode.ScreenSpaceOverlay;canvas.sortingOrder=220
 local scaler=root:AddComponent(typeof(U.UI.CanvasScaler));scaler.uiScaleMode=U.UI.CanvasScaler.ScaleMode.ScaleWithScreenSize;scaler.referenceResolution=V2(1920,1080);scaler.matchWidthOrHeight=1
 root:AddComponent(typeof(U.UI.GraphicRaycaster))
 toggle,toggleLabel=makeButton(root.transform,"WeaponMenu","武器",128,128,-108,350,function()
  if context and context.mode=="combat"then SetMode("explore")else SetMode("combat")end
 end,V2(1,0))
 toggle.image.sprite=getRing(true);toggle.image.color=U.Color.white;toggleLabel.fontSize=23;toggleLabel.text="";setIcon(toggle,"duel",70)
 toggle.gameObject:SetActive(false)
 local drt
 backdrop,drt=rect(root.transform,"ContractBackdrop",0,0,0,0);drt.anchorMin=V2.zero;drt.anchorMax=V2.one;drt.offsetMin=V2.zero;drt.offsetMax=V2.zero
 backdrop:AddComponent(typeof(U.UI.Image)).color=U.Color(0,0,0,.38);backdrop:SetActive(false)
 contract=rect(root.transform,"ClassContract",1355,900,0,0)
 local background=contract:AddComponent(typeof(U.UI.RawImage));background.texture=K.bookTex;background.color=U.Color.white
 C15.group=contract:AddComponent(typeof(U.CanvasGroup))
 confirmLabel={};detailLabel={};statusLabel={}
 local lx,rx=-299,299
 K.img(contract.transform,'cls_title',nil,nil,lx,300)
 C15.pick=K.img(contract.transform,'cls_pick',nil,nil,rx,60)
 C15.detail=K.img(contract.transform,'cls_melee',nil,nil,rx,66);C15.detail.go:SetActive(false)
 C15.glow=K.img(contract.transform,'card_glow',200,nil,0,0);C15.glow.go:SetActive(false)
 uiRefs={}
 C15.select=function(kind)
  selection=kind
  for k,v in pairs(uiRefs)do local sc=k==kind and 1.1 or 1;v.rt.localScale=V3(sc,sc,1);v.ri.color=(kind==nil or k==kind)and U.Color.white or U.Color(.86,.82,.76,1)end
  C15.pick.go:SetActive(kind==nil);C15.detail.go:SetActive(kind~=nil);C15.glow.go:SetActive(kind~=nil)
  if kind then
   K.set(C15.detail,'cls_'..kind,1)
   C15.glow.rt.anchoredPosition=V2(uiRefs[kind].x,40+13);C15.glow.rt.localScale=V3(1.1,1.1,1)
   K.play('card',.8)
  end
  K.set(C15.sign,kind and 'btn_sign'or 'btn_sign_off')
 end
 for i,kind in ipairs({"melee","mage","ranged"})do
  local x=lx+(i-2)*188
  local card=K.button(contract.transform,'card_'..kind,176,x,40,function()C15.select(kind)end)
  card.go.name="Class_"..kind;card.x=x;uiRefs[kind]=card
 end
 K.img(contract.transform,'cls_foot',nil,nil,lx,-268)
 C15.sign=K.button(contract.transform,'btn_sign_off',380,rx,-296,function()
  if not selection then toast("请先选择职业");return end
  if signPending then return end
  if not progress or not progress.IsLoaded()then toast("玩法正在初始化");return end
  if external.inBattle or external.mounted or actor:IsSitting()or actor:IsFlying()then toast("请先结束战斗或骑乘");return end
  signPending=true
  local ok,why=progress.SelectClass(selection,function(saved,message)
   signPending=false
   if not saved then toast(message);return end
   profile=progress.GetProfile();context.class=profile.class
   K.play('stamp')
   contract:SetActive(false);backdrop:SetActive(false);context.menu=false;ready=true
   local callback=contractCallback;contractCallback=nil
   if callback then callback(profile.class)else actor:Immobilize(false)end
   log:info("class saved",profile.class)
  end)
  if not ok then signPending=false;toast(why)end
 end)
 C15.sign.go.name="SignContract"
 contract:SetActive(false)
 battleButton,battleLabel=makeButton(root.transform,"BattleStart","试炼",86,86,100,-325,function()
  if not battle then return end
  if battle.IsParticipating()then battle.Retreat()else local ok,why=battle.Begin();if not ok then toast(why)end end
 end,V2(0,1));battleButton.image.sprite=getRing();battleButton.image.color=U.Color.white;battleLabel.fontSize=22;battleLabel.text="";setIcon(battleButton,"shield",50)
 battleHUD=label(root.transform,"BattleStatus","",25,880,70,0,400)
 if PreviewMode then local btn,txt=makeButton(root.transform,"PreviewClassSwitch","誓约",86,86,100,-205,function()OpenContract(true,nil)end,V2(0,1));btn.image.sprite=getRing();btn.image.color=U.Color.white;txt.fontSize=22;txt.text="";setIcon(btn,"book",50);previewButton=btn end
 for i=2,3 do
  local index=i
  local b,t=makeButton(root.transform,"Skill"..i,"",136,136,i==2 and -397 or -452,i==2 and 338 or 165,function()skillPressed=index;skillPressedAt=U.Time.time end,V2(1,0))
  b.image.sprite=getRing();b.image.color=U.Color.white;t.fontSize=25
  skillButtons[i]={button=b,label=t};b.gameObject:SetActive(false)
 end
 return true
end
getRing=function(plain)
 if K and not plain then return K.sprite('cb_base')end
 if ringSprite then return ringSprite end
 ringTexture=U.Texture2D(96,96,U.TextureFormat.RGBA32,false)
 local pixels=CS.System.Array.CreateInstance(typeof(U.Color),96*96)
 for y=0,95 do for x=0,95 do
  local d=math.sqrt((x-47.5)^2+(y-47.5)^2)
  pixels[y*96+x]=d>46.5 and U.Color.clear or(d>43 and U.Color(1,1,1,math.min(.95,(46.5-d)*1.2))or U.Color(1,1,1,.2))
 end end
 ringTexture:SetPixels(pixels);ringTexture:Apply()
 ringSprite=U.Sprite.Create(ringTexture,U.Rect(0,0,96,96),V2(.5,.5),100)
 return ringSprite
end
local function clearSlots()
 held=false;attackPressed=false;skillPressed=false;pending={}
 for _,v in pairs(skillButtons)do v.button.gameObject:SetActive(false)end
 for _,v in ipairs(native)do
  local glyph=v.button and v.button.transform:Find("ActionGlyph");if glyph then U.Object.Destroy(glyph.gameObject)end
  local cdo=v.button and v.button.transform:Find("Cooldown");if cdo then U.Object.Destroy(cdo.gameObject)end;v.cdo=nil
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
  bindSlot(CS.UIType.CustomMain,"",function()held=true;attackPressed=true end,function()held=false end,CS.UIType.Jump)
  bindSlot(CS.UIType.CustomSub,"",function()skillPressed=1;skillPressedAt=U.Time.time end,function()end,CS.UIType.HoldHands)
  local cls=rules.GetClasses()[profile.class]
  native[1].button.image.sprite=K.sprite('cb_atk')
   setIcon(native[1].button,profile.class=="melee"and "sword"or(profile.class=="mage"and "staff"or "bow"),112)
  setIcon(native[2].button,cls.skills[1].icon,78)
  for i=2,3 do local v=skillButtons[i];setIcon(v.button,cls.skills[i].icon,78);v.button.gameObject:SetActive(true)end
  hideExplore();context.mode="combat";toggleLabel.text="";setIcon(toggle,"exit",C15.iconSize or 60)
 else
  clearSlots();context.mode="explore";weapons.Unequip(actor);fx.Clear();toggleLabel.text="";setIcon(toggle,"duel",C15.iconSize or 70)
 end
 return true
end
function IsContractOpen()return contract~=nil and contract.activeInHierarchy end
function OpenContract(change,callback,parent)
 if not rules or not actor or not buildUI()then return false end
 if not progress or not progress.IsLoaded()then toast("玩法正在初始化");return false end
 local bridge=scope:GetScript('dragon_world_bridge.lua')
 contract.transform:SetParent(parent or root.transform,false);contract.transform.anchoredPosition=V2.zero
 contract:GetComponent(typeof(U.UI.RawImage)).enabled=parent==nil
 if bridge and bridge.GetBookTexture()then contract:GetComponent(typeof(U.UI.RawImage)).texture=bridge.GetBookTexture()end
 if external.inBattle or external.mounted or actor:IsSitting()or actor:IsFlying()then toast("请先结束战斗或骑乘");return false end
 SetMode("explore");context.menu=true;ready=false;respec=change;selection=nil;contractCallback=callback
 C15.select(nil);C15.group.alpha=0;contract:SetActive(true);backdrop:SetActive(parent==nil);contract.transform:SetAsLastSibling();if previewButton then previewButton.gameObject:SetActive(false)end;actor:Immobilize(true)
 return true
end
function SetContext(value)
 if value and value.mounted and not external.mounted and context and context.mode=='combat'then resumeAfterMount=true end
 for k,v in pairs(value or {})do external[k]=v end
 if external.menu or external.mounted or external.dead then SetMode("explore")end
end
function SetExplorationReady(value)ready=value==true end
function SetProfile(value)
 if not value or value.schema~=2 then return false end
 profile=value;if context then context.class=value.class end;return true
end
function GetProfile()return profile end
function GetStatus()
 return {mode=context and context.mode,class=profile and profile.class,ready=ready,sequence=context and context.sequence,contract=contract and contract.activeSelf,
  nativeSlots=#native,skills=rules and profile and profile.class and rules.GetClasses()[profile.class].skills,skillCooldowns=context and {context.skill1Until,context.skill2Until,context.skill3Until},pending=#pending,held=held,outfit=actor and outfits and outfits.GetOutfitStatus(actor),
  weapon=actor and weapons and weapons.GetRigStatus(actor),battle=battle and battle.GetStatus()}
end
local function act(kind)
 local action=rules.TryAction(context,kind,U.Time.time);if not action then return false end
 local d=actor.rotation*V3.forward;local p=actor.position;local target=V3(p.x+d.x*action.range,p.y+.65,p.z+d.z*action.range);local aim=battle and battle.GetAim(d,action.range);if aim then target=aim;local delta=target-V3(p.x,p.y+.65,p.z);delta.y=0;if delta.sqrMagnitude>.001 then d=delta.normalized end end
 if weapons.Attack(actor,profile.class,kind,target)then
  action.origin=V3(p.x,p.y+.65,p.z);action.direction=d;if not(battle and battle.SendAction(action))then fx.Charge(action.class,action.kind,action.origin,target);pending[#pending+1]=action end
  return true
 end
 return false
end
function OnUIPointerDown(ui)
 if not context or context.mode~='combat'then return end
 if ui==CS.UIType.CustomMain then held=true;attackPressed=true
 elseif ui==CS.UIType.CustomSub then skillPressed=1;skillPressedAt=U.Time.time end
end
function OnUIPointerUp(ui)if ui==CS.UIType.CustomMain then held=false end end
function FixedUpdate()
 if not context or not actor or context.mode~="combat"then return end
 context.mounted=external.mounted or actor:IsSitting();context.flying=actor:IsFlying();context.dead=external.dead;context.menu=external.menu or(contract and contract.activeSelf)
 if not rules.CanUse(context)then SetMode("explore");return end
 if skillPressed then if U.Time.time-skillPressedAt>.65 or act("skill"..skillPressed)then skillPressed=false end elseif held or attackPressed then attackPressed=false;act("attack")end
end
function Update()
 if not scope then return end
 if not rules then rules=scope:GetScript("dragon_rules.lua");outfits=scope:GetScript("dragon_outfits.lua");weapons=scope:GetScript("dragon_weapons.lua");fx=scope:GetScript("dragon_fx.lua")end
 if not rules or not outfits or not weapons or not fx then rules=nil;return end
 if not battle then battle=scope:GetScript("dragon_combat.lua")end
 if not combatRules then combatRules=scope:GetScript("dragon_combat_rules.lua")end
 actor=CS.DouyinActorService.GetLocalActor();if not actor then return end
 if not progress then progress=scope:GetScript("dragon_progress.lua")end
 if not progress or not progress.IsLoaded()then return end
 profile=progress.GetProfile()
 if not context then context={mode="explore",class=profile.class}end
 context.class=profile.class
 if battle and combatRules then battle.Configure({GetProfile=GetProfile,SetMode=SetMode,SetContext=SetContext,ShowDamage=ShowDamage,AwardBattle=progress.AwardBattle},rules,fx,combatRules)end
 if not buildUI()then return end
 root:SetActive(true)
 context.menu=external.menu or(contract and contract.activeSelf)or false
 context.mounted=external.mounted or actor:IsSitting()
 context.flying=actor:IsFlying();context.dead=external.dead
 updateFeedback()
 if PreviewMode and not openedPreview then openedPreview=OpenContract(false,nil)end
 if profile.class then outfits.Equip(actor,profile.class)end
 local available=ready and not context.menu and not external.menu and not external.mounted and not external.dead and not actor:IsSitting()and not actor:IsFlying()
 toggle.gameObject:SetActive(available)
 if resumeAfterMount and available and U.Time.time>=resumeRetry then
  resumeRetry=U.Time.time+.75;if SetMode('combat')then resumeAfterMount=false end
 end
 if battleButton then battleButton.gameObject:SetActive(false);battleHUD.gameObject:SetActive(false)end
 if contract.activeSelf and C15.group then
  C15.group.alpha=math.min(1,C15.group.alpha+U.Time.unscaledDeltaTime*3.5)
  if selection and uiRefs[selection]then local sc=1.1+.012*math.sin(U.Time.unscaledTime*4);uiRefs[selection].rt.localScale=V3(sc,sc,1)end
 end
 local nearArena=battle and battle.IsNearArena()
 local nearDuel=battle and battle.IsNearDuel()
 local showTrial=available and battle and (nearArena or nearDuel or battle.IsParticipating())
 if showTrial and not nativeTrial then
  nativeTrial=self:AddInteractorButton()
  if nativeTrial then nativeTrial.onClick:AddListener(function()if battle.IsParticipating()then battle.Retreat()else local ok,why=battle.Begin(battle.IsNearDuel());if not ok then toast(why)end end end)end
 elseif not showTrial and nativeTrial then self:RemoveInteractorButton(nativeTrial);nativeTrial=nil end
 if nativeTrial then local t=nativeTrial:GetComponentInChildren(typeof(U.UI.Text),true);if t then t.text=battle.IsParticipating()and(battle.IsDuel()and "认输离场"or "离开试炼")or(nearDuel and(battle.IsDuelOpen()and "加入对决"or "发起对决")or "挑战影灵")end end
 local safe=U.Screen.safeArea;local scale=1080/U.Screen.height
 local rt=toggle.transform
 -- 拔剑键跟原生的跳跃键、牵手键排成一道弧：和牵手键一样大，落在弧线上牵手键的下一个位置
 local hand=CS.DouyinUIService.GetInteractionButton(CS.HandType.Right,CS.UIType.HoldHands)
 local jump=CS.DouyinUIService.GetInteractionButton(CS.HandType.Right,CS.UIType.Jump)
 if hand and jump and context.mode~="combat"then
  local h,j=hand.transform,jump.transform
  local unit=root.transform.lossyScale.x
  local size=h.rect.width*h.lossyScale.x/unit
  if size>20 then
   rt.sizeDelta=V2(size,size)
   if C15.iconSize~=size*.56 then C15.iconSize=size*.56;setIcon(toggle,"duel",C15.iconSize)end
   local d=h.position-j.position
   local q=U.Quaternion.Euler(0,0,-62)*V3(d.x,d.y,0)
   C15.togglePos=j.position+q
  end
 end
 if context.mode=="combat"then rt.anchoredPosition=V2(-(U.Screen.width-safe.xMax)*scale-74,(safe.yMin)*scale+392)
 elseif C15.togglePos then rt.position=C15.togglePos
 else rt.anchoredPosition=V2(-(U.Screen.width-safe.xMax)*scale-108,(safe.yMin)*scale+350)end
 if not available and context.mode=="combat"then SetMode("explore")end
 if context.mode=="combat"then
  for i=1,2 do
   if not combatAnchors[i]then local go,rt=rect(root.transform,"CombatAnchor"..i,i==1 and 216 or 136,i==1 and 216 or 136,i==1 and -215 or -235,i==1 and 185 or 422,V2(1,0));combatAnchors[i]=rt end
   local slot=native[i];if slot then slot.button.transform.position=combatAnchors[i].position;slot.button.transform.sizeDelta=combatAnchors[i].sizeDelta*(combatAnchors[i].lossyScale.x/slot.button.transform.parent.lossyScale.x) end
  end
  for _,v in ipairs(hidden)do v.group.alpha=0;v.group.blocksRaycasts=false end
  for i=1,3 do
   local slot=i==1 and native[2]or skillButtons[i];local left=math.max(0,(context["skill"..i.."Until"]or 0)-U.Time.time)
   if slot then
    if slot.label then slot.label.color=U.Color.white;slot.label.text=left>0 and string.format("%.1f",left)or "";slot.label.transform:SetAsLastSibling()end
    local glyph=slot.button.transform:Find("ActionGlyph");if glyph then glyph:GetComponent(typeof(U.UI.Image)).color=left>0 and U.Color(1,1,1,.22)or U.Color.white end
    slot.button.image.color=left>0 and U.Color(.8,.8,.8,1)or U.Color.white
    -- 冷却：一圈退去的暗影
    if not slot.cdo then
     local g,grt=rect(slot.button.transform,"Cooldown",10,10,0,0);grt.anchorMin=V2(0,0);grt.anchorMax=V2(1,1);grt.sizeDelta=V2(0,0);grt.anchoredPosition=V2(0,0)
     local cim=g:AddComponent(typeof(U.UI.Image));cim.sprite=K.sprite('cb_cd');cim.type=U.UI.Image.Type.Filled;cim.fillMethod=U.UI.Image.FillMethod.Radial360;cim.raycastTarget=false;slot.cdo=cim
    end
    slot.cdo.fillAmount=left>0 and math.min(1,left/rules.GetClasses()[profile.class].skills[i].cooldown)or 0
   end
  end
 end
 for i=#pending,1,-1 do local a=pending[i]
  if U.Time.time>=a.hitAt then fx.Play(a.class,a.kind,a.origin,a.direction);table.remove(pending,i)end
 end
end
function OnEnable()if root then root:SetActive(true)end end
function OnApplicationFocus(focused)if not focused then held=false;attackPressed=false;skillPressed=false end end
function OnDisable()
 if nativeTrial then self:RemoveInteractorButton(nativeTrial);nativeTrial=nil end
 clearSlots();if actor and weapons then weapons.Unequip(actor)end
 if actor and contract and contract.activeSelf then actor:Immobilize(false)end
 if root then root:SetActive(false)end
end
function OnDestroy()
 OnDisable();if actor and outfits then outfits.Unequip(actor)end
 if root then U.Object.Destroy(root);root=nil end
 if ringSprite then U.Object.Destroy(ringSprite);U.Object.Destroy(ringTexture);ringSprite=nil;ringTexture=nil end
end

do local previous=OnDestroy;function OnDestroy()if previous then previous()end;ReleaseMobileDependencies()end end
