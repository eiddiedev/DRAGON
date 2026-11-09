---
name: world-editor-pipeline
description: 造世界编辑器实测管线：Lua 脚本绑定入口、调试日志通道、模型子节点旋转、关工程写存档的流程
metadata:
  node_type: memory
  type: reference
  originSessionId: bebdc553-7213-45f1-a774-1701177b23fd
  modified: 2026-11-05T14:20:18.205Z
---

抖音造世界编辑器（工程 project_lapv8fm0，龙眠之境）实测到的非显而易见的事实，2026-11-05：

- 脚本入口：选中节点 → 右侧「逻辑属性」→ 右下角按钮 →「新建 Lua 脚本」。文件落在 `scripts/modules/<名字>.lua`，直接改磁盘文件，下次「本地运行」就生效；保存工程时内容会写进 `SerializePcgData.json` 的 `runtimeScripts`。脚本写全局函数 `Update()` 等，末尾 `return {}`。`OnPlayerJoined` 没有触发（或被相机初始化覆盖），可靠做法是在 `Update` 里等 `DouyinNetService.isNetworkSettled` 和 `DouyinActorService.GetLocalActor()`。
- 调试日志：`print` 看不到；`CS.UnityEngine.Debug.LogError(msg)` 会写进 `~/Library/Logs/造世界编辑器/main.log`。`UnityEngine.Physics.RaycastAll` 可用，能直接量碰撞高度。
- 模型旋转：导入模型的 `main`、`glow` 子节点存的是世界变换，只改根节点 `rot` 不生效，必须同步子节点（地形块没有子节点所以不受影响）。
- 相机：默认俯仰 18°，`SetPitch(-10)` 是抬头。`SetPitch` 要连续设置约 30 帧才不被覆盖。
- 输入：游戏画面只吃前台真实输入（需要 computer_batch），后台 app_* 的拖动和按键进不去。工具栏的按钮也要真实点击；顶部运行按钮用 app_click 更稳。
- 写存档流程：运行中先停止 → 项目>保存 → 造世界编辑器>退出应用（回首页，工程关闭）→ 写 scene.data → 首页「去编辑」重新打开。工程开着时写会被覆盖。
- 编辑器自带文档 `addon/agent-runtime/skills/**` 是加密占位，公开可读的只有 `addon/lua-support` 下的 Meta 声明、snippets、Library。

工具脚本在 `tools/`（place_world.py、fix_child_rot.py、post_place_fixes.py），脚本副本在 `scripts/world_main.lua`。
- 写存档的命令链不要用 `脚本 | grep && cp`：脚本崩溃时 grep 仍成功，会把旧文件装进去（2026-11-05 踩过）。用 `set -euo pipefail` 或先判断退出码。
- 退出工程要走 造世界编辑器>退出应用，弹出「是否保存工程」时点保存；`项目>保存` 有时不落盘，改完要看 scene.data 的修改时间。
- 大范围散碎小面（花）容易出错，花草用带透明贴图的交叉面片加节点克隆。高精度地形块导入约 100 秒，等待时间不够会被下一次操作顶掉。
- 引擎把导入的每张贴图压到 1024（不透明 ETC2 带 mipmap，透明 ARGB32 无 mipmap），GLB 里的法线贴图会被丢掉，同一 GLB 的多个材质会合并成一张（2026-11-05 实测）。一块 64 米地形只有 16 像素/米，想更清晰只能拆成多个 GLB。
- 地形近景细节的做法：运行时把重复贴图设给 `_EmissionTex`（`SetTextureScale` 可独立平铺，有 mipmap），由 `_EmissionPower` 控制强度，不用重新导入也不加面。贴图用一张藏在地下的小方片带进工程，脚本取走后隐藏。材质 `Douyin/AI/PBR/EnvLit_AI` 的 `_BaseColor` 也可运行时改（城堡昼夜变色靠它）。
- 引擎原生草（Terrain detail）接口不报错但画不出来。草片晃动用两层 Transform 做剪切（父节点旋转+非均匀缩放、子节点反向旋转）。
- 容量按节点计，1240 面的草片每个节点约 4。Find 找不到未激活节点。导入有时被 Claude 窗口抢焦点，每批前先 open_application。
- 骨骼动画可用（2026-11-06 实测）：GLB 的蒙皮和动画片段都保留，节点上是旧版 `Animation` 组件，不会自动循环，要在 Lua 里设 `wrapMode = Loop` 再 `Play(clip)`。导入框会显示容量和面数：960 面容量 2，容量约等于面数/1000。多物体 GLB 保留父子层级。
- 不依赖 Blender 的 GLB 写入器在 `tools/models/glbw.py`（调色板贴图、蒙皮、动画、自发光），离线预览用 `tools/models/preview_glb.py`。摆放用 `tools/place_world4.py`，模板不要改名，全部克隆。
- 用户可能同时在编辑器里操作（比如跑编辑器自己的 Agent），动手前先用 app_screenshot 看一眼，别抢。
- 导入硬限制（2026-11-06）：单个模型不超过 3 万面，资产名不超过 15 个字符，音效 mp3/wav 不超过 10 MB。超了就拆模型，多个蒙皮模型共用同一套骨骼和动画片段可以保持同步。
- 蒙皮模型结构是 根节点 → rig → 同名网格 + 骨骼。根节点和网格同名时 `GameObject.Find` 可能找到网格，动画组件在根节点上，要先取根（看父节点是不是 rig）。`Animation` 组件比节点晚出现，要重试。蒙皮模型默认缩放是 1，静态模型默认缩放是最大边长。
- 自定义背景音乐：导入音效后，云端地址在 `~/Library/Application Support/AI World Creator/asset-cache/cache.json`（要拖一次才会缓存），写进 scene 的 `audioData.uri`。本地运行时 AudioSource 看不到 clip，是否真的在响要用户听。
- 没有改动时退出不弹保存框，磁盘上的 Lua 不会写进 scene.data；工程关闭时可以直接改 `runtimeScripts` 里 `modules/world_main.lua` 的 `content`。

- 导入提速（2026-11-07）：导入框的「资产描述」留空会走 AI 自动生成，慢且常卡。手动填一个词（点 (686,560) 再打字）后，普通模型 15~30 秒，密集草块 40~55 秒。导入框转圈超过 2 分钟基本是卡死（取消按钮不可用），只能 造世界编辑器>退出应用>保存 后重进。上一个没结束时后面的点击全被吞，批量后要对照存档里的根节点名补漏。
- 蒙皮烟花：一颗火星一根骨骼，片段里用缩放 0 控制隐藏和寿命，循环播放即可，不需要粒子。ParticleSystem 能创建但没有材质（显示紫红方块），编辑器没有可用的粒子着色器。
- 跳跃输入会在 GetKeyDown 的下一帧再通过 onJumpInputStart 触发一次，用同一个键切换状态要加冷却。
- 背景音乐：audioData 的 refId 为 0、audioType 为 20 是官方曲目也用的格式。声音资产不进场景树，拖一次后地址写进 asset-cache/cache.json。
- world_main 主块的局部变量已贴近 Lua 200 上限（2026-11-08 加骑龙时超限，脚本整段不运行、日志无任何输出）。新增状态一律放进表（如 DR、BT、HV），改完用 python `lupa` 的 `load()` 检查语法和局部变量数。
- 编辑器「资产生成」有两种模式：Agent 模式（技能：一体铸造 / 模块组装 / MIX，可生成带脚本、可骑乘的模组，产物在 ai-sessions/workspace_*/package/*.glb）和模型生成（Douyin 3D / Hyper3D / Tripo）。人物坐姿接口：actor:SitDown(go, true) / actor:StandUp(go)。
- 自定义界面可行（2026-11-09 实测）：Lua 里直接建 `UnityEngine.Canvas`（ScreenSpaceOverlay）+ `CanvasScaler` + `UI.RawImage`，点击用 `Input.GetMouseButtonDown(0)` 自己算命中。贴图做成带透明的小方片 GLB 导入（tools/ui/make_ui.py），脚本 `GameObject.Find` 后取 `_BaseTex` 再隐藏节点。`DouyinUIService.SetUIVisible/SetNativeUIVisible` 可隐藏平台摇杆。UI 代码在 scripts/ui_v1.lua，用 tools/ui/embed_ui.py 嵌进 world_main_v5.lua。
- 音效可在运行时合成：`AudioClip.Create(name, n, 1, 22050, false)` + `SetData(lua表, 0)`，AudioSource:PlayOneShot。是否真响要用户听。
- 中文开源字体在 assets/fonts（思源黑/宋 Heavy、霞鹜文楷，均 OFL）。「不背单词」里的 BB- 字体是子集，会缺字，别用。
- 导入框的「前往文件夹」偶尔残留旧文字，先点输入框右侧的清除钮 (870,285) 再输路径。
