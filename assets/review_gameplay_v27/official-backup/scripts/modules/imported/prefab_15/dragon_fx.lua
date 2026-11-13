---@id daa6dc08-7ce4-4f5f-9306-865c2510365a
---@sourceScriptId 6329c644-9169-4c74-b1c2-6cf72ca3dae4
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
 v.go.transform.position=position;v.source.volume=math.max(0,math.min(1,c[2]));v.source.minDistance=math.min(2,c[3]*.1);v.source.maxDistance=c[3];v.source:PlayOneShot(c[1]);audioPlayed=audioPlayed+1;audioLast='original-'..kind
end
local hurtFeel=nil
function Hurt(p)originalSound('Hurt',p);if hurtFeel then hurtFeel()end end
local flying={}
local queued={}
local arena=nil
local arenaKey=nil
local wantedArena=nil
local arenaRetry=0
local emitted=0
local failed=0
local lastReason=nil
-- v15：特效整体放大、叠层、带余爆；大招带屏幕闪光和镜头震动
local BOOM=1.55
local later={}
local bridge=nil
local scope15=require('official.core.runtime_scope').from(self)
local function feel(flash,shake,duration)
 if not bridge then bridge=scope15:GetScript('dragon_world_bridge.lua')end
 if bridge then pcall(function()bridge.ScreenFx(flash,shake,duration or .35)end)end
end
local function one(key,p,rotation,scale)
 if not key then return end
 local go,why=Effect.spawn(self,key,p,{rotation=rotation or U.Quaternion.identity,scale=(scale or 1)*BOOM})
 if go then emitted=emitted+1 else failed=failed+1;lastReason=why end
end
hurtFeel=function()if not bridge then bridge=scope15:GetScript('dragon_world_bridge.lua')end;if bridge then pcall(function()bridge.ScreenFx(.3,.6,.3,true)end)end end
local function after(delay,fn)later[#later+1]={at=U.Time.time+delay,fn=fn}end
local function ring(key,p,count,radius,scale,y)
 for i=1,count do local a=i*math.pi*2/count+radius;one(key,p+V(math.cos(a)*radius,y or .1,math.sin(a)*radius),nil,scale)end
end
-- v23: reuse finished flight effects; preserve particle sources and visible timing.
local flightPool={}
local flightCreated,flightReused,flightReleased=0,0,0
local function releaseFlight(entry)
 entry.h:Release();flightReleased=flightReleased+1
end
local function parkFlight(v)
 if v.entry then
  v.h:Stop(true);v.entry.busy=false;v.entry.idleAt=U.Time.time
 end
end
local function acquireFlight(key,p,d,scale)
 local entry=nil
 for _,e in ipairs(flightPool)do if not e.busy and e.key==key and e.h:GetGameObject()then entry=e;break end end
 if entry then
  local go=entry.h:GetGameObject()
  go.transform.position=p;go.transform.rotation=U.Quaternion.LookRotation(d,V.up)
  go.transform.localScale=entry.baseScale*scale
  if not entry.h:Play()then return nil,'effect-replay-not-ready' end
  entry.busy=true;flightReused=flightReused+1;return entry
 end
 local cap=MobileBudget and 10 or 26
 if #flightPool>=cap then
  for i,e in ipairs(flightPool)do if not e.busy then releaseFlight(e);table.remove(flightPool,i);break end end
 end
 if #flightPool>=cap then return nil,'flight-pool-busy' end
 local h,why=Effect.create(self,key,p,{rotation=U.Quaternion.LookRotation(d,V.up),scale=scale})
 if not h then return nil,why end
 local go=h:GetGameObject()
 if not go then h:Release();return nil,'effect-instance-missing' end
 entry={h=h,key=key,baseScale=go.transform.localScale/scale,busy=true}
 flightPool[#flightPool+1]=entry;flightCreated=flightCreated+1
 return entry
end
local function projectile(key,p,d,speed,life,pierce,scale)
 if not key or #flying>=(MobileBudget and 10 or 26) then return end
 local entry,why=acquireFlight(key,p,d,scale or 1.5)
 if not entry then failed=failed+1;lastReason=why;return end
 emitted=emitted+1
 flying[#flying+1]={h=entry.h,entry=entry,p=p,d=d,speed=speed,start=U.Time.time,life=life,pierce=pierce,stop=false}
end
function Charge(kind,action,p,target)
 if action=='attack'then return end
 if kind=='mage'and action=='skill3'then
  sound('v2-meteor-fall');local start=target+V(-3,14,-2)
  for i=0,2 do after(i*.12,function()projectile(BoltEffect,start+V(i*.8,i*1.2,0),(target-start).normalized,16,.95,false,2.6)end)end
  one(TellEffect,V(target.x,target.y-.5,target.z),nil,2.6)
 elseif kind=='mage'then one(HitEffect,p+V(0,.6,0),nil,1.3)
 elseif kind=='ranged'and action=='skill3'then sound('v2-rain-fall');one(TellEffect,V(target.x,target.y-.5,target.z),nil,2.4)
 elseif kind=='melee'and action=='skill3'then sound('v2-giant-awaken',.8);one(ShieldEffect,p-V(0,.45,0),nil,1.1);ring(HitEffect,p,6,1.4,.9,.4)
 elseif kind=='ranged'and action=='skill2'then sound('v2-leaf-charge',.75);one(HitEffect,p,nil,1.2)end
end
function Area(kind,action,p,burst)
 if kind=='ranged'then
  sound('v2-rain-hit',.8)
  for i=1,12 do local a=i*2.39996;local radius=.5+(i%4)*.8;local at=p+V(math.cos(a)*radius,0,math.sin(a)*radius)
   after(i*.035,function()projectile(ArrowEffect,at+V(0,7,0),V.down,34,.2,false,1.6);one(HitEffect,at,nil,1)end)
  end
  after(.45,function()one(BlastEffect,p,nil,1.3);ring(HitEffect,p,8,3,.9)end)
  feel(.16,.5,.45)
 elseif action=='skill2'then
  sound('v2-time-hit');one(FrostEffect,p,nil,1.9);ring(FrostEffect,p,5,2.4,.7)
  for i=1,10 do local a=i*math.pi/5;projectile(BoltEffect,p+V(0,.3,0),V(math.cos(a),.2,math.sin(a)),7,.5,false,1.3)end
  after(.25,function()one(FrostEffect,p,nil,1.2)end)
  feel(.14,.35,.3)
 elseif action=='skill3'then
  sound('v2-meteor-impact');one(MeteorEffect,p,nil,2.6);one(BlastEffect,p,nil,2.4);ring(HitEffect,p,10,2.6,1.4)
  after(.18,function()ring(BlastEffect,p,5,3.2,1.1);sound('v2-cannon-explode',.7)end)
  after(.4,function()ring(HitEffect,p,12,4.4,1.1);one(MeteorEffect,p,nil,1.5)end)
  feel(.4,1.4,.7)
 else
  sound('v2-magic-burst');one(BlastEffect,p,nil,2.1);ring(HitEffect,p,7,1.9,1.1)
  after(.16,function()one(BlastEffect,p+V(0,.4,0),nil,1.2);ring(HitEffect,p,5,3,.8)end)
  feel(.2,.6,.4)
 end
end
function Play(kind,action,origin,direction)
 local d=direction.sqrMagnitude>.001 and direction.normalized or V.forward
 local q=U.Quaternion.LookRotation(d,V.up)
 if action=='skill'then action='skill1'end
 if kind=='melee'then
  if action=='skill1'then
   sound('v2-giant-hit',.8);one(ShieldEffect,origin-V(0,.45,0),nil,2.3);ring(HitEffect,origin,8,2.6,1)
   after(.15,function()one(ShieldEffect,origin-V(0,.45,0),nil,3.2)end);feel(.18,.6,.4)
  elseif action=='skill2'then
   sound('v2-sword-swing')
   for i=0,5 do after(i*.05,function()one(SlashEffect,origin+V(0,.1*(i%2),0),q*U.Quaternion.Euler(0,i*60,i%2==0 and 12 or -12),1.7)end)end
   after(.2,function()ring(HitEffect,origin,8,3,1)end);feel(.1,.45,.35)
  elseif action=='skill3'then
   sound('v2-giant-hit')
   one(SlashEffect,origin,q*U.Quaternion.Euler(0,0,85),2.6);one(SlashEffect,origin,q*U.Quaternion.Euler(0,0,95),2.1)
   local hit=origin+d*2.6
   one(ShieldEffect,hit-V(0,.45,0),nil,2);one(BlastEffect,hit,nil,1.6);one(MeteorEffect,hit,nil,1.3)
   after(.12,function()for i=1,4 do one(HitEffect,origin+d*(1.5+i*1.1)-V(0,.3,0),nil,1.5)end;sound('v2-wall-break',.7)end)
   feel(.34,1.2,.6)
  else
   sound('v2-sword-swing');one(SlashEffect,origin+V(0,.05,0),q,1.45);one(SlashEffect,origin+V(0,.25,0),q*U.Quaternion.Euler(0,0,24),1.1)
  end
 elseif kind=='mage'then
  if action~='attack'then Area(kind,action,origin+d*6,1)else sound('v2-magic-shot',.8);one(HitEffect,origin+d*.6,nil,.9);projectile(BoltEffect,origin,d,18,.75,false,1.8)end
 else
  if action=='skill3'then Area(kind,action,origin+d*6,1)
  elseif action=='skill1'then for i=0,4 do queued[#queued+1]={at=U.Time.time+i*.16,p=origin,d=(q*U.Quaternion.Euler(0,(i-2)*3.5,0))*V.forward}end
  else originalSound('Bow',origin);one(HitEffect,origin+d*.5,nil,.7);projectile(ArrowEffect,origin,d,26,.75,action=='skill2',action=='skill2'and 2.4 or 1.6)
   if action=='skill2'then projectile(ArrowEffect,origin+V(0,.12,0),d,26,.75,true,2);projectile(BoltEffect,origin,d,26,.75,true,1.2);feel(.08,.3,.25)end end
 end
end
function Impact(kind,position,amount,class)
 if kind=='tell'then one(TellEffect,V(position.x,position.y-.5,position.z),nil,1.25)
 elseif kind=='blast'then one(BlastEffect,position,nil,1.6)
 elseif kind=='hit'then
  sound(class=='mage'and'v2-magic-hit'or(class=='ranged'and'v2-arrow-hit'or'v2-sword-hit'),.8)
  local big=(amount or 0)>=3
  one(HitEffect,position,nil,big and 1.8 or 1.25)
  if class=='mage'then one(BlastEffect,position,nil,big and 1.1 or .6)
  elseif class=='melee'then one(SlashEffect,position,U.Quaternion.Euler(0,math.random()*360,60),big and 1.2 or .8)
  else ring(HitEffect,position,3,.5,.6,.2)end
  if big then feel(.1,.4,.25)end
  -- End only nearby cosmetic flights; authoritative hit/damage lives in combat rules.
  for _,v in ipairs(flying)do
   if not v.stop then
    local age=U.Time.time-v.start;local p=v.p+v.d*(v.speed*math.min(age,v.life))
    if not v.pierce and (p-position).sqrMagnitude<1.5 then v.h:Stop();v.stop=true;v.release=U.Time.time+.35 end
   end
  end
 elseif kind=='strike'then originalSound('Enemy',position);one(HitEffect,V(position.x,position.y-.4,position.z),nil,.9)end
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

 for i=#queued,1,-1 do local q=queued[i];if now>=q.at then originalSound('Bow',q.p);projectile(ArrowEffect,q.p,q.d,26,.75,false,1.6);table.remove(queued,i)end end
 for i=#later,1,-1 do local q=later[i];if now>=q.at then table.remove(later,i);pcall(q.fn)end end
 for i=#flying,1,-1 do
  local v=flying[i];local age=now-v.start
  if not v.stop then
   local go=v.h:GetGameObject()
   if go then go.transform.position=v.p+v.d*(v.speed*math.min(age,v.life))end
   if age>=v.life then v.h:Stop();v.stop=true;v.release=now+.4 end
  elseif now>=v.release then parkFlight(v);table.remove(flying,i)end
 end
 -- Bound retained memory when combat has been idle; never interrupt live effects.
 for i=#flightPool,1,-1 do local e=flightPool[i];if not e.busy and now-(e.idleAt or now)>30 then releaseFlight(e);table.remove(flightPool,i)end end
 if wantedArena and not arena then SetArena(wantedArena.p,wantedArena.r,true)end
end
function GetStatus()
 local playing=0;for _,s in ipairs(audioPool)do if s.isPlaying then playing=playing+1 end end
 return{build='v23-flight-pool',flightPool={retained=#flightPool,created=flightCreated,reused=flightReused,released=flightReleased},audio={played=audioPlayed,failed=audioFailed,last=audioLast,playing=playing,warmed=warmIndex-1},available=Effect.isAvailable(),emitted=emitted,failed=failed,lastReason=lastReason,flying=#flying,arena=arena~=nil,refs={frost=FrostEffect~=nil,meteor=MeteorEffect~=nil,slash=SlashEffect~=nil,shield=ShieldEffect~=nil,bolt=BoltEffect~=nil,arrow=ArrowEffect~=nil,blast=BlastEffect~=nil,hit=HitEffect~=nil,tell=TellEffect~=nil}}
end
function Clear()
 for _,e in ipairs(flightPool)do releaseFlight(e)end;flightPool={};flying={}
 SetArena(V.zero,1,false);queued={};later={}
end
function OnDisable()Clear()end
function OnDestroy()
 for _,v in pairs(originalSources)do v.source:Stop();U.Object.Destroy(v.go)end;originalSources={}
 Clear();if audioRoot then U.Object.Destroy(audioRoot)end
 audioClips={};audioPool={}
end
