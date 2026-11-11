# 主场景战斗合并交接 — v14（2026-11-11）

本对话不操作、不保存主场景，也不恢复旧 scene.data。独立验证实例已停止。

## 最新交付

- 版本：v14（包含 v13 六项修复 + 怪物正面轴/权威目标朝向修复）。
- URI：`hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/fsbsshd8ybyrfgfu.wprefab`
- 本地包：`/Users/bytedance/Documents/ChatGPT/DRAGON/assets/rpg_phase1/dragon-rpg-combat-preview.wprefab`
- 大小：4082492 bytes。SHA256：`a357eaf0d5de3c5e001e1c759fa493824c8bd5aa84fe2e378cdbc5491f573c94`。
- 作者目录：`/Users/bytedance/Library/Application Support/AI World Creator/projects/project-508139d3-e199-4b21-805c-0050141438e3/ai-sessions/workspace_jcb1a5xe/wprefabs/dragon_rpg_restored`
- 作者工作区 `workspace_jcb1a5xe`，Prefab `dragon_rpg_restored`。独立项目场景根 `-736011009`，**不是主场景节点 ID，不能在主场景拿它作删除目标**。
- 同步源码目录：`/Users/bytedance/Documents/ChatGPT/DRAGON/assets/rpg_phase1/combat/`。规范源为 `*.body.lua`，FX 源在 `vfx/dragon_fx.body.lua`；根目录 `assets/rpg_phase1/*.lua` 为带注册头副本。

## 场地与配置

**没有最终确认的主场景坐标。** 当前正式参数只是既有候选 `ArenaX=157, ArenaZ=27, ArenaRadius=10`（世界坐标）。Y 根据玩家高度附近向下 RaycastAll 取可站表面，未在最新麦田地形验收，不应称为最终坐标。独立版 `PreviewMode=true`，中心使用本地玩家前方 3 米，不能原样留在主场景。

集成方在用户最新麦田附近空地区域确认中心、地面、边界、撤退/死亡落点后再设参数。`dragon_rpg` 与 `dragon_combat` 的 PreviewMode 都设为 false；不要保留独立版自动签约开场。敌人和法阵按世界坐标生成，不靠移动导入根节点改变场地。

## 统一档案：尚未接入

此包仍使用本地测试档案。必须在主场景接统一 dragon_progress 后再测试正式进度：

1. `dragon_rpg.Update` 当前调用 `rules.NewProfile()`；换为 IsLoaded 门禁和 GetProfile，档案未加载时不签约、不创建覆盖存档。注意仅跳过 NewProfile 会让 context 未初始化，需要分别初始化 context。
2. `dragon_rpg` SignContract 回调当前 `rules.SelectClass(profile,selection,external.inBattle)`；改调用 progress.SelectClass，成功后从 GetProfile 刷新职业，不直接改共享档案。参数/返回值以集成方实际 dragon_progress 为准。
3. `dragon_combat.Update` 结算当前 `rules.RewardVictory(p,epoch,damage>0,hp>0)`，失败直接 `p.moon=floor(p.moon*.5)`；正式模式均替换为统一结算接口。AwardBattle 必须按 epoch/battleId 幂等，移除旧奖励/扣款路径，不能两者同时执行。
4. 骑龙解锁由统一 CanRideDragon/主线管，战斗包没有正式接线，不要把测试权限带入正式流程。

## 必需接口与绑定

- `dragon_rpg`: OpenContract(change,callback)、SetProfile(value)、GetProfile()、SetContext(value)、SetExplorationReady(bool)、SetMode(mode)、ShowDamage(position,amount,hurt)。SetProfile 当前要求 schema==1，需与统一档案适配。
- `dragon_combat`: Begin() -> ok,reason；Retreat()；IsActive()；IsParticipating()；GetStatus()；GetSnapshot()。
- `Configure(client,profileRules,effects,simulation)`：由 dragon_rpg.Update 显式注入 `{GetProfile,SetMode,SetContext,ShowDamage}`、dragon_rules、dragon_fx、dragon_combat_rules。保留显式注入，不恢复战斗脚本向职业脚本的循环 Scope 查询（换装克隆时曾失效）。
- 规则动作名 `attack/skill1/skill2/skill3`，职业键 `melee/mage/ranged`。
- `ShadowSpiritSource` 路径/生成源及其骨骼、UGCAnimator、Idle/FloatMove 控制器必须随包保留。模型经 Unity 导入后正面 -X，显示朝向 = LookRotation(faceX,0,faceZ) * Euler(0,90,0)，不可再额外转源节点 90 度。
- FX 十个 GameObject 绑定 Slash/Shield/Bolt/Arrow/Blast/Hit/Tell/Arena/Frost/MeteorEffect 必须保留，不能只拷 Lua。Arrow/Bolt 的 Trail 节点已设 renderMode=none，避免无主体材质的紫方块。
- 音频 BowSound/EnemySound/HurtSound 及各自 Volume/MaxDistance 参数保留。引用原 WAV 已在包中，独立归档明细 original-audio.json。
- 武器/服装与时间轴依赖随包保留；对主场景同名脚本逐项合并，不能并行运行两套职业协调器或重复占用 CustomMain/CustomSub。
- 世界开场调用 OpenContract(false,callback)，树下重新签约调用 OpenContract(true,callback)。进入/退出世界菜单、骑乘、死亡时通过 SetContext 通知；世界可游览时 SetExplorationReady(true)。有 callback 时签约后由调用方负责解除 Immobilize，避免角色锁住。

## 建议合并顺序

1. 公共 CLI 核验主场景身份并保存用户最新状态，备份当前内容。读取现有绑定和模型，不导入/覆盖历史 scene.data。
2. 在单独作者副本适配上述统一档案与世界入口，按同名脚本差异合并；保留最新模型位置、武器资源、服装参数和世界逻辑。
3. 确认 PreviewMode=false、麦田坐标、影灵源和十项特效/三项原音频绑定后 build/archive 新集成包；用新 URI 装入主场景，清除明确识别的旧重复战斗协调器。
4. 从正式开场签约 → 武器菜单 → 麦田入阵 → 三阶段战斗 → 唯一结算 → 重进房间档案保持依次验收；同时测骑乘/菜单抢占原生按钮后的恢复。
5. 最后停止运行并保存主场景，读回保存状态；本对话不代集成方保存主场景。

## 已验收和未验收

已验收：独立本地原生按钮实测三技能/伤害/冷却/角色血条；命中与受伤数字采集；两类弹道实际材质预览无紫方块；攻击/受伤原 WAV 播放器运行；模型正面朝向采样196次 dot最低0.99999988；10项基础规则、九技能和三阶段/扑击/朝向锁定测试通过。临时钩子0，独立场景保存 committed。

未验收：统一存档、主线骑龙解锁、正式麦田坐标/高度/墙体射线和死亡落点、多人加入窗口/所有权切换/重连/请求身份核验/唯一结算、移动端安全区/性能、正式4000容量。音频未完成人耳试听。三阶段共12只，数量与HP按首轮设计；规则模拟游侠70.65秒、法师77.8秒通关，简单骑士策略第3阶段失败，不是最终平衡结论。
