---
title: Network Design — 通用入口
description: 本文档汇总了网络同步的核心概念与开发约束，并提供详细文档的索引
---

## 适用场景（什么时候读这个文件）

- 判断当前玩法该使用 SharedMode 还是 DedicatedServer 的网络模型
- 编写跨端一致性、晚进房同步、断线重连和全局管理器逻辑
- 使用动态网络对象、同步变量、RPC / 远程通信前确认规则
- 判断网络对象生命周期、销毁责任、主权写入和网络就绪时机
- 排查同步不生效、消息丢包、对象重复生成、管理器归属错误等网络问题

---

## 文档索引（以此表为准）

匹配到相关功能时，**必须先完整读取对应的参考文档**再开始编码。严禁凭记忆或拼凑现有 Demo 调用 API。

「模式」列说明文档适用的网络架构：`SharedMode` 只在 SharedMode 项目读取，`DS` 只在 DedicatedServer 项目读取，`通用` 两种架构都要按需读取；当前项目架构在 hamlet-preferences.md 已固定，不要读另一架构的文档以免用错 API。

| 资料 | 模式 | 路径 | 什么时候读 |
|---|---|---|---|
| 网络概述 | 通用 | [网络概述.md](../../references/manual/04-multiplayer-and-network/network-overview.md) | 了解 Douyin World 多人游戏三大板块（网络模型、网络基础、数据通信）的入口。漏读易犯：缺乏全局网络视野，不知道查什么资料。 |
| 网络模型总览 | 通用 | [网络模型概述.md](../../references/manual/04-multiplayer-and-network/network-models/network-models-overview.md) | 在项目初期决定使用单机、Shared Mode 还是 DS 模式时读。漏读易犯：选错模型导致后期需重构 30%-50% 代码。 |
| Single Player 架构总览 | 通用 | [网络模型-Single Player.md](../../references/manual/04-multiplayer-and-network/network-models/network-model-single-player.md) | 制作纯单机体验、个人空间且无需多人同步时读。 |
| SharedMode 架构总览 | SharedMode | [网络模型-Shared Mode.md](../../references/manual/04-multiplayer-and-network/network-models/network-model-shared-mode.md) | SharedMode 项目写网络同步代码前读。它解释分布式架构、主权分配、断线迁移和分布式管理器实践。漏读易犯：误以为存在权威服务端、把中心化管理器套进 SharedMode、忽视主权转移。 |
| DedicatedServer 架构总览 | DS | [网络模型-Dedicated Server.md](../../references/manual/04-multiplayer-and-network/network-models/network-model-dedicated-server.md) | DS 项目写网络同步代码前读。它解释中心化架构、服务端权威、客户端 / 服务端职责划分。漏读易犯：在客户端直接写权威逻辑，或把 SharedMode 语义套到 DS。 |
| SharedMode 升级 DS 指南 | DS | [SharedMode 模式升级到Dedicated Server模式.md](../../references/manual/04-multiplayer-and-network/network-models/upgrade-shared-mode-to-dedicated-server.md) | 将 Shared Mode 项目迁移至 DS 模式时读。漏读易犯：逻辑未分层、存储未迁移导致运行错误。 |
| 分布式与中心化管理器 | 通用 | [分布式网络对象管理器.md](../../references/best-practice/network-object-management/distributed-network-object-manager.md) | 判断全局管理器在当前架构下该挂在哪、由谁执行时读。漏读易犯：管理器归属模式选错，断线迁移或权限逻辑错乱。 |
| 主权与控制权 | 通用 | [主权与控制权.md](../../references/manual/04-multiplayer-and-network/networking-basics/ownership-and-controllership.md) | 写任何修改网络状态（如写入同步变量、处理主权转移）的代码前读。漏读易犯：非主权方写入静默失败、在 Awake 中判定主权、缓存权限状态。 |
| 网络对象总览 | 通用 | [网络对象的动态创建.md](../../references/manual/04-multiplayer-and-network/networking-basics/network-object-dynamic-creation.md) | 写任何 `NetSpawn` / `NetDestroy` / `ServerSpawn` 动态创建代码前读。它解释静态 / 动态、房间级 / 玩家绑定对象的分类与销毁语义。漏读易犯：房间对象反复生成堆积，或把玩家绑定对象当房间对象管理。 |
| 同步变量规则 | 通用 | [同步变量.md](../../references/manual/04-multiplayer-and-network/data-and-communication/synchronized-variables.md) | 声明或读写任何同步变量前读。它解释类型限制、主权驱动写入、变化事件时序、有效值窗口和数据三阶段模型。漏读易犯：网络生成前读到默认值，或非主权方写入被忽略。 |
| RPC 通信规则 | 通用 | [RPC 概述.md](../../references/manual/04-multiplayer-and-network/data-and-communication/rpc/rpc-overview.md) | 写任何消息 / RPC / DS 远程通信前读。它解释可靠性、参数类型限制、网络就绪前置和 RPC vs 同步变量的选型。漏读易犯：把 RPC 当可靠通道，或传复杂结构导致静默丢包。 |
| SendMessage 互通规则 | 通用 | [SendMessage.md](../../references/manual/04-multiplayer-and-network/data-and-communication/rpc/sendmessage.md) | 写跨端互发事件指令时读。漏读易犯：传递复杂类型静默丢包、未判断网络就绪调用失效。 |
| RemoteEvent 单向通信 | DS | [RemoteEvent.md](../../references/manual/04-multiplayer-and-network/data-and-communication/rpc/remoteevent.md) | DS 模式下写客户端与服务端异步单向通信时读。漏读易犯：通道名不匹配、把服务端当真实玩家处理。 |
| RemoteFunction 双向通信 | DS | [RemoteFunction.md](../../references/manual/04-multiplayer-and-network/data-and-communication/rpc/remotefunction.md) | DS 模式下写客户端与服务端异步双向通信时读。漏读易犯：误以为响应回调必定触发，或过度依赖回调传递关键数据。 |
| 断线重连 | 通用 | [断线重连机制.md](../../references/manual/04-multiplayer-and-network/networking-basics/disconnect-and-reconnect.md) | 做重连容错、对象重复触发和状态恢复时读。漏读易犯：断线后状态恢复不完整，或重连后重复生成 / 重复结算。 |

