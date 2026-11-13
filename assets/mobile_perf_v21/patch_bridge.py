exec(open('assets/mobile_perf_v21/prepare.py').read().split('# Add cache immediately')[0])
s=(B/'dragon_world_bridge.lua').read_text()
a=s.index('function UI.updateFoliage(actor)');b=s.index('-- Runtime-only visual changes:',a)
reed=re.search(r'UI.reeds=\{names=\{.*?\},items=\{\},next=0,tick=0\}',s[a:b]).group(0)
s=s[:a]+reed+'\n'+(O/'vegetation.lua').read_text()+'\n'+s[b:]
# Keep only names verified in the current saved snapshot, not deleted historical objects.
for target in ['foliage','reeds']:
 pat=r'(UI\.'+target+r'\s*=\s*\{[^\n]*?names\s*=\s*)\{([^}]*)\}'
 m=re.search(pat,s);assert m,target
 valid=[n for n in re.findall(r'"([^"]+)"',m[2])if n in names]
 print(target,len(valid));s=s[:m.start(2)]+','.join(json.dumps(n)for n in valid)+s[m.end(2):]
s=s.replace('DR.phase1={scope=require("official.core.runtime_scope").from(self)}','DR.phase1={scope=require("official.core.runtime_scope").from(self)}'+cache.replace('SCOPE','DR.phase1.scope').replace('RELEASE','DR.releaseMobileDependencies').replace('do\n local target=', 'function DR.installDependencyCache()\n local target=')+'\nDR.installDependencyCache()\n')
s+='''
-- Bounded resource readiness and frame-time ring; no full-scene searches per frame.
DR.mobile={build='mobile-v21',start=Time.realtimeSinceStartup,nextAt=0,checks=0,frames={},index=0,horse='pending',wheat='pending',profession='pending'}
function DR.installMobileDiagnostics()
 local previous=Update
 function Update()
  previous()
  local m=DR.mobile;local now=Time.realtimeSinceStartup
  m.index=m.index%300+1;m.frames[m.index]=Time.unscaledDeltaTime*1000
  if now<m.nextAt or m.checks>=30 then return end;m.nextAt=now+1;m.checks=m.checks+1
  if m.horse=='pending'then local go=GameObject.Find('tripo_horse');if go then local rs=go:GetComponentsInChildren(typeof(UnityEngine.Renderer),true);if rs.Length>0 then m.horse='ready';m.horseAt=now-m.start end end end
  if #UI.reeds.items>0 then m.wheat='ready';m.wheatCount=#UI.reeds.items end
  if DR.phase1.rpg then m.profession='ready' end
  if m.checks==30 then for _,key in ipairs({'horse','wheat','profession'})do if m[key]=='pending'then m[key]='failed';report('mobile-v21 '..key..' not ready after 30 checks')end end end
 end
 local destroy=OnDestroy
 function OnDestroy()if destroy then destroy()end;DR.releaseMobileDependencies();DR.mobile.frames={}end
end
DR.installMobileDiagnostics()
function GetMobileDiagnostics()
 local m=DR.mobile;local ordered={};local sum=0
 for _,v in ipairs(m.frames)do ordered[#ordered+1]=v;sum=sum+v end;table.sort(ordered)
 return {build=m.build,horse=m.horse,wheat=m.wheat,wheatCount=#UI.reeds.items,wheatExpected=#UI.reeds.names,profession=m.profession,foliageCount=#UI.foliage.items,foliageExpected=#UI.foliage.names,meanMs=#ordered>0 and sum/#ordered or 0,p95Ms=ordered[math.max(1,math.ceil(#ordered*.95))]or 0,elapsed=Time.realtimeSinceStartup-m.start}
end
'''
(A/'scripts/dragon_world_bridge.lua').write_text(s)
# Validate Lua bytecode compilation before touching scene.
lua=LuaRuntime();check=lua.eval('function(s) local f,e=load(s);return f~=nil,e end')
for p in (A/'scripts').glob('*.lua'):
 ok,e=check(p.read_text());assert ok,(p.name,e)
print('13 Lua scripts syntax valid')
