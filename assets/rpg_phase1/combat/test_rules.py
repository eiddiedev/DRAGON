from pathlib import Path
from lupa import LuaRuntime
L=LuaRuntime(unpack_returned_tuples=True);L.execute(Path(__file__).with_name('dragon_combat_rules.body.lua').read_text())
L.execute('''
local function fresh(class)
 local s=New(0,0,0,10,'test');assert(Join(s,'p',class,{x=0,z=0}));Spawn(s);s.enemies={{id=1,x=0,z=2,hp=20,maxHP=20,speed=0,state='stun',timer=100,hit=0}};return s
end
local function step(s,n,pos)for i=1,n do Step(s,.05,{p=pos or {x=0,z=0}})end end
local s=fresh('melee');assert(Request(s,'p',1,'attack',0,1));assert(not Request(s,'p',1,'attack',0,1));assert(not Request(s,'p',2,'attack',0,1));step(s,6);assert(s.enemies[1].hp==18,'melee single hit')
s=fresh('melee');s.enemies[1].z=-2;Request(s,'p',1,'attack',0,1);step(s,6);assert(s.enemies[1].hp==20,'rear outside cone')
s=fresh('mage');s.enemies[1].z=5;Request(s,'p',1,'attack',0,1);step(s,5);assert(s.enemies[1].hp==20,'no early damage');step(s,12);assert(s.enemies[1].hp==19,'projectile travel')
s=fresh('ranged');s.enemies[1].z=5;Request(s,'p',1,'skill',0,1);step(s,30);assert(s.enemies[1].hp==15,'five sequential arrows');assert(not Request(s,'p',2,'skill',0,1),'cooldown')
s=fresh('mage');s.enemies[1].z=5;s.enemies[2]={id=2,x=2,z=5,hp=4,maxHP=4,speed=0,state='stun',timer=100,hit=0};Request(s,'p',1,'skill',0,1);step(s,15);assert(s.enemies[1].hp==17 and s.enemies[2].hp==1,'area damage')
s=fresh('melee');Request(s,'p',1,'skill',0,1);step(s,5);assert(s.members.p.shield>s.t and s.enemies[1].z>3.5,'shield and knockback');s.enemies[1].state='windup';s.enemies[1].timer=0;s.enemies[1].tx=0;s.enemies[1].tz=0;step(s,1);assert(s.members.p.hp==6,'shield stops damage')
s=fresh('melee');s.enemies[1].state='windup';s.enemies[1].timer=.1;s.enemies[1].tx=0;s.enemies[1].tz=0;step(s,3,{x=3,z=0});assert(s.members.p.hp==6,'tell can be dodged')
s=fresh('mage');Request(s,'p',1,'attack',0,1);for i=1,20 do Step(s,.05,{p={x=0,z=0}},function()return true end)end;assert(s.enemies[1].hp==20,'wall occlusion')
s=fresh('melee');local x,z=Boundary(s,40,40);assert(x*x+z*z<=9.5^2+.001,'arena limit');s.stage=3;s.enemies[1].hp=2;Request(s,'p',1,'attack',0,1);step(s,6);assert(s.phase=='victory','victory');assert(not Request(s,'p',3,'attack',0,1),'no postbattle attacks')
s=fresh('melee');s.members.p.hp=0;step(s,1);assert(s.phase=='defeat','defeat')
''')
print('10 combat scenarios passed: cone, dedupe, cooldown, travel, volley, AoE, shield, dodge, walls, boundaries and outcomes')
