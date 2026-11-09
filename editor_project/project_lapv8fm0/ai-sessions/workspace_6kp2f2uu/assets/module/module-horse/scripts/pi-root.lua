-- Shared mounted interaction template baseline.
-- Root interaction host: owns platform Seat callbacks, button state, input listeners, and motion handoff.
---@displayName 骑乘交互

---@start
---@var mountText:string="上马"
---@name 上马文案
---@desc 目标空闲时交互按钮显示的文案
---@group 交互
---@var dismountText:string="下马"
---@name 下马文案
---@desc 本地玩家乘坐目标时交互按钮显示的文案
---@group 交互
---@var TriggerRangeScale:number=1
---@name 触发范围倍率
---@desc 基于 meta.json 的初始触发范围等比放大
---@group 交互
---@end

-- Walk/run switching is coupled to the motion peer and stays an internal preset.
local RUN_THRESHOLD = 0.75

local UnityEngine = CS.UnityEngine
local Input = UnityEngine.Input
local KeyCode = UnityEngine.KeyCode
local DouyinInputService = CS.DouyinInputService
local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")
local Trigger = require("official.interaction.trigger")
Trigger.applyRangeScale(self, TriggerRangeScale)
local interactionLogger = Logger.create("animated-creature-interaction")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)

-- BEGIN TEMPLATE CONFIG
local DEAD_ZONE = 0.1
-- END TEMPLATE CONFIG

local localActor = nil
local interactorBtn = nil
local hasPassenger = false
local motionPeer = nil
local motionControlProfile = nil
local seatPeer = nil
local riderPeer = nil
local moveVec = UnityEngine.Vector2.zero
local ownershipPending = false

local onMoveInputStart = nil
local onMoveInputPerform = nil
local onMoveInputCancel = nil

local function ensureOwnership(action)
    if action == nil then
        return
    end

    if not DouyinNetService.isNetworkSettled then
        return
    end

    if self:HasOwnership() then
        action()
        return
    end

    if ownershipPending then
        return
    end
    ownershipPending = true

    self:RequestOwnership(function(succeeded)
        ownershipPending = false
        if succeeded then
            action()
        end
    end)
end

local function setButtonText(btn, text)
    if btn == nil then
        return
    end
    local label = btn:GetComponentInChildren(typeof(UnityEngine.UI.Text), true)
    if label ~= nil then
        label.gameObject:SetActive(true)
        label.text = text
    end
end

local function refreshButtonText()
    if interactorBtn == nil then
        return
    end
    setButtonText(interactorBtn, hasPassenger and dismountText or mountText)
end

local function sameRootObject(a, b)
    if a == nil or b == nil or a.transform == nil or b.transform == nil then
        return false
    end
    return a.transform.root == b.transform.root
end

local function resolveSeatPeer()
    if seatPeer ~= nil then
        return seatPeer
    end
    if runtimeScope == nil then
        interactionLogger:warnOnce("seat-scope-unavailable", "rig seat scope unavailable", runtimeScopeReason)
        return nil
    end

    local peer, reason = runtimeScope:GetScript("pi-rig-seat.lua")
    if
        peer == nil or not sameRootObject(peer.self, self) or
            type(peer.ResolveRigMountHelpers) ~= "function" or
            type(peer.HasRigSeatTarget) ~= "function"
     then
        interactionLogger:warnOnce("seat-script-unavailable", "rig seat script unavailable", reason)
        return nil
    end
    seatPeer = peer
    return seatPeer
end

local function resolveRiderPeer()
    if riderPeer ~= nil then
        return riderPeer
    end
    if runtimeScope == nil then
        return nil
    end
    local peer, reason = runtimeScope:GetScript("pi-rig-rider.lua")
    if
        peer == nil or not sameRootObject(peer.self, self) or
            type(peer.PrepareRigActorMount) ~= "function" or
            type(peer.ReleaseRigActorMount) ~= "function" or
            type(peer.SetRigActorColliderEnabled) ~= "function"
     then
        interactionLogger:warnOnce("rider-script-unavailable", "rig rider script unavailable", reason)
        return nil
    end
    riderPeer = peer
    return riderPeer
end

local function resolveMotionPeer()
    if runtimeScope == nil then
        interactionLogger:warnOnce("motion-scope-unavailable", "motion script scope unavailable", runtimeScopeReason)
        return nil
    end
    local motion, reason = runtimeScope:GetScript("ms-root.lua")
    if
        motion == nil or not sameRootObject(motion.self, self) or type(motion.GetRigControlProfile) ~= "function" or
            type(motion.SetMountedRider) ~= "function"
     then
        interactionLogger:warnOnce("motion-script-unavailable", "motion script unavailable or incompatible", reason)
        return nil
    end
    return motion
end

local function resolveMotionControlProfile()
    if motionControlProfile ~= nil then
        return motionControlProfile
    end
    if motionPeer == nil then
        motionPeer = resolveMotionPeer()
    end
    if motionPeer == nil then
        return nil
    end
    local ok, profile = pcall(motionPeer.GetRigControlProfile)
    if not ok or (profile ~= "land" and profile ~= "flying" and profile ~= "fish") then
        interactionLogger:warnOnce(
            "motion-profile-unavailable",
            "motion control profile unavailable or incompatible",
            tostring(profile)
        )
        return nil
    end
    motionControlProfile = profile
    return motionControlProfile
end

local function hasSeatTarget()
    local profile = resolveMotionControlProfile()
    if profile == nil then
        return false
    end
    local peer = resolveSeatPeer()
    if peer == nil then
        return false
    end
    return peer.HasRigSeatTarget(profile) == true
end

local function callMotion(methodName, ...)
    if motionPeer == nil then
        motionPeer = resolveMotionPeer()
    end
    if motionPeer == nil then
        return nil
    end
    local fn = motionPeer[methodName]
    if type(fn) ~= "function" then
        return nil
    end
    local ok, result = pcall(fn, ...)
    if ok then
        return result
    end
    return nil
end

local function handoffMoveIntent()
    local forward = moveVec.y
    if math.abs(forward) < DEAD_ZONE then
        forward = 0
    end
    callMotion("SetMountedMoveIntent", forward, 0)
end

local function handoffMoveState()
    local moveMode = "idle"
    if moveVec.y <= -DEAD_ZONE then
        moveMode = "back"
    elseif moveVec.y >= DEAD_ZONE then
        moveMode = moveVec.y > RUN_THRESHOLD and "run" or "walk"
    end
    callMotion("SetMountedMoveMode", moveMode)
end

local function handoffTurnIntent()
    local x = moveVec.x
    if math.abs(x) < DEAD_ZONE then
        x = 0
    end
    callMotion("SetMountedTurnIntent", x)
end

local function handoffVerticalIntent()
    local profile = resolveMotionControlProfile()
    if profile ~= "flying" and profile ~= "fish" then
        callMotion("SetMountedVerticalIntent", 0)
        return
    end
    local verticalIntent = 0
    if Input.GetKey(KeyCode.E) then
        verticalIntent = verticalIntent + 1
    end
    if Input.GetKey(KeyCode.Q) then
        verticalIntent = verticalIntent - 1
    end
    callMotion("SetMountedVerticalIntent", verticalIntent)
end

local function handoffJumpIntent()
    -- Only grounded profiles expose jump from interaction; flying/fish use vertical intent instead.
    local shouldJump = resolveMotionControlProfile() == "land" and Input.GetKeyDown(KeyCode.Space)
    callMotion("SetMountedJumpIntent", shouldJump)
end

function Start()
    if runtimeScope == nil then
        interactionLogger:warn("resource scope unavailable", runtimeScopeReason)
    end
    motionPeer = resolveMotionPeer()
    local profile = resolveMotionControlProfile()
    if profile ~= nil then
        local peer = resolveSeatPeer()
        if peer ~= nil then
            peer.ResolveRigMountHelpers(profile)
        end
    end

    onMoveInputStart = function(vec)
        moveVec = vec
    end
    onMoveInputPerform = function(vec)
        moveVec = vec
    end
    onMoveInputCancel = function()
        moveVec = UnityEngine.Vector2.zero
    end

    DouyinInputService.onMoveInputStart:AddListener(onMoveInputStart)
    DouyinInputService.onMoveInputPerform:AddListener(onMoveInputPerform)
    DouyinInputService.onMoveInputCancel:AddListener(onMoveInputCancel)
end

function OnDestroy()
    if onMoveInputStart ~= nil then
        DouyinInputService.onMoveInputStart:RemoveListener(onMoveInputStart)
    end
    if onMoveInputPerform ~= nil then
        DouyinInputService.onMoveInputPerform:RemoveListener(onMoveInputPerform)
    end
    if onMoveInputCancel ~= nil then
        DouyinInputService.onMoveInputCancel:RemoveListener(onMoveInputCancel)
    end
end

function OnActorTriggerEnter(actor)
    if actor == nil or not actor.isLocal or not hasSeatTarget() then
        return
    end
    localActor = actor
    self:EnableInteraction()
end

function OnActorTriggerExit(actor)
    if actor == nil or not actor.isLocal or hasPassenger then
        return
    end
    self:DisableInteraction()
end

function OnFocus(handType)
    interactorBtn = self:AddInteractorButton()
    refreshButtonText()
end

function OnLostFocus(handType)
    if interactorBtn ~= nil then
        self:RemoveInteractorButton(interactorBtn)
        interactorBtn = nil
    end
end

function OnInteractorButtonClick(index)
    if index ~= 1 or localActor == nil then
        return
    end
    ensureOwnership(function()
        if hasPassenger then
            localActor:StandUp(self.gameObject)
        else
            localActor:SitDown(self.gameObject)
        end
    end)
end

function OnSeatEntered(actor, handType)
    if actor == nil then
        return
    end
    local peer = nil
    if hasSeatTarget() then
        peer = resolveRiderPeer()
    end
    if peer == nil or peer.PrepareRigActorMount(actor) ~= true then
        if actor.isLocal then
            hasPassenger = false
            refreshButtonText()
        end
        return
    end

    if actor.isLocal then
        hasPassenger = true
    end
    motionPeer = resolveMotionPeer()
    callMotion("SetMountedRider", actor)
    if resolveMotionControlProfile() == "land" then
        callMotion("RefreshMountedGrounding", true)
    end
    if actor.isLocal then
        refreshButtonText()
    end
end

function OnSeatExited(actor)
    if actor == nil then
        return
    end
    local peer = resolveRiderPeer()
    if peer ~= nil then
        peer.ReleaseRigActorMount(actor)
    end
    if actor.isLocal then
        hasPassenger = false
        moveVec = UnityEngine.Vector2.zero
    end
    callMotion("ClearMountedRider")
    callMotion("ClearMountedGroundingState")
    callMotion("SetMountedVerticalIntent", 0)
    -- Restore collision only after the rider has left the creature volume and motion no longer treats it as mounted.
    if peer ~= nil then
        peer.SetRigActorColliderEnabled(actor, true)
    end
    if actor.isLocal then
        refreshButtonText()
    end
end

function Update()
    if not hasPassenger then
        return
    end
    handoffMoveIntent()
    handoffMoveState()
    handoffTurnIntent()
    handoffJumpIntent()
    handoffVerticalIntent()
end
