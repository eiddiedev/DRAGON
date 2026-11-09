-- 玩家靠近女巫后出现交谈按钮，点击后头顶浮起紫色魔法气泡并轮播呓语
---@displayName 女巫呓语
---@start
---@var InteractButtonText:string="交谈"
---@name 交互按钮文字
---@desc 玩家靠近女巫后看到的按钮文字
---@var DialogueText:string="夜色真浓，你闻到了吗？|紫水晶在低语……它在记住你的脸。|别碰我的药瓶。|……退下吧，凡人的眼睛会灼伤。"
---@name 呓语台词
---@desc 用 | 分隔每一句，点击交谈后依次显示
---@var LineInterval:number=2.2
---@name 每句停留秒数
---@var EnableMagicBubble:boolean=true
---@name 显示魔法气泡
---@desc 交谈时在女巫头顶浮起紫色魔法气泡
---@end

local UnityEngine = CS.UnityEngine
local Time = CS.UnityEngine.Time
local PrimitiveType = CS.UnityEngine.PrimitiveType
local DouyinUtility = CS.DouyinUtility
local RuntimeScope = require("official.core.runtime_scope")
local Logger = require("official.core.logger")

local logger = Logger.create("pi-witch-dialogue")
local runtimeScope, runtimeScopeReason = RuntimeScope.from(self)

-- 下面都是本地临时状态：按钮引用、范围标记、交谈进度和气泡节点只服务当前客户端。
local interactionButton = nil
local localActorId = nil
local dialogueLines = {}
local talking = false
local lineIndex = 0
local lineTimer = 0
local bubbleRoot = nil
local bubbleMaterial = nil
local bubbleBasePosition = nil
local bubblePopTime = 0
local bubbleBobTime = 0

-- 把面板中的竖线分隔台词拆成逐句列表，忽略空句。
local function parseDialogue()
  dialogueLines = {}
  if type(DialogueText) ~= "string" then
    return
  end
  for piece in string.gmatch(DialogueText, "[^|]+") do
    local line = string.match(piece, "^%s*(.-)%s*$")
    if line ~= nil and line ~= "" then
      dialogueLines[#dialogueLines + 1] = line
    end
  end
end

local function getRootTransform()
  if runtimeScope == nil then
    return nil
  end
  local resourceRoot = runtimeScope:GetResourceRoot()
  if resourceRoot == nil then
    return nil
  end
  return resourceRoot.transform
end

-- 气泡外观取自模组本体渲染器的材质，复制后再改色，避免污染女巫自身模型。
local function acquireBubbleMaterial()
  if bubbleMaterial ~= nil then
    return bubbleMaterial
  end
  local rootTransform = getRootTransform()
  if rootTransform == nil then
    return nil
  end
  local sourceRenderer = rootTransform.gameObject:GetComponentInChildren(typeof(UnityEngine.Renderer), true)
  if sourceRenderer == nil or sourceRenderer.sharedMaterial == nil then
    logger:warnOnce("material-missing", "女巫模型没有可用材质，魔法气泡沿用默认外观")
    return nil
  end

  local material = UnityEngine.Material(sourceRenderer.sharedMaterial)
  local glow = UnityEngine.Color(0.46, 0.18, 0.92, 1)
  if material:HasProperty("_BaseColor") then
    material:SetColor("_BaseColor", glow)
  elseif material:HasProperty("baseColorFactor") then
    material:SetColor("baseColorFactor", glow)
  elseif material:HasProperty("_Color") then
    material:SetColor("_Color", glow)
  end
  if material:HasProperty("_EmissionColor") then
    pcall(function()
      material:EnableKeyword("_EMISSION")
      material:SetColor("_EmissionColor", UnityEngine.Color(0.32, 0.07, 0.62, 1))
    end)
  end

  bubbleMaterial = material
  return bubbleMaterial
end

local function createBubbleSphere(parent, scale, position, material)
  local sphere = UnityEngine.GameObject.CreatePrimitive(PrimitiveType.Sphere)
  if sphere == nil then
    return nil
  end

  -- 只做视觉，不要碰撞体，避免影响玩家走动。
  local sphereCollider = sphere:GetComponent(typeof(UnityEngine.Collider))
  if sphereCollider ~= nil then
    UnityEngine.Object.Destroy(sphereCollider)
  end

  local renderer = sphere:GetComponent(typeof(UnityEngine.MeshRenderer))
  if renderer ~= nil and material ~= nil then
    renderer.sharedMaterial = material
  end

  sphere.transform:SetParent(parent, false)
  sphere.transform.localPosition = position
  sphere.transform.localScale = scale
  return sphere
end

-- 一个思考气泡：上方大圆泡加两个向下的圆点，尺寸按模型自身坐标单位。
local function ensureBubble()
  if EnableMagicBubble == false or bubbleRoot ~= nil then
    return
  end
  local rootTransform = getRootTransform()
  if rootTransform == nil then
    logger:warnOnce("root-missing", "无法取得女巫模型根节点，跳过魔法气泡")
    return
  end

  local material = acquireBubbleMaterial()
  local bubble = UnityEngine.GameObject("WitchMagicBubble")
  bubble.transform:SetParent(rootTransform, false)
  bubbleBasePosition = UnityEngine.Vector3(0, 2.35, 0.06)
  bubble.transform.localPosition = bubbleBasePosition
  bubble.transform.localScale = UnityEngine.Vector3(1, 1, 1)

  createBubbleSphere(bubble.transform, UnityEngine.Vector3(0.9, 0.62, 0.8), UnityEngine.Vector3(0, 0, 0), material)
  createBubbleSphere(bubble.transform, UnityEngine.Vector3(0.3, 0.3, 0.3), UnityEngine.Vector3(0.02, -0.34, 0), material)
  createBubbleSphere(bubble.transform, UnityEngine.Vector3(0.18, 0.18, 0.18), UnityEngine.Vector3(0.04, -0.5, 0), material)

  bubbleRoot = bubble
  bubble:SetActive(false)
end

local function showBubble()
  if EnableMagicBubble == false then
    return
  end
  ensureBubble()
  if bubbleRoot == nil then
    return
  end
  bubblePopTime = 0
  bubbleBobTime = 0
  bubbleRoot.transform.localScale = UnityEngine.Vector3(0.2, 0.2, 0.2)
  bubbleRoot:SetActive(true)
end

local function hideBubble()
  if bubbleRoot ~= nil then
    bubbleRoot:SetActive(false)
  end
end

local function finishTalking()
  talking = false
  lineIndex = 0
  lineTimer = 0
  hideBubble()
end

local function advanceLine()
  lineIndex = lineIndex + 1
  local line = dialogueLines[lineIndex]
  if line == nil then
    finishTalking()
    return
  end
  if DouyinUtility ~= nil then
    DouyinUtility.Toast("女巫：" .. line)
  end
  lineTimer = 0
end

-- 交谈只是当前客户端的本地表现，不改变任何跨端业务状态。
local function startTalking()
  if talking then
    return
  end
  if #dialogueLines == 0 then
    logger:warnOnce("no-lines", "呓语台词为空，交谈没有可显示的内容")
    return
  end
  talking = true
  lineIndex = 0
  lineTimer = 0
  showBubble()
  advanceLine()
end

-- 对象被禁用或失焦时按钮与气泡都要收口，避免残留入口或悬空特效。
local function cleanupInteraction()
  if interactionButton ~= nil then
    self:RemoveInteractorButton(interactionButton)
  end
  interactionButton = nil
  localActorId = nil
  finishTalking()
end

local function refreshButtonText()
  if interactionButton == nil then
    return
  end
  local label = interactionButton:GetComponentInChildren(typeof(CS.UnityEngine.UI.Text), true)
  if label ~= nil then
    label.text = InteractButtonText
  end
end

function Start()
  parseDialogue()
  if getRootTransform() == nil then
    logger:warn("初始化失败，runtimeScope 不可用：" .. tostring(runtimeScopeReason))
  end
end

function Update()
  -- 气泡出现时做一次弹出缩放，之后缓慢上下浮动。
  if bubbleRoot ~= nil and bubbleRoot.activeSelf then
    bubblePopTime = bubblePopTime + Time.deltaTime
    bubbleBobTime = bubbleBobTime + Time.deltaTime
    local pop = math.min(bubblePopTime / 0.18, 1)
    local scale = 0.2 + 0.8 * pop
    local bob = math.sin(bubbleBobTime * 2.4) * 0.03
    bubbleRoot.transform.localPosition = UnityEngine.Vector3(
      bubbleBasePosition.x, bubbleBasePosition.y + bob, bubbleBasePosition.z)
    bubbleRoot.transform.localScale = UnityEngine.Vector3(scale, scale, scale)
  end

  if not talking then
    return
  end
  lineTimer = lineTimer + Time.deltaTime
  if lineTimer >= LineInterval then
    advanceLine()
  end
end

function OnActorTriggerEnter(actor)
  if actor == nil or not actor.isLocal then
    return
  end
  localActorId = actor.actorID
  self:EnableInteraction()
end

function OnActorTriggerExit(actor)
  if actor == nil or not actor.isLocal then
    return
  end
  self:DisableInteraction()
  localActorId = nil
  finishTalking()
end

function OnFocus(handType)
  interactionButton = self:AddInteractorButton()
  refreshButtonText()
end

function OnLostFocus(handType)
  cleanupInteraction()
end

function OnInteractorButtonClick(index)
  if index ~= 1 or localActorId == nil then
    return
  end
  startTalking()
end

function OnDisable()
  cleanupInteraction()
end
