from pathlib import Path
A=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9/ai-sessions/workspace_m293a9tg/wprefabs/dragon_fx_mobile_v22/scripts/dragon_fx.lua')
s=A.read_text();Path('assets/mobile_compat_v23/dragon_fx.before.lua').write_text(s)
a=s.index('local function projectile(');b=s.index('\nfunction Charge',a)
s=s[:a]+'''-- v23: reuse finished flight effects; preserve particle sources and visible timing.
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
end'''+s[b:]
s=s.replace('elseif now>=v.release then v.h:Release();table.remove(flying,i)end','elseif now>=v.release then parkFlight(v);table.remove(flying,i)end')
s=s.replace(' if wantedArena and not arena then SetArena', ''' -- Bound retained memory when combat has been idle; never interrupt live effects.
 for i=#flightPool,1,-1 do local e=flightPool[i];if not e.busy and now-(e.idleAt or now)>30 then releaseFlight(e);table.remove(flightPool,i)end end
 if wantedArena and not arena then SetArena''')
s=s.replace('return{audio={played=',"return{build='v23-flight-pool',flightPool={retained=#flightPool,created=flightCreated,reused=flightReused,released=flightReleased},audio={played=")
s=s.replace(' for _,v in ipairs(flying)do v.h:Release()end;flying={}', ' for _,e in ipairs(flightPool)do releaseFlight(e)end;flightPool={};flying={}')
assert s!=A.read_text()
A.write_text(s);Path('assets/mobile_compat_v23/dragon_fx.lua').write_text(s)
from lupa import LuaRuntime
l=LuaRuntime(unpack_returned_tuples=True);f,e=l.eval('function(s)local f,e=load(s);return f,e end')(s);assert f,e
print('v23 flight pool written; compile passed')
