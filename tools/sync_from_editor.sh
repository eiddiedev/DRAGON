#!/bin/bash
# 把编辑器里的最新工程同步回仓库（提交前运行）。编辑器要先回到首页，保证 scene.data 已保存。
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$HOME/Library/Application Support/AI World Creator/projects/project_lapv8fm0"
mkdir -p "$REPO/editor_project"
rsync -a --delete --exclude '.DS_Store' "$SRC/" "$REPO/editor_project/project_lapv8fm0/"
cp "$REPO/scripts/world_main_v5.lua" "$REPO/scripts/world_main.lua"
echo "已同步 $SRC → editor_project/"
