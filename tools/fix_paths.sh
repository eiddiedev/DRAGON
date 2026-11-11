#!/bin/bash
# 换电脑后运行一次：把工具脚本里写死的 /Users/bytedance/Documents/ChatGPT/DRAGON 换成当前仓库所在路径。
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OLD="/Users/bytedance/Documents/ChatGPT/DRAGON"
if [ "$REPO" = "$OLD" ]; then echo "路径一致，无需修改"; exit 0; fi
grep -rl "$OLD" "$REPO/tools" "$REPO/scripts" | while read -r f; do
  sed -i '' "s#$OLD#$REPO#g" "$f"
  echo "改了 $f"
done
