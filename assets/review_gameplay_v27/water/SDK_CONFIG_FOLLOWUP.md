# 水域：补充 SDK 与保存/导出配置核对

本次仅阅读文档、保存文件与已有提审 ZIP，未开启实例、未操作触发器。新反馈是：全新进入、未骑过坐骑时，河道仍不能游泳；海面可以步行。因此坐骑停用恢复缺陷不能解释这次全新进入的复现。

## 公开接口的真实范围

当前安装公开文档：

- `skills/hamlet-skill/references/api-reference/DouyinActor/Methods/DouyinActor.CanSwim.md` 只提供 `public bool CanSwim()` 查询；没有 setter。
- `.../DouyinActor.IsSwimming.md` 只提供 `public bool IsSwimming()` 查询。
- `.../manual/01-core-system/player-network-objects/character-control/character-movement-flight-and-swimming.md` 明确：游泳由 SDK 水体被动触发；CanSwim 受房间设置、角色配置限制；业务不能主动开启。
- `.../coding-constraints-and-guidelines/character-control-development-constraints.md` 不允许调用不存在的 StartSwim；异常时检查房间及角色配置。
- 公开 waterEditorData schema 提供水体几何/快照/地形参数，`kind=2` 明确为 River；没有 enableSwimming/triggerEnabled。
- 当前公开 waterBodyAuthoringData schema 只公开 version/payloadJson/sourceRevision/derivedRevision；未公开 payload 内游泳权限结构。不能编造内部字段。

**文档没有说明 CanSwim 在入水前后的具体时序。** 已有本地真实样本在陆地是 false、入水后变 true 且 IsSwimming=true，因此不能单凭陆地 false 推断关闭了房间游泳权限。

## 海与河是不同保存和运行路径

| 项目 | 海洋 | 河道 |
| --- | --- | --- |
| 节点 | -2071044909 / 海洋 | -1442080189 / PCGRiverEditor |
| 保存结构 | waterDisplayData.waterType=1，Sea 标签 | waterEditorData.kind=2（River），Untagged 标签 |
| 保存碰撞 | physicsColliderData=null；一个 enabled Box Trigger | physicsColliderData=null；根 triggerData=[] |
| 几何来源 | waterDisplayData 的 meshRefId | 13 个控制点、19.6 宽、3 深与 editor_water 网格快照 |
| 既有本地运行组件 | DouyinWaterArea + Rigidbody + BoxCollider | DouyinWaterArea2 + Rigidbody + MeshCollider + PCGRiverRuntimeMarker，并生成 1744 个 Proxy/MeshCollider Trigger |
| 既有本地测试 | (245,26.616,50) 时 IsSwimming=true | (97.715,29.744,136.268) 时 IsSwimming=true |

上述水体 `waterType`、`waterEditorData.kind`、`waterAppearanceData.displayType` 属于不同字段/枚举，不能相互套用数值。海洋的显示类型和海洋节点名不等于存在一个通用可写“游泳类型”。

## room / character 数据核查结果

核查三份数据：当前正式磁盘 scene.data、仓库 editor_project 的 scene.data、已提供的 `world_dev_unity_143175468-dsst-PROD.zip`（场景时间 2026-11-13 10:57:44）。

- 三份场景都有 moveMaxSpeed=4、jumpMaxHeight=1、playerAnimatorData=null、isOpenStreamingLoad=true；没有 CanSwim/swimming 开关字段。
- 所查 ZIP 没有独立 room/character config 或 manifest；顶层唯一 JSON 是 SerializePcgData.json。无法由这个资源 ZIP 断言审核房间/角色的实际服务端配置。
- 当前保存与该旧 ZIP 的海、河 basic/landscape/physics 内容一致；不是本轮修改把海和河换成不同水体。
- 海和河的 waterBodyAuthoringData 都为 null；waterNetworks 和 waterTerrainBaselines 都为空。这些相同数据在本地海/河能正常游泳，故它们不能单独作为“漏配”的证据。
- 河道快照在旧 ZIP 中存在，348,213 字节，CRC32 2425906157 与 envelope 和 ZIP entry 均一致。其 5 组序列化 Trigger 子树每组 1744 项没有保存有效碰撞组件；它们依赖消费者重建，不能从空壳数量推断注册正常，也不能盲删。
- 本次没有拿到**用户实际复现失败的最新提审 ZIP**。Downloads 里最新仍是上面这份 dsst 旧包；最新消费者房间/角色配置、原生水体组件与加载日志均缺失。

## 可行动的下一步

1. 先核对实际失败版本的最新 ZIP，复用 audit_review_water.py 校验海/河节点、快照及场景版本；不要把旧包与新二维码混为一份。
2. 在消费者失败水段采集 CanSwim/IsSwimming/onSwimStart，以及实际存在的原生海洋 DouyinWaterArea、河道 DouyinWaterArea2/Proxy 和 Collider.isTrigger/enabled。应在接触水域后记录，不能只采陆地状态。
3. 对“海面行走”额外记录脚下实际支撑 Collider 的名字、isTrigger、enabled、位置；这能区分海面被当实体碰撞与踩在浅处地形。截图/描述本身不能决定是哪一种。
4. 若最新包与当前保存一致而消费者缺少原生水域或角色能力不同，将旧/新包、两个水体 ID、河快照 CRC、本地/消费者状态对照交给平台核查；没有公开 SDK 依据可以安全通过业务脚本强开游泳。

当前结论是已经缩小到消费者水域重建/角色房间状态的证据缺口，**未确认根因，也未宣称游泳已修复**。
