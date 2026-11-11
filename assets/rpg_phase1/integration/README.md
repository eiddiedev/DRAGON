## 无存档版运行已确认

主场景 runtime b16e1726-8450-46ea-a764-dce45ead1894 实测 progress loaded=true / busy=false / persistent=false，职业签约 revision=1；截图 /tmp/dragon-session-v3.png 显示誓约已签订、职业服装和武器入口正常出现，不再显示云端读取。此结果仅确认本轮无存档启动与签约，非完整玩法验收。

# 当前装入状态（16:48）

无存档 v3 已重新导入主场景，根 984406944；save-v3-reopened.json 返回 committed / hasUnsavedChanges=false。实例 0d44b402-a25f-45f5-ac45-b315f61c8597。正在实际运行验收。下方 16:42 中断记录已被本段替代。

# 最新状态（2026-11-11 16:42）

用户明确说明此世界不支持存档，要求不要存档。已将 progress 完整改为本次游玩内存态，离开重置；无 DATASTORE/GetDataStore 调用。已同步 noncombat 源和注册作者。

v3 URI：hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/6ikc8wgdcb5afyxm.wprefab

旧主逻辑 -1906224344 删除已 committed 并保存。v1 已实测卡云读取（非 Lua 包装接口），v3 移除全部持久化而非继续修云。
v1 根 1036911262 删除 committed；v3 导入根 1720956093 committed，但随后保存、runtime status 都报 null function，v3 未保存成功。磁盘仍是 v1 根 1036911262，无旧主逻辑节点。不要恢复旧场景文件。

失效实例 8270d4cb-1572-4f7a-9d25-f42f84d651a1 已执行 instance stop，回主页。重新打开后应以最新磁盘场景为基准，仅删除 v1 根、导入 v3（新请求 ID），保存并运行确认。当前作者包完整，不需重新制作。

已通过规则测试、语法测试和无云服务内存态签约/奖励去重测试。没有通过 v3 实际运行验收。UI 地图故事书仍未接入。

--- 以下为早期记录 ---

# 主场景第一阶段合并（2026-11-11）

## 当前状态：导入已落盘，替换和验收中断

- 最新主场景先由公开 CLI 保存，committed / hasUnsavedChanges=false。快照：`backups/before-gameplay-merge-20261111-160118/scene-current.data`。
- v14 战斗包导入独立作者 `workspace_sbazsi67/dragon_phase1_merged`；不修改战斗对话作者目录。
- 整合源码已写回合法注册脚本，校验、构建、归档通过，`archive-v1.json`。
- 新 URI：`hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/3j8dd0zaaf2zfb7z.wprefab`。
- 导入请求 `dragon-phase1-integrate-v1` 超时；随后 operation 返回“自动化会话暂停清理尚未完成”。前台随后切到「仔仔塔防森林篇」，已停止 CUA 操作。
- **只读存档确认合并根 1036911262 已落盘；旧主逻辑节点 -1906224344 仍在。因此尚不能运行验收，不能称合并完成。不要重复导入。**
- 待取得用户独占编辑器时段后：核验项目实例，查询原请求，确认新根及注册脚本完整；删除明确旧主逻辑节点 -1906224344（无子节点，模型和原坐标已复制到新包 n164），再运行。
- 不恢复旧 scene.data。保留最新模型摆放。草叶子节点有风动姿态差异，根节点变换差异另见 merge-status.json，不回滚这些子节点。

## 改动

- SignContract 改为 dragon_progress 云档案事务，未加载时拒绝，保存成功才确认职业。
- battle 奖励改为统一 AwardBattle(epoch,10)，由持久化战斗 ID 去重，不并行走旧 RewardVictory；去掉测试版失败直接减半月辉。
- PreviewMode=false（职业和战斗），PreviewOnly=false（存档）。未植入测试材料。
- 保留 v14 原武器、服装、十项 FX、三项 WAV 和怪物骨骼朝向。
- 主逻辑基于用户最新已保存脚本添加窄桥接，两个骑龙入口均检查龙契；保留其它旧世界行为。
- 非战斗模块同包：材料、调制、烹饪、药水、供奉、共享昼夜；这些仅为首轮集成，**尚未在游戏里验收**。
- 地图和故事书新美术本包未接入。

## 已运行检查

`/tmp/dragon-integration-python/bin/python assets/rpg_phase1/integration/test_progress.py` 通过：玩家隔离、每日额度、夜晚拒采、职业变更保留材料、战斗重试去重、分次供奉、六种烹饪阈值、所有整合 Lua 语法。修复精确 68% 阈值的浮点误差及烹饪秒级计时不足。
原战斗 test_rules.py / test_skills.py / test_encounter.py 全通过。
这些不代替真实云存档、多客户端、骑乘/药水恢复或玩家视角验收。

## 下一步

1. 完成上述旧节点替换，启动并固定新 runtimeId。
2. 先读 Lua 错误和 progress / rpg / exploration 状态；实际走签约、武器切换及麦田入阵。
3. 麦田中心 (157,27) 半径10仍是候选，须地形实测。真实胜利奖励验证云档案去重与重进恢复。
4. 检查地图/探索/骑乘抢占原生按钮，及所有非战斗交互。
5. 停止运行、保存、检查无临时探针，记录最终容量。当前只有合并前容量2285/4000，不能宣称合并后容量。
