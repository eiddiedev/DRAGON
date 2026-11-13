## 2026-11-13 正式版 GitHub 交付快照

仓库 `editor_project/project_lapv8fm0` 已同步正式「龙眠之境」v26（实际本机工程 project-55a43370-8734-4825-92a8-b0de824a45e2），并包含最新作者工作区 workspace_m293a9tg。991份旧清单已重新生成扩充，以 docs/project-manifest.json 和 verify_handoff.py 验证结果为准。完整特效录像副本不作为正式工程。正式场景 SHA256：673742f831afab0487784ec8bc8436aaaa6a82adfec53ba76b5c97235f5f9366。审核端黑屏/骑乘修复仍待新审核码验证，不能将源码交付当作手机验收通过。云端资源依赖首次打开仍需同账号权限及网络。

## 2026-11-13 v26 已后台安装保存（审核端待验收）

本次只更新正式工程两份已注册 Lua 正文，保留原脚本身份与绑定：`prefab_20/dragon_world_bridge.lua`（v26-bundled-ui）与 `prefab_14/horse_seat_v1.lua`（v26-actor-follow）。正式工程为 `project-55a43370-8734-4825-92a8-b0de824a45e2`。保存请求 `v26-main-scripts-save` 首次连接回执断开，但按同一请求查询最终 **committed / hasUnsavedChanges=false**；保存文件已读回，两脚本均与候选一致，13项TextureSource、resourceRefs未改变。SHA256 `673742f831afab0487784ec8bc8436aaaa6a82adfec53ba76b5c97235f5f9366`。后台实例已明确停止，未开运行、未操作前台、未上传审核、未推GitHub。

源码与回执见 `assets/mobile_visual_riding_v26/STATUS.json`、`main-install-verification.json`、`main-save-operation.json`。界面原图备用路径与原生骑乘回归只通过隔离本地测试，**审核黑屏和骑手脱离尚未通过手机审核入口验收**。下一步上传这一轮测试版，核对产物含上述v26标记，再测试审核码的开场书/地图/武器及骑乘。下方“尚未装主场景”是本轮安装前的历史记录。玩法根节点名称仍保留历史v25，不代表脚本版本。

## 2026-11-13 v26 后台候选（尚未装主场景/未提审）

用户最新提审ZIP `world_dev_unity_143175468-dsst-PROD.zip` 是v25，不能再归因于旧包或笼统环境差异。详见 `assets/mobile_visual_riding_v26/REPORT.md`、`STATUS.json`。UI全13引用置空的隔离测试已通过，原生骑马/跟随/下马回归通过；都不等于审核端通过。主场景字节未变、未删主体、未推送。用户仍要求不在前台运行；不要擅自切换。正式候选归档见archive-gameplay.json/archive-actors.json，严禁安装故障测试archive-nil-assets-test.json。

# 龙眠之境：当前工程交接

## 2026-11-13 提审 ZIP 已查明版本落后

用户提供的 `world_dev_unity_143126706-t0z0-PROD.zip` 为99.95 MB（解压154.30 MB），CRC通过，主资源表198项随包资源齐全。包内世界桥脚本仍是v24，没有本地已保存v25的13项显式依赖及开场门控修复；截图超时文字与v24完全一致。详见 `assets/mobile_visual_riding_v26/REVIEW_FINDINGS.md` 和 `review-package-audit.json`。用户确认手机预览功能正常，审核渠道异常，先排查发布版本与加载顺序，不要盲改已工作的骑乘。用户正在开会：不操作前台，不运行主场景。此次只读检查未改玩法或模型；任务作者后台实例已停止。

## 2026-11-13 当前补充：v25 已后台保存

以 `assets/review_startup_v25/STATUS.json`、`REPORT.md` 和保存回执为准。正式项目 `project-55a43370-8734-4825-92a8-b0de824a45e2`，新玩法根 `-1471846761`；保留 v23 兼容角色根 `-535980144`。作者为 `project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9 / workspace_m293a9tg / dragon_fx_mobile_v22`（历史名称，现为 v25）。不要重导下方历史 v17/v15 包。

开场 UI 和植被地色改为 13 项显式资产引用，开场不再等待远处模型。主场景标题、古书签约、地图/时间、任务书及武器入口已实际检查；植被材质绑定读回 1167。手机审核新包尚未上传或验收；不能宣称审核加载和白草已真机解决。保留 v24 低负载及相机修复，不新增材料、存档，不推送 GitHub。

本次独立 offscreen 实例成功导入、保存、运行验证，前台可以同时使用另一工程。下文“必须前台/被遮挡必卡”是旧推断，不能继续作为操作要求。导入超时查询原 requestId，最终 committed 才保存。当前仓库便携工程未做本轮全量同步，正式磁盘场景和本轮证据优先。

更新于 2026-11-12。以本仓库 `editor_project/project_lapv8fm0/scene.data` 和同目录脚本、作者工作区为当前已保存版本。历史设计文档不等于实际完成状态。

## 最新性能缩减：80 簇麦田（2026-11-12）

- 用户再次反馈严重卡顿，已通过公开 CLI 删除外围95簇，主场景175→80簇；保留中心和渐疏边缘，不移动剩余模型。包围范围由53.62×22.07缩至36.63×14.07。
- `assets/wheat80/save.json` 确认 committed / hasUnsavedChanges=false；读取保存后的 scene.data 验证80个名称与 deletion-plan.json 的 keptNames 完全一致。已同步便携 scene.data。
- 原场景备份 `assets/wheat80/before.scene.data`。本轮未重新导入玩法、未推送。流畅度待用户体验，不宣称已解决卡顿。
- **防回退：dragon_v17 作者包仍有175簇，查询作者接口超时，尚未同步删除。禁止直接重导旧归档；下次修改作者包必须按 assets/wheat80/deletion-plan.json 的 keptNames 仅保留80簇再构建。** dragon_wheat80 是废弃未部署小样，不要导入。

## 当前已保存 v17（2026-11-12 15:29，北京时间）

- 正式项目仍为 `project-55a43370-8734-4825-92a8-b0de824a45e2`。新玩法根 `1897025846`，旧根 `-1174359006` 已删除。save committed / hasUnsavedChanges=false，回执 `assets/v17/`。
- 麦田总计 **175 簇**，全部归入新玩法包，原有外部58簇已移除以免重复。覆盖范围向内收约8%，避让房屋和魔法阵，重新贴地。不得再导入含200或350簇旧作者包。
- 新作者为 **workspace_l7e231w9 / dragon_v17**，正式注册工作区。当前脚本 `scripts/modules/imported/prefab_27/`。旧 workspace_sbazsi67/dragon_phase1_merged 为历史源，勿继续部署。
- 魔法阵全天显示，白天保留挑战入口，点击提示“晚上才能挑战影灵”；实际夜间准入校验仍保留。
- 漩涡由 arena_gate 的实际模型包围盒、朝向决定位置，取消面向镜头；入口触发和返回点随门移动。
- 重新签约显式进入/退出菜单状态并重建原生按钮，逻辑测试连续三次通过。无限材料和额度重置撤除，保留会话进度、免费神秘药水。
- 攻击之前用户已确认恢复，本轮未改伤害/技能规则，需实测回归。
- 校验/构建/归档/导入/保存均成功，磁盘核对175个唯一麦草名称。玩家输入验收未完成：预览启动后代次变化，出现 `null function`；旧编辑器退出，新前台实例随后出现，正在等待恢复。
- 当前本地已同步 scene.data、prefab_27、workspace_l7e231w9，未提交/推送。

## 当前正式工程：2026-11-12 副本转正

用户明确要求将成功副本直接作为正式工程，已通过编辑器主页重命名完成：
- **龙眠之境**：`project-55a43370-8734-4825-92a8-b0de824a45e2`，原“龙眠替换排障”，v16 导入、旧包删除及保存均 committed，hasUnsavedChanges=false。新根 `-1174359006`，350 簇麦田。
- **龙眠之境旧版备份**：`project_lapv8fm0`，保留不覆盖。
- 作者工作区已完整复制到新正式工程。同步与恢复脚本已指向新工程；仓库内便携目录仍保留 `editor_project/project_lapv8fm0` 这一历史名称，不代表本机正式工程 ID。
- 本轮只做本地同步，**未提交、未推送、未上传发布，未运行验收**。下方“部署受阻”等为历史过程，当前状态以上述转正结果为准。

## 2026-11-12 接手部署结果：v16 已归档，导入受阻

- **磁盘主场景仍为 v15 根 `2144325317`，不要视为 v16 已交付。** 作者包 validate/build 通过，成功归档回执见 `assets/v16_deploy/archive-final.json`；下次可复用其中 URI，不必重新归档。
- 前台、后台各尝试一次替换，删除旧根的内存事务 committed，但导入没有成功回执；本轮没有调用 scene save，没有同步半成品回仓库，也没有运行预览。
- 前台导入 `v16-import-20261112` 返回 TIMEOUT，窗口用户与工具均无法操作，用户已强制退出。后台导入 `v16-bg-import-20261112` 返回 SESSION_CLOSED，后续查询超时。故障实例均不可当作可续用的正常实例。
- 包压缩约 12 MB、解压约 16.8 MB，SerializePcgData.json 约 10.85 MB；高负载下操作查询也超时。**尚不能确认是包内容、序列化性能还是编辑器 bug；后台也复现，不能再归因于窗口被遮挡。**
- 回执与恢复状态见 `assets/v16_deploy/`。不要继续盲目重启并重复整包导入；应先定位导入挂起原因，再核验目标并部署。其余 v16 变更和未验证项仍适用。

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

## v16（2026-11-11 晚，Claude）已改好但**尚未归档导入**——接手后先做这一步

用户反馈的六条都已写进作者包源码，构建通过（`build-k.json`），但归档反复超时，没有导入主场景。**磁盘上的主场景仍是 v15 的根 `2144325317`**，所以现在打开游戏看到的还是旧脚本和旧麦簇。

**接手要做的（编辑器窗口必须一直在最前面，被挡住就会超时或卡死）**
1. 打开工程后拿到实例 ID：`douyin-world instance list`。
2. `NORUN=1 bash tools/v15/deploy.sh <实例ID> n 2144325317`（validate → build → 归档 → 删旧根 2144325317 → 导入 → 保存）。去掉 `NORUN=1` 会在最后启动预览。
3. 归档或导入超时：不要换参数乱试。归档可以直接重跑；导入超时后先 `douyin-world scene operation <原requestId>` 查结果，报「自动化会话暂停清理尚未完成」就重启实例，换新标签从头跑。保存报 `table index is out of bounds` / `null function` 也是重启后重做。
4. 保存成功后：`bash tools/sync_from_editor.sh && python3 tools/verify_handoff.py --write`，提交推送。

**v16 改了什么（都在作者包 `ai-sessions/workspace_sbazsi67/wprefabs/dragon_phase1_merged/` 里）**
- 魔法阵退出后还能再进：打完一场后黑夜至少再留两分钟（`dragon_daycycle.lua` 的 `battleWas`）。之前是战斗期间昼夜计时照走，一退出立刻变白天，魔法阵只在夜里出现所以就没了。
- 昼夜各 12 分钟（`dragon_daycycle.lua` 的 720、`dragon_world_bridge.lua` 的 `DAY_SECONDS/NIGHT_SECONDS`）。
- 战斗时的退出键固定在右侧 (-74, 392)，不再压在技能键上（`dragon_rpg.lua`）。
- 烤蘑菇光标速度降 25%（`dragon_exploration.lua` 的 `R.speed`）。
- 麦田加密：作者包 `prefab.json` 新增 90 簇（`golden_geometry_260`~`349`），主脚本尾段把它们登记进随风摆动的名单。
- 麦田贴坡：全部麦簇的高度改为脚下一圈里最低的地面再下埋 4 厘米。西侧 150 簇和新麦簇脚下的麦金底色**已直接写进 scene.data**（`tools/terrain/wheat_v16.py`，备份在 `backups/before-v16-*`）；东侧 110 簇和新增 90 簇在作者包里，要等上面的导入才生效。
- 以上全部**没有实机验证**（用户要求不测试直接推送）。v15 里未验证的清单见下一节，同样有效。

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


## 2026-11-12 手机优化 v21-A（待手机验收）

- 第一批已通过公开 CLI 导入并保存。当前玩法根名：龙眠手机优化甲版，ID -1786989290。归档 URI 及 SHA 见 assets/mobile_perf_v21/candidate-manifest.json。
- 修改：依赖缓存、限时补登记、树叶/麦田距离分档更新、移除叶片 CPU 顶点变形与生成碰撞体、22 个预制音效、影灵限时加载/生成诊断。没有删除主体。
- 桌面：连续五次重新立誓成功；最终包原生挑战按钮召出 4 只影灵。手机问题尚未验收。
- 完整记录与剩余项：assets/mobile_perf_v21/REPORT.md。后台 20 Hz 的帧时不能作为手机性能成绩。
- 不要重跑 prepare.py/patch_*.py 覆盖后续修订。未推送 GitHub。

## 2026-11-12 手机 v21-A 验收失败与 v22 排查

- v21-A 手机未通过：模型仍缺失，最初反馈更卡；最新反馈普通游览暂未明显卡顿，攻击特效触发返回抖音页面。缺失还包括女巫、飞毯及龙或羊。
- 主场景已通过 CLI 回退并保存到 v19 归档，玩法根 `-526571371`（龙眠玩法轻量版）。18:15:34 旧二维码仍是失败包，不是回退包。
- 最新要求：**先不降低画质**。降低粒子数量/纹理分辨率/远景档位均未装入。
- 发现攻击震屏 `UI.fxCam` 复制主相机且两台同时渲染。独立作者 v22 改为单相机 view matrix，同时保留原粒子资源、触发数量、技能伤害与动作；尚待 native 与手机验证。
- v22 作者位于兼容检查工程 workspace_m293a9tg / dragon_fx_mobile_v22。来源、回执与测试在 assets/mobile_failure_v22。不要把未验证作者误装成正式完成版。
- createWLRD 的参考怪物存在骨骼，动作 Lua 驱动；龙眠使用 external animation set。只是对照差异，未证实是模型消失根因。

- 更新：v22 单相机版已导入主场景并保存，根 ID 1356710006；主场景及独立原生运行通过，待手机验收。详见 assets/mobile_failure_v22/no-quality-manifest.json。减量草稿没有采用。任务自建后台实例已停止。
