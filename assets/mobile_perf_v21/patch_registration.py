from pathlib import Path
import json
A=Path(json.load(open('assets/mobile_perf_v21/baseline.json'))['source']);p=A/'scripts/dragon_exploration.lua';s=p.read_text()
insert='''
-- Streamed interaction objects can arrive after the first discovery pass.
-- Append missing targets without rebuilding live native button identities.
local function pollInteractionResources()
 if #targets==0 then return end
 if not R.pendingTargets then
  R.pendingTargets={{'holy_tree3','tree',9,'古树 · 重新立誓'},{'tripo_witch','witch',2.8,'女巫 · 调制'},{'camp','camp',4,'篝火 · 烤蘑菇'}}
  for i=0,35 do R.pendingTargets[#R.pendingTargets+1]={i==0 and 'mush'or 'mush_'..i,'mushroom',3.5,'采集蘑菇'}end
  for i=0,8 do R.pendingTargets[#R.pendingTargets+1]={'sheep_'..i,'wool',3,'取羊毛'}end
  R.foundTargets={};for _,t in ipairs(targets)do if t.go then R.foundTargets[t.go.name]=true end end
  R.targetUntil=U.Time.realtimeSinceStartup+30;R.targetAt=0;R.targetIndex=0
 end
 local now=U.Time.realtimeSinceStartup
 if now>R.targetUntil or now<R.targetAt then return end;R.targetAt=now+.1
 for _=1,2 do
  R.targetIndex=R.targetIndex%#R.pendingTargets+1;local q=R.pendingTargets[R.targetIndex]
  if not R.foundTargets[q[1]]then local go=U.GameObject.Find(q[1]);if go then targets[#targets+1]={go=go,kind=q[2],radius=q[3],label=q[4]};R.foundTargets[q[1]]=true end end
 end
end
'''
pos=s.index('local function handleNativeClick');s=s[:pos]+insert+s[pos:]
s=s.replace("if #targets==0 then discover()end end", "if #targets==0 then discover()end end\n pollInteractionResources()")
p.write_text(s)
