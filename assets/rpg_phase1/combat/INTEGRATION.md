# 战斗独立验证版接入边界（2026-11-11）

本目录和独立项目 project-508139d3-e199-4b21-805c-0050141438e3 由战斗对话维护。主场景 project_lapv8fm0 和 world_main 未修改。当前仅验证单个本地玩家；多客户端同步、正式档案接入仍须集成验收。

## 已有公共接口

- dragon_combat.lua: `Configure(client, profileRules, effects, simulation)` 由 dragon_rpg 在初始化时显式注入同实例依赖，避免换装克隆时的循环 Scope 查询。`Begin()` → ok, reason；`Retreat()`；`IsActive()`（准备/战斗中）；`IsParticipating()`；`GetStatus()`（phase、epoch、hp、maxHP、damage、enemyCount、authority）；`GetSnapshot()`（完整遭遇战只读快照）。
- dragon_rpg.lua: `OpenContract(change, callback)`；`SetMode('combat'|'explore')`；`SetContext({menu,mounted,dead,inBattle})`；`SetExplorationReady(bool)`；`SetProfile(profile)`；`GetProfile()`。
- dragon_rules.lua：`GetClasses()` 返回每职业三技能元数据。技能动作键固定 `attack`、`skill1`、`skill2`、`skill3`；每技能独立冷却。

## 与非战斗模块的合并约定

非战斗对话建议接口：dragon_progress.IsLoaded/GetProfile/SelectClass/AwardBattle/CanRideDragon。**本版尚未连接这些接口**，独立版仍使用本地测试档案，胜利 +10 月辉，非撤离失败减半。正式合入必须将签约和结算改接 dragon_progress：未加载档案禁止覆盖；签约走 SelectClass；结算按 epoch/battleId 幂等调用 AwardBattle；不直接写共享材料、供奉、自然日额度。不要同时保留旧 RewardVictory 路径重复奖励。

共享 dragon_rpg/dragon_rules/武器/服装脚本不可直接用旧快照覆盖；由双方对照本版合并。战斗包中 PreviewMode=true，正式主场景设 false 并由世界开场驱动职业签约。正式 ArenaX/ArenaZ 仍须按麦田场地确认。

## 本轮动作、表现来源

透明白线图标复用 createWLRD 当前 ui_31.lua 的 installQuietArt；射箭、怪物攻击、角色受伤改用参考项目原始 hero-ranged.wav / attack-basic.wav / hurt.wav；其余技能暂沿用 ms-audio.lua 配方。玩家动作继续使用参考项目骨骼握持时间轴，增加第三技能与战士上举劈斩。敌人使用现有 14 骨影灵，胸、头、左右上臂/前臂六骨做蓄力—挥击—回收；无需重新生成模型。

原生 CustomMain/CustomSub 用于普攻、技能一；另两个同风格 UGUI 图标为技能二/三。切回探索恢复原生跳跃/牵手。按钮禁用/冷却、伤害判定和发射事件均实际接线。UI 图片不是额外收费生成。

## 安装及验证

`python3 assets/rpg_phase1/combat/install.py` 现转发 final-body 安装器。不要重跑 upgrade_v7.py/upgrade_ui.py/upgrade_fx.py/refine_v8.py：这些是一次性改版脚本，不幂等。

规则回归：test_rules.py、test_skills.py、test_encounter.py。CLI 收据及实际运行截图保存在本目录 v13-*（本轮）；v7-* / v8-*（历史）；最终打包及保存信息见 DELIVERY.md。
