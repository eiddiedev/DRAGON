from pathlib import Path
from lupa import LuaRuntime
l=LuaRuntime(unpack_returned_tuples=True)
l.execute('''
local mt={};local function v(x,y,z)return setmetatable({x=x or 0,y=y or 0,z=z or 0,sqrMagnitude=1},mt)end
mt.__add=function(a,b)return v(a.x+b.x,a.y+b.y,a.z+b.z)end
mt.__sub=function(a,b)return v(a.x-b.x,a.y-b.y,a.z-b.z)end
mt.__mul=function(a,b)return v(a.x*b,a.y*b,a.z*b)end
mt.__div=function(a,b)return v(a.x/b,a.y/b,a.z/b)end
mt.__index=function(a,k)if k=='normalized'then return a end end
local V=setmetatable({up=v(0,1,0),down=v(0,-1,0),zero=v(),forward=v(0,0,1),one=v(1,1,1)},{__call=function(_,...)return v(...)end})
local Q={identity={}};Q.LookRotation=function()return Q.identity end;Q.Euler=Q.LookRotation
local U={Vector3=V,Quaternion=Q,Time={time=0,realtimeSinceStartup=0},Object={Destroy=function()end}}
CS={UnityEngine=U,DouyinActorService={GetLocalActor=function()return nil end}}
self={};MobileBudget=true;BoltEffect={};ArrowEffect={};HitEffect={}
local E={};E.isAvailable=function()return true end;E.spawn=function()return {}end
E.create=function(_,key,p,opt)
 local g={transform={position=p,rotation=opt.rotation,localScale=V.one*opt.scale}}
 return {GetGameObject=function()return g end,Play=function()return g~=nil end,Stop=function()return true end,Release=function()g=nil end}
end
require=function(n)
 if n=='official.effect.playback'then return E end
 if n=='official.core.logger'then return {create=function()return {warnOnce=function()end}end}end
 if n=='official.core.runtime_scope'then return {from=function()return {GetScript=function()return nil end}end}end
 error(n)
end
''')
l.execute(Path('assets/mobile_compat_v23/dragon_fx.lua').read_text())
l.execute('''
local U=CS.UnityEngine;local V=U.Vector3
local function tick(t)U.Time.time=t;U.Time.realtimeSinceStartup=t;Update()end
for i=1,50 do local t=i*2;tick(t);Play('mage','attack',V.zero,V.forward);tick(t+.8);tick(t+1.3)end
local s=GetStatus();assert(s.flightPool.created==1);assert(s.flightPool.reused==49);assert(s.flightPool.retained==1);assert(s.flying==0)
tick(140);assert(GetStatus().flightPool.retained==0)
for i=1,30 do Play('mage','attack',V.zero,V.forward)end
assert(GetStatus().flying==10);assert(GetStatus().flightPool.retained==10)
OnDisable();assert(GetStatus().flightPool.retained==0);assert(GetStatus().flying==0)
Play('mage','attack',V.zero,V.forward);assert(GetStatus().flying==1);OnDestroy();assert(GetStatus().flightPool.retained==0)
''')
print('PASS: 50 sequential projectiles create 1 instance and reuse 49; 30s idle eviction; 10-flight cap unchanged; disable/destroy fully release; restart works')
