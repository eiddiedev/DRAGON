from pathlib import Path
import json
from lupa import LuaRuntime
D=Path(__file__).parent
lua=LuaRuntime(unpack_returned_tuples=True)
for p in D.glob('*.lua'):
 lua.execute('assert(load(...))',p.read_text())
lua.execute('''
CS={UnityEngine={Time={realtimeSinceStartup=0},Debug={LogWarning=function(x)end}}}
CS.ModularAnim={Runtime={UGCAnimator='UGC'}}
typeof=function(t)return t end
owner={lookups=0}
function owner:GetComponent(t)self.lookups=self.lookups+1;return self.anim end
function owner:GetComponentInChildren(t,children)return nil end
''')
lua.execute((D/'animation_player.lua').read_text()+'\nplayer=createAnimationPlayer(owner,"test")')
lua.execute('''
player.request('Idle');player.tick();assert(player.status=='waiting controller')
CS.UnityEngine.Time.realtimeSinceStartup=1.1
calls=0;owner.anim={enabled=true,Controller={}}
function owner.anim:Play(name)calls=calls+1;return self.succeeds==true end
player.tick();assert(player.played==nil and calls==1)
CS.UnityEngine.Time.realtimeSinceStartup=1.2;player.tick();assert(calls==1)
owner.anim.succeeds=true;CS.UnityEngine.Time.realtimeSinceStartup=1.7;player.tick()
assert(player.played=='Idle' and calls==2)
for i=1,20 do CS.UnityEngine.Time.realtimeSinceStartup=2+i/10;player.request('Idle');player.tick()end
assert(calls==2) -- don't restart a healthy looping clip
owner.anim.Controller={};CS.UnityEngine.Time.realtimeSinceStartup=4.1;player.tick()
assert(calls==3 and player.played=='Idle') -- rebind invalidates same-state cache
player.request('Run');CS.UnityEngine.Time.realtimeSinceStartup=4.7;player.tick()
assert(player.played=='Run' and calls==4)
player.stop();CS.UnityEngine.Time.realtimeSinceStartup=5;player.tick();assert(calls==4)
player.resume();player.tick();assert(calls==5)
owner2={lookups=0,GetComponent=owner.GetComponent,GetComponentInChildren=owner.GetComponentInChildren}
''')
lua.execute((D/'animation_player.lua').read_text()+'\nmissing=createAnimationPlayer(owner2,"missing")')
lua.execute('''
missing.request('Idle')
for i=6,70 do CS.UnityEngine.Time.realtimeSinceStartup=i;missing.tick()end
local n=owner2.lookups;CS.UnityEngine.Time.realtimeSinceStartup=120;missing.tick()
assert(missing.status=='controller timeout' and owner2.lookups==n)
missing.resume();missing.tick();assert(owner2.lookups>n)
''')
lua.execute('''
local U=CS.UnityEngine
local vector={};vector.__index=function(t,k)if k=='sqrMagnitude'then return t.x*t.x+t.y*t.y+t.z*t.z end return vector[k]end
vector.__add=function(a,b)return setmetatable({x=a.x+b.x,y=a.y+b.y,z=a.z+b.z},vector)end
vector.__sub=function(a,b)return setmetatable({x=a.x-b.x,y=a.y-b.y,z=a.z-b.z},vector)end
U.Vector3=setmetatable({},{__call=function(_,x,y,z)return setmetatable({x=x,y=y,z=z},vector)end})
U.Vector3.zero=U.Vector3(0,0,0);U.Vector3.down=U.Vector3(0,-1,0)
U.QueryTriggerInteraction={Ignore=1}
U.Time.realtimeSinceStartup=0
rayAvailable=false;actorNear=false
U.Physics={RaycastAll=function()if not rayAvailable then return {Length=0}end
 return {[0]={collider={isTrigger=false,enabled=true,gameObject={activeInHierarchy=true},transform={IsChildOf=function()return false end}},normal=U.Vector3(0,1,0),point=U.Vector3(3,42,4)},Length=1}end}
DouyinActorService={GetLocalActor=function()return actorNear and {position=U.Vector3(3,42,4)}or nil end}
sheep={name='sheep_0',transform={position=U.Vector3(3,42.1,4)}}
body={isKinematic=false,useGravity=true,position=sheep.transform.position}
''')
lua.execute((D/'sheep_ground_guard.lua').read_text()+'\nguard=createSheepGroundGuard(sheep,body)')
lua.execute('''
assert(body.isKinematic and not body.useGravity)
for i=0,10 do CS.UnityEngine.Time.realtimeSinceStartup=i;assert(not guard.tick())end
assert(body.position.y==42.1 and not guard.ready)
rayAvailable=true;CS.UnityEngine.Time.realtimeSinceStartup=11;assert(not guard.tick())
CS.UnityEngine.Time.realtimeSinceStartup=11.3;assert(guard.tick())
assert(not body.isKinematic and body.useGravity and guard.status=='dynamic')
''')
results={"luaSyntax":"all candidate lua parsed", "animation":["delayed controller","failed Play retry","no same-state replay","controller rebound","clip transition","disable/resume","bounded missing-component lookup"],"sheep":["gravity held before support","two real support probes before dynamic release"],"notVerified":["review-client playback/bone motion","phone physics/streaming order","exact dragon contact"]}
(D/'test-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False))
