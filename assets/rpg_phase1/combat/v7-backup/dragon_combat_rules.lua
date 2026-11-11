---@id f8282ad6-a565-4d4e-a7b9-6cd59266b13a
---@referenceName dragon_combat_rules.lua
-- Deterministic encounter simulation. No rendering, network or avatar side effects.
---@displayName 龙眠魔法阵战斗规则
local C={melee={hp=6,damage=2,range=2.8,interval=.55,windup=.23,skillDelay=.20,cooldown=8},mage={hp=5,damage=1,range=12,interval=.7,windup=.28,skillDelay=.65,cooldown=8},ranged={hp=5,damage=1,range=18,interval=.65,windup=.18,skillDelay=.38,cooldown=8}}
local function distance(x,z,a,b)return math.sqrt((x-a)^2+(z-b)^2)end
local function clamp(x,z,s,padding)
 local dx,dz=x-s.x,z-s.z;local d=math.sqrt(dx*dx+dz*dz);local r=s.radius-(padding or 0)
 if d>r then return s.x+dx*r/d,s.z+dz*r/d end;return x,z
end
local function emit(s,kind,data)
 s.eventId=s.eventId+1;data=data or {};data.id=s.eventId;data.type=kind;data.time=s.t;s.events[#s.events+1]=data
 if #s.events>32 then table.remove(s.events,1)end
end
function Classes()return C end
function New(x,y,z,radius,epoch)
 return {schema=1,epoch=epoch,x=x,y=y,z=z,radius=radius,t=0,phase='ready',members={},enemies={},shots={},queue={},events={},eventId=0,nextShot=0,prep=2}
end
function Join(s,id,class,pos)
 if not C[class]or not pos or s.phase~='ready' or s.members[id]then return false end
 if distance(pos.x,pos.z,s.x,s.z)>s.radius then return false end
 s.members[id]={class=class,hp=C[class].hp,maxHP=C[class].hp,damage=0,ack=0,attackUntil=0,skillUntil=0,busy=0,shield=0,invulnerable=0,x=pos.x,z=pos.z}
 return true
end
function Spawn(s)
 for i=1,4 do local a=(i-1)*math.pi*.5
  s.enemies[i]={id=i,x=s.x+math.sin(a)*5,z=s.z+math.cos(a)*5,hp=i==4 and 8 or 4,maxHP=i==4 and 8 or 4,speed=i==4 and .9 or 1.25,state='chase',timer=0,hit=0,elite=i==4}
 end
 s.phase='active';emit(s,'begin')
end
local function target(s,m,dx,dz,range)
 local best,score=nil,-1e9
 for _,e in ipairs(s.enemies)do if e.hp>0 then local x,z=e.x-m.x,e.z-m.z;local d=math.sqrt(x*x+z*z);local dot=d>.01 and(x*dx+z*dz)/d or 1
  if d<=range then local v=dot*3-d*.15;if v>score then best=e;score=v end end
 end end
 return best
end
function Aim(s,id,dx,dz,range)
 local m=s.members[id];if not m then return nil end;return target(s,m,dx,dz,range)
end
function Request(s,id,seq,kind,dx,dz)
 local m=s.members[id];if not m or s.phase~='active'or m.hp<=0 or type(seq)~='number'or seq%1~=0 or seq<=m.ack then return false end
 m.ack=seq
 if kind=='retreat'then m.hp=0;m.retreat=true;return true end
 if kind~='attack'and kind~='skill'then return false end
 if type(dx)~='number'or type(dz)~='number'or dx~=dx or dz~=dz then return false end
 local length=math.sqrt(dx*dx+dz*dz);if length<.001 or length>2 then return false end;dx,dz=dx/length,dz/length
 local c=C[m.class];if s.t<m.busy or s.t<(kind=='skill'and m.skillUntil or m.attackUntil)then return false end
 if kind=='skill'then m.skillUntil=s.t+c.cooldown else m.attackUntil=s.t+c.interval end
 m.busy=s.t+(kind=='skill'and 1.2 or c.interval)
 local e=target(s,m,dx,dz,c.range);if e and m.class~='melee'then local d=distance(e.x,e.z,m.x,m.z);if d>.01 then dx,dz=(e.x-m.x)/d,(e.z-m.z)/d end end
 local tx,tz=m.x+dx*6,m.z+dz*6;if e then tx,tz=e.x,e.z end
 local count=m.class=='ranged'and kind=='skill'and 5 or 1
 for i=1,count do s.queue[#s.queue+1]={at=s.t+(kind=='skill'and c.skillDelay or c.windup)+(i-1)*.16,owner=id,class=m.class,kind=kind,dx=dx,dz=dz,tx=tx,tz=tz}end
 emit(s,'action',{owner=id,class=m.class,kind=kind});return true
end
local function damage(s,e,value,owner)
 if e.hp<=0 then return end;local amount=math.min(e.hp,value);e.hp=e.hp-amount;e.hit=s.t+.18
 local m=s.members[owner];if m then m.damage=m.damage+amount end
 emit(s,'hit',{x=e.x,z=e.z,damage=amount,dead=e.hp<=0})
end
local function launch(s,q)
 local m=s.members[q.owner];if not m or m.hp<=0 then return end;local c=C[q.class]
 if q.class=='melee'then
  if q.kind=='skill'then m.shield=s.t+3;emit(s,'shield',{owner=q.owner,x=m.x,z=m.z})end
  for _,e in ipairs(s.enemies)do if e.hp>0 then local dx,dz=e.x-m.x,e.z-m.z;local d=math.sqrt(dx*dx+dz*dz)
   if d<=(q.kind=='skill'and 3.5 or c.range)and(q.kind=='skill'or d<.01 or(dx*q.dx+dz*q.dz)/d>=.5)then
    if q.kind=='skill'then if d>.01 then e.x,e.z=clamp(e.x+dx/d*2,e.z+dz/d*2,s,.7)end;e.state='stun';e.timer=.8
    else damage(s,e,c.damage,q.owner)end
   end
  end end
  emit(s,'slash',{x=m.x,z=m.z,dx=q.dx,dz=q.dz,skill=q.kind=='skill'})
 elseif q.class=='mage'and q.kind=='skill'then
  local tx,tz=clamp(q.tx,q.tz,s,.5);local d=distance(tx,tz,m.x,m.z);if d>6 then tx,tz=m.x+(tx-m.x)*6/d,m.z+(tz-m.z)*6/d end
  emit(s,'blast',{x=tx,z=tz});for _,e in ipairs(s.enemies)do if distance(e.x,e.z,tx,tz)<=3 then damage(s,e,3,q.owner)end end
 else
  s.nextShot=s.nextShot+1;s.shots[#s.shots+1]={id=s.nextShot,owner=q.owner,class=q.class,x=m.x,z=m.z,dx=q.dx,dz=q.dz,left=c.range,speed=q.class=='mage'and 16 or 24,damage=c.damage}
  emit(s,'shot',{x=m.x,z=m.z,dx=q.dx,dz=q.dz,class=q.class})
 end
end
local function segmentDistance(px,pz,ax,az,bx,bz)
 local dx,dz=bx-ax,bz-az;local len=dx*dx+dz*dz;local t=len>0 and math.max(0,math.min(1,((px-ax)*dx+(pz-az)*dz)/len))or 0
 return distance(px,pz,ax+dx*t,az+dz*t),t
end
function Step(s,dt,positions,blocked)
 if s.phase~='ready'and s.phase~='active'then return end;dt=math.max(0,math.min(.1,dt));s.t=s.t+dt
 local alive=0
 for id,m in pairs(s.members)do local p=positions[id]
  if p then m.x,m.z=clamp(p.x,p.z,s,.5);m.missing=0 else m.missing=(m.missing or 0)+dt;if m.missing>5 then m.hp=0 end end
  if m.hp>0 then alive=alive+1 end
 end
 if alive==0 then s.phase='defeat';emit(s,'defeat');return end
 if s.phase=='ready'then if s.t>=s.prep then Spawn(s)end;return end
 for i=#s.queue,1,-1 do local q=s.queue[i];if q.at<=s.t then launch(s,q);table.remove(s.queue,i)end end
 for i=#s.shots,1,-1 do local q=s.shots[i];local step=math.min(q.left,q.speed*dt);local nx,nz=q.x+q.dx*step,q.z+q.dz*step;local hit,best=nil,2
  for _,e in ipairs(s.enemies)do if e.hp>0 then local d,t=segmentDistance(e.x,e.z,q.x,q.z,nx,nz);if d<(e.elite and .7 or .5)and t<best then hit=e;best=t end end end
  local wall=blocked and blocked(q.x,q.z,nx,nz)
  if hit and not wall then damage(s,hit,q.damage,q.owner)end
  q.left=q.left-step;q.x,q.z=nx,nz
  if hit or wall or q.left<=0 or distance(nx,nz,s.x,s.z)>s.radius then table.remove(s.shots,i)end
 end
 local enemiesAlive=0
 for _,e in ipairs(s.enemies)do if e.hp>0 then
  enemiesAlive=enemiesAlive+1;local closest,dist=nil,1e9
  for id,m in pairs(s.members)do if m.hp>0 then local d=distance(e.x,e.z,m.x,m.z);if d<dist then closest=m;dist=d end end end
  if closest then
   if e.state=='windup'then e.timer=e.timer-dt;if e.timer<=0 then
    -- Target position is locked when the tell begins: movement can dodge the strike.
    e.x,e.z=clamp(e.tx,e.tz,s,.7)
    for id,m in pairs(s.members)do if m.hp>0 and distance(e.x,e.z,m.x,m.z)<1.1 and s.t>=m.invulnerable and s.t>=m.shield then
     m.hp=math.max(0,m.hp-(e.elite and 2 or 1));m.invulnerable=s.t+1.1;emit(s,'hurt',{owner=id,x=m.x,z=m.z})
    end end
    e.state='recover';e.timer=1.8;emit(s,'strike',{x=e.x,z=e.z})
   end
   elseif e.state=='recover'or e.state=='stun'then e.timer=e.timer-dt;if e.timer<=0 then e.state='chase'end
   elseif dist<1.8 then e.state='windup';e.timer=e.elite and 1.1 or .8;local dx,dz=closest.x-e.x,closest.z-e.z;local d=math.sqrt(dx*dx+dz*dz);e.tx,e.tz=closest.x,closest.z;if d>.9 then e.tx,e.tz=closest.x-dx/d*.9,closest.z-dz/d*.9 end;emit(s,'tell',{x=e.tx,z=e.tz})
   elseif dist>.01 then local step=math.min(dist-1.3,e.speed*dt);e.x,e.z=clamp(e.x+(closest.x-e.x)/dist*step,e.z+(closest.z-e.z)/dist*step,s,.7)end
  end
 end end
 if enemiesAlive==0 then s.phase='victory';s.queue={};s.shots={};emit(s,'victory')end
end
function Boundary(s,x,z)return clamp(x,z,s,.5)end
