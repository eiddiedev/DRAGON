---@id 4575e392-032c-4d6c-9a03-9617cfa1c7dd
---@referenceName scene_mushroom.lua
local U=CS.UnityEngine
local bus=require('modules.scene_interaction_bus')
local source,nearby,restoreActor,oldHeight=nil,nil,nil,nil
local restoreAt,nextBounce=0,0
local colliders={}
function Start()
 local all=self.gameObject:GetComponentsInChildren(typeof(U.Collider),true)
 for i=0,all.Length-1 do if not all[i].isTrigger then colliders[all[i]]=true end end
 source=self.gameObject:AddComponent(typeof(U.AudioSource))
 source.playOnAwake=false;source.spatialBlend=1;source.minDistance=2;source.maxDistance=20
end
function OnActorTriggerEnter(actor)
 if actor and actor.isLocal then nearby=actor end
end
function OnActorTriggerExit(actor)
 if actor==nearby then nearby=nil end
end
local function restore()
 if restoreActor then restoreActor.jumpHeight=oldHeight;restoreActor=nil end
end
function Update()
 local now=U.Time.time
 if restoreActor and now>=restoreAt then restore() end
 if not nearby or now<nextBounce then return end
 local p=nearby.position
 local hits=U.Physics.RaycastAll(p+U.Vector3(0,.15,0),U.Vector3.down,.4,-1,U.QueryTriggerInteraction.Ignore)
 for i=0,hits.Length-1 do
  local hit=hits[i]
  if colliders[hit.collider] and hit.normal.y>.55 then
   restoreActor=nearby;oldHeight=nearby.jumpHeight;nearby.jumpHeight=6
   nearby:Jump();restoreAt=now+.25;nextBounce=now+2
   if bus.clips.bounce then source:PlayOneShot(bus.clips.bounce,.65) end
   return
  end
 end
end
function OnDestroy()
 restore()
 if source then U.Object.Destroy(source) end
end
