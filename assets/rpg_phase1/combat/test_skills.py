from pathlib import Path
from lupa import LuaRuntime
L=LuaRuntime(unpack_returned_tuples=True);L.execute(Path(__file__).with_name('dragon_combat_rules.body.lua').read_text())
L.execute('''
local function fresh(class)
 local s=New(0,0,0,10,'nine');Join(s,'p',class,{x=0,z=0});Spawn(s)
 s.enemies={{id=1,x=0,z=2,hp=100,maxHP=100,speed=0,state='stun',timer=100,hit=0},{id=2,x=0,z=4,hp=100,maxHP=100,speed=0,state='stun',timer=100,hit=0}}
 return s
end
for _,class in ipairs({'melee','ranged','mage'})do for i=1,3 do
 local s=fresh(class);local kind='skill'..i;assert(Request(s,'p',1,kind,0,1),class..kind)
 for j=1,28 do Step(s,.05,{p={x=0,z=0}})end
 assert(not Request(s,'p',2,kind,0,1),'same skill must cool down')
 assert(Request(s,'p',3,'skill'..(i%3+1),0,1),'other skill must remain available')
 if class=='melee'and i==1 then assert(s.members.p.shield>s.t,'guard')
 elseif class=='ranged'and i==2 then assert(s.enemies[1].hp==97 and s.enemies[2].hp==97,'pierce both')
 elseif class=='mage'and i==2 then assert(s.enemies[1].state=='stun','frost control')
 else assert(s.members.p.damage>0,'skill damage '..class..i)end
end end
local s=fresh('mage');assert(not Request(s,'p',1,'skill4',0,1));assert(not Request(s,'p',2,'skill3',0/0,1))
''')
L=LuaRuntime(unpack_returned_tuples=True);L.execute(Path(__file__).with_name('dragon_rules.body.lua').read_text())
L.execute('''
for _,kind in ipairs({'melee','mage','ranged'})do
 local c={class=kind,mode='combat'};assert(#GetClasses()[kind].skills==3)
 assert(TryAction(c,'skill1',0));assert(not TryAction(c,'skill2',.1));assert(TryAction(c,'skill2',1.1));assert(TryAction(c,'skill3',2.2));assert(not TryAction(c,'skill1',4));assert(TryAction(c,'skill1',8.1))
end
''')
print('All nine skills: independent cooldowns, damage, guard, frost, piercing, validation and client locks PASS')
