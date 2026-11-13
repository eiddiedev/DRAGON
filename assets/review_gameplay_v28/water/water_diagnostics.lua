---@id 930663d2-842e-43fa-a929-d88a8e697258
---@referenceName water_diagnostics.lua
---@displayName 水域只读诊断 water-v28
---@var ShowDiagnostics:boolean=false
-- Diagnostic only: no actor movement, collider writes, water registration, or UI.
-- See README.md for public API signatures and the limits of this evidence.
local U=CS.UnityEngine
local VERSION='water-v28'
local INTERVAL=1
local OVERLAP_LIMIT=12
local RAY_LIMIT=32
local ROOT_COLLIDER_LIMIT=8
local COMPONENT_LIMIT=16
local ANCESTOR_LIMIT=8
local FIND_AT={0,15,45}
local river={
 {77.3460541,41.5980377,253.073517},{76.987289452,41.406517009,235.574417},
 {80.4260711,37.3875657,219.4867097},{73.5425491,31.7575187,192.425873},
 {78.55059817,30.716095,173.371917},{88.2049179,32.0960997,152.155029},
 {97.714798,30.6084595,136.267899},{108.3557511,27.497921,123.755966},
 {124.7716441,29.1038971,115.621826},{140.5224762,32.3107147,118.027802},
 {153.5650341,30.2453995,109.557358},{168.1419841,31.3340377,110.401199},
 {187.1679541,26.8347626,103.331696}
}
local active=true
local destroyed=false
local nextSample=0
local startedAt=nil
local findAttempts=0
local root={sea=nil,river=nil}
local actor=nil
local subscriptions={start=false,stop=false}
local events={started=0,stopped=0,last='none',at=nil}
local errors={count=0,recent={}}
local snapshot={version=VERSION,status='waiting',reason='not-sampled',summary=VERSION..' 等待水域采样',samples=0}
local debugUI=nil
local uiAttempts=0
local uiRetryAt=0
local uiReason=nil

local function now()return U.Time.realtimeSinceStartup end
local function short(s,n)
 s=tostring(s or '');n=n or 160
 if #s<=n then return s end
 -- Do not cut a Chinese collider name in the middle of a UTF-8 character.
 while n>0 do local b=string.byte(s,n+1);if not b or b<128 or b>=192 then break end;n=n-1 end
 return string.sub(s,1,n)
end
local function errorReason(key,value)
 errors.count=errors.count+1
 errors.recent[#errors.recent+1]={reason=key,detail=short(value)}
 if #errors.recent>6 then table.remove(errors.recent,1)end
end
local function finite(v)return type(v)=='number'and v==v and v~=math.huge and v~=-math.huge end
local function vector(v)
 if not v or not finite(v.x)or not finite(v.y)or not finite(v.z)then return nil end
 return {x=v.x,y=v.y,z=v.z}
end
local function alive(v)
 if v==nil then return false end
 local ok,id=pcall(function()return v:GetInstanceID()end)
 return ok and id~=nil and id~=0
end
local function copy(v)
 if type(v)~='table'then return v end
 local result={};for k,x in pairs(v)do result[k]=copy(x)end;return result
end
local function markStart()events.started=events.started+1;events.last='start';events.at=now()end
local function markStop()events.stopped=events.stopped+1;events.last='stop';events.at=now()end
local function unbindActor()
 if actor then
  if subscriptions.start then
   local ok,e=pcall(function()actor.onSwimStart:RemoveListener(markStart)end)
   if not ok then errorReason('remove-swim-start',e)end
  end
  if subscriptions.stop then
   local ok,e=pcall(function()actor.onSwimStop:RemoveListener(markStop)end)
   if not ok then errorReason('remove-swim-stop',e)end
  end
 end
 subscriptions={start=false,stop=false};actor=nil
end
local function bindActor(value)
 if value==actor then return end
 unbindActor();actor=value
 if not actor then return end
 local ok,e=pcall(function()actor.onSwimStart:AddListener(markStart)end)
 subscriptions.start=ok;if not ok then errorReason('add-swim-start',e)end
 ok,e=pcall(function()actor.onSwimStop:AddListener(markStop)end)
 subscriptions.stop=ok;if not ok then errorReason('add-swim-stop',e)end
end

local function locateRoots(t)
 if alive(root.sea)and alive(root.river)then return end
 if findAttempts>=#FIND_AT or t-startedAt<FIND_AT[findAttempts+1]then return end
 findAttempts=findAttempts+1
 -- Only this call searches the scene; at most THREE calls during this script's
 -- lifetime, even across disable/re-enable. Descendant Find is path-local.
 local ok,e=pcall(function()
  local map=U.GameObject.Find('地图')
  if not map then return end
  local terrain=map.transform:Find('地形')
  if not terrain then return end
  local sea=terrain:Find('海洋')
  local r=terrain:Find('水体/PCGRiverEditor')
  if sea then root.sea=sea.gameObject end
  if r then root.river=r.gameObject end
 end)
 if not ok then errorReason('water-root-find',e)end
end
local function componentNames(go)
 local a=go:GetComponents(typeof(U.Component));local names={}
 for i=0,math.min(a.Length,COMPONENT_LIMIT)-1 do
  if a[i]then names[#names+1]=short(a[i]:GetType().Name,80)end
 end
 return names,a.Length>COMPONENT_LIMIT
end
local function ownerOf(c)
 local tr=c.transform
 local fallback=nil
 for _=1,ANCESTOR_LIMIT do
  if not tr then break end
  if alive(root.sea)and tr==root.sea.transform then return 'sea','cached-root'end
  if alive(root.river)and tr==root.river.transform then return 'river','cached-root'end
  local name=tr.gameObject.name
  if name=='海洋'then fallback='sea'end
  if name=='PCGRiverEditor'then fallback='river'end
  tr=tr.parent
 end
 -- Name-only evidence is explicitly labelled, never proof of native registration.
 return fallback,fallback and 'ancestor-name' or nil
end
local function colliderRecord(c)
 local b=c.bounds;local water,evidence=ownerOf(c)
 return {name=short(c.gameObject.name,80),id=c:GetInstanceID(),enabled=c.enabled,
  active=c.gameObject.activeInHierarchy,isTrigger=c.isTrigger,layer=c.gameObject.layer,
  colliderType=short(c:GetType().Name,64),center=vector(b.center),size=vector(b.size),
  water=water,waterEvidence=evidence}
end
local function isActorCollider(c)
 local tr=c.transform;local own=actor and actor.gameObject and actor.gameObject.transform
 return own~=nil and (tr==own or tr:IsChildOf(own))
end
local function rootRecord(go)
 if not alive(go)then return {found=false,reason='root-not-loaded'}end
 local result={found=true,name=short(go.name,80),active=go.activeInHierarchy,colliders={}}
 local ok,e=pcall(function()
  result.components,result.componentsTruncated=componentNames(go)
  local cols=go:GetComponents(typeof(U.Collider));result.rootColliderCount=cols.Length
  result.rootCollidersTruncated=cols.Length>ROOT_COLLIDER_LIMIT
  for i=0,math.min(cols.Length,ROOT_COLLIDER_LIMIT)-1 do result.colliders[#result.colliders+1]=colliderRecord(cols[i])end
 end)
 if not ok then result.reason='root-components-error';errorReason(result.reason,e)end
 return result
end
local function zoneFor(p)
 local best=math.huge;local surface=nil
 for i=1,#river-1 do
  local a,b=river[i],river[i+1];local dx,dz=b[1]-a[1],b[3]-a[3]
  local u=math.max(0,math.min(1,((p.x-a[1])*dx+(p.z-a[3])*dz)/(dx*dx+dz*dz)))
  local x,z=a[1]+u*dx,a[3]+u*dz;local d=(p.x-x)^2+(p.z-z)^2
  if d<best then best=d;surface=a[2]+u*(b[2]-a[2])end
 end
 if best<=14*14 and math.abs(p.y-surface)<=8 then return 'river',surface,math.sqrt(best)end
 if p.x>=0 and p.x<=255 and p.z>=0 and p.z<=255 and math.abs(p.y-27)<=5 then return 'sea',27,nil end
 return nil,nil,nil
end
local function boolText(v)if v==nil then return '?'end;return v and '1'or'0'end
local function makeSummary(s)
 if s.status~='sampled'then
  local words={away='远离水域',waiting='等待玩家',disabled='诊断暂停',error='采样异常'}
  return VERSION..' '..(words[s.status]or s.status)..' '..short(s.reason,60)
 end
 local support=s.support and s.support.name or '无'
 local zone=s.zone=='river'and'河'or'海'
 local cut=s.overlapTruncated and '+'or''
 return string.format('%s %s %.0f/%.0f 能%s 泳%s 水触%d%s 脚下:%s 进/出%d/%d%s',
  VERSION,zone,s.position.x,s.position.z,boolText(s.canSwim),boolText(s.isSwimming),
  s.observedWaterTriggers or 0,cut,short(support,36),events.started,events.stopped,
  s.reason~='ok'and(' '..short(s.reason,48))or'')
end
local function updateDiagnosticUI(t)
 local visible=ShowDiagnostics==true and snapshot.status=='sampled'
 if debugUI then
  debugUI.go:SetActive(visible)
  if visible then debugUI.text.text=snapshot.summary end
  return
 end
 if not visible or uiAttempts>=3 or t<uiRetryAt then return end
 uiAttempts=uiAttempts+1;uiRetryAt=t+15
 local made=nil
 local ok,e=pcall(function()
  -- Borrow only a native button's ready font. No global font/UI scan or new
  -- font texture, no GraphicRaycaster, and neither graphic accepts raycasts.
  local font=nil
  for _,name in ipairs({'CustomMain','Jump','HoldHands'})do
   local b=CS.DouyinUIService.GetInteractionButton(CS.UIType[name])
   if b then local label=b:GetComponentInChildren(typeof(U.UI.Text),true)
    if label and label.font then font=label.font;break end end
  end
  if not font then uiReason='native-font-not-ready';return end
  made=U.GameObject('WaterDiagnosticsV28')
  local canvas=made:AddComponent(typeof(U.Canvas));canvas.renderMode=U.RenderMode.ScreenSpaceOverlay;canvas.sortingOrder=260
  local scaler=made:AddComponent(typeof(U.UI.CanvasScaler))
  scaler.uiScaleMode=U.UI.CanvasScaler.ScaleMode.ScaleWithScreenSize
  scaler.referenceResolution=U.Vector2(1920,1080);scaler.matchWidthOrHeight=1
  local panel=U.GameObject('WaterDiagnosticLine');panel.transform:SetParent(made.transform,false)
  local rt=panel:AddComponent(typeof(U.RectTransform));rt.anchorMin=U.Vector2(.5,.5);rt.anchorMax=rt.anchorMin
  rt.sizeDelta=U.Vector2(1120,52);rt.anchoredPosition=U.Vector2(0,-150)
  local bg=panel:AddComponent(typeof(U.UI.Image));bg.color=U.Color(.04,.05,.07,.72);bg.raycastTarget=false
  local textGo=U.GameObject('Summary');textGo.transform:SetParent(panel.transform,false)
  local tr=textGo:AddComponent(typeof(U.RectTransform));tr.anchorMin=U.Vector2(0,0);tr.anchorMax=U.Vector2(1,1)
  tr.offsetMin=U.Vector2(12,0);tr.offsetMax=U.Vector2(-12,0)
  local text=textGo:AddComponent(typeof(U.UI.Text));text.font=font;text.fontSize=22
  text.color=U.Color(1,1,1,1);text.alignment=U.TextAnchor.MiddleCenter;text.raycastTarget=false
  text.text=snapshot.summary;debugUI={go=made,text=text};uiReason=nil
 end)
 if not ok then
  if made then pcall(U.Object.Destroy,made)end
  uiReason='diagnostic-ui-error';errorReason(uiReason,e)
 end
end
local function sample(t)
 local s={version=VERSION,status='waiting',reason='actor-missing',samples=(snapshot.samples or 0)+1,
  sampledAt=t,findAttempts=findAttempts,events=copy(events),eventListeners=copy(subscriptions)}
 local ok,a=pcall(function()return CS.DouyinActorService.GetLocalActor()end)
 if not ok then unbindActor();errorReason('local-actor-query',a);s.reason='local-actor-query'else
  local good,isLocal=pcall(function()return a and a.isLocal==true end)
  if good and isLocal then bindActor(a)else unbindActor()end
 end
 if actor then
  local good,p=pcall(function()return vector(actor.position)end)
  if not good or not p then s.status='error';s.reason='actor-position-invalid'
  else
   s.position=p;s.zone,s.configuredSurfaceY,s.riverCenterDistance=zoneFor(p)
   if not s.zone then s.status='away';s.reason='outside-known-water-band'
   else
    s.status='sampled';s.reason='ok';s.nearby={};s.observedWaterTriggers=0
    local cOk,c=pcall(function()return actor:CanSwim()end)
    if cOk then s.canSwim=c else s.reason='can-swim-query';errorReason(s.reason,c)end
    local wOk,w=pcall(function()return actor:IsSwimming()end)
    if wOk then s.isSwimming=w else s.reason='swimming-query';errorReason(s.reason,w)end
    s.roots={sea=rootRecord(root.sea),river=rootRecord(root.river)}
    local oOk,o=pcall(function()
     return U.Physics.OverlapSphere(U.Vector3(p.x,p.y+.45,p.z),1.5,-1,U.QueryTriggerInteraction.Collide)
    end)
    if oOk and o then
     s.overlapTotal=o.Length;s.overlapTruncated=o.Length>OVERLAP_LIMIT
     -- Deliberately inspect only the FIRST 12, not 12 after filtering. An omitted
     -- collider cannot support a "no water trigger" conclusion when truncated.
     for i=0,math.min(o.Length,OVERLAP_LIMIT)-1 do
      local rOk,r=pcall(function()return colliderRecord(o[i])end)
      if rOk then
       r.isActor=isActorCollider(o[i]);s.nearby[#s.nearby+1]=r
       if r.water and r.isTrigger and not r.isActor then s.observedWaterTriggers=s.observedWaterTriggers+1 end
      else errorReason('overlap-collider-query',r);s.reason='overlap-collider-query'end
     end
    else s.reason='overlap-query';errorReason(s.reason,o)end
    local rOk,hits=pcall(function()
     return U.Physics.RaycastAll(U.Vector3(p.x,p.y+.75,p.z),U.Vector3.down,8,-1,U.QueryTriggerInteraction.Ignore)
    end)
    if rOk and hits then
     s.rayTotal=hits.Length;s.rayTruncated=hits.Length>RAY_LIMIT
     local nearest=nil
     for i=0,math.min(hits.Length,RAY_LIMIT)-1 do
      local h=hits[i]
      local hOk,eligible=pcall(function()
       return h.collider and not h.collider.isTrigger and not isActorCollider(h.collider)
        and h.point.y<=p.y+.35 and h.normal.y>.2
      end)
      if hOk and eligible and(not nearest or h.distance<nearest.distance)then nearest=h end
     end
     if nearest then
      local hOk,h=pcall(function()
       local v=colliderRecord(nearest.collider);v.hitPoint=vector(nearest.point)
       v.distance=nearest.distance;v.actorAboveSupport=p.y-nearest.point.y;return v
      end)
      if hOk then s.support=h else s.reason='support-query';errorReason(s.reason,h)end
     end
    else s.reason='raycast-query';errorReason(s.reason,hits)end
    if s.reason=='ok'and not s.roots[s.zone].found then s.reason='water-root-not-loaded'end
   end
  end
 end
 s.events=copy(events);s.eventListeners=copy(subscriptions);s.errors=copy(errors)
 s.summary=makeSummary(s);snapshot=s
end
function OnEnable()
 if destroyed then return end
 active=true
end
function Update()
 if not active or destroyed then return end
 local t=now();if t<nextSample then return end;nextSample=t+INTERVAL
 if not startedAt then startedAt=t end
 locateRoots(t)
 local ok,e=pcall(sample,t)
 if not ok then
  errorReason('sample-error',e)
  snapshot={version=VERSION,status='error',reason='sample-error',summary=VERSION..' 采样异常 sample-error',
   sampledAt=t,samples=(snapshot.samples or 0)+1,findAttempts=findAttempts,events=copy(events),errors=copy(errors)}
 end
 local uiOk,uiError=pcall(updateDiagnosticUI,t)
 if not uiOk then errorReason('diagnostic-ui-update',uiError);uiReason='diagnostic-ui-update'end
 snapshot.ui={enabled=ShowDiagnostics==true,created=debugUI~=nil,attempts=uiAttempts,reason=uiReason}
end
function GetWaterDiagnostics()return copy(snapshot)end
function GetWaterDiagnosticSummary()return snapshot.summary end
function OnDisable()
 active=false;unbindActor();snapshot.status='disabled';snapshot.reason='component-disabled'
 snapshot.events=copy(events);snapshot.eventListeners=copy(subscriptions);snapshot.summary=makeSummary(snapshot)
 if debugUI then pcall(function()debugUI.go:SetActive(false)end)end
end
function OnDestroy()
 active=false;destroyed=true;unbindActor();root={sea=nil,river=nil}
 snapshot.status='disabled';snapshot.reason='component-destroyed';snapshot.summary=makeSummary(snapshot)
 if debugUI then pcall(U.Object.Destroy,debugUI.go);debugUI=nil end
end
