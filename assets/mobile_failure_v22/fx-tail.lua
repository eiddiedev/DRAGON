-- mobile-v22: bounded presentation only; combat damage/timing is owned by dragon_combat.
local pool={}
local MAX_POOL=6
local created=0
local emitted=0
local dropped=0
local failed=0
local lastReason=nil
local lastCreateFrame=-1
local arena=nil
local wantedArena=nil
local arenaRetry=0
local retryCount=0
local function releasePool()
 for _,v in ipairs(pool)do v.h:Stop();v.h:Release()end
 pool={}
end
local function take(key,p,rotation,scale,life,d,speed)
 if not key then failed=failed+1;lastReason='asset not ready';return end
 local now=U.Time.time
 local slot=nil
 for _,v in ipairs(pool)do if v.key==key and now>=v.reuseAt then slot=v;break end end
 if not slot then
  if U.Time.frameCount==lastCreateFrame then dropped=dropped+1;return end
  local idle=nil
  for i,v in ipairs(pool)do if now>=v.reuseAt then idle=i;break end end
  if #pool>=MAX_POOL then
   if not idle then dropped=dropped+1;return end
   pool[idle].h:Release();table.remove(pool,idle)
  end
  lastCreateFrame=U.Time.frameCount
  local h,why=Effect.create(self,key,p,{rotation=rotation or U.Quaternion.identity,scale=scale or 1})
  if not h then failed=failed+1;lastReason=why;return end
  slot={h=h,key=key};pool[#pool+1]=slot;created=created+1
 else
  local go=slot.h:GetGameObject()
  if not go then slot.reuseAt=math.huge;failed=failed+1;lastReason='effect object lost';return end
  go.transform.position=p;go.transform.rotation=rotation or U.Quaternion.identity
  go.transform.localScale=V.one*(scale or 1)
  slot.h:Play()
 end
 slot.p=p;slot.d=d;slot.speed=speed;slot.start=now;slot.stopAt=now+(life or .5)
 slot.reuseAt=slot.stopAt+.45;slot.stopped=false;emitted=emitted+1
end
local function one(key,p,rotation,scale)
 take(key,p,rotation,math.min(scale or 1,1.6),.5)
end
local function projectile(key,p,d,speed,life,scale)
 local flights=0
 for _,v in ipairs(pool)do if v.d and not v.stopped then flights=flights+1 end end
 if flights>=2 then dropped=dropped+1;return end
 take(key,p,U.Quaternion.LookRotation(d,V.up),math.min(scale or 1,1.4),math.min(life or .6,.65),d,speed)
end
-- Telegraphs use the existing tiny single-layer asset and retain their exact gameplay timing.
local function tell(p,scale)
 if TellEffect then Effect.spawn(self,TellEffect,p,{scale=scale or 1})end
end
function Hurt(p)originalSound('Hurt',p)end
function Charge(kind,action,p,target)
 if action=='attack'then return end
 if kind=='mage'and action=='skill3'then sound('v2-meteor-fall');tell(target-V(0,.5,0),2.6)
 elseif kind=='ranged'and action=='skill3'then sound('v2-rain-fall');tell(target-V(0,.5,0),2.4)
 elseif kind=='melee'and action=='skill3'then sound('v2-giant-awaken',.8);one(ShieldEffect,p-V(0,.45,0),nil,1)
 elseif kind=='ranged'and action=='skill2'then sound('v2-leaf-charge',.75);one(HitEffect,p,nil,.8)
 elseif kind=='mage'then one(HitEffect,p+V(0,.6,0),nil,.8)end
end
function Area(kind,action,p,burst)
 if kind=='ranged'then sound('v2-rain-hit',.8);one(BlastEffect,p,nil,1.2)
 elseif action=='skill2'then sound('v2-time-hit');one(FrostEffect,p,nil,1.4)
 elseif action=='skill3'then sound('v2-meteor-impact');one(MeteorEffect,p,nil,1.6)
 else sound('v2-magic-burst');one(BlastEffect,p,nil,1.3)end
end
function Play(kind,action,origin,direction)
 local d=direction.sqrMagnitude>.001 and direction.normalized or V.forward
 local q=U.Quaternion.LookRotation(d,V.up)
 if action=='skill'then action='skill1'end
 if kind=='melee'then
  if action=='skill1'then sound('v2-giant-hit',.8);one(ShieldEffect,origin-V(0,.45,0),nil,1.4)
  elseif action=='skill2'then sound('v2-sword-swing');one(SlashEffect,origin,q*U.Quaternion.Euler(0,0,20),1.4)
  elseif action=='skill3'then sound('v2-giant-hit');one(SlashEffect,origin,q*U.Quaternion.Euler(0,0,85),1.6)
  else sound('v2-sword-swing');one(SlashEffect,origin+V(0,.05,0),q,1)end
 elseif kind=='mage'then
  if action~='attack'then Area(kind,action,origin+d*6,1)
  else sound('v2-magic-shot',.8);projectile(BoltEffect,origin,d,18,.6,1)end
 else
  if action=='skill3'then Area(kind,action,origin+d*6,1)
  else originalSound('Bow',origin);projectile(ArrowEffect,origin,d,26,.6,action=='attack'and 1 or 1.3)end
 end
end
local lastHit=-1
function Impact(kind,position,amount,class)
 if kind=='tell'then tell(position-V(0,.5,0),1.25)
 elseif kind=='blast'then one(BlastEffect,position,nil,1.2)
 elseif kind=='hit'then
  sound(class=='mage'and'v2-magic-hit'or(class=='ranged'and'v2-arrow-hit'or'v2-sword-hit'),.8)
  if U.Time.time-lastHit>=.08 then one(HitEffect,position,nil,(amount or 0)>=3 and 1.2 or .8);lastHit=U.Time.time end
 elseif kind=='strike'then originalSound('Enemy',position);one(HitEffect,position-V(0,.4,0),nil,.8)end
end
function SetArena(center,radius,visible)
 if not visible then wantedArena=nil;if arena then arena:Release();arena=nil end;retryCount=0;return end
 wantedArena={p=center,r=radius}
 if not arena and ArenaEffect and U.Time.time>=arenaRetry and retryCount<5 then
  local why;arena,why=Effect.create(self,ArenaEffect,center,{scale=radius})
  arenaRetry=U.Time.time+1;retryCount=retryCount+1;if not arena then lastReason=why end
 end
end
function Update()
 local now=U.Time.time
 for _,v in ipairs(pool)do
  if not v.stopped then
   if v.d then local go=v.h:GetGameObject();if go then go.transform.position=v.p+v.d*(v.speed*math.min(now-v.start,v.stopAt-v.start))end end
   if now>=v.stopAt then v.h:Stop();v.stopped=true end
  end
 end
 if wantedArena and not arena then SetArena(wantedArena.p,wantedArena.r,true)end
end
function GetStatus()
 local active,flights,playing=0,0,0
 for _,v in ipairs(pool)do if not v.stopped then active=active+1;if v.d then flights=flights+1 end end end
 for _,s in ipairs(audioPool)do if s.isPlaying then playing=playing+1 end end
 return{build='mobile-v22-fx-only',audio={played=audioPlayed,failed=audioFailed,last=audioLast,playing=playing},pooled=#pool,active=active,created=created,emitted=emitted,dropped=dropped,failed=failed,lastReason=lastReason,flying=flights,arena=arena~=nil}
end
function Clear()releasePool();SetArena(V.zero,1,false)end
function OnDisable()Clear()end
function OnDestroy()
 Clear()
 for _,v in pairs(originalSources)do v.source:Stop();U.Object.Destroy(v.go)end;originalSources={}
 if audioRoot then U.Object.Destroy(audioRoot)end;audioPool={};audioClips={}
end
