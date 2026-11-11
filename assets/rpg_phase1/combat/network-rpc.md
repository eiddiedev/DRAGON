# Lua 版本基础 RPC 通信

> **阅读指南**：本文仅提供基础 RPC 通信的代码骨架与最佳实践。
> 关于 RPC 的分派规则、参数类型限制、OwnerCall 的机制以及常见坑点（如生命周期调用失败、参数不支持 table 等），请务必阅读核心概念手册：[SendMessage 与 [Rpc] (消息互通)](../../../manual/04-multiplayer-and-network/data-and-communication/rpc/sendmessage.md)。

## 示例 A：`SendMessageToOwner` — 通知主权方

```lua
local Input = UnityEngine.Input

function Update()
    if not DouyinNetService.isNetworkSettled then return end
    if Input.GetKeyDown("1") then
        SendMessageToOwnerSample()
    end
end

function SendMessageToOwnerSample()
    print("--DouyinNetSample:发送消息给主权方")
    self:SendMessageToOwner("Method1", 1)
end

-- 主权方（自己或另一玩家）会执行到此
function Method1(index)
    -- 兜底：主权方独占的写入必须先查一次 HasOwnership
    if not self:HasOwnership() then return end
    print("--DouyinNetSample:收到 SendMessageToOwner 消息 " .. index)
end
```

## 示例 B：`SendMessageToAll` — 广播给所有人（含自己）

```lua
local Input = UnityEngine.Input

function Update()
    if not DouyinNetService.isNetworkSettled then return end
    if Input.GetKeyDown("1") then
        SendMessageToAllSample()
    end
end

function SendMessageToAllSample()
    print("--DouyinNetSample:发送消息给所有玩家")
    self:SendMessageToAll("Method2", 2)
end

-- 所有玩家都会执行到此，包括发送者自己
function Method2(index)
    print("--DouyinNetSample:收到 SendMessageToAll 消息 " .. index)
end
```

## 示例 C：`SendMessageToOthers` — 广播（不含自己）

```lua
local Input = UnityEngine.Input

function Update()
    if not DouyinNetService.isNetworkSettled then return end
    if Input.GetKeyDown("1") then
        SendMessageToOthersSample()
    end
end

function SendMessageToOthersSample()
    -- 本地立即处理
    Method3(3)
    -- 通知其他人做同样的处理
    print("--DouyinNetSample:发送消息除了自己外的其他玩家")
    self:SendMessageToOthers("Method3", 3)
end

function Method3(index)
    print("--DouyinNetSample:收到 SendMessageToOthers 消息 " .. index)
end
```

## 示例 D：`SendMessageToTarget` — 点对点消息

```lua
local Input = UnityEngine.Input
local anotherPlayerID -- 缓存的目标玩家 ID

function Update()
    if not DouyinNetService.isNetworkSettled then return end
    if Input.GetKeyDown("1") then
        SendMessageToTargetSample()
    end
end

function OnPlayerJoined(player, evt)
    -- 记录第一个进房的非本地玩家
    if player and not player.isLocal and not anotherPlayerID then
        anotherPlayerID = player.playerID
        print("--DouyinNetSample:UID=" .. anotherPlayerID)
    end
end

function SendMessageToTargetSample()
    local player = DouyinPlayerService.GetPlayer(anotherPlayerID)
    if not player then
        print("获取 player 失败: " .. tostring(anotherPlayerID))
        return
    end
    print("--DouyinNetSample:发送消息给指定玩家")
    self:SendMessageToTarget("Method4", player, 4)
end

function Method4(index)
    print("--DouyinNetSample:收到 SendMessageToTarget 消息 " .. index)
end
```

## 示例 E：`OwnerCall` — 通知主权方并拿到结果

```lua
local Input = UnityEngine.Input

function Update()
    if not DouyinNetService.isNetworkSettled then return end
    if Input.GetKeyDown("1") then
        OwnerCallSample()
    end
end

function OwnerCallSample()
    print("--DouyinNetSample:调用主权方的某个函数")
    -- 第二个参数是本地回调；第三个参数以后是要传给主权方的可变参数
    self:OwnerCall("Method5", function(result)
        if result then
            print("--DouyinNetSample:调用主权方的 Method5 成功: " .. tostring(result))
        else
            print("--DouyinNetSample:调用主权方的 Method5 失败")
        end
    end, 5)
end

-- 主权方执行，返回值会（尝试）回传给发起端的 onFinish
function Method5(index)
    if not self:HasOwnership() then return end
    print("--DouyinNetSample:收到 OwnerCall 消息 " .. index)
    return "Method5Success"
end
```

## 示例 F：`TargetCall` — 通知指定玩家并拿到结果

```lua
local Input = UnityEngine.Input
local anotherPlayerID

function Update()
    if not DouyinNetService.isNetworkSettled then return end
    if Input.GetKeyDown("1") then
        TargetCallSample()
    end
end

function OnPlayerJoined(player, evt)
    if player and not player.isLocal and not anotherPlayerID then
        anotherPlayerID = player.playerID
    end
end

function TargetCallSample()
    local player = DouyinPlayerService.GetPlayer(anotherPlayerID)
    if not player then
        print("获取 player 失败: " .. tostring(anotherPlayerID))
        return
    end
    print("--DouyinNetSample:调用某个玩家的某个函数")
    self:TargetCall("Method6", player, function()
        -- 注意：onFinish 不一定会触发
        print(string.format("--DouyinNetSample:调用 %s 的 Method6 成功", player.playerOpenID))
    end, 6)
end

-- 指定玩家执行
function Method6(index)
    print("--DouyinNetSample:收到 TargetCall 消息 " .. index)
    -- 也可 return，SDK 会尝试把返回值传回发起端的 onFinish
end
```
