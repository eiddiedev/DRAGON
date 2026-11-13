# 2026-11-12 重新誓约连续交互修复

用户现象：攻击本轮已可用；古树重新誓约第一次成功，第二次点击失效。

修改作者 `dragon_phase1_merged/scripts/dragon_exploration.lua`：
- 打开职业页时明确持有 class 菜单状态，清理原生探索按钮。
- 完成时释放菜单、恢复角色和原生 UI，并清空按钮目标，让下一帧重新建立入口。
- 重复打开、重复回调不覆盖当前会话；打开失败恢复可交互状态。
- 同步至本仓库 portable 作者目录，未改主场景已注册的 prefab_26 脚本。

验证：`python3 tests/test_recontract_lifecycle.py` 通过 Lua 语法、三次连续签约、重复点击/回调、打开失败恢复和战斗/骑乘拒绝。
CLI authoring validate 成功；build 返回 TIMEOUT，随后 context.capabilities 只读查询也 TIMEOUT，CUA 读取编辑器也 timeoutReached。package/prefab.wprefab 仍为 13:23:32 旧包。

**未归档、未导入、未保存主场景，未完成玩家按钮实测。不要报告已装入或已修好。**
实例已确认重新切回 project-55a43370-8734-4825-92a8-b0de824a45e2。未退出用户编辑器，未提交/推送 Git。
下一步先核实当前构建是否完成，再构建/归档/替换玩法根并连续签约验收。魔法阵显示和传送门漩涡对齐仍待处理，攻击当前按用户反馈可用保留。
