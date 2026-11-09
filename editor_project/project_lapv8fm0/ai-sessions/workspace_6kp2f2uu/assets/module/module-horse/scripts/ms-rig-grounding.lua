-- Animated creature grounding companion.
-- Owns facing calibration, terrain sampling, grounded pose resolution, and scripted Rigidbody stabilization.
---@displayName 生物贴地

local UnityEngine = CS.UnityEngine
local Time = UnityEngine.Time
local Physics = UnityEngine.Physics
local Mathf = UnityEngine.Mathf
local Quaternion = UnityEngine.Quaternion
local Vector3 = UnityEngine.Vector3
local Logger = require("official.core.logger")
local motionLogger = Logger.create("animated-creature-grounding")

-- BEGIN TEMPLATE CONFIG
local facingMismatchAngleThreshold = 20
-- END TEMPLATE CONFIG

local hostRuntime = {}

local function bindHostRuntime(runtime)
    if
        type(runtime) ~= "table" or
            (runtime.controlProfile ~= "land" and runtime.controlProfile ~= "flying" and runtime.controlProfile ~= "fish") or
            tonumber(runtime.groundProbeDistance) == nil or tonumber(runtime.groundProbeUpDistance) == nil or
            tonumber(runtime.groundContactOffset) == nil
     then
        return false
    end
    hostRuntime = runtime
    return true
end

local function getGroundProbeUpDistance()
    return math.max(0.01, tonumber(hostRuntime.groundProbeUpDistance))
end

local function getGroundProbeDownDistance()
    return math.max(0.01, tonumber(hostRuntime.groundProbeDistance))
end

local function getGroundSnapSpeed()
    return 8.0
end

local function getGroundWarnCooldown()
    return 1.0
end

local function getMountedGroundContactThreshold()
    return 0.18
end

local function normalizeOrUp(vec)
    if vec == nil then
        return Vector3.up
    end
    if vec.sqrMagnitude == nil or vec.sqrMagnitude < 0.0001 then
        return Vector3.up
    end
    return vec.normalized
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

local function getHorizontalForward(root)
    local forward = root and root.forward or Vector3.forward
    local horizontal = Vector3(forward.x, 0, forward.z)
    if horizontal.sqrMagnitude == nil or horizontal.sqrMagnitude < 0.0001 then
        return Vector3.forward
    end
    return horizontal.normalized
end

local function getPelvisNode(root)
    if hostRuntime.pelvisNode ~= nil then
        return hostRuntime.pelvisNode
    end
    if root == nil then
        return nil
    end
    local direct = findFirstByNameToken(root, "pelvis")
    hostRuntime.pelvisNode = direct
    return hostRuntime.pelvisNode
end

local function getHeadNode(root)
    if hostRuntime.headNode ~= nil then
        return hostRuntime.headNode
    end
    if root == nil then
        return nil
    end
    local direct = findFirstByNameToken(root, "head")
    hostRuntime.headNode = direct
    return hostRuntime.headNode
end

local function getAnatomicalForward(root)
    local pelvis = getPelvisNode(root)
    local head = getHeadNode(root)
    if pelvis ~= nil and head ~= nil and pelvis.position ~= nil and head.position ~= nil then
        local forward = Vector3(head.position.x - pelvis.position.x, 0, head.position.z - pelvis.position.z)
        if forward.sqrMagnitude ~= nil and forward.sqrMagnitude >= 0.0001 then
            return forward.normalized
        end
    end
    return getHorizontalForward(root)
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
    local dot = Mathf.Clamp(from.x * to.x + from.z * to.z, -1.0, 1.0)
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

local function rotateHorizontal(vector, yawDegrees)
    local radians = math.rad(yawDegrees)
    local cosValue = math.cos(radians)
    local sinValue = math.sin(radians)
    local x = vector.x * cosValue + vector.z * sinValue
    local z = (-vector.x) * sinValue + vector.z * cosValue
    local rotated = Vector3(x, 0, z)
    if rotated.sqrMagnitude == nil or rotated.sqrMagnitude < 0.0001 then
        return Vector3.forward
    end
    return rotated.normalized
end

local function ensureFacingCalibration(root, forceRefresh)
    if root == nil then
        hostRuntime.hasFacingMismatch = false
        hostRuntime.facingOffsetDegrees = 0.0
        hostRuntime.facingForward = Vector3.forward
        return hostRuntime.facingForward
    end

    if forceRefresh or hostRuntime.restAnatomicalForward == nil or hostRuntime.restRootForward == nil then
        hostRuntime.pelvisNode = nil
        hostRuntime.headNode = nil
        hostRuntime.restAnatomicalForward = getAnatomicalForward(root)
        hostRuntime.restRootForward = getHorizontalForward(root)
        local mismatchAngle = signedYawDegrees(hostRuntime.restRootForward, hostRuntime.restAnatomicalForward)
        hostRuntime.hasFacingMismatch = math.abs(mismatchAngle) >= (tonumber(facingMismatchAngleThreshold) or 20.0)
        hostRuntime.facingOffsetDegrees = hostRuntime.hasFacingMismatch and mismatchAngle or 0.0
        hostRuntime.facingForward =
            hostRuntime.hasFacingMismatch and hostRuntime.restAnatomicalForward or hostRuntime.restRootForward
        return hostRuntime.facingForward
    end

    if hostRuntime.facingForward == nil then
        hostRuntime.facingForward =
            hostRuntime.hasFacingMismatch and (hostRuntime.restAnatomicalForward or getAnatomicalForward(root)) or
            (hostRuntime.restRootForward or getHorizontalForward(root))
    end
    return hostRuntime.facingForward
end

local function warnMissingGround(message)
    local now = Time.time or 0.0
    if now - hostRuntime.lastGroundWarnTime < getGroundWarnCooldown() then
        return
    end
    hostRuntime.lastGroundWarnTime = now
    motionLogger:warn(message)
end

local function clearGroundingState()
    hostRuntime.grounded = false
    hostRuntime.groundOffset = nil
    hostRuntime.lastGroundHeight = nil
    hostRuntime.lastGroundNormal = nil
    hostRuntime.lastGroundedPosition = nil
    hostRuntime.lastGroundWarnTime = -1000.0
    hostRuntime.hasResolvedGroundOnce = false
end

local function enforceMountedRigidBodySettings()
    if hostRuntime.rb == nil then
        return
    end
    if hostRuntime.rb.useGravity == true and hostRuntime.hasStarted then
        motionLogger:warnOnce(
            "mounted-rigidbody-gravity-enabled",
            tostring(hostRuntime.controlProfile) ..
                " mounted animated creature root rigidBody should keep useGravity disabled; overriding to preserve scripted motion"
        )
    end
    hostRuntime.rb.isKinematic = true
    hostRuntime.rb.useGravity = false
end

local function isSelfCollider(root, collider)
    if root == nil or collider == nil or collider.transform == nil then
        return false
    end
    return collider.transform.root == root.root
end

local function isMountedRiderCollider(collider)
    if collider == nil or collider.transform == nil or hostRuntime.mountedRider == nil then
        return false
    end
    if hostRuntime.mountedRider.gameObject == nil or hostRuntime.mountedRider.gameObject.transform == nil then
        return false
    end
    return collider.transform.root == hostRuntime.mountedRider.gameObject.transform.root
end

local function shouldIgnoreGroundCollider(root, collider)
    if collider == nil then
        return true
    end
    if collider.isTrigger then
        return true
    end
    if isSelfCollider(root, collider) then
        return true
    end
    if isMountedRiderCollider(collider) then
        return true
    end
    return false
end

local function getRaycastHitAt(hits, index)
    if hits == nil then
        return nil
    end

    local hit = hits[index]
    if hit ~= nil then
        return hit
    end

    if type(hits.GetValue) == "function" then
        local ok, value =
            pcall(
            function()
                return hits:GetValue(index)
            end
        )
        if ok then
            return value
        end
    end

    return nil
end

local function sampleGroundAt(root, worldPosition)
    if root == nil or worldPosition == nil or Physics == nil then
        return nil
    end

    local origin = Vector3(worldPosition.x, worldPosition.y + getGroundProbeUpDistance(), worldPosition.z)
    local maxDistance = getGroundProbeUpDistance() + getGroundProbeDownDistance()
    local hits = Physics.RaycastAll(origin, Vector3.down, maxDistance)
    if hits == nil or hits.Length == nil or hits.Length <= 0 then
        return nil
    end

    local best = nil
    local bestDistance = nil
    for i = 0, hits.Length - 1 do
        local hit = getRaycastHitAt(hits, i)
        if hit ~= nil then
            local collider = hit.collider
            if collider ~= nil and not shouldIgnoreGroundCollider(root, collider) then
                local hitDistance = tonumber(hit.distance) or 0.0
                if best == nil or hitDistance < bestDistance then
                    best = hit
                    bestDistance = hitDistance
                end
            end
        end
    end

    if best == nil then
        return nil
    end

    return {
        point = best.point,
        normal = normalizeOrUp(best.normal),
        distance = tonumber(best.distance) or 0.0,
        collider = best.collider
    }
end

local function ensureGroundOffset(root, groundHit, forceResetOffset)
    if root == nil or groundHit == nil or groundHit.point == nil then
        return hostRuntime.groundOffset
    end

    -- Land creatures must plant their pivot on the terrain surface, not preserve
    -- the (possibly airborne) spawn-time height differential. The contact offset
    -- accounts for pivot-to-foot distance and is authored per rig, defaulting to 0.
    if hostRuntime.controlProfile == "land" then
        hostRuntime.groundOffset = tonumber(hostRuntime.groundContactOffset)
        return hostRuntime.groundOffset
    end

    if forceResetOffset or hostRuntime.groundOffset == nil then
        hostRuntime.groundOffset = root.position.y - groundHit.point.y
    end

    return hostRuntime.groundOffset
end

local function applyGroundAlignedRotation(root, targetNormal, deltaTime)
    if root == nil then
        return
    end

    local limitedNormal = normalizeOrUp(targetNormal)
    local heading =
        hostRuntime.facingForward or
        (hostRuntime.hasFacingMismatch and (hostRuntime.restAnatomicalForward or getAnatomicalForward(root)) or
            getHorizontalForward(root))
    local rootForward =
        hostRuntime.hasFacingMismatch and rotateHorizontal(heading, hostRuntime.facingOffsetDegrees or 0.0) or heading
    local forward = Vector3.ProjectOnPlane(rootForward, limitedNormal)
    if forward.sqrMagnitude == nil or forward.sqrMagnitude < 0.0001 then
        forward = Vector3.ProjectOnPlane(Vector3.forward, limitedNormal)
    end
    if forward.sqrMagnitude == nil or forward.sqrMagnitude < 0.0001 then
        return
    end

    local targetRotation = Quaternion.LookRotation(forward.normalized, limitedNormal)
    local t = Mathf.Clamp01(getGroundSnapSpeed() * (deltaTime or 0.0))
    if t <= 0.0 then
        root.rotation = targetRotation
        return
    end
    root.rotation = Quaternion.Slerp(root.rotation, targetRotation, t)
end

local function resolveGroundedPose(root, candidatePosition, deltaTime, forceResetOffset, immediateSnap, shouldWarnOnMiss)
    if root == nil or candidatePosition == nil then
        return candidatePosition, nil
    end

    local groundHit = sampleGroundAt(root, candidatePosition)
    if groundHit == nil then
        hostRuntime.grounded = false
        if shouldWarnOnMiss and hostRuntime.hasResolvedGroundOnce then
            warnMissingGround("ground probe missed; keeping current mounted height")
        end
        return Vector3(candidatePosition.x, root.position.y, candidatePosition.z), nil
    end

    local offset = ensureGroundOffset(root, groundHit, forceResetOffset)
    local targetY = groundHit.point.y + (tonumber(offset) or 0.0)
    local currentY = root.position.y
    local snappedY = targetY
    if not immediateSnap then
        snappedY = Mathf.MoveTowards(currentY, targetY, getGroundSnapSpeed() * deltaTime)
    end

    hostRuntime.grounded = true
    hostRuntime.hasResolvedGroundOnce = true
    hostRuntime.lastGroundHeight = targetY
    hostRuntime.lastGroundNormal = groundHit.normal
    hostRuntime.lastGroundedPosition = Vector3(candidatePosition.x, snappedY, candidatePosition.z)

    return hostRuntime.lastGroundedPosition, groundHit
end

local function refreshMountedGroundingInternal(forceResetOffset)
    if hostRuntime.controlProfile ~= "land" then
        return false
    end
    local root = self and self.transform or nil
    if root == nil then
        return false
    end

    enforceMountedRigidBodySettings()
    local groundedPosition, groundHit = resolveGroundedPose(root, root.position, 0.0, forceResetOffset, true, true)
    if groundHit == nil then
        return false
    end

    root.position = groundedPosition
    applyGroundAlignedRotation(root, groundHit.normal, 0.0)
    return true
end

-- Smooth per-frame grounding used while the land creature is idle/unmounted so it
-- keeps following terrain height and slope instead of only snapping once at Start.
local function refreshUnmountedGroundingInternal(dt)
    if hostRuntime.controlProfile ~= "land" then
        return false
    end
    local root = self and self.transform or nil
    if root == nil then
        return false
    end

    local groundedPosition, groundHit = resolveGroundedPose(root, root.position, dt or 0.0, false, false, false)
    if groundHit == nil then
        return false
    end

    root.position = groundedPosition
    applyGroundAlignedRotation(root, groundHit.normal, dt or 0.0)
    return true
end

local function clampMountedAirborneDescent(root, currentPosition, candidatePosition, verticalIntent)
    if root == nil or currentPosition == nil or candidatePosition == nil then
        return candidatePosition, false
    end
    if tonumber(verticalIntent) == nil or tonumber(verticalIntent) >= 0 then
        return candidatePosition, false
    end

    local probePosition =
        Vector3(candidatePosition.x, math.max(currentPosition.y, candidatePosition.y), candidatePosition.z)
    local groundHit = sampleGroundAt(root, probePosition)
    if groundHit == nil or groundHit.point == nil then
        return candidatePosition, false
    end

    local contactThreshold = getMountedGroundContactThreshold()
    local currentClearance = currentPosition.y - groundHit.point.y
    local candidateClearance = candidatePosition.y - groundHit.point.y
    local storedClearance = tonumber(hostRuntime.mountedGroundClearance)

    if storedClearance == nil and currentClearance <= contactThreshold then
        storedClearance = math.max(currentClearance, 0.0)
        hostRuntime.mountedGroundClearance = storedClearance
    end
    if storedClearance == nil and candidateClearance <= contactThreshold then
        storedClearance = math.max(candidateClearance, 0.0)
        hostRuntime.mountedGroundClearance = storedClearance
    end

    local minimumHeight = groundHit.point.y + math.max(storedClearance or 0.0, 0.0)
    if candidatePosition.y >= minimumHeight then
        return candidatePosition, false
    end

    return Vector3(candidatePosition.x, minimumHeight, candidatePosition.z), true
end

function EnforceRigRigidbodySettings(runtime)
    if not bindHostRuntime(runtime) then
        return false
    end
    enforceMountedRigidBodySettings()
    return true
end

function EnsureRigFacingCalibration(runtime, root, forceRefresh)
    if not bindHostRuntime(runtime) then
        return nil
    end
    return ensureFacingCalibration(root, forceRefresh == true)
end

function GetRigHorizontalForward(runtime, root)
    if not bindHostRuntime(runtime) then
        return Vector3.forward
    end
    return getHorizontalForward(root)
end

function RotateRigHorizontal(runtime, vector, yawDegrees)
    if not bindHostRuntime(runtime) then
        return vector
    end
    return rotateHorizontal(vector, yawDegrees)
end

function ResolveRigGroundedPose(
    runtime,
    root,
    candidatePosition,
    deltaTime,
    forceResetOffset,
    immediateSnap,
    shouldWarnOnMiss)
    if not bindHostRuntime(runtime) then
        return candidatePosition, nil
    end
    return resolveGroundedPose(
        root,
        candidatePosition,
        deltaTime,
        forceResetOffset == true,
        immediateSnap == true,
        shouldWarnOnMiss == true
    )
end

function ApplyRigGroundAlignedRotation(runtime, root, targetNormal, deltaTime)
    if not bindHostRuntime(runtime) then
        return false
    end
    applyGroundAlignedRotation(root, targetNormal, deltaTime)
    return true
end

function RefreshRigMountedGrounding(runtime, forceResetOffset)
    if not bindHostRuntime(runtime) then
        return false
    end
    return refreshMountedGroundingInternal(forceResetOffset == true)
end

function RefreshRigUnmountedGrounding(runtime, deltaTime)
    if not bindHostRuntime(runtime) then
        return false
    end
    return refreshUnmountedGroundingInternal(deltaTime)
end

function ClearRigGroundingState(runtime)
    if not bindHostRuntime(runtime) then
        return false
    end
    clearGroundingState()
    return true
end

function ClampRigAirborneDescent(runtime, root, currentPosition, candidatePosition, verticalIntent)
    if not bindHostRuntime(runtime) then
        return candidatePosition, false
    end
    return clampMountedAirborneDescent(root, currentPosition, candidatePosition, verticalIntent)
end
