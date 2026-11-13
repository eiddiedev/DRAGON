# 原生水域修复：公开能力边界与最小隔离实验

日期：2026-11-13。仅查阅当前安装的公开 CLI 指南、API 文档、已捕获的 Scene SDK Schema 及既有采样。本次未启动实例，未写主场景、未删触发器，未使用私有实现或 IPC。

## 结论

当前公开资料**不足以实现一个有依据的「自定义原生游泳 Volume」或「将 1744 个原生河道代理合并成少量 Volume」修复**。公开 `DouyinWaterArea` 白名单并未提供构造、字段、Volume 形状、注册或重建合同。普通 `triggerData` 是交互检测区域，不能据此认定它能触发原生游泳。

可以合法做的是：在隔离场景保留原生海/河作者节点及依赖，分别验证标准原生水体在**与失败版本相同的提审导出入口**上的行为；有明确碰撞配置错误时，只按公开 `physicsColliderData` / `triggerData` Schema 修正已证实的字段。不能把本地水体正常当作提审端正常，也不能把官方 API 查询缺失当作已确认的客户端平台故障。

## 已核对的公开合同

当前 `douyin-world --help` 报版本 `1.0.104`。`scene --help` 只列 import/remove/save/operation/cancel、environment get/set、player-animation clear，没有独立 water create/rebuild 命令。`guide prefab` 支持通用 Scene SDK 创建/复制/组件读写/归档；没有原生水域专用制作流程。`guide map` 的通用几何地图不能自动视为有游泳能力的原生水体。

| 来源 | 确认能力 | 不可由此推出 |
| --- | --- | --- |
| `hamlet-skill/references/api-whitelist.md:48` | `DouyinWaterArea` 是公开水域组件名称 | 没有 Volume、Trigger 网格密度、主动注册/重建的字段或方法文档；`DouyinWaterArea2` / Proxy 未列入此白名单 |
| `.../character-movement-flight-and-swimming.md:41–49` | 原生水域被动触发；可查询 `CanSwim()` / `IsSwimming()` 并监听开始/结束事件 | 不能 `StartSwim()`，不能靠播游泳动画或改浮力伪造原生状态；未公开房间/角色游泳开关的写入入口 |
| `prefab-edit/resources/model/components.md:15–38` | 实体碰撞、Trigger 分开；普通 Trigger 回调要求层及 Rigidbody 配合；带 Rigidbody 的 MeshCollider 要凸包 | 单个大凸包会填平弯曲河道凹口，不能保持岸线；实体 MeshCollider 不等于游泳体积 |
| 同上 `:57` 起的 Trigger 部分 | 独立 `triggerData`；box/sphere/capsule 按 Schema 保存；Trigger 不阻挡 | 添加普通 Trigger 不会自动获得原生水域语义；不能在河根增加 Box 就声称游泳修复 |
| `prefab-edit/editing/operations/nodes.md:76–90` | `nodes.clone` 复制所选根/后代，返回新 handles；资源共用，组件和参数独立 | 不承诺特定原生水域重建、源节点 ID 或快照重映射的细节；复制后仍须实际核对保存与导出 |
| 已捕获 `waterEditorData` Schema | Lake/River 类型、控制点/宽度/深度、地形关联、网格快照引用/校验等可写 | 没有 triggerDensity、triggerCount、nativeVolume、enableSwimming；不能杜撰字段，也不手写快照/CRC |
| 已捕获 `waterBodyAuthoringData` Schema | 仅 version / payloadJson / sourceRevision / derivedRevision | 未公开 payload 内部格式，不应编造 Volume JSON |

上列资料根：

`/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/dist/kit/references/skills/`

现有 Schema：`../schema.json`、`water-editor-schema.json`。

## 现有海河为什么不能互相直接替换

已有本地运行样本显示：海洋节点 `-2071044909` 生成 `DouyinWaterArea + Rigidbody + BoxCollider`；河道节点 `-1442080189` 生成 `DouyinWaterArea2 + Rigidbody + MeshCollider + RuntimeMarker`，加一组 **1744 个启用的 Proxy/MeshCollider Trigger**。已有入水样本中，海和河的 `IsSwimming` 都曾为 true。该样本不是用户失败的提审端采样。

保存数据中的 5 组 × 1744 个 Trigger 壳与运行时一组 1744 个启用组件，不是等价数量；不能按保存名字删除成「去重」。河道曲线有 13 个控制点，水面高差约 14.76 米。用一个水平大海盒覆盖整河会把高位岸边/桥面或低处空间错误纳入水域，不能保持既有行为。按弯道或高度分成几个盒子也需要公开原生水体创建与水面高度契约及岸线实测，现有资料没有这些保证。

单纯降低可视水面三角面、改 `riverDisplayData.meshParams` 的 `vertexDistance` 或改旧快照，都不能从公开资料证明会安全重建、减少原生代理；不应把 JSON 中存在某个私有参数当成公开制作方法。

## 最小合法隔离实验（尚未执行）

实验只在独立副本，所有包用同一当前导出路径、同一 iPhone、同一账号/房间条件；每包记录包哈希与版本。首次入水前不骑乘、不喝药、不进入战斗。

1. **A：已有原生海/河基线。** 保留当前作者海、河节点、地形及其真实依赖，在隔离副本停止无关玩法脚本；只挂只读的原生游泳状态/事件观测。正常走入海、河再走出。除少量诊断之外不要添加替代触发器或手动触发回调。
2. **B：标准原生水体对照。** 通过编辑器公开的原生水体工具在隔离副本创建一个最小标准水域。如果没有可确认的公开创建入口，就不伪造组件；可用 SDK `nodes.clone` 复制已有海节点作为「同源原生海模板」对照，但必须明确它并非全新标准水体。先保留原尺寸/几何/原生属性；复制后回读新节点及依赖并确认实际生成的原生组件。禁止仅创建名为 Sea 的普通水面模型。
3. **如需小范围海模板实验**，只对副本里实际返回的新 handles，用 `transforms` 和已有 `triggerData` Schema 缩放/调整；保持原生海类型、材质、所需 Rigidbody 与 Layer。先确认导出重载后水面和触发边界一致，不允许原来的巨大海 Trigger 干扰试验。这个实验只检验一个局部标准水段，不能直接替换整条河。
4. 每个测试点记录：刚入场、入水前、接触后、离开后 `CanSwim/IsSwimming` 和事件计数；另核对实际原生组件存在、有效 Collider 的 `enabled/isTrigger/attachedRigidbody`，以及脚下是水面实体还是河床。普通走入为验收依据；瞬移到水里仅可辅助定位。
5. 验收包含两岸、多段河道、桥面不误游泳、桥下入水、开船/下船、浅水与深水、重复进出、冷启动三次。先在隔离提审包成功，才评估主场景修复。

| 结果 | 下一步 |
| --- | --- |
| A 海正常、河失效，B 标准水域正常 | 集中核对当前河道快照/作者数据在提审导出时的恢复；在公开水体工具中对副本重建一小段河，再比较依赖/原生状态。不要用 A 海盒覆盖全河 |
| A 海河均失效、B 正常 | 核对旧作者节点的原生水体持久化和导出注册；保留最小差异作重建依据 |
| A 海河与 B 均失效 | 不能继续靠删河代理定位；需要当前提审端角色/房间状态及原生组件加载证据，向平台提供最小标准水域复现 |
| A 关玩法后正常、开玩法后失效 | 在副本二分脚本组；针对接管移动/碰撞/骑乘生命周期修复，保留原生水体 |

## 可以承诺与不能承诺的范围

- 可以按公开 Schema 修复**实测证实**的错误，例如水面被额外普通实体 Collider 阻挡、已保存原生海 Trigger 被禁用或尺寸错误；前提是识别正确节点，保留原生水体本身的碰撞/触发组件。
- 目前不能承诺以公开 API 将河道 1744 代理安全减少至某个数目。没有原生 Volume 合同与岸线等价验证之前，保留代理。
- 最新失败提审 ZIP/消费者运行日志仍欠缺。现有 `world_dev_unity_143175468-dsst-PROD.zip` 是旧包；其中河快照完整且 CRC 匹配，只能说明旧包未缺这项依赖。
- 本文给出的是实验与能力核查结果，不是已经完成的水域修复。
