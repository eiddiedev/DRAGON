---@id 313ebddc-058f-40f1-be60-76f6a590e9f8
---@referenceName dragon_combat.lua
---@displayName 龙眠魔法阵遭遇战
---@start
---@var PreviewMode:boolean=false
---@name 独立验证模式
---@var ArenaX:number=157
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
local Spawn=require('official.core.spawn')
local engine,rpg,fx,rules
local state=nil
local netReady=false
local previewCenter=nil
local visuals={}
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
 local hits=U.Physics.RaycastAll(V(x,a.position.y+10,z),V.down,80,1,U.QueryTriggerInteraction.Ignore)
 local y=a.position.y;local nearest=1e9
 for i=0,hits.Length-1 do local hit=hits[i];if hit.normal.y>.45 and hit.distance<nearest then y=hit.point.y;nearest=hit.distance end end
 return y
end
local function center(a)
 if PreviewMode then if not previewCenter then local p=a.position;previewCenter=V(p.x,ground(p.x,p.z+3,a),p.z+3)end;return previewCenter end
 return V(ArenaX,ground(ArenaX,ArenaZ,a),ArenaZ)
end
local function active()return state and(state.phase=='ready'or state.phase=='active')end
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
  local c=center(a);if V.Distance(V(a.position.x,c.y,a.position.z),c)>ArenaRadius then return end
  if not active()then serial=serial+1;state=engine.New(c.x,c.y,c.z,ArenaRadius,tostring(os.time())..':'..q.id..':'..serial)end
  engine.Join(state,q.id,q.class,{x=a.position.x,z=a.position.z});publish();return
 end
 if not state or q.epoch~=state.epoch then return end
 engine.Request(state,q.id,q.seq,q.kind,q.dx,q.dz);publish()
end
function Begin()
 local a=localActor();local profile=rpg and rpg.GetProfile()
 if not a or not profile or not profile.class then return false,'先在古书选择职业'end
 if not engine or not scope:GetGameObjectByPath('ShadowSpiritSource')then return false,'影灵正在准备'end
 local c=center(a);if V.Distance(V(a.position.x,c.y,a.position.z),c)>ArenaRadius then return false,'请走近麦田旁的魔法阵'end
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
 return {phase=state and state.phase or 'idle',hp=m and m.hp,maxHP=m and m.maxHP,shield=m and math.max(0,m.shield-state.t),enemyCount=alive,epoch=state and state.epoch,time=state and state.t,netReady=netReady,authority=authority(),preview=PreviewMode,damage=m and m.damage,ack=m and m.ack}
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
 for _,v in pairs(visuals)do if v.go then Spawn.destroy(v.go)end;for _,m in ipairs(v.materials or{})do U.Object.Destroy(m)end end;visuals={}
end
local function syncVisuals()
 if not state then return end
 local source=scope:GetGameObjectByPath('ShadowSpiritSource');if not source then return end
 source.transform.localPosition=V(0,-500,0)
 for _,e in ipairs(state.enemies)do
  local v=visuals[e.id]
  if not v and e.hp>0 then
   local go=Spawn.spawn(self,'ShadowSpiritSource',{networked=false});if go then
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
    v={go=go,materials=materials,bar=bar,bars=bars};visuals[e.id]=v
   end
  end
  if v then
   v.go:SetActive(e.hp>0 and active())
   if e.hp>0 then
    local desired=V(e.x,state.y+.15+math.sin(state.t*2+e.id)*.04,e.z)
    local before=v.go.transform.position;v.go.transform.position=V.Lerp(before,desired,math.min(1,U.Time.deltaTime*14))
    if before.y<state.y-10 then v.go.transform.position=desired end
    local a=localActor();if a then local d=a.position-desired;d.y=0;if d.sqrMagnitude>.01 then v.go.transform.rotation=Q.LookRotation(d,V.up)end end
    local scale=e.elite and 1.4 or .95;v.go.transform.localScale=V.one*scale
    if v.bar then
     v.bar.transform.position=desired+V(0,scale*1.15,0);if U.Camera.main then v.bar.transform.rotation=U.Camera.main.transform.rotation end
     v.bars[1].transform.localScale=V(.7,.07,.02);v.bars[2].transform.localScale=V(.68*e.hp/e.maxHP,.045,.025)
     v.bars[2].transform.localPosition=V(-.34*(1-e.hp/e.maxHP),0,-.02)
    end
    local anim=v.go:GetComponentInChildren(typeof(CS.ModularAnim.Runtime.UGCAnimator),true)
    local desiredAnim=e.state=='chase'and 'FloatMove'or 'Idle'
    if anim and anim.Controller and v.anim~=desiredAnim then if anim:Play(desiredAnim)then v.anim=desiredAnim end end
    for _,mat in ipairs(v.materials)do if mat:HasProperty('_EmissionPower')then mat:SetFloat('_EmissionPower',e.hit>state.t and 2 or(e.state=='windup'and 1 or .08))end end
   end
  end
 end
 fx.SetArena(V(state.x,state.y+.06,state.z),state.radius,active())
 for _,event in ipairs(state.events)do if event.id>seenEvent then
  seenEvent=event.id
  local p=V(event.x or state.x,state.y+.6,event.z or state.z);local d=V(event.dx or 0,0,event.dz or 1)
  if event.type=='slash'then fx.Play('melee',event.skill and 'skill'or 'attack',p,d)
  elseif event.type=='shot'then fx.Play(event.class,'attack',p,d)
  elseif event.type=='blast'or event.type=='hit'or event.type=='tell'or event.type=='strike'then fx.Impact(event.type,p,event.damage or 0)
  end
 end end
end
function Update()
 if not engine then engine=scope:GetScript('dragon_combat_rules.lua');rpg=scope:GetScript('dragon_rpg.lua');fx=scope:GetScript('dragon_fx.lua');rules=scope:GetScript('dragon_rules.lua')end
 if not engine or not rpg or not fx or not rules then engine=nil;return end
 local a=localActor();if not a then return end
 center(a)
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
 lastActive=playing;rpg.SetContext({inBattle=playing,dead=m and m.hp<=0 and active()or false})
 if state and m and not resolved[state.epoch]and(state.phase=='victory'or state.phase=='defeat'or m.hp<=0)then
  resolved[state.epoch]=true;local p=rpg.GetProfile()
  if state.phase=='victory'then rules.RewardVictory(p,state.epoch,m.damage>0,m.hp>0)
  elseif not m.retreat then p.moon=math.floor(p.moon*.5)end
  if m.hp<=0 then a:Teleport(V(state.x-state.radius-1,state.y+.2,state.z))end
 end
 syncVisuals()
end
function OnDisable()
 local a=localActor();if a and flyWas then a:EnableFly()end;flyWas=nil;lastActive=false
 if rpg then rpg.SetContext({inBattle=false,dead=false})end
 if fx then fx.SetArena(V.zero,1,false)end;clearVisuals();pending={}
end
function OnDestroy()OnDisable()end
