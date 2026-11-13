import json,re
from pathlib import Path
from lupa import LuaRuntime
O=Path('assets/mobile_perf_v21');A=Path(json.load(open(O/'baseline.json'))['source']);L=LuaRuntime(unpack_returned_tuples=True)
check=L.eval('function(s)local f,e=load(s);return f~=nil,e end')
for p in(A/'scripts').glob('*.lua'):
 ok,e=check(p.read_text());assert ok,(p.name,e)
# Exercise the actual inserted resolver with delayed availability and permanent failure.
s=(A/'scripts/dragon_exploration.lua').read_text();block=s[s.index('-- mobile-v21: resolve'):s.index('local ',s.index('end\n',s.index('RELEASE='))) ] if False else None
start=s.index('-- mobile-v21: resolve');end=s.index('\nend\n',start)+5
L.execute('CS={UnityEngine={Time={realtimeSinceStartup=0}}}; calls=0;ready=false;scope={GetScript=function(self,name)calls=calls+1;if ready and name=="good" then return {value=42} end end}')
L.execute(s[start:end]);L.execute('for i=1,100 do scope:GetScript("good")end;assert(calls==1);CS.UnityEngine.Time.realtimeSinceStartup=1;ready=true;assert(scope:GetScript("good").value==42);for i=1,100 do scope:GetScript("good")end;assert(calls==2);for i=2,100 do CS.UnityEngine.Time.realtimeSinceStartup=i;scope:GetScript("missing")end;assert(calls==32);assert(GetDependencyDiagnostics().failures.missing)')
bridge=(A/'scripts/dragon_world_bridge.lua').read_text();vegetation=bridge[bridge.index('function UI.discoverVegetation'):bridge.index('-- Runtime-only visual changes:')]
assert 'MeshCollider' not in vegetation and '.vertices'not in vegetation and 'Shader.Find'not in vegetation
fx=(A/'scripts/dragon_fx.lua').read_text();assert 'AudioClip.Create'not in fx and 'SetData('not in fx
m=json.load(open(O/'audio-manifest.json'));assert len(m)==22 and all(v.get('uri')for v in m)
(O/'source-checks.json').write_text(json.dumps({'luaSyntax':13,'dependencyCache':'100 calls -> one scan; late ready cached; failure capped at 30','vegetation':'no runtime mesh collider, vertex copies or shader lookup','audioRegistered':len(m),'audioPCMBytes':sum(v['bytes']for v in m),'phoneValidated':False},indent=2))
print('source checks passed')
