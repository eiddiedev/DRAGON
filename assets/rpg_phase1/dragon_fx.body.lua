---@displayName 龙眠职业粒子特效
---@var SlashEffect:UnityEngine.GameObject=nil
---@name 战士弧形刀光
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var ShieldEffect:UnityEngine.GameObject=nil
---@name 战士守护震波
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var BoltEffect:UnityEngine.GameObject=nil
---@name 法师飞弹拖尾
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var ArrowEffect:UnityEngine.GameObject=nil
---@name 游侠箭矢拖尾
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var BlastEffect:UnityEngine.GameObject=nil
---@name 奥术星爆
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var HitEffect:UnityEngine.GameObject=nil
---@name 命中火花
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var TellEffect:UnityEngine.GameObject=nil
---@name 敌袭地面预警
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var ArenaEffect:UnityEngine.GameObject=nil
---@name 试炼边界流光
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
local U=CS.UnityEngine
local V=U.Vector3
local Effect=require('official.effect.playback')
local flying={}
local queued={}
local arena=nil
local arenaKey=nil
local wantedArena=nil
local arenaRetry=0
local emitted=0
local failed=0
local lastReason=nil
local function one(key,p,rotation,scale)
 if not key then return end
 local go,why=Effect.spawn(self,key,p,{rotation=rotation or U.Quaternion.identity,scale=scale or 1})
 if go then emitted=emitted+1 else failed=failed+1;lastReason=why end
end
local function projectile(key,p,d,speed,life)
 if not key or #flying>=18 then return end
 local h,why=Effect.create(self,key,p,{rotation=U.Quaternion.LookRotation(d,V.up),scale=1})
 if not h then failed=failed+1;lastReason=why;return end
 emitted=emitted+1
 flying[#flying+1]={h=h,p=p,d=d,speed=speed,start=U.Time.time,life=life,stop=false}
end
function Play(kind,action,origin,direction)
 local d=direction.sqrMagnitude>.001 and direction.normalized or V.forward
 local q=U.Quaternion.LookRotation(d,V.up)
 if kind=='melee'then
  if action=='skill'then one(ShieldEffect,V(origin.x,origin.y-.45,origin.z),nil,1.4)
  else one(SlashEffect,V(origin.x,origin.y+.05,origin.z),q,1)end
 elseif kind=='mage'then
  if action=='skill'then Impact('blast',origin+d*6,0)else projectile(BoltEffect,origin,d,16,.75)end
 else
  if action=='skill'then for i=0,4 do queued[#queued+1]={at=U.Time.time+i*.16,p=origin,d=d}end
  else projectile(ArrowEffect,origin,d,24,.75)end
 end
end
function Impact(kind,position,amount)
 if kind=='tell'then one(TellEffect,V(position.x,position.y-.5,position.z),nil,1.1)
 elseif kind=='blast'then one(BlastEffect,position,nil,1.25)
 elseif kind=='hit'then
  one(HitEffect,position,nil,1)
  -- End only nearby cosmetic flights; authoritative hit/damage lives in combat rules.
  for _,v in ipairs(flying)do
   if not v.stop then
    local age=U.Time.time-v.start;local p=v.p+v.d*(v.speed*math.min(age,v.life))
    if (p-position).sqrMagnitude<1.5 then v.h:Stop();v.stop=true;v.release=U.Time.time+.35 end
   end
  end
 elseif kind=='strike'then one(HitEffect,V(position.x,position.y-.4,position.z),nil,.6)end
end
function SetArena(center,radius,visible)
 if not visible then wantedArena=nil;if arena then arena:Release();arena=nil;arenaKey=nil end;return end
 wantedArena={p=center,r=radius}
 if arenaKey~=ArenaEffect and arena then arena:Release();arena=nil end
 if not arena and ArenaEffect and U.Time.time>=arenaRetry then
  local why;arena,why=Effect.create(self,ArenaEffect,center,{scale=radius})
  arenaRetry=U.Time.time+.5
  if arena then arenaKey=ArenaEffect else lastReason=why end
 end
end
function Update()
 local now=U.Time.time
 for i=#queued,1,-1 do local q=queued[i];if now>=q.at then projectile(ArrowEffect,q.p,q.d,24,.75);table.remove(queued,i)end end
 for i=#flying,1,-1 do
  local v=flying[i];local age=now-v.start
  if not v.stop then
   local go=v.h:GetGameObject()
   if go then go.transform.position=v.p+v.d*(v.speed*math.min(age,v.life))end
   if age>=v.life then v.h:Stop();v.stop=true;v.release=now+.4 end
  elseif now>=v.release then v.h:Release();table.remove(flying,i)end
 end
 if wantedArena and not arena then SetArena(wantedArena.p,wantedArena.r,true)end
end
function GetStatus()
 return{available=Effect.isAvailable(),emitted=emitted,failed=failed,lastReason=lastReason,flying=#flying,arena=arena~=nil,refs={slash=SlashEffect~=nil,shield=ShieldEffect~=nil,bolt=BoltEffect~=nil,arrow=ArrowEffect~=nil,blast=BlastEffect~=nil,hit=HitEffect~=nil,tell=TellEffect~=nil}}
end
function Clear()
 for _,v in ipairs(flying)do v.h:Release()end;flying={}
 SetArena(V.zero,1,false);queued={}
end
function OnDisable()Clear()end
function OnDestroy()Clear()end
