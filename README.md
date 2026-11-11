# 龙眠之境 · DRAGON

造世界编辑器项目：场景、注册脚本、玩法作者工程、自制模型与制作源文件。

**从 [HANDOFF.md](HANDOFF.md) 开始**：当前状态、换电脑恢复、源码入口、未完成事项与验证记录。

```bash
git clone https://github.com/eiddiedev/DRAGON.git ~/Documents/DRAGON
cd ~/Documents/DRAGON
python3 tools/verify_handoff.py
# 目标工程未打开时执行；已有同名工程会先备份
bash tools/restore_project.sh
```

需安装造世界编辑器并登录同一账号，云端模型首次打开会下载。当前为无限资源、每次重开的测试版，不支持玩家跨次存档。地面麦金色在实际游览生效。

参考：[世界观](docs/世界观与UI定调.md) · [玩法设计](docs/玩法设计.md) · [城堡设计](docs/城堡设计.md) · [资产提示词](docs/资产重制提示词.md)。
