from cli import P,D
from pathlib import Path
import re
S=P/'scripts'
B=D/'v7-backup';B.mkdir(exist_ok=True)
for n in ['dragon_rpg','dragon_rules','dragon_weapons','dragon_timeline','dragon_fx','dragon_combat','dragon_combat_rules']:
 p=S/(n+'.lua');b=B/p.name
 if not b.exists():b.write_text(p.read_text())
# Freeze current final bodies instead of regenerating UI from obsolete snapshots.
for n in ['dragon_rpg','dragon_rules']:
 b=D/(n+'.body.lua')
 if not b.exists():b.write_text('\n'.join((S/(n+'.lua')).read_text().splitlines()[2:])+'\n')
r=(D/'dragon_rules.body.lua').read_text()
r=r.replace('function GetClasses()', '''local skills={
 melee={{name="破晓守护",icon="shield",cooldown=8,delay=.20},{name="回旋斩",icon="spin",cooldown=6,delay=.22},{name="巨剑裁决",icon="sword",cooldown=14,delay=.68}},
 ranged={{name="月羽连射",icon="bow",cooldown=8,delay=.38},{name="贯晶箭",icon="prism",cooldown=6,delay=.22},{name="万箭齐下",icon="rain",cooldown=14,delay=.65}},
 mage={{name="星火爆裂",icon="prism",cooldown=8,delay=.65},{name="霜星禁锢",icon="frost",cooldown=7,delay=.48},{name="陨星裁决",icon="meteor",cooldown=15,delay=.95}}
}
for k,v in pairs(classes)do v.skills=skills[k]end
function GetClasses()''')
a=r.index('function TryAction(');b=r.index('function InsideCircle',a)
r=r[:a]+'''function TryAction(context,kind,now)
 local ok,why=CanUse(context);if not ok then return nil,why end
 if kind=="skill"then kind="skill1"end
 local index=tonumber(string.match(kind or "","^skill([123])$"));local c=classes[context.class]
 if kind~="attack"and not index then return nil,"未知动作"end
 if now<(context.busyUntil or 0)then return nil,"动作尚未结束"end
 local key=index and(kind.."Until")or "attackUntil";local sk=index and c.skills[index]
 if now<(context[key]or 0)then return nil,"冷却中"end
 context[key]=now+(sk and sk.cooldown or c.attackInterval)
 context.busyUntil=now+(sk and(index==3 and 1.25 or 1.0)or c.attackInterval)
 context.sequence=(context.sequence or 0)+1
 return {sequence=context.sequence,class=context.class,kind=kind,hitAt=now+(sk and sk.delay or(context.class=="ranged"and .18 or c.hitDelay)),range=c.range,started=now,expires=now+1.5}
end
''' +r[b:]
(D/'dragon_rules.body.lua').write_text(r)
# Combat authoritative skills, independent cooldowns, piercing projectiles, repeat area strikes.
p=D/'dragon_combat_rules.body.lua';r=p.read_text()
r=r.replace("if kind~='attack'and kind~='skill'then return false end", "if kind=='skill'then kind='skill1'end\n local si=tonumber(string.match(kind or '', '^skill([123])$'));if kind~='attack'and not si then return false end")
a=r.index(' local c=C[m.class];if s.t<m.busy');b=r.index(" emit(s,'action'",a)
r=r[:a]+''' local c=C[m.class];local cds={8,m.class=='mage'and 7 or 6,m.class=='mage'and 15 or 14};local delays=m.class=='mage'and{.65,.48,.95}or(m.class=='ranged'and{.38,.22,.65}or{.20,.22,.68})
 local key=si and(kind..'Until')or'attackUntil'
 if s.t<m.busy or s.t<(m[key]or 0)then return false end
 m[key]=s.t+(si and cds[si]or c.interval);m.busy=s.t+(si and(si==3 and 1.25 or 1)or c.interval)
 local e=target(s,m,dx,dz,c.range);if e and m.class~='melee'then local d=distance(e.x,e.z,m.x,m.z);if d>.01 then dx,dz=(e.x-m.x)/d,(e.z-m.z)/d end end
 local tx,tz=m.x+dx*6,m.z+dz*6;if e then tx,tz=e.x,e.z end
 local count=m.class=='ranged'and(si==1 and 5 or(si==3 and 3 or 1))or 1
 for i=1,count do s.queue[#s.queue+1]={at=s.t+(si and delays[si]or c.windup)+(i-1)*(si==3 and .32 or .16),owner=id,class=m.class,kind=kind,dx=dx,dz=dz,tx=tx,tz=tz,burst=i}end
''' +r[b:]
r=r.replace("emit(s,'hit',{x=e.x,z=e.z,damage=amount,dead=e.hp<=0})","emit(s,'hit',{x=e.x,z=e.z,damage=amount,dead=e.hp<=0,class=m and m.class})")
a=r.index(' if q.class==\'melee\'then',r.index('local function launch'));b=r.index('\nend\nlocal function segmentDistance',a)
r=r[:a]+''' local si=tonumber(string.match(q.kind,'^skill([123])$'))
 if q.class=='melee'then
  if si==1 then m.shield=s.t+3 end
  for _,e in ipairs(s.enemies)do if e.hp>0 then
   local dx,dz=e.x-m.x,e.z-m.z;local d=math.sqrt(dx*dx+dz*dz)
   local reach=si==3 and 5 or(si and 3.5 or c.range)
   if d<=reach and(si==1 or si==2 or d<.01 or(dx*q.dx+dz*q.dz)/d>=.5)then
    if si==1 then if d>.01 then e.x,e.z=clamp(e.x+dx/d*2,e.z+dz/d*2,s,.7)end;e.state='stun';e.timer=.8
    else damage(s,e,si==3 and 5 or(si==2 and 3 or c.damage),q.owner)end
   end
  end end
  emit(s,'slash',{x=m.x,z=m.z,dx=q.dx,dz=q.dz,kind=q.kind,class=q.class})
 elseif(q.class=='mage'and si)or(q.class=='ranged'and si==3)then
  local tx,tz=clamp(q.tx,q.tz,s,.5);local d=distance(tx,tz,m.x,m.z);if d>10 then tx,tz=m.x+(tx-m.x)*10/d,m.z+(tz-m.z)*10/d end
  local radius=si==3 and 3.6 or 3
  emit(s,'area',{x=tx,z=tz,class=q.class,kind=q.kind,burst=q.burst})
  for _,e in ipairs(s.enemies)do if e.hp>0 and distance(e.x,e.z,tx,tz)<=radius then
   damage(s,e,q.class=='ranged'and 1 or(si==3 and 5 or(si==2 and 2 or 3)),q.owner)
   if q.class=='mage'and si==2 then e.state='stun';e.timer=2 end
  end end
 else
  s.nextShot=s.nextShot+1;s.shots[#s.shots+1]={id=s.nextShot,owner=q.owner,class=q.class,x=m.x,z=m.z,dx=q.dx,dz=q.dz,left=c.range,speed=q.class=='mage'and 16 or 24,damage=si==2 and 3 or c.damage,pierce=si==2,hitIds={}}
  emit(s,'shot',{x=m.x,z=m.z,dx=q.dx,dz=q.dz,class=q.class,kind=q.kind})
 end''' +r[b:]
r=r.replace("if e.hp>0 then local d,t=segmentDistance", "if e.hp>0 and not q.hitIds[e.id]then local d,t=segmentDistance")
r=r.replace("if hit and not wall then damage(s,hit,q.damage,q.owner)end", "if hit and not wall then damage(s,hit,q.damage,q.owner);q.hitIds[hit.id]=true end")
r=r.replace('if hit or wall or q.left<=0','if (hit and not q.pierce)or wall or q.left<=0')
r=r.replace("e.state='windup';e.timer=e.elite and 1.1 or .8;", "e.state='windup';e.timer=e.elite and 1.1 or .8;e.attackStart=s.t;e.attackDuration=e.timer;")
p.write_text(r)
# Smaller real held meshes. Leave original wardrobe untouched.
p=S/'dragon_weapons.lua';r=p.read_text();r=r.replace('clamp(reach*2.7,1.5,2.4)or(entry.className=="ranged"and clamp(reach*1.3,.7,1.2)or clamp(reach*1.8,1,1.7))','clamp(reach*1.65,.65,1.15)or(entry.className=="ranged"and clamp(reach*1.15,.48,.82)or clamp(reach*1.25,.5,.95))');r=r.replace('  skill2 = true,','  skill2 = true,\n  skill3 = true,');p.write_text(r);(D.parent/p.name).write_text(r)
# Reuse source timeline; third actions get distinct duration, not basic attack fallback.
p=S/'dragon_timeline.lua';r=p.read_text();idx=r.index('\nlocal function',r.index('local TIMELINES='));r=r[:idx]+'''
for _,kind in ipairs({'melee','ranged','mage'})do
 local from=TIMELINES[kind].skill1;local t={duration=kind=='mage'and 1.2 or 1.05,keys={}}
 for _,k in ipairs(from.keys)do local n={};for a,b in pairs(k)do n[a]=b end;n.t=k.t/from.duration*t.duration;t.keys[#t.keys+1]=n end
 TIMELINES[kind].skill3=t
end
''' +r[idx:];p.write_text(r);(D.parent/p.name).write_text(r)
print('rules, nine skills, weapon scale, timelines updated')
