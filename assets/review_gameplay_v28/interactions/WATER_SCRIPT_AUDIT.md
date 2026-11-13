# v28：脚本物理范围与开场清理审计

依据为正式工程 `project-55a43370-8734-4825-92a8-b0de824a45e2/scene.data` 内 38 项 runtimeScripts。outfits、weapons、bridge 的当前磁盘源与场景内 content 逐字相同。没有启动实例、修改正式/隔离工程或水域。

## 可独立修复的两项缺陷

1. `dragon_outfits.lua` 的 Start 原先递归关闭整个 `runtimeScope:GetResourceRoot()` 的 Collider；该 scope 本次是带 resource-root-bootstrap 的 DragonRPG（节点 66338468），含 664 个节点，其中 SourceSets 仅 150 个。其他 514 个含武器、影灵源、书、麦簇等，超出服装职责。候选只去掉整个 resourceRoot 的关闭，保留 SourceSets 及自产服装克隆。真正的海洋、PCGRiverEditor 及其触发器不在 DragonRPG 后代，因此**该越权缺陷不能被宣称为此次未骑乘游泳失败的原因**。

2. `dragon_world_bridge.lua` 原先 UI.camStart 禁用捕获的主相机，UI.lockPlayer 锁摇杆；正常结束和 UI.update 抛错路径有 camEnd/解锁，但 OnDisable/OnDestroy 链没有释放标题相机或 UI 输入。候选加入本模块输入 lease 与一次性相机清理；无持有记录不解锁，已有骑乘、飞行、龙、船父节点接管、战斗参与/准备时交由对方控制器处理。保持原剧情、画面、按钮和水域规则。

官方 `角色移动、飞行与游泳` 文档明确 Immobilize 只控制摇杆输入，不改变重力和碰撞。所以开场锁清理缺失可能导致“不能动/主相机未恢复”，不能解释“仍能行走但不进入游泳”。

## 已核实的其它 Collider 写入范围

- 马、飞毯：仅 OnSeatEntered 捕获并关闭该 actor 根 Collider；未乘坐不会执行。船仅点击开船后执行。退出恢复捕获原值。没有 Start/Update 默认关闭玩家 Collider。
- sheep motion：只修改 self Rigidbody 和 self CapsuleCollider；不存在 player Rigidbody 修改。
- combat：仅新生成的敌人克隆关闭 Collider，战斗用解析命中；仅实际战斗成员边界 Teleport，非成员不执行。
- exploration：变羊视觉克隆关闭自身 Collider/重力，不更改演员 Collider；药水缩放由 actor.scale 实现。
- weapons：只关闭新生成武器克隆 Collider。
- bridge：仅 dragon_v8_live rig、显式 pl_tree_* 对象的 Leaves 子树、显式 golden_geometry_* 麦簇、自产 Quad、六个指定城堡门头装饰。城堡装饰循环还明确跳过 isTrigger。没有全场 Collider 清理。
- bridge sharedMesh 修改是旧风车几何分离路径，目标为风车自己的 MeshFilter/MeshCollider，不是原生地形或河道。
- official geometry/containment 仅查询 Collider；official interaction/trigger 只缩放调用方传入的 BoxCollider。没有全局 Physics/IgnoreLayerCollision/queriesHitTriggers/layer 写入。

在所有场景登记脚本中未发现主动写游泳能力、水域注册，或调用 StartFly/StopFly/SetFlyMode。战斗只暂时 DisableFly，结束恢复原 CanFly 权限。未发现审核加载超时兜底关闭水域或碰撞。

## RuntimeScope 核对

平台 scope.from 先取对象缓存，否则向上寻找最近 resource/host bootstrap marker；没有 marker 返回 nil，并不存在自动兜底整个 scene。正式 DragonRPG 自己带 resource marker，河/海属于其它地图分支。Consumer 是否实际保留相同 runtime 层级需真实运行证据，不能由预览成功推定，也不能先假设其 scope 必定扩大。

## createWLRD 对照

`authoring/forest-reentry-audit/scene-scripts/36a0d6b8-55ee-434f-ae5a-a9d3ba51a3e2.lua` 也有 disableCollidersOn(resourceRoot)，说明宽范围代码来自参考服装实现，而不是“该项目能显示动态模型”就能证明此写法适于混合 scope。

参考 runtime-host `964153e6-4611-4f70-9d53-d29ebf5bf52c.lua` 明确清理 StopMove/Immobilize(false)/角色参数，并在禁止飞行前 StopFly。当前龙眠没有主动 StartFly，因此不存在必须猜测补 StopFly 的证据。参考项目未发现能直接复用的游泳实现；游泳仍依赖 SDK 原生水域。

## 文件与测试

- `dragon_outfits.lua`、`outfit-collider-ownership.patch`
- `dragon_world_bridge.lua`、`presentation-lifecycle.patch`
- `test_collider_ownership.py`：执行真实 Lua Start/clone helper；当前 saved tree 确认限定 150 个服装节点，514 个其它玩法及 9 个水域节点不触碰。
- `test_presentation_lifecycle.py`：正常结束、异常 OnDisable 后 OnDestroy、重复清理、无 lease、原禁用主相机、骑乘/飞行/龙/船/战斗/准备接管均通过。

上述是源码控制流和范围测试，不是手机原生 Trigger/Proxy 注册或游泳验收；水域问题需要继续沿平台水体生成、流式加载和 Consumer 进入/退出事件核验。没有使用透明地板或强制游泳动画冒充修复。
