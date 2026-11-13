---@id e11f9edb-bf6d-45db-af89-7515b0bae5ca
---@sourceScriptId 313ebddc-058f-40f1-be60-76f6a590e9f8
---@referenceName dragon_combat.lua
---@displayName 龙眠魔法阵遭遇战
---@start
---@var PreviewMode:boolean=false
---@name 独立验证模式
---@var ArenaX:number=133
---@name 魔法阵中心X
---@var ArenaZ:number=27
---@name 魔法阵中心Z
---@var ArenaRadius:number=10
---@name 魔法阵半径
---@varSync Encounter:string=""
---@hidden
---@end
local U=CS.UnityEngine
local V=U.Vector3
local Q=U.Quaternion
local json=dkjson
local scope=require('official.core.runtime_scope').from(self)
-- review-v27: private cache. Never replace the shared runtime-scope resolver.
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

local Spawn=require('official.core.spawn')
local engine,rpg,fx,rules
local state=nil
local netReady=false
local previewCenter=nil
local visuals={}
local shadowReady={source=nil,attempts=0,nextAt=0,status='pending',error=nil,spawnAttempts={}}
local function shadowSource()
 if shadowReady.source then return shadowReady.source end
 local now=U.Time.realtimeSinceStartup
 if shadowReady.attempts>=30 or now<shadowReady.nextAt then return nil end
 shadowReady.attempts=shadowReady.attempts+1;shadowReady.nextAt=now+1
 local go=scope:GetGameObjectByPath('ShadowSpiritSource')
 if go then
  local rs=go:GetComponentsInChildren(typeof(U.Renderer),true)
  for i=0,rs.Length-1 do
   local skin=rs[i].gameObject:GetComponent(typeof(U.SkinnedMeshRenderer))
   local mesh=rs[i].gameObject:GetComponent(typeof(U.MeshFilter))
   if (skin and skin.sharedMesh)or(mesh and mesh.sharedMesh)then shadowReady.source=go;shadowReady.status='ready';return go end
  end
 end
 if shadowReady.attempts==30 then shadowReady.status='failed';shadowReady.error='shadow mesh not loaded';print('[mobile-v23] shadow source failed')end
 return nil
end
function GetShadowDiagnostics()
 local count=0;for _,v in pairs(visuals)do if v.go and v.go.activeInHierarchy then count=count+1 end end
 return {build='mobile-v23',source=shadowReady.status,error=shadowReady.error,attempts=shadowReady.attempts,visible=count}
end

local seenEvent=0
local seenEpoch=nil
local published=0
local serial=0
local pending={}
local resolved={}
local flyWas=nil
local lastActive=false
local function id(a)return tostring(a.actorID)end
local function localActor()return CS.DouyinActorService.GetLocalActor()end
local function authority()return netReady and CS.DouyinNetService.isNetworkSettled and self:HasOwnership()end
local function ground(x,z,a)
 -- v15：先读地形高度（射线会打到树冠、麦子甚至天空罩，魔法阵就飘到看不见的地方去了）
 local okT,hT=pcall(function()local t=U.Terrain.activeTerrain;return t:SampleHeight(V(x,0,z))+t.transform.position.y end)
 if okT and hT and hT>1 then return hT end
 local hits=U.Physics.RaycastAll(V(x,400,z),V.down,600,1,U.QueryTriggerInteraction.Ignore)
 local y=a.position.y;local nearest=1e9
 for i=0,hits.Length-1 do local hit=hits[i];if hit.normal.y>.45 and hit.distance<nearest then y=hit.point.y;nearest=hit.distance end end
 return y
end
local function center(a)
 if PreviewMode then if not previewCenter then local p=a.position;previewCenter=V(p.x,ground(p.x,p.z+3,a),p.z+3)end;return previewCenter end
 return V(ArenaX,ground(ArenaX,ArenaZ,a),ArenaZ)
end
local function active()return state and(state.phase=='ready'or state.phase=='active')end
-- v15 对决场：裂隙之门通到的地下试炼场
local DUEL={x=127,z=172,r=9.5}
local bridge=nil
local function inDuelZone(a)return a.position.y<38 and(a.position.x-DUEL.x)^2+(a.position.z-DUEL.z)^2<=(DUEL.r+6)^2 end
function IsNearDuel()local a=CS.DouyinActorService.GetLocalActor();return a and inDuelZone(a)or false end
function IsDuel()return state~=nil and state.duel==true and active()==true end
function IsDuelOpen()return state~=nil and state.duel==true and state.phase=='ready'end
local function receive(value)
 if type(value)~='string'or value==''then return end
 local decoded=json.decode(value);if decoded and decoded.schema==1 then state=decoded end
end
local function publish()
 if netReady and authority()then Encounter:SetValue(json.encode(state))end
end
function OnNetSpawned()
 netReady=true
 Encounter:OnValueChange(function(value)receive(value)end);receive(Encounter:GetValue())
end
function OnNetDestroy()netReady=false end
function OnOwnershipTransferred()if netReady then receive(Encounter:GetValue())end end
local function request(packet)
 if not netReady or not CS.DouyinNetService.isNetworkSettled then return false end
 if authority()then ReceiveRequest(json.encode(packet))else self:SendMessageToOwner('ReceiveRequest',json.encode(packet))end;return true
end
function ReceiveRequest(raw)
 if not authority()or not engine or type(raw)~='string'or #raw>2048 then return end
 local q=json.decode(raw);if not q or type(q.id)~='string'then return end
 local a=CS.DouyinActorService.GetActorById(tonumber(q.id)or -1);if not a or a:IsSitting()or a:IsFlying()then return end
 if q.kind=='join'then
  if not engine.Classes()[q.class]then return end
  if q.duel then
   if not inDuelZone(a)then return end
   if active()and(not state.duel or state.phase~='ready')then return end
   if not active()then serial=serial+1;state=engine.New(DUEL.x,a.position.y,DUEL.z,DUEL.r,tostring(os.time())..':duel:'..q.id..':'..serial,true)end
   local jx,jz=engine.Boundary(state,a.position.x,a.position.z)
   engine.Join(state,q.id,q.class,{x=jx,z=jz});publish();return
  end
  if active()and state.duel then return end
  if not IsNight()then return end
  local c=center(a);if V.Distance(V(a.position.x,c.y,a.position.z),c)>ArenaRadius+2 then return end
  if not active()then serial=serial+1;state=engine.New(c.x,c.y,c.z,ArenaRadius,tostring(os.time())..':'..q.id..':'..serial)end
  local jx,jz=engine.Boundary(state,a.position.x,a.position.z)
  engine.Join(state,q.id,q.class,{x=jx,z=jz});publish();return
 end
 if not state or q.epoch~=state.epoch then return end
 engine.Request(state,q.id,q.seq,q.kind,q.dx,q.dz);publish()
end
function Configure(client,profileRules,effects,simulation)
 if not client or not client.GetProfile or not simulation or not simulation.Step then return false end
 rpg=client;rules=profileRules;fx=effects;engine=simulation;return true
end
function IsNight()local day=getDependency('dragon_daycycle.lua');return day and not day.IsDay()or false end
function IsNearArena()local a=localActor();if not a then return false end;local c=center(a);return (a.position.x-c.x)^2+(a.position.z-c.z)^2<=(ArenaRadius+2)^2 end
function Begin(duel)
 local a=localActor();local profile=rpg and rpg.GetProfile()
 if not a or not profile or not profile.class then return false,'先在古书选择职业'end
 if duel then
  if not engine then return false,'对决正在准备'end
  if not inDuelZone(a)then return false,'请先穿过裂隙之门，进入试炼场'end
  if active()and(not state.duel or state.phase~='ready')then return false,'请等这场战斗结束'end
  if not rpg.SetMode('combat')then return false,'请先结束当前操作'end
  local packet={kind='join',id=id(a),class=profile.class,duel=true};if not request(packet)then return false,'房间战斗尚未就绪'end
  pending.join={packet=packet,next=U.Time.time+.5,expires=U.Time.time+3};return true
 end
 if not IsNight()then return false,'晚上才能挑战影灵'end
 if not engine or not shadowSource()then return false,shadowReady.status=='failed'and '影灵资源加载失败，请重新进入世界'or '影灵正在准备'end
 if PreviewMode and not active()then previewCenter=nil end
 local c=center(a);if V.Distance(V(a.position.x,c.y,a.position.z),c)>ArenaRadius+2 then return false,'请走近麦田旁的魔法阵'end
 if active()and state.phase~='ready'then return false,'请等这场战斗结束'end
 if not rpg.SetMode('combat')then return false,'请先结束当前操作'end
 local packet={kind='join',id=id(a),class=profile.class};if not request(packet)then return false,'房间战斗尚未就绪'end
 pending.join={packet=packet,next=U.Time.time+.5,expires=U.Time.time+3};return true
end
function SendAction(action)
 local a=localActor();if not a or not active()or not state.members[id(a)]then return false end
 local packet={id=id(a),epoch=state.epoch,seq=action.sequence,kind=action.kind,dx=action.direction.x,dz=action.direction.z}
 request(packet);pending[tostring(action.sequence)]={packet=packet,next=U.Time.time+.25,expires=U.Time.time+.8};return true
end
function Retreat()
 local a=localActor();if not a or not active()then return end
 local m=state.members[id(a)];if m then request({id=id(a),epoch=state.epoch,seq=m.ack+1000,kind='retreat',dx=0,dz=1})end
end
function GetAim(direction,range)
 local a=localActor();if not a or not state or not engine then return nil end
 local e=engine.Aim(state,id(a),direction.x,direction.z,range);if e then return V(e.x,state.y+.7,e.z)end
end
function IsActive()return active()==true end
function IsParticipating()local a=localActor();local m=a and state and state.members[id(a)];return active()and m and m.hp>0 or false end
function GetStatus()
 local a=localActor();local m=a and state and state.members[id(a)]
 local alive=0;if state then for _,e in ipairs(state.enemies)do if e.hp>0 then alive=alive+1 end end end
 local foe,count=nil,0;if state and state.duel then for k,v in pairs(state.members)do count=count+1;if not a or k~=id(a)then foe=v end end end
 return {duel=state and state.duel or false,members=count,foeHp=foe and foe.hp,foeMax=foe and foe.maxHP,winner=state and state.winner,me=a and id(a),member=m~=nil,readyAt=state and state.readyAt,dependencies={engine=engine~=nil,rpg=rpg~=nil,fx=fx~=nil,rules=rules~=nil,profileClass=rpg and rpg.GetProfile()and rpg.GetProfile().class},stage=state and state.stage,phase=state and state.phase or 'idle',hp=m and m.hp,maxHP=m and m.maxHP,shield=m and math.max(0,m.shield-state.t),enemyCount=alive,epoch=state and state.epoch,time=state and state.t,netReady=netReady,authority=authority(),preview=PreviewMode,attackBoneCount=(function()local n=0;for _,v in pairs(visuals)do for _ in pairs(v.bones or{})do n=n+1 end end;return n end)(),damage=m and m.damage,ack=m and m.ack}
end
function GetSnapshot()return state end
function GetHUD()
 local s=GetStatus();if s.phase=='idle'then return '麦田试炼 · 走进魔法阵，迎战影灵'end
 if s.phase=='victory'then return s.damage and s.damage>0 and s.hp>0 and '影灵已散 · 月辉 +10'or '影灵已散 · 战斗结束'end
 if s.phase=='defeat'then return '心火暂熄 · 重整后可再挑战'end
 if s.phase=='ready'then return '魔法阵正在展开…'end
 return string.format('心火 %d / %d    影灵 %d%s',s.hp or 0,s.maxHP or 0,s.enemyCount,s.shield and s.shield>0 and '    圣盾' or '')
end
local function clearVisuals()
 for _,v in pairs(visuals)do if v.go then Spawn.destroy(v.go)end;for _,m in ipairs(v.materials or{})do U.Object.Destroy(m)end end;visuals={};shadowReady.spawnAttempts={}
end
local function syncVisuals()
 if not state then return end
 local source=shadowSource();if not source then return end
 source.transform.localPosition=V(0,-500,0)
 for _,e in ipairs(state.enemies)do
  local v=visuals[e.id]
  if not v and e.hp>0 then
   local retry=shadowReady.spawnAttempts[e.id]or{count=0,nextAt=0};shadowReady.spawnAttempts[e.id]=retry
   local go=nil
   if retry.count<10 and U.Time.time>=retry.nextAt then
    retry.count=retry.count+1;retry.nextAt=U.Time.time+.5
    local ok,result=pcall(Spawn.spawn,self,'ShadowSpiritSource',{networked=false,position=V(e.x,state.y+.15,e.z)})
    if ok then go=result else shadowReady.error=tostring(result);print('[mobile-v23] shadow spawn '..shadowReady.error)end
   end
   if go then
    go.name='BattleShadow_'..e.id;local cols=go:GetComponentsInChildren(typeof(U.Collider),true);for i=0,cols.Length-1 do cols[i].enabled=false end
    local materials={};local rs=go:GetComponentsInChildren(typeof(U.Renderer),true);for i=0,rs.Length-1 do local ms=rs[i].materials;for j=0,ms.Length-1 do materials[#materials+1]=ms[j]end end
    local bar=U.GameObject('Heartfire');bar.transform:SetParent(go.transform,false)
    local bars={}
    for index=1,2 do
     local part=U.GameObject.CreatePrimitive(U.PrimitiveType.Cube);part.name=index==1 and 'HealthTrack'or 'HealthFill';part.transform:SetParent(bar.transform,false)
     local col=part:GetComponent(typeof(U.Collider));col.enabled=false;U.Object.Destroy(col)
     local render=part:GetComponent(typeof(U.Renderer));render.shadowCastingMode=U.Rendering.ShadowCastingMode.Off
     local mat=U.Material(materials[1]);if mat:HasProperty('_BaseTex')then mat:SetTexture('_BaseTex',nil)end
     if mat:HasProperty('_BaseColor')then mat:SetColor('_BaseColor',index==1 and U.Color(.04,.025,.06,1)or U.Color(.8,.2,.5,1))end
     if mat:HasProperty('_EmissionPower')then mat:SetFloat('_EmissionPower',index==1 and 0 or .7)end
     render.sharedMaterial=mat;bars[index]=part;materials[#materials+1]=mat
    end
    v={go=go,materials=materials,bar=bar,bars=bars,bones={},animator=go:GetComponentInChildren(typeof(CS.ModularAnim.Runtime.UGCAnimator),true)};visuals[e.id]=v
    local ts=go:GetComponentsInChildren(typeof(U.Transform),true)
    for bi=0,ts.Length-1 do local t=ts[bi];if t.name=='Chest'or t.name=='Head'or t.name=='UpperArm_L'or t.name=='UpperArm_R'or t.name=='Forearm_L'or t.name=='Forearm_R'then v.bones[t.name]={t=t}end end
   end
  end
  if v then
   v.go:SetActive(e.hp>0 and active())
   if e.hp>0 then
    local desired=V(e.x,state.y+.15+math.sin(state.t*2+e.id)*.04,e.z)
    local before=v.go.transform.position;v.go.transform.position=V.Lerp(before,desired,math.min(1,U.Time.deltaTime*14))
    if before.y<state.y-10 then v.go.transform.position=desired end
    -- GLB source faces +X; Unity import reflects X, so the visible face is -X.
    -- Use replicated authoritative aim, never each viewer's local avatar.
    local d=V(e.faceX or 0,0,e.faceZ or 1)
    if d.sqrMagnitude>.001 then v.go.transform.rotation=Q.LookRotation(d,V.up)*Q.Euler(0,90,0)end
    local scale=e.boss and 1.75 or(e.elite and 1.25 or .95);v.go.transform.localScale=V.one*scale
    if v.bar then
     v.bar.transform.position=desired+V(0,scale*1.15,0);if U.Camera.main then v.bar.transform.rotation=U.Camera.main.transform.rotation end
     v.bars[1].transform.localScale=V(.7,.07,.02);v.bars[2].transform.localScale=V(.68*e.hp/e.maxHP,.045,.025)
     v.bars[2].transform.localPosition=V(-.34*(1-e.hp/e.maxHP),0,-.02)
    end
    v.enemy=e
    local anim=v.animator
    local desiredAnim=e.state=='chase'and 'FloatMove'or 'Idle'
    if anim and anim.Controller and v.anim~=desiredAnim then if anim:Play(desiredAnim)then v.anim=desiredAnim end end
    for _,mat in ipairs(v.materials)do if mat:HasProperty('_EmissionPower')then mat:SetFloat('_EmissionPower',e.hit>state.t and 2 or(e.state=='windup'and 1 or .08))end end
   end
  end
 end
 fx.SetArena(V(state.x,state.y+.08,state.z),state.radius,false)
 for _,event in ipairs(state.events)do if event.id>seenEvent then
  seenEvent=event.id
  local p=V(event.x or state.x,state.y+.6,event.z or state.z);local d=V(event.dx or 0,0,event.dz or 1)
  if event.type=='hit'and rpg.ShowDamage then rpg.ShowDamage(p,event.damage,false)end
  if event.type=='hurt'then local a=localActor();if a and event.owner==id(a)then if rpg.ShowDamage then rpg.ShowDamage(p,event.damage,true)end;fx.Hurt(p)end end
  if event.type=='slash'then fx.Play('melee',event.kind or 'attack',p,d)
  elseif event.type=='shot'then fx.Play(event.class,event.kind=='skill1'and 'attack'or event.kind,p,d)
  elseif event.type=='area'then fx.Area(event.class,event.kind,p,event.burst)
  elseif event.type=='action'then fx.Charge(event.class,event.kind,p,V(event.tx,state.y+.6,event.tz))
  elseif event.type=='blast'or event.type=='hit'or event.type=='tell'or event.type=='strike'then fx.Impact(event.type,p,event.damage or 0,event.class)
  end
 end end
end
-- Restore before the animator evaluates; additive rotations never accumulate.
local function restoreBones()
 for _,v in pairs(visuals)do for _,b in pairs(v.bones or{})do if b.base then b.t.localRotation=b.base;b.base=nil end end end
end
function LateUpdate()
 if not state then return end
 for _,v in pairs(visuals)do local e=v.enemy
  if e and e.hp>0 and(e.state=='windup'or e.state=='recover')and e.attackStart then
   local duration=e.attackDuration or .8;local elapsed=state.t-e.attackStart;local pull,hit=0,0
   if elapsed<duration then pull=math.min(1,elapsed/(duration*.7))
   else local t=elapsed-duration;hit=math.max(0,1-t/.55);pull=0 end
   local poses={Chest={-18*pull+28*hit,-22*pull+30*hit,0},Head={12*pull-15*hit,8*pull,0},UpperArm_R={-65*pull+85*hit,20*pull,-35*pull},Forearm_R={-70*pull+25*hit,0,0},UpperArm_L={-25*pull+48*hit,-12*pull,22*pull},Forearm_L={-38*pull+12*hit,0,0}}
   for name,p in pairs(poses)do local b=v.bones[name];if b then b.base=b.t.localRotation;b.t.localRotation=b.base*Q.Euler(p[1],p[2],p[3])end end
  end
 end
end
local sigilRoot,sigilMaterial,sigilLines,sigilAt=nil,nil,{},nil
-- v15：魔法阵改成一张贴地的发光图（地面已填平），由主脚本提供
local function showSigil(c,radius,on)
 if not bridge then bridge=getDependency('dragon_world_bridge.lua')end
 local go=bridge and bridge.GetSigil();if not go then return end
 if go.activeSelf~=on then go:SetActive(on)end
 if on then
  go.transform.position=V(c.x,c.y+.09,c.z);go.transform.rotation=Q.Euler(90,U.Time.time*5,0)
  go.transform.localScale=V(radius*2.1,radius*2.1,1);bridge.SetSigilAlpha(.72+.2*math.sin(U.Time.time*1.6))
 end
end
local function drawSigil(c)
 if not sigilRoot then
  sigilRoot=U.GameObject('TrialPermanentSigil');sigilMaterial=U.Material(U.Shader.Find('Sprites/Default'))
  local function line(name,points,width)
   local go=U.GameObject(name);go.transform:SetParent(sigilRoot.transform,false)
   local lr=go:AddComponent(typeof(U.LineRenderer));lr.useWorldSpace=true;
   local sampled={}
   for i=1,#points-1 do local a,b=points[i],points[i+1];local count=math.max(1,math.ceil((b-a).magnitude/.3))
    for j=0,count-1 do local p=c+V.Lerp(a,b,j/count);p.y=ground(p.x,p.z,localActor())+.10;sampled[#sampled+1]=p end
   end
   local p=c+points[#points];p.y=ground(p.x,p.z,localActor())+.10;sampled[#sampled+1]=p
   lr.positionCount=#sampled;lr.startWidth=width;lr.endWidth=width;lr.material=sigilMaterial
   lr.startColor=U.Color(.48,.35,1,.8);lr.endColor=U.Color(.24,.7,1,.8);lr.shadowCastingMode=U.Rendering.ShadowCastingMode.Off
   for i,p in ipairs(sampled)do lr:SetPosition(i-1,p)end;sigilLines[#sigilLines+1]=lr
  end
  for _,radius in ipairs({ArenaRadius,ArenaRadius-.45,ArenaRadius*.66})do
   local points={};for i=0,128 do local t=i*math.pi*2/128;points[#points+1]=V(math.cos(t)*radius,0,math.sin(t)*radius)end
   line('RuneCircle',points,.065)
  end
  for k=0,1 do local points={};for i=0,3 do local t=(i*2/3+k/3)*math.pi;points[#points+1]=V(math.cos(t)*ArenaRadius*.65,0,math.sin(t)*ArenaRadius*.65)end;line('SixPointStar',points,.07)end
  for i=0,23 do
   local t=i*math.pi/12;local r=ArenaRadius*.83;local a=V(math.cos(t)*r,0,math.sin(t)*r);local across=V(-math.sin(t),0,math.cos(t));local outward=a.normalized
   line('RuneMark',{a-outward*.3,a+outward*.3,a+across*.22,a-outward*.1,a-across*.22},.055)
  end
 end
 sigilRoot.transform.position=V.zero
 local alpha=.65+.2*math.sin(U.Time.time*1.4)
 for _,lr in ipairs(sigilLines)do lr.startColor=U.Color(.48,.35,1,alpha);lr.endColor=U.Color(.24,.7,1,alpha)end
end
function Update()
 shadowSource()
 restoreBones()
 if not engine or not rpg or not fx or not rules then return end
 local a=localActor();if not a then return end
 local arenaCenter=center(a);local night=IsNight()
 if active()then showSigil(V(state.x,state.y,state.z),state.radius,true)
 else showSigil(arenaCenter,ArenaRadius,true)end
 if not active()then fx.SetArena(arenaCenter+V(0,.12,0),ArenaRadius,false)end
 if authority()and active()then
  local positions={};for key in pairs(state.members)do local other=CS.DouyinActorService.GetActorById(tonumber(key));if other then positions[key]={x=other.position.x,z=other.position.z}end end
  engine.Step(state,U.Time.deltaTime,positions,function(x,z,nx,nz)return U.Physics.Linecast(V(x,state.y+.6,z),V(nx,state.y+.6,nz),1,U.QueryTriggerInteraction.Ignore)end)
  published=published+U.Time.deltaTime;if published>.2 then published=0;publish()end
 end
 if state and seenEpoch~=state.epoch then clearVisuals();seenEpoch=state.epoch;seenEvent=0 end
 local m=state and state.members[id(a)];local playing=active()and m and m.hp>0 or false
 for key,p in pairs(pending)do
  if (key=='join'and m)or(key~='join'and m and m.ack>=p.packet.seq)or U.Time.time>p.expires then pending[key]=nil
  elseif U.Time.time>=p.next then p.next=U.Time.time+.25;request(p.packet)end
 end
 if playing then
  if not lastActive then flyWas=a:CanFly();a:DisableFly()end
  local x,z=engine.Boundary(state,a.position.x,a.position.z);if math.abs(x-a.position.x)+math.abs(z-a.position.z)>.01 then a:Teleport(V(x,a.position.y,z))end
 elseif lastActive then
  if flyWas then a:EnableFly()end;flyWas=nil
  rpg.SetMode('explore')
 end
 lastActive=playing;rpg.SetContext({inBattle=playing,dead=m and not m.retreat and m.hp<=0 and active()or false})
 if state and m and not resolved[state.epoch]and(state.phase=='victory'or state.phase=='defeat'or m.hp<=0)then
  local epoch=state.epoch
  if state.phase=='victory'and m.damage>0 and m.hp>0 and not state.duel then
   -- Retry pending rewards on subsequent frames; storage transaction owns deduplication.
   if rpg.AwardBattle then
    resolved[epoch]='saving'
    local ok=rpg.AwardBattle(epoch,10,function(saved)
     resolved[epoch]=saved and true or nil
    end)
    if not ok then resolved[epoch]=nil end
   end
  else resolved[epoch]=true end
  if m.hp<=0 then if state.duel then a:Teleport(V(state.x,state.y+.2,state.z-state.radius+1))else a:Teleport(V(state.x-state.radius-1,state.y+.2,state.z))end end
 end
 syncVisuals()
end
function OnDisable()
 local a=localActor();if a and flyWas then a:EnableFly()end;flyWas=nil;lastActive=false
 if rpg then rpg.SetContext({inBattle=false,dead=false})end
 if fx then fx.SetArena(V.zero,1,false)end;clearVisuals();pending={}
end
function OnDestroy()
 if sigilRoot then U.Object.Destroy(sigilRoot)end;if sigilMaterial then U.Object.Destroy(sigilMaterial)end;OnDisable()end

do local previous=OnDestroy;function OnDestroy()if previous then previous()end;ReleaseMobileDependencies()end end
