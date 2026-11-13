# 麦田减半对照 2026-11-12

用户授权：先减少麦田；没有未保存手动改动，可以重启。
执行：通过公开 scene remove 分三批移除 175 个 golden_geometry 草簇；保留 175 簇，最远点采样维持原范围。三批 committed，scene save committed / hasUnsavedChanges=false。
原 scene.data 保存在 before.scene.data；selection.json 保留完整移除草簇节点与保留名称。
磁盘复核 golden_geometry 数量 350 → 175。已复制已保存 scene.data 到仓库便携工程。未提交/推送。

本轮未导入新的玩法包：正式场景仍含无限资源；撤除无限资源和重新誓约修复在作者源码及本地构建包中，尚未归档/导入。归档报 existing workspace 缺失，创建工作区超时，勿当已部署。

重要：保存前后总节点数 23196 → 23891。移除 1051 节点，同时新增 1746 节点，其中 1744 名称为 Trigger_*（锁定、空 triggerData），另有出生点和空名称节点；已有节点还出现动画姿态及编辑数据变化。此变化由编辑器加载/保存过程产生，未由本次 remove 请求创建；来源尚未确证。不能宣称总节点数下降或卡顿已改善。
后台实例 awc-38d05805-55e2-4c35-9a72-a2eacff1ed69 已请求停止，见 stop.json。

未来重导 dragon_phase1_merged 前必须按 selection.json 的 keptNames 同步作者节点（当前作者 prefab.json 仍含350簇），否则会恢复到350簇。不得盲目导入当前正常资源构建包。
