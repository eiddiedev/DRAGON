---@id 5a9edffe-7c92-477d-bc9c-9865e864567e
---@referenceName tripo_sheep_motion.lua
-- Physical sheep: preserve impulses instead of snapping to pasture coordinates.
---@displayName 可推动绵羊
local U=CS.UnityEngine
local rb,home,target,anim,last=nil,nil,nil,nil,nil
local nextChoice,pushedUntil=0,0
local previousActor=nil
local nextPush=0
local function play(name)
 if name~=last and anim and anim.enabled and anim.Controller and anim:Play(name) then last=name end
end
function Start()
 rb=self.gameObject:GetComponent(typeof(U.Rigidbody));home=self.transform.position
 anim=self.gameObject:GetComponent(typeof(CS.ModularAnim.Runtime.UGCAnimator))
 if not rb then U.Debug.LogError('Sheep physics body is missing');return end
 local c=self.gameObject:GetComponent(typeof(U.CapsuleCollider))
 if not c then c=self.gameObject:AddComponent(typeof(U.CapsuleCollider));c.center=U.Vector3(0,.45,0);c.radius=.28;c.height=1.05;c.direction=2 end
 rb.constraints=U.RigidbodyConstraints.FreezeRotation
 nextChoice=U.Time.time+2+math.random()*4
end
function FixedUpdate()
 if not rb then return end
 local now=U.Time.time;local dt=U.Time.fixedDeltaTime;local p=rb.position
 local a=DouyinActorService.GetLocalActor()
 if a then
  local ap=a.position;local v=previousActor and (ap-previousActor)/math.max(dt,.001) or U.Vector3.zero;previousActor=ap
  local d=p-ap;d.y=0
  local radius=a:IsSitting() and 1.85 or 1.4
  if d.magnitude<radius and math.abs(p.y-ap.y)<2.5 and v.magnitude>.1 and v.magnitude<30 then
   local away=d.magnitude>.02 and d.normalized or v.normalized
   if U.Vector3.Dot(v,away)>0 and now>=nextPush then rb:AddForce(away*math.min(2.5,v.magnitude*.7),U.ForceMode.VelocityChange);nextPush=now+.3;pushedUntil=now+1.5;target=nil end
  end
 end
 if now>=nextChoice and now>=pushedUntil then
  nextChoice=now+3+math.random()*5
  if math.random()<.5 then target=nil else
   local angle=math.random()*6.283;target=p+U.Vector3(math.cos(angle)*3,0,math.sin(angle)*3)
  end
 end
 if target and now>=pushedUntil then
  local d=target-p;d.y=0
  if d.magnitude<.35 then target=nil else
   local hits=U.Physics.RaycastAll(p+U.Vector3(0,.65,0),d.normalized,1.1,-1,U.QueryTriggerInteraction.Ignore)
   local blocked=false
   for i=0,hits.Length-1 do local c=hits[i].collider;if c and not c.transform:IsChildOf(self.transform) and hits[i].normal.y<.5 then blocked=true end end
   if blocked then target=nil else
    local v=rb.velocity;local force=(d.normalized*.75-U.Vector3(v.x,0,v.z))*10
    rb:AddForce(force,U.ForceMode.Acceleration)
    local rotation=U.Quaternion.LookRotation(-d.normalized)
    rb:MoveRotation(U.Quaternion.Slerp(rb.rotation,rotation,dt*3))
   end
  end
 end
 local v=rb.velocity;play(v.x*v.x+v.z*v.z>.02 and 'Walk' or 'Idle')
end
function OnCollisionEnter(c)
 if rb and c.relativeVelocity.magnitude>.6 then pushedUntil=U.Time.time+1.5;target=nil end
end
