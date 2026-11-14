-- v31 备用步态：提审端平台动画不播时（腿骨一秒多没动），由脚本直接摆动四条腿的骨骼。
-- 不依赖动画资源；平台动画正常时它只做检测，不接管。
local function createGait(owner,tag)
 local g={legs={},on=false,probeT=0,probeMove=0,t=0,amp=0,axis=U.Vector3.right,nextSay=0,tries=0}
 local function bind()
  if g.bound then return true end
  local now=U.Time.realtimeSinceStartup
  if now<(g.nextBind or 0)then return false end;g.nextBind=now+1
  local ts=owner:GetComponentsInChildren(typeof(U.Transform),true)
  g.legs={}
  for i=0,ts.Length-1 do local t=ts[i]
   local a,side,idx=string.match(t.name,'^tripo::(%d)_(%a+)_Limb_(%d)$')
   if a and(idx=='0'or idx=='1')then g.legs[#g.legs+1]={t=t,base=t.localRotation,front=a=='0',left=side=='Left',upper=idx=='0'}end
  end
  if #g.legs>=4 then g.bound=true end
  return g.bound
 end
 function g.tick(moving,speed,dir,dt)
  local now=U.Time.realtimeSinceStartup
  if tag and now>=g.nextSay then g.nextSay=now+1
   pcall(function()U.PlayerPrefs.SetString('dr_diag_'..tag,tostring(g.status and g.status()or'-')..(g.on and'+步态'or'')..' 腿'..#g.legs)end)
  end
  if not bind()then return end
  if dir and dir.sqrMagnitude>.0001 then g.axis=U.Vector3.Cross(U.Vector3.up,dir.normalized)end
  if not g.on then
   if moving then
    local cur=g.legs[1].t.localRotation
    if g.prev then g.probeMove=g.probeMove+U.Quaternion.Angle(g.prev,cur)end
    g.prev=cur;g.probeT=g.probeT+dt
    if g.probeT>1.2 then
     if g.probeMove<1.5 then g.on=true;for _,l in ipairs(g.legs)do l.base=l.t.localRotation end end
     g.probeT=0;g.probeMove=0
    end
   else g.prev=nil;g.probeT=0;g.probeMove=0 end
   return
  end
  local want=moving and math.min(34,14+speed*3.5)or 0
  g.amp=g.amp+(want-g.amp)*math.min(1,dt*6)
  g.t=g.t+dt*(5+math.min(speed,8)*1.2)
  for _,l in ipairs(g.legs)do
   local phase=(l.front==l.left)and 0 or math.pi
   local a=math.sin(g.t+phase)*g.amp
   if not l.upper then a=-math.max(0,math.sin(g.t+phase+1.1))*g.amp*.8 end
   l.t.localRotation=l.base
   if math.abs(a)>.05 then l.t:Rotate(g.axis,a,U.Space.World)end
  end
 end
 return g
end
