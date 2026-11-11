# 13 条修订验收记录

2026-11-11。本轮只替换 gameplay WPrefab，不回滚主场景模型与摆放。

当前主场景 v10 根：1003422053；v10 保存已 committed。
v11 URI：hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/0rxt8yxri4ofy0sw.wprefab
v11 导入请求：dragon-review-v11-import，已 committed，新根 81930566；旧根 1003422053 已移除。保存请求 dragon-review-v11-save 已 committed，hasUnsavedChanges=false。随后实例消失，尚未开始 v11 运行验收。

## 已有证据
- v10 运行状态 running，进度模块 loaded=true，无云存档依赖。
- v10 实际地图显示麦田、马厩、影灵试炼，旧版地形图。
- 用户实测发现 v10 职业文字空白、全部探索原生入口无响应，不能算通过。
- 找到字库 JSON 中反斜线转义损坏；v11 修复，并补 JSON 解析和覆盖测试。
- v11 探索按钮直接绑定 native Button.onClick，并加 250ms 双回调去重；待真实点击。
- v11 主线图标独立为竖卷轴与羽毛笔，不再复用地图图标。

## 尚待逐项运行验收
1. 祭坛龙蛋位置及旧位置替代物。
2. 古书/职业/任务插画纸面融合。
3. 手写字库、两页排版、外置关闭键。
4. 地图时间与可读性。
5. 武器按钮间距及战斗退出位置。
6. 独立任务图标。
7. 重新签约实际点击。
8. 女巫室内瓶子及去掉室外法杖。
9. 原生星露/免费神秘药水；变大/变小/羊、效果与音效。
10. 专用篝火 UI 与按住/松手结算。
11. 夜间西侧魔法阵。
12. 离场隐藏血条。
13. 真正攻击、命中与伤害。

规则测试通过不等同于上述玩家操作通过。未完成 13 条验收前不得宣称全部修复。

运行阻塞：旧实例消失；CLI 启动的新实例 awc-256b7a41-eaf7-49ca-9b0d-e73012a657da 返回 RENDERER_NOT_READY（真实 owner 清理尚未确认），未能运行。已请求停止该启动实例。用户原主页可操作。不得声称 v11 原生按钮实测成功。
