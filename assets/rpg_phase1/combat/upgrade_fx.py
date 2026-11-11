from cli import D
from pathlib import Path
ref=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project_nuk7p7hj/scripts/modules/ms-audio.lua').read_text()
audio=ref[ref.index('local SAMPLE_RATE'):ref.index('local function ensureSource')]
# Keep original recipes and safe native sample upload, remove unused reference runtime state if present.
print(audio[audio.index('local SEEDS'):audio.index('local function setSeed')][-600:])
(D/'vfx/reference-audio-recipes.lua').write_text(audio)
p=D/'vfx/dragon_fx.body.lua';r=p.read_text();pos=r.index('local flying=')
r=r[:pos]+'''local AudioClip=U.AudioClip
local logger=require('official.core.logger').create('dragon-combat-audio')
'''+audio+'''
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
 local clip=audioClips[name];if not clip then clip=buildClip(name);audioClips[name]=clip end
 if not clip then audioFailed=audioFailed+1;return end
 if not audioRoot then audioRoot=U.GameObject('DragonCombatAudio')end
 local source=nil
 for _,v in ipairs(audioPool)do if not v.isPlaying then source=v;break end end
 if not source and #audioPool<8 then local go=U.GameObject('CombatVoice'..#audioPool);go.transform:SetParent(audioRoot.transform,false);source=go:AddComponent(typeof(U.AudioSource));source.playOnAwake=false;source.spatialBlend=0;source.loop=false;audioPool[#audioPool+1]=source end
 if not source then return end
 source.volume=.48;source.mute=false;source.pitch=1;source:PlayOneShot(clip,gain or 1)
 audioLastTime[name]=now;audioPlayed=audioPlayed+1;audioLast=name
end
''' +r[pos:]
a=r.index('function Play(');b=r.index('function Impact(',a)
r=r[:a]+'''function Charge(kind,action,p,target)
 if action=='attack'then return end
 if kind=='mage'and action=='skill3'then
  sound('v2-meteor-fall');local start=target+V(-2,9,-1);projectile(BoltEffect,start,(target-start).normalized,10,.9)
 elseif kind=='ranged'and action=='skill3'then sound('v2-rain-fall')
 elseif kind=='melee'and action=='skill3'then sound('v2-giant-awaken',.8)
 elseif kind=='ranged'and action=='skill2'then sound('v2-leaf-charge',.75)end
end
function Area(kind,action,p,burst)
 if kind=='ranged'then
  sound('v2-rain-hit',.8)
  for i=1,7 do local a=i*2.39996;local radius=.6+(i%3)*.7;local at=p+V(math.cos(a)*radius,0,math.sin(a)*radius)
   projectile(ArrowEffect,at+V(0,4,0),V.down,25,.16);one(HitEffect,at,nil,.7)
  end
 elseif action=='skill2'then
  sound('v2-time-hit');one(BlastEffect,p,nil,1.1)
  for i=1,6 do local a=i*math.pi/3;projectile(BoltEffect,p,V(math.cos(a),.15,math.sin(a)),4,.45)end
 else sound(action=='skill3'and'v2-meteor-impact'or'v2-magic-burst');one(BlastEffect,p,nil,action=='skill3'and 2 or 1.4)
  if action=='skill3'then for i=1,7 do local a=i*2.39996;one(HitEffect,p+V(math.cos(a)*2,.1,math.sin(a)*2),nil,1.2)end end
 end
end
function Play(kind,action,origin,direction)
 local d=direction.sqrMagnitude>.001 and direction.normalized or V.forward
 local q=U.Quaternion.LookRotation(d,V.up)
 if action=='skill'then action='skill1'end
 if kind=='melee'then
  if action=='skill1'then sound('v2-giant-hit',.8);one(ShieldEffect,origin-V(0,.45,0),nil,1.5)
  elseif action=='skill2'then sound('v2-sword-swing');for i=0,2 do one(SlashEffect,origin,q*U.Quaternion.Euler(0,i*120,0),1.25)end
  elseif action=='skill3'then sound('v2-giant-hit');one(SlashEffect,origin,q*U.Quaternion.Euler(0,0,85),1.7);one(ShieldEffect,origin+d*2-V(0,.45,0),nil,1.2)
  else sound('v2-sword-swing');one(SlashEffect,origin+V(0,.05,0),q,1)end
 elseif kind=='mage'then
  if action~='attack'then Area(kind,action,origin+d*6,1)else sound('v2-magic-shot',.8);projectile(BoltEffect,origin,d,16,.75)end
 else
  if action=='skill3'then Area(kind,action,origin+d*6,1)
  elseif action=='skill1'then for i=0,4 do queued[#queued+1]={at=U.Time.time+i*.16,p=origin,d=d}end
  else sound(action=='skill2'and 'v2-leaf-whoosh'or'v2-bow-release');projectile(ArrowEffect,origin,d,24,.75);if action=='skill2'then projectile(ArrowEffect,origin+V(0,.1,0),d,24,.75)end end
 end
end
''' +r[b:]
r=r.replace('function Impact(kind,position,amount)','function Impact(kind,position,amount,class)')
r=r.replace("elseif kind=='hit'then\n", "elseif kind=='hit'then\n  sound(class=='mage'and'v2-magic-hit'or(class=='ranged'and'v2-arrow-hit'or'v2-sword-hit'),.8)\n")
r=r.replace("elseif kind=='strike'then one", "elseif kind=='strike'then sound('v2-leaf-whoosh',.65);one")
r=r.replace(' local now=U.Time.time\n for i=#queued', ' local now=U.Time.time\n if warmIndex<=#SOUND_NAMES then local name=SOUND_NAMES[warmIndex];audioClips[name]=audioClips[name]or buildClip(name);warmIndex=warmIndex+1 end\n for i=#queued')
r=r.replace('if now>=q.at then projectile', "if now>=q.at then sound('v2-bow-release');projectile")
r=r.replace('return{available=Effect.isAvailable(),','local playing=0;for _,s in ipairs(audioPool)do if s.isPlaying then playing=playing+1 end end\n return{audio={played=audioPlayed,failed=audioFailed,last=audioLast,playing=playing,warmed=warmIndex-1},available=Effect.isAvailable(),')
r=r.replace('function OnDestroy()Clear()end','''function OnDestroy()
 Clear();if audioRoot then U.Object.Destroy(audioRoot)end
 for _,clip in pairs(audioClips)do U.Object.Destroy(clip)end;audioClips={};audioPool={}
end''')
p.write_text(r)
# events and real skinned-bone attacks
p=D/'dragon_combat_rules.body.lua';r=p.read_text().replace("kind=kind});return true", "kind=kind,x=m.x,z=m.z,tx=tx,tz=tz});return true");p.write_text(r)
p=D/'dragon_combat.body.lua';r=p.read_text()
r=r.replace("skill=q.kind=='skill'", "kind=q.kind")
r=r.replace("event.skill and 'skill'or 'attack'", "event.kind or 'attack'")
r=r.replace("elseif event.type=='shot'then fx.Play(event.class,'attack',p,d)", "elseif event.type=='shot'then fx.Play(event.class,event.kind=='skill1'and 'attack'or event.kind,p,d)\n  elseif event.type=='area'then fx.Area(event.class,event.kind,p,event.burst)\n  elseif event.type=='action'then fx.Charge(event.class,event.kind,p,V(event.tx,state.y+.6,event.tz))")
r=r.replace('fx.Impact(event.type,p,event.damage or 0)','fx.Impact(event.type,p,event.damage or 0,event.class)')
r=r.replace('v={go=go,materials=materials,bar=bar,bars=bars};visuals[e.id]=v', '''v={go=go,materials=materials,bar=bar,bars=bars,bones={}};visuals[e.id]=v
    local ts=go:GetComponentsInChildren(typeof(U.Transform),true)
    for bi=0,ts.Length-1 do local t=ts[bi];if t.name=='Chest'or t.name=='Head'or t.name=='UpperArm_L'or t.name=='UpperArm_R'or t.name=='Forearm_L'or t.name=='Forearm_R'then v.bones[t.name]={t=t}end end''')
r=r.replace('    local anim=v.go:GetComponentInChildren', '    v.enemy=e\n    local anim=v.go:GetComponentInChildren')
r=r.replace('function Update()\n', '''-- Restore before the animator evaluates; additive rotations never accumulate.
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
function Update()
 restoreBones()
''')
r=r.replace("preview=PreviewMode,damage=", "preview=PreviewMode,attackBoneCount=(function()local n=0;for _,v in pairs(visuals)do for _ in pairs(v.bones or{})do n=n+1 end end;return n end)(),damage=")
p.write_text(r)
print('original combat audio recipes, skill effects, rigged enemy attacks updated')
