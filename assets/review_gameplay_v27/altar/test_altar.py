from pathlib import Path
import json
from lupa import LuaRuntime
D=Path(__file__).parent
l=LuaRuntime(unpack_returned_tuples=True)
l.execute('''
UnityEngine={Time={realtimeSinceStartup=0},Transform='t',Renderer='r'}
typeof=function(t)return t end
Vector3=function(x,y,z)return {x=x,y=y,z=z}end
objects={};finds=0
GameObject={Find=function(n)finds=finds+1;if UnityEngine.Time.realtimeSinceStartup<75 then return nil end return objects[n]end}
children={Length=7}
for i=0,6 do local n=i<4 and 'beam_'..i or 'runeg_'..(i-4)
 local go={active=false,transform={position=Vector3(0,-10,0)}}
 function go:SetActive(x)self.active=x end
 children[i]={name=n,gameObject=go};objects[n]=go
end
objects.DragonAltarProgressVisuals={GetComponentsInChildren=function()return children end}
for i=0,3 do
 local name=i<3 and 'rune_'..i or 'altar3'
 objects[name]={transform={position=Vector3(48+i,52,150)},GetComponentsInChildren=function()return {Length=1,[0]={bounds={size={y=3},max={y=55}}}}end}
end
profile=nil
progress={GetProfile=function()return profile end}
''')
l.execute('local runeGo,beamGo,runeGlow;local litCount=0;local runeLit={};\n'+(D/'controller.lua').read_text()+'''
function step(t)
 UnityEngine.Time.realtimeSinceStartup=t
 updateAltar(nil)
 if beamGo then beamGo.progress=progress end
end
''')
l.execute('''
for t=0,74 do step(t)end
for i=0,3 do assert(objects['beam_'..i].active==false)end
step(75);step(76)
for i=0,3 do assert(objects['beam_'..i].active==false);assert(objects['beam_'..i].transform.position.y==55.04)end
profile={deposited={moon=2,ember=0,stardew=0},hatchReady=false,pact=false};step(77)
assert(objects.beam_0.active and not objects.beam_1.active and not objects.beam_3.active)
profile.deposited.ember=3;profile.deposited.stardew=1;profile.hatchReady=true;step(78)
for i=0,3 do assert(objects['beam_'..i].active==true)end
profile=nil;step(79);for i=0,3 do assert(not objects['beam_'..i].active)end
local n=finds;for i=80,200 do step(i)end;assert(finds==n)
''')
r={'passed':['initial visuals hidden','dependencies delayed 75 seconds','surface anchored','partial offering','hatch-ready central beam','missing profile hides lights','no continued scene search after ready']}
(D/'test-results.json').write_text(json.dumps(r,indent=2));print(r)
