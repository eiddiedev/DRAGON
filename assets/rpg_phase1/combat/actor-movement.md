---
title: Movement Design — Lua 版本
language: lua
description: 本文档汇总使用 Lua 实现玩家 Actor 原生移动的相关说明与代码示例索引。
---

## 适用场景（什么时候读这个文件）

用 Lua 写玩家 Actor 原生移动代码时，遇到以下场景读本文件：

- 调整玩家速度：加速带、冰面、泥潭、疾跑、缓行
- 程序化控制本地玩家：持续移动、停止移动、禁止摇杆、跳跃、传送
- 开启 / 禁止飞行，切换正常飞行 / 悬浮，监听飞行开始 / 结束
- 判断游泳状态或监听进入 / 退出游泳
- 排查“改远端玩家无效”“速度还原不对”“MoveContinuously 后一直漂移”等问题

---

## 文档索引（以此表为准）

确定所需功能后，**必须先完整读取对应的参考文档**再开始编码。严禁凭记忆或拼凑现有 Demo 调用 API。

| 资料 | 路径 | 什么时候读 |
|---|---|---|
| 基础移动-Lua | [基础移动-Lua.md](../../references/best-practice/movement/basic-movement-lua.md) | 地面移动、速度控制、持续移动、禁摇杆、跳跃、传送和变速道具的完整写法。写加速带、泥潭、冰面、疾跑、强制移动、剧情锁定或瞬移时读。漏读易犯：改远端无效、`MoveContinuously` 后不停止、用 `transform.position` 强改位置、变速没有对称还原。 |
| 飞行-Lua | [飞行-Lua.md](../../references/best-practice/movement/flying-lua.md) | 玩家原生飞行 / 悬浮的权限开关、状态触发、模式切换、参数调整和事件监听。写区域飞行、按钮起飞、悬浮、座位禁飞 / 恢复飞行时读。漏读易犯：把 `DisableFly` 当作强制落地、不查 `CanFly` 直接起飞、`EnableFly` / `DisableFly` 不配对。 |
| 游泳-Lua | [游泳-Lua.md](../../references/best-practice/movement/swimming-lua.md) | 游泳能力查询、游泳状态查询和进入 / 退出事件监听。写水域状态、游泳禁拾取、游泳禁飞 / 恢复飞行时读。漏读易犯：寻找不存在的 `StartSwim` 或游泳速度 API，或只在按钮显示阶段拦截、没有在实际拾取 / 飞行恢复处做互斥。 |

