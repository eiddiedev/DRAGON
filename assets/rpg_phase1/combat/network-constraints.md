# 多人游戏与网络开发约束

## 1. 概念 (Concept)
在多人网络游戏中，状态的同步与指令的下发是核心。引擎提供 同步变量 和 RPC（远程过程调用）用于端到端的通信。

## 2. 边界 (Boundary)
- **主权写入限制**：同步变量（C# `NetworkVariable` / Lua `---@varSync`）只能由**主权方 (Owner)** 写入。非主权方写入会被系统**静默忽略**。
- **就绪时机 (Network Settled)**：在 `isNetworkSettled` 变为 `true` 之前，或在 `OnNetSpawned` / `OnNetworkSpawn` 回调触发之前，禁止强读同步变量或发送跨端 RPC。同步变量的初始值不会触发 `OnValueChange` 回调，需在初始化时手动读取一次。
- **RPC 参数类型限制**：RPC 通信的参数只支持**基础数据类型**。不支持 Lua 的 `table`、C# 的自定义 `class`、`List` 或 `Dictionary` 等复杂容器。如果需要跨端传递复杂数据，请拆分为多个基础类型，或序列化为 JSON 字符串。
- **同步变量类型支持差异**：
  - Lua 与 C# 支持的基础类型基本一致，但 **C# 不支持结构体 (struct) 或复杂的自定义类**。
  - 在集合同步变量中，C# 的 `NetworkList<T>` **不支持 `bool`**，`NetworkDictionary<K, V>` 的键 **不支持 `byte` 和 `short`**。

## 3. 机制与规范 (Mechanism & Specification)
- **网络对象的生命周期约束**：
  - 动态网络对象只能使用 `NetSpawn`（或 `ServerSpawn`）等专用接口创建，销毁必须使用 `NetDestroy`（或 `ServerDestroy`）。**严禁使用 Unity 原生 `Destroy`**。
  - C# 的 `NetSpawn` 是同步返回 GameObject 的，而不是基于回调。
  - `NetSpawn` 第一个参数必须是在资产列表中注册过的 `key` 字符串。
- **同步变量的有效值窗口**：
  - `Awake / Start` 阶段（未就绪）：可以读值，但值可能尚未从服务端同步，**读取到的值不可靠**；禁止在此阶段写入。
  - `NetSpawn` 动态对象回调：此为专属赋值窗口，可以在回调中给同步变量赋初始值。
  - `OnNetSpawned` 到 `OnNetDestroy` 阶段：这是同步变量的**唯一有效值窗口**。在此阶段内读写稳定有效。

## 4. 黄金法则与避坑指南 (Golden Rules & Pitfalls)
- **💡 黄金法则：RPC 与同步变量选型**
  - **需要确保可靠同步的持续状态**（如生命值、得分、位置）：用**同步变量**，配合 `OnValueChange`。
  - **只需一次性通知副作用**（如播放特效、弹窗）：用 **RPC 通信**。
- **🚫 避坑：RPC 通信非可靠性**
  所有 RPC（包括 C# `[Rpc]`、`DouyinRemoteEvent`、Lua `SendMessageTo*`）**均不保证送达、不保证回调**。禁止把 RPC 当作可靠数据通道。
- **🚫 避坑：非主权方写入静默失败**
  非主权方调用赋值接口“表面上没写进去”是因为 SDK 会自动忽略非主权方的写入。如果非主权方需要修改，必须通过 RPC 将请求**转发给主权方**，且主权方在实际执行赋值前必须**再判一次主权**（防范 RPC 回程期间主权已迁移）。
- **💡 黄金法则：主权申请固定判定顺序**
  在修改网络对象前申请主权时，必须严格遵守 `isNetworkSettled` → `HasOwnership` → `RequestOwnership` 的判定顺序。
  - `isNetworkSettled` 是唯一总闸，网络未就绪时调用主权 API 会抛出异常。
  - 申请回调中只有成功才可执行修改业务，失败或被拒绝时必须直接结束，严禁兜底执行。
