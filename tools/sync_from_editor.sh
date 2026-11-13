#!/bin/bash
# 把编辑器里的最新工程同步回仓库（提交前运行）。先确认目标工程保存完成并关闭其编辑实例；无需切走其他前台工程。
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$HOME/Library/Application Support/AI World Creator/projects/project-55a43370-8734-4825-92a8-b0de824a45e2"
mkdir -p "$REPO/editor_project"
# 保留仓库中已有、但正式工程没有的历史制作源；不要因运行工程精简而删掉可编辑资产。
rsync -a --delete --filter 'P ai-sessions/***' --exclude '.DS_Store' --exclude '*_log/' --exclude '.awc/' --exclude '*.bak' --exclude 'scene.before-*.data' "$SRC/" "$REPO/editor_project/project_lapv8fm0/"
echo "已同步 $SRC → editor_project/"
