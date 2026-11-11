# 原生职业粒子特效

此目录属于独立战斗验证版。源来自公开 effect-template，build_effects.py 以完整模板快照为母版制作8个资源；不是直接编辑 package。effects/ 仅保存当前效果及引用依赖；archives.json 保存当前归档URI。

复现：build_effects.py → archive_effects.py → bind_effects.py → ../install.py → validate/build/archive/import。cli.py 内 P/I 必须先核验并更新为自己的作者和实例。禁止操作 project_lapv8fm0，城堡仍在并行修改。

表现：双层弧刃、命中火花、守护震波、飞弹光核/尾迹、连射箭迹、范围爆发、敌袭落点、试炼边界。玩法伤害只由 dragon_combat_rules 计算，任何特效失败不阻断伤害。create 句柄均有Stop/Release，spawn由系统回收。

运行验收使用真实原生按钮。capture_native.py 在原生按住普攻时截图；inspect_particles.js是只读跨帧观测。effect-review 的外部截图能力不可用，未记录模型评审通过。旧版本截图可能曾有粉色光核，当前 mage-1.png 已确认修复。

可调资产均在 dragon_fx.lua 的 GameObject 参数披露。参考粒子计数不等于世界容量积分；仍需正式世界整合后的容量检查。当前包仅独立验证，不含正式多人存档/主线完成声明。
