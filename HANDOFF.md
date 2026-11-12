# 龙眠之境：当前工程交接

更新于 2026-11-12。以本仓库 `editor_project/project_lapv8fm0/scene.data` 和同目录脚本、作者工作区为当前已保存版本。历史设计文档不等于实际完成状态。

## 换电脑恢复

1. 安装造世界编辑器，登录同一抖音账号。云端模型 URI 需要该账号权限和网络；仓库不含账号凭据与编辑器资源下载缓存，首次加载仍需下载资源。
2. `git clone https://github.com/eiddiedev/DRAGON.git ~/Documents/DRAGON`（已有仓库则先保存本地工作，再 `git pull`）。
3. `cd ~/Documents/DRAGON && python3 tools/verify_handoff.py`，确认传输完整。
4. 确保目标电脑没有打开本工程，再运行 `bash tools/restore_project.sh`。脚本会先备份目标电脑已有的同名工程，再复制完整工程，不会覆盖其它工程。
5. 打开编辑器中的「龙眠之境」。用公开 CLI 的 `instance list` 发现新 instanceId；不要复用任何历史回执里的 instanceId、runtimeId、端口或会话。
6. Python 制作工具按需安装：`python3 -m pip install numpy pillow opencv-python-headless scipy fonttools lupa`。首次开发时读本机最新 douyin-game-creator Skill；旧脚本中的直接改 scene.data 流程不再采用。

## 当前源码入口

- **已保存主场景和注册脚本**：`editor_project/project_lapv8fm0/scene.data`、`scripts/`。
- **当前整合 WPrefab 作者工程**：`editor_project/project_lapv8fm0/ai-sessions/workspace_sbazsi67/wprefabs/dragon_phase1_merged/`。包含作者源、注册 Lua、资源与构建包。
- **可读玩法源与验证工具**：`assets/rpg_phase1/integration/`。其中 `dragon_world_bridge.body.lua`、`dragon_exploration.body.lua`、`dragon_progress*.body.lua`、`dragon_rpg.body.lua`、`dragon_combat.body.lua` 等是本轮整合来源。
- **本轮布局源、模型布局、染色图与回执**：`assets/layout_fix_v14/`；前一轮在 `assets/layout_sw_v13/`。
- 自制模型、贴图、音效和制作脚本保留在 `assets/`、`tools/`。项目内已注册的脚本头两行 ID/referenceName 必须保留。
- `scripts/world_main_v5.lua`、旧 place_world/install_lua 工具属于历史实现，**不是当前整合主场景的唯一真源**，不要运行它们恢复旧摆放。

## 最新已保存与验证状态

- v14 场景新根 `982882180`。保存 operation `7a70d2b31013c683353b26a17a1259d0895dca9639f65d3cae64234f943a56dc` 为 committed，hasUnsavedChanges=false；磁盘复核一致。
- 魔法阵按用户定位物：中心 X130.3/Z19.4、半径13.275米，贴地曲面，只在夜间出现。定位物「圆形传送阵」已删除。
- 麦田共260簇。东侧新增110簇中的86簇已移开房屋、马厩和入口；对应草地清理已落盘。
- 麦金色渐变通过运行时克隆地形材质的 `_CoverTex` 实现。**实际游览有染色，编辑态仍显示原地色**。运行取样和截图已确认生效，不是编辑器永久地形涂绘。
- 此次后台验证实例已停止，当前工程可重新打开。重启后保存故障解除；不宣称编辑器的根本 bug 已修复。

## 玩法与未完成事项

- 当前是用户要求的**无限资源测试版**：每次进入重新读开场书、签职业；材料补足99999；无云存档、无跨次进度，不要当正式经济版本发布。
- 正常配方：星露1（3蘑菇+3月见花+1羊毛）、火种3（完美烤蘑菇）、月辉30（战斗）。祭坛可分次供奉，完成后缔结龙契。
- 蛋目前是阶段模型+约3秒抖动提示，**无完整破壳成长动画**。当前骑龙仍是祭坛附近按跳跃直接上雪山龙背；落地后龙回山顶。龙飞来接人、原生骑乘按钮、龙魂回归剧情只是建议，尚未实现或获确认。
- 战斗由另一个对话推进。不要把之前的所有交互、技能、多人行为写成已全面验收；参考本轮回执与用户最新反馈逐项验证。
- 用户明确要求保留最新模型与摆放；编辑采用公开 CLI 场景导入/删除/保存及 Scene SDK，不直接写主 scene.data，不恢复旧场景。

## v15（2026-11-11，Claude）本轮改动与验证状态

场景新根 `2144325317`（「龙眠玩法与界面v15」），保存 `v15-save-j` committed。回执在 `assets/layout_v15/receipts/`。

**改了什么**
- 界面贴图改为 PNG/JPG base64 随 `dragon_world_bridge.lua` 带入、`Texture2D.LoadImage` 载入（不再受导入压到 1024 的限制）。生成：`python3 tools/ui/make_ui2.py`，打进作者脚本：`python3 tools/ui/patch_bridge_v15.py`。界面区源码 `assets/v15/bridge_ui_region.lua`，尾段 `assets/v15/bridge_tail.lua`，探索脚本 `assets/v15/dragon_exploration.lua`。
- 故事书：三个对开页重画，剧情改为「蛋里封的是龙魂，龙身在雪山」；第三对开页恢复为「你」+ 龙魂之卵；合书时旧页闪现已修（原因是签约回调里把旧页重新显示）。
- 职业页、誓约之书（主线面板）、左上角三个同大按钮（地图 / 誓约 / 唤龙）、屏幕上方正中的主线提示（带方向和距离）、战斗按键（环形排布、冷却转圈）、拔剑键（原生白色半透明样式，和牵手键同大，排在跳跃—牵手弧线上）。
- 地图：按当前地形重画 2048 图；新增马厩、金穗麦田、影灵试炼；走到地点自动盖印，显示「已探访 n/22」和「手稿碑文 n/8」。
- 烤蘑菇：蘑菇串来回晃，晃进金色火区时按「出锅」算烤熟（得火种、20 秒加速），否则是生的（10 秒眩晕、画面摇晃扭曲）。规则在 `dragon_progress_rules.lua` 的 `roast`。
- 手稿与碑文 8 处：书库三处、营地石碑、祭坛三柱、圣所契碑。
- 唤龙：结契后点左侧龙印 → 龙从雪山飞到祭坛落地 → 走近点龙印或按跳跃骑上。多人房间由 `dragon_daycycle.lua` 的同步变量 `DragonState` 裁决，别人唤龙时提示「请稍后」。
- 裂隙之门加漩涡；进门后的地下试炼场可「发起对决 / 加入对决」（`dragon_combat_rules.lua` 的 duel 模式，对决时心火 ×4）。战斗特效放大叠层，大招带闪光和镜头震动。
- 地形：魔法阵洼地填平（中心 130.3/19.4，平地半径 15.5，高 35.6）；麦田底色直接写进地形底色图；东侧 110 簇麦子并回主田。工具 `tools/terrain/arena_wheat.py`（**直接改 scene.data 和 prefab.json，只能在编辑器关闭时运行**，备份在 `backups/before-v15-*`）。魔法阵改为一张贴地的发光图，高度读地形。

**实机看过的**：标题、故事书三页、职业页、左上角按钮、主线提示、地图与盖印、战斗按键与特效。
**没来得及实机验证的**（用户要求先推送）：誓约之书面板和烤蘑菇面板的排版、地图时间数字、夜里的魔法阵、手稿阅读、唤龙全流程、漩涡、对决（需要两个人）、多人唤龙提示。主脚本取探索/昼夜脚本改成了由它们主动登记（`RegisterScript`），这一改动也还没实测。

**这台机器上踩到的坑**
- `authoring result archive` 必须在前台实例里做；后台实例上传成功但卡在生成缩略图，一直超时。
- 编辑器窗口被别的窗口挡住时，导入会卡死并报「自动化会话暂停清理尚未完成」，只能重启实例。导入和保存时让编辑器保持在最前面。
- 脚本包 17 MB 时保存连续崩溃（`table index is out of bounds` / `null function`）；把贴图压成调色板 PNG、主脚本降到约 11 MB 后保存成功。不要再往脚本里塞大图。
- 部署脚本：`tools/v15/deploy.sh <实例ID> <标签> <旧根ID|none>`。

## 协作与故障处理

- 先查实例和工程，复用同项目；其它对话在导入/运行时不要同时改主场景。源码可在独立目录准备。
- CLI 超时不等于失败：保留原 requestId 查询 `scene operation`，确认后再继续下一步，禁止盲目重复导入。
- 保存报 `table index is out of bounds` 时，先保留作者包、备份最后成功版本，确认用户无额外未保存修改后再重启。先保存成功再做预览。
- 同步回仓库：编辑器已成功保存并停止修改后运行 `bash tools/sync_from_editor.sh`，然后运行 `python3 tools/verify_handoff.py --write` 更新校验清单，再提交。此脚本仅复制工程，不覆盖旧主脚本副本。

## 参考文档

[世界观与UI定调](docs/世界观与UI定调.md) · [玩法设计](docs/玩法设计.md) · [城堡设计](docs/城堡设计.md) · [资产重制提示词](docs/资产重制提示词.md)。这些文档保留设计历史，冲突时以本交接和用户最新要求为准。
