---@id 1c4128ac-0d75-431c-b406-2c24e259a71d
---@referenceName dragon_outfits.lua
-- 三职业职装控制器：按 Actor 标签本地克隆职装，并逐帧用骨骼世界坐标对齐
---@displayName 三职业职装控制器
---@start
---@var GlobalScale:number=1
---@name 整体缩放
---@desc 在 Hips→Head 尺寸校准之后再整体放大或缩小职装
---@var ReferenceHipsToHead:number=0.34
---@name 尺寸校准参考
---@desc 作者空间中 Hips 到 Head 的参考距离（米），克隆创建时用它校准基准缩放
---@end

local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")
local Spawn = require("official.core.spawn")

local logger = Logger.create("ms-outfit-rig")

local UnityEngine = CS.UnityEngine
local Vector3 = UnityEngine.Vector3
local Quaternion = UnityEngine.Quaternion
local Time = UnityEngine.Time
local HumanBodyBones = UnityEngine.HumanBodyBones
local SkinnedMeshRenderer = UnityEngine.SkinnedMeshRenderer
local Collider = UnityEngine.Collider

local RESOURCE_ID = "dragon-rpg-outfits"
local CLASS_TAG = "jiejie_classwear_class"
local VISIBLE_TAG = "jiejie_classwear_visible"
local REFRESH_EVENT = "Classwear.refresh"
local REFRESH_INTERVAL = 0.25
local SOURCE_SETS_PATH = "ClasswearRoot/SourceSets"
local PROTOTYPE_PARK = Vector3(0, -500, 0)
local MIN_SCALE = 0.55
local MAX_SCALE = 1.8

local runtimeScope, scopeReason = RuntimeScope.from(self)
local resourceRoot = nil
local resourceRootTransform = nil
if runtimeScope ~= nil then
  resourceRoot = runtimeScope:GetResourceRoot()
  if resourceRoot ~= nil then
    resourceRootTransform = resourceRoot.transform
  end
end
if runtimeScope == nil or resourceRoot == nil then
  logger:warnOnce("resource-scope-unavailable", "outfit controller disabled", scopeReason)
end

local CLASS_SOURCE = {
  melee = "ClasswearRoot/SourceSets/WarriorSet",
  ranged = "ClasswearRoot/SourceSets/ArcherSet",
  mage = "ClasswearRoot/SourceSets/MageSet",
}

-- offset 使用躯干局部坐标，+X 即躯干 right；符号与源模型一致，不再翻转。
-- 源模型 +X 部件（名称带 L）跟随角色右侧骨骼，源 -X 部件（名称带 R）跟随左侧。
-- offset 会乘以当前 worldScale，父级缩放由克隆根节点的 localScale 抵消。
local PART_SPECS = {
  melee = {
    { name = "Chest", kind = "torso" },
    { name = "Hips", kind = "torso" },
    { name = "ShoulderL", kind = "upperArm", side = "L" },
    { name = "ShoulderR", kind = "upperArm", side = "R" },
    { name = "BracerL", kind = "forearm", side = "L" },
    { name = "BracerR", kind = "forearm", side = "R" },
    {
      name = "TabardFront", kind = "hem", parent = "hips",
      offset = { 0.0, 0.034, 0.133 },
      basePitch = -2, forwardLimit = 7, backLimit = 17, rollLimit = 9, phase = 0.0,
    },
    {
      name = "TabardBack", kind = "hem", parent = "hips",
      offset = { 0.0, 0.034, -0.142 },
      basePitch = 2, forwardLimit = 5, backLimit = 19, rollLimit = 9, phase = 1.7,
    },
  },
  ranged = {
    { name = "Chest", kind = "torso" },
    { name = "Hips", kind = "torso" },
    { name = "ShoulderL", kind = "upperArm", side = "L" },
    { name = "ShoulderR", kind = "upperArm", side = "R" },
    { name = "SleeveL", kind = "upperArm", side = "L", shift = 0.36 },
    { name = "SleeveR", kind = "upperArm", side = "R", shift = 0.36 },
    { name = "BracerL", kind = "forearm", side = "L" },
    { name = "BracerR", kind = "forearm", side = "R" },
    {
      name = "HemFrontL", kind = "hem", parent = "hips",
      offset = { 0.058, 0.0, 0.128 },
      basePitch = -2, forwardLimit = 7, backLimit = 16, rollLimit = 8, phase = 0.2,
    },
    {
      name = "HemFrontR", kind = "hem", parent = "hips",
      offset = { -0.058, 0.0, 0.128 },
      basePitch = -2, forwardLimit = 7, backLimit = 16, rollLimit = 8, phase = 2.1,
    },
    {
      name = "HemBackL", kind = "hem", parent = "hips",
      offset = { 0.058, 0.0, -0.138 },
      basePitch = 3, forwardLimit = 5, backLimit = 20, rollLimit = 9, phase = 0.9,
    },
    {
      name = "HemBackR", kind = "hem", parent = "hips",
      offset = { -0.058, 0.0, -0.138 },
      basePitch = 3, forwardLimit = 5, backLimit = 20, rollLimit = 9, phase = 2.8,
    },
  },
  mage = {
    { name = "Chest", kind = "torso" },
    { name = "Hips", kind = "torso" },
    { name = "ShoulderL", kind = "upperArm", side = "L" },
    { name = "ShoulderR", kind = "upperArm", side = "R" },
    { name = "BracerL", kind = "forearm", side = "L" },
    { name = "BracerR", kind = "forearm", side = "R" },
    {
      name = "CloakBackL", kind = "hem", parent = "chest",
      offset = { 0.095, 0.056, -0.132 },
      basePitch = 2, forwardLimit = 4, backLimit = 26, rollLimit = 7, phase = 0.4,
    },
    {
      name = "CloakBackR", kind = "hem", parent = "chest",
      offset = { -0.095, 0.056, -0.132 },
      basePitch = 2, forwardLimit = 4, backLimit = 26, rollLimit = 7, phase = 2.4,
    },
    {
      name = "CloakSideL", kind = "hem", parent = "chest",
      offset = { 0.166, 0.010, -0.012 },
      basePitch = 0, forwardLimit = 8, backLimit = 17, rollLimit = 12, phase = 1.2,
    },
    {
      name = "CloakSideR", kind = "hem", parent = "chest",
      offset = { -0.166, 0.010, -0.012 },
      basePitch = 0, forwardLimit = 8, backLimit = 17, rollLimit = 12, phase = 3.3,
    },
    {
      name = "HoodBack", kind = "torsoOffset", parent = "chest",
      offset = { 0.0, 0.118, -0.086 },
    },
  },
}


-- Verify actual geometry, not merely the presence of a GameObject.
local function visualSignature(go)
 if go==nil then return nil end
 local ok,result=pcall(function()
  local E=CS.UnityEngine
  local rs=go:GetComponentsInChildren(typeof(E.Renderer),true)
  local keys={};local count=0
  for i=0,rs.Length-1 do
   local r=rs[i];local skin=r:GetComponent(typeof(E.SkinnedMeshRenderer))
   local filter=r:GetComponent(typeof(E.MeshFilter))
   if skin~=nil or filter~=nil then
    local mesh=skin~=nil and skin.sharedMesh or filter.sharedMesh
    if mesh==nil or mesh.vertexCount<=0 then return nil end
    local mats=r.sharedMaterials
    if mats==nil or mats.Length==0 then return nil end
    for j=0,mats.Length-1 do if mats[j]==nil then return nil end end
    local key=tostring(mesh:GetInstanceID())
    if skin~=nil then
     local bones=skin.bones
     if bones==nil or bones.Length==0 or skin.rootBone==nil then return nil end
     for j=0,bones.Length-1 do if bones[j]==nil then return nil end end
     key=key..":"..tostring(bones.Length)..":"..tostring(skin.rootBone:GetInstanceID())
    end
    count=count+1;keys[count]=key
   end
  end
  if count==0 then return nil end
  return table.concat(keys,"|")
 end)
 return ok and result or nil
end

local REQUIRED_MESH_PATHS = {
 melee = {"Chest/__optimized_merged_material_0","Chest/__optimized_merged_material_1","Chest/__optimized_merged_material_2","Chest/__optimized_merged_material_3","Chest/__optimized_merged_material_4","Chest/__optimized_merged_material_5","Chest/__optimized_merged_material_6","Chest/__optimized_merged_material_7","Hips/__optimized_merged_material_2","Hips/__optimized_merged_material_0","Hips/__optimized_merged_material_4","Hips/__optimized_merged_material_7","Hips/__optimized_merged_material_8","ShoulderL/__optimized_merged_material_2","ShoulderL/__optimized_merged_material_0","ShoulderL/__optimized_merged_material_3","BracerL/__optimized_merged_material_1","BracerL/__optimized_merged_material_3","BracerL/__optimized_merged_material_2","ShoulderR/__optimized_merged_material_2","ShoulderR/__optimized_merged_material_0","ShoulderR/__optimized_merged_material_3","BracerR/__optimized_merged_material_1","BracerR/__optimized_merged_material_3","BracerR/__optimized_merged_material_2","TabardFront/__optimized_merged_material_9","TabardFront/__optimized_merged_material_5","TabardFront/__optimized_merged_material_10","TabardFront/__optimized_merged_material_8","TabardFront/__optimized_merged_material_6","TabardBack/__optimized_merged_material_9","TabardBack/__optimized_merged_material_5","TabardBack/__optimized_merged_material_10","TabardBack/__optimized_merged_material_8"},
 ranged = {"Chest/__optimized_merged_material_11","Chest/__optimized_merged_material_8","Chest/__optimized_merged_material_10","Chest/__optimized_merged_material_12","Chest/__optimized_merged_material_13","Chest/__optimized_merged_material_3","Chest/__optimized_merged_material_4","Hips/__optimized_merged_material_8","Hips/__optimized_merged_material_2","Hips/__optimized_merged_material_4","Hips/__optimized_merged_material_12","Hips/__optimized_merged_material_5","ShoulderL/__optimized_merged_material_8","ShoulderL/__optimized_merged_material_3","SleeveL/__optimized_merged_material_11","SleeveL/__optimized_merged_material_10","BracerL/__optimized_merged_material_8","BracerL/__optimized_merged_material_12","BracerL/__optimized_merged_material_2","BracerL/__optimized_merged_material_3","ShoulderR/__optimized_merged_material_8","ShoulderR/__optimized_merged_material_3","SleeveR/__optimized_merged_material_11","SleeveR/__optimized_merged_material_10","BracerR/__optimized_merged_material_8","BracerR/__optimized_merged_material_12","BracerR/__optimized_merged_material_2","BracerR/__optimized_merged_material_3","HemFrontL/__optimized_merged_material_11","HemFrontL/__optimized_merged_material_10","HemFrontR/__optimized_merged_material_11","HemFrontR/__optimized_merged_material_10","HemBackL/__optimized_merged_material_11","HemBackL/__optimized_merged_material_10","HemBackR/__optimized_merged_material_11","HemBackR/__optimized_merged_material_10"},
 mage = {"Chest/__optimized_merged_material_10","Chest/__optimized_merged_material_14","Chest/__optimized_merged_material_5","Chest/__optimized_merged_material_4","Chest/__optimized_merged_material_15","Hips/__optimized_merged_material_16","Hips/__optimized_merged_material_5","Hips/__optimized_merged_material_14","ShoulderL/__optimized_merged_material_14","ShoulderL/__optimized_merged_material_10","ShoulderL/__optimized_merged_material_5","ShoulderL/__optimized_merged_material_4","BracerL/__optimized_merged_material_14","BracerL/__optimized_merged_material_10","BracerL/__optimized_merged_material_5","ShoulderR/__optimized_merged_material_14","ShoulderR/__optimized_merged_material_10","ShoulderR/__optimized_merged_material_5","ShoulderR/__optimized_merged_material_4","BracerR/__optimized_merged_material_14","BracerR/__optimized_merged_material_10","BracerR/__optimized_merged_material_5","CloakBackL/__optimized_merged_material_14","CloakBackL/__optimized_merged_material_10","CloakBackL/__optimized_merged_material_5","CloakBackR/__optimized_merged_material_14","CloakBackR/__optimized_merged_material_10","CloakBackR/__optimized_merged_material_5","CloakSideL/__optimized_merged_material_14","CloakSideL/__optimized_merged_material_10","CloakSideR/__optimized_merged_material_14","CloakSideR/__optimized_merged_material_10","HoodBack/__optimized_merged_material_14","HoodBack/__optimized_merged_material_10","HoodBack/__optimized_merged_material_5"},
}
-- Saved asset mesh slices must all be ready, not just the first downloaded child.
local function completeVisual(go,className)
 if go==nil then return nil end
 local ok,result=pcall(function()
  for _,path in ipairs(REQUIRED_MESH_PATHS[className]or{})do
   local part=go.transform:Find(path)
   if not part or not visualSignature(part.gameObject)then return nil end
  end
  return visualSignature(go)
 end)
 return ok and result or nil
end

local actors = {}
local started = false
local resourceEntry = nil
local refreshTimer = 0
local elapsed = 0

-- ---------------------------------------------------------------------------
-- 小工具
-- ---------------------------------------------------------------------------
local function isAlive(object)
  if object == nil then return false end
  local ok, referenced = pcall(function()
    return CS.System.Object.ReferenceEquals(object, nil)
  end)
  if ok then return referenced ~= true end
  return true
end

local function actorGameObject(actor)
  if actor == nil then return nil end
  local ok, gameObject = pcall(function() return actor.gameObject end)
  if not ok then return nil end
  return gameObject
end

local function actorIdOf(actor)
  if actor == nil then return nil end
  local ok, actorId = pcall(function() return actor.actorID end)
  if not ok then return nil end
  return actorId
end

local function getTag(actor, tagName)
  if actor == nil then return "" end
  local value = actor:GetActorTag(tagName)
  if value == nil then return "" end
  return tostring(value)
end

local gameStates = {}
local function readState(actor)
  local state=gameStates[actorIdOf(actor)]
  return state and state.className or "", state and state.visible==true or false
end

local function clamp(value, minimum, maximum)
  if value < minimum then return minimum end
  if value > maximum then return maximum end
  return value
end

local function subtract(a, b)
  return Vector3(a.x - b.x, a.y - b.y, a.z - b.z)
end

local function negate(a)
  return Vector3(-a.x, -a.y, -a.z)
end

local function dot(a, b)
  return a.x * b.x + a.y * b.y + a.z * b.z
end

local function scaleVector(a, factor)
  return Vector3(a.x * factor, a.y * factor, a.z * factor)
end

local function cross(a, b)
  return Vector3(
    a.y * b.z - a.z * b.y,
    a.z * b.x - a.x * b.z,
    a.x * b.y - a.y * b.x
  )
end

local function safeUnit(value, fallback)
  local length = math.sqrt(value.x * value.x + value.y * value.y + value.z * value.z)
  if length < 0.00001 then return fallback end
  return Vector3(value.x / length, value.y / length, value.z / length)
end

local function subtractUnit(value, axis)
  local projected = scaleVector(axis, dot(value, axis))
  return subtract(value, projected)
end

local function lerpVector(a, b, t)
  return Vector3(
    a.x + (b.x - a.x) * t,
    a.y + (b.y - a.y) * t,
    a.z + (b.z - a.z) * t
  )
end

local function bonePosition(actor, bone)
  if actor == nil then return nil end
  local ok, transform = pcall(function()
    return actor:GetBoneTransform(bone)
  end)
  if not ok or transform == nil then return nil end
  return transform.position
end

local function findMainRenderer(gameObject)
  if not isAlive(gameObject) then return nil end
  local ok, renderers = pcall(function()
    return gameObject:GetComponentsInChildren(typeof(SkinnedMeshRenderer), true)
  end)
  if not ok or renderers == nil then return nil end

  local best = nil
  local bestBones = -1
  for index = 0, renderers.Length - 1 do
    local renderer = renderers[index]
    if renderer ~= nil and renderer.enabled and renderer.gameObject.activeInHierarchy and renderer.sharedMesh~=nil then
      local boneCount = 0
      local bones = renderer.bones
      if bones ~= nil then boneCount = bones.Length end
      if boneCount > bestBones then
        bestBones = boneCount
        best = renderer
      end
    end
  end
  return best
end

local function isActorRenderable(entry)
  if entry == nil or entry.actor == nil then return false end
  local gameObject = actorGameObject(entry.actor)
  if not isAlive(gameObject) then return false end
  if not gameObject.activeInHierarchy then return false end
  -- Do not retain the disabled placeholder renderer after native avatar loading.
  entry.mainRenderer=findMainRenderer(gameObject)
  local renderer = entry.mainRenderer
  if renderer == nil then return false end
  if renderer ~= nil then
    local ok, enabled = pcall(function() return renderer.enabled end)
    if not ok then
      entry.mainRenderer = nil
    elseif enabled == false then
      return false
    end
  end
  return true
end

local function lengthOf(value)
  return math.sqrt(value.x * value.x + value.y * value.y + value.z * value.z)
end

-- 绕过 Quaternion * Vector3，直接按四元数分量旋转方向。
local function rotateVector(rotation, value)
  local qx, qy, qz, qw = rotation.x, rotation.y, rotation.z, rotation.w
  local tx = 2 * (qy * value.z - qz * value.y)
  local ty = 2 * (qz * value.x - qx * value.z)
  local tz = 2 * (qx * value.y - qy * value.x)
  return Vector3(
    value.x + qw * tx + (qy * tz - qz * ty),
    value.y + qw * ty + (qz * tx - qx * tz),
    value.z + qw * tz + (qx * ty - qy * tx)
  )
end

local function actorRotationOf(actor)
  if actor == nil then return nil end
  local ok, value = pcall(function() return actor.rotation end)
  if not ok or value == nil then return nil end
  return value
end

local function actorScaleOf(actor)
  if actor == nil then return nil end
  local ok, value = pcall(function() return actor.scale end)
  if not ok or type(value) ~= "number" then return nil end
  return value
end

local function computeBaseScale(hips, head)
  local reference = ReferenceHipsToHead
  if type(reference) ~= "number" or reference < 0.05 then reference = 0.34 end
  if hips == nil or head == nil then return nil end
  local hipsToHead = Vector3.Distance(hips, head)
  if hipsToHead <= 0.02 then return nil end
  return hipsToHead / reference
end

local function globalScaleValue()
  local value = GlobalScale
  if type(value) ~= "number" or value <= 0 then return 1 end
  return value
end

-- ---------------------------------------------------------------------------
-- 克隆生命周期
-- ---------------------------------------------------------------------------
local function clearClone(entry)
  if entry == nil then return end
  if entry.pendingClone then pcall(function()Spawn.destroy(entry.pendingClone)end);entry.pendingClone=nil end
  entry.pendingClass=nil;entry.pendingSignature=nil;entry.sourceSignature=nil

  if entry.clone ~= nil then
    pcall(function() Spawn.destroy(entry.clone) end)
  end
  entry.clone = nil
  entry.posed=false
  entry.parts = {}
  entry.className = ""
end

local function collectParts(entry)
  entry.parts = {}
  local specList = PART_SPECS[entry.className]
  if specList == nil or entry.clone == nil then return end
  for _, spec in ipairs(specList) do
    local transform = entry.clone.transform:Find(spec.name)
    if transform == nil then
      logger:warnOnce("missing-part-" .. spec.name, "outfit part not found", spec.name)
    else
      table.insert(entry.parts, {
        transform = transform,
        spec = spec,
        pitch = 0,
        roll = 0,
      })
    end
  end
end

local function disableCollidersOn(gameObject)
  if not isAlive(gameObject) then return end
  local ok, colliders = pcall(function()
    return gameObject:GetComponentsInChildren(typeof(Collider), true)
  end)
  if not ok or colliders == nil then return end
  for index = 0, colliders.Length - 1 do
    local collider = colliders[index]
    if collider ~= nil then collider.enabled = false end
  end
end

local function disableCollisions(clone)
  disableCollidersOn(clone)
end

local function spawnClone(entry, className)
  local sourcePath = CLASS_SOURCE[className]
  if sourcePath == nil or resourceRootTransform == nil then return false end

  local source=runtimeScope:GetGameObjectByPath(sourcePath)
  local signature=completeVisual(source,className)
  if not signature then return false end

  local clone=entry.pendingClone
  if clone and (not isAlive(clone) or entry.pendingClass~=className or entry.pendingSignature~=signature)then
    pcall(function()Spawn.destroy(clone)end);clone=nil;entry.pendingClone=nil
  end
  if not clone then
    local ok,created=pcall(function()return Spawn.spawn(self,sourcePath,{networked=false})end)
    if not ok or not created then
      logger:warnOnce("spawn-failed-"..className,"outfit spawn failed",tostring(created));return false
    end
    clone=created;clone:SetActive(false)
    entry.pendingClone=clone;entry.pendingClass=className;entry.pendingSignature=signature
  end
  if not completeVisual(clone,className)then return false end
  entry.pendingClone=nil;entry.pendingClass=nil;entry.pendingSignature=nil
  entry.sourceSignature=signature
  clone:SetActive(false)
  clone.transform:SetParent(resourceRootTransform, true)
  clone.transform.localPosition = Vector3(0, 0, 0)
  clone.transform.localRotation = Quaternion.identity
  clone.transform.localScale = Vector3(1, 1, 1)
  disableCollisions(clone)

  entry.clone = clone
  entry.className = className
  entry.baseScale = computeBaseScale(
    bonePosition(entry.actor, HumanBodyBones.Hips),
    bonePosition(entry.actor, HumanBodyBones.Head)
  )
  entry.actorScale = actorScaleOf(entry.actor)
  collectParts(entry)
  return true
end

local function ensureClone(entry, className)
  if entry.clone ~= nil and entry.className == className then
    if Time.time<(entry.nextHealthCheck or 0) then return end
    entry.nextHealthCheck=Time.time+.5
    local source=runtimeScope:GetGameObjectByPath(CLASS_SOURCE[className])
    local signature=completeVisual(source,className)
    if completeVisual(entry.clone,className) and (not signature or signature==entry.sourceSignature) then return end
  end
  if entry.clone ~= nil then clearClone(entry) end
  spawnClone(entry, className)
end

-- ---------------------------------------------------------------------------
-- 骨架对齐
-- ---------------------------------------------------------------------------
-- 克隆创建时缓存基准缩放；之后只叠乘 GlobalScale，仅在 actor.scale 明显变化时重算。
local function worldScaleFor(entry, hips, head)
  local currentActorScale = actorScaleOf(entry.actor)
  if currentActorScale ~= nil then
    if entry.actorScale == nil then
      entry.actorScale = currentActorScale
    elseif math.abs(currentActorScale - entry.actorScale) > 0.05 then
      entry.actorScale = currentActorScale
      entry.baseScale = computeBaseScale(hips, head) or entry.baseScale
    end
  end
  -- Recompute when avatar proportions settle; actor.scale alone does not change
  -- when a placeholder is replaced by the user's final appearance.
  entry.baseScale=computeBaseScale(hips,head) or entry.baseScale
  return clamp((entry.baseScale or 1) * globalScaleValue(), MIN_SCALE, MAX_SCALE)
end

local function applyRootScale(entry, worldScale)
  if entry.clone == nil or resourceRootTransform == nil then return end
  local parentScale = resourceRootTransform.lossyScale
  local function factor(value)
    if math.abs(value) < 0.0001 then return 1 end
    return value
  end
  entry.clone.transform.localScale = Vector3(
    worldScale / factor(parentScale.x),
    worldScale / factor(parentScale.y),
    worldScale / factor(parentScale.z)
  )
end

local function limbRotation(rootPosition, endPosition, outward, fallbackUp)
  local zAxis = safeUnit(subtract(endPosition, rootPosition), fallbackUp)
  local yAxis = safeUnit(subtractUnit(outward, zAxis), fallbackUp)
  return Quaternion.LookRotation(zAxis, yAxis)
end

local function updateEntry(entry, deltaTime)
  if entry.clone == nil or entry.className == "" then return end

  if entry.visible==false or not isActorRenderable(entry) then
    if entry.clone.activeSelf then entry.clone:SetActive(false) end
    return
  end
  local actor = entry.actor
  local hips = bonePosition(actor, HumanBodyBones.Hips)
  local chest = bonePosition(actor, HumanBodyBones.Chest)
  local head = bonePosition(actor, HumanBodyBones.Head)
  local leftUpper = bonePosition(actor, HumanBodyBones.LeftUpperArm)
  local rightUpper = bonePosition(actor, HumanBodyBones.RightUpperArm)
  local leftLower = bonePosition(actor, HumanBodyBones.LeftLowerArm)
  local rightLower = bonePosition(actor, HumanBodyBones.RightLowerArm)
  local leftHand = bonePosition(actor, HumanBodyBones.LeftHand)
  local rightHand = bonePosition(actor, HumanBodyBones.RightHand)

  if hips==nil or chest==nil or head==nil or leftUpper==nil or rightUpper==nil or leftLower==nil or rightLower==nil or leftHand==nil or rightHand==nil then
    entry.clone:SetActive(false);entry.posed=false;return
  end
  local distance=Vector3.Distance(hips,head)
  if distance~=distance or distance<.02 or distance>4 then
    entry.clone:SetActive(false);entry.posed=false;return
  end

  local torsoUp = safeUnit(subtract(chest, hips), Vector3(0, 1, 0))

  -- 朝向优先取 actor.rotation 的前向，并投影到躯干 up 轴；臂展只作兜底。
  local forward = nil
  local actorRotation = actorRotationOf(actor)
  if actorRotation ~= nil then
    local ok, rawForward = pcall(function()
      return rotateVector(actorRotation, Vector3(0, 0, 1))
    end)
    if ok and rawForward ~= nil then
      local projected = subtract(rawForward, scaleVector(torsoUp, dot(rawForward, torsoUp)))
      if lengthOf(projected) > 0.0001 then
        forward = safeUnit(projected, Vector3(0, 0, 1))
      end
    end
  end
  if forward == nil and leftUpper ~= nil and rightUpper ~= nil then
    local span = subtract(rightUpper, leftUpper)
    if lengthOf(span) > 0.0001 then
      forward = safeUnit(cross(safeUnit(span, Vector3(1, 0, 0)), torsoUp), Vector3(0, 0, 1))
    end
  end
  if forward == nil then
    forward = safeUnit(cross(Vector3(1, 0, 0), torsoUp), Vector3(0, 0, 1))
  end
  local lateral = safeUnit(cross(torsoUp, forward), Vector3(1, 0, 0))
  local torsoRotation = Quaternion.LookRotation(forward, torsoUp)

  local worldScale = worldScaleFor(entry, hips, head)
  applyRootScale(entry, worldScale)

  local velocity = actor.velocity
  local velocityRight = 0
  local velocityForward = 0
  if velocity ~= nil then
    velocityRight = dot(velocity, lateral)
    velocityForward = dot(velocity, forward)
  end

  for _, part in ipairs(entry.parts) do
    local spec = part.spec
    local transform = part.transform
    if spec.kind == "torso" then
      if spec.name == "Chest" then
        transform.position = chest
      else
        transform.position = hips
      end
      transform.rotation = torsoRotation
    elseif spec.kind == "upperArm" then
      -- 源模型 +X 部件（L）跟随角色右侧骨骼，-X 部件（R）跟随左侧。
      local rootBone = spec.side == "L" and rightUpper or leftUpper
      local endBone = spec.side == "L" and rightLower or leftLower
      if endBone ~= nil and rootBone ~= nil then
        local outward = spec.side == "L" and lateral or negate(lateral)
        local anchor = rootBone
        if spec.shift ~= nil then
          anchor = lerpVector(rootBone, endBone, spec.shift)
        end
        transform.position = anchor
        transform.rotation = limbRotation(rootBone, endBone, outward, torsoUp)
      end
    elseif spec.kind == "forearm" then
      local elbow = spec.side == "L" and rightLower or leftLower
      local hand = spec.side == "L" and rightHand or leftHand
      if elbow ~= nil then
        local outward = spec.side == "L" and lateral or negate(lateral)
        local endPosition = hand
        if endPosition == nil then
          local rootBone = spec.side == "L" and rightUpper or leftUpper
          endPosition = Vector3(
            elbow.x + (elbow.x - rootBone.x),
            elbow.y + (elbow.y - rootBone.y),
            elbow.z + (elbow.z - rootBone.z)
          )
        end
        transform.position = lerpVector(elbow, endPosition, 0.45)
        transform.rotation = limbRotation(elbow, endPosition, outward, torsoUp)
      end
    elseif spec.kind == "hem" or spec.kind == "torsoOffset" then
      local reference = hips
      if spec.parent == "chest" then reference = chest end
      local offset = spec.offset
      local offsetX = offset[1] * worldScale
      local offsetY = offset[2] * worldScale
      local offsetZ = offset[3] * worldScale
      transform.position = Vector3(
        reference.x + lateral.x * offsetX + torsoUp.x * offsetY + forward.x * offsetZ,
        reference.y + lateral.y * offsetX + torsoUp.y * offsetY + forward.y * offsetZ,
        reference.z + lateral.z * offsetX + torsoUp.z * offsetY + forward.z * offsetZ
      )

      if spec.kind == "hem" then
        local targetPitch = spec.basePitch + clamp(velocityForward * 9, -spec.forwardLimit, spec.backLimit)
        local targetRoll = clamp(-velocityRight * 7, -spec.rollLimit, spec.rollLimit)
        local idle = math.sin(elapsed * 1.6 + spec.phase) * 0.9
        local smoothing = 1 - math.exp(-deltaTime * 7)
        part.pitch = part.pitch + (targetPitch + idle - part.pitch) * smoothing
        part.roll = part.roll + (targetRoll - part.roll) * smoothing
        transform.rotation = torsoRotation * Quaternion.Euler(part.pitch, 0, part.roll)
      else
        transform.rotation = torsoRotation
      end
    end
  end
  entry.posed=true
  if not entry.clone.activeSelf then entry.clone:SetActive(true)end
end

-- ---------------------------------------------------------------------------
-- Actor 同步
-- ---------------------------------------------------------------------------
local function syncActor(actor)
  if actor == nil then return end
  local gameObject = actorGameObject(actor)
  if not isAlive(gameObject) then return end
  local actorId = actorIdOf(actor)
  if actorId == nil then return end
  local entry = actors[actorId]
  if entry == nil then
    entry = {
      actor = actor,
      actorID = actorId,
      className = "",
      clone = nil,
      parts = {},
      mainRenderer = nil,
      visible = true,
    }
    actors[actorId] = entry
  end

  entry.actor = actor
  local className, visible = readState(actor)
  entry.visible = visible
  if entry.mainRenderer == nil then
    entry.mainRenderer = findMainRenderer(gameObject)
  end

  if className == "" then
    clearClone(entry)
    return
  end

  ensureClone(entry, className)
  if not visible or not isActorRenderable(entry) then
    if entry.clone ~= nil and entry.clone.activeSelf then
      entry.clone:SetActive(false)
    end
    return
  end

  -- LateUpdate enables the clone only after a complete valid bone pose.
end

local function refreshActors()
  local ok, list = pcall(function()
    return CS.DouyinActorService.GetActors()
  end)
  if not ok or list == nil then return end

  local seen = {}
  for index = 0, list.Length - 1 do
    local actor = list[index]
    local gameObject = actorGameObject(actor)
    local actorId = actorIdOf(actor)
    if actor ~= nil and isAlive(gameObject) and actorId ~= nil then
      seen[actorId] = true
      syncActor(actor)
    end
  end

  local stale = {}
  for actorId, entry in pairs(actors) do
    if seen[actorId] ~= true then
      table.insert(stale, actorId)
    end
    if entry.actor == nil or not isAlive(actorGameObject(entry.actor)) then
      table.insert(stale, actorId)
    end
  end
  for _, actorId in ipairs(stale) do
    local entry = actors[actorId]
    if entry ~= nil then
      clearClone(entry)
      actors[actorId] = nil
    end
  end
end

local function clearAll()
  for actorId, entry in pairs(actors) do
    clearClone(entry)
  end
  actors = {}
end

-- ---------------------------------------------------------------------------
-- Runtime Host 接入
-- ---------------------------------------------------------------------------
local function handleRefresh(eventName, payload)
  if eventName ~= REFRESH_EVENT then return false end
  if type(payload) ~= "table" then return false end

  local actorId = tonumber(payload.actorID)
  if actorId == nil then
    refreshTimer = REFRESH_INTERVAL
    return true
  end

  local ok, actor = pcall(function()
    return CS.DouyinActorService.GetActorById(actorId)
  end)
  if not ok or actor == nil then return true end

  syncActor(actor)
  return true
end

local function registerWithHost()
  if runtimeScope == nil or resourceRoot == nil or resourceEntry ~= nil then return end
  local host = runtimeScope:GetRuntimeHostScript("runtime-host.lua")
  if host == nil or type(host.RegisterResource) ~= "function" then
    logger:warnOnce("runtime-host-unavailable", "outfit refresh events disabled")
    return
  end
  resourceEntry = host.RegisterResource(resourceRoot, RESOURCE_ID, {
    events = { REFRESH_EVENT },
    handler = handleRefresh,
    options = { resourceId = RESOURCE_ID },
  })
end

local function unregisterFromHost()
  if resourceEntry == nil or runtimeScope == nil then return end
  local host = runtimeScope:GetRuntimeHostScript("runtime-host.lua")
  if host ~= nil and type(host.UnregisterResource) == "function" then
    host.UnregisterResource(resourceEntry)
  end
  resourceEntry = nil
end

-- ---------------------------------------------------------------------------
-- 生命周期
-- ---------------------------------------------------------------------------
local nextInitAttempt=-1
local outfitStatus="waiting resources"
function Start()
 if started or Time.time<nextInitAttempt then return end
 nextInitAttempt=Time.time+.5
 -- RuntimeScope is fixed by the saved binding; retry only model payload readiness.
 resourceRoot=runtimeScope and runtimeScope:GetResourceRoot()or nil
 resourceRootTransform=resourceRoot and resourceRoot.transform or nil
 if not resourceRoot then outfitStatus="scope unavailable";return end
 local sourceSets=runtimeScope:GetTransformByPath(SOURCE_SETS_PATH)
 if not sourceSets then outfitStatus="source sets missing";return end
 for className,path in pairs(CLASS_SOURCE)do
  if not runtimeScope:GetGameObjectByPath(path)then outfitStatus="source missing: "..className;return end
 end
 disableCollidersOn(resourceRoot)
 sourceSets.localPosition=PROTOTYPE_PARK
 disableCollidersOn(sourceSets.gameObject)
 started=true;outfitStatus="resources ready"
 registerWithHost()
 refreshActors()
end

function OnEnable()
  if started then registerWithHost() end
end

function OnDisable()
  unregisterFromHost()
  clearAll()
end

function OnDestroy()
  unregisterFromHost()
  clearAll()
end

function OnActorSpawned(actor)
  if actor == nil then return end
  syncActor(actor)
end

function OnActorDespawned(actor)
  if actor == nil then return end
  local actorId = actorIdOf(actor)
  if actorId == nil then return end
  local entry = actors[actorId]
  if entry ~= nil then
    clearClone(entry)
    actors[actorId] = nil
  end
end

function Update()
  if not started then Start()end
  if not started then return end
  if not resourceEntry then registerWithHost()end
  refreshTimer = refreshTimer + Time.deltaTime
  if refreshTimer >= REFRESH_INTERVAL then
    refreshTimer = 0
    refreshActors()
  end
end

function LateUpdate()
  if runtimeScope == nil or resourceRoot == nil then return end
  local deltaTime = Time.deltaTime
  elapsed = elapsed + deltaTime

  for _, entry in pairs(actors) do
    updateEntry(entry, deltaTime)
  end
end
-- Driven by the existing replicated combat snapshot; no second network state.
function Equip(actor, className)
 if not started then Start()end
 if not started then return false end
 local id=actorIdOf(actor)
 if id==nil or CLASS_SOURCE[className]==nil then return false end
 local state=gameStates[id]
 if not state or state.actor~=actor or state.className~=className then
  gameStates[id]={actor=actor,className=className,visible=state==nil or state.visible}
  syncActor(actor)
 end
 local entry=actors[id]
 return entry~=nil and isAlive(entry.clone) and entry.sourceSignature~=nil
end
function SetVisible(actor, visible)
 local id=actorIdOf(actor);local state=id and gameStates[id]
 if not state then return false end
 if state.visible~=(visible==true)then state.visible=visible==true;syncActor(actor)end
 return true
end
function Unequip(actor)
 local id=actorIdOf(actor);if id==nil then return end
 gameStates[id]=nil
 local entry=actors[id]
 if entry then clearClone(entry);actors[id]=nil end
end

function GetOutfitStatus(actor)
 local entry=actors[actorIdOf(actor)]
 if not entry or not entry.clone then return outfitStatus.."; clone pending"end
 return entry.clone.activeInHierarchy and "visible"or "hidden"
end

function ResourcesReady()
 if not started then Start()end
 if not started then return false,outfitStatus end
 for className,path in pairs(CLASS_SOURCE)do
  if not completeVisual(runtimeScope:GetGameObjectByPath(path),className)then return false,"outfit mesh pending: "..className end
 end
 return true,"ready"
end
function IsReady(actor,className)
 local id=actorIdOf(actor);local entry=id and actors[id]
 if not entry or entry.className~=className or not isAlive(entry.clone)then return false end
 return entry.posed==true and entry.clone.activeInHierarchy and completeVisual(entry.clone,className)~=nil
end
