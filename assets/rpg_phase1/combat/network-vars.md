# 基础同步变量（Lua）最佳实践

> 💡 **理论与机制指引**：关于同步变量的支持类型、生命周期窗口、完整触发链路以及常见坑（如 `---@var` 不可用），请参考手册：[同步变量.md](../../../manual/04-multiplayer-and-network/data-and-communication/synchronized-variables.md)。
> 本文仅提供基础同步变量在 Lua 侧开发时的标准代码骨架。

---

## 1. 最小可用基础同步变量骨架

```lua
-- 基础同步变量脚本
-- 1. 声明同步变量；如同时声明 ---@var，必须共用同一个声明块。
---@displayName 基础同步变量
---@start
---@var energyBallKey:string
---@name 能量球键
---@varSync intValue:int
---@varSync vectorValue:Vector3
---@end

-- 2. 统一在 OnNetSpawned 窗口中注册变化监听
function OnNetSpawned()
    -- 基础值 handler 参数顺序：(curVal, preVal)
    intValue:OnValueChange(function(curVal, preVal)
        print(string.format("intValue changed: %s -> %s", tostring(preVal), tostring(curVal)))
        RefreshUi(curVal)
    end)

    vectorValue:OnValueChange(function(curVal, preVal)
        -- ...
    end)
end

-- 3. 业务触发入口：处理主权方与非主权方的写入逻辑
function OnScoreChanged(newScore)
    if not self:HasOwnership() then
        -- 非主权方：转发请求到主权方执行
        self:SendMessageToOwner("OnScoreChanged", newScore)
        return
    end
    
    -- 主权方：直接写入，触发全端（含本端）的 OnValueChange
    intValue:SetValue(newScore)
    vectorValue:SetValue(UnityEngine.Vector3(1, 2, 0))
end

function RefreshUi(score)
    -- 表现层：根据新值更新 UI
end
```

---

## 2. 动态对象设置初始值（NetSpawn 窗口）

```lua
-- ================= 被创建的动态对象脚本 =================
---@displayName 动态对象同步变量
---@start
---@varSync ownerId:string
---@varSync initScore:int
---@end

function OnNetSpawned()
    -- 晚进房玩家和创建端（如果监听在此注册），都会在此时读取到有效值
    ownerId:OnValueChange(function(curVal, preVal)
       -- ...
    end)
    initScore:OnValueChange(function(curVal, preVal)
       -- ...
    end)
end

-- ================= 创建端（主权方）业务逻辑 =================
function CreateRoomObject(key, position, rotation, myOpenId, score)
    DouyinObjectService.NetSpawn(key, position, rotation, function(go)
        -- NetSpawn 回调：处于 Awake 之后、OnNetSpawned 之前
        -- 此时写入的值会可靠地同步给所有客户端
        local script = go:DouyinScript("动态对象脚本名")
        script.ownerId:SetValue(myOpenId)
        script.initScore:SetValue(score)
    end)
end
```

