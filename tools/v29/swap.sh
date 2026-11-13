#!/bin/bash
# 用已有的归档回执换根：删旧根 → 导入动物包、玩法包 → 保存。
# 用法：tools/v29/swap.sh <实例ID> <归档回执标签> <本次标签> <旧玩法根ID> <旧角色根ID>
set -uo pipefail
cd "$(dirname "$0")/../.."
I=$1; AT=$2; TAG=$3; OLDG=$4; OLDA=$5; R=assets/review_v29/receipts
ok() { python3 -c "import json,sys;d=json.load(open('$1'));print('$1',json.dumps(d.get('data',d.get('error')),ensure_ascii=False)[:200]);sys.exit(0 if d['ok'] else 1)"; }
front() { open -a "造世界编辑器"; }
front; douyin-world scene remove --args "{\"rootIDs\":[\"$OLDG\",\"$OLDA\"]}" --request-id v29-remove-$TAG --instance $I --timeout-ms 200000 --json > $R/remove-$TAG.json 2>&1; ok $R/remove-$TAG.json || exit 3
for k in actors gameplay; do
  URI=$(python3 -c "import json;print(json.load(open('$R/archive-$k-$AT.json'))['data']['uri'])")
  front; douyin-world scene import --uri "$URI" --request-id v29-import-$k-$TAG --instance $I --timeout-ms 290000 --json > $R/import-$k-$TAG.json 2>&1; ok $R/import-$k-$TAG.json || exit 4
done
front; douyin-world scene save --request-id v29-save-$TAG --instance $I --timeout-ms 240000 --json > $R/save-$TAG.json 2>&1; ok $R/save-$TAG.json || exit 5
