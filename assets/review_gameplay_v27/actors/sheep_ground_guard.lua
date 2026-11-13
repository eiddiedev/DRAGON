-- v27: defer dynamic gravity until this sheep has real support below its saved spawn.
-- Initial scene physics should also be saved as kinematic/no-gravity (see SDK plan).
-- After support is ready the original dynamic/push behavior is restored.
local function createSheepGroundGuard(owner, body)
 local U=CS.UnityEngine
 local s={home=owner.transform.position,nextProbe=0,deadline=U.Time.realtimeSinceStartup+45,
  started=U.Time.realtimeSinceStartup,hits=0,probes=0,ready=false,status='waiting ground',lastError=nil,
  dynamicGravity=true,dynamicKinematic=false}
 body.velocity=U.Vector3.zero;body.angularVelocity=U.Vector3.zero
 body.isKinematic=true;body.useGravity=false
 function s.tick()
  if s.ready then return true end
  local now=U.Time.realtimeSinceStartup
  if now<s.nextProbe then return false end
  if now>s.deadline then
   s.status='ground timeout'
   if not s.warned then s.warned=true;U.Debug.LogWarning('[sheep-ground] '..owner.name..' has no loaded support; held at saved spawn')end
   -- A nearby player may arrive after streaming loads the pasture. No global scan.
   local a=DouyinActorService.GetLocalActor()
   if not a or (a.position-s.home).sqrMagnitude>50*50 then s.nextProbe=now+5;return false end
   s.deadline=now+10
  end
  s.nextProbe=now+.25;s.probes=s.probes+1
  local ok,supported=pcall(function()
   local hs=U.Physics.RaycastAll(s.home+U.Vector3(0,1.0,0),U.Vector3.down,4,-1,U.QueryTriggerInteraction.Ignore)
   for i=0,hs.Length-1 do local h=hs[i];local c=h.collider
    if c and not c.isTrigger and c.enabled and c.gameObject.activeInHierarchy then
     local t=c.transform
     if t~=owner.transform and not t:IsChildOf(owner.transform) and c.attachedRigidbody==nil
      and h.normal.y>.25 and h.point.y<=s.home.y+.5 and h.point.y>=s.home.y-2.5 then return true end
    end
   end
   return false
  end)
  if not ok then s.lastError=tostring(supported);s.status='ground query error';supported=false end
  s.hits=supported and s.hits+1 or 0
  if s.hits>=2 then
   -- Holding the model does not substitute a fake surface. Release only on two real hits.
   body.position=s.home;body.velocity=U.Vector3.zero;body.angularVelocity=U.Vector3.zero
   body.useGravity=s.dynamicGravity;body.isKinematic=s.dynamicKinematic
   s.ready=true;s.status='dynamic';return true
  end
  return false
 end
 return s
end
