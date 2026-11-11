# 最新交付 v14 — 怪物朝向修正

独立验证版，场景根 -736011009。按导入后的模型 -X 正面校正 90 度；由权威规则同步朝向，蓄力至收招保持攻击方向，追击时重新朝向实际目标。
原生运行采样196次，模型正面与静止目标方向点积最低0.99999988；截图 v14-facing.png。朝向锁定、收招重新锁定及原规则/九技能测试通过。
归档 hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/fsbsshd8ybyrfgfu.wprefab
包SHA256 a357eaf0d5de3c5e001e1c759fa493824c8bd5aa84fe2e378cdbc5491f573c94

---
历史记录：

# 最新交付 v13 — 2026-11-11

独立项目 project-508139d3-e199-4b21-805c-0050141438e3，主场景未合入。
场景根 -1571854438。场景保存已 committed，hasUnsavedChanges=false。
归档：hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/hrgmztbwt7q4cybm.wprefab
包：../dragon-rpg-combat-preview.wprefab，4082309 bytes，SHA256 b23facb75b2cd59a604f6d13a8e9805ab3b0a283f122e1957ece475b6df75aac。
变更和证据见 V13_CHANGES.md。本次不是正式主场景、多客户端或最终平衡验收。

---
以下为历史交付记录，版本和容量已被上文替代。

# 六项战斗修复交付 — v11 / 2026-11-11

状态：已在独立验证项目保存、打包；未修改或导入正式 project_lapv8fm0。最新独立场景根 ID -1577648340。

归档 URI：hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/lrl358f0l0lrcnq3.wprefab

本地包：../dragon-rpg-combat-preview.wprefab（4,050,602 字节；SHA-256 d94e52310fe368efcbffd58374f1ed57ea0e492c261429bb98cac7231092fdf7）。文件字节数不是编辑器的 4000 容量计费值；正式场景总容量须合入时再读。

## 完成内容

1. 原参考项目 ms-audio.lua 的 22 个音效配方，实际战斗按挥剑、释放、命中、冲击、蓄力事件播放；8 路音源上限、短时重复限制、销毁清理。原生探针确认 AudioListener 未暂停/音量 1、CombatVoice 播放中/未静音/基础音量 .48。本次没有声称人工试听通过。
2. 实测持有长度：剑 .50、弓 .48、法杖 .65，保留手掌握持点。战士/游侠参考服装及法师现服装保留；仅修复材质安全读取。
3. 每职业普通攻击 + 三技能：战士护盾/回旋斩/裁决，游侠连射/贯穿/箭雨，法师星爆/霜星禁锢/陨星。独立冷却、动作、伤害/控制、0.65 秒输入缓冲。
4. 原生粒子、弧刃网格、飞弹拖尾、金色/翠绿/紫色/冰蓝/橙红效果。无圆柱攻击特效。修复旧环纹理导致弧刃只剩一段的问题；贯穿箭视觉不会在第一个命中点提前回收。
5. 复用原项目白色透明线稿图标；普攻、三技能、书、试炼、收起各自图形；冷却时保留暗图标和倒计时。CustomMain/Sub 加两个补充同风格按钮，退出恢复跳跃/牵手。
6. 已绑骨影灵的胸、头、双上臂、双前臂做蓄力—挥击—收招叠加动画，逐帧恢复基础姿态，保持原有待机/移动，攻击时机对齐权威命中。

## 实测结果

- test_rules.py：10 组基础战斗场景通过。
- test_skills.py：9 技能独立冷却、伤害、护盾、贯穿双目标、霜冻控制、非法输入及本地动作锁通过。
- 实际原生按钮三职业各一场胜利：法师 9.95 秒、剩 1/5 HP；游侠 9.08 秒、剩 2/5；战士 9.85 秒、剩 3/6。均伤害 20，敌人数 0；证据 v11-result-*.json。
- 三场奖励各一次，月辉 30、3 个不同战斗 ID，再读不重复奖励。
- 最终 FX 171 次生成，失败 0；音效 83 次触发，失败 0；结束时飞行特效 0、法阵清除。
- v7-enemy-probe.json 的连续帧确认影灵攻击上臂发生大幅骨骼旋转，v7-enemy.png 为实机姿态。
- v9-arc-0.png 为修复后弧刃与透明操作图标的实际玩家画面，所有视觉源码与最终版相同；v8/v9 技能图中部分帧位于效果开始前/结束后，不将其当效果峰值证据。
- Lua/玩法错误 0、临时钩子 0；保存 committed / hasUnsavedChanges=false。重新打开后再次签约、原生试炼按钮启动已核验，见 v11-reload-status.json。

## 集成限制

此为独立单人验证；多人客户端/所有权转移、正式档案与非战斗进度尚未联调。接口及待接入的 dragon_progress 约定见 INTEGRATION.md。依赖改为 dragon_rpg 显式 Configure 战斗模块，避免换装时 RuntimeScope 循环查询偶发失败。不要恢复 v7-v10 中的旧查询逻辑。
