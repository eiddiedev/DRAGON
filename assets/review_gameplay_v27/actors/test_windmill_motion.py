from pathlib import Path
import json
from lupa import LuaRuntime
D=Path(__file__).parent
src=(D/'windmill-motion-after.lua.part').read_text()
base='''
UI={};skyReady=false;finds=0;meshReads=0;rotations=0;model=nil;failRotation=false
Time={realtimeSinceStartup=0,deltaTime=1/30}
UnityEngine={Transform='Transform',MeshFilter='MeshFilter',Shader={Find=function()error('sky shader not ready')end}}
typeof=function(v)return v end
report=function()end
GameObject={Find=function(name)assert(name=='windmill');finds=finds+1;return model end}
pivot={name='windmill_rotor_pivot',Rotate=function(self,x,y,z)if failRotation then error('destroyed transform')end;rotations=rotations+1 end}
authoredModel={GetComponentsInChildren=function(self,typ,all)assert(typ=='Transform','authored rotor must not read CPU mesh');return {[0]=pivot,Length=1}end}
'''
lua=LuaRuntime();lua.execute(base+'\n'+src)
lua.execute('''
UI.updateMotion();assert(finds==1 and not UI.motion.rotor)
for i=1,50 do Time.realtimeSinceStartup=i/100;UI.updateMotion()end
assert(finds==1,'missing resource lookup must be throttled')
model=authoredModel;Time.realtimeSinceStartup=2.1;UI.updateMotion()
assert(UI.motion.rotor==pivot and rotations==1,'windmill can initialize before sky')
for i=1,30 do Time.realtimeSinceStartup=2.1+i/30;UI.updateMotion()end
assert(finds==2 and rotations==31,'ready rotor does not re-discover or rebuild')
skyReady=true;Time.realtimeSinceStartup=4.2;UI.updateMotion()
assert(rotations==32 and UI.motion.skyError,'sky shader failure does not stop rotor')
failRotation=true;Time.realtimeSinceStartup=4.3;UI.updateMotion()
assert(UI.motion.rotor==nil and UI.motion.windStatus=='waiting replacement')
failRotation=false;Time.realtimeSinceStartup=6.4;UI.updateMotion()
assert(UI.motion.rotor==pivot,'streamed replacement can rebind')
''')
lua=LuaRuntime();lua.execute(base+'\n'+src)
lua.execute('''
for i=0,200 do Time.realtimeSinceStartup=i*2.1;UI.updateMotion()end
assert(finds==60 and UI.motion.windAttempts==60 and UI.motion.windStatus=='model timeout')
''')
lua=LuaRuntime();lua.execute(base+'\n'+src)
lua.execute('''
local broken={name='main'}
setmetatable(broken,{__index=function(self,key)if key=='mesh'then error('mesh is not readable')end end})
broken.gameObject={name='main'};broken.sharedMesh={}
model={GetComponentsInChildren=function(self,typ,all)
 if typ=='Transform'then return {Length=0}end
 meshReads=meshReads+1;return {[0]=broken,Length=1}
end}
UI.updateMotion();assert(UI.motion.windError and not UI.motion.failed)
Time.realtimeSinceStartup=1;UI.updateMotion();assert(meshReads==1)
-- Resource replaced by offline split model: previous failure is not sticky.
model=authoredModel;Time.realtimeSinceStartup=2.1;UI.updateMotion();assert(UI.motion.rotor==pivot)
''')
result={'passed':['no sky dependency','two-second pending lookup throttle','ready rotor no rebuild','sky error isolated','destroyed rotor rebind','60-attempt upper bound','unreadable legacy error recovers after authored pivot arrives'],'notVerified':['actual consumer GLB import and rotor motion','current failed review package not supplied']}
(D/'windmill-motion-test-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
