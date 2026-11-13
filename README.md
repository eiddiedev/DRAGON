# 龙眠之境 · DRAGON

造世界编辑器项目：场景、注册脚本、玩法作者工程、自制模型与制作源文件。

**从 [最新 Agent 交接](assets/handoff_20261113/AGENT_HANDOFF.md) 开始**：正式 v27、未接入的 v28 候选、最新审核包、手机环境和未解决问题。历史过程见 [HANDOFF.md](HANDOFF.md)。

```bash
git clone https://github.com/eiddiedev/DRAGON.git ~/Documents/DRAGON
cd ~/Documents/DRAGON
python3 tools/verify_handoff.py
python3 tools/reassemble_review_package.py  # 还原最新提审 ZIP 并校验
# 目标工程未打开时执行；已有同名工程会先备份
bash tools/restore_project.sh
```

需安装造世界编辑器并登录同一账号，云端模型首次打开会下载。当前不支持玩家跨次存档，也未启用无限资源。具体修复和待验收项以 [v27 报告](assets/review_gameplay_v27/REPORT.md) 与 [交接文档](HANDOFF.md) 为准。地面麦金色在实际游览生效。

参考：[世界观](docs/世界观与UI定调.md) · [玩法设计](docs/玩法设计.md) · [城堡设计](docs/城堡设计.md) · [资产提示词](docs/资产重制提示词.md)。
