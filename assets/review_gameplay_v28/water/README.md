# water-v28 · 下一提审只读诊断

独立候选 `water_diagnostics.lua`，尚未绑定正式场景。它用于定位消费者与本地预览的实际水域差异，**不是游泳修复**。

只读取原生 Actor、Unity Collider 和 Physics 结果。不改变位置、碰撞、游泳权限或水体组件；不创建模型、碰撞体、材质或粒子。默认 `ShowDiagnostics=false` 不创建 UI；绑定参数设为 true 后，近水时显示一条小诊断文字。

## 接入

将脚本注册到下一隔离验证包的唯一常驻节点，避免绑在流式加载水体或角色节点上。正式采用由主线程完成，当前目录不导入、不启动实例。

已有提示 UI 通过缓存脚本引用调用：

```lua
local d = waterDiagnostics.GetWaterDiagnostics()
-- 原提示 UI 的文本内容使用 d.summary；getter 本身不执行任何查询。
-- 仅靠近水域时显示，离开可清除该临时诊断文字。
local visible = d.status == 'sampled' or d.status == 'error'
local text = visible and d.summary or ''
```

也提供 `GetWaterDiagnosticSummary()`。典型短文字：

`water-v28 河 98/136 能1 泳0 水触2 脚下:地形块 进/出0/0`

可直接设绑定参数 `ShowDiagnostics=true` 使用脚本自带的小块文字；只有靠近水时显示，远离和停用时隐藏，销毁时释放。它借用已就绪原生按钮字体，无 GraphicRaycaster，文字/背景 `raycastTarget=false`，不接收输入。字体查询和建 UI 最多尝试 3 次，间隔 15 秒；失败原因在 `GetWaterDiagnostics().ui.reason`，不会影响数据采样。

- 能/泳：`CanSwim` / `IsSwimming`，查询失败为 `?`。不能仅凭陆地“能0”判断权限关闭。
- 水触：本次前 12 个结果中，处于已知海/河层级的触发器数；`+` 代表数组被截断。它不是全水域触发器总数，也不是原生注册成功证明。
- 脚下：从角色附近向下射线得到的实际非 Trigger 支撑，过滤角色自身；完整记录带命中坐标和角色高度差。
- 进/出：脚本监听期间的 `onSwimStart/onSwimStop` 次数，不推算之前发生过的事件。
- 错误理由会附在摘要后，详细错误最多保留最近 6 项，每项最多 160 字节。

## 查询边界

- Update 按真实时间最多 1 Hz；停用再启用不重置这个间隔；getter 不采样。
- 三次全图查找上限：首次、15 秒、45 秒。每次仅一次 `GameObject.Find('地图')`，之后用固定子路径 `Transform.Find` 缓存海与河。全部找到后停止搜索。停用/启用不恢复搜索预算；销毁清引用。
- 远离已知水域时仅检查 Actor 和坐标，不执行 Physics 查询。河道区间来自正式保存的 13 个控制点，范围为中心线 14 米且与配置水面高度差不超过 8 米；海区为地图内且 Y 距 27 不超过 5 米。此范围只决定是否诊断，不判定玩家已经在水里。
- 近水时一次半径 1.5 米 `OverlapSphere`（含触发器），只查看原返回数组前 12 个，记录总长和截断标记，不排序或遍历剩余元素。
- 一次 8 米向下 `RaycastAll`（忽略 Trigger），最多查看前 32 个；结果本身无序，在已查看结果中选最近且朝上的支撑。`rayTruncated=true` 时不能宣称找到了全部结果中的最终支撑。
- 已缓存海/河根仅查询根组件，不递归扫描其 1,744 个水域子物体。每个根最多记录 8 个 Collider、16 个组件名；最多向上检查 8 层归属。
- Physics 返回数组仍由 Unity 分配；小半径、低频率、固定调用次数约束查询开销。输出截断不能保证原生引擎只产生 12 个候选。
- `roots.*.components` 仅使用 Unity `GetComponents(Component)` 读取类型名，不访问或修改原生水组件的私有字段。
- Actor 更换、脚本停用或销毁时移除已成功注册的事件监听；不修改其他模块监听。

## 已确认的公开签名

Unity 官方 2022.3 文档（当前主版本地址重定向失败，使用官方版本化文档核对）：

- [Physics.OverlapSphere](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Physics.OverlapSphere.html)：`Collider[] OverlapSphere(Vector3 position, float radius, int layerMask, QueryTriggerInteraction queryTriggerInteraction)`。
- [Physics.RaycastAll](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Physics.RaycastAll.html)：`RaycastHit[] RaycastAll(Vector3 origin, Vector3 direction, float maxDistance, int layerMask, QueryTriggerInteraction queryTriggerInteraction)`；返回顺序未定义。
- [GameObject.Find](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/GameObject.Find.html)：按名字/路径寻找活动对象，不缓存查询结果；所以脚本自行限制并缓存。
- [Collider.bounds](https://docs.unity3d.com/2022.3/Documentation/ScriptReference/Collider-bounds.html)：世界空间包围盒；Collider 禁用或物体不活动时可为空。
- [Component.GetComponents](https://docs.unity3d.com/ScriptReference/Component.GetComponents.html)：按 Type 读取当前对象组件。

安装包公开 SDK 文档根：`/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/dist/kit/references/skills/hamlet-skill/references/`。

- `api-reference/DouyinActor/Methods/DouyinActor.CanSwim.md`：`public bool CanSwim()`。
- `api-reference/DouyinActor/Methods/DouyinActor.IsSwimming.md`：`public bool IsSwimming()`。
- `api-reference/DouyinActor/Events/DouyinActor.onSwimStart.md`、`onSwimStop.md`：UnityEvent，Lua 使用 `AddListener(callback)` / `RemoveListener(callback)`。
- `best-practice/movement/swimming-lua.md` 给出相同订阅及退出取消的实现。

## 验证范围

`test_water_diagnostics.py` 使用 Lua runtime 的公开接口 mock 验证语法、1 Hz、3 次全图查找上限、结果截断、角色自身过滤、事件注销、错误可见性。mock 通过不等于客户端支持已验证；下一提审仍需真实手机截图，尤其 `OverlapSphere/RaycastAll` 的绑定、原生水组件和游泳事件。
