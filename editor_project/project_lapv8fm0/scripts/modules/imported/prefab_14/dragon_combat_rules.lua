---@id bd38d583-5faf-47e3-b41d-c6efd14f319c
---@sourceScriptId f8282ad6-a565-4d4e-a7b9-6cd59266b13a
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
 s.stage=(s.stage or 0)+1;s.nextEnemy=s.nextEnemy or 0
 local players=0;for _,m in pairs(s.members)do if m.hp>0 then players=players+1 end end
 local count=({4,5,3})[s.stage];local hpScale=1+math.max(0,players-1)*.55
 for i=1,count do local a=(i-1)*math.pi*2/count+s.stage*.6
  local boss=s.stage==3 and i==1;local elite=boss or(s.stage==2 and i>=4)
  local hp=math.ceil((boss and 30 or(elite and 12 or 7))*hpScale)
  s.nextEnemy=s.nextEnemy+1
  s.enemies[#s.enemies+1]={id=s.nextEnemy,x=s.x+math.sin(a)*7.5,z=s.z+math.cos(a)*7.5,hp=hp,maxHP=hp,speed=boss and 1.15 or(elite and 1.2 or 1.7),state='recover',timer=1+i*.2,hit=0,elite=elite,boss=boss}
 end
 s.phase='active';s.intermission=nil;emit(s,'begin',{stage=s.stage})
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
 if kind=='skill'then kind='skill1'end
 local si=tonumber(string.match(kind or '', '^skill([123])$'));if kind~='attack'and not si then return false end
 if type(dx)~='number'or type(dz)~='number'or dx~=dx or dz~=dz then return false end
 local length=math.sqrt(dx*dx+dz*dz);if length<.001 or length>2 then return false end;dx,dz=dx/length,dz/length
 local c=C[m.class];local cds={8,m.class=='mage'and 7 or 6,m.class=='mage'and 15 or 14};local delays=m.class=='mage'and{.65,.48,.95}or(m.class=='ranged'and{.38,.22,.65}or{.20,.22,.68})
 local key=si and(kind..'Until')or'attackUntil'
 if s.t<m.busy or s.t<(m[key]or 0)then return false end
 m[key]=s.t+(si and cds[si]or c.interval);m.busy=s.t+(si and(si==3 and 1.25 or 1)or c.interval)
 local e=target(s,m,dx,dz,c.range);if e and m.class~='melee'then local d=distance(e.x,e.z,m.x,m.z);if d>.01 then dx,dz=(e.x-m.x)/d,(e.z-m.z)/d end end
 local tx,tz=m.x+dx*6,m.z+dz*6;if e then tx,tz=e.x,e.z end
 local count=m.class=='ranged'and(si==1 and 5 or(si==3 and 3 or 1))or 1
 for i=1,count do s.queue[#s.queue+1]={at=s.t+(si and delays[si]or c.windup)+(i-1)*(si==3 and .32 or .16),owner=id,class=m.class,kind=kind,dx=dx,dz=dz,tx=tx,tz=tz,burst=i}end
 emit(s,'action',{owner=id,class=m.class,kind=kind,x=m.x,z=m.z,tx=tx,tz=tz});return true
end
local function damage(s,e,value,owner)
 if e.hp<=0 then return end;local amount=math.min(e.hp,value);e.hp=e.hp-amount;e.hit=s.t+.18
 local m=s.members[owner];if m then m.damage=m.damage+amount end
 emit(s,'hit',{x=e.x,z=e.z,damage=amount,dead=e.hp<=0,class=m and m.class,owner=owner,enemyId=e.id})
end
local function launch(s,q)
 local m=s.members[q.owner];if not m or m.hp<=0 then return end;local c=C[q.class]
 local si=tonumber(string.match(q.kind,'^skill([123])$'))
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
  for _,e in ipairs(s.enemies)do if e.hp>0 and not q.hitIds[e.id]then local d,t=segmentDistance(e.x,e.z,q.x,q.z,nx,nz);if d<(e.elite and .7 or .5)and t<best then hit=e;best=t end end end
  local wall=blocked and blocked(q.x,q.z,nx,nz)
  if hit and not wall then damage(s,hit,q.damage,q.owner);q.hitIds[hit.id]=true end
  q.left=q.left-step;q.x,q.z=nx,nz
  if (hit and not q.pierce)or wall or q.left<=0 or distance(nx,nz,s.x,s.z)>s.radius then table.remove(s.shots,i)end
 end
 local enemiesAlive=0
 for _,e in ipairs(s.enemies)do if e.hp>0 then
  enemiesAlive=enemiesAlive+1;local closest,dist=nil,1e9
  for id,m in pairs(s.members)do if m.hp>0 then local d=distance(e.x,e.z,m.x,m.z);if d<dist then closest=m;dist=d end end end
  if closest then
   -- Authority owns facing; freeze aim through windup/lunge/recovery so dodges remain readable.
   if e.state=='chase'or not e.faceX then local dx,dz=closest.x-e.x,closest.z-e.z;local d=math.sqrt(dx*dx+dz*dz);if d>.001 then e.faceX,e.faceZ=dx/d,dz/d end end
   if e.state=='windup'then e.timer=e.timer-dt;if e.timer<=0 then
    e.state='lunge';e.timer=.28;e.lungeStartX=e.x;e.lungeStartZ=e.z
    emit(s,'strike',{x=e.x,z=e.z,enemyId=e.id})
   end
   elseif e.state=='lunge'then
    e.timer=math.max(0,e.timer-dt);local t=1-e.timer/.28
    e.x,e.z=clamp(e.lungeStartX+(e.tx-e.lungeStartX)*t,e.lungeStartZ+(e.tz-e.lungeStartZ)*t,s,.7)
    if e.timer<=0 then
     for id,m in pairs(s.members)do if m.hp>0 and distance(e.x,e.z,m.x,m.z)<(e.boss and 2.1 or 1.35)and s.t>=m.invulnerable and s.t>=m.shield then
      local amount=math.min(m.hp,e.elite and 2 or 1);m.hp=m.hp-amount;m.invulnerable=s.t+.85
      emit(s,'hurt',{owner=id,x=m.x,z=m.z,damage=amount})
     end end
     e.state='recover';e.timer=e.boss and 1.25 or 1.5
    end
   elseif e.state=='recover'or e.state=='stun'then e.timer=e.timer-dt;if e.timer<=0 then e.state='chase'end
   elseif dist<(e.boss and 3 or 2.3)then e.state='windup';e.timer=e.elite and 1.1 or .8;e.attackStart=s.t;e.attackDuration=e.timer;local dx,dz=closest.x-e.x,closest.z-e.z;local d=math.sqrt(dx*dx+dz*dz);e.tx,e.tz=closest.x,closest.z;if d>.9 then e.tx,e.tz=closest.x-dx/d*.9,closest.z-dz/d*.9 end;emit(s,'tell',{x=e.tx,z=e.tz})
   elseif dist>.01 then local step=math.min(dist-1.3,e.speed*dt);e.x,e.z=clamp(e.x+(closest.x-e.x)/dist*step,e.z+(closest.z-e.z)/dist*step,s,.7)end
  end
 end end
 if enemiesAlive==0 then
  s.queue={};s.shots={}
  if s.stage<3 then
   if not s.intermission then s.intermission=s.t+3;emit(s,'reinforcement',{stage=s.stage+1})end
   if s.t>=s.intermission then for _,m in pairs(s.members)do if m.hp>0 then m.hp=math.min(m.maxHP,m.hp+1)end end;Spawn(s)end
  else s.phase='victory';emit(s,'victory')end
 end
end
function Boundary(s,x,z)return clamp(x,z,s,.5)end
