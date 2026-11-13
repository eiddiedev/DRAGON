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

l.execute("CS.UnityEngine.Time.frameCount=1;SlashEffect={};ShieldEffect={};BlastEffect={};FrostEffect={};MeteorEffect={};TellEffect={}")
l.execute(Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9/ai-sessions/workspace_m293a9tg/wprefabs/dragon_fx_mobile_v22/scripts/dragon_fx.lua').read_text())
l.execute("""
local U=CS.UnityEngine;local V=U.Vector3
for frame=1,30 do
 U.Time.frameCount=frame;U.Time.time=frame*.02
 for _,kind in ipairs({'melee','mage','ranged'})do for _,action in ipairs({'attack','skill1','skill2','skill3'})do
 Charge(kind,action,V.zero,V.one);Play(kind,action,V.zero,V.forward);Impact('hit',V.zero,4,kind)
 end end
 Update();local s=GetStatus();assert(s.oneShots<=4);assert(s.flying<=2);assert(s.flightPool.retained<=2)
end
U.Time.time=3;Update();U.Time.time=4;Update();assert(GetStatus().oneShots==0);assert(GetStatus().flying==0)
OnDisable();assert(GetStatus().flightPool.retained==0);assert(GetStatus().oneShots==0)
""")
print('PASS: all 3 classes/3 skills burst stress bounded to 4 one-shots + 2 flights; expiry and disable release all')
