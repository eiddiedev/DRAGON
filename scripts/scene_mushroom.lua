---@id 655bb578-1c21-4668-9bce-742316b5798b
---@referenceName scene_mushroom.lua
local U=CS.UnityEngine
local clip,source=nil,nil
local colliders={}
local nextBounce=0
local restoreActor,restoreAt=nil,0
local bounceAt,visuals=nil,nil
local function resetJump()
 if restoreActor then restoreActor.jumpHeight=2;restoreActor=nil end
end
local function prepareVisuals()
 if visuals then return end
 visuals={}
 local fs=self.gameObject:GetComponentsInChildren(typeof(U.MeshFilter),true)
 for i=0,fs.Length-1 do local f=fs[i]
  if f.sharedMesh and f.sharedMesh.isReadable then
   local original=f.sharedMesh;local mesh=U.Object.Instantiate(original);f.sharedMesh=mesh
   visuals[#visuals+1]={f=f,original=original,mesh=mesh,base=mesh.vertices,work=mesh.vertices,minY=mesh.bounds.min.y}
  end
 end
end
function Start()
 local rate=16000;local samples={}
 for i=1,7680 do local t=(i-1)/rate;local phase=2*math.pi*(420*t-310*t*t);samples[i]=.5*math.min(1,t/.012)*math.exp(-t*8)*(math.sin(phase)+.22*math.sin(phase*2)) end
 clip=U.AudioClip.Create('mushroom_spring',#samples,1,rate,false);clip:SetData(samples,0)
 local cs=self.gameObject:GetComponentsInChildren(typeof(U.Collider),true)
 for i=0,cs.Length-1 do if not cs[i].isTrigger then colliders[cs[i]]=true end end
 source=self.gameObject:AddComponent(typeof(U.AudioSource));source.playOnAwake=false;source.spatialBlend=1;source.minDistance=2;source.maxDistance=25
end
function Update()
 local now=U.Time.time
 if restoreActor and now>=restoreAt then resetJump() end
 if bounceAt then
  local t=now-bounceAt
  local squish=t<.8 and -.16*math.exp(-t*5)*math.sin(t*18) or 0
  for _,b in ipairs(visuals or {}) do
   for i=0,b.base.Length-1 do local p=b.base[i];b.work[i]=U.Vector3(p.x*(1-squish*.35),b.minY+(p.y-b.minY)*(1+squish),p.z*(1-squish*.35)) end
   b.mesh.vertices=b.work;b.mesh:RecalculateBounds()
  end
  if t>=.8 then bounceAt=nil end
 end
 local actor=DouyinActorService.GetLocalActor()
 if not actor or now<nextBounce or not actor:IsGrounded() or actor:IsSitting() or actor:IsFlying() then return end
 local p=actor.position;local root=self.gameObject.transform;local s=math.abs(root.lossyScale.y)
 local delta=p-root.position;if math.abs(delta.x)>s or math.abs(delta.z)>s or delta.y<.1 or delta.y>s*1.2 then return end
 local hits=U.Physics.RaycastAll(p+U.Vector3(0,.12,0),U.Vector3.down,.4,-1,U.QueryTriggerInteraction.Ignore)
 for i=0,hits.Length-1 do local h=hits[i]
  if colliders[h.collider] and h.normal.y>.45 then
   -- Trigger only after actual ground contact, so each landing re-arms the trampoline.
   actor.jumpHeight=math.max(3.5,math.min(14,2+3*s/1.33144617))
   actor:Jump();restoreActor=actor;restoreAt=now+.2;nextBounce=now+.4
   prepareVisuals();bounceAt=now
   source.pitch=math.max(.65,1.2-s*.08);source:PlayOneShot(clip,.65)
   return
  end
 end
end
function OnDestroy()
 resetJump()
 for _,b in ipairs(visuals or {}) do if b.f then b.f.sharedMesh=b.original end;U.Object.Destroy(b.mesh) end
 if source then U.Object.Destroy(source) end
 if clip then U.Object.Destroy(clip) end
end
