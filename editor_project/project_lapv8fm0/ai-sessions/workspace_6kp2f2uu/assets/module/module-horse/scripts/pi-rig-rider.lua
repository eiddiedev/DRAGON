-- Shared rig rider companion for mounted interaction.
-- Owns actor parenting, scale compensation, dismount placement, collider state, and per-frame seat alignment.
---@displayName 骑乘角色

local UnityEngine = CS.UnityEngine
local Vector3 = UnityEngine.Vector3
local Quaternion = UnityEngine.Quaternion
local HumanBodyBones = UnityEngine.HumanBodyBones
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")
local riderLogger = Logger.create("animated-creature-interaction/rig-rider")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)
local seatPeer = nil

local MOUNTED_HIP_CLEARANCE_RATIO = 0.08
local MOUNTED_HIP_CLEARANCE_MIN = 0.08
local MOUNTED_HIP_CLEARANCE_MAX = 0.18
local DISMOUNT_MIN_ACTOR_RADIUS = 0.35
local DISMOUNT_CLEARANCE = 0.15
local DISMOUNT_FALLBACK_DISTANCE = 1.1

local seatedActors = {}
local savedScale = {}
local savedDismountOffsets = {}
local savedDismountRotations = {}

local function clamp(value, minValue, maxValue)
    if value < minValue then
        return minValue
    end
    if value > maxValue then
        return maxValue
    end
    return value
end

local function resolveSeatPeer()
    if seatPeer ~= nil then
        return seatPeer
    end
    if runtimeScope == nil then
        riderLogger:warnOnce("scope-unavailable", "resource scope unavailable", runtimeScopeReason)
        return nil
    end
    local peer, reason = runtimeScope:GetScript("pi-rig-seat.lua")
    if
        peer == nil or type(peer.GetRigSeatTarget) ~= "function" or
            type(peer.GetRigStandUpAnchor) ~= "function" or
            type(peer.GetRigRootTransform) ~= "function" or
            type(peer.GetRigAnatomicalForward) ~= "function" or
            type(peer.GetRigCombinedRendererBounds) ~= "function" or
            type(peer.SampleRigSeatSurface) ~= "function"
     then
        riderLogger:warnOnce("seat-script-unavailable", "rig seat script unavailable", reason)
        return nil
    end
    seatPeer = peer
    return seatPeer
end

local function getCombinedRendererBounds(root)
    local peer = resolveSeatPeer()
    return peer ~= nil and peer.GetRigCombinedRendererBounds(root) or nil
end

local function sampleSeatSurfaceAtWorldPoint(root, bounds, worldPoint)
    local peer = resolveSeatPeer()
    return peer ~= nil and peer.SampleRigSeatSurface(root, bounds, worldPoint) or worldPoint
end

local function setActorColliderEnabled(actor, enabled)
    if actor == nil or actor.gameObject == nil then
        return
    end
    local collider = actor.gameObject:GetComponent(typeof(UnityEngine.CapsuleCollider))
    if collider ~= nil then
        collider.enabled = enabled
    end
end

local function getCreatureRootTransform()
    local peer = resolveSeatPeer()
    return peer ~= nil and peer.GetRigRootTransform() or nil
end

local function getSafeScaleAxis(value)
    if value == nil or math.abs(value) < 0.0001 then
        return 1.0
    end
    return value
end

local function isOutsideExpandedHorizontalBounds(bounds, worldPosition, actorRadius)
    if bounds == nil or worldPosition == nil then
        return false
    end
    local clearance = actorRadius + DISMOUNT_CLEARANCE
    return math.abs(worldPosition.x - bounds.center.x) > bounds.extents.x + clearance or
        math.abs(worldPosition.z - bounds.center.z) > bounds.extents.z + clearance
end

local function resolveSafeDismountPosition(actor, root)
    if root == nil then
        return nil
    end

    local creatureBounds = getCombinedRendererBounds(root)
    local actorBounds = nil
    if actor ~= nil and actor.gameObject ~= nil then
        actorBounds = getCombinedRendererBounds(actor.gameObject.transform)
    end
    local actorRadius = DISMOUNT_MIN_ACTOR_RADIUS
    if actorBounds ~= nil then
        actorRadius = math.max(actorRadius, actorBounds.extents.x, actorBounds.extents.z)
    end

    local savedOffset = savedDismountOffsets[actor]
    if savedOffset ~= nil then
        local candidate = root.position + savedOffset
        if creatureBounds == nil or isOutsideExpandedHorizontalBounds(creatureBounds, candidate, actorRadius) then
            return candidate
        end
    end

    local horizontalRight = Vector3.ProjectOnPlane(root.right, Vector3.up)
    if horizontalRight.sqrMagnitude == nil or horizontalRight.sqrMagnitude < 0.0001 then
        horizontalRight = Vector3.right
    else
        horizontalRight = horizontalRight.normalized
    end

    local distance = DISMOUNT_FALLBACK_DISTANCE
    local center = root.position
    if creatureBounds ~= nil then
        distance = math.max(creatureBounds.extents.x, creatureBounds.extents.z) + actorRadius + DISMOUNT_CLEARANCE
        center = creatureBounds.center
    end
    return Vector3(
        center.x + horizontalRight.x * distance,
        root.position.y,
        center.z + horizontalRight.z * distance
    )
end

local function placeActorAtStandPoint(actor)
    if actor == nil or actor.gameObject == nil then
        return
    end

    local actorTransform = actor.gameObject.transform
    actorTransform:SetParent(nil)
    if savedScale[actor] ~= nil then
        actorTransform.localScale = savedScale[actor]
    end

    local root = getCreatureRootTransform()
    local peer = resolveSeatPeer()
    local standUpAnchor = peer ~= nil and peer.GetRigStandUpAnchor() or nil
    if standUpAnchor ~= nil then
        actor.position = standUpAnchor.position
        actor.rotation = standUpAnchor.rotation
    else
        local safePosition = resolveSafeDismountPosition(actor, root)
        if safePosition ~= nil then
            actor.position = safePosition
        end
        local fallbackRotation = actorTransform.rotation
        if root ~= nil then
            fallbackRotation = root.rotation
        end
        actor.rotation = savedDismountRotations[actor] or fallbackRotation
    end

    savedScale[actor] = nil
    savedDismountOffsets[actor] = nil
    savedDismountRotations[actor] = nil
end

local function applyMountedSeatLift(actor, actorTransform, hips, target)
    if actor == nil or actorTransform == nil or hips == nil then
        return
    end
    local creatureRoot = getCreatureRootTransform()
    if creatureRoot == nil or target == nil then
        return
    end
    local creatureBounds = getCombinedRendererBounds(creatureRoot)
    local actorBounds = getCombinedRendererBounds(actorTransform)
    if creatureBounds == nil or actorBounds == nil then
        return
    end
    local surfacePoint = sampleSeatSurfaceAtWorldPoint(creatureRoot, creatureBounds, target.position)
    if surfacePoint == nil then
        return
    end
    local clearance =
        clamp(
        (tonumber(actorBounds.size.y) or 1.0) * MOUNTED_HIP_CLEARANCE_RATIO,
        MOUNTED_HIP_CLEARANCE_MIN,
        MOUNTED_HIP_CLEARANCE_MAX
    )
    local desiredHipY = math.max(surfacePoint.y + clearance, target.position.y)
    local currentHipY = hips.position.y
    if currentHipY < desiredHipY then
        local deltaY = desiredHipY - currentHipY
        actorTransform.position =
            Vector3(actorTransform.position.x, actorTransform.position.y + deltaY, actorTransform.position.z)
    end
end

local function alignActorHipsToSeat(actor, target)
    local peer = resolveSeatPeer()
    target = target or (peer ~= nil and peer.GetRigSeatTarget() or nil)
    if actor == nil or actor.gameObject == nil or target == nil then
        return
    end
    local actorTransform = actor.gameObject.transform
    actorTransform:SetParent(target)
    actorTransform.localPosition = Vector3.zero
    actorTransform.localRotation = Quaternion.identity
    local originalScale = savedScale[actor] or Vector3.one
    local parentScale = target.lossyScale
    actorTransform.localScale = Vector3(
        originalScale.x / getSafeScaleAxis(parentScale.x),
        originalScale.y / getSafeScaleAxis(parentScale.y),
        originalScale.z / getSafeScaleAxis(parentScale.z)
    )
    local root = getCreatureRootTransform() or target
    local anatomicalForward = peer ~= nil and peer.GetRigAnatomicalForward(root) or root.forward
    actorTransform.rotation = Quaternion.LookRotation(anatomicalForward, Vector3.up)
    local animator = actor.gameObject:GetComponentInChildren(typeof(UnityEngine.Animator))
    if animator == nil then
        return
    end
    local hips = animator:GetBoneTransform(HumanBodyBones.Hips)
    if hips == nil then
        return
    end
    local hipsPos = hips.position
    local actorPos = actorTransform.position
    actorTransform.position =
        Vector3(
        actorPos.x - (hipsPos.x - actorPos.x),
        actorPos.y - (hipsPos.y - actorPos.y),
        actorPos.z - (hipsPos.z - actorPos.z)
    )
    applyMountedSeatLift(actor, actorTransform, hips, target)
end

function PrepareRigActorMount(actor)
    local peer = resolveSeatPeer()
    local target = peer ~= nil and peer.GetRigSeatTarget() or nil
    if actor == nil or actor.gameObject == nil or target == nil then
        return false
    end

    local actorTransform = actor.gameObject.transform
    local root = getCreatureRootTransform()
    if root ~= nil then
        savedDismountOffsets[actor] = actorTransform.position - root.position
    end
    savedDismountRotations[actor] = actorTransform.rotation
    savedScale[actor] = actorTransform.localScale
    alignActorHipsToSeat(actor, target)
    seatedActors[actor] = target
    setActorColliderEnabled(actor, false)
    return true
end

function ReleaseRigActorMount(actor)
    if actor == nil then
        return false
    end
    seatedActors[actor] = nil
    placeActorAtStandPoint(actor)
    return true
end

function SetRigActorColliderEnabled(actor, enabled)
    setActorColliderEnabled(actor, enabled == true)
end

function LateUpdate()
    for actor, target in pairs(seatedActors) do
        alignActorHipsToSeat(actor, target)
    end
end
