---@id f554579e-f9d9-438d-a027-577b6310c6e2
---@referenceName dragon_rules.lua
-- RPG 职业与动作规则；由绑定的协调器调用，不依赖表现层。
---@displayName 龙眠职业与战斗规则
local classes={
 melee={name="骑士",weapon="剑",skill="破晓守护",cooldown=8,attackInterval=.55,hitDelay=.23,range=2.8,hp=6},
 mage={name="法师",weapon="法杖",skill="星火爆裂",cooldown=8,attackInterval=.7,hitDelay=.3,range=12,hp=5},
 ranged={name="游侠",weapon="弓",skill="月羽连射",cooldown=8,attackInterval=.65,hitDelay=.33,range=18,hp=5},
}
local skills={
 melee={{name="破晓守护",icon="shield",cooldown=8,delay=.20},{name="回旋斩",icon="spin",cooldown=6,delay=.22},{name="巨剑裁决",icon="judgement",cooldown=14,delay=.68}},
 ranged={{name="月羽连射",icon="volley",cooldown=8,delay=.38},{name="贯晶箭",icon="pierce",cooldown=6,delay=.22},{name="万箭齐下",icon="rain",cooldown=14,delay=.65}},
 mage={{name="星火爆裂",icon="nova",cooldown=8,delay=.65},{name="霜星禁锢",icon="frost",cooldown=7,delay=.48},{name="陨星裁决",icon="meteor",cooldown=15,delay=.95}}
}
for k,v in pairs(classes)do v.skills=skills[k]end
function GetClasses() return classes end
function NewProfile()
 return {schema=1,class=nil,moon=0,ember=0,stardew=0,mushroom=0,flower=0,wool=0,
  deposited={moon=0,ember=0,stardew=0},pact=false,rewards={}}
end
function SelectClass(profile,kind,inBattle)
 if not classes[kind]then return false,"请选择职业"end
 if inBattle then return false,"战斗结束后才能重新签约"end
 profile.class=kind
 return true
end
function CanUse(context)
 if not context or not classes[context.class]then return false,"先在古书签约"end
 if context.mode~="combat"or context.menu or context.mounted or context.flying or context.dead then return false,"当前不能使用武器"end
 return true
end
function TryAction(context,kind,now)
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
function InsideCircle(x,z,cx,cz,radius)
 return (x-cx)^2+(z-cz)^2<=radius*radius
end
function ClampCircle(x,z,cx,cz,radius)
 local dx,dz=x-cx,z-cz;local d=math.sqrt(dx*dx+dz*dz)
 if d<=radius then return x,z end
 return cx+dx*radius/d,cz+dz*radius/d
end
function RewardVictory(profile,battleId,contributed,eligible)
 if not contributed or not eligible or not battleId or profile.rewards[battleId]then return false end
 profile.rewards[battleId]=true;profile.moon=profile.moon+10
 return true
end
function Deposit(profile)
 local costs={moon=30,ember=3,stardew=1};local moved=0
 for key,cost in pairs(costs)do
  local amount=math.max(0,math.min(profile[key]or 0,cost-(profile.deposited[key]or 0)))
  profile[key]=(profile[key]or 0)-amount;profile.deposited[key]=(profile.deposited[key]or 0)+amount;moved=moved+amount
 end
 profile.pact=profile.deposited.moon==30 and profile.deposited.ember==3 and profile.deposited.stardew==1
 return moved,profile.pact
end
