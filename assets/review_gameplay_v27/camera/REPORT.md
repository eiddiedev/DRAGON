# 游览相机下钻与夜间云片候选

仅新增候选文件，未写正式工程、隔离工程或操作 CLI 实例。

## 相机证据与修复边界

- 手机截图 `/Users/bytedance/Downloads/截屏 2026-11-13 15.30.12.png` 显示地表背面剔除、树根及模型底部，符合镜头进入地形下方；不是应该给全地形开启双面的纹理故障。
- v26/v27 bridge 普通游览没有俯仰下限；出生设为 -11°。`LateUpdate()` 仅处理骑龙与眩晕。场景数据未发现独立相机碰撞/最小俯仰配置。
- 当前公开 `DouyinCameraService` 仅有相机 getter、Pitch/Yaw/Distance/Offset 与拍照模式，未公开碰撞开关。公开 camera-view-control.md 表明正 pitch 更偏俯视，所有业务干预应经过 CameraService，不能抢写 Camera.main transform。
- 候选限制**普通游览** `pitch >= 0°`。只在实际越过下限时调用 `SetPitch(0)`，既不持续强制回正，也不改 yaw、距离、FOV、offset、矩阵。水平以上的画面仍有相机视野，但不能再把轨道眼点向下绕到角色目标点下方。
- 跳过开场、古书、地图、弹出菜单、出生相机过渡、骑乘/飞行/游泳、唤龙、拍照、战斗、药水、蘑菇状态与震屏。脚本依赖独立缓存、最多 30 次解析；缺失时不抢镜头，诊断返回 dependencies。
- 这是极端仰视的限制性修复，**不是完整地形或建筑物碰撞解算**。陡坡、墙体遮挡仍须实测；不得宣称所有穿透问题已解决。若需要保持任意仰视同时自动缩短距离，应等待公开碰撞入口或单独设计并验证地形探测，不叠加另一个世界相机。

## 云片证据与删除

`updateClouds()` 首帧只 `GameObject.Find("cl_"..i)` 一次，把当时存在的 16 片云挂到 `cloud_pivot`。流式后到的对象仍在场景根节点，漏过昼夜父节点显隐，这与夜里仍出现白云相符。实际晚到时序尚未在审核设备捕获，故这是代码风险和与现象相符的解释。

用户已要求删除云片。`cloud-nodes.json` 同时列出 v26 与 v27 的精确节点 ID。删除清单为 16 个 **cl_0..cl_15**；5 个 inactive **cloud_0..cloud_4** 只是原资源模板，未列入删除。

`remove_cloud_controller(source)` 将原云旋转/激活逻辑替换为无操作函数，保留原调用接口；不能只停控制器而不删场景节点，否则 active 云片会永久显示。天空盒、漩涡、昼夜及夜光树冠完全不涉及。

## 合并

```python
from patch_camera import patch, remove_cloud_controller
source = patch(remove_cloud_controller(source))
```

先按 JSON 清单用公开 Scene SDK 删除 cl_0..15，再将函数补丁叠加到 root 最新 bridge 源码。补丁不包含整个桥脚本，因此不会覆盖交互修复、祭坛修改或树冠补丁。

## 测试

`python3 assets/review_gameplay_v27/camera/test_camera.py`：35 条通过，包含 Lua mock 的模式排除、nil / NaN、有限依赖解析、生命周期、合法角度不回拨、异常不影响原 LateUpdate，以及合并后的完整 bridge 语法编译。尚未执行运行场景/手机相机验收。

建议 root 运行后读取 `GetRoamingCameraDiagnostics()`，在出生区、马厩旁平地、河岸坡地极限上拖镜头，确认 pitch 不低于 0、没有地下反面；再验证开场/骑马/药水/游泳/战斗均未被 guard 改角度。昼夜各看一遍天空确认 cl_ 云片消失、天空漩涡保留。

公开文档位置：
`/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/dist/kit/references/skills/hamlet-skill/references/manual/01-core-system/player-network-objects/camera-control/camera-view-control.md`
