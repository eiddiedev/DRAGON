-- Tripo clothing with real weighted skins; retarget to the current avatar's bind-pose rotations.
---@displayName 龙眠三职业蒙皮服饰
local U=CS.UnityEngine
local Q=U.Quaternion
local V=U.Vector3
local scope=require('official.core.runtime_scope').from(self)
local Spawn=require('official.core.spawn')
local paths={melee='TripoWarrior',mage='TripoMage',ranged='TripoRanger'}
local entries={}
local names={'Hips','Spine','Chest','UpperChest','Neck','Head','LeftUpperArm','RightUpperArm','LeftLowerArm','RightLowerArm','LeftHand','RightHand','LeftUpperLeg','RightUpperLeg','LeftLowerLeg','RightLowerLeg','LeftFoot','RightFoot'}
local function actorKey(a)return tostring(a.gameObject:GetInstanceID())end
local function ready(go)
 if not go then return false end
 local skins=go:GetComponentsInChildren(typeof(U.SkinnedMeshRenderer),true)
 if skins.Length==0 then return false end
 for i=0,skins.Length-1 do local s=skins[i]
  if not s.sharedMesh or s.sharedMesh.vertexCount==0 or s.bones.Length==0 or not s.rootBone then return false end
  for j=0,s.bones.Length-1 do if not s.bones[j]then return false end end
 end
 return true
end
local function restoreBody(e)
 if e and e.bodyMasks then for _,m in ipairs(e.bodyMasks)do if m.renderer then m.renderer.sharedMesh=m.original end;U.Object.Destroy(m.mesh)end;e.bodyMasks=nil end
end
local function maskBody(e)
 local skins=e.actor.gameObject:GetComponentsInChildren(typeof(U.SkinnedMeshRenderer),true);e.bodyMasks={}
 for i=0,skins.Length-1 do local r=skins[i]
  if r.name=='body' and r.sharedMesh then
   local original=r.sharedMesh;local mesh=U.Object.Instantiate(original);local weights=original.boneWeights;local bs=r.bones;local hide={}
   for j=0,bs.Length-1 do local name=bs[j].name
    hide[j]=name=='Hips' or name=='Spine' or name=='Spine1' or name=='Spine2' or name=='LeftShoulder' or name=='RightShoulder' or name=='LeftArm' or name=='RightArm'
    if e.class~='melee' and (string.find(name,'Leg') or string.find(string.lower(name),'foot'))then hide[j]=true end
   end
   local removed={}
   for j=0,weights.Length-1 do local w=weights[j];local sum=0
    if hide[w.boneIndex0]then sum=sum+w.weight0 end;if hide[w.boneIndex1]then sum=sum+w.weight1 end;if hide[w.boneIndex2]then sum=sum+w.weight2 end;if hide[w.boneIndex3]then sum=sum+w.weight3 end
    removed[j]=sum>.5
   end
   for sub=0,original.subMeshCount-1 do local tris=original:GetTriangles(sub);local kept={}
    for j=0,tris.Length-1,3 do local a,b,c=tris[j],tris[j+1],tris[j+2]
     if not(removed[a] and removed[b] and removed[c])then kept[#kept+1]=a;kept[#kept+1]=b;kept[#kept+1]=c end
    end
    local arr=CS.System.Array.CreateInstance(typeof(CS.System.Int32),#kept);for j=1,#kept do arr[j-1]=kept[j]end;mesh:SetTriangles(arr,sub)
   end
   r.sharedMesh=mesh;e.bodyMasks[#e.bodyMasks+1]={renderer=r,original=original,mesh=mesh}
  end
 end
end
local function remove(e)
 restoreBody(e)
 if e and e.clone then Spawn.destroy(e.clone);e.clone=nil end
end
local function bind(a,kind)
 local source=scope:GetGameObjectByPath(paths[kind]);if not ready(source)then return nil end
 local go=Spawn.spawn(self,paths[kind],{networked=false});if not ready(go)then if go then Spawn.destroy(go)end;return nil end
 go:SetActive(false);go.transform.position=V.zero;go.transform.rotation=Q.identity;go.transform.localScale=V.one
 local colliders=go:GetComponentsInChildren(typeof(U.Collider),true);for i=0,colliders.Length-1 do colliders[i].enabled=false end
 local animator=a.gameObject:GetComponentInChildren(typeof(U.Animator));if not animator then Spawn.destroy(go);return nil end
 local transforms=go:GetComponentsInChildren(typeof(U.Transform),true);local sourceBones={}
 for i=0,transforms.Length-1 do sourceBones[transforms[i].name]=transforms[i]end
 local rest={};local skins=a.gameObject:GetComponentsInChildren(typeof(U.SkinnedMeshRenderer),true)
 for i=0,skins.Length-1 do local r=skins[i];if r.sharedMesh then
  local poses=r.sharedMesh.bindposes;local bs=r.bones
  for j=0,math.min(bs.Length,poses.Length)-1 do
   local t=bs[j];if t then rest[t:GetInstanceID()]=Q.Inverse(a.gameObject.transform.rotation)*r.transform.rotation*poses[j].inverse.rotation end
  end
 end end
 local e={actor=a,clone=go,class=kind,bones={},visible=true}
 for _,name in ipairs(names)do
  local b=sourceBones[name];local t=animator:GetBoneTransform(U.HumanBodyBones[name])
  if b and t and rest[t:GetInstanceID()]then
   e.bones[#e.bones+1]={bone=b,target=t,offset=Q.Inverse(rest[t:GetInstanceID()])*b.rotation}
  end
 end
 if #e.bones<12 then Spawn.destroy(go);return nil end
 source:SetActive(false)
 return e
end
function Equip(actor,kind)
 if not actor or not paths[kind]then return false end
 local key=actorKey(actor);local e=entries[key]
 if e and e.class==kind then e.visible=true;return true end
 local replacement=bind(actor,kind);if not replacement then return false end
 remove(e);maskBody(replacement);entries[key]=replacement;return true
end
function SetVisible(actor,visible)local e=actor and entries[actorKey(actor)];if e then e.visible=visible end end
function Unequip(actor)if actor then local k=actorKey(actor);remove(entries[k]);entries[k]=nil end end
function GetOutfitStatus(actor)local e=actor and entries[actorKey(actor)];return e and(e.visible and 'visible' or 'hidden')or 'waiting' end
function ResourcesReady()for _,path in pairs(paths)do if not ready(scope:GetGameObjectByPath(path))then return false end end;return true end
function IsReady(actor,kind)local e=actor and entries[actorKey(actor)];return e~=nil and e.class==kind and #e.bones>=12 end
function Start()
 for _,path in pairs(paths)do local s=scope:GetGameObjectByPath(path);if s then s.transform.localPosition=V(0,-500,0)end end
 -- The former prototype is superseded by the skinned garments.
 local old=scope:GetGameObjectByPath('ClasswearRoot');if old then old:SetActive(false)end
end
function LateUpdate()
 for _,e in pairs(entries)do
  if e.clone then
   if e.visible then
    local root=e.actor.gameObject.transform;e.clone.transform.position=root.position;e.clone.transform.rotation=root.rotation;e.clone.transform.localScale=root.lossyScale
    for _,p in ipairs(e.bones)do p.bone.position=p.target.position;p.bone.rotation=p.target.rotation*p.offset end
   end
   e.clone:SetActive(e.visible)
  end
 end
end
function OnActorDespawned(actor)Unequip(actor)end
function OnDisable()for _,e in pairs(entries)do if e.clone then e.clone:SetActive(false)end end end
function OnDestroy()for _,e in pairs(entries)do remove(e)end;entries={}end
