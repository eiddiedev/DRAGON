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

## 协作与故障处理

- 先查实例和工程，复用同项目；其它对话在导入/运行时不要同时改主场景。源码可在独立目录准备。
- CLI 超时不等于失败：保留原 requestId 查询 `scene operation`，确认后再继续下一步，禁止盲目重复导入。
- 保存报 `table index is out of bounds` 时，先保留作者包、备份最后成功版本，确认用户无额外未保存修改后再重启。先保存成功再做预览。
- 同步回仓库：编辑器已成功保存并停止修改后运行 `bash tools/sync_from_editor.sh`，然后运行 `python3 tools/verify_handoff.py --write` 更新校验清单，再提交。此脚本仅复制工程，不覆盖旧主脚本副本。

## 参考文档

[世界观与UI定调](docs/世界观与UI定调.md) · [玩法设计](docs/玩法设计.md) · [城堡设计](docs/城堡设计.md) · [资产重制提示词](docs/资产重制提示词.md)。这些文档保留设计历史，冲突时以本交接和用户最新要求为准。
