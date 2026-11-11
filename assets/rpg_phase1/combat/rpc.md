# SendMessage (消息互通)

消息互通是指跨端直接互发事件指令的方式。这种方式具有更高的自由度，允许一次性传递多个参数，方便实现诸如“播放动作”、“触发特效”等一次性事件的同步。

## Lua 接口 (SendMessage)

在 Lua 中，消息互通主要通过 `DouyinScript` 提供的 `SendMessageTo*` 等接口完成：

| API | 说明 |
| --- | --- |
| `SendMessageToOwner(string method, ...)` | 向当前网络对象的主权方发送消息 |
| `SendMessageToAll(string method, ...)` | 向所有人发送消息（包括自己） |
| `SendMessageToTarget(string method, targetId, ...)` | 向特定的某个玩家客户端发送消息 |
| `SendMessageToOthers(string method, ...)` | 广播给除自己以外的所有在线玩家 |
| `SendMessageToServer(string method, ...)` | 仅发送给 DS 服务端 (DS 模式) |
| `OwnerCall(string method, onFinish, ...)` | 通知主权方，主权方 return 的结果会回传给 `onFinish` |
| `TargetCall(string method, target, onFinish, ...)`| 通知指定玩家，目标玩家 return 的结果会回传给 `onFinish` |

### 消息分派规则 (Lua)
- 发送时第一个参数 `method` 是字符串，接收端会在**同一份 DouyinScript** 中查找同名 `function`。
- 如果找不到该函数，**不会抛出异常（静默失败）**。
- 接收端的函数签名必须与发送端传递的可变参数一一对应。

### Lua 示例：通知所有人播放特效
**发送方逻辑：**
```lua
function PlayEffect()
    -- 通知所有人执行 PlayEffectRpc 方法，并传递参数
    self:SendMessageToAll("PlayEffectRpc", "FireEffect", 1.5)
end
```

**接收方逻辑（同一脚本中定义同名函数）：**
```lua
-- 自动响应收到的消息
function PlayEffectRpc(effectName, duration)
    print("收到播放特效通知:", effectName, duration)
    -- 执行播放特效的逻辑
end
```

## 参数限制与通用注意事项

- **支持的参数类型**：消息参数必须是基础数据类型（`int`, `float`, `string`, `bool` 等）。
- **复杂参数限制**：不支持传递复杂的 `table`，否则可能发生静默丢包。
- **不可靠性**：消息底层基于 UDP，存在丢包可能且**不保证送达**，新进房间的玩家也收不到之前发过的消息。如需强一致性请使用同步变量。
- **网络就绪前置**：如果 `isNetworkSettled` 还未变为 `true`，发出的消息会被系统静默丢弃。

## 常见坑点与避坑指南 (FAQ)

### 坑 1：`Awake / Start` 中直接调用静默失败
**现象**：脚本 `Start` 里立刻 `SendMessageToAll`，其他玩家没收到。
**原因**：`Start` 触发时网络环境未必就绪。
**修复**：所有网络 API 调用前必须查 `DouyinNetService.isNetworkSettled`。推荐将首次发起的时机放在 `OnNetworkSpawn` 之后。

### 坑 2：传递复杂参数
**现象**：接收端收到 `nil` 或发生序列化异常。
**原因**：消息参数仅支持基础类型。
**修复**：用多个基础类型参数分开传，或序列化为 JSON 字符串。

### 坑 3：`SendMessageToAll` 后本地立刻读出旧值
**现象**：广播消息，消息内部修改了状态，本地紧接着读取发现是旧值。
**原因**：广播是异步的，本地也要等网络消息回环才会执行。
**修复**：如果需要本地立刻响应，请拆分为：先直接调用本地函数处理，然后使用 `SendMessageToOthers` 通知其他人。

