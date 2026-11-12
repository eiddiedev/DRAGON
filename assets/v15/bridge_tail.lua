
---------------------------------------------------------------- v15：给其它脚本用的界面工具、誓约页入口
function GetKit()
 if UI.K.ready and UI.root and UI.P_hud then
  UI.K.L=UI.K2L;UI.K.bookTex=UI.tex.ui_book;UI.K.bookAspect=UI.L.book.aspect;UI.K.root=UI.root
  return UI.K
 end
end
-- 探索脚本和昼夜脚本启动后把自己的接口登记到这里（主脚本直接查不到它们）
function RegisterScript(name,api)DR.phase1[name]=api end
function GetVisitCount()return UI.visit.n,#UI.K2L.poi end
function ShowNote(kind,nameKey,n,total)UI.note(kind,nameKey,n,total)end
function UI.showOath()
 local r=DR.phase1.rpg;if not r or not UI.P_book then return false end
 local B=UI.P_book;UI.spread=4;B.left.go:SetActive(false);B.right.go:SetActive(false);B.hint.go:SetActive(false)
 UI.show(B,true);UI.state='book';UI.lockPlayer(DouyinActorService.GetLocalActor(),true)
 return r.OpenContract(false,function()
  -- 书页保持隐藏，直到下次翻开；否则合书淡出时旧页会闪一下
  UI.leaveBook(DouyinActorService.GetLocalActor())
 end,B.book.rt)
end
function ReplayPrologue()
 if UI.P_book and UI.state=='play' then UI.spread=1;UI.setSpread(1);UI.show(UI.P_book,true);UI.P_book.fade=3;UI.state='book';UI.play('open')
  local a=DouyinActorService.GetLocalActor();if a then UI.lockPlayer(a,true)end
 end
end

---------------------------------------------------------------- v15：特效用的材质（依次尝试可用的着色器）
function UI.fxMaterial(tex,color)
 if not UI.fxShader then
  for _,name in ipairs({'Sprites/Default','UI/Default','Universal Render Pipeline/Particles/Unlit','Unlit/Transparent','Legacy Shaders/Particles/Alpha Blended'})do
   local sh=UnityEngine.Shader.Find(name);if sh then UI.fxShader=sh;break end
  end
 end
 if not UI.fxShader then return nil end
 local m=UnityEngine.Material(UI.fxShader)
 if tex then m.mainTexture=tex end
 if color then m.color=color end
 m.renderQueue=3100
 return m
end
function UI.fxQuad(name,tex,color,size)
 local m=UI.fxMaterial(tex,color);if not m then return nil end
 local go=UnityEngine.GameObject.CreatePrimitive(UnityEngine.PrimitiveType.Quad);go.name=name
 local col=go:GetComponent(typeof(UnityEngine.Collider));if col then col.enabled=false;UnityEngine.Object.Destroy(col)end
 local r=go:GetComponent(typeof(UnityEngine.Renderer));r.sharedMaterial=m;r.shadowCastingMode=UnityEngine.Rendering.ShadowCastingMode.Off;r.receiveShadows=false
 go.transform.localScale=Vector3(size,size,1)
 return {go=go,mat=m,size=size}
end

---------------------------------------------------------------- v15：裂隙之门的漩涡（两扇门各一个，始终面向镜头，三层反向旋转）
UI.vortex={}
function UI.setupVortex()
 if UI.vortex.ready or UI.vortex.failed or not UI.K.ready then return end
 local tex=UI.K.tex.vortex
 UI.vortex.list={}
 for i,c in ipairs({Vector3(ARENA_GATE.x,ARENA_GATE.y+1.7,ARENA_GATE.z),Vector3(ARENA_EXIT.x,ARENA_EXIT.y+1.7,ARENA_EXIT.z)})do
  local v={center=c,layers={}}
  for k,spec in ipairs({{5.4,UnityEngine.Color(.55,.35,1,.55),26},{4.2,UnityEngine.Color(.5,.85,1,.8),-48},{2.6,UnityEngine.Color(1,1,1,.95),95}})do
   local q=UI.fxQuad('RiftVortex'..i..'_'..k,tex,spec[2],spec[1])
   if not q then UI.vortex.failed=true;report('vortex: no shader');return end
   q.speed=spec[3];q.base=spec[1];v.layers[k]=q
  end
  local lg=UnityEngine.GameObject('RiftVortexLight'..i);local light=lg:AddComponent(typeof(UnityEngine.Light))
  light.type=UnityEngine.LightType.Point;light.color=UnityEngine.Color(.55,.5,1,1);light.range=9;light.intensity=2.2;light.shadows=UnityEngine.LightShadows.None
  lg.transform.position=c;v.light=light
  UI.vortex.list[i]=v
 end
 UI.vortex.ready=true
end
function UI.updateVortex()
 if not UI.vortex.ready then UI.setupVortex();return end
 local cam=UnityEngine.Camera.main;if not cam then return end
 local t=Time.time
 for _,v in ipairs(UI.vortex.list)do
  local look=Quaternion.LookRotation(v.center-cam.transform.position)
  for k,q in ipairs(v.layers)do
   local s=q.base*(1+.05*math.sin(t*2.3+k))
   q.go.transform.position=v.center-(look*Vector3.forward)*(.06*k)
   q.go.transform.rotation=look*Quaternion.Euler(0,0,t*q.speed)
   q.go.transform.localScale=Vector3(s,s,1)
  end
  v.light.intensity=2+.6*math.sin(t*3.1)
 end
end

---------------------------------------------------------------- v15：眩晕（生蘑菇）与镜头震动（大招）。另开一台跟随主相机的相机，加上摇晃、滚转和视野伸缩；眩晕时再叠一层旋转的紫雾
UI.dizzy={}
function UI.fxCam()
 local D=UI.dizzy
 if D.cam then return D.cam end
 local main=UnityEngine.Camera.main;if not main then return nil end
 local go=UnityEngine.GameObject('dr_fx_cam');local cam=go:AddComponent(typeof(UnityEngine.Camera))
 cam:CopyFrom(main);cam.depth=main.depth+2
 pcall(function()
  local T=typeof(CS.UnityEngine.Rendering.Universal.UniversalAdditionalCameraData)
  local a=main:GetComponent(T);local b=go:GetComponent(T) or go:AddComponent(T)
  if a and b then b.renderPostProcessing=a.renderPostProcessing;b.renderShadows=a.renderShadows;b.antialiasing=a.antialiasing end
 end)
 D.cam=cam
 return cam
end
function UI.fxOverlay()
 local D=UI.dizzy
 if D.overlay or not UI.root or not UI.K.ready then return end
 local go2,rt=UI.node(UI.root.transform,'screen_fx',true);go2.transform:SetAsFirstSibling()
 D.overlay=go2;D.cg=go2:AddComponent(typeof(UnityEngine.CanvasGroup));D.cg.blocksRaycasts=false;D.cg.interactable=false
 D.flash=UI.fullImg(rt,nil,UnityEngine.Color(1,1,1,0));D.flash.ri.raycastTarget=false
 D.fog=UI.img(rt,UI.K.tex.vortex,nil,2600,2600,0,0,UnityEngine.Color(.62,.4,1,0))
 D.fog2=UI.img(rt,UI.K.tex.vortex,nil,1900,1900,0,0,UnityEngine.Color(.4,.9,.8,0))
 D.vig=UI.fullImg(rt,UI.tex.ui_atlas,UnityEngine.Color(.35,.1,.5,0));D.vig.ri.uvRect=UI.R(UI.L.atlas.vignette);D.vig.ri.raycastTarget=false
end
function SetDizzy(seconds)
 local D=UI.dizzy
 D.untilT=Time.time+(seconds or 10);D.total=seconds or 10
 UI.fxCam();UI.fxOverlay()
end
function IsDizzy()return UI.dizzy.untilT~=nil and UI.dizzy.untilT>Time.time end
-- flash：闪光强度 0~1；shake：震动幅度；hurt：受伤用红色
function ScreenFx(flash,shake,duration,hurt)
 local D=UI.dizzy
 UI.fxOverlay()
 if flash and flash>0 and D.flash then
  D.flashA=math.max(D.flashA or 0,flash);D.flashD=duration or .3;D.flashT=Time.time
  D.flashC=hurt and {1,.15,.1} or {.92,.86,1}
 end
 if shake and shake>0 then
  D.shakeA=math.max(D.shakeLeft and D.shakeLeft>0 and D.shakeA or 0,shake);D.shakeD=duration or .3;D.shakeT=Time.time
  UI.fxCam()
 end
end
function UI.dizzyLate()
 local D=UI.dizzy
 local now=Time.time
 -- 闪光
 if D.flash then
  local a=0
  if D.flashT then
   local u=(now-D.flashT)/D.flashD
   if u>=1 then D.flashT=nil else a=D.flashA*(1-u)*(1-u) end
  end
  local c=D.flashC or {1,1,1}
  D.flash.ri.color=UnityEngine.Color(c[1],c[2],c[3],a)
 end
 local k=0
 if D.untilT then
  local left=D.untilT-now
  if left<=0 then D.untilT=nil else k=math.min(1,left/.8)*math.min(1,(D.total-left)/.5) end
 end
 local sh=0
 if D.shakeT then
  local u=(now-D.shakeT)/D.shakeD
  if u>=1 then D.shakeT=nil;D.shakeLeft=0 else sh=D.shakeA*(1-u);D.shakeLeft=1-u end
 end
 if D.overlay then
  D.overlay:SetActive(k>0 or D.flashT~=nil)
  D.fog.ri.color=UnityEngine.Color(.62,.4,1,.36*k)
  D.fog2.ri.color=UnityEngine.Color(.4,.9,.8,.22*k)
  D.vig.ri.color=UnityEngine.Color(.35,.1,.5,.85*k)
  if k>0 then
   D.fog.rt.localEulerAngles=Vector3(0,0,now*38)
   D.fog2.rt.localEulerAngles=Vector3(0,0,-now*61)
   local s=1+.12*math.sin(now*2)
   D.fog.rt.localScale=Vector3(s,s,1)
  end
 end
 if not D.cam then return end
 local main=UnityEngine.Camera.main
 if (k<=0 and sh<=0) or not main then
  UnityEngine.Object.Destroy(D.cam.gameObject);D.cam=nil
  return
 end
 local t=now
 local mt=main.transform
 local roll=(math.sin(t*1.7)*13+math.sin(t*4.1)*4)*k+math.sin(t*61)*1.6*sh
 local yaw=math.sin(t*1.1+1)*5*k+math.sin(t*47)*.9*sh
 local pitch=math.sin(t*1.9)*4*k+math.sin(t*53)*1.1*sh
 D.cam.transform.position=mt.position+mt.right*(math.sin(t*2.3)*.35*k+math.sin(t*71)*.12*sh)+mt.up*(math.sin(t*3.1)*.22*k+math.sin(t*83)*.14*sh)
 D.cam.transform.rotation=mt.rotation*Quaternion.Euler(pitch,yaw,roll)
 D.cam.fieldOfView=main.fieldOfView+(math.sin(t*2.6)*16+math.sin(t*5.3)*5)*k-2.5*sh
end

---------------------------------------------------------------- v15：铺在平地上的魔法阵（一张水平的发光贴图，慢慢转）
function GetSigil()
 if UI.sigil then return UI.sigil.go end
 if not UI.K.ready then return nil end
 local q=UI.fxQuad('TrialSigil',UI.K.tex.sigil,UnityEngine.Color(1,1,1,.9),1)
 if not q then return nil end
 UI.sigil=q
 return q.go
end
function SetSigilAlpha(a)if UI.sigil then UI.sigil.mat.color=UnityEngine.Color(1,1,1,a)end end

---------------------------------------------------------------- v15：唤龙。龙从雪山飞到祭坛落地，等人骑上去；多人房间里同一时间只有一位龙骑能唤龙
DR.slack=2.5
function DR.altarSpot()
 local ax,az=DR.ALTAR[1],DR.ALTAR[2]
 local keep=DR.yaw
 local found=nil
 for _,slack in ipairs({2.5,4.5,7})do
  DR.slack=slack
  for _,r in ipairs({18,22,27,33})do
   for k=0,11 do
    local a=k*math.pi/6
    local x,z=ax+math.sin(a)*r,az+math.cos(a)*r
    for _,turn in ipairs({90,-90})do
     -- 龙身横在祭坛外圈，不压到石柱
     DR.yaw=math.deg(math.atan(ax-x,az-z))+turn
     local h=DR.landingHeight(x,z)
     if h then found={Vector3(x,h,z),DR.yaw};break end
    end
    if found then break end
   end
   if found then break end
  end
  if found then break end
 end
 DR.slack=2.5;DR.yaw=keep
 if found then return found[1],found[2]end
end
function DR.goHome()
 DR.dest,DR.destHome,DR.destYaw,DR.arriving,DR.summoning=DR.home,true,DR.homeYaw,false,false
 DR.takeoff(true)
end
function DR.release()
 DR.claimed=false
 local c=DR.phase1.cycle;if c then pcall(c.DragonRelease)end
end
function DR.summon(actor)
 if not DR.parts or not DR.v8 then toast('墨曜还没准备好');return end
 if not CanRideDragon()then toast('龙魂尚未苏醒');return end
 if DR.state=='await'then
  if DR.nearAwait then DR.rideTap=true else toast('墨曜在唤龙祭坛等你')end
  return
 end
 if DR.state~='perch'then toast(DR.rider and '你正骑着墨曜' or '墨曜正在路上');return end
 if DR.remoteOn then toast('墨曜正在回应另一位龙骑，请稍后');return end
 local ex=DR.phase1.explore
 if ex and ex.IsBattleActive()then toast('战斗结束后再唤龙');return end
 local c=DR.phase1.cycle
 if c then local ok,why=c.DragonClaim();if not ok then toast(why or '墨曜正在回应另一位龙骑，请稍后');return end end
 local spot,yaw=DR.altarSpot()
 if not spot then toast('祭坛附近没有落脚的地方');DR.release();return end
 DR.claimed=true
 DR.dest,DR.destYaw,DR.destHome,DR.summoning,DR.arriving=spot,yaw,false,true,false
 DR.cool=1
 DR.takeoff(true)
 toast('墨曜听见了你的呼唤，正从雪山飞来')
end
-- 龙魂苏醒：一团魂光从蛋里升起，飞回雪山，随后墨曜第一次飞来祭坛
function DragonAwaken()
 if DR.soul or not DR.parts then return end
 local q=UI.fxQuad('DragonSoul',UI.K.ready and UI.K.tex.vortex or nil,UnityEngine.Color(.75,.95,1,1),3.2)
 local lg=UnityEngine.GameObject('DragonSoulLight');local light=lg:AddComponent(typeof(UnityEngine.Light))
 light.type=UnityEngine.LightType.Point;light.color=UnityEngine.Color(.6,.9,1,1);light.range=18;light.intensity=4;light.shadows=UnityEngine.LightShadows.None
 DR.soul={t=0,quad=q,light=lg,from=Vector3(DR.ALTAR[1],DR.ground(DR.ALTAR[1],DR.ALTAR[2])+2.5,DR.ALTAR[2]),to=DR.home+Vector3(0,12,0)}
 toast('龙魂离开了蛋壳，飞向雪山')
end
function DR.updateSoul(actor)
 local S=DR.soul;if not S then return end
 S.t=S.t+Time.deltaTime
 local u=math.min(1,S.t/6)
 local e=u*u*(3-2*u)
 local p=Vector3.Lerp(S.from,S.to,e)+Vector3(0,math.sin(u*math.pi)*26,0)
 S.light.transform.position=p
 if S.quad then
  local cam=UnityEngine.Camera.main
  if cam then S.quad.go.transform.rotation=Quaternion.LookRotation(p-cam.transform.position)*Quaternion.Euler(0,0,Time.time*220)end
  S.quad.go.transform.position=p
  local s=3.2+math.sin(Time.time*9)*.5+u*3
  S.quad.go.transform.localScale=Vector3(s,s,1)
 end
 if S.t>1 and S.t<1.1 then pcall(function()DouyinCameraService.SetYaw(math.deg(math.atan(S.to.x-actor.position.x,S.to.z-actor.position.z)))end)end
 if u>=1 then
  if S.quad then UnityEngine.Object.Destroy(S.quad.go);UnityEngine.Object.Destroy(S.quad.mat)end
  UnityEngine.Object.Destroy(S.light);DR.soul=nil
  toast('魂归其身，墨曜睁开了眼睛')
  DR.summon(actor)
 end
end
function DR.updateSync(actor)
 local c=DR.phase1.cycle;if not c or not DR.parts or not DR.v8 then return end
 local okr,rem=pcall(c.DragonRemote)
 rem=okr and rem or nil
 if rem and DR.state=='perch'and not DR.claimed then
  -- 别的龙骑唤走了龙：这边按同步来的位置摆放
  local target=Vector3(rem.x,rem.y,rem.z)
  if not DR.remoteOn then DR.remoteOn=true;DR.pos=DR.home end
  DR.pos=Vector3.Lerp(DR.pos,target,math.min(1,Time.deltaTime*4))
  local diff=(rem.yaw-DR.yaw+540)%360-180
  DR.yaw=DR.yaw+diff*math.min(1,Time.deltaTime*4);DR.roll=0
  DR.place(0);DR.play(rem.idle==1 and 'idle' or 'fly',true)
 elseif DR.remoteOn then
  DR.remoteOn=false;DR.yaw=DR.homeYaw;DR.clip=nil
 end
 if DR.claimed then
  if DR.state=='perch'and not DR.summoning then DR.release();return end
  DR.syncT=(DR.syncT or 0)-Time.deltaTime
  if DR.syncT<=0 then
   DR.syncT=.3
   pcall(c.DragonPose,DR.pos.x,DR.pos.y,DR.pos.z,DR.yaw,(DR.state=='await'or DR.state=='rest')and 1 or 0)
   -- 两人同时唤龙时由房主裁决，没抢到的一方让龙回山
   local oko,owner=pcall(c.DragonOwner)
   if oko and owner and owner~=''and owner~=tostring(actor.actorID)and not DR.rider and DR.state~='perch'then
    DR.claimed=false;toast('墨曜正在回应另一位龙骑，请稍后');DR.goHome()
   end
  end
 end
end

---------------------------------------------------------------- v15：包住主循环
DR.phase1.v15Update=Update
function Update()
 DR.phase1.v15Update()
 local s=DR.phase1
 if not s.prules then s.prules=s.scope:GetScript('dragon_progress_rules.lua')end
 local a=DouyinActorService.GetLocalActor();if not a then return end
 if not UI.vortex.failed then
  local ok,err=pcall(UI.updateVortex);if not ok then UI.vortex.failed=true;report('vortex '..tostring(err))end
 end
 if not DR.syncFailed then
  local ok,err=pcall(DR.updateSync,a);if not ok then DR.syncFailed=true;report('dragon sync '..tostring(err))end
 end
 if DR.soul then
  local ok,err=pcall(DR.updateSoul,a);if not ok then DR.soul=nil;report('soul '..tostring(err))end
 end
end
function LateUpdate()
 if DR.v8 and DR.rider then DR.align(DR.rider) end
 local ok,err=pcall(UI.dizzyLate)
 if not ok and not UI.dizzy.err then UI.dizzy.err=true;report('dizzy '..tostring(err))end
end

---------------------------------------------------------------- v16：加密的麦簇也登记进随风摆动的名单
function UI.addReedNames()for i=260,349 do UI.reeds.names[#UI.reeds.names+1]='golden_geometry_'..i end end
UI.addReedNames()
