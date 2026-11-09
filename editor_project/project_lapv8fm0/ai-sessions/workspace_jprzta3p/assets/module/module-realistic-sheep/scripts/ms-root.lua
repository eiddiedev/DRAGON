-- RIG_RUNTIME_CONTRACT_JSON: {"schemaVersion":2,"rigFamily":"creature","capability":"1","controlProfile":"land","files":["ms-root.lua","ms-rig-grounding.lua","ms-rig-adapter.lua"]}
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
local capability = "1"
local controlProfile = "land"
local bindingMode = "controller_avatar"
local avatarResourcePath = "ModuleAnim/Animals/Sheep/FBX/SK_Sheep"
local controllerResourcePath = "ModuleAnim/Animals/Sheep/Sheep_Controller_Param"
local scriptFilePath = "resources/skeleton/data/Sheep_Controller_Param_Embedded.lua"
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
    mountedTakeoffPlayed = false
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
            currentTransform.position = groundedPosition
            if groundHit ~= nil then
                applyGroundAlignedRotation(currentTransform, groundHit.normal, dt)
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

-- BEGIN WORKSPACE SHEEP ROAMING
-- Ambient sheep behaviour: slow wandering, grazing pauses and stepping away from nearby players.
-- The animator supplies leg, body and head motion; this block only steers the root and picks states.
-- Hamlet exposes service objects as script globals; keep a guarded CS lookup for older runtimes.
local DouyinActorService = DouyinActorService
if DouyinActorService == nil then
    local serviceOk, service = pcall(
        function()
            return CS.DouyinActorService
        end
    )
    if serviceOk then
        DouyinActorService = service
    end
end

local SHEEP_WALK_SPEED = 0.65
local SHEEP_FLEE_SPEED = 1.35
local SHEEP_TURN_SPEED = 70
local SHEEP_FLEE_TURN_SPEED = 110
local SHEEP_NOTICE_RADIUS = 2.2
local SHEEP_CALM_RADIUS = 5.5
local SHEEP_WANDER_RADIUS = 4.5
local SHEEP_ARRIVE_DISTANCE = 0.4
local EAR_PIVOT_LEFT_PATH =
    "rig/SK_Sheep/root/SHEEP_/SHEEP_ Pelvis/SHEEP_ Spine/SHEEP_ Spine1/SHEEP_ Neck/SHEEP_ Neck1/SHEEP_ Neck2/SHEEP_ Head/EarPivot_L"
local EAR_PIVOT_RIGHT_PATH =
    "rig/SK_Sheep/root/SHEEP_/SHEEP_ Pelvis/SHEEP_ Spine/SHEEP_ Spine1/SHEEP_ Neck/SHEEP_ Neck1/SHEEP_ Neck2/SHEEP_ Head/EarPivot_R"
local TAIL_PIVOT_PATH = "rig/SK_Sheep/root/SHEEP_/SHEEP_ Pelvis/SHEEP_ Tail/SHEEP_ Tail1/SHEEP_ Tail2/TailPivot"

local sheep = {
    ready = false,
    mode = "idle",
    moveMode = nil,
    modeTimer = 0,
    idleActionTimer = 0,
    walkTimer = 0,
    fleeTimer = 0,
    noticeTimer = 0,
    ownershipTimer = 0,
    isOwner = true,
    home = nil,
    walkTarget = nil,
    threatActor = nil,
    threatDistance = nil,
    swayTime = 0,
    earLeft = nil,
    earRight = nil,
    tailPivot = nil,
    earLeftEuler = nil,
    earRightEuler = nil,
    tailEuler = nil,
    warnedSwayNodes = false,
    lastObservedPosition = nil,
}

local function sheepRandom(minValue, maxValue)
    return minValue + math.random() * (maxValue - minValue)
end

-- atan2 kept explicit so the script does not depend on a two-argument math.atan.
local function sheepAtan2(y, x)
    if x > 0 then
        return math.atan(y / x)
    end
    if x < 0 then
        if y >= 0 then
            return math.atan(y / x) + math.pi
        end
        return math.atan(y / x) - math.pi
    end
    if y > 0 then
        return math.pi * 0.5
    end
    if y < 0 then
        return -math.pi * 0.5
    end
    return 0
end

local function sheepSignedYawDegrees(fromVec, toVec)
    local fromLength = math.sqrt(fromVec.x * fromVec.x + fromVec.z * fromVec.z)
    local toLength = math.sqrt(toVec.x * toVec.x + toVec.z * toVec.z)
    if fromLength < 0.0001 or toLength < 0.0001 then
        return 0
    end
    local fromX = fromVec.x / fromLength
    local fromZ = fromVec.z / fromLength
    local toX = toVec.x / toLength
    local toZ = toVec.z / toLength
    local cross = fromX * toZ - fromZ * toX
    local dot = fromX * toX + fromZ * toZ
    dot = math.max(-1, math.min(1, dot))
    return math.deg(sheepAtan2(cross, dot))
end

local function sheepApplyMoveMode(mode)
    if sheep.moveMode == mode then
        return
    end
    sheep.moveMode = mode
    if mode == "idle" then
        applyNeutralIdleDefaults()
    else
        callAdapter("SetMoveMode", self, hostRuntime, mode)
    end
end

local function sheepFindNode(relativePath)
    if runtimeScope == nil then
        return nil
    end
    return runtimeScope:GetTransformByPath(relativePath)
end

local function sheepBindSwayNodes()
    sheep.earLeft = sheepFindNode(EAR_PIVOT_LEFT_PATH)
    sheep.earRight = sheepFindNode(EAR_PIVOT_RIGHT_PATH)
    sheep.tailPivot = sheepFindNode(TAIL_PIVOT_PATH)
    if sheep.earLeft ~= nil then
        sheep.earLeftEuler = sheep.earLeft.localEulerAngles
    end
    if sheep.earRight ~= nil then
        sheep.earRightEuler = sheep.earRight.localEulerAngles
    end
    if sheep.tailPivot ~= nil then
        sheep.tailEuler = sheep.tailPivot.localEulerAngles
    end
    if sheep.earLeft == nil and sheep.earRight == nil and sheep.tailPivot == nil and not sheep.warnedSwayNodes then
        sheep.warnedSwayNodes = true
        motionLogger:warnOnce("sheep-sway-nodes-missing", "sheep ear/tail pivots not found; sway animation skipped")
    end
end

local function sheepApplySway()
    local time = sheep.swayTime
    local earAngle = math.sin(time * 2.2) * 3.0
    if sheep.earLeft ~= nil and sheep.earLeftEuler ~= nil then
        local base = sheep.earLeftEuler
        sheep.earLeft.localEulerAngles = Vector3(base.x, base.y + earAngle, base.z)
    end
    if sheep.earRight ~= nil and sheep.earRightEuler ~= nil then
        local base = sheep.earRightEuler
        sheep.earRight.localEulerAngles = Vector3(base.x, base.y - earAngle, base.z)
    end
    if sheep.tailPivot ~= nil and sheep.tailEuler ~= nil then
        local base = sheep.tailEuler
        sheep.tailPivot.localEulerAngles = Vector3(base.x, base.y + math.sin(time * 1.7 + 0.6) * 4.0, base.z)
    end
end

local function sheepCanDrive()
    local ok, owned = pcall(
        function()
            return self:HasOwnership()
        end
    )
    if not ok or owned == true then
        return true
    end
    local ownerOk, owner = pcall(
        function()
            return self:GetOwner()
        end
    )
    if ownerOk and owner == nil then
        return true
    end
    return false
end

local function sheepRefreshThreat(root)
    if DouyinActorService == nil then
        sheep.threatActor = nil
        sheep.threatDistance = nil
        return
    end
    local ok, actors = pcall(
        function()
            return DouyinActorService.GetActors()
        end
    )
    if not ok then
        sheep.threatActor = nil
        sheep.threatDistance = nil
        return
    end
    local count = 0
    if actors ~= nil then
        if actors.Length ~= nil then
            count = actors.Length
        else
            local lengthOk, length = pcall(
                function()
                    return #actors
                end
            )
            if lengthOk and length ~= nil then
                count = length
            end
        end
    end
    -- C# arrays are zero based; fall back to Lua indexing if the wrapper exposes 1-based access.
    local indexBase = 1
    if count > 0 then
        local zeroOk, zeroValue = pcall(
            function()
                return actors[0]
            end
        )
        if zeroOk and zeroValue ~= nil then
            indexBase = 0
        end
    end
    local nearestActor = nil
    local nearestDistance = nil
    local nearestX = nil
    local nearestZ = nil
    for offset = 0, count - 1 do
        local actor = actors[offset + indexBase]
        if actor ~= nil then
            if actor.isPet ~= true then
                local position = actor.position
                if position ~= nil then
                    local dx = position.x - root.position.x
                    local dz = position.z - root.position.z
                    local distance = math.sqrt(dx * dx + dz * dz)
                    if nearestDistance == nil or distance < nearestDistance then
                        nearestDistance = distance
                        nearestActor = actor
                        nearestX = position.x
                        nearestZ = position.z
                    end
                end
            end
        end
    end
    sheep.threatActor = nearestActor
    sheep.threatDistance = nearestDistance
    sheep.threatX = nearestX
    sheep.threatZ = nearestZ
end

local function sheepSteerTowards(root, direction, dt, turnSpeed)
    local forward = hostRuntime.facingForward or getHorizontalForward(root)
    local yaw = sheepSignedYawDegrees(forward, direction)
    local maxTurn = turnSpeed * dt
    if yaw > maxTurn then
        yaw = maxTurn
    elseif yaw < -maxTurn then
        yaw = -maxTurn
    end
    if math.abs(yaw) > 0.0001 then
        hostRuntime.facingForward = rotateHorizontal(forward, yaw)
    else
        hostRuntime.facingForward = forward
    end
end

local function sheepMoveForward(root, speed, dt)
    local forward = hostRuntime.facingForward or getHorizontalForward(root)
    local position = root.position
    root.position = Vector3(position.x + forward.x * speed * dt, position.y, position.z + forward.z * speed * dt)
end

local function sheepPulseIdleAction()
    local roll = math.random()
    if roll < 0.5 then
        callAdapter("PulseTriggerIdleGraze", self, hostRuntime)
    elseif roll < 0.75 then
        callAdapter("PulseTriggerIdleChew", self, hostRuntime)
    elseif roll < 0.92 then
        callAdapter("PulseTriggerIdleLookAround", self, hostRuntime)
    else
        callAdapter("PulseTriggerIdleBaaa", self, hostRuntime)
    end
end

local function sheepEnterIdle()
    sheep.mode = "idle"
    sheep.modeTimer = sheepRandom(4.0, 8.0)
    sheep.idleActionTimer = sheepRandom(0.5, 1.6)
    sheep.walkTarget = nil
    sheepApplyMoveMode("idle")
    callAdapter("PulseTriggerIdleGraze", self, hostRuntime)
end

local function sheepEnterWalk(root)
    local home = sheep.home or root.position
    local angle = math.random() * math.pi * 2
    local radius = sheepRandom(1.2, SHEEP_WANDER_RADIUS)
    sheep.walkTarget = Vector3(home.x + math.cos(angle) * radius, home.y, home.z + math.sin(angle) * radius)
    sheep.walkTimer = 0
    sheep.mode = "walk"
    sheepApplyMoveMode("walk")
end

local function sheepUpdateIdle(dt)
    sheepApplyMoveMode("idle")
    sheep.modeTimer = sheep.modeTimer - dt
    sheep.idleActionTimer = sheep.idleActionTimer - dt
    if sheep.idleActionTimer <= 0 then
        sheep.idleActionTimer = sheepRandom(2.2, 4.8)
        sheepPulseIdleAction()
    end
    if sheep.modeTimer <= 0 then
        local root = self and self.transform or nil
        if root ~= nil then
            sheepEnterWalk(root)
        end
    end
end

local function sheepUpdateWalk(root, dt)
    local target = sheep.walkTarget
    if target == nil then
        sheepEnterIdle()
        return
    end
    sheep.walkTimer = sheep.walkTimer + dt
    local dx = target.x - root.position.x
    local dz = target.z - root.position.z
    local distance = math.sqrt(dx * dx + dz * dz)
    if distance <= SHEEP_ARRIVE_DISTANCE or sheep.walkTimer >= 9.0 then
        sheepEnterIdle()
        return
    end
    local direction = Vector3(dx / distance, 0, dz / distance)
    sheepSteerTowards(root, direction, dt, SHEEP_TURN_SPEED)
    local speed = SHEEP_WALK_SPEED * math.max(0.25, math.min(1, distance / 1.2))
    sheepMoveForward(root, speed, dt)
end

local function sheepUpdateFlee(root, dt)
    sheep.fleeTimer = sheep.fleeTimer + dt
    local awayX = 0
    local awayZ = 0
    if sheep.threatX ~= nil and sheep.threatZ ~= nil then
        awayX = root.position.x - sheep.threatX
        awayZ = root.position.z - sheep.threatZ
    end
    local length = math.sqrt(awayX * awayX + awayZ * awayZ)
    if length < 0.0001 then
        local forward = hostRuntime.facingForward or getHorizontalForward(root)
        awayX = -forward.x
        awayZ = -forward.z
        length = 1
    end
    local direction = Vector3(awayX / length, 0, awayZ / length)
    sheepSteerTowards(root, direction, dt, SHEEP_FLEE_TURN_SPEED)
    sheepApplyMoveMode("walk")
    local forward = hostRuntime.facingForward or direction
    local remainingTurn = math.abs(sheepSignedYawDegrees(forward, direction))
    local speed = SHEEP_FLEE_SPEED * math.max(0, 1 - remainingTurn / 100)
    if speed > 0.02 then
        sheepMoveForward(root, speed, dt)
    end
    local farEnough = sheep.threatDistance == nil or sheep.threatDistance >= SHEEP_CALM_RADIUS
    if (farEnough and sheep.fleeTimer >= 1.2) or sheep.fleeTimer >= 5.0 then
        sheepEnterIdle()
    end
end

local function sheepUpdateRemote(root, dt)
    local previous = sheep.lastObservedPosition
    local speed = 0
    if previous ~= nil and dt > 0.0001 then
        local dx = root.position.x - previous.x
        local dz = root.position.z - previous.z
        speed = math.sqrt(dx * dx + dz * dz) / dt
    end
    sheep.lastObservedPosition = Vector3(root.position.x, root.position.y, root.position.z)
    if speed > 1.1 then
        sheepApplyMoveMode("run")
    elseif speed > 0.08 then
        sheepApplyMoveMode("walk")
    else
        sheepApplyMoveMode("idle")
    end
end

local function updateSheepRoaming(dt)
    local root = self and self.transform or nil
    if root == nil then
        return
    end

    if not sheep.ready then
        sheep.ready = true
        sheep.home = Vector3(root.position.x, root.position.y, root.position.z)
        sheep.lastObservedPosition = Vector3(root.position.x, root.position.y, root.position.z)
        sheep.modeTimer = sheepRandom(2.5, 5.0)
        sheep.idleActionTimer = sheepRandom(0.8, 2.0)
        sheep.ownershipTimer = 0.6
        sheep.isOwner = sheepCanDrive()
        ensureFacingCalibration(root, true)
        sheepBindSwayNodes()
    end

    sheep.swayTime = sheep.swayTime + dt
    sheepApplySway()

    sheep.ownershipTimer = sheep.ownershipTimer - dt
    if sheep.ownershipTimer <= 0 then
        sheep.ownershipTimer = 0.6
        sheep.isOwner = sheepCanDrive()
    end

    if not sheep.isOwner then
        sheepUpdateRemote(root, dt)
        return
    end

    sheep.noticeTimer = sheep.noticeTimer - dt
    if sheep.noticeTimer <= 0 then
        sheep.noticeTimer = 0.2
        sheepRefreshThreat(root)
    end

    if sheep.threatDistance ~= nil and sheep.threatDistance <= SHEEP_NOTICE_RADIUS and sheep.mode ~= "flee" then
        sheep.mode = "flee"
        sheep.fleeTimer = 0
        sheepApplyMoveMode("walk")
    end

    if sheep.mode == "flee" then
        sheepUpdateFlee(root, dt)
    elseif sheep.mode == "walk" then
        sheepUpdateWalk(root, dt)
    else
        sheepUpdateIdle(dt)
    end

    sheep.lastObservedPosition = Vector3(root.position.x, root.position.y, root.position.z)
end
-- END WORKSPACE SHEEP ROAMING

local function updateAutonomousMotion(dt)
    if not hostRuntime.isMounted then
        updateSheepRoaming(dt)
    end
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
