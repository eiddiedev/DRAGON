-- 黑龙鞍座：靠近触发、上下座按钮、骑手对齐与离座恢复
---@displayName 黑龙鞍座
---@start
---@var TriggerRangeScale:number=1
---@name 触发范围倍率
---@desc 基于初始触发范围等比放大
---@group 交互
---@end

local UnityEngine = CS.UnityEngine
local RuntimeScope = require("official.core.runtime_scope")
local Trigger = require("official.interaction.trigger")

local runtimeScope = RuntimeScope.from(self)
Trigger.applyRangeScale(self, TriggerRangeScale)

local interactionButton = nil
local localActorId = nil
local hasLocalPassenger = false
local localActor = nil

local seatedActors = {}
local savedScale = {}
local savedPosition = {}
local savedRotation = {}
local savedColliderEnabled = {}

local flightScript = nil

local function getFlightScript()
  if flightScript ~= nil then return flightScript end
  if runtimeScope == nil then return nil end
  flightScript = runtimeScope:GetScript("ms-flight.lua")
  return flightScript
end

local function notifyFlight(active)
  local flight = getFlightScript()
  if flight == nil or type(flight.SetRiderActive) ~= "function" then return end
  flight.SetRiderActive(active)
end

local function notifyOccupied(value)
  local flight = getFlightScript()
  if flight == nil or type(flight.SetOccupied) ~= "function" then return end
  flight.SetOccupied(value)
end

local function setButtonText(text)
  if interactionButton == nil then return end
  local label = interactionButton:GetComponentInChildren(
    typeof(CS.UnityEngine.UI.Text), true)
  if label ~= nil then
    label.text = text
  end
end

local function ensureInteractionButton()
  if interactionButton == nil then
    interactionButton = self:AddInteractorButton()
  end
  setButtonText(hasLocalPassenger and "站起" or "坐下")
end

local function removeInteractionButton()
  if interactionButton ~= nil then
    self:RemoveInteractorButton(interactionButton)
    interactionButton = nil
  end
end

local function resolveSeatTrans()
  return self.transform
end

local function alignActorHipsToSeat(actor, target)
  target = target or resolveSeatTrans()
  if actor == nil or actor.gameObject == nil or target == nil then return end

  local trans = actor.gameObject.transform
  trans:SetParent(target)
  trans.localPosition = UnityEngine.Vector3.zero
  trans.localRotation = UnityEngine.Quaternion.identity

  local original = savedScale[actor] or UnityEngine.Vector3.one
  local parentScale = target.lossyScale
  trans.localScale = UnityEngine.Vector3(
    original.x / (parentScale.x ~= 0 and parentScale.x or 1),
    original.y / (parentScale.y ~= 0 and parentScale.y or 1),
    original.z / (parentScale.z ~= 0 and parentScale.z or 1)
  )

  local animator = actor.gameObject:GetComponentInChildren(
    typeof(CS.UnityEngine.Animator))
  if animator == nil then return end

  local hips = animator:GetBoneTransform(CS.UnityEngine.HumanBodyBones.Hips)
  if hips == nil then return end

  local hipsPosition = hips.position
  local actorPosition = trans.position
  trans.position = UnityEngine.Vector3(
    actorPosition.x - (hipsPosition.x - actorPosition.x),
    actorPosition.y - (hipsPosition.y - actorPosition.y),
    actorPosition.z - (hipsPosition.z - actorPosition.z)
  )
end

local function setActorColliderEnabled(actor, enabled)
  if actor == nil or actor.gameObject == nil then return end
  local collider = actor.gameObject:GetComponent(typeof(CS.UnityEngine.Collider))
  if collider == nil then return end

  if not enabled then
    savedColliderEnabled[actor] = collider.enabled
    collider.enabled = false
  else
    local previous = savedColliderEnabled[actor]
    collider.enabled = previous == nil or previous
    savedColliderEnabled[actor] = nil
  end
end

local function placeActorAtStandPoint(actor)
  if actor == nil or actor.gameObject == nil then return end

  local trans = actor.gameObject.transform
  trans:SetParent(nil)

  if savedScale[actor] ~= nil then
    trans.localScale = savedScale[actor]
    savedScale[actor] = nil
  end

  local savedPos = savedPosition[actor]
  local savedRot = savedRotation[actor]
  if savedPos ~= nil and savedRot ~= nil then
    actor.position = savedPos
    actor.rotation = savedRot
  else
    local right = self.transform.right
    local base = self.transform.position
    actor.position = UnityEngine.Vector3(
      base.x + right.x * 1.2,
      base.y,
      base.z + right.z * 1.2
    )
    actor.rotation = self.transform.rotation
  end

  savedPosition[actor] = nil
  savedRotation[actor] = nil
end

function OnActorTriggerEnter(actor)
  if actor == nil or not actor.isLocal then return end
  localActorId = actor.actorID
  self:EnableInteraction()
end

function OnActorTriggerExit(actor)
  if actor == nil or not actor.isLocal then return end

  -- 在座时保留 Actor ID 和交互通道，保证飞行中仍能站起。
  if not hasLocalPassenger then
    self:DisableInteraction()
    localActorId = nil
  end
end

function OnFocus(handType)
  ensureInteractionButton()
end

function OnLostFocus(handType)
  removeInteractionButton()
end

function OnInteractorButtonClick(index)
  if index ~= 1 or localActorId == nil then return end

  local actor = DouyinActorService.GetActorById(localActorId)
  if actor == nil then return end

  if hasLocalPassenger then
    actor:StandUp(self.gameObject)
  else
    if actor:IsFlying() or resolveSeatTrans() == nil then return end
    actor:SitDown(self.gameObject, true)
  end
end

function OnSeatEntered(actor, handType)
  if actor == nil or actor.gameObject == nil then return end

  local target = resolveSeatTrans()
  if target == nil then return end

  local trans = actor.gameObject.transform
  savedPosition[actor] = trans.position
  savedRotation[actor] = trans.rotation
  savedScale[actor] = trans.localScale

  alignActorHipsToSeat(actor, target)
  seatedActors[actor] = target
  setActorColliderEnabled(actor, false)
  notifyOccupied(true)

  if actor.isLocal then
    hasLocalPassenger = true
    localActor = actor
    if actor.Immobilize ~= nil then
      actor:Immobilize(true)
    end
    self:EnableInteraction()
    ensureInteractionButton()
    notifyFlight(true)
  end
end

function OnSeatExited(actor)
  if actor == nil then return end

  -- 先停止持续对齐，再解除挂载，避免离座后又被拉回座位。
  seatedActors[actor] = nil
  if actor.gameObject == nil then
    notifyOccupied(false)
    if actor.isLocal then
      hasLocalPassenger = false
      localActor = nil
      notifyFlight(false)
    end
    return
  end
  placeActorAtStandPoint(actor)
  setActorColliderEnabled(actor, true)
  notifyOccupied(false)

  if actor.isLocal then
    hasLocalPassenger = false
    if localActor == actor then
      localActor = nil
    end
    if actor.Immobilize ~= nil then
      actor:Immobilize(false)
    end
    setButtonText("坐下")
    notifyFlight(false)
  end
end

function LateUpdate()
  for actor, target in pairs(seatedActors) do
    alignActorHipsToSeat(actor, target)
  end
end

local function cleanupLocalRider()
  if localActor ~= nil and localActor.Immobilize ~= nil then
    localActor:Immobilize(false)
  end
  localActor = nil
  hasLocalPassenger = false
  seatedActors = {}
  notifyOccupied(false)
  notifyFlight(false)
end

function OnDisable()
  removeInteractionButton()
end

function OnDestroy()
  removeInteractionButton()
  cleanupLocalRider()
end
