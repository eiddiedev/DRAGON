from pathlib import Path
import json,shutil,re
A=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9/ai-sessions/workspace_m293a9tg/wprefabs/dragon_fx_mobile_v22');O=Path('assets/mobile_low_v24');(O/'before').mkdir(exist_ok=True)
for name in ['dragon_fx.lua','dragon_world_bridge.lua']:shutil.copy2(A/'scripts'/name,O/'before'/name)
s=(A/'scripts/dragon_fx.lua').read_text()
s=s.replace('local BOOM=1.55','local BOOM=MobileBudget and 1 or 1.55')
# Managed one-shots: strict lifetime and concurrent budget, independent of template duration.
a=s.index('local function one(');b=s.index('hurtFeel=function()',a)
s=s[:a]+'''local lowShots={}
local lowSpawnFrame=-1
local lowFrameCount=0
local lowDropped=0
local function one(key,p,rotation,scale)
 if not key then return end
 if MobileBudget then
  local frame=U.Time.frameCount
  if frame~=lowSpawnFrame then lowSpawnFrame=frame;lowFrameCount=0 end
  if #lowShots>=4 or lowFrameCount>=2 then lowDropped=lowDropped+1;return end
  lowFrameCount=lowFrameCount+1
  local h,why=Effect.create(self,key,p,{rotation=rotation or U.Quaternion.identity,scale=math.min(scale or 1,1.6)})
  if h then lowShots[#lowShots+1]={h=h,untilT=U.Time.time+.55};emitted=emitted+1 else failed=failed+1;lastReason=why end
  return
 end
 local go,why=Effect.spawn(self,key,p,{rotation=rotation or U.Quaternion.identity,scale=(scale or 1)*BOOM})
 if go then emitted=emitted+1 else failed=failed+1;lastReason=why end
end
''' +s[b:]
s=s.replace('MobileBudget and 10 or 26','MobileBudget and 2 or 26')
s=s.replace('local function feel(flash,shake,duration)\n','local function feel(flash,shake,duration)\n if MobileBudget then return end\n')
s=s.replace("hurtFeel=function()if not bridge", "hurtFeel=function()if MobileBudget then return end;if not bridge")
s=s.replace("function Charge(kind,action,p,target)\n",'''function Charge(kind,action,p,target)
 if MobileBudget then
  if action=='skill3' then sound(kind=='mage'and 'v2-meteor-fall'or(kind=='ranged'and 'v2-rain-fall'or 'v2-giant-awaken'),.6) end
  return -- no redundant charge particles; attack animation carries anticipation
 end
''')
s=s.replace('function Area(kind,action,p,burst)\n', '''function Area(kind,action,p,burst)
 if MobileBudget then
  if kind=='ranged' then sound('v2-rain-hit',.7);one(HitEffect,p,nil,1.2);projectile(ArrowEffect,p+V(0,4,0),V.down,20,.2,false,1)
  elseif action=='skill2' then sound('v2-time-hit',.7);one(FrostEffect,p,nil,1.4)
  elseif action=='skill3' then sound('v2-meteor-impact',.7);one(MeteorEffect,p,nil,1.5)
  else sound('v2-magic-burst',.7);one(BlastEffect,p,nil,1.3) end
  return
 end
''')
needle=" if action=='skill'then action='skill1'end\n"
s=s.replace(needle,needle+''' if MobileBudget then
  if kind=='melee' then
   sound(action=='attack'and 'v2-sword-swing'or 'v2-giant-hit',.7)
   one(action=='skill1'and ShieldEffect or SlashEffect,origin,q,action=='attack'and .9 or 1.4)
  elseif kind=='mage' then
   if action=='attack' then sound('v2-magic-shot',.7);projectile(BoltEffect,origin,d,18,.6,false,1) else Area(kind,action,origin+d*6,1) end
  elseif action=='skill3' then Area(kind,action,origin+d*6,1)
  else originalSound('Bow',origin);projectile(ArrowEffect,origin,d,26,.6,action=='skill2',action=='skill2'and 1.3 or .9) end
  return
 end
''')
s=s.replace("function Impact(kind,position,amount,class)\n",'''function Impact(kind,position,amount,class)
 if MobileBudget then
  if kind=='tell' then one(TellEffect,V(position.x,position.y-.5,position.z),nil,1)
  elseif kind=='strike' then originalSound('Enemy',position);one(HitEffect,position,nil,.6)
  elseif kind=='hit' then sound(class=='mage'and 'v2-magic-hit'or(class=='ranged'and 'v2-arrow-hit'or 'v2-sword-hit'),.7);one(HitEffect,position,nil,.65)
  elseif kind=='blast' then one(BlastEffect,position,nil,1) end
  return
 end
''')
s=s.replace('function SetArena(center,radius,visible)\n','function SetArena(center,radius,visible)\n if MobileBudget then if arena then arena:Release();arena=nil end;wantedArena=nil;return end -- terrain sigil remains visible\n')
s=s.replace(' local now=U.Time.time\n\n for i=#queued',' local now=U.Time.time\n for i=#lowShots,1,-1 do local v=lowShots[i];if now>=v.untilT then v.h:Release();table.remove(lowShots,i)end end\n\n for i=#queued')
s=s.replace("build='v23-flight-pool'","build='v24-mobile-low',oneShots=#lowShots,dropped=lowDropped")
s=s.replace('function Clear()\n','function Clear()\n for _,v in ipairs(lowShots)do v.h:Release()end;lowShots={}\n')
(A/'scripts/dragon_fx.lua').write_text(s)
# Restore low authored source candidates only, never revert current gameplay scripts.
stats=[]
for p in (Path('assets/mobile_failure_v22/fx-source')).glob('*.json'):
 dest=A/'assets/effects'/('effect-combat-'+p.stem)/'effect.json'
 if not dest.exists():continue
 shutil.copy2(dest,O/'before'/('effect-'+p.stem+'.json'))
 d=json.loads(p.read_text());cap=0;systems=0
 for n in d['nodeTransformDatas']:
  ps=n.get('effects',{}).get('particleSystemData')
  if ps and n['basic'].get('isActive',True):
   ps['main']['maxParticles']=min(6,ps['main']['maxParticles']);cap+=ps['main']['maxParticles'];systems+=1
   for b in ps['emission'].get('bursts',[]):
    c=b['count'];v=min(ps['main']['maxParticles'],c.get('max',1));c.update(mode='constant',min=v,max=v,multiplier=v)
 dest.write_text(json.dumps(d,ensure_ascii=False));stats.append({'effect':p.stem,'systems':systems,'maxParticles':cap})
(O/'effect-budget.json').write_text(json.dumps(stats,indent=2))
print(stats)
