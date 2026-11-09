-- RIG_RUNTIME_CONTRACT_JSON: {"schemaVersion":2,"rigFamily":"creature","capability":"1+2","controlProfile":"land","files":["ms-root.lua","ms-rig-grounding.lua","ms-rig-adapter.lua"]}
-- Animated creature motion template baseline.
-- Root motion host: owns lifecycle and mounted API, and delegates controller adaptation and grounding to rig companions.
---@displayName 生物运动

-- BEGIN TEMPLATE PARAMETERS
---@start
---@var defaultMoveSpeed:number=2.5
---@name 普通移动速度
---@desc 生物普通移动时的速度
---@group 移动
---@var defaultRunSpeed:number=4.5
---@name 奔跑速度
---@desc 生物奔跑或高强度输入时的速度
---@group 移动
---@var turnSpeed:number=120
---@name 转向灵敏度
---@desc 生物改变前进方向的快慢
---@group 移动
---@end
-- END TEMPLATE PARAMETERS

local UnityEngine = CS.UnityEngine
local Time = UnityEngine.Time
local Physics = UnityEngine.Physics
local Mathf = UnityEngine.Mathf
local Quaternion = UnityEngine.Quaternion
local Vector3 = UnityEngine.Vector3
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")
local motionLogger = Logger.create("animated-creature-motion")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)
local adapterPeer = nil
local generatedControllerAdapter = nil

-- BEGIN TEMPLATE CONFIG
local capability = "1+2"
local controlProfile = "land"
local bindingMode = "controller_avatar"
local avatarResourcePath = "ModuleAnim/Animals/Zebra/FBX/SK_Zebra"
local controllerResourcePath = "ModuleAnim/Animals/Zebra/Zebra_Controller_Param"
local scriptFilePath = "resources/skeleton/data/Zebra_Controller_Param_Embedded.lua"
-- Internal ground-calibration inputs passed to ms-rig-grounding.lua.
local groundProbeDistance = 10
local groundProbeUpDistance = 5
local groundContactOffset = 0
-- END TEMPLATE CONFIG


local hostRuntime = {
    animator = nil,
    rb = nil,
    adapterDefaultMoveMode = "idle",
    adapterHasMountedGlue = false,
    adapterHasNeutralIdleGlue = false,
    adapterIdentifier = nil,
    adapterProfileSupported = true,
    adapterSupportedControlProfiles = nil,
    capability = nil,
    controlProfile = controlProfile,
    bindingMode = nil,
    avatarResourcePath = nil,
    controllerResourcePath = nil,
    scriptFilePath = nil,
    defaultMoveSpeed = nil,
    defaultRunSpeed = nil,
    turnSpeed = nil,
    ascendSpeed = nil,
    descendSpeed = nil,
    groundProbeDistance = groundProbeDistance,
    groundProbeUpDistance = groundProbeUpDistance,
    groundContactOffset = groundContactOffset,
    isMounted = false,
    mountedRider = nil,
    mountedMoveMode = "idle",
    mountedForwardIntent = 0,
    mountedTurnIntent = 0,
    mountedJumpIntent = false,
    mountedVerticalIntent = 0,
    grounded = false,
    groundOffset = nil,
    lastGroundHeight = nil,
    lastGroundNormal = nil,
    lastGroundedPosition = nil,
    lastGroundWarnTime = -1000.0,
    hasStarted = false,
    hasResolvedGroundOnce = false,
    pelvisNode = nil,
    headNode = nil,
    restAnatomicalForward = nil,
    restRootForward = nil,
    hasFacingMismatch = false,
    facingOffsetDegrees = 0.0,
    facingForward = nil,
    visualStateKey = nil,
    mountedBaseHeight = nil,
    mountedGroundClearance = nil,
    mountedAirborne = false,
    mountedTakeoffPlayed = false,
    horseJumpActive = false,
    horseJumpVelocity = 0
}

local function loadTypedResource(path, resourceType)
    if path == nil or path == "" or resourceType == nil then
        return nil
    end
    local ok, resource =
        pcall(
        function()
            return UnityEngine.Resources.Load(path, resourceType)
        end
    )
    if ok then
        return resource
    end
    motionLogger:warn("resource load failed", path, "error=" .. tostring(resource))
    return nil
end

local function abs(value)
    if value < 0 then
        return -value
    end
    return value
end

local function resolveAdapter()
    if type(generatedControllerAdapter) == "table" then
        return generatedControllerAdapter
    end
    if runtimeScope == nil then
        motionLogger:warnOnce("adapter-scope-unavailable", "controller adapter scope unavailable", runtimeScopeReason)
        return nil
    end
    if adapterPeer == nil then
        adapterPeer = runtimeScope:GetScript("ms-rig-adapter.lua")
    end
    if adapterPeer == nil or type(adapterPeer.GetRigControllerAdapter) ~= "function" then
        motionLogger:warnOnce("adapter-script-unavailable", "controller adapter script unavailable")
        return nil
    end
    local ok, adapter = pcall(adapterPeer.GetRigControllerAdapter)
    if not ok then
        motionLogger:warnOnce("adapter-contract-unavailable", "controller adapter contract unavailable")
        return nil
    end
    if adapter == nil then
        return nil
    end
    if type(adapter) ~= "table" then
        motionLogger:warnOnce("adapter-contract-invalid", "controller adapter contract must be a table")
        return nil
    end
    generatedControllerAdapter = adapter
    return generatedControllerAdapter
end

local function adapterHasMethod(methodName)
    local adapter = resolveAdapter()
    return adapter ~= nil and type(adapter[methodName]) == "function"
end

local function callAdapter(methodName, ...)
    local adapter = resolveAdapter()
    if adapter == nil then
        return nil
    end
    local fn = adapter[methodName]
    if type(fn) ~= "function" then
        return nil
    end
    local ok, result = pcall(fn, ...)
    if ok then
        return result
    end
    motionLogger:info("adapter call failed", methodName)
    return nil
end

local function syncHostFacts()
    hostRuntime.capability = capability
    hostRuntime.controlProfile = controlProfile
    hostRuntime.bindingMode = bindingMode
    hostRuntime.avatarResourcePath = avatarResourcePath
    hostRuntime.controllerResourcePath = controllerResourcePath
    hostRuntime.scriptFilePath = scriptFilePath
    hostRuntime.defaultMoveSpeed = defaultMoveSpeed
    hostRuntime.defaultRunSpeed = defaultRunSpeed
    hostRuntime.turnSpeed = turnSpeed
    hostRuntime.ascendSpeed = ascendSpeed
    hostRuntime.descendSpeed = descendSpeed
    hostRuntime.groundProbeDistance = groundProbeDistance
    hostRuntime.groundProbeUpDistance = groundProbeUpDistance
    hostRuntime.groundContactOffset = groundContactOffset
end

local function syncAdapterFacts()
    local adapter = resolveAdapter()
    if adapter == nil then
        hostRuntime.adapterIdentifier = nil
        hostRuntime.adapterDefaultMoveMode = "idle"
        hostRuntime.adapterHasMountedGlue = false
        hostRuntime.adapterHasNeutralIdleGlue = false
        hostRuntime.adapterProfileSupported = true
        hostRuntime.adapterSupportedControlProfiles = nil
        return
    end

    hostRuntime.adapterIdentifier = adapter.IDENTIFIER or adapter.CONTROLLER_NAME or adapter.controllerName or "unknown"
    hostRuntime.adapterDefaultMoveMode = adapter.DEFAULT_MOVE_MODE or "idle"
    hostRuntime.adapterHasMountedGlue = adapterHasMethod("OnMountedInput") or adapterHasMethod("ApplyMountedLocomotion")
    hostRuntime.adapterHasNeutralIdleGlue =
        adapterHasMethod("ApplyNeutralIdleDefaults") or adapterHasMethod("ApplyDefaults")
    hostRuntime.adapterSupportedControlProfiles = adapter.SUPPORTED_CONTROL_PROFILES
    hostRuntime.adapterProfileSupported =
        type(adapter.SUPPORTED_CONTROL_PROFILES) ~= "table" or
        table.concat(adapter.SUPPORTED_CONTROL_PROFILES, ","):find(controlProfile, 1, true) ~= nil

    if not hostRuntime.adapterProfileSupported then
        motionLogger:warnOnce(
            "adapter-profile-unsupported",
            "adapter " ..
                tostring(hostRuntime.adapterIdentifier) ..
                    " does not declare support for controlProfile=" .. tostring(controlProfile)
        )
    end

    motionLogger:info(
        "adapter facts: identifier=" ..
            tostring(hostRuntime.adapterIdentifier) ..
                ", defaultMoveMode=" ..
                    tostring(hostRuntime.adapterDefaultMoveMode) .. ", profile=" .. tostring(controlProfile)
    )
end

local function resolveMountedIdleMode()
    local adapterMode = hostRuntime.adapterDefaultMoveMode
    if adapterMode ~= nil and adapterMode ~= "" then
        return tostring(adapterMode)
    end
    return "idle"
end

local function clearMountedIntents()
    hostRuntime.mountedMoveMode = resolveMountedIdleMode()
    hostRuntime.mountedForwardIntent = 0
    hostRuntime.mountedTurnIntent = 0
    hostRuntime.mountedJumpIntent = false
    hostRuntime.mountedVerticalIntent = 0
end

local function resolveRootGameObject()
    if hostRuntime.rootGameObject ~= nil then
        return hostRuntime.rootGameObject
    end
    if self == nil or self.gameObject == nil or self.gameObject.transform == nil then
        return nil
    end

    hostRuntime.rootGameObject = self.gameObject
    return hostRuntime.rootGameObject
end

local function applyBindingFacts()
    local rootGameObject = resolveRootGameObject()
    if rootGameObject == nil then
        motionLogger:warnOnce("root-gameobject-missing", "Root GameObject is missing; animator binding skipped.")
        return
    end

    hostRuntime.animator = rootGameObject:GetComponentInChildren(typeof(UnityEngine.Animator))
    if hostRuntime.animator == nil then
        hostRuntime.animator = rootGameObject:AddComponent(typeof(UnityEngine.Animator))
        motionLogger:warn("Animator component was missing on root GameObject and has been added automatically by host binding.")
    end

    hostRuntime.animator.cullingMode = UnityEngine.AnimatorCullingMode.CullUpdateTransforms
    hostRuntime.animator.applyRootMotion = false

    local hasAvatar = hostRuntime.animator.avatar ~= nil
    local hasController = hostRuntime.animator.runtimeAnimatorController ~= nil

    if bindingMode == "controller_avatar" and hasAvatar and hasController then
        return
    end

    if bindingMode == "avatar_only" and hasAvatar then
        return
    end

    if bindingMode == "controller_avatar" then
        if not hasAvatar then
            local avatar = loadTypedResource(avatarResourcePath, typeof(UnityEngine.Avatar))
            if avatar ~= nil then
                hostRuntime.animator.avatar = avatar
            end
        end
        if not hasController then
            local controller = loadTypedResource(controllerResourcePath, typeof(UnityEngine.RuntimeAnimatorController))
            if controller ~= nil then
                hostRuntime.animator.runtimeAnimatorController = controller
            end
        end
        return
    end

    if bindingMode == "avatar_only" then
        if not hasAvatar then
            local avatar = loadTypedResource(avatarResourcePath, typeof(UnityEngine.Avatar))
            if avatar ~= nil then
                hostRuntime.animator.avatar = avatar
            end
        end
    end
end

local groundPeer = nil

local function resolveGroundPeer()
    if groundPeer ~= nil then
        return groundPeer
    end
    if runtimeScope == nil then
        motionLogger:warnOnce("grounding-scope-unavailable", "rig grounding scope unavailable", runtimeScopeReason)
        return nil
    end
    local peer, reason = runtimeScope:GetScript("ms-rig-grounding.lua")
    if
        peer == nil or type(peer.EnforceRigRigidbodySettings) ~= "function" or
            type(peer.EnsureRigFacingCalibration) ~= "function" or
            type(peer.GetRigHorizontalForward) ~= "function" or
            type(peer.RotateRigHorizontal) ~= "function" or
            type(peer.ResolveRigGroundedPose) ~= "function" or
            type(peer.ApplyRigGroundAlignedRotation) ~= "function" or
            type(peer.RefreshRigMountedGrounding) ~= "function" or
            type(peer.RefreshRigUnmountedGrounding) ~= "function" or
            type(peer.ClearRigGroundingState) ~= "function" or
            type(peer.ClampRigAirborneDescent) ~= "function"
     then
        motionLogger:warnOnce("grounding-script-unavailable", "rig grounding script unavailable", reason)
        return nil
    end
    groundPeer = peer
    return groundPeer
end

local function callGround(methodName, ...)
    local peer = resolveGroundPeer()
    if peer == nil then
        return nil
    end
    local method = peer[methodName]
    if type(method) ~= "function" then
        return nil
    end
    return method(hostRuntime, ...)
end

local function getHorizontalForward(root)
    return callGround("GetRigHorizontalForward", root) or Vector3.forward
end

local function rotateHorizontal(vector, yawDegrees)
    return callGround("RotateRigHorizontal", vector, yawDegrees) or vector
end

local function ensureFacingCalibration(root, forceRefresh)
    return callGround("EnsureRigFacingCalibration", root, forceRefresh)
end

local function enforceMountedRigidBodySettings()
    return callGround("EnforceRigRigidbodySettings")
end

local function resolveGroundedPose(root, candidatePosition, deltaTime, forceResetOffset, immediateSnap, shouldWarnOnMiss)
    local peer = resolveGroundPeer()
    if peer == nil then
        return candidatePosition, nil
    end
    return peer.ResolveRigGroundedPose(
        hostRuntime,
        root,
        candidatePosition,
        deltaTime,
        forceResetOffset,
        immediateSnap,
        shouldWarnOnMiss
    )
end

local function applyGroundAlignedRotation(root, targetNormal, deltaTime)
    return callGround("ApplyRigGroundAlignedRotation", root, targetNormal, deltaTime)
end

local function refreshMountedGroundingInternal(forceResetOffset)
    return callGround("RefreshRigMountedGrounding", forceResetOffset) == true
end

local function refreshUnmountedGroundingInternal(deltaTime)
    return callGround("RefreshRigUnmountedGrounding", deltaTime) == true
end

local function clearGroundingState()
    callGround("ClearRigGroundingState")
end

local function resolveForwardIntent()
    if math.abs(hostRuntime.mountedForwardIntent) > 0.0001 then
        return hostRuntime.mountedForwardIntent
    end

    if hostRuntime.mountedMoveMode == "run" or hostRuntime.mountedMoveMode == "walk" then
        return 1
    end
    if hostRuntime.mountedMoveMode == "back" or hostRuntime.mountedMoveMode == "reverse" then
        return -1
    end
    return 0
end

local function tryAdapterMethodList(methodNames, ...)
    if type(methodNames) ~= "table" then
        return nil
    end
    for i = 1, #methodNames do
        local methodName = methodNames[i]
        if adapterHasMethod(methodName) then
            local result = callAdapter(methodName, ...)
            if result ~= nil then
                return result
            end
        end
    end
    return nil
end

local function adapterCallSucceeded(result)
    return result ~= nil and result ~= false
end

local function appendStateCandidate(candidates, stateName)
    if type(stateName) ~= "string" or stateName == "" then
        return
    end
    for i = 1, #candidates do
        if candidates[i] == stateName then
            return
        end
    end
    candidates[#candidates + 1] = stateName
end

local function appendSnapshotStateGroupCandidates(candidates, snapshot, groupName)
    if type(snapshot) ~= "table" or type(snapshot.stateGroups) ~= "table" then
        return
    end
    local group = snapshot.stateGroups[groupName]
    if type(group) ~= "table" then
        return
    end
    for i = 1, #group do
        appendStateCandidate(candidates, group[i])
    end
end

local function resetAdapterTriggerMethods(triggerNames)
    if type(triggerNames) ~= "table" then
        return false
    end

    local didReset = false
    for i = 1, #triggerNames do
        local triggerName = triggerNames[i]
        if type(triggerName) == "string" and triggerName ~= "" then
            local methodName = "Reset" .. triggerName
            if adapterHasMethod(methodName) then
                local result = callAdapter(methodName, self, hostRuntime)
                if result ~= nil then
                    didReset = true
                end
            end
        end
    end
    return didReset
end

local function resetNeutralIdleTriggers()
    local adapter = resolveAdapter()
    if adapter ~= nil then
        resetAdapterTriggerMethods(adapter.TRIGGER_PARAMS)
        resetAdapterTriggerMethods(adapter.NEUTRAL_IDLE_RESET_TRIGGERS)
    end

    tryAdapterMethodList(
        {
            "ResetTriggerDeath",
            "ResetTriggerDeathGrounded",
            "ResetTriggerDeathHitTheGround",
            "ResetTriggerDeathGoToFall",
            "ResetTriggerRevive",
            "ResetTriggerGetHit",
            "ResetTriggerGetHitFront",
            "ResetTriggerGetHitLeft",
            "ResetTriggerGetHitRight",
            "ResetTriggerGlide",
            "ResetTriggerTakeOffGrounded",
            "ResetTriggerTakeOffBranch",
            "ResetTriggerLandingGrounded",
            "ResetTriggerLandingBranch"
        },
        self,
        hostRuntime
    )
end

local function tryCrossFadeAdapterStates(stateNames, visualStateKey)
    if hostRuntime.visualStateKey == visualStateKey then
        return true
    end
    if type(stateNames) ~= "table" then
        return false
    end
    for i = 1, #stateNames do
        local stateName = stateNames[i]
        if type(stateName) == "string" and stateName ~= "" then
            local ok = callAdapter("CrossFadeState", self, hostRuntime, stateName, 0.15, 0)
            if ok == true then
                hostRuntime.visualStateKey = visualStateKey
                return true
            end
        end
    end
    return false
end

local function tryCrossFadeAdapterSnapshotIdleState(visualStateKey)
    local snapshot = callAdapter("GetAnimatorSnapshot", hostRuntime)
    local candidates = {}

    appendSnapshotStateGroupCandidates(candidates, snapshot, "idle")
    appendSnapshotStateGroupCandidates(candidates, snapshot, "grounded_idle")
    appendSnapshotStateGroupCandidates(candidates, snapshot, "groundedIdle")
    appendSnapshotStateGroupCandidates(candidates, snapshot, "neutralIdle")

    if #candidates == 0 then
        return false
    end

    return tryCrossFadeAdapterStates(candidates, visualStateKey)
end

local function applyGroundedIdleVisualState()
    if hostRuntime.visualStateKey == "grounded_idle" then
        return true
    end

    resetNeutralIdleTriggers()

    if tryCrossFadeAdapterSnapshotIdleState("grounded_idle") then
        return true
    end

    local idlePulseResult =
        tryAdapterMethodList(
        {
            "PulseTriggerIdleLookAroundGrounded",
            "PulseTriggerIdleStretchWingsGrounded",
            "PulseTriggerIdleLookStretchLegsGrounded",
            "PulseTriggerIdleStareBranch",
            "PulseTriggerIdleLookAroundBranch",
            "PulseTriggerIdleStretchWingsBranch",
            "PulseTriggeridleFlapWings"
        },
        self,
        hostRuntime
    )
    if idlePulseResult ~= nil then
        hostRuntime.visualStateKey = "grounded_idle"
        return true
    end

    return tryCrossFadeAdapterStates(
        {
            "IdleStareGrounded",
            "IdleLookAroundGrounded",
            "IdleStretchWingsGrounded",
            "IdleStareBranch",
            "IdleLookAroundBranch",
            "IdleStretchWingsBranch"
        },
        "grounded_idle"
    )
end

local function applyMountedFlightVisualState(airborneTransition)
    if airborneTransition and not hostRuntime.mountedTakeoffPlayed then
        tryAdapterMethodList(
            {
                "PulseTriggerTakeOffGrounded",
                "PulseTriggerTakeOffBranch"
            },
            self,
            hostRuntime
        )
        hostRuntime.mountedTakeoffPlayed = true
    end

    local flightPulseResult =
        tryAdapterMethodList(
        {
            "PulseTriggerGlide"
        },
        self,
        hostRuntime
    )
    if flightPulseResult ~= nil then
        hostRuntime.visualStateKey = "mounted_flight"
        return
    end

    tryCrossFadeAdapterStates(
        {
            "Fly",
            "Glide"
        },
        "mounted_flight"
    )
end

local function applyNeutralIdleDefaults()
    if not hostRuntime.adapterHasNeutralIdleGlue and resolveAdapter() ~= nil then
        motionLogger:warnOnce(
            "adapter-neutral-idle-missing",
            "adapter is missing neutral idle glue; host keeps fallback idle state"
        )
    end
    local adapterIdleApplied = callAdapter("ApplyNeutralIdleDefaults", self, hostRuntime)
    if adapterCallSucceeded(adapterIdleApplied) then
        if applyGroundedIdleVisualState() ~= true then
            hostRuntime.visualStateKey = "grounded_idle"
        end
        return true
    end

    local adapterDefaultsApplied = callAdapter("ApplyDefaults", self, hostRuntime)
    if adapterCallSucceeded(adapterDefaultsApplied) then
        if applyGroundedIdleVisualState() ~= true then
            hostRuntime.visualStateKey = "grounded_idle"
        end
        return true
    end

    return applyGroundedIdleVisualState()
end

local function ensureNeutralIdleBootstrap()
    if hostRuntime.isMounted or hostRuntime.visualStateKey == "grounded_idle" then
        return
    end
    applyBindingFacts()
    applyNeutralIdleDefaults()
end

local function updateMountedMotion(dt)
    if not hostRuntime.isMounted then
        return
    end
    if not hostRuntime.adapterHasMountedGlue and resolveAdapter() ~= nil then
        motionLogger:warnOnce(
            "adapter-mounted-glue-missing",
            "adapter is missing mounted locomotion glue; mounted motion will stay host-minimal"
        )
    end

    local forwardIntent = resolveForwardIntent()
    local result =
        callAdapter(
        "OnMountedInput",
        self,
        hostRuntime,
        hostRuntime.mountedMoveMode,
        hostRuntime.mountedTurnIntent,
        forwardIntent,
        hostRuntime.mountedJumpIntent,
        hostRuntime.mountedVerticalIntent
    )

    if result == nil then
        result =
            callAdapter(
            "ApplyMountedLocomotion",
            self,
            hostRuntime,
            hostRuntime.mountedMoveMode,
            hostRuntime.mountedTurnIntent,
            forwardIntent,
            hostRuntime.mountedJumpIntent,
            hostRuntime.mountedVerticalIntent
        )
    end

    if result == nil and controlProfile ~= "land" then
        if controlProfile == "fish" then
            motionLogger:warnOnce(
                "fish-fallback",
                "fish profile is retaining fish semantics while reusing flying-style mounted locomotion glue"
            )
        end
        -- `flying` / `fish` vertical intent is still retained on the host even when
        -- the current adapter only consumes move/turn/forward.
        callAdapter(
            "ApplyMountedLocomotion",
            self,
            hostRuntime,
            hostRuntime.mountedMoveMode,
            hostRuntime.mountedTurnIntent,
            forwardIntent
        )
    end

    local currentTransform = self and self.transform or nil
    if currentTransform ~= nil and dt ~= nil and dt > 0 then
        ensureFacingCalibration(currentTransform, false)
        local turnValue = tonumber(hostRuntime.mountedTurnIntent) or 0
        local yawDelta = turnValue * (hostRuntime.turnSpeed or turnSpeed or 0) * dt
        if math.abs(yawDelta) > 0.0001 then
            local euler = currentTransform.eulerAngles
            currentTransform.rotation = Quaternion.Euler(euler.x, euler.y + yawDelta, euler.z)
            hostRuntime.facingForward =
                rotateHorizontal(hostRuntime.facingForward or getHorizontalForward(currentTransform), yawDelta)
        end

        local forwardValue = resolveForwardIntent()
        if controlProfile == "land" then
            enforceMountedRigidBodySettings()

            local moveSpeed = hostRuntime.defaultMoveSpeed or defaultMoveSpeed
            if hostRuntime.mountedMoveMode == "run" then
                moveSpeed = hostRuntime.defaultRunSpeed or defaultRunSpeed
            end
            if forwardValue < 0 then
                moveSpeed = moveSpeed * 0.6
            end

            local forwardDistance = forwardValue * moveSpeed * dt
            local currentPosition = currentTransform.position
            local horizontalForward = hostRuntime.facingForward or getHorizontalForward(currentTransform)
            local candidatePosition =
                Vector3(
                currentPosition.x + horizontalForward.x * forwardDistance,
                currentPosition.y,
                currentPosition.z + horizontalForward.z * forwardDistance
            )
            local shouldWarnOnMiss =
                math.abs(forwardDistance) > 0.0001 or math.abs(turnValue) > 0.0001 or hostRuntime.mountedJumpIntent
            local groundedPosition, groundHit =
                resolveGroundedPose(currentTransform, candidatePosition, dt, false, false, shouldWarnOnMiss)
            if hostRuntime.horseJumpActive then
                -- Horse jump arc: keep the horizontal move, replace the grounded Y with
                -- a gravity-driven arc until the hooves reach the sampled ground again.
                local jumpVelocity = (hostRuntime.horseJumpVelocity or 0) - 9.8 * dt
                local nextY = currentPosition.y + jumpVelocity * dt
                if nextY > groundedPosition.y + 0.02 then
                    hostRuntime.horseJumpVelocity = jumpVelocity
                    currentTransform.position = Vector3(groundedPosition.x, nextY, groundedPosition.z)
                else
                    currentTransform.position = Vector3(groundedPosition.x, groundedPosition.y, groundedPosition.z)
                    hostRuntime.horseJumpActive = false
                    hostRuntime.horseJumpVelocity = 0
                    refreshMountedGroundingInternal(true)
                    if groundHit ~= nil then
                        applyGroundAlignedRotation(currentTransform, groundHit.normal, dt)
                    end
                end
            else
                currentTransform.position = groundedPosition
                if groundHit ~= nil then
                    applyGroundAlignedRotation(currentTransform, groundHit.normal, dt)
                end
            end
        elseif controlProfile == "flying" or controlProfile == "fish" then
            local verticalDistance = 0
            local verticalIntent = tonumber(hostRuntime.mountedVerticalIntent) or 0
            if verticalIntent > 0 then
                verticalDistance = (hostRuntime.ascendSpeed or ascendSpeed) * math.min(verticalIntent, 1) * dt
            elseif verticalIntent < 0 then
                verticalDistance =
                    -(hostRuntime.descendSpeed or descendSpeed) * math.min(math.abs(verticalIntent), 1) * dt
            end

            local moveSpeed = hostRuntime.defaultMoveSpeed or defaultMoveSpeed
            local forwardDistance = forwardValue * moveSpeed * dt
            local descentBlockedByGround = false
            if math.abs(forwardDistance) > 0.0001 or math.abs(verticalDistance) > 0.0001 then
                local currentPosition = currentTransform.position
                local forward = currentTransform.forward
                local up = currentTransform.up
                local candidatePosition =
                    Vector3(
                    currentPosition.x + forward.x * forwardDistance + up.x * verticalDistance,
                    currentPosition.y + forward.y * forwardDistance + up.y * verticalDistance,
                    currentPosition.z + forward.z * forwardDistance + up.z * verticalDistance
                )
                candidatePosition, descentBlockedByGround =
                    clampMountedAirborneDescent(currentTransform, currentPosition, candidatePosition, verticalIntent)
                currentTransform.position = candidatePosition
            end

            local currentHeight = currentTransform.position.y
            local baseHeight = hostRuntime.mountedBaseHeight
            if baseHeight == nil then
                baseHeight = currentHeight
                hostRuntime.mountedBaseHeight = currentHeight
            end
            local effectiveVerticalIntent = verticalIntent
            if descentBlockedByGround and effectiveVerticalIntent < 0 then
                effectiveVerticalIntent = 0
            end
            local airborneNow =
                math.abs(effectiveVerticalIntent) > 0.08 or currentHeight > baseHeight + 0.18 or
                (hostRuntime.mountedAirborne and currentHeight > baseHeight + 0.05)
            if airborneNow then
                applyMountedFlightVisualState(not hostRuntime.mountedAirborne)
            elseif hostRuntime.mountedAirborne then
                tryAdapterMethodList(
                    {
                        "PulseTriggerLandingGrounded",
                        "PulseTriggerLandingBranch"
                    },
                    self,
                    hostRuntime
                )
                hostRuntime.visualStateKey = nil
                hostRuntime.mountedTakeoffPlayed = false
                applyGroundedIdleVisualState()
            end
            hostRuntime.mountedAirborne = airborneNow
        end
    end

    hostRuntime.mountedJumpIntent = false
end

local function updateAutonomousMotion(dt)
    if not hostRuntime.isMounted and controlProfile == "land" then
        refreshUnmountedGroundingInternal(dt)
    end
    if capability == "2" then
        ensureNeutralIdleBootstrap()
        return
    end
    if not hostRuntime.isMounted then
        ensureNeutralIdleBootstrap()
    end
    -- Workspace-specific autonomous branches may be appended later.
end

function GetRigControlProfile()
    return controlProfile
end

function SetMountedRider(actorOrNil)
    hostRuntime.mountedRider = actorOrNil
    hostRuntime.isMounted = actorOrNil ~= nil
    hostRuntime.visualStateKey = nil
    if hostRuntime.isMounted then
        hostRuntime.mountedMoveMode = resolveMountedIdleMode()
        hostRuntime.mountedForwardIntent = 0
        hostRuntime.mountedBaseHeight = self ~= nil and self.transform ~= nil and self.transform.position.y or nil
        hostRuntime.mountedAirborne = false
        hostRuntime.mountedTakeoffPlayed = false
        ensureFacingCalibration(self and self.transform or nil, true)
    else
        clearMountedIntents()
        clearGroundingState()
        hostRuntime.horseJumpActive = false
        hostRuntime.horseJumpVelocity = 0
        hostRuntime.mountedBaseHeight = nil
        hostRuntime.mountedGroundClearance = nil
        hostRuntime.mountedAirborne = false
        hostRuntime.mountedTakeoffPlayed = false
        applyNeutralIdleDefaults()
    end
    callAdapter("OnMountedStateChanged", self, hostRuntime, hostRuntime.isMounted, actorOrNil)
    if hostRuntime.isMounted then
        refreshMountedGroundingInternal(true)
    end
end

function ClearMountedRider()
    SetMountedRider(nil)
end

function SetMountedMoveIntent(forwardIntent, strafeIntent)
    hostRuntime.mountedForwardIntent = tonumber(forwardIntent) or 0
    if math.abs(hostRuntime.mountedForwardIntent) < 0.08 then
        hostRuntime.mountedMoveMode = "idle"
    elseif hostRuntime.mountedForwardIntent > 0.75 then
        hostRuntime.mountedMoveMode = "run"
    elseif hostRuntime.mountedForwardIntent > 0 then
        hostRuntime.mountedMoveMode = "walk"
    elseif hostRuntime.mountedForwardIntent < 0 then
        hostRuntime.mountedMoveMode = "back"
    end
end

function SetMountedMoveMode(mode)
    if mode == nil or mode == "" then
        hostRuntime.mountedMoveMode = resolveMountedIdleMode()
        return
    end
    hostRuntime.mountedMoveMode = tostring(mode)
end

function SetMountedTurnIntent(turnValue)
    hostRuntime.mountedTurnIntent = tonumber(turnValue) or 0
end

function SetMountedJumpIntent(isPressedOrPulse)
    hostRuntime.mountedJumpIntent = isPressedOrPulse == true
    if
        hostRuntime.mountedJumpIntent and hostRuntime.isMounted and controlProfile == "land" and
            not hostRuntime.horseJumpActive
     then
        hostRuntime.horseJumpActive = true
        hostRuntime.horseJumpVelocity = 3.8
    end
end

function SetMountedVerticalIntent(intentValue)
    hostRuntime.mountedVerticalIntent = tonumber(intentValue) or 0
end

function RefreshMountedGrounding(forceResetOffset)
    return refreshMountedGroundingInternal(forceResetOffset == true)
end

function ClearMountedGroundingState()
    clearGroundingState()
end

function GetMountedRuntimeSnapshot()
    local adapterSnapshot = callAdapter("GetAnimatorSnapshot", hostRuntime)
    return {
        adapterDefaultMoveMode = hostRuntime.adapterDefaultMoveMode,
        adapterHasMountedGlue = hostRuntime.adapterHasMountedGlue,
        adapterHasNeutralIdleGlue = hostRuntime.adapterHasNeutralIdleGlue,
        adapterIdentifier = hostRuntime.adapterIdentifier,
        adapterProfileSupported = hostRuntime.adapterProfileSupported,
        adapterSupportedControlProfiles = hostRuntime.adapterSupportedControlProfiles,
        capability = hostRuntime.capability,
        controlProfile = hostRuntime.controlProfile,
        isMounted = hostRuntime.isMounted,
        mountedMoveMode = hostRuntime.mountedMoveMode,
        mountedForwardIntent = hostRuntime.mountedForwardIntent,
        mountedTurnIntent = hostRuntime.mountedTurnIntent,
        mountedJumpIntent = hostRuntime.mountedJumpIntent,
        mountedVerticalIntent = hostRuntime.mountedVerticalIntent,
        adapterSnapshot = adapterSnapshot
    }
end

function Start()
    syncHostFacts()
    syncAdapterFacts()
    hostRuntime.rb = self.gameObject:GetComponent(typeof(UnityEngine.Rigidbody))
    enforceMountedRigidBodySettings()
    applyBindingFacts()
    if scriptFilePath ~= nil and scriptFilePath ~= "" then
        motionLogger:info("scriptFile facts available", scriptFilePath)
    end
    callAdapter("BindHost", self, hostRuntime)
    callAdapter("OnHostStart", self, hostRuntime)
    if resolveAdapter() ~= nil then
        applyNeutralIdleDefaults()
    end
    ensureFacingCalibration(self and self.transform or nil, true)
    hostRuntime.hasStarted = true
    if controlProfile == "land" then
        refreshMountedGroundingInternal(true)
    end
end

function Update()
    local dt = Time.deltaTime
    enforceMountedRigidBodySettings()
    updateAutonomousMotion(dt)
    updateMountedMotion(dt)
    if not hostRuntime.isMounted then
        clearMountedIntents()
    end
    -- Match the walk-cycle playback to the faster mounted run speed so the
    -- alternating hooves do not visibly slide over the ground.
    if hostRuntime.animator ~= nil then
        local runActive =
            hostRuntime.isMounted and hostRuntime.mountedMoveMode == "run" and resolveForwardIntent() > 0.1
        hostRuntime.animator.speed = runActive and 1.7 or 1.0
    end
end

function OnDisable()
    clearMountedIntents()
    callAdapter("OnHostStop", self, hostRuntime)
end

function OnDestroy()
    clearMountedIntents()
    callAdapter("OnHostStop", self, hostRuntime)
end

-- Workspace-specific extra logic may be appended below by the generating agent.
