---@id 6329c644-9169-4c74-b1c2-6cf72ca3dae4
---@referenceName dragon_fx.lua
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
---@var FrostEffect:UnityEngine.GameObject=nil
---@name 霜星冲击
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var MeteorEffect:UnityEngine.GameObject=nil
---@name 陨星冲击
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var BowSound:UnityEngine.AudioClip=nil
---@name 射箭音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BowSoundVolume:number=0.65
---@name 射箭音量
---@var BowSoundMaxDistance:number=25
---@name 射箭最大作用范围
---@var EnemySound:UnityEngine.AudioClip=nil
---@name 怪物攻击音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var EnemySoundVolume:number=0.65
---@name 怪物攻击音量
---@var EnemySoundMaxDistance:number=25
---@name 怪物攻击最大作用范围
---@var HurtSound:UnityEngine.AudioClip=nil
---@name 受伤音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var HurtSoundVolume:number=0.65
---@name 受伤音量
---@var HurtSoundMaxDistance:number=25
---@name 受伤最大作用范围
---@var BankSwordSwing:UnityEngine.AudioClip=nil
---@name 挥剑音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankSwordSwingVolume:number=0.48
---@name 挥剑音量
---@var BankSwordSwingMaxDistance:number=25
---@name 挥剑作用范围
---@var BankSwordHit:UnityEngine.AudioClip=nil
---@name 剑击音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankSwordHitVolume:number=0.48
---@name 剑击音量
---@var BankSwordHitMaxDistance:number=25
---@name 剑击作用范围
---@var BankGiantAwaken:UnityEngine.AudioClip=nil
---@name 巨力觉醒音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankGiantAwakenVolume:number=0.48
---@name 巨力觉醒音量
---@var BankGiantAwakenMaxDistance:number=25
---@name 巨力觉醒作用范围
---@var BankGiantHit:UnityEngine.AudioClip=nil
---@name 重击音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankGiantHitVolume:number=0.48
---@name 重击音量
---@var BankGiantHitMaxDistance:number=25
---@name 重击作用范围
---@var BankBowRelease:UnityEngine.AudioClip=nil
---@name 弓弦音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankBowReleaseVolume:number=0.48
---@name 弓弦音量
---@var BankBowReleaseMaxDistance:number=25
---@name 弓弦作用范围
---@var BankArrowHit:UnityEngine.AudioClip=nil
---@name 箭击音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankArrowHitVolume:number=0.48
---@name 箭击音量
---@var BankArrowHitMaxDistance:number=25
---@name 箭击作用范围
---@var BankLeafCharge:UnityEngine.AudioClip=nil
---@name 叶刃蓄力音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankLeafChargeVolume:number=0.48
---@name 叶刃蓄力音量
---@var BankLeafChargeMaxDistance:number=25
---@name 叶刃蓄力作用范围
---@var BankLeafWhoosh:UnityEngine.AudioClip=nil
---@name 叶刃破空音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankLeafWhooshVolume:number=0.48
---@name 叶刃破空音量
---@var BankLeafWhooshMaxDistance:number=25
---@name 叶刃破空作用范围
---@var BankLeafHit:UnityEngine.AudioClip=nil
---@name 叶刃命中音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankLeafHitVolume:number=0.48
---@name 叶刃命中音量
---@var BankLeafHitMaxDistance:number=25
---@name 叶刃命中作用范围
---@var BankRainFall:UnityEngine.AudioClip=nil
---@name 箭雨落下音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankRainFallVolume:number=0.48
---@name 箭雨落下音量
---@var BankRainFallMaxDistance:number=25
---@name 箭雨落下作用范围
---@var BankRainHit:UnityEngine.AudioClip=nil
---@name 箭雨命中音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankRainHitVolume:number=0.48
---@name 箭雨命中音量
---@var BankRainHitMaxDistance:number=25
---@name 箭雨命中作用范围
---@var BankMagicShot:UnityEngine.AudioClip=nil
---@name 奥术发射音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankMagicShotVolume:number=0.48
---@name 奥术发射音量
---@var BankMagicShotMaxDistance:number=25
---@name 奥术发射作用范围
---@var BankMagicHit:UnityEngine.AudioClip=nil
---@name 奥术命中音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankMagicHitVolume:number=0.48
---@name 奥术命中音量
---@var BankMagicHitMaxDistance:number=25
---@name 奥术命中作用范围
---@var BankMagicBurst:UnityEngine.AudioClip=nil
---@name 奥术爆发音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankMagicBurstVolume:number=0.48
---@name 奥术爆发音量
---@var BankMagicBurstMaxDistance:number=25
---@name 奥术爆发作用范围
---@var BankMeteorFall:UnityEngine.AudioClip=nil
---@name 陨星下落音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankMeteorFallVolume:number=0.48
---@name 陨星下落音量
---@var BankMeteorFallMaxDistance:number=25
---@name 陨星下落作用范围
---@var BankMeteorImpact:UnityEngine.AudioClip=nil
---@name 陨星撞击音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankMeteorImpactVolume:number=0.48
---@name 陨星撞击音量
---@var BankMeteorImpactMaxDistance:number=25
---@name 陨星撞击作用范围
---@var BankCannonFire:UnityEngine.AudioClip=nil
---@name 冲击发射音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankCannonFireVolume:number=0.48
---@name 冲击发射音量
---@var BankCannonFireMaxDistance:number=25
---@name 冲击发射作用范围
---@var BankCannonExplode:UnityEngine.AudioClip=nil
---@name 冲击爆炸音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankCannonExplodeVolume:number=0.48
---@name 冲击爆炸音量
---@var BankCannonExplodeMaxDistance:number=25
---@name 冲击爆炸作用范围
---@var BankTimeHit:UnityEngine.AudioClip=nil
---@name 时空命中音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankTimeHitVolume:number=0.48
---@name 时空命中音量
---@var BankTimeHitMaxDistance:number=25
---@name 时空命中作用范围
---@var BankWallBreak:UnityEngine.AudioClip=nil
---@name 破壁音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankWallBreakVolume:number=0.48
---@name 破壁音量
---@var BankWallBreakMaxDistance:number=25
---@name 破壁作用范围
---@var BankCoin:UnityEngine.AudioClip=nil
---@name 奖励音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankCoinVolume:number=0.48
---@name 奖励音量
---@var BankCoinMaxDistance:number=25
---@name 奖励作用范围
---@var BankDash:UnityEngine.AudioClip=nil
---@name 闪避音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BankDashVolume:number=0.48
---@name 闪避音量
---@var BankDashMaxDistance:number=25
---@name 闪避作用范围
---@var MobileBudget:boolean=true
---@name 手机特效预算
local U=CS.UnityEngine
local V=U.Vector3
local Effect=require('official.effect.playback')
local AudioClip=U.AudioClip
local logger=require('official.core.logger').create('dragon-combat-audio')
local function audioConfig()return {
 ['v2-sword-swing']={BankSwordSwing,BankSwordSwingVolume,BankSwordSwingMaxDistance},
 ['v2-sword-hit']={BankSwordHit,BankSwordHitVolume,BankSwordHitMaxDistance},
 ['v2-giant-awaken']={BankGiantAwaken,BankGiantAwakenVolume,BankGiantAwakenMaxDistance},
 ['v2-giant-hit']={BankGiantHit,BankGiantHitVolume,BankGiantHitMaxDistance},
 ['v2-bow-release']={BankBowRelease,BankBowReleaseVolume,BankBowReleaseMaxDistance},
 ['v2-arrow-hit']={BankArrowHit,BankArrowHitVolume,BankArrowHitMaxDistance},
 ['v2-leaf-charge']={BankLeafCharge,BankLeafChargeVolume,BankLeafChargeMaxDistance},
 ['v2-leaf-whoosh']={BankLeafWhoosh,BankLeafWhooshVolume,BankLeafWhooshMaxDistance},
 ['v2-leaf-hit']={BankLeafHit,BankLeafHitVolume,BankLeafHitMaxDistance},
 ['v2-rain-fall']={BankRainFall,BankRainFallVolume,BankRainFallMaxDistance},
 ['v2-rain-hit']={BankRainHit,BankRainHitVolume,BankRainHitMaxDistance},
 ['v2-magic-shot']={BankMagicShot,BankMagicShotVolume,BankMagicShotMaxDistance},
 ['v2-magic-hit']={BankMagicHit,BankMagicHitVolume,BankMagicHitMaxDistance},
 ['v2-magic-burst']={BankMagicBurst,BankMagicBurstVolume,BankMagicBurstMaxDistance},
 ['v2-meteor-fall']={BankMeteorFall,BankMeteorFallVolume,BankMeteorFallMaxDistance},
 ['v2-meteor-impact']={BankMeteorImpact,BankMeteorImpactVolume,BankMeteorImpactMaxDistance},
 ['v2-cannon-fire']={BankCannonFire,BankCannonFireVolume,BankCannonFireMaxDistance},
 ['v2-cannon-explode']={BankCannonExplode,BankCannonExplodeVolume,BankCannonExplodeMaxDistance},
 ['v2-time-hit']={BankTimeHit,BankTimeHitVolume,BankTimeHitMaxDistance},
 ['v2-wall-break']={BankWallBreak,BankWallBreakVolume,BankWallBreakMaxDistance},
 ['v2-coin']={BankCoin,BankCoinVolume,BankCoinMaxDistance},
 ['v2-dash']={BankDash,BankDashVolume,BankDashMaxDistance}
}end
local audioClips={}
local audioPool={}
local audioRoot=nil
local audioPlayed=0
local audioFailed=0
local audioLast=nil
local audioLastTime={}
local warmIndex=1
local function sound(name,gain)
 local now=U.Time.time;if audioLastTime[name]and now-audioLastTime[name]<.07 then return end
 local c=audioConfig()[name];local clip=c and c[1]
 if not clip then audioFailed=audioFailed+1;logger:warnOnce('missing-'..name,'audio asset unavailable',name);return end
 if c[2]<=0 or c[3]<=0 then return end
 local actor=CS.DouyinActorService.GetLocalActor()
 if not actor then return end
 if not audioRoot then audioRoot=U.GameObject('DragonCombatAudio')end
 local source=nil
 for _,v in ipairs(audioPool)do if not v.isPlaying then source=v;break end end
 local limit=MobileBudget and 4 or 8
 if not source and #audioPool<limit then local go=U.GameObject('CombatVoice'..#audioPool);go.transform:SetParent(audioRoot.transform,false);source=go:AddComponent(typeof(U.AudioSource));source.playOnAwake=false;source.spatialBlend=1;source.rolloffMode=U.AudioRolloffMode.Linear;source.loop=false;audioPool[#audioPool+1]=source end
 if not source then return end
 source.transform.position=actor.position;source.minDistance=math.min(2,c[3]*.1);source.maxDistance=c[3]
 source.volume=math.max(0,math.min(1,c[2]));source.mute=false;source.pitch=1;source:PlayOneShot(clip,gain or 1)
 audioLastTime[name]=now;audioPlayed=audioPlayed+1;audioLast=name
end
local originalSources={}
local function originalSound(kind,position)
 local config={Bow={BowSound,BowSoundVolume,BowSoundMaxDistance},Enemy={EnemySound,EnemySoundVolume,EnemySoundMaxDistance},Hurt={HurtSound,HurtSoundVolume,HurtSoundMaxDistance}}
 local c=config[kind];if not c or not c[1]or c[2]<=0 or c[3]<=0 then return end
 local v=originalSources[kind]
 if not v then local go=U.GameObject('OriginalCombatAudio_'..kind);local source=go:AddComponent(typeof(U.AudioSource));source.playOnAwake=false;source.spatialBlend=1;source.rolloffMode=U.AudioRolloffMode.Linear;v={go=go,source=source};originalSources[kind]=v end
 if v.clip~=c[1]then v.source:Stop();v.clip=c[1]end
 if v.source.isPlaying then return end
 v.go.transform.position=position;v.source.volume=math.max(0,math.min(1,c[2]));v.source.minDistance=math.min(2,c[3]*.1);v.source.maxDistance=c[3];v.source:PlayOneShot(c[1]);audioPlayed=audioPlayed+1;audioLast='original-'..kind
end
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
