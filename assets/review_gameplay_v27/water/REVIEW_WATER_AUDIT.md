# 河道提审不游泳：只读审计

## 结论

暂未找到可以证实并安全落地的水体配置修复。不能把本地 `IsSwimming=true` 写成提审已修复，也不能因为 ZIP 里有 Trigger 名称便认为 C 端已有正确的原生水域注册。

本次输入的 `world_dev_unity_143175468-dsst-PROD.zip` 是先前提供的旧包，**不是用户最新出问题的 v26 提审包**。它只能用于分析旧导出结构；最新包与当前消费者运行日志缺失仍是明确的证据缺口。

## 可复查事实

- 旧 ZIP 为 123,746,748 字节。`SerializePcgData.json` 包内时间 2026-11-13 10:57:44，`isOpenStreamingLoad=true`。
- 河道节点 `-1442080189 / PCGRiverEditor` 与当前保存节点快照的 `basic`、`landscape`、`physics` 完全相同；海洋节点也相同。
- 河道包含 13 个控制点，引用地形 `3193404` 存在，`waterEditorData` 版本 2、类型 River，宽度 19.6、深度 3，网格快照版本 1。
- `editor_water/-1442080189_river_mesh.bin` 实际存在，348,213 字节；CRC32 `2425906157` 同时匹配 `waterEditorData.editorMeshSnapshotChecksum` 和 ZIP entry CRC。没有发现这份旧包河道网格快照漏打包或损坏的证据。
- 旧包含 5 组、每组 1,744 个 `__DouyinWaterArea2Triggers / Trigger_*` 子节点，但这些子节点只有 basic 与空 physics，`physicsColliderData=null`、`triggerData=[]`，没有持久化原生游泳 Proxy。它们是序列化空壳，不能单凭它们证明手机游泳会注册。没有修改或删除这些节点。
- root 提供的同一保存场景本地运行探针显示，平台实际重建了一组 1,744 个有效 MeshCollider/`DouyinWaterArea2TriggerProxy`；在河中测试点 `97.715,29.744,136.268`，后续九次 `IsSwimming=true`。这证明本地重建路径可工作，仍不能证明审核消费者的重建路径也正常。
- 旧 JSON 未出现 `riverExportRuntime` 字符串；当前保存的河道 `editorOnlyData.editorData` 也为空。本地组件却出现 `PCGRiverExportMarker` / `PCGRiverRuntimeMarker`。这说明 marker 至少不是这个 JSON 里的直接同名字段；其字符串缺失本身不是配置缺失的证据。

完整字段比较和校验数据：`review-zip-audit.json`，可运行 `audit_review_water.py <最新提审ZIP>` 重算。

## 公开能力边界

读取了当前公开 Scene SDK 的 `waterEditorData` schema（`water-editor-schema.json`）和 `waterBodyAuthoringData` schema（父目录 `schema.json`）：

- `waterEditorData` 可写字段是控制点、中心、缩放、宽度、深度、快照引用、地形追踪等，没有 `enableSwimming`、`triggerEnabled` 或主动重建原生游泳组件的开关。
- `waterBodyAuthoringData` 仅公开 envelope：version、payloadJson、sourceRevision、derivedRevision。payloadJson 内部结构不在当前 schema 合同中，不能编造键值来伪造新水体配置。
- 官方角色移动文档明确游泳由 SDK 水体被动触发；只有 CanSwim、IsSwimming、onSwimStart/onSwimStop，不允许业务主动 StartSwim。
- API 白名单列出 `DouyinWaterArea`，未提供本次河流的 `DouyinWaterArea2` / Proxy 注册方法。未调用内部服务、反射或未知 API。

`riverDisplayData.meshParams.width=4` 而 `waterEditorData.riverWidth=19.6` 是旧源中的表面不一致，但同一数据在本地可游泳，网格快照也完整；没有证据说明消费者实际使用哪一个生成触发器。因此本轮没有将其擅自统一或重建岸线。

## 下一步最小取证

1. 对用户实际失败的最新提审 ZIP 运行同一审计，确认其场景与本轮准备提交版本一致。
2. 在手机失败河段记录 actor.CanSwim/IsSwimming 及平台加载错误；若 CanSwim=false，要分清角色/房间能力与水体注册。若可见水面、CanSwim允许、没有游泳进入事件，重点核对消费者是否按快照生成原生河道 trigger/proxy。
3. 若最新包仍为同配置且消费者没有原生河道组件，向平台提供这两个节点、快照引用和 CRC，以及桌面成功/手机失败对照，而不是添加普通透明碰撞箱或假游泳动作来掩盖。

本调查未操作任何运行实例、未保存工程、未改动水域和现有玩法。
