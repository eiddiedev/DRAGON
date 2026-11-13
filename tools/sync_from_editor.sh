#!/bin/bash
# 把编辑器里的最新工程同步回仓库（提交前运行）。编辑器要先回到首页，保证 scene.data 已保存。
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$HOME/Library/Application Support/AI World Creator/projects/project-55a43370-8734-4825-92a8-b0de824a45e2"
mkdir -p "$REPO/editor_project"
rsync -a --delete --exclude '.DS_Store' --exclude '*_log/' --exclude '.awc/' --exclude '*.bak' --exclude 'scene.before-*.data' "$SRC/" "$REPO/editor_project/project_lapv8fm0/"
echo "已同步 $SRC → editor_project/"
