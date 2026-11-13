# 影灵黑粉大方块及重复模型

## 证据

用户截图 `/Users/bytedance/Downloads/截屏 2026-11-13 15.40.15.png` 中，黑色方块与粉色边正好对应旧 `dragon_combat.lua` 的 `HealthTrack` / `HealthFill` 配色。

旧路径：

1. `Spawn.spawn` 生成影灵。
2. 创建两个默认 1×1×1 的 Cube 并给它们黑色、粉色材质。
3. 无保护地读取 `CS.ModularAnim.Runtime.UGCAnimator`，随后才把影灵登记进 `visuals[e.id]`。
4. 待后面的更新阶段才把两个 Cube 缩成很薄的血条。

在 2～3 步之间的任意异常，会留下未登记、不能正常清理的模型和默认大 Cube。下次同步仍认为该影灵没创建，每 0.5 秒重试，最多 10 次。敌方权威位置继续变化时，这些遗留模型就会沿移动路径形成一排。

实际 Lua 注入测试在旧动画查询处抛错：12 次同步产生 **10 个孤儿影灵、20 个默认 Cube**，`visuals` 始终为空。新代码同样异常只保留 **1 个登记且可见的影灵、0 个 Cube**。这证明旧代码存在该异常放大路径；目前没有手机异常堆栈，不能断言真实设备失败的就是 UGCAnimator API，也不能声称该 API 本身不受平台支持。

源场景只有一个 `ShadowSpiritSource`（ID `-293511830`），它直接包含一个 `ShadowSpiritRig`，并非一排怪物模板。正式战斗规则仍为三幕 4、5、3 只；补丁不改这一规则。

## 补丁范围

`patch_enemy.py::patch(source)` 仅替换 `clearVisuals` 到 `syncVisuals` 的敌方显示与创建部分。

- Spawn 返回后立刻登记所有权，再执行可选组件工作。
- 核心设置失败先关闭、销毁该实例再允许有限重试，不留孤儿。
- 动画查询/播放、血条 UI 独立处理异常，不能打断整个生成循环或伤害事件消费。
- 血条换成 WorldSpace Canvas 的两张 Image。无 Primitive Cube、无碰撞体、不再复制怪物 shader；即使 UI 准备失败也不留下黑粉几何体。
- 保留原来的分析型受击/碰撞逻辑、朝向修正、怪物缩放、骨骼攻击、技能事件、奖励与网络同步。
- 未扫场景乱删名称相似的模型。旧运行中的孤儿不会被新代码追删，因此需重新开始一次预览/世界使旧实例销毁。

`GetShadowVisualDiagnostics()` 提供 expected、owned、visible、created、destroyed、setupFailures、healthFailures、animationFailures 和最近错误。注意 owned 可包含之前幕次已死亡、隐藏的缓存模型；验收应主要比较 active encounter 的 visible 与 expected，并核对实际层级不存在孤儿。

## 验证

`python3 assets/review_gameplay_v27/enemy/test_enemy.py` 共 12 项通过：旧缺陷复现、可选动画查询失败、播放失败、血条失败、核心失败清理、HP 更新、死亡/清理、第一幕始终 4 怪、完整 Lua 编译，以及核心规则/网络/动作事件/奖励区字节不变。

候选未写主工程，未操作任何实例。下一步需 root 合并后开启新战斗，检查实际血条尺寸和朝向、三幕怪数、攻击动作与受击，然后用审核包再验证一次。手机异常堆栈及 C 端完整运行仍未验收。
