# 河道游泳：脚本层只读审计与坐骑生命周期候选

检查依据：当前 `editor_project/project_lapv8fm0/scene.data` 的 38 项脚本登记、25 个实际启用绑定脚本，以及 v27 候选。只分析公开项目源码，未操作实例、未改变河道或触发器。

## 已排除的直接路径

- 实际绑定脚本没有读写 `CanSwim`、`IsSwimming`、Start/StopSwim、`DouyinWaterArea`、`PCGRiver` 的业务路径，也没有修改 `Physics.queriesHitTriggers`、IgnoreLayerCollision 或 Collider.layer。
- 未发现“扫描全场所有 Collider 后删除/关闭”代码。没有按 `__DouyinWaterArea2Triggers` 或 Trigger 名称清理水域。
- `dragon_outfits.lua:962` 的 `disableCollidersOn(resourceRoot)` 虽然范围较宽，但本次保存的 Resource Scope 根是 `-1471846761 / 龙眠审核加载修复v25`。原生河道 `-1442080189 / PCGRiverEditor` 属于独立的 `地图/地形/水体` 层级，不是该资源根后代。故这条调用不覆盖本次河道。
- `dragon_world_bridge.lua:1448` 仅关闭龙 rig 子树 Collider；`:1993` 仅关闭选定树的 `Leaves` 子树 Collider；`:2039` 仅关闭选定麦田模型子树 Collider；`:3920` 仅处理六个指定城堡饰件，且明确跳过 Trigger。它们没有包含原生河道。
- v24/v26 画质、草地纹理、启动等待代码只改渲染/材质/UI，未发现它们禁用原生水域注册或碰撞。

这只能排除检查到的项目源码直接清理水域，不足以证明消费者正确加载/重建了平台的原生河道触发器。

## 已证实、可独立修的缺陷

三种坐骑均捕获并关闭**玩家根 Collider**：

- 马 `prefab_14/horse_seat_v1.lua:123–125`，正常退出 `:133–144` 恢复，但 v26 没有 `OnDisable`。
- 飞毯 `prefab_14/scene_vehicle_carpet.lua:80–82`，正常退出 `:90–103` 恢复，但 v26 没有 `OnDisable`。
- 船 `scripts/scene_vehicle_boat.lua:55–58`，`leave():25–33` 恢复，但只从按钮和 `OnDestroy` 调用，没有 `OnDisable`。

因此如果坐骑脚本被停用、但没有销毁或正常下马/下船，已经接管的玩家 Collider 会继续关闭。该代码缺口可通过生命周期测试复现。它可能影响后续角色触发感知，但**没有证据说明用户本次河道失败正是这条路径**。此前同一本地场景已经实测原生 `IsSwimming=true`；也不能把在陆地读到的 `CanSwim=false` 当作游泳权限被关闭。

## 候选与测试

- `horse_seat_v1.lua`：已在候选中加入停用时释放骑乘；保留动画修复及原骑马移动逻辑。
- `boat-lifecycle.patch`、`carpet-lifecycle.patch`：独立补丁，未套入主工程。
- 各 Collider 恢复捕获的原值；原本 disabled 的保持 disabled；未接管的 Collider 不处理。一个已销毁 Collider 不阻断其他恢复。恢复捕获的父节点与缩放。
- StandUp 同步回调、延迟回调、调用抛错均能清理；同一次骑乘的重复退出回调不再次传送；原生 StandUp 如果抛错，只能保证脚本接管状态归还，不能声称原生坐姿状态也已成功退出。
- `test_vehicle_lifecycle.py`：7 组候选测试通过，同时 v26 三脚本都重现缺少 OnDisable；`test_actors.py` 的既有动画与羊落地检查仍通过。

## 下一步取证

在最新提审包确认版本后，分别测试“直接步行入河”与“完成一次骑乘/下马后入河”，记录玩家根 Collider 的 enabled 原值/现值、IsSitting、IsFlying、IsSwimming 以及本次坐骑停用日志。若直接步行也失败，就不能由本次坐骑修复宣称解决河道；继续对照最新 ZIP 河道快照及消费者实际原生 Trigger/Proxy 是否注册。不要添加透明碰撞箱或强制游泳动画代替原生水域。
