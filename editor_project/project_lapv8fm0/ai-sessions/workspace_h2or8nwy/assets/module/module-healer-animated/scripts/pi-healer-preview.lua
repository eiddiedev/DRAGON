-- 灯祭者动作互动预览面板：待机 / 行走 / 攻击 / 受击 + 自动轮播
---@displayName 灯祭者动作预览
---@start
---@var PreviewControls:boolean=true
---@name 预览面板
---@desc 关闭后不创建预览面板，动作仍按默认动作播放；面板右上角 × 也可关闭
---@end

local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")

local logger = Logger.create("pi-healer-preview")

local UnityEngine = CS.UnityEngine
local UI = CS.UnityEngine.UI
local Vector2 = CS.UnityEngine.Vector2
local Color = CS.UnityEngine.Color
local TextAnchor = CS.UnityEngine.TextAnchor
local Time = CS.UnityEngine.Time

local runtimeScope, scopeReason = RuntimeScope.from(self)

local animScript = nil
local animWait = 0
local animReported = false

local canvasGo = nil
local canvasTransform = nil
local panelGo = nil
local statusText = nil
local lastStatus = ""
local toggleText = nil
local panelBuilt = false
local started = false

local ACTION_LABEL = { Idle = "待机", Walk = "行走", Attack = "攻击", Hit = "受击" }
local BUTTON_ORDER = { "Idle", "Walk", "Attack", "Hit" }

-- 自动轮播状态
local autoCycle = true
local cycleStarted = false
local step = 1
local stepTimer = 0
local attackLeft = 0

local function logError(stage, err)
  logger:error("[" .. stage .. "] " .. tostring(err))
end

local function bindAnim()
  if animScript ~= nil then return true end
  if runtimeScope == nil then return false end
  local script, reason = runtimeScope:GetScript("ms-healer-animation.lua")
  if script ~= nil then
    animScript = script
    logger:info("[anim-bind] 已取得动作脚本")
    return true
  end
  if not animReported then
    animReported = true
    logger:warn("[anim-bind] 动作脚本尚未就绪（" .. tostring(reason) .. "），稍后重试")
  end
  return false
end

local function durationOf(name)
  if animScript == nil or type(animScript.GetActionDuration) ~= "function" then
    return 0
  end
  return animScript.GetActionDuration(name)
end

local function playAction(name)
  if animScript == nil then return end
  animScript.Play(name, { restart = true })
end

local function startStep(index)
  step = index
  if index == 1 then
    playAction("Idle")
    stepTimer = 2.0
  elseif index == 2 then
    playAction("Walk")
    stepTimer = 5.0
  elseif index == 3 then
    attackLeft = 2
    playAction("Attack")
    stepTimer = durationOf("Attack")
  else
    playAction("Hit")
    stepTimer = durationOf("Hit") + 0.05
  end
end

local function loadFont()
  local names = { "LegacyRuntime.ttf", "Arial.ttf" }
  for i = 1, #names do
    local ok, font = pcall(function()
      return UnityEngine.Resources.GetBuiltinResource(typeof(UnityEngine.Font), names[i])
    end)
    if ok and font ~= nil then
      return font, names[i]
    end
  end
  return nil, nil
end

local function makeNode(name, parentTransform, width, height)
  local go = nil
  local ok = pcall(function()
    go = UnityEngine.GameObject(name, typeof(UnityEngine.RectTransform))
  end)
  if not ok or go == nil then
    go = UnityEngine.GameObject(name)
    go:AddComponent(typeof(UnityEngine.RectTransform))
  end
  local rect = go:GetComponent(typeof(UnityEngine.RectTransform))
  if rect == nil then
    go:AddComponent(typeof(UnityEngine.RectTransform))
    rect = go:GetComponent(typeof(UnityEngine.RectTransform))
  end
  if parentTransform ~= nil then
    rect:SetParent(parentTransform, false)
  end
  rect.sizeDelta = Vector2(width, height)
  return go, rect
end

local function place(rect, anchorX, anchorY, pivotX, pivotY, x, y)
  rect.anchorMin = Vector2(anchorX, anchorY)
  rect.anchorMax = Vector2(anchorX, anchorY)
  rect.pivot = Vector2(pivotX, pivotY)
  rect.anchoredPosition = Vector2(x, y)
end

local function addText(go, font, size, anchor, color)
  local text = go:AddComponent(typeof(UI.Text))
  text.font = font
  text.fontSize = size
  text.alignment = anchor
  text.color = color or Color(0.93, 0.97, 1.0, 1.0)
  text.horizontalOverflow = UnityEngine.HorizontalWrapMode.Overflow
  text.verticalOverflow = UnityEngine.VerticalWrapMode.Overflow
  return text
end

local function makeButton(parentTransform, label, font, x, y, width, height, onClick)
  local go, rect = makeNode("Btn_" .. label, parentTransform, width, height)
  place(rect, 0, 1, 0, 1, x, y)
  local image = go:AddComponent(typeof(UI.Image))
  image.color = Color(0.09, 0.31, 0.30, 0.95)
  local button = go:AddComponent(typeof(UI.Button))
  button.targetGraphic = image

  local textGo, textRect = makeNode("Label", go.transform, width, height)
  place(textRect, 0.5, 0.5, 0.5, 0.5, 0, 0)
  local text = addText(textGo, font, 22, TextAnchor.MiddleCenter, Color(0.90, 1.0, 0.96, 1.0))
  text.text = label

  button.onClick:AddListener(function()
    local ok, err = pcall(onClick)
    if not ok then logError("button-" .. label, err) end
  end)
  return go, text
end

local function ensureEventSystem()
  local okType, eventSystemType = pcall(function()
    return typeof(UnityEngine.EventSystems.EventSystem)
  end)
  if not okType or eventSystemType == nil then
    return false, "EventSystem 类型不可用：" .. tostring(eventSystemType)
  end
  local okFind, existing = pcall(function()
    return UnityEngine.Object.FindObjectOfType(eventSystemType)
  end)
  if okFind and existing ~= nil then
    return true, "复用场景内 EventSystem"
  end
  local okNew, err = pcall(function()
    local go = UnityEngine.GameObject("HealerPreviewEventSystem")
    go:AddComponent(eventSystemType)
    local okModule, moduleType = pcall(function()
      return typeof(UnityEngine.EventSystems.StandaloneInputModule)
    end)
    if okModule and moduleType ~= nil then
      go:AddComponent(moduleType)
    end
    return true
  end)
  if not okNew then
    return false, "创建 EventSystem 失败：" .. tostring(err)
  end
  return true, "新建 EventSystem"
end

local function refreshStatus()
  if statusText == nil then return end
  local actionName = "Idle"
  local boneInfo = "骨骼 0/22"
  if animScript ~= nil then
    if type(animScript.GetAction) == "function" then
      actionName = animScript.GetAction() or "Idle"
    end
    if type(animScript.GetRigStatus) == "function" then
      local status = animScript.GetRigStatus()
      if status ~= nil then
        boneInfo = "骨骼 " .. tostring(status.boneCount) .. "/" .. tostring(status.expected)
      end
    end
  end
  local label = ACTION_LABEL[actionName] or actionName
  local line = "当前动作：" .. label .. "    " .. boneInfo
  if line ~= lastStatus then
    lastStatus = line
    statusText.text = line
  end
end

local function setToggleLabel()
  if toggleText == nil then return end
  toggleText.text = autoCycle and "自动轮播：开" or "自动轮播：关"
end

local function destroyPanel()
  if canvasGo ~= nil then
    UnityEngine.Object.Destroy(canvasGo)
  end
  canvasGo = nil
  canvasTransform = nil
  panelGo = nil
  statusText = nil
  toggleText = nil
  lastStatus = ""
  panelBuilt = false
end

local function buildPanel()
  if not PreviewControls then
    logger:info("[panel] PreviewControls 关闭，不创建预览面板")
    return
  end
  local font, fontName = loadFont()
  if font == nil then
    logger:error("[font] 未能取得内置字体，面板文字可能不显示")
  else
    logger:info("[font] 使用字体 " .. tostring(fontName))
  end

  local okCanvas, canvasErr = pcall(function()
    canvasGo = UnityEngine.GameObject("HealerPreviewCanvas", typeof(UnityEngine.RectTransform))
    local canvas = canvasGo:AddComponent(typeof(UnityEngine.Canvas))
    canvas.renderMode = UnityEngine.RenderMode.ScreenSpaceOverlay
    canvas.sortingOrder = 200
    local scaler = canvasGo:AddComponent(typeof(UI.CanvasScaler))
    scaler.uiScaleMode = UI.CanvasScaler.ScaleMode.ScaleWithScreenSize
    scaler.referenceResolution = Vector2(1920, 1080)
    scaler.matchWidthOrHeight = 0.5
    canvasGo:AddComponent(typeof(UI.GraphicRaycaster))
    canvasTransform = canvasGo.transform
  end)
  if not okCanvas then
    logError("canvas", canvasErr)
    destroyPanel()
    return
  end

  local okPanel, panelErr = pcall(function()
    local panelRect = nil
    panelGo, panelRect = makeNode("Panel", canvasTransform, 470, 300)
    place(panelRect, 0, 1, 0, 1, 36, -120)
    local bg = panelGo:AddComponent(typeof(UI.Image))
    bg.color = Color(0.03, 0.09, 0.11, 0.86)

    local titleGo, titleRect = makeNode("Title", panelGo.transform, 380, 34)
    place(titleRect, 0, 1, 0, 1, 14, -10)
    local title = addText(titleGo, font, 24, TextAnchor.UpperLeft, Color(0.75, 1.0, 0.88, 1.0))
    title.text = "灯祭者动作预览"

    local statusGo, statusRect = makeNode("Status", panelGo.transform, 440, 30)
    place(statusRect, 0, 1, 0, 1, 14, -50)
    statusText = addText(statusGo, font, 20, TextAnchor.UpperLeft, Color(0.80, 0.90, 0.95, 1.0))
    statusText.text = "当前动作：待机    骨骼 0/22"

    local x0 = 14
    local w = 104
    local gap = 8
    for i = 1, #BUTTON_ORDER do
      local name = BUTTON_ORDER[i]
      makeButton(panelGo.transform, ACTION_LABEL[name], font, x0 + (i - 1) * (w + gap), -92, w, 54, function()
        autoCycle = false
        setToggleLabel()
        step = 0
        playAction(name)
      end)
    end

    local toggleGo, toggleRect = makeNode("ToggleAuto", panelGo.transform, 250, 48)
    place(toggleRect, 0, 1, 0, 1, 14, -158)
    local toggleImage = toggleGo:AddComponent(typeof(UI.Image))
    toggleImage.color = Color(0.16, 0.28, 0.36, 0.95)
    local toggleButton = toggleGo:AddComponent(typeof(UI.Button))
    toggleButton.targetGraphic = toggleImage
    local toggleLabelGo, toggleLabelRect = makeNode("Label", toggleGo.transform, 250, 48)
    place(toggleLabelRect, 0.5, 0.5, 0.5, 0.5, 0, 0)
    toggleText = addText(toggleLabelGo, font, 20, TextAnchor.MiddleCenter, Color(0.88, 0.96, 1.0, 1.0))
    toggleButton.onClick:AddListener(function()
      local ok, err = pcall(function()
        autoCycle = not autoCycle
        setToggleLabel()
        if autoCycle then
          cycleStarted = true
          startStep(1)
        else
          cycleStarted = false
        end
      end)
      if not ok then logError("toggle", err) end
    end)

    local hintGo, hintRect = makeNode("Hint", panelGo.transform, 430, 24)
    place(hintRect, 0, 1, 0, 1, 14, -216)
    local hint = addText(hintGo, font, 16, TextAnchor.UpperLeft, Color(0.55, 0.68, 0.72, 1.0))
    hint.text = "点击任一动作会停止轮播；攻击与受击结束自动回待机"

    local closeGo, closeRect = makeNode("Close", panelGo.transform, 34, 34)
    place(closeRect, 1, 1, 1, 1, -10, -8)
    local closeImage = closeGo:AddComponent(typeof(UI.Image))
    closeImage.color = Color(0.35, 0.15, 0.16, 0.9)
    local closeButton = closeGo:AddComponent(typeof(UI.Button))
    closeButton.targetGraphic = closeImage
    local closeLabelGo, closeLabelRect = makeNode("Label", closeGo.transform, 34, 34)
    place(closeLabelRect, 0.5, 0.5, 0.5, 0.5, 0, 0)
    local closeLabel = addText(closeLabelGo, font, 22, TextAnchor.MiddleCenter, Color(1, 0.88, 0.88, 1))
    closeLabel.text = "×"
    closeButton.onClick:AddListener(function()
      logger:info("[panel] 用户关闭预览面板")
      destroyPanel()
    end)
  end)
  if not okPanel then
    logError("panel", panelErr)
    destroyPanel()
    return
  end

  panelBuilt = true
  setToggleLabel()
  refreshStatus()
  logger:info("[panel] 预览面板创建完成")
end

function Start()
  if runtimeScope == nil then
    logger:error("预览初始化失败：没有取得资源 Scope（" .. tostring(scopeReason) .. "）")
    return
  end
  started = true
  bindAnim()
  local okCall, okEs, esMessage = pcall(ensureEventSystem)
  if not okCall then
    logError("event-system", okEs)
  elseif okEs then
    logger:info("[event-system] " .. tostring(esMessage))
  else
    logger:error("[event-system] " .. tostring(esMessage))
  end
  buildPanel()
  if autoCycle and animScript ~= nil then
    cycleStarted = true
    startStep(1)
  end
end

function OnEnable()
  if started and not panelBuilt and PreviewControls then
    buildPanel()
  end
end

function OnDisable()
  destroyPanel()
end

function Update()
  if started and animScript == nil then
    animWait = animWait + Time.deltaTime
    if animWait > 0.5 then
      animWait = 0
      bindAnim()
    end
  end

  if animScript == nil then return end

  if autoCycle and not cycleStarted then
    cycleStarted = true
    startStep(1)
  end
  if not autoCycle then
    cycleStarted = false
  end

  local dt = Time.deltaTime
  if autoCycle and step > 0 then
    stepTimer = stepTimer - dt
    if stepTimer <= 0 then
      if step == 3 then
        attackLeft = attackLeft - 1
        if attackLeft > 0 then
          playAction("Attack")
          stepTimer = durationOf("Attack")
        else
          startStep(4)
        end
      else
        startStep(step % 4 + 1)
      end
    end
  end
  refreshStatus()
end