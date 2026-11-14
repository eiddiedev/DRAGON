---@id 89aa39a9-fb6b-4f17-929f-bf10f36900aa
---@sourceScriptId 5a9edffe-7c92-477d-bc9c-9865e864567e
---@referenceName tripo_sheep_motion.lua
-- Physical sheep: preserve impulses instead of snapping to pasture coordinates.
---@displayName 可推动绵羊
local U=CS.UnityEngine
-- v27 bounded UGC animation requests. This file is inlined into each actor script.
-- It never patches shared scope functions and never changes the model/Controller.
local function createAnimationPlayer(owner, prefix)
 local s={wanted=nil,played=nil,anim=nil,controller=nil,nextProbe=0,nextPlay=0,deadline=0,
  attempts=0,successes=0,errors=0,status='idle',warnings={},disposed=false}
 local function warn(key,msg)
  if s.warnings[key] then return end;s.warnings[key]=true
  CS.UnityEngine.Debug.LogWarning('['..prefix..'] '..msg)
 end
 local function resetAttempt(now)
  s.nextProbe=0;s.nextPlay=0;s.deadline=now+60;s.attempts=0;s.status='waiting'
 end
 function s.request(name)
  if s.disposed then return end
  if s.wanted~=name then s.wanted=name;resetAttempt(CS.UnityEngine.Time.realtimeSinceStartup) end
 end
 function s.resume()
  s.disposed=false;s.anim=nil;s.controller=nil;s.played=nil
  resetAttempt(CS.UnityEngine.Time.realtimeSinceStartup)
 end
 function s.tick()
  if s.disposed or not s.wanted then return end
  local now=CS.UnityEngine.Time.realtimeSinceStartup
  if now>s.deadline and s.anim==nil then s.status='waiting animator';s.deadline=now+60 end
  if now>=s.nextProbe then
   s.nextProbe=now+1
   local ok,a=pcall(function()
    local typ=typeof(CS.ModularAnim.Runtime.UGCAnimator)
    -- Both saved actors own UGCAnimator on this exact root. A seated player
    -- becomes a child, so never scan children and accidentally acquire their animator.
    return owner:GetComponent(typ)
   end)
   if not ok then s.status='component error';s.errors=s.errors+1;warn('component',tostring(a));a=nil end
   if a~=s.anim then s.anim=a;s.controller=nil;s.played=nil;resetAttempt(now);s.nextProbe=now+1 end
  end
  local ok,controller=pcall(function()return s.anim and s.anim.enabled and s.anim.Controller or nil end)
  if not ok then s.errors=s.errors+1;warn('controller',tostring(controller));controller=nil end
  if controller~=s.controller then
   s.controller=controller;s.played=nil;resetAttempt(now)
  end
  if s.played==s.wanted and controller then s.status='playing';return end
  if now>s.deadline then s.deadline=now+60;s.attempts=0 end
  if now<s.nextPlay then return end;s.nextPlay=now+.5
  if not controller then s.status='waiting controller';return end
  s.attempts=s.attempts+1
  local good,played=pcall(function()return s.anim:Play(s.wanted)end)
  if good and played==true then
   s.played=s.wanted;s.successes=s.successes+1;s.status='playing'
  else
   s.status=good and 'clip unavailable' or 'play error'
   if not good then s.errors=s.errors+1 end
   warn(s.status..':'..s.wanted,s.status..' '..s.wanted..(good and '' or ': '..tostring(played)))
  end
 end
 function s.stop()s.disposed=true;s.anim=nil;s.controller=nil;s.played=nil end
 function s.diagnostics()
  return {wanted=s.wanted,played=s.played,status=s.status,attempts=s.attempts,successes=s.successes,errors=s.errors}
 end
 return s
end

-- v27: defer dynamic gravity until this sheep has real support below its saved spawn.
-- Initial scene physics should also be saved as kinematic/no-gravity (see SDK plan).
-- After support is ready the original dynamic/push behavior is restored.
local function createSheepGroundGuard(owner, body)
 local U=CS.UnityEngine
 local s={home=owner.transform.position,nextProbe=0,deadline=U.Time.realtimeSinceStartup+45,
  started=U.Time.realtimeSinceStartup,hits=0,probes=0,ready=false,status='waiting ground',lastError=nil,
  dynamicGravity=true,dynamicKinematic=false}
 body.velocity=U.Vector3.zero;body.angularVelocity=U.Vector3.zero
 body.isKinematic=true;body.useGravity=false
 function s.tick()
  if s.ready then return true end
  local now=U.Time.realtimeSinceStartup
  if now<s.nextProbe then return false end
  if now>s.deadline then
   s.status='ground timeout'
   if not s.warned then s.warned=true;U.Debug.LogWarning('[sheep-ground] '..owner.name..' has no loaded support; held at saved spawn')end
   -- A nearby player may arrive after streaming loads the pasture. No global scan.
   local a=DouyinActorService.GetLocalActor()
   if not a or (a.position-s.home).sqrMagnitude>50*50 then s.nextProbe=now+5;return false end
   s.deadline=now+10
  end
  s.nextProbe=now+.25;s.probes=s.probes+1
  local ok,supported=pcall(function()
   local hs=U.Physics.RaycastAll(s.home+U.Vector3(0,1.0,0),U.Vector3.down,4,-1,U.QueryTriggerInteraction.Ignore)
   for i=0,hs.Length-1 do local h=hs[i];local c=h.collider
    if c and not c.isTrigger and c.enabled and c.gameObject.activeInHierarchy then
     local t=c.transform
     if t~=owner.transform and not t:IsChildOf(owner.transform) and c.attachedRigidbody==nil
      and h.normal.y>.25 and h.point.y<=s.home.y+.5 and h.point.y>=s.home.y-2.5 then return true end
    end
   end
   return false
  end)
  if not ok then s.lastError=tostring(supported);s.status='ground query error';supported=false end
  s.hits=supported and s.hits+1 or 0
  if s.hits>=2 then
   -- Holding the model does not substitute a fake surface. Release only on two real hits.
   body.position=s.home;body.velocity=U.Vector3.zero;body.angularVelocity=U.Vector3.zero
   body.useGravity=s.dynamicGravity;body.isKinematic=s.dynamicKinematic
   s.ready=true;s.status='dynamic';return true
  end
  return false
 end
 return s
end

local rb,home,target=nil,nil,nil
local animationPlayer,groundGuard=nil,nil
local bodyNextAttempt,bodyAttempts=0,0
local started=false

local nextChoice,pushedUntil=0,0
local previousActor=nil
local nextPush=0
-- v31 备用步态：提审端平台动画不播时（腿骨一秒多没动），由脚本直接摆动四条腿的骨骼。
-- 不依赖动画资源；平台动画正常时它只做检测，不接管。
local function createGait(owner,tag)
 local g={legs={},on=false,probeT=0,probeMove=0,t=0,amp=0,axis=U.Vector3.right,nextSay=0,tries=0}
 local function bind()
  if g.bound then return true end
  local now=U.Time.realtimeSinceStartup
  if now<(g.nextBind or 0)then return false end;g.nextBind=now+1
  local ts=owner:GetComponentsInChildren(typeof(U.Transform),true)
  g.legs={}
  for i=0,ts.Length-1 do local t=ts[i]
   local a,side,idx=string.match(t.name,'^tripo::(%d)_(%a+)_Limb_(%d)$')
   if a and(idx=='0'or idx=='1')then g.legs[#g.legs+1]={t=t,base=t.localRotation,front=a=='0',left=side=='Left',upper=idx=='0'}end
  end
  if #g.legs>=4 then g.bound=true end
  return g.bound
 end
 function g.tick(moving,speed,dir,dt)
  local now=U.Time.realtimeSinceStartup
  if tag and now>=g.nextSay then g.nextSay=now+1
   pcall(function()U.PlayerPrefs.SetString('dr_diag_'..tag,tostring(g.status and g.status()or'-')..(g.on and'+步态'or'')..' 腿'..#g.legs)end)
  end
  if not bind()then return end
  if dir and dir.sqrMagnitude>.0001 then g.axis=U.Vector3.Cross(U.Vector3.up,dir.normalized)end
  if not g.on then
   if moving then
    local cur=g.legs[1].t.localRotation
    if g.prev then g.probeMove=g.probeMove+U.Quaternion.Angle(g.prev,cur)end
    g.prev=cur;g.probeT=g.probeT+dt
    if g.probeT>1.2 then
     if g.probeMove<1.5 then g.on=true;for _,l in ipairs(g.legs)do l.base=l.t.localRotation end end
     g.probeT=0;g.probeMove=0
    end
   else g.prev=nil;g.probeT=0;g.probeMove=0 end
   return
  end
  local want=moving and math.min(34,14+speed*3.5)or 0
  g.amp=g.amp+(want-g.amp)*math.min(1,dt*6)
  g.t=g.t+dt*(5+math.min(speed,8)*1.2)
  for _,l in ipairs(g.legs)do
   local phase=(l.front==l.left)and 0 or math.pi
   local a=math.sin(g.t+phase)*g.amp
   if not l.upper then a=-math.max(0,math.sin(g.t+phase+1.1))*g.amp*.8 end
   l.t.localRotation=l.base
   if math.abs(a)>.05 then l.t:Rotate(g.axis,a,U.Space.World)end
  end
 end
 return g
end
local gait=nil
local function play(name)
 if not animationPlayer then animationPlayer=createAnimationPlayer(self.gameObject,'sheep-animation') end
 animationPlayer.request(name);animationPlayer.tick()
end
local function acquireBody()
 if rb then return true end
 if U.Time.realtimeSinceStartup<bodyNextAttempt or bodyAttempts>=60 then return false end
 bodyNextAttempt=U.Time.realtimeSinceStartup+1;bodyAttempts=bodyAttempts+1
 rb=self.gameObject:GetComponent(typeof(U.Rigidbody))
 if not rb then
  if bodyAttempts==60 then U.Debug.LogWarning('[sheep-ground] missing body '..self.gameObject.name)end
  return false
 end
 local c=self.gameObject:GetComponent(typeof(U.CapsuleCollider))
 if not c then c=self.gameObject:AddComponent(typeof(U.CapsuleCollider));c.center=U.Vector3(0,.45,0);c.radius=.28;c.height=1.05;c.direction=2 end
 rb.constraints=U.RigidbodyConstraints.FreezeRotation
 groundGuard=createSheepGroundGuard(self.gameObject,rb)
 return true
end
function Start()
 home=self.transform.position;started=true
 acquireBody();play('Idle')
 nextChoice=U.Time.time+2+math.random()*4
end
function Update()
 if animationPlayer then animationPlayer.tick() end
 if started and not rb then acquireBody() end
end
function FixedUpdate()
 if not rb or not groundGuard or not groundGuard.tick() then return end
 local now=U.Time.time;local dt=U.Time.fixedDeltaTime;local p=rb.position
 local a=DouyinActorService.GetLocalActor()
 if a then
  local ap=a.position;local v=previousActor and (ap-previousActor)/math.max(dt,.001) or U.Vector3.zero;previousActor=ap
  local d=p-ap;d.y=0
  local radius=a:IsSitting() and 1.85 or 1.4
  if d.magnitude<radius and math.abs(p.y-ap.y)<2.5 and v.magnitude>.1 and v.magnitude<30 then
   local away=d.magnitude>.02 and d.normalized or v.normalized
   if U.Vector3.Dot(v,away)>0 and now>=nextPush then rb:AddForce(away*math.min(2.5,v.magnitude*.7),U.ForceMode.VelocityChange);nextPush=now+.3;pushedUntil=now+1.5;target=nil end
  end
 end
 if now>=nextChoice and now>=pushedUntil then
  nextChoice=now+3+math.random()*5
  if math.random()<.5 then target=nil else
   local angle=math.random()*6.283;target=p+U.Vector3(math.cos(angle)*3,0,math.sin(angle)*3)
  end
 end
 if target and now>=pushedUntil then
  local d=target-p;d.y=0
  if d.magnitude<.35 then target=nil else
   local hits=U.Physics.RaycastAll(p+U.Vector3(0,.65,0),d.normalized,1.1,-1,U.QueryTriggerInteraction.Ignore)
   local blocked=false
   for i=0,hits.Length-1 do local c=hits[i].collider;if c and not c.transform:IsChildOf(self.transform) and hits[i].normal.y<.5 then blocked=true end end
   if blocked then target=nil else
    local v=rb.velocity;local force=(d.normalized*.75-U.Vector3(v.x,0,v.z))*10
    rb:AddForce(force,U.ForceMode.Acceleration)
    local rotation=U.Quaternion.LookRotation(-d.normalized)
    rb:MoveRotation(U.Quaternion.Slerp(rb.rotation,rotation,dt*3))
   end
  end
 end
 local v=rb.velocity;play(v.x*v.x+v.z*v.z>.02 and 'Walk' or 'Idle')
 if not gait then gait=createGait(self.gameObject,'sheep');gait.status=function()return animationPlayer and animationPlayer.diagnostics().status or 'no-player' end end
 local sp=math.sqrt(v.x*v.x+v.z*v.z);pcall(gait.tick,sp>.14,sp*3,U.Vector3(v.x,0,v.z),U.Time.deltaTime)
end
function OnCollisionEnter(c)
 if rb and c.relativeVelocity.magnitude>.6 then pushedUntil=U.Time.time+1.5;target=nil end
end

function GetSheepDiagnostics()
 return {build='v27-sheep-ground',body=rb~=nil,bodyAttempts=bodyAttempts,
  ground=groundGuard and groundGuard.status or 'waiting body',groundProbes=groundGuard and groundGuard.probes or 0,
  groundError=groundGuard and groundGuard.lastError or nil,position=tostring(self.transform.position),
  animation=animationPlayer and animationPlayer.diagnostics() or nil}
end
function OnDisable()
 if animationPlayer then animationPlayer.stop() end
 if rb then rb.velocity=U.Vector3.zero;rb.isKinematic=true;rb.useGravity=false end
end
function OnEnable()
 if animationPlayer then animationPlayer.resume() end
 if started and rb then groundGuard=createSheepGroundGuard(self.gameObject,rb);previousActor=nil;target=nil end
end
function OnDestroy()if animationPlayer then animationPlayer.stop() end end
