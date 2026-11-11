from pathlib import Path
from lupa import LuaRuntime
L=LuaRuntime(unpack_returned_tuples=True);L.execute(Path(__file__).with_name('dragon_combat_rules.body.lua').read_text())
L.execute('''
local s=New(0,0,0,10,'stages');Join(s,'p','mage',{x=0,z=0});Spawn(s)
assert(#s.enemies==4 and s.stage==1)
for stage=1,3 do
 for _,e in ipairs(s.enemies)do e.hp=0 end
 Step(s,.05,{p={x=0,z=0}})
 if stage<3 then
  assert(s.phase=='active','no premature win')
  for i=1,61 do Step(s,.05,{p={x=0,z=0}})end
  assert(s.stage==stage+1,'reinforcement')
 else assert(s.phase=='victory')end
end
assert(#s.enemies==12 and s.enemies[10].boss,'12 enemies including boss')
local s=New(0,0,0,10,'lunge');Join(s,'p','melee',{x=0,z=0});Spawn(s)
s.enemies={{id=1,x=0,z=2,hp=20,maxHP=20,speed=1,state='windup',timer=.05,tx=0,tz=.9,hit=0}}
Step(s,.05,{p={x=0,z=0}});assert(s.enemies[1].z==2,'windup must not teleport')
for i=1,6 do local z=s.enemies[1].z;Step(s,.05,{p={x=0,z=0}});assert(math.abs(s.enemies[1].z-z)<.21,'bounded lunge displacement')end
assert(s.members.p.hp==5)
local hurt;for _,e in ipairs(s.events)do if e.type=='hurt'then hurt=e end end;assert(hurt.damage==1 and hurt.owner=='p')
''')
L.execute("""
local s=New(0,0,0,10,'facing');Join(s,'p','melee',{x=2,z=0});Spawn(s)
s.enemies={{id=1,x=0,z=0,hp=10,maxHP=10,speed=1,state='chase',timer=0,hit=0}}
Step(s,.05,{p={x=2,z=0}});local e=s.enemies[1]
assert(e.state=='windup'and e.faceX>.999 and math.abs(e.faceZ)<.001,'face actual target')
for i=1,20 do Step(s,.05,{p={x=-2,z=0}});assert(e.faceX>.999,'locked strike must not swivel at moving player')end
for i=1,40 do Step(s,.05,{p={x=-2,z=0}})end
assert(e.faceX<-.99,'reacquire target after recovery')
""")
print('Encounter progression, unique enemy IDs, final-only victory, continuous lunge and hurt payload PASS')
