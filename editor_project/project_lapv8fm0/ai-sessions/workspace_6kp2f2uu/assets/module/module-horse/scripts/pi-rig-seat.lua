-- Shared rig Seat companion for mounted interaction.
-- Owns seat discovery, fallback alignment, anatomical orientation, and renderer-bound queries.
---@displayName 骑乘座位

local UnityEngine = CS.UnityEngine
local Vector3 = UnityEngine.Vector3
local Quaternion = UnityEngine.Quaternion
local Physics = UnityEngine.Physics
local GameObject = UnityEngine.GameObject
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")
local seatLogger = Logger.create("animated-creature-interaction/rig-seat")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)
local resourceRoot = runtimeScope ~= nil and runtimeScope:GetResourceRoot() or nil

-- BEGIN TEMPLATE CONFIG
local seatTargetPath = "rig/SK_Zebra/root/ZEBRA_/ZEBRA_ Pelvis/ZEBRA_ Spine/ZEBRA_ Spine1/SaddlePad/SeatAnchor"
local standUpTargetPath = nil
-- END TEMPLATE CONFIG

local FACING_MISMATCH_ANGLE_THRESHOLD = 20.0
local SEAT_FALLBACK_FORWARD_RATIO = 2 / 5
local SEAT_FALLBACK_BOTTOM_MARGIN_RATIO = 0.1
local SEAT_FALLBACK_TOP_SAFE_BAND_RATIO = 0.22
local SEAT_FALLBACK_PROBE_HEIGHT = 0.25
local SEAT_FALLBACK_SURFACE_LIFT = 0.08
local SEAT_EMBEDDED_SURFACE_DELTA_RATIO = 0.05
local SEAT_EMBEDDED_SURFACE_DELTA_MIN = 0.08

local seatAnchor = nil
local seatTrans = nil
local standUpAnchor = nil
local seatRuntimeFallback = nil
local hasFacingMismatch = false
local facingOffsetDegrees = 0.0
local cachedAnatomicalForward = nil
local seatControlProfile = nil

local function usesBackSurfaceFallback()
    return seatControlProfile == "flying" or seatControlProfile == "fish"
end

local function setSeatControlProfile(profile)
    if profile ~= "land" and profile ~= "flying" and profile ~= "fish" then
        seatLogger:warnOnce("control-profile-unavailable", "rig seat control profile unavailable", tostring(profile))
        return false
    end
    seatControlProfile = profile
    return true
end

local function clamp(value, minValue, maxValue)
    if value < minValue then
        return minValue
    end
    if value > maxValue then
        return maxValue
    end
    return value
end

local function arrayAt(values, index)
    if values == nil then
        return nil
    end
    local direct = values[index]
    if direct ~= nil then
        return direct
    end
    if type(values.GetValue) == "function" then
        local ok, value =
            pcall(
            function()
                return values:GetValue(index)
            end
        )
        if ok then
            return value
        end
    end
    return nil
end

local function getCombinedRendererBounds(root)
    if root == nil or root.gameObject == nil then
        return nil
    end

    local renderers = root.gameObject:GetComponentsInChildren(typeof(UnityEngine.Renderer), true)
    if renderers == nil or renderers.Length == nil or renderers.Length <= 0 then
        return nil
    end

    local bounds = nil
    for i = 0, renderers.Length - 1 do
        local renderer = arrayAt(renderers, i)
        if renderer ~= nil then
            if bounds == nil then
                bounds = renderer.bounds
            else
                bounds:Encapsulate(renderer.bounds)
            end
        end
    end
    return bounds
end

local function getHorizontalForward(root)
    local forward = root and root.forward or Vector3.forward
    local horizontal = Vector3(forward.x, 0, forward.z)
    if horizontal.sqrMagnitude == nil or horizontal.sqrMagnitude < 0.0001 then
        return Vector3.forward
    end
    return horizontal.normalized
end

local function findFirstByNameToken(parent, token)
    if parent == nil or token == nil or token == "" then
        return nil
    end
    local lowerToken = string.lower(token)
    local selfName = string.lower(tostring(parent.name or ""))
    if string.find(selfName, lowerToken, 1, true) ~= nil then
        return parent
    end
    for i = 0, parent.childCount - 1 do
        local child = parent:GetChild(i)
        if child ~= nil then
            local found = findFirstByNameToken(child, token)
            if found ~= nil then
                return found
            end
        end
    end
    return nil
end

local function findPelvisLikeNode(root)
    if root == nil then
        return nil
    end
    return findFirstByNameToken(root, "pelvis")
end

local function findHeadLikeNode(root)
    if root == nil then
        return nil
    end
    return findFirstByNameToken(root, "head")
end

local function getAnatomicalForward(root)
    if root == nil then
        return Vector3.forward
    end
    local pelvis = findPelvisLikeNode(root)
    local head = findHeadLikeNode(root)
    if pelvis ~= nil and head ~= nil and pelvis.position ~= nil and head.position ~= nil then
        local forward = Vector3(head.position.x - pelvis.position.x, 0, head.position.z - pelvis.position.z)
        if forward.sqrMagnitude ~= nil and forward.sqrMagnitude >= 0.0001 then
            return forward.normalized
        end
    end
    return getHorizontalForward(root)
end

local function getCreatureUp(root)
    local up = root and root.up or Vector3.up
    if up.sqrMagnitude == nil or up.sqrMagnitude < 0.0001 then
        return Vector3.up
    end
    return up.normalized
end

local function signedYawDegrees(fromVec, toVec)
    local from = Vector3(fromVec.x, 0, fromVec.z)
    local to = Vector3(toVec.x, 0, toVec.z)
    if from.sqrMagnitude == nil or from.sqrMagnitude < 0.0001 then
        from = Vector3.forward
    else
        from = from.normalized
    end
    if to.sqrMagnitude == nil or to.sqrMagnitude < 0.0001 then
        to = Vector3.forward
    else
        to = to.normalized
    end
    local cross = from.x * to.z - from.z * to.x
    local dot = clamp(from.x * to.x + from.z * to.z, -1.0, 1.0)
    local angleRadians = nil
    local ok, result =
        pcall(
        function()
            return math.atan(cross, dot)
        end
    )
    if ok then
        angleRadians = result
    else
        angleRadians = math.atan(cross / math.max(math.abs(dot), 0.0001))
        if dot < 0 then
            if cross >= 0 then
                angleRadians = angleRadians + math.pi
            else
                angleRadians = angleRadians - math.pi
            end
        end
    end
    return math.deg(angleRadians)
end

local function ensureFacingMismatchState(root)
    if root == nil then
        hasFacingMismatch = false
        facingOffsetDegrees = 0.0
        cachedAnatomicalForward = Vector3.forward
        return false
    end
    local anatomicalForward = getAnatomicalForward(root)
    local rootForward = getHorizontalForward(root)
    local mismatchAngle = signedYawDegrees(rootForward, anatomicalForward)
    facingOffsetDegrees = mismatchAngle
    cachedAnatomicalForward = anatomicalForward
    hasFacingMismatch = math.abs(mismatchAngle) >= FACING_MISMATCH_ANGLE_THRESHOLD
    return hasFacingMismatch
end

local function getBoundsExtentAlongDirection(bounds, direction)
    local dir = direction.normalized
    local extents = bounds.extents
    return math.abs(dir.x) * extents.x + math.abs(dir.y) * extents.y + math.abs(dir.z) * extents.z
end

local function buildSeatFallbackReferencePoint(root, bounds, pelvis)
    if root == nil or bounds == nil then
        return nil
    end

    local forward = cachedAnatomicalForward or getAnatomicalForward(root)
    local up = getCreatureUp(root)
    local probeBase = bounds.center
    if pelvis ~= nil and pelvis.position ~= nil then
        probeBase = pelvis.position
    end

    local forwardExtent = getBoundsExtentAlongDirection(bounds, forward)
    local upExtent = getBoundsExtentAlongDirection(bounds, up)
    local directionScale = 1
    if usesBackSurfaceFallback() then
        directionScale = -1
    end
    local forwardOffset = forwardExtent * SEAT_FALLBACK_FORWARD_RATIO * directionScale
    local upOffset = math.max(SEAT_FALLBACK_SURFACE_LIFT, upExtent * 0.14)
    return Vector3(
        probeBase.x + forward.x * forwardOffset + up.x * upOffset,
        probeBase.y + forward.y * forwardOffset + up.y * upOffset,
        probeBase.z + forward.z * forwardOffset + up.z * upOffset
    )
end

local function isSeatReferenceInsideBounds(bounds, point)
    if bounds == nil or point == nil then
        return false
    end
    local sizeY = bounds.size.y
    local bottomMargin = math.max(0.05, sizeY * SEAT_FALLBACK_BOTTOM_MARGIN_RATIO)
    local topSafeBand = math.max(0.18, sizeY * SEAT_FALLBACK_TOP_SAFE_BAND_RATIO)
    return point.x >= bounds.min.x and point.x <= bounds.max.x and point.z >= bounds.min.z and point.z <= bounds.max.z and
        point.y >= bounds.min.y + bottomMargin and
        point.y <= bounds.max.y - topSafeBand
end

local function isSeatReferenceEmbedded(bounds, point, surfacePoint)
    if not isSeatReferenceInsideBounds(bounds, point) then
        return false
    end
    if surfacePoint == nil then
        return true
    end
    local maxSurfaceDelta = math.max(SEAT_EMBEDDED_SURFACE_DELTA_MIN, bounds.size.y * SEAT_EMBEDDED_SURFACE_DELTA_RATIO)
    return (surfacePoint.y - point.y) > maxSurfaceDelta
end

local function tryFindSeatSurfaceHit(root, bounds, pelvis)
    if root == nil or bounds == nil then
        return nil
    end

    local referencePoint = buildSeatFallbackReferencePoint(root, bounds, pelvis)
    if referencePoint == nil then
        return nil
    end
    local origin = Vector3(referencePoint.x, referencePoint.y + SEAT_FALLBACK_PROBE_HEIGHT, referencePoint.z)
    local maxDistance = bounds.size.y + SEAT_FALLBACK_PROBE_HEIGHT * 2.0
    local hits = Physics.RaycastAll(origin, Vector3.down, maxDistance)
    if hits == nil or hits.Length == nil or hits.Length <= 0 then
        return referencePoint
    end

    local preferredHit = nil
    local preferredDistance = nil
    local triggerHit = nil
    local triggerDistance = nil
    for i = 0, hits.Length - 1 do
        local hit = arrayAt(hits, i)
        if
            hit ~= nil and hit.collider ~= nil and hit.collider.transform ~= nil and
                hit.collider.transform.root == root.root
         then
            local hitDistance = tonumber(hit.distance) or 0.0
            if hit.collider.isTrigger then
                if triggerHit == nil or hitDistance < triggerDistance then
                    triggerHit = hit
                    triggerDistance = hitDistance
                end
            else
                if preferredHit == nil or hitDistance < preferredDistance then
                    preferredHit = hit
                    preferredDistance = hitDistance
                end
            end
        end
    end

    local finalHit = preferredHit or triggerHit
    if finalHit == nil or finalHit.point == nil then
        return referencePoint
    end

    return Vector3(finalHit.point.x, finalHit.point.y + SEAT_FALLBACK_SURFACE_LIFT, finalHit.point.z)
end

local function ensureSeatRuntimeFallback(root)
    if root == nil then
        return nil
    end
    local fallbackParent = findPelvisLikeNode(root) or root
    if seatRuntimeFallback == nil then
        local go = GameObject("SeatRuntimeFallback")
        if go == nil then
            return nil
        end
        seatRuntimeFallback = go.transform
        seatRuntimeFallback:SetParent(fallbackParent)
    elseif seatRuntimeFallback.parent ~= fallbackParent then
        local worldPos = seatRuntimeFallback.position
        local worldRot = seatRuntimeFallback.rotation
        seatRuntimeFallback:SetParent(fallbackParent)
        seatRuntimeFallback.position = worldPos
        seatRuntimeFallback.rotation = worldRot
    end
    return seatRuntimeFallback
end

local function applySeatFallbackFromBounds(root)
    local bounds = getCombinedRendererBounds(root)
    if bounds == nil then
        return nil
    end

    local pelvis = findPelvisLikeNode(root)
    local fallback = ensureSeatRuntimeFallback(root)
    if fallback == nil then
        return nil
    end

    local candidate = tryFindSeatSurfaceHit(root, bounds, pelvis)
    fallback.position = candidate
    fallback.rotation = Quaternion.LookRotation(cachedAnatomicalForward or getAnatomicalForward(root), Vector3.up)
    return fallback
end

local function sampleSeatSurfaceAtWorldPoint(root, bounds, worldPoint)
    if root == nil or bounds == nil or worldPoint == nil or Physics == nil then
        return worldPoint
    end
    local origin = Vector3(worldPoint.x, bounds.max.y + SEAT_FALLBACK_PROBE_HEIGHT, worldPoint.z)
    local maxDistance = bounds.size.y + SEAT_FALLBACK_PROBE_HEIGHT * 2.0
    local hits = Physics.RaycastAll(origin, Vector3.down, maxDistance)
    if hits == nil or hits.Length == nil or hits.Length <= 0 then
        return worldPoint
    end

    local preferredHit = nil
    local preferredDistance = nil
    local triggerHit = nil
    local triggerDistance = nil
    for i = 0, hits.Length - 1 do
        local hit = arrayAt(hits, i)
        if
            hit ~= nil and hit.collider ~= nil and hit.collider.transform ~= nil and
                hit.collider.transform.root == root.root
         then
            local hitDistance = tonumber(hit.distance) or 0.0
            if hit.collider.isTrigger then
                if triggerHit == nil or hitDistance < triggerDistance then
                    triggerHit = hit
                    triggerDistance = hitDistance
                end
            else
                if preferredHit == nil or hitDistance < preferredDistance then
                    preferredHit = hit
                    preferredDistance = hitDistance
                end
            end
        end
    end

    local finalHit = preferredHit or triggerHit
    if finalHit == nil or finalHit.point == nil then
        return worldPoint
    end
    return Vector3(finalHit.point.x, finalHit.point.y + SEAT_FALLBACK_SURFACE_LIFT, finalHit.point.z)
end

local function projectPointToPlane(point, planeOrigin, planeNormal)
    if point == nil or planeOrigin == nil or planeNormal == nil then
        return point
    end
    local normal = planeNormal.normalized
    local toPoint = Vector3(point.x - planeOrigin.x, point.y - planeOrigin.y, point.z - planeOrigin.z)
    local distance = toPoint.x * normal.x + toPoint.y * normal.y + toPoint.z * normal.z
    return Vector3(point.x - normal.x * distance, point.y - normal.y * distance, point.z - normal.z * distance)
end

local function applySeatMidlineAdjustment(root, bounds)
    if not hasFacingMismatch or root == nil or bounds == nil or seatTrans == nil then
        return
    end
    local pelvis = findPelvisLikeNode(root)
    if pelvis == nil or pelvis.position == nil then
        return
    end
    local forward = cachedAnatomicalForward or getAnatomicalForward(root)
    local up = getCreatureUp(root)
    local planeNormal = Vector3.Cross(forward, up)
    if planeNormal.sqrMagnitude == nil or planeNormal.sqrMagnitude < 0.0001 then
        return
    end
    local projected = projectPointToPlane(seatTrans.position, pelvis.position, planeNormal)
    local adjusted = sampleSeatSurfaceAtWorldPoint(root, bounds, projected)
    local seatPositionHost = seatTrans == seatRuntimeFallback and seatTrans or (seatAnchor or seatTrans)
    if seatPositionHost ~= nil then
        seatPositionHost.position = adjusted
    end
end

local function alignSeatFacing(root, anchor, seat)
    if root == nil then
        return
    end
    local targetRotation = Quaternion.LookRotation(cachedAnatomicalForward or getAnatomicalForward(root), Vector3.up)
    if anchor ~= nil then
        anchor.rotation = targetRotation
    end
    if seat ~= nil then
        seat.rotation = targetRotation
    end
end

local function resolveMountHelpers()
    local root = resourceRoot ~= nil and resourceRoot.transform or nil
    if root == nil then
        seatLogger:warn("resource root unavailable; mount interaction disabled")
        return
    end

    ensureFacingMismatchState(root)
    local seatReason = nil
    seatAnchor, seatReason = runtimeScope:GetTransformByPath(seatTargetPath)
    if seatAnchor == nil then
        seatLogger:warn("SeatAnchor missing; mount unavailable", "reason=" .. tostring(seatReason))
    else
        seatTrans = seatAnchor
    end

    local bounds = getCombinedRendererBounds(root)
    local seatReference = seatTrans or seatAnchor
    local sampledSeatSurface = nil
    if seatReference ~= nil and bounds ~= nil then
        sampledSeatSurface = sampleSeatSurfaceAtWorldPoint(root, bounds, seatReference.position)
    end
    if
        seatReference ~= nil and bounds ~= nil and
            isSeatReferenceEmbedded(bounds, seatReference.position, sampledSeatSurface)
     then
        local fallback = applySeatFallbackFromBounds(root)
        if fallback ~= nil then
            seatTrans = fallback
            if usesBackSurfaceFallback() then
                seatLogger:warn("SeatAnchor appears inside body; using pelvis-linked back-surface seat fallback")
            else
                seatLogger:warn("SeatAnchor appears inside body; using pelvis-linked forward-surface seat fallback")
            end
        end
    elseif seatTrans == nil then
        local fallback = applySeatFallbackFromBounds(root)
        if fallback ~= nil then
            seatTrans = fallback
            if usesBackSurfaceFallback() then
                seatLogger:warn("Seat helper missing or incomplete; using pelvis-linked back-surface seat fallback")
            else
                seatLogger:warn("Seat helper missing or incomplete; using pelvis-linked forward-surface seat fallback")
            end
        end
    end

    if bounds ~= nil then
        applySeatMidlineAdjustment(root, bounds)
    end

    alignSeatFacing(root, seatAnchor, seatTrans)

    if standUpTargetPath ~= nil and standUpTargetPath ~= "" then
        standUpAnchor = runtimeScope:GetTransformByPath(standUpTargetPath)
    end
    if standUpAnchor == nil then
        seatLogger:info("StandUpAnchor missing; current world position will be kept on dismount")
    end
end

function ResolveRigMountHelpers(profile)
    if not setSeatControlProfile(profile) then
        return false
    end
    if runtimeScope == nil then
        seatLogger:warnOnce("scope-unavailable", "resource scope unavailable", runtimeScopeReason)
        return false
    end
    resolveMountHelpers()
    return seatTrans ~= nil
end

function HasRigSeatTarget(profile)
    if profile ~= nil and profile ~= seatControlProfile then
        return ResolveRigMountHelpers(profile)
    end
    if seatControlProfile == nil then
        return false
    end
    if seatTrans == nil then
        ResolveRigMountHelpers(seatControlProfile)
    end
    return seatTrans ~= nil
end

function GetRigSeatTarget()
    if not HasRigSeatTarget() then
        return nil
    end
    return seatTrans
end

function GetRigStandUpAnchor()
    if standUpAnchor == nil and standUpTargetPath ~= nil and standUpTargetPath ~= "" then
        standUpAnchor = runtimeScope:GetTransformByPath(standUpTargetPath)
    end
    return standUpAnchor
end

function GetRigRootTransform()
    if resourceRoot ~= nil and resourceRoot.transform ~= nil then
        return resourceRoot.transform
    end
    return self ~= nil and self.transform or nil
end

function GetRigAnatomicalForward(root)
    return cachedAnatomicalForward or getAnatomicalForward(root)
end

function GetRigCombinedRendererBounds(root)
    return getCombinedRendererBounds(root)
end

function SampleRigSeatSurface(root, bounds, worldPoint)
    return sampleSeatSurfaceAtWorldPoint(root, bounds, worldPoint)
end
