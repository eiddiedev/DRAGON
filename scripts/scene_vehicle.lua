-- Native seat lifecycle shared by the horse, boats and flying carpet.
---@displayName 骑乘控制
local U=CS.UnityEngine
local kind=__KIND__
local H=__HEIGHT_GRID__
local seated,saved={},{}
local button,seat,localId,passenger=nil,nil,nil,nil
local home,homeRot,baseOffset,yaw,speed,progress
local moveX,moveY=0,0
local lastClip=nil
local floorOffset=0
local function external(c)
 if not c or c.isTrigger then return false end
 local t=c.transform
 if t==self.transform or t:IsChildOf(self.transform) then return false end
 if passenger and (t==passenger.gameObject.transform or t:IsChildOf(passenger.gameObject.transform)) then return false end
 return true
end
local function surface(x,z,y)
 local hits=U.Physics.RaycastAll(U.Vector3(x,y+.8,z),U.Vector3.down,4.0,-1,U.QueryTriggerInteraction.Ignore)
 local best=nil
 for i=0,hits.Length-1 do local h=hits[i];if external(h.collider) and h.normal.y>.55 and (not best or h.point.y>best) then best=h.point.y end end
 return best
end
local function clearPath(p,delta,floor)
 if delta.magnitude<.001 then return true end
 local hits=U.Physics.CapsuleCastAll(p+U.Vector3(0,.85,0),p+U.Vector3(0,1.7,0),.42,delta.normalized,delta.magnitude+.12,-1,U.QueryTriggerInteraction.Ignore)
 for i=0,hits.Length-1 do local h=hits[i];if external(h.collider) and h.distance>.001 and h.normal.y<.55 and U.Vector3.Dot(h.normal,delta.normalized)<-.05 and h.point.y>math.max(p.y,floor or p.y)+.65 then return false end end
 return true
end
local path={{112,60,38},{150,86,62},{175,74,104},{196,84,140},{196,110,188},{166,122,196},{128,118,204},{82,108,196},{92,94,150},{120,98,126},{86,78,96},{62,64,44}}
local segment=1
local function ground(x,z)
 local a=math.max(0,math.min(63.999,x/4));local b=math.max(0,math.min(63.999,z/4))
 local ix,iz=math.floor(a),math.floor(b);a=a-ix;b=b-iz
 return (H[iz+1][ix+1]*(1-a)+H[iz+1][ix+2]*a)*(1-b)+(H[iz+2][ix+1]*(1-a)+H[iz+2][ix+2]*a)*b
end
local function label()
 if not button then return end
 local t=button:GetComponentInChildren(typeof(U.UI.Text),true)
 if t then t.text=passenger and (kind=='horse' and '下马' or kind=='boat' and '下船' or '结束飞行') or (kind=='horse' and '骑马' or kind=='boat' and '开船' or '乘坐飞毯') end
end
local function play(name)
 if lastClip==name then return end
 local a=self.gameObject:GetComponent(typeof(CS.ModularAnim.Runtime.UGCAnimator))
 if a and a.enabled and a.Controller~=nil and a:Play(name) then lastClip=name end
end
local function align(actor)
 local s=saved[actor];if not s or not seat then return end
 local tr=actor.gameObject.transform
 tr:SetParent(seat.transform,true);tr.localScale=s.scale;tr.localRotation=U.Quaternion.identity;tr.localPosition=U.Vector3.zero
 local an=actor.gameObject:GetComponentInChildren(typeof(U.Animator),true)
 if an then
  local hips=an:GetBoneTransform(U.HumanBodyBones.Hips)
  if hips then tr.position=tr.position-(hips.position-tr.position) end
  if kind=='horse' then
   -- Retarget seated thighs out to the saddle sides; calves hang down.
   local function aim(a,b,d)
    local j=an:GetBoneTransform(a);local k=an:GetBoneTransform(b)
    if j and k then j.rotation=U.Quaternion.FromToRotation(k.position-j.position,d)*j.rotation end
   end
   local f=seat.transform.forward;local r=seat.transform.right
   aim(U.HumanBodyBones.LeftUpperLeg,U.HumanBodyBones.LeftLowerLeg,-r*.7+f*.35+U.Vector3.down*.6)
   aim(U.HumanBodyBones.RightUpperLeg,U.HumanBodyBones.RightLowerLeg,r*.7+f*.35+U.Vector3.down*.6)
   aim(U.HumanBodyBones.LeftLowerLeg,U.HumanBodyBones.LeftFoot,U.Vector3.down-f*.18)
   aim(U.HumanBodyBones.RightLowerLeg,U.HumanBodyBones.RightFoot,U.Vector3.down-f*.18)
  end
 end
end
local function setSeat()
 local t=self.transform
 if kind=='horse' then seat.transform.position=t:TransformPoint(U.Vector3(0,.72,.025))
 elseif kind=='boat' then seat.transform.position=t:TransformPoint(U.Vector3(0,.72,-2.0))
 else seat.transform.position=t.position+U.Vector3(0,.55,0) end
 seat.transform.rotation=U.Quaternion.Euler(0,yaw,0)
end
function Start()
 home=self.transform.position;homeRot=self.transform.rotation
 baseOffset=home.y-ground(home.x,home.z);yaw=homeRot.eulerAngles.y-(kind=='horse' and 180 or kind=='boat' and 180 or 0)
 speed=0;progress=0
 seat=U.GameObject(self.gameObject.name..'_SeatAnchor');seat.transform.localScale=U.Vector3.one;setSeat()
 DouyinInputService.onMoveInputPerform:AddListener(OnMove)
 DouyinInputService.onMoveInputCancel:AddListener(OnMoveStop)
 if kind=='horse' then floorOffset=.02;play('Idle') end
end
function OnMove(v) if passenger then moveX=v.x;moveY=v.y end end
function OnMoveStop() moveX=0;moveY=0 end
function OnActorTriggerEnter(actor)
 if not actor or not actor.isLocal then return end
 localId=actor.actorID;self:EnableInteraction()
end
function OnActorTriggerExit(actor)
 if not actor or not actor.isLocal or passenger then return end
 self:DisableInteraction();localId=nil
end
function OnFocus()
 if not button then button=self:AddInteractorButton() end
 label()
end
function OnLostFocus()
 if button then self:RemoveInteractorButton(button);button=nil end
end
function OnInteractorButtonClick(index)
 if index~=1 or not localId then return end
 local actor=DouyinActorService.GetActorById(localId);if not actor then return end
 if passenger then actor:StandUp(self.gameObject)
 elseif seat and not actor:IsFlying() then actor:SitDown(self.gameObject) end
end
function OnSeatEntered(actor)
 if not actor or seated[actor] then return end
 local tr=actor.gameObject.transform;local cols=actor.gameObject:GetComponents(typeof(U.Collider));local cs={}
 for i=0,cols.Length-1 do cs[#cs+1]={c=cols[i],enabled=cols[i].enabled};cols[i].enabled=false end
 saved[actor]={scale=tr.localScale,position=tr.position,rotation=tr.rotation,colliders=cs}
 seated[actor]=true;setSeat();align(actor)
 if actor.isLocal then
  passenger=actor;localId=actor.actorID;self:EnableInteraction();OnFocus();moveX=0;moveY=0;speed=0;segment=1
  DouyinCameraService.SetDistance(kind=='horse' and 7 or kind=='boat' and 12 or 9)
  U.Debug.Log('[interaction] boarded '..kind)
 end
end
function OnSeatExited(actor)
 if not actor then return end
 seated[actor]=nil;local s=saved[actor]
 local tr=actor.gameObject.transform;tr:SetParent(nil,true)
 if s then
  tr.localScale=s.scale
  for _,v in ipairs(s.colliders) do v.c.enabled=v.enabled end
  local p=self.transform.position+self.transform.right*2
  if kind=='boat' or kind=='carpet' then p=s.position else p.y=(surface(p.x,p.z,self.transform.position.y) or self.transform.position.y)+.1 end
  actor:Teleport(p,s.rotation);saved[actor]=nil
 end
 if actor.isLocal then passenger=nil;speed=0;moveX=0;moveY=0;label();DouyinCameraService.SetDistance(7);U.Debug.Log('[interaction] dismounted '..kind) end
 if kind=='horse' then play('Idle') end
end
function Update()
 if not seat then return end
 local dt=math.min(U.Time.deltaTime,.05);local t=self.transform
 if passenger then
  if kind=='carpet' then
   local q=path[segment];local target=q and U.Vector3(q[1],q[2],q[3]) or home
   local d=target-t.position;local step=12*dt
   if d.magnitude<step then t.position=target;segment=segment+1;if segment>#path+1 then passenger:StandUp(self.gameObject) end
   else t.position=t.position+d.normalized*step;yaw=math.deg(math.atan(d.x,d.z));t.rotation=U.Quaternion.Euler(0,yaw+180,0) end
  else
   local x,y=moveX,moveY
   if U.Input.GetKey('w') then y=y+1 end;if U.Input.GetKey('s') then y=y-1 end
   if U.Input.GetKey('a') then x=x-1 end;if U.Input.GetKey('d') then x=x+1 end
   local mag=math.min(1,math.sqrt(x*x+y*y));local targetSpeed=0
   if mag>.12 then
    if kind=='horse' then targetSpeed=mag<.55 and (mag-.12)/.43*3.2 or 3.2+(mag-.55)/.45*6.3
    else targetSpeed=mag*8 end
   end
   if mag>.05 then
    local want=DouyinCameraService.GetYaw()+math.deg(math.atan(x,y));local diff=(want-yaw+540)%360-180
    yaw=yaw+math.max(-100*dt,math.min(100*dt,diff))
   end
   speed=speed+(targetSpeed-speed)*math.min(1,dt*4)
   local p=t.position;local nx=p.x+math.sin(math.rad(yaw))*speed*dt;local nz=p.z+math.cos(math.rad(yaw))*speed*dt
   local h=ground(nx,nz)
   if kind=='horse' then
    local floor=surface(nx,nz,p.y-floorOffset)
    local delta=U.Vector3(nx-p.x,0,nz-p.z)
    if floor and floor>27.4 and floor+floorOffset-p.y<.8 and p.y-floor-floorOffset<3.2 and clearPath(p,delta,floor) then t.position=U.Vector3(nx,math.max(floor+floorOffset,p.y-7*dt),nz) else speed=0 end
    play(speed<.2 and 'Idle' or speed<2.4 and 'Walk' or speed<5.5 and 'Trot' or speed<8 and 'Run' or 'RunFast')
   elseif h<27.4 or (nx-home.x)^2+(nz-home.z)^2<16^2 then t.position=U.Vector3(nx,home.y+.08*math.sin(U.Time.time),nz) else speed=0 end
   t.rotation=U.Quaternion.Euler(0,yaw+180,0)
  end
 elseif kind=='carpet' then t.position=U.Vector3.Lerp(t.position,home,math.min(1,dt*2));t.rotation=U.Quaternion.Slerp(t.rotation,homeRot,dt*2) end
 setSeat()
end
function LateUpdate() for actor,_ in pairs(seated) do align(actor) end end
function OnDestroy()
 for actor,_ in pairs(seated) do pcall(function() actor:StandUp(self.gameObject);OnSeatExited(actor) end) end
 pcall(function() DouyinInputService.onMoveInputPerform:RemoveListener(OnMove);DouyinInputService.onMoveInputCancel:RemoveListener(OnMoveStop) end)
 if seat then U.Object.Destroy(seat) end
end
