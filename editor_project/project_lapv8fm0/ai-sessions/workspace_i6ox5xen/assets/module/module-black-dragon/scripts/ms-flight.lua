-- 黑龙飞行驱动与翅膀挥动表现
---@displayName 黑龙飞行控制
---@start
---@var HorizontalSpeed:number=9
---@name 水平飞行速度
---@desc 按住前进或后退时的最高飞行速度
---@group 飞行
---@var VerticalSpeed:number=5
---@name 升降速度
---@desc 上升和下降的最高速度
---@group 飞行
---@var TurnSpeed:number=75
---@name 转向速度
---@desc 左右输入时每秒转向的角度
---@group 转向
---@var FlightFlapSpeed:number=1.9
---@name 飞行扇翅频率
---@desc 飞行时每秒扇动翅膀的次数
---@group 表现
---@var IdleFlapSpeed:number=0.55
---@name 待机扇翅频率
---@desc 未被骑乘时每秒轻扇翅膀的次数
---@group 表现
---@end

local UnityEngine = CS.UnityEngine
local Vector2 = CS.UnityEngine.Vector2
local Vector3 = CS.UnityEngine.Vector3
local Quaternion = CS.UnityEngine.Quaternion
local Mathf = CS.UnityEngine.Mathf
local Time = CS.UnityEngine.Time
local Input = CS.UnityEngine.Input
local KeyCode = CS.UnityEngine.KeyCode
local DouyinInputService = CS.DouyinInputService
local DouyinUIService = CS.DouyinUIService
local UIType = CS.UIType
local EventTrigger = CS.UnityEngine.EventSystems.EventTrigger
local EventTriggerType = CS.UnityEngine.EventSystems.EventTriggerType
local RuntimeScope = require("official.core.runtime_scope")

local runtimeScope = RuntimeScope.from(self)

local deadZone = 0.12
local idleDamping = 4.5
local horizontalAccel = 9
local verticalAccel = 7
local pitchAngle = 18
local rollAngle = 20
local motionLerpSpeed = 5
local flightFlapAmplitude = 30
local idleFlapAmplitude = 8
local bobAmplitude = 0.035

local rb = nil
local visualRoot = nil
local wingLeft = nil
local wingRight = nil
local neckRoot = nil
local tailRoot = nil

local moveVec = Vector2.zero
local onMoveInputStart = nil
local onMoveInputPerform = nil
local onMoveInputCancel = nil

local riderActive = false
local occupied = false
local controlReady = false
local controlSupported = false
local controlPending = false
local nextControlTry = 0
local velocityX = 0
local velocityY = 0
local velocityZ = 0
local m_yaw = 0
local m_pitch = 0
local m_roll = 0
local animationTime = 0
local rideCameraApplied = false

local ascendBtn = nil
local ascendTrigger = nil
local descendBtn = nil
local descendTrigger = nil
local btnAscend = false
local btnDescend = false

local function clearTrigger(trigger)
  if trigger == nil then return end
  if trigger.triggers ~= nil then
    trigger.triggers:Clear()
  end
end

local function bindTrigger(btn, onDown, onUp)
  if btn == nil or btn.gameObject == nil then return nil end
  local trigger = btn.gameObject:GetComponent(typeof(EventTrigger))
  if trigger == nil then
    trigger = btn.gameObject:AddComponent(typeof(EventTrigger))
  end
  clearTrigger(trigger)

  local entryDown = EventTrigger.Entry()
  entryDown.eventID = EventTriggerType.PointerDown
  entryDown.callback:AddListener(function(_) onDown() end)
  trigger.triggers:Add(entryDown)

  local entryUp = EventTrigger.Entry()
  entryUp.eventID = EventTriggerType.PointerUp
  entryUp.callback:AddListener(function(_) onUp() end)
  trigger.triggers:Add(entryUp)

  return trigger
end

local function setButtonText(btn, text)
  if btn == nil then return end
  local label = btn:GetComponentInChildren(typeof(CS.UnityEngine.UI.Text), true)
  if label ~= nil then
    label.gameObject:SetActive(true)
    label.text = text
  end
end

local function setupActionButton(uiType, btnText, onDown, onUp)
  local btn = DouyinUIService.GetInteractionButton(uiType)
  if btn == nil then return nil, nil end
  btn.gameObject:SetActive(true)
  btn.transition = CS.UnityEngine.UI.Selectable.Transition.None
  local tween = btn.gameObject:GetComponentInChildren(typeof(CS.ButtonTweenEffect), true)
  if tween ~= nil then
    tween.enabled = false
  end
  setButtonText(btn, btnText)
  local trigger = bindTrigger(btn, onDown, onUp)
  return btn, trigger
end

local function hideButton(btn, trigger)
  if trigger ~= nil then clearTrigger(trigger) end
  if btn ~= nil then btn.gameObject:SetActive(false) end
end

local function showFlightButtons()
  if ascendBtn ~= nil or descendBtn ~= nil then return end
  ascendBtn, ascendTrigger = setupActionButton(
    UIType.CustomMain, "上升",
    function() if riderActive then btnAscend = true end end,
    function() btnAscend = false end
  )
  descendBtn, descendTrigger = setupActionButton(
    UIType.CustomSub, "下降",
    function() if riderActive then btnDescend = true end end,
    function() btnDescend = false end
  )
end

local function hideFlightButtons()
  hideButton(ascendBtn, ascendTrigger)
  ascendBtn = nil
  ascendTrigger = nil
  hideButton(descendBtn, descendTrigger)
  descendBtn = nil
  descendTrigger = nil
  btnAscend = false
  btnDescend = false
end

local function applyRideCamera()
  if rideCameraApplied then return end
  CS.DouyinCameraService.SetDistance(15)
  CS.DouyinCameraService.SetPitch(18)
  CS.DouyinCameraService.SetOffset(Vector3(0, 2.6, 0))
  rideCameraApplied = true
end

local function restoreRideCamera()
  if not rideCameraApplied then return end
  CS.DouyinCameraService.SetDistance(4)
  CS.DouyinCameraService.SetPitch(0)
  CS.DouyinCameraService.SetOffset(Vector3(0, 0, 0))
  rideCameraApplied = false
end

local function clearInput()
  moveVec = Vector2.zero
  btnAscend = false
  btnDescend = false
  velocityX = 0
  velocityY = 0
  velocityZ = 0
end

local function requestControl()
  if not controlSupported or controlPending or controlReady then return end
  if self:IsNull() then return end
  if self:HasControllership() then
    controlReady = true
    return
  end

  controlPending = true
  self:RequestControllership(function(success)
    controlPending = false
    if self:IsNull() then return end
    if success and self:HasControllership() then
      controlReady = true
    else
      nextControlTry = Time.time + 1.0
    end
  end)
end

local function releaseControl()
  controlReady = false
  if controlSupported and self:HasControllership() then
    self:ReleaseControllership()
  end
end

local function resolveVerticalInput()
  local up = Input.GetKey(KeyCode.E) or btnAscend
  local down = Input.GetKey(KeyCode.Q) or btnDescend
  if up and not down then return 1 end
  if down and not up then return -1 end
  return 0
end

local function findNodes()
  if runtimeScope == nil then return end
  visualRoot = runtimeScope:GetTransformByPath("DragonRoot/VisualRoot")
  wingLeft = runtimeScope:GetTransformByPath("DragonRoot/VisualRoot/WingLeftRoot")
  wingRight = runtimeScope:GetTransformByPath("DragonRoot/VisualRoot/WingRightRoot")
  neckRoot = runtimeScope:GetTransformByPath("DragonRoot/VisualRoot/NeckRoot")
  tailRoot = runtimeScope:GetTransformByPath("DragonRoot/VisualRoot/TailRoot")
end

local function animateCreature()
  animationTime = animationTime + Time.deltaTime
  local flying = occupied
  local flapHz = flying and FlightFlapSpeed or IdleFlapSpeed
  local flapAmplitude = flying and flightFlapAmplitude or idleFlapAmplitude
  local flap = Mathf.Sin(animationTime * flapHz * 2 * Mathf.PI) * flapAmplitude

  -- Unity 的 X 轴相对 glTF 镜像：左翼位于 -X，需要反向 Z 旋转抬翼。
  if wingLeft ~= nil then
    wingLeft.localEulerAngles = Vector3(0, 0, -flap)
  end
  if wingRight ~= nil then
    wingRight.localEulerAngles = Vector3(0, 0, flap)
  end

  local swayAmplitude = flying and 4.5 or 2.2
  if tailRoot ~= nil then
    local sway = Mathf.Sin(animationTime * 1.25) * swayAmplitude
    tailRoot.localEulerAngles = Vector3(0, sway, 0)
  end

  if neckRoot ~= nil then
    local neckBob = Mathf.Sin(animationTime * 0.85) * 1.2
    neckRoot.localEulerAngles = Vector3(neckBob, 0, 0)
  end

  if visualRoot ~= nil then
    local bob = 0
    if flying then
      bob = Mathf.Sin(animationTime * 2.1) * bobAmplitude
    end
    visualRoot.localPosition = Vector3(0, bob, 0)
  end
end

function Start()
  rb = self.gameObject:GetComponent(typeof(UnityEngine.Rigidbody))
  controlSupported = self.HasControllership ~= nil and self.RequestControllership ~= nil
  findNodes()

  onMoveInputStart = function()
    -- 起手时保持当前方向，由 Perform 覆盖。
  end
  onMoveInputPerform = function(vec)
    moveVec = vec
  end
  onMoveInputCancel = function()
    moveVec = Vector2.zero
  end

  DouyinInputService.onMoveInputStart:AddListener(onMoveInputStart)
  DouyinInputService.onMoveInputPerform:AddListener(onMoveInputPerform)
  DouyinInputService.onMoveInputCancel:AddListener(onMoveInputCancel)
end

function SetOccupied(value)
  occupied = value == true
end

function SetRiderActive(active)
  if active then
    if riderActive then return end
    riderActive = true
    occupied = true
    velocityX = 0
    velocityY = 0
    velocityZ = 0
    m_pitch = 0
    m_roll = 0
    m_yaw = self.transform.eulerAngles.y
    controlReady = not controlSupported
    nextControlTry = 0
    applyRideCamera()
    showFlightButtons()
    if controlSupported then
      requestControl()
    end
  else
    if not riderActive then return end
    riderActive = false
    occupied = false
    clearInput()
    m_pitch = 0
    m_roll = 0
    hideFlightButtons()
    restoreRideCamera()
    releaseControl()
  end
end

function OnControllershipTransferred(prevPlayer, currentPlayer)
  if not controlSupported then return end
  controlReady = self:HasControllership()
  if not controlReady and riderActive then
    nextControlTry = Time.time + 1.0
  end
end

function Update()
  animateCreature()

  if riderActive and controlSupported and not controlReady and not controlPending
    and Time.time >= nextControlTry then
    requestControl()
  end
end

function FixedUpdate()
  if not riderActive or not controlReady or rb == nil then return end

  local dt = Time.fixedDeltaTime
  local forwardInput = moveVec.y
  local turnInput = moveVec.x
  if math.abs(forwardInput) < deadZone then forwardInput = 0 end
  if math.abs(turnInput) < deadZone then turnInput = 0 end
  local verticalInput = resolveVerticalInput()

  m_yaw = m_yaw + turnInput * TurnSpeed * dt
  local targetPitch = -verticalInput * pitchAngle
  local targetRoll = -turnInput * rollAngle
  local lerpT = Mathf.Clamp01(motionLerpSpeed * dt)
  m_pitch = Mathf.Lerp(m_pitch, targetPitch, lerpT)
  m_roll = Mathf.Lerp(m_roll, targetRoll, lerpT)
  rb:MoveRotation(Quaternion.Euler(m_pitch, m_yaw, m_roll))

  local forward = self.transform.forward
  local horizontalForward = Vector3(forward.x, 0, forward.z)
  if horizontalForward.sqrMagnitude <= 0.0001 then
    horizontalForward = Vector3(0, 0, 1)
  else
    horizontalForward:Normalize()
  end

  local targetX = horizontalForward.x * forwardInput * HorizontalSpeed
  local targetZ = horizontalForward.z * forwardInput * HorizontalSpeed
  local targetY = verticalInput * VerticalSpeed
  local horizontalStep = (forwardInput == 0 and idleDamping or horizontalAccel) * dt
  local verticalStep = (verticalInput == 0 and idleDamping or verticalAccel) * dt

  velocityX = Mathf.MoveTowards(velocityX, targetX, horizontalStep)
  velocityZ = Mathf.MoveTowards(velocityZ, targetZ, horizontalStep)
  velocityY = Mathf.MoveTowards(velocityY, targetY, verticalStep)

  local nextPosition = rb.position + Vector3(velocityX, velocityY, velocityZ) * dt
  rb:MovePosition(nextPosition)
end

function OnDisable()
  if riderActive then
    riderActive = false
    clearInput()
    hideFlightButtons()
    restoreRideCamera()
    releaseControl()
  end
end

function OnDestroy()
  if onMoveInputStart ~= nil then
    DouyinInputService.onMoveInputStart:RemoveListener(onMoveInputStart)
    onMoveInputStart = nil
  end
  if onMoveInputPerform ~= nil then
    DouyinInputService.onMoveInputPerform:RemoveListener(onMoveInputPerform)
    onMoveInputPerform = nil
  end
  if onMoveInputCancel ~= nil then
    DouyinInputService.onMoveInputCancel:RemoveListener(onMoveInputCancel)
    onMoveInputCancel = nil
  end
  hideFlightButtons()
  restoreRideCamera()
  releaseControl()
end
