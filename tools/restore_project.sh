#!/bin/bash
# 把仓库里的编辑器工程装进「造世界编辑器」的工程目录。先退出编辑器或回到首页再运行。
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$HOME/Library/Application Support/AI World Creator/projects"
mkdir -p "$DEST"
if [ -d "$DEST/project_lapv8fm0" ]; then
  BK="$DEST/project_lapv8fm0.bak.$(date +%Y%m%d-%H%M%S)"
  mv "$DEST/project_lapv8fm0" "$BK"
  echo "已有同名工程，已改名备份到 $BK"
fi
cp -R "$REPO/editor_project/project_lapv8fm0" "$DEST/"
echo "已装好：$DEST/project_lapv8fm0"
echo "打开编辑器（同一个抖音账号登录），首页「最近编辑」或工程列表里找「我的项目」→ 去编辑。"
