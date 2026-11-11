# 龙眠之境 RPG 第一阶段

2026-11-11 用户确认。此目录独立于城堡建模；只通过新 WPrefab 与窄范围脚本补丁集成，不恢复旧 scene.data。

## 玩法约束
- 开场古书签约：骑士、法师、游侠；出生圣树可换职业。每职业对应服饰，保留玩家形象。
- 探索：原生跳跃、牵手按钮；牵手右上方武器入口。
- 战斗：原生 CustomMain 普攻、CustomSub 技能；上方安全区域切回探索。清理指针状态与监听，骑乘、飞行和菜单让出槽位。
- 使用 DRAGON 已批准新剑、法杖、弓。参考工程的弩动作须改为双臂拉弓。
- 特效：有体积的剑弧、法术球与轨迹、箭矢拖尾；限定同屏数量，技能反馈与伤害时刻对应。
- 战斗仅在麦田靠村落一侧的魔法阵内，玩家与敌人不越界；多人共享敌人，各自贡献结算。候选中心 (157,27)、半径10米，仍需运行验证地形与通行。
- 日晷为唯一昼夜入口；准备或战斗期间锁定切换。寝殿不切昼夜。
- 主线：签约 → 采集/星露/火种 → 夜间战斗月辉 → 30月辉、3火种、1星露孵蛋 → 龙契骑龙。
- 不做塔防、守夜灯或灯升级。正式玩家不能测试直通骑龙。
- 多人存档、断线和奖励幂等需独立验证；不能用本地 PlayerPrefs 冒充多人存档。

## 参考来源
`createWLRD/game-workspace` 失效，实际源来自 project_nuk7p7hj/scripts/modules：
- prefab_3/36a0d6b8-55ee-434f-ae5a-a9d3ba51a3e2.lua：三职业服饰骨骼跟随。
- prefab_2/d7508e1d-05a6-42d1-a7c8-5da9fd60d9b7.lua：掌心挂点、双节臂 IK、武器尺寸校准。
- prefab_2/19bdbb99-c5cc-4c8a-b21c-3d6c45f73025.lua：攻击时间轴。
- ui_31.lua：原生操作按钮隐藏/恢复。新代码用官方 CustomMain/CustomSub。

## 作者目标与状态
- workspace_zpuv5vvs / dragon_rpg_v1，属于龙眠之境 project_lapv8fm0。
- 独立验证项目 project-508139d3-e199-4b21-805c-0050141438e3，第一次启动在发布实例前退出；未有成功运行回执。
- 这里只创建独立作者资源；未导入正式场景，未改动城堡或用户摆放。

## 2026-11-11 12:47 UI 与服装进展（替代上面的旧运行状态）
- 独立验证项目已经成功运行。真实点击验证三职业签约/重新签约、武器切换、普攻；最新 ranger status sequence=1、nativeSlots=2、outfit visible。前一轮已采样三职业技能动画和 FX；不能据此宣称本轮所有服装动态穿插已通过。
- UI 使用工程既有古书 `ui_book.glb`；左右新入口、普攻/技能为白边透明底。签约背景遮罩拦截点击，左侧验证入口在签约期间隐藏。原生字体保留 NotoSansSC-Medium。最新白色原生文字修正已保存和构建，截图早于该颜色修正。
- 服装：添加骨骼挂点兜帽、分片披风、法师宽檐尖帽、长袍/饰带与战士甲片。截图在 tailoring/。这是轮廓验证版，**未达到用户参考图的精细度，不可标作服装完成**；缺少细腻布料/皮甲构造和配饰，袖口/不同发型仍需适配。
- 已向用户请求收费模型生成授权：douyin-3d 每个任务5星光，三套首轮共15。**尚未收到答复，未提交收费任务**。详见 tailoring/visual-brief.md。
- 主 Dragon 共享实例 12:30 起暂不可达，未重启它；将本次构建包通过公开 prefab import 迁到自己的验证作者 workspace_jcb1a5xe/dragon_rpg_ui_v2，继续制作。
- 最新 archive：`hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/vystl1mv2kcc88ua.wprefab`。文件 `dragon-rpg-ui-preview.wprefab`，导出sha256 0c6ed08b136e1666d536d5dc411a56267baa28804700ba0b78e74334a9d1d0d5。
- 测试 scene root -336122601，场景保存 committed / hasUnsavedChanges=false，见 ui-final-save.json。runtime verifyNoTempHooks 无残留。只停止自己的测试实例。
- 正式 Dragon 场景未导入本资源，main.lua 未安装补丁；准备的 book-integration.patch 需要对最新脚本做窄范围合并。PreviewMode=true 为独立测试，正式安装须 false。
- **重要：scene import 会重映射脚本UUID。修改导入的 Lua 必须保留该文件两行身份头，不可直接复制作者UUID；否则 reload 丢绑定。** 作者脚本和导入脚本UUID可不同。
- 原共享作者源码已同步，但其 package 未重建；可用最新导出包/验证作者继续。tailoring/install.py 是可重复的主补丁；refine/detail 脚本是历史单次变换，不可重复运行。
- 职业档案目前仅会话内存，尚无正式多人战斗/存档/主线安装。衣服改进与原生按钮可预览不等于第一阶段玩法完成。

## 2026-11-11 13:35 Tripo 服装已按用户要求回退
- 用户授权后改用 Tripo，三套生成任务已结算，各20，共60星光（见 tripo_costumes/*-billing.json）。
- 新服装试穿出现破碎/兜帽变形，**用户明确弃用，停止后续生成与适配**。已恢复生成前服装，不将失败模型装入正式世界。
- 当前有效作者：独立项目 project-508139d3-e199-4b21-805c-0050141438e3 / workspace_jcb1a5xe / **dragon_rpg_restored**，由 dragon-rpg-ui-preview.wprefab 恢复。旧 dragon_rpg_ui_v2 现在是失败试制，勿再作为正式来源。
- 独立场景删除 Tripo 包根 -1318693746，恢复生成前归档 vystl1mv2kcc88ua.wprefab，根1909151203。实际点击签约并截图确认原服装恢复，职业/武器/UI仍保留。
- 正式龙眠之境及城堡没有被本轮修改。详情 tripo_costumes/README.md，保存回执 rollback-final-save.json。

## 2026-11-11 14:40 独立职业战斗验证版（当前有效）

用户确认城堡仍在修改，本轮**不合入正式龙眠之境**。作者仍为独立项目 workspace_jcb1a5xe / dragon_rpg_restored。战士、游侠已恢复参考工程基础服装（跳过新增 tailor 装饰）；法师保留当前版本。

- 新增 dragon_combat / dragon_combat_rules：四影灵试炼、近战扇形命中、飞行弹道命中、游侠五连射、法师范围爆发、战士守护/击退、敌人蓄力落点预警、可闪避攻击、心火、边界约束、胜负/撤离、单次月辉奖励。
- 攻击和技能由原生按钮触发；战斗结束恢复探索槽位。共享主权实例运行规则并同步状态，客户端播放表现；**仅单客户端已验收，多人/主权移交未实测**。
- 职业档案和月辉仍仅会话内存。正式主线、云存档、昼夜锁定、麦田地形接入与龙契任务尚未合入；本包不能标作完整第一阶段上线版。
- 用户明确拒绝圆柱拼接攻击。dragon_fx 全面改为 official.effect.playback，8 个可替换资产引用；旧 tube / MeshFilter 攻击代码已删除。战士双层渐隐弧刃与火花，游侠连续箭迹，法师光核/星屑/范围爆发；地面预警和边界也改用粒子。
- 来源：公开 effect-template 的 battle-water-explosion 与 trails-rainbow；裁取并重配所需层，弧形刀光使用自制薄曲面 GLB 与原生透明材质。保留源文件与制作输入 `combat/vfx/`，不使用实体圆柱模拟光效。
- 单资源粒子容量：刀光72、护盾192、飞弹196、箭迹196、爆发384、命中192、预警4、边界4；飞行句柄最多18，停止后自然消散并释放。**这些数字不是编辑器4000容量计分；正式场景合入后仍需读真实总开销。**
- 资源 check、WPrefab validate/build/archive 均通过。effect-review capture-only 返回 CAPABILITY_UNAVAILABLE，未伪造评审通过；使用独立 Runtime 的原生按键、截图和真实 ParticleSystem 跨帧观测验收。
- 真实输入证据：combat/fx3-battle-end.json 战士12.35秒击败全部4影灵、剩4心火；画面显示月辉+10且恢复探索。fx5-ranger-damage/boundary：五连射后伤害4、击败1个影灵，持续D移动后距中心9.5米；撤离恢复探索。fx6-mage-combat：技能/普攻伤害5、击败1个影灵；fx6-clean-effects：退出后arena=false、flying=0、failed=0。10项纯Lua规则场景测试通过。
- 修复了拖尾宽度为零和光核粉色方块；当前法师光核截图 `combat/vfx/mage-1.png`、实战爆发 `combat/vfx/mage-combat-impact.png`。高亮画面仍以亮核为主；最终夜景配色与正式场景容量尚未验证。
- 现有服装初始化仍有 EnvLit_AI 缺少 _Color 的日志（非特效播放失败）；未擅自改变用户保留的法师服装。武器脚本重复的 host-unavailable 日志已改为只记录一次。
- 最新归档：`hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/tltg4jn0r8hrzg5c.wprefab`。
- 导出：`dragon-rpg-combat-preview.wprefab`（3,340,500字节，SHA256 7fcc71917812901f9cfb86ff48a779f3adcf24c3fec99c62f138cd14e321fa0e）。
- 独立场景根1105211001；保存、重开与清理回执见 combat/final-*.json。本轮没有模型生成或星光扣费。
- 最终当前包再验：`combat/final-outcome.json` 战士胜利，伤害20、剩3心火；`final-profile.json` 与 `final-profile-again.json` 月辉均10、奖励键唯一。`final-save.json` 和 `final-scene-save.json` 保存无未保存改动；`final-reopen-fx.json` 引用齐全，`final-reopen-clean.json` 无调试残留。自建实例停止回执 `final-instance-stop.json`。

## 2026-11-11 战斗六项修复 v11

最新独立验证包已更新：每职业三技能、原项目战斗音效、缩小武器、彩色粒子和弧刃、透明图标、影灵骨骼攻击。三职业实战各胜一场，奖励不重复；主场景未合入。交付记录见 `combat/DELIVERY.md`，对非战斗进度的接入边界见 `combat/INTEGRATION.md`。`combat/install.py` 现在只安装当前 final bodies，不再重建旧 UI。
