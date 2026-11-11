# 主权最佳实践 (Lua)

> 本文提供 Lua 侧主权 (Ownership) 的标准代码骨架与常见套路。关于主权的核心概念、生命周期与避坑指南，请参阅 [主权与控制权](../../manual/04-multiplayer-and-network/networking-basics/ownership-and-controllership.md)。

## 1. 常用状态判定套路

### 1.1 前置检查三件套
网络就绪检查，只有在 Unity 生命周期（Awake/OnEnable/Start/Update 等）时才需要检查。
```lua
function TrySetHp(value)
    -- 1. 网络环境准备好没（仅在 Unity 生命周期回调中需要）
    if not DouyinNetService.isNetworkSettled then return end
    -- 2. 对象是否已被销毁（跨帧调用时防御）
    if self:IsNull() then return end
    -- 3. 只有主权方才能写入同步变量
    if not self:HasOwnership() then return end

    hp:SetValue(value)
end
```

### 1.2 请求主权的兜底封装
```lua
function TryRequestOwnership()
    if not DouyinNetService.isNetworkSettled then return end
    if self:IsNull() then return end
    
    -- 已经是主权方：直接跳过
    if self:HasOwnership() then return end

    self:RequestOwnership(function(success)
        -- 回调时对象可能已被销毁，兜底一次
        if self:IsNull() then return end
        
        if success then
            -- 兜底检查（极少数情况可能被别人瞬间抢走）
            if not self:HasOwnership() then return end
            OnGainOwnership()
        else
            OnGainOwnershipFailed()
        end
    end)
end
```

### 1.3 转移后接管 / 清理
```lua
-- 记住上一帧是否是主权方，用于判断"变化"
local wasOwner = false

function OnOwnershipTransferred()
    local isOwner = self:HasOwnership()
    
    if isOwner and not wasOwner then
        -- 刚拿到主权，启动权威逻辑
        StartAuthorityLogic()
    elseif not isOwner and wasOwner then
        -- 刚失去主权，清理权威逻辑
        StopAuthorityLogic()
    end
    
    wasOwner = isOwner
end
```

---

## 2. 经典业务场景骨架

### 2.1 最小可用的同步变量写入
```lua
-- 主权方同步血量脚本
---@displayName 主权方同步血量
---@start
---@varSync hp:float=100
---@end

function Update()
    if not DouyinNetService.isNetworkSettled then return end
    -- 非主权方直接跳过，不参与逻辑推进
    if not self:HasOwnership() then return end

    hp:SetValue(hp:GetValue() - 1)
end

function Start()
    -- 所有端都会收到 OnValueChange，用于表现层同步
    hp:OnValueChange(function(cur, prev)
        print(string.format("血量变化：%s -> %s", tostring(prev), tostring(cur)))
    end)
end
```

### 2.2 非主权方转发写入
```lua
-- 非主权方同步血量脚本
---@displayName 非主权方同步血量
---@start
---@varSync hp:float=100
---@end

function OnClickTakeDamage(damage)
    if not DouyinNetService.isNetworkSettled then return end
    if self:IsNull() then return end

    if self:HasOwnership() then
        -- 主权方本地直接执行
        ApplyDamage(damage)
    else
        -- 非主权方转发给主权方执行
        self:SendMessageToOwner("ApplyDamage", damage)
    end
end

function ApplyDamage(damage)
    if not self:HasOwnership() then return end

    local cur = hp:GetValue()
    hp:SetValue(math.max(0, cur - damage))
end
```

### 2.3 请求主权 + 审批接管完整链路
```lua
-- 主权请求状态同步脚本
---@displayName 主权请求状态同步
---@start
---@varSync isBusy:bool=false
---@end

local wasOwner = false

-- === 1. 发起请求端 ===
function TryRequestOwnership()
    if self:HasOwnership() then return end
    
    self:RequestOwnership(function(success)
        if self:IsNull() then return end
        if not success then
            print("请求主权失败或被拒绝")
        end
    end)
end

-- === 2. 审批端（当前主权方） ===
function OnOwnershipRequest(senderId)
    -- 只做判断和 return，禁止在此处修改任何状态或 UI
    if isBusy:GetValue() then
        return false -- 拒绝
    end
    return true -- 同意
end

-- === 3. 转移后的全端广播 ===
function OnOwnershipTransferred()
    local isOwner = self:HasOwnership()
    if isOwner and not wasOwner then
        StartAuthorityLogic()
    elseif not isOwner and wasOwner then
        StopAuthorityLogic()
    end
    wasOwner = isOwner
end
```

### 2.4 主权方主动指派
```lua
-- 通过 Player 对象转交
function GiveOwnershipTo(targetPlayer)
    if not DouyinNetService.isNetworkSettled then return end
    if self:IsNull() or not self:HasOwnership() then return end

    -- SetOwner 返回 false 表示条件不满足
    local success = self:SetOwner(targetPlayer)
end

-- 通过 Actor ID 转交
function GiveOwnershipToActor(actorId)
    if not DouyinNetService.isNetworkSettled then return end
    if not self:HasOwnership() then return end

    self:SetOwnership(actorId, function(success)
        if self:IsNull() then return end
        -- 转移成功或目标已离线
    end)
end
```

### 2.5 权威计时器的接管与清理
```lua
local authorityTimer = nil
local isAuthorityRunning = false

function OnNetSpawned()
    if self:HasOwnership() then StartAuthorityLoop() end
end

function OnNetDestroy()
    StopAuthorityLoop()
end

function OnOwnershipTransferred()
    if self:HasOwnership() then
        StartAuthorityLoop()
    else
        StopAuthorityLoop()
    end
end

function StartAuthorityLoop()
    if isAuthorityRunning then return end 
    isAuthorityRunning = true
    
    authorityTimer = setInterval(function()
        if self:IsNull() or not self:HasOwnership() then
            StopAuthorityLoop()
            return
        end
        -- 执行周期性逻辑
    end, 1000)
end

function StopAuthorityLoop()
    isAuthorityRunning = false
    if authorityTimer then
        clearInterval(authorityTimer)
        authorityTimer = nil
    end
end
```

---

## 3. 按钮路径主权闭环 (ensureOwnership 最小化写法)

适用于会修改网络物体状态（含 `---@varSync` 写入）的所有 `interaction-button` 场景。

```lua
-- 主权确保：执行任何修改网络对象的业务前，先经网络总闸 + 主权判定
local ownershipPending = false

local function ensureOwnership(action)
  if action == nil then return end

  -- 硬约束 1：isNetworkSettled 必须是唯一总闸
  if not DouyinNetService.isNetworkSettled then return end

  -- 硬约束 2：已有主权直接执行
  if self:HasOwnership() then
    action()
    return
  end

  -- 防连点重入
  if ownershipPending then return end
  ownershipPending = true

  -- 硬约束 3：请求主权，失败不兜底
  self:RequestOwnership(function(bSucceed)
    ownershipPending = false
    if bSucceed then
      action()
    end
  end)
end

-- 按钮标准写法
function OnInteractorButtonClick(index)
  if index ~= 1 or localActor == nil then return end

  ensureOwnership(function()
    -- 业务分发（如 varSync:SetValue）统一写在这里
  end)
end
```

---

## 4. 与框架接管 API 的边界

对于 `Pickup / SitDown`，框架已接管主权和控制权切换，业务侧**禁止**手写主权链路。
```lua
function OnInteractorButtonClick(index)
    local actor = DouyinActorService.GetLocalActor()
    if not actor or actor:IsPickup() then return end

    -- ✅ 直接调用框架接口，主权由框架代管
    DouyinActor.Pickup(self.gameObject, 0)
end

function OnPickup(actor, hand, matrix)
    -- 此时主权已经转移完成
    self.transform:SetParent(actor.gameObject.transform)
end
```

