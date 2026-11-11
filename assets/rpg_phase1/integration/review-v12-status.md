# 第二轮 7 项修订

作者包：dragon_phase1_merged；主场景新根 -753924050，旧根 81930566 已移除。
归档：hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/a4aavby1s09e1xnb.wprefab
保存请求：dragon-review-v12-save。

1. QuestBook 关闭按钮采用地图 atlas.close 纸签底框与原有收起文字。
2. 羊外观相对人物旋转 180°。
3. 变大倍率 2.25 → 3.5，仍用 actor.scale，保留原尺寸恢复。
4. 职业 UV y=.532,h=.468；龙蛋图 h=.527，按真实上下图边界裁切。
5. 现有 horse_seat_v1.lua 移除人物 s.scale*1.6；不更改马的位置。保留身份头。
6. ArenaX 145 → 133，Z27，R10；法阵每段不超过 .3米向下取地表高度+.10，移除原水平粒子边界；接近入口范围 R+2。
7. RPG Update 持续刷新菜单/骑乘状态，恢复控制根显隐；骑乘前处于武器模式时，下马后尝试恢复原生攻击/技能槽。

源码语法、规则回归、字库 JSON 测试已通过。以上尚需本轮实际运行验收，不能将源码变更等同于体验已修复。
