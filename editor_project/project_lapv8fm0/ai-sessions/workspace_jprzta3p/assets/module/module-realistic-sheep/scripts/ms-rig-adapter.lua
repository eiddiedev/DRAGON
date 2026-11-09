-- Animated creature controller adapter companion.
-- Keeps generated controller locals outside ms-root.lua while exposing one stable adapter contract.
---@displayName 生物动画适配

-- BEGIN GENERATED CONTROLLER ADAPTER
-- merged from agent-runtime/resources/skeleton/data/Sheep_Controller_Param_Embedded.lua
--[[
Embedded animator adapter; original generator input omitted.
Adapter: embedded:Sheep_Controller_Param

This companion script is queried by ms-root.lua.
It does not declare standalone lifecycle hooks such as Awake / Start / Update.

Inference notes:
  - Heuristic Move mapping inferred from semantic tags and state names.
  - Adjust MOVE_VALUES if the controller expects different integer values.
]]

local Animator = CS.UnityEngine.Animator
local AnimatorCullingMode = CS.UnityEngine.AnimatorCullingMode
local adapterLogger = require("official.core.logger").create("animated-creature-adapter")

local GENERATED_CONTROLLER_ADAPTER = {
    controllerName = "Sheep_Controller_Param",
    identifier = "Sheep_Controller_Param",
}

GENERATED_CONTROLLER_ADAPTER.CONTRACT_VERSION = 1
GENERATED_CONTROLLER_ADAPTER.ADAPTER_KIND = "embedded_animator_controller"
GENERATED_CONTROLLER_ADAPTER.CONTROLLER_NAME = "Sheep_Controller_Param"
GENERATED_CONTROLLER_ADAPTER.IDENTIFIER = "Sheep_Controller_Param"
GENERATED_CONTROLLER_ADAPTER.SOURCE_JSON = "embedded:Sheep_Controller_Param"
GENERATED_CONTROLLER_ADAPTER.SUPPORTED_CONTROL_PROFILES = { "land" }
GENERATED_CONTROLLER_ADAPTER.PRIMARY_MOVE_PARAM = "MoveState"
GENERATED_CONTROLLER_ADAPTER.DEFAULT_MOVE_MODE = "idle"

local PARAMS = {
    MoveState = "MoveState",
    TriggerDeath = "TriggerDeath",
    TriggerGetHit = "TriggerGetHit",
    TriggerIdleBaaa = "TriggerIdleBaaa",
    TriggerIdleChew = "TriggerIdleChew",
    TriggerIdleGraze = "TriggerIdleGraze",
    TriggerIdleLookAround = "TriggerIdleLookAround",
    TriggerRest = "TriggerRest",
    TriggerRestToGoBackUp = "TriggerRestToGoBackUp",
    TriggerGoToRest = "TriggerGoToRest",
    TriggerRunTurnL = "TriggerRunTurnL",
    TriggerWalkTurnR = "TriggerWalkTurnR",
    TriggerRunTurnR = "TriggerRunTurnR",
    TriggerSleepToGoBackUp = "TriggerSleepToGoBackUp",
    TriggerWalkTurnL = "TriggerWalkTurnL",
    TriggerSleep = "TriggerSleep",
    TriggerRevive = "TriggerRevive",
}

local DEFAULTS = {
    MoveState = 0,
    TriggerDeath = false,
    TriggerGetHit = false,
    TriggerIdleBaaa = false,
    TriggerIdleChew = false,
    TriggerIdleGraze = false,
    TriggerIdleLookAround = false,
    TriggerRest = false,
    TriggerRestToGoBackUp = false,
    TriggerGoToRest = false,
    TriggerRunTurnL = false,
    TriggerWalkTurnR = false,
    TriggerRunTurnR = false,
    TriggerSleepToGoBackUp = false,
    TriggerWalkTurnL = false,
    TriggerSleep = false,
    TriggerRevive = false,
}

local MOVE_VALUES = {
    idle = 0,
    walk = 1,
    run = 2,
}

local STATE_GROUPS = {
    idle = {
        "IdleBreathe",
        "IdleBaaa",
        "IdleChew",
        "IdleGraze",
        "IdleLookAround",
    },
    walk = {
        "Walk",
        "WalkTurnR",
        "WalkTurnL",
    },
    run = {
        "Run",
        "RunTurnL",
        "RunTurnR",
    },
    die = {
        "Death",
    },
    misc = {
        "GetHit",
        "Rest",
        "RestToGoBackUp",
        "GoToRest",
        "SleepToGoBackUp",
        "Sleep",
    },
}

local DIRECT_STATES = {
    sleepLoop = "Sleep",
}

local TRIGGER_PARAMS = {
    "TriggerDeath",
    "TriggerGetHit",
    "TriggerIdleBaaa",
    "TriggerIdleChew",
    "TriggerIdleGraze",
    "TriggerIdleLookAround",
    "TriggerRest",
    "TriggerRestToGoBackUp",
    "TriggerGoToRest",
    "TriggerRunTurnL",
    "TriggerWalkTurnR",
    "TriggerRunTurnR",
    "TriggerSleepToGoBackUp",
    "TriggerWalkTurnL",
    "TriggerSleep",
    "TriggerRevive",
}

local NEUTRAL_IDLE_RESET_TRIGGERS = {
    "TriggerIdleChew",
    "TriggerIdleGraze",
    "TriggerIdleLookAround",
    "TriggerRestToGoBackUp",
    "TriggerGoToRest",
    "TriggerSleepToGoBackUp",
}

local TURN_TRIGGER_PARAMS = {
    walk = {
        left = "TriggerWalkTurnL",
        right = "TriggerWalkTurnR",
    },
    run = {
        left = "TriggerRunTurnL",
        right = "TriggerRunTurnR",
    },
}

local EMBEDDED_RUNTIME = {}

local function clamp(value, minValue, maxValue)
    if value < minValue then
        return minValue
    end
    if value > maxValue then
        return maxValue
    end
    return value
end

local function ensure_adapter_runtime(hostRuntime)
    local storage = hostRuntime or EMBEDDED_RUNTIME
    local adapterRuntime = storage.__generatedControllerAdapter
    if adapterRuntime == nil then
        adapterRuntime = {
            animator = nil,
            hashes = {},
            state = {},
            isMounted = false,
            lastMountedRider = nil,
            lastTurnIntent = 0,
            lastForwardIntent = 0,
            lastJumpIntent = false,
            lastVerticalIntent = 0,
        }
        adapterRuntime.state.MoveState = DEFAULTS.MoveState
        storage.__generatedControllerAdapter = adapterRuntime
    end
    return adapterRuntime
end

local function get_param_hash(hostRuntime, paramName)
    local adapterRuntime = ensure_adapter_runtime(hostRuntime)
    local hash = adapterRuntime.hashes[paramName]
    if hash == nil then
        hash = Animator.StringToHash(paramName)
        adapterRuntime.hashes[paramName] = hash
    end
    return hash
end

function GENERATED_CONTROLLER_ADAPTER.EnsureAnimator(scriptSelf, hostRuntime)
    local adapterRuntime = ensure_adapter_runtime(hostRuntime)
    if adapterRuntime.animator ~= nil then
        return adapterRuntime.animator
    end
    if hostRuntime ~= nil and hostRuntime.animator ~= nil then
        adapterRuntime.animator = hostRuntime.animator
        return adapterRuntime.animator
    end
    if scriptSelf == nil or scriptSelf.gameObject == nil then
        return nil
    end
    local animator = scriptSelf.gameObject:GetComponent(typeof(Animator))
    if animator ~= nil then
        animator.cullingMode = AnimatorCullingMode.AlwaysAnimate
    else
        animator = scriptSelf.gameObject:AddComponent(typeof(Animator))
        animator.cullingMode = AnimatorCullingMode.AlwaysAnimate
        adapterLogger:warn("Sheep_Controller_Param_Embedded: Animator component was missing and has been added automatically.")
    end
    adapterRuntime.animator = animator
    if hostRuntime ~= nil and hostRuntime.animator == nil then
        hostRuntime.animator = animator
    end
    return animator
end

function GENERATED_CONTROLLER_ADAPTER.BindHost(scriptSelf, hostRuntime)
    local adapterRuntime = ensure_adapter_runtime(hostRuntime)
    if hostRuntime ~= nil and hostRuntime.controlProfile ~= nil then
        adapterRuntime.controlProfile = hostRuntime.controlProfile
    end
    GENERATED_CONTROLLER_ADAPTER.EnsureAnimator(scriptSelf, hostRuntime)
    return adapterRuntime
end

function GENERATED_CONTROLLER_ADAPTER.OnHostStart(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.EnsureAnimator(scriptSelf, hostRuntime)
    return true
end

function GENERATED_CONTROLLER_ADAPTER.OnMountedStateChanged(scriptSelf, hostRuntime, isMounted, riderOrNil)
    local adapterRuntime = ensure_adapter_runtime(hostRuntime)
    adapterRuntime.isMounted = isMounted == true
    adapterRuntime.lastMountedRider = riderOrNil
    if adapterRuntime.isMounted then
        return GENERATED_CONTROLLER_ADAPTER.SetMoveMode(scriptSelf, hostRuntime, "idle")
    end
    return GENERATED_CONTROLLER_ADAPTER.ApplyNeutralIdleDefaults(scriptSelf, hostRuntime)
end

function GENERATED_CONTROLLER_ADAPTER.OnMountedInput(scriptSelf, hostRuntime, moveMode, turnIntent, forwardIntent, jumpIntent, verticalIntent)
    local adapterRuntime = ensure_adapter_runtime(hostRuntime)
    adapterRuntime.lastTurnIntent = tonumber(turnIntent) or 0
    adapterRuntime.lastForwardIntent = tonumber(forwardIntent) or 0
    adapterRuntime.lastJumpIntent = jumpIntent == true
    adapterRuntime.lastVerticalIntent = tonumber(verticalIntent) or 0
    return GENERATED_CONTROLLER_ADAPTER.ApplyMountedLocomotion(scriptSelf, hostRuntime, moveMode, turnIntent, forwardIntent)
end

function GENERATED_CONTROLLER_ADAPTER.OnHostStop(scriptSelf, hostRuntime)
    local adapterRuntime = ensure_adapter_runtime(hostRuntime)
    adapterRuntime.lastTurnIntent = 0
    adapterRuntime.lastForwardIntent = 0
    adapterRuntime.lastJumpIntent = false
    adapterRuntime.lastVerticalIntent = 0
    return true
end

local function set_bool(scriptSelf, hostRuntime, paramName, value)
    local animator = GENERATED_CONTROLLER_ADAPTER.EnsureAnimator(scriptSelf, hostRuntime)
    if animator == nil then
        return false
    end
    animator:SetBool(get_param_hash(hostRuntime, paramName), value and true or false)
    return true
end

local function set_float(scriptSelf, hostRuntime, paramName, value)
    local animator = GENERATED_CONTROLLER_ADAPTER.EnsureAnimator(scriptSelf, hostRuntime)
    if animator == nil then
        return false
    end
    animator:SetFloat(get_param_hash(hostRuntime, paramName), value)
    return true
end

local function set_int(scriptSelf, hostRuntime, paramName, value)
    local animator = GENERATED_CONTROLLER_ADAPTER.EnsureAnimator(scriptSelf, hostRuntime)
    if animator == nil then
        return false
    end
    animator:SetInteger(get_param_hash(hostRuntime, paramName), value)
    return true
end

local function pulse_trigger(scriptSelf, hostRuntime, paramName)
    local animator = GENERATED_CONTROLLER_ADAPTER.EnsureAnimator(scriptSelf, hostRuntime)
    if animator == nil then
        return false
    end
    animator:SetTrigger(get_param_hash(hostRuntime, paramName))
    return true
end

local function reset_trigger(scriptSelf, hostRuntime, paramName)
    local animator = GENERATED_CONTROLLER_ADAPTER.EnsureAnimator(scriptSelf, hostRuntime)
    if animator == nil then
        return false
    end
    animator:ResetTrigger(get_param_hash(hostRuntime, paramName))
    return true
end

local function full_state_name(stateName)
    if stateName == nil or stateName == "" then
        return nil
    end
    if string.find(stateName, ".", 1, true) ~= nil then
        return stateName
    end
    return "Base Layer." .. stateName
end

function GENERATED_CONTROLLER_ADAPTER.CrossFadeState(scriptSelf, hostRuntime, stateName, fadeSeconds, layer)
    local animator = GENERATED_CONTROLLER_ADAPTER.EnsureAnimator(scriptSelf, hostRuntime)
    local fullName = full_state_name(stateName)
    if animator == nil or fullName == nil then
        return false
    end
    animator:CrossFadeInFixedTime(fullName, fadeSeconds or 0.15, layer or 0)
    return true
end

function GENERATED_CONTROLLER_ADAPTER.SetMoveStateValue(scriptSelf, hostRuntime, value)
    local adapterRuntime = ensure_adapter_runtime(hostRuntime)
    adapterRuntime.state.MoveState = math.floor(tonumber(value) or DEFAULTS.MoveState)
    set_int(scriptSelf, hostRuntime, PARAMS.MoveState, adapterRuntime.state.MoveState)
    return adapterRuntime.state.MoveState
end

function GENERATED_CONTROLLER_ADAPTER.SetMoveState(scriptSelf, hostRuntime, value)
    return GENERATED_CONTROLLER_ADAPTER.SetMoveStateValue(scriptSelf, hostRuntime, value)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerDeath(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerDeath)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerDeath(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerDeath)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerGetHit(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerGetHit)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerGetHit(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerGetHit)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerIdleBaaa(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerIdleBaaa)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerIdleBaaa(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerIdleBaaa)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerIdleChew(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerIdleChew)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerIdleChew(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerIdleChew)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerIdleGraze(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerIdleGraze)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerIdleGraze(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerIdleGraze)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerIdleLookAround(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerIdleLookAround)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerIdleLookAround(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerIdleLookAround)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerRest(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerRest)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerRest(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerRest)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerRestToGoBackUp(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerRestToGoBackUp)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerRestToGoBackUp(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerRestToGoBackUp)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerGoToRest(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerGoToRest)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerGoToRest(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerGoToRest)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerRunTurnL(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerRunTurnL)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerRunTurnL(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerRunTurnL)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerWalkTurnR(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerWalkTurnR)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerWalkTurnR(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerWalkTurnR)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerRunTurnR(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerRunTurnR)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerRunTurnR(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerRunTurnR)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerSleepToGoBackUp(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerSleepToGoBackUp)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerSleepToGoBackUp(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerSleepToGoBackUp)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerWalkTurnL(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerWalkTurnL)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerWalkTurnL(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerWalkTurnL)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerSleep(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerSleep)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerSleep(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerSleep)
end

function GENERATED_CONTROLLER_ADAPTER.PulseTriggerRevive(scriptSelf, hostRuntime)
    return pulse_trigger(scriptSelf, hostRuntime, PARAMS.TriggerRevive)
end

function GENERATED_CONTROLLER_ADAPTER.ResetTriggerRevive(scriptSelf, hostRuntime)
    return reset_trigger(scriptSelf, hostRuntime, PARAMS.TriggerRevive)
end

local function resolve_move_mode_value(modeName, fallback)
    if modeName == nil then
        return fallback
    end
    local value = MOVE_VALUES[string.lower(tostring(modeName))]
    if value == nil then
        return fallback
    end
    return value
end

local function normalize_mounted_move_mode(modeName, forwardIntent)
    local normalizedMode = string.lower(tostring(modeName or "idle"))
    local forward = tonumber(forwardIntent) or 0
    if math.abs(forward) < 0.08 or normalizedMode == "idle" then
        return "idle"
    end
    if normalizedMode == "run" or normalizedMode == "back" or normalizedMode == "reverse" then
        return "walk"
    end
    if MOVE_VALUES[normalizedMode] ~= nil then
        return normalizedMode
    end
    if forward > 0 then
        return "walk"
    end
    return "idle"
end

function GENERATED_CONTROLLER_ADAPTER.GetMoveModeName(hostRuntime)
    local adapterRuntime = ensure_adapter_runtime(hostRuntime)
    for modeName, modeValue in pairs(MOVE_VALUES) do
        if adapterRuntime.state.MoveState == modeValue then
            return modeName
        end
    end
    return "unknown"
end

function GENERATED_CONTROLLER_ADAPTER.SetMoveMode(scriptSelf, hostRuntime, modeName)
    local adapterRuntime = ensure_adapter_runtime(hostRuntime)
    return GENERATED_CONTROLLER_ADAPTER.SetMoveStateValue(scriptSelf, hostRuntime, resolve_move_mode_value(modeName, adapterRuntime.state.MoveState))
end

function GENERATED_CONTROLLER_ADAPTER.SetMoveValue(scriptSelf, hostRuntime, value)
    return GENERATED_CONTROLLER_ADAPTER.SetMoveStateValue(scriptSelf, hostRuntime, value)
end

function GENERATED_CONTROLLER_ADAPTER.ApplyMountedLocomotion(scriptSelf, hostRuntime, moveMode, turnIntent, forwardIntent)
    local forward = tonumber(forwardIntent) or 0
    local turn = tonumber(turnIntent) or 0
    local resolvedMode = normalize_mounted_move_mode(moveMode, forward)
    GENERATED_CONTROLLER_ADAPTER.SetMoveMode(scriptSelf, hostRuntime, resolvedMode)
    if resolvedMode ~= "idle" and forward > 0 then
        local pair = TURN_TRIGGER_PARAMS[resolvedMode]
        if pair ~= nil then
            if turn > 0.28 and pair.right ~= nil then
                pulse_trigger(scriptSelf, hostRuntime, pair.right)
            elseif turn < -0.28 and pair.left ~= nil then
                pulse_trigger(scriptSelf, hostRuntime, pair.left)
            end
        end
    end
    return resolvedMode
end

function GENERATED_CONTROLLER_ADAPTER.ApplyNeutralIdleDefaults(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.SetMoveMode(scriptSelf, hostRuntime, "idle")
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerIdleChew(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerIdleGraze(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerIdleLookAround(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerRestToGoBackUp(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerGoToRest(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerSleepToGoBackUp(scriptSelf, hostRuntime)
    return true
end

function GENERATED_CONTROLLER_ADAPTER.PlayDie(scriptSelf, hostRuntime, variantIndex, fadeSeconds)
    local index = math.floor(tonumber(variantIndex) or 1)
    local states = STATE_GROUPS.die
    local stateName = states[clamp(index, 1, #states)]
    return GENERATED_CONTROLLER_ADAPTER.CrossFadeState(scriptSelf, hostRuntime, stateName, fadeSeconds, 0)
end

function GENERATED_CONTROLLER_ADAPTER.ApplyDefaults(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.SetMoveStateValue(scriptSelf, hostRuntime, DEFAULTS.MoveState)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerDeath(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerGetHit(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerIdleBaaa(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerIdleChew(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerIdleGraze(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerIdleLookAround(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerRest(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerRestToGoBackUp(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerGoToRest(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerRunTurnL(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerWalkTurnR(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerRunTurnR(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerSleepToGoBackUp(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerWalkTurnL(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerSleep(scriptSelf, hostRuntime)
    GENERATED_CONTROLLER_ADAPTER.ResetTriggerRevive(scriptSelf, hostRuntime)
    return true
end

function GENERATED_CONTROLLER_ADAPTER.GetAnimatorSnapshot(hostRuntime)
    local adapterRuntime = ensure_adapter_runtime(hostRuntime)
    return {
        MoveState = adapterRuntime.state.MoveState,
        MoveMode = GENERATED_CONTROLLER_ADAPTER.GetMoveModeName(hostRuntime),
        stateGroups = STATE_GROUPS,
        directStates = DIRECT_STATES,
    }
end

GENERATED_CONTROLLER_ADAPTER.PARAMS = PARAMS
GENERATED_CONTROLLER_ADAPTER.DEFAULTS = DEFAULTS
GENERATED_CONTROLLER_ADAPTER.STATE_GROUPS = STATE_GROUPS
GENERATED_CONTROLLER_ADAPTER.DIRECT_STATES = DIRECT_STATES
GENERATED_CONTROLLER_ADAPTER.TRIGGER_PARAMS = TRIGGER_PARAMS
GENERATED_CONTROLLER_ADAPTER.NEUTRAL_IDLE_RESET_TRIGGERS = NEUTRAL_IDLE_RESET_TRIGGERS
GENERATED_CONTROLLER_ADAPTER.MOVE_VALUES = MOVE_VALUES
GENERATED_CONTROLLER_ADAPTER.TURN_TRIGGER_PARAMS = TURN_TRIGGER_PARAMS
-- END GENERATED CONTROLLER ADAPTER

function GetRigControllerAdapter()
    return GENERATED_CONTROLLER_ADAPTER
end
