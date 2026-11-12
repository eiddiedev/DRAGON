#!/usr/bin/env python3
"""v15：职业誓约页、战斗按键、对决提示（打进作者包的 dragon_rpg.lua；对未打过补丁的原文件运行一次）。"""
import os, lupa
PROJ = os.path.expanduser('~/Library/Application Support/AI World Creator/projects/project_lapv8fm0')
p = f'{PROJ}/ai-sessions/workspace_sbazsi67/wprefabs/dragon_phase1_merged/scripts/dragon_rpg.lua'
lua=lupa.LuaRuntime();chk=lua.eval('function(s) local f,e=load(s) return f and "ok" or e end')
s=open(p,encoding='utf8').read()
def rep(old,new,n=1):
    global s
    assert s.count(old)==n,(s.count(old),old[:70]); s=s.replace(old,new)
def cut(a,b,new,incl_b=True):
    global s
    assert s.count(a)==1,(s.count(a),a[:60]); i=s.index(a); j=s.index(b,i)
    if incl_b: j+=len(b)
    s=s[:i]+new+s[j:]
rep("local battleButton,battleLabel,battleHUD\n","local battleButton,battleLabel,battleHUD\nlocal K=nil\nlocal C15={}          -- v15 界面状态（放进表里，少占局部变量）\n")
rep(""" local im=go:GetComponent(typeof(U.UI.Image));im.sprite=icons[key]or icons.sword;im.color=U.Color.white""",
""" local grt=go:GetComponent(typeof(U.RectTransform));grt.sizeDelta=V2(size,size)
 local im=go:GetComponent(typeof(U.UI.Image));im.sprite=(K and K.L.atlas['ic_'..key]and K.sprite('ic_'..key))or icons[key]or icons.sword;im.color=U.Color.white""")
rep(""" if root then return true end
 if not sourceFont()then return false end
 installIcons()""",""" if root then return true end
 if not sourceFont()then return false end
 local bridge15=scope:GetScript('dragon_world_bridge.lua');K=bridge15 and bridge15.GetKit()
 if not K then return false end
 installIcons()""")
rep(""" toggle,toggleLabel=makeButton(root.transform,"WeaponMenu","武器",92,92,-108,350,function()""",""" toggle,toggleLabel=makeButton(root.transform,"WeaponMenu","武器",128,128,-108,350,function()""")
rep(""" toggle.image.sprite=getRing();toggle.image.color=U.Color.white;toggleLabel.fontSize=23;toggleLabel.text="";setIcon(toggle,"sword",55)""",
""" toggle.image.sprite=getRing();toggle.image.color=U.Color.white;toggleLabel.fontSize=23;toggleLabel.text="";setIcon(toggle,"duel",70)
 C15.toggleLabel=K.img(toggle.transform,'lbl_fight',nil,nil,0,-72)""")
cut(' contract=rect(root.transform,"ClassContract",1200,800,0,0)',' contract:SetActive(false)\n',r''' contract=rect(root.transform,"ClassContract",1355,900,0,0)
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
''')
rep('''  local b,t=makeButton(root.transform,"Skill"..i,"",106,106,i==2 and -335 or -385,i==2 and 330 or 170,''','''  local b,t=makeButton(root.transform,"Skill"..i,"",136,136,i==2 and -372 or -425,i==2 and 352 or 172,''')
rep('''getRing=function()
 if ringSprite then return ringSprite end''','''getRing=function()
 if K then return K.sprite('cb_base')end
 if ringSprite then return ringSprite end''')
rep('''local glyph=v.button and v.button.transform:Find("ActionGlyph");if glyph then U.Object.Destroy(glyph.gameObject)end''','''local glyph=v.button and v.button.transform:Find("ActionGlyph");if glyph then U.Object.Destroy(glyph.gameObject)end
  local cdo=v.button and v.button.transform:Find("Cooldown");if cdo then U.Object.Destroy(cdo.gameObject)end;v.cdo=nil''')
rep('''setIcon(native[1].button,profile.class=="melee"and "sword"or(profile.class=="mage"and "prism"or "bow"),80)''','''native[1].button.image.sprite=K.sprite('cb_atk')
   setIcon(native[1].button,profile.class=="melee"and "sword"or(profile.class=="mage"and "staff"or "bow"),112)''')
rep('''setIcon(native[2].button,cls.skills[1].icon,62)''','''setIcon(native[2].button,cls.skills[1].icon,78)''')
rep('''setIcon(v.button,cls.skills[i].icon,62)''','''setIcon(v.button,cls.skills[i].icon,78)''')
rep('''hideExplore();context.mode="combat";toggleLabel.text="";setIcon(toggle,"exit",55)''','''hideExplore();context.mode="combat";toggleLabel.text="";toggle.image.sprite=K.sprite('cb_exit');setIcon(toggle,"exit",60);K.set(C15.toggleLabel,'lbl_sheath',1)''')
rep('''fx.Clear();toggleLabel.text="";setIcon(toggle,"sword",55)''','''fx.Clear();toggleLabel.text="";toggle.image.sprite=K.sprite('cb_base');setIcon(toggle,"duel",70);K.set(C15.toggleLabel,'lbl_fight',1)''')
rep('''confirmLabel.text="选择职业后签约";contract:SetActive(true)''','''C15.select(nil);C15.group.alpha=0;contract:SetActive(true)''')
rep('''rect(root.transform,"CombatAnchor"..i,i==1 and 156 or 106,i==1 and 156 or 106,i==1 and -190 or -190,i==1 and 170 or 360,V2(1,0))''','''rect(root.transform,"CombatAnchor"..i,i==1 and 216 or 136,i==1 and 216 or 136,i==1 and -190 or -190,i==1 and 190 or 420,V2(1,0))''')
rep('''slot.button.image.color=left>0 and U.Color(1,1,1,.45)or U.Color.white''','''slot.button.image.color=left>0 and U.Color(.8,.8,.8,1)or U.Color.white
    -- 冷却：一圈退去的暗影
    if not slot.cdo then
     local g,grt=rect(slot.button.transform,"Cooldown",10,10,0,0);grt.anchorMin=V2(0,0);grt.anchorMax=V2(1,1);grt.sizeDelta=V2(0,0);grt.anchoredPosition=V2(0,0)
     local cim=g:AddComponent(typeof(U.UI.Image));cim.sprite=K.sprite('cb_cd');cim.type=U.UI.Image.Type.Filled;cim.fillMethod=U.UI.Image.FillMethod.Radial360;cim.raycastTarget=false;slot.cdo=cim
    end
    slot.cdo.fillAmount=left>0 and math.min(1,left/rules.GetClasses()[profile.class].skills[i].cooldown)or 0''')
rep('''hpText.text="心火  "..st.hp.." / "..st.maxHP.."   第 "..(st.stage or 1).." / 3 幕"''','''hpText.text=st.duel and("心火  "..st.hp.." / "..st.maxHP..(st.foeHp and("      对手  "..st.foeHp.." / "..st.foeMax)or""))or("心火  "..st.hp.." / "..st.maxHP.."   第 "..(st.stage or 1).." / 3 幕")''')
rep(''' for _,v in ipairs(damagePool)do if v.active then
  local q=(U.Time.time-v.at)/.85;local camera=U.Camera.main''',''' -- 对决提示：等人、开打、胜负
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
  local q=(U.Time.time-v.at)/.85;local camera=U.Camera.main''')
rep(''' local nearArena=battle and battle.IsNearArena()
 local showTrial=available and battle and ((nearArena and battle.IsNight())or battle.IsParticipating())''',''' if contract.activeSelf and C15.group then
  C15.group.alpha=math.min(1,C15.group.alpha+U.Time.unscaledDeltaTime*3.5)
  if selection and uiRefs[selection]then local sc=1.1+.012*math.sin(U.Time.unscaledTime*4);uiRefs[selection].rt.localScale=V3(sc,sc,1)end
 end
 local nearArena=battle and battle.IsNearArena()
 local nearDuel=battle and battle.IsNearDuel()
 local showTrial=available and battle and ((nearArena and battle.IsNight())or nearDuel or battle.IsParticipating())''')
rep('''if battle.IsParticipating()then battle.Retreat()else local ok,why=battle.Begin();if not ok then toast(why)end end end)end
 elseif not showTrial''','''if battle.IsParticipating()then battle.Retreat()else local ok,why=battle.Begin(battle.IsNearDuel());if not ok then toast(why)end end end)end
 elseif not showTrial''')
rep('''if t then t.text=battle.IsParticipating()and "离开试炼"or "挑战影灵"end end''','''if t then t.text=battle.IsParticipating()and(battle.IsDuel()and "认输离场"or "离开试炼")or(nearDuel and(battle.IsDuelOpen()and "加入对决"or "发起对决")or "挑战影灵")end end''')
r=chk(s);print(r)
if r=='ok': open(p,'w',encoding='utf8').write(s)
