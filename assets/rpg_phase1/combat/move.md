# 基础移动 - Lua

> Lua 代码骨架。
>
> 使用前阅读 Manual 中的角色移动、飞行与游泳，以及角色控制开发约束。

---

## 一、基础移动骨架

### 1.1 走进触发区限速

```lua
local originalSpeed = nil
local affectedActor = nil

function OnActorTriggerEnter(actor)
  if actor == nil or not actor.isLocal then return end
  if originalSpeed == nil then    -- 幂等哨兵，避免重复缓存"改后的速度"
    originalSpeed = actor.speed
    affectedActor = actor
  end
  actor.speed = originalSpeed * 0.5   -- 减速 50%
end

function OnActorTriggerExit(actor)
  if actor == nil or not actor.isLocal then return end
  if originalSpeed == nil then return end
  if affectedActor ~= nil then
    affectedActor.speed = originalSpeed
  end
  originalSpeed = nil
  affectedActor = nil
end

function OnDestroy()
  -- 兜底：脚本销毁时未离开触发区也要还原，避免玩家永久卡在改速状态
  if originalSpeed == nil then return end
  if affectedActor ~= nil then affectedActor.speed = originalSpeed end
  originalSpeed = nil
  affectedActor = nil
end
```

### 1.2 强制自动跑向目标（剧情引导）

```lua
local targetActor = nil
local moveVec = nil

local function StartAutoRun(actor, direction)
  if actor == nil or not actor.isLocal then return end
  targetActor = actor
  moveVec = direction
  actor:MoveContinuously(direction)  -- 强制持续朝方向
end

local function StopAutoRun()
  if targetActor ~= nil then
    targetActor:StopMove()  -- 必须 StopMove，否则玩家永远漂移
    targetActor = nil
    moveVec = nil
  end
end

-- 到达指定坐标后停止
function Update()
  if targetActor == nil then return end
  local dist = CS.UnityEngine.Vector3.Distance(targetActor.position, targetPosition)
  if dist < 0.5 then
    StopAutoRun()
  end
end

function OnDestroy()
  StopAutoRun()  -- 兜底
end
```

### 1.3 剧情锁定（禁摇杆）

```lua
local lockedActor = nil

local function LockMovement(actor)
  if actor == nil or not actor.isLocal then return end
  lockedActor = actor
  actor:Immobilize(true)  -- 禁止摇杆输入
end

local function UnlockMovement()
  if lockedActor ~= nil then
    lockedActor:Immobilize(false)
    lockedActor = nil
  end
end

function OnDestroy()
  UnlockMovement()  -- 兜底
end
```

### 1.4 传送

```lua
local function TeleportToSpawn(actor)
  if actor == nil or not actor.isLocal then return end
  actor:Teleport(CS.UnityEngine.Vector3(0, 1, 0))
  -- 可选：指定朝向
  -- actor:Teleport(CS.UnityEngine.Vector3(0, 1, 0), CS.UnityEngine.Quaternion.Euler(0, 90, 0))
end
```

### 1.5 跳跃触发与监听

```lua
local localActor = nil

function OnActorSpawned(actor)
  if actor == nil or not actor.isLocal then return end
  localActor = actor
  actor.onJump:AddListener(OnJumpCallback)
  actor.onFallingGround:AddListener(OnFallingGroundCallback)
end

function OnJumpCallback()
  print("[movement] 玩家跳跃")
end

function OnFallingGroundCallback()
  print("[movement] 玩家落地")
end

function OnDestroy()
  if localActor ~= nil then
    localActor.onJump:RemoveListener(OnJumpCallback)
    localActor.onFallingGround:RemoveListener(OnFallingGroundCallback)
  end
end
```

## 二、变速骨架

### 2.1 状态初值

```lua
local SPEED_SCALE = 0.5     -- <1 减速；>1 加速。减速建议 >= 0.4，避免滑步
local DEFAULT_SPEED = 4.0   -- 仅作 savedSpeed 读取兜底，不作还原目标

local savedSpeed = nil      -- 改速前缓存的原速；nil = 当前无效果（幂等哨兵）
local affectedActor = nil   -- 被施加效果的本地玩家
local localActor = nil      -- 由 trigger / spawn 生命周期缓存
```

`SPEED_SCALE`、`DURATION`、`RAMP` 等调参必须使用 Lua `local` 声明。减速比例建议不低于 `0.4`，否则动画倍率不变时容易滑步。

### 2.2 核心 helper

```lua
-- 施加：仅当无效果时缓存一次原速，再按 scale 缩放。
-- 幂等、不叠加、绝不把"已经改过的速度"当成原速缓存。
local function applySpeedScale(actor, scale)
  if actor == nil or not actor.isLocal then return end

  if savedSpeed == nil then
    savedSpeed = actor.speed
    affectedActor = actor
  end
  affectedActor.speed = savedSpeed * scale
end

-- 还原：把 speed 还回缓存原速，并清空哨兵。幂等（无效果时直接返回）。
local function restoreSpeed()
  if savedSpeed == nil then return end
  if affectedActor ~= nil then
    affectedActor.speed = savedSpeed
  end
  savedSpeed = nil
  affectedActor = nil
end
```

首次施加变速时缓存 `savedSpeed` 和 `affectedActor`，结束时恢复缓存并清空二者；不要写死 `actor.speed = 4.0`。只有 `savedSpeed == nil` 时才能缓存，避免把已经缩放的速度再次当作原速。

### 2.3 销毁兜底

```lua
-- 效果仍生效时宿主被销毁，避免玩家永久卡在改速状态
function OnDestroy()
  restoreSpeed()
end
```

### 2.4 接入 A：靠近触发区

```lua
function OnActorTriggerEnter(actor)
  if actor == nil or not actor.isLocal then return end
  localActor = actor
  applySpeedScale(actor, SPEED_SCALE)
end

function OnActorTriggerExit(actor)
  if actor == nil or not actor.isLocal then return end
  restoreSpeed()
end
```

每个脚本独立缓存速度时，默认不支持改速区域重叠；需要叠加时必须由同一业务模块统一仲裁。变速无效果通常是传入了远端 Actor，离开区域未恢复通常是遗漏 Exit 路径或硬编码恢复。

### 2.5 接入 B：拾取手持

```lua
function OnPickup(actor, handType, pickUpPoint)
  -- ...pickup 主体（actor == nil guard、挂手骨、掌心对齐）对任意非 nil actor 照常执行...

  -- 变速是本地控制属性：只对本地玩家施加，与上面的挂手骨 isLocal 语义相反
  if actor ~= nil and actor.isLocal then
    applySpeedScale(actor, SPEED_SCALE)
  end
end

function OnDrop(actor, handType)
  -- ...pickup 主体（actor ~= currentPlayer guard、还原父节点 / 物理）照常执行...

  if actor ~= nil and actor.isLocal then
    restoreSpeed()
  end
end
```

拾取主体的挂手、父节点和物理处理不能因为 `isLocal` 被整体跳过；只有变速效果使用本地判断。变速还原必须保留 Drop 和 `OnDestroy()` 兜底路径。

### 2.6 接入 C：限时

```lua
local DURATION = 5.0   -- 生效秒数
local timeLeft = 0

local function applyTimedSpeed(actor)
  applySpeedScale(actor, SPEED_SCALE)
  timeLeft = DURATION
end

function Update()
  if savedSpeed == nil then return end
  timeLeft = timeLeft - CS.UnityEngine.Time.deltaTime
  if timeLeft <= 0 then
    restoreSpeed()
  end
end
```

限时效果必须在计时结束时还原；遗漏计时结束或销毁清理，会导致玩家持续保持错误速度。

### 2.7 接入 D：交互按钮开关

```lua
function OnInteractorButtonClick(index)
  if index ~= 1 or localActor == nil then return end

  -- 单玩家默认：直接执行，无 ensureOwnership。
  -- 若宿主按钮骨架启用了多人扩展，本段整体随其它点击业务一起包进 ensureOwnership 闭包（见网络开发约束）。
  if savedSpeed == nil then
    applySpeedScale(localActor, SPEED_SCALE)
  else
    restoreSpeed()
  end
end
```

按钮开关需要保持施加与还原对称；变速属性不需要单独申请网络对象主权。不要使用 `actor.velocity` 或 `Immobilize` 模拟减速，变速应通过 `actor.speed` 缩放实现。

### 2.8 平滑过渡

```lua
local RAMP = 6.0           -- 每秒逼近速度（单位 speed/秒）
local targetSpeed = nil    -- 当前要逼近的目标 speed；nil = 不插值

local function rampToScale(actor, scale)
  if actor == nil or not actor.isLocal then return end
  if savedSpeed == nil then
    savedSpeed = actor.speed
    affectedActor = actor
  end
  targetSpeed = savedSpeed * scale
end

local function rampRestore()
  if savedSpeed == nil then return end
  targetSpeed = savedSpeed
end

function Update()
  if affectedActor == nil or targetSpeed == nil then return end

  affectedActor.speed = CS.UnityEngine.Mathf.MoveTowards(
    affectedActor.speed, targetSpeed, RAMP * CS.UnityEngine.Time.deltaTime)

  -- 还原到位后清空哨兵
  if savedSpeed ~= nil and targetSpeed == savedSpeed
      and affectedActor.speed == savedSpeed then
    savedSpeed = nil
    affectedActor = nil
    targetSpeed = nil
  end
end
```

### 2.9 加速动画同步

```lua
affectedActor:SetSpeed(savedSpeed * SPEED_SCALE, 1.0)
```

