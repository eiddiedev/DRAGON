#!/bin/bash
# v29 部署：两个作者包 validate → build → 归档，然后删旧根 → 导入 → 保存。
# 用法：tools/v29/deploy.sh <实例ID> <标签> <旧玩法根ID> <旧角色根ID>
# 归档要在前台实例里做；导入和保存时编辑器窗口保持在最前。超时不要换参数重试，先查原 requestId。
set -uo pipefail
cd "$(dirname "$0")/../.."
I=$1; TAG=$2; OLDG=$3; OLDA=$4
R=assets/review_v29/receipts; mkdir -p $R
ok() { python3 -c "import json,sys;d=json.load(open('$1'));print('$1',json.dumps(d.get('data',d.get('error')),ensure_ascii=False)[:170]);sys.exit(0 if d['ok'] else 1)"; }
front() { open -a "造世界编辑器"; }
for pf in gameplay_v29 actors_v29; do
  front; douyin-world authoring prefab validate $pf --workspace-id workspace_l7e231w9 --instance $I --timeout-ms 120000 --json > $R/validate-$pf-$TAG.json 2>&1; ok $R/validate-$pf-$TAG.json || exit 1
  front; douyin-world authoring prefab build $pf --workspace-id workspace_l7e231w9 --instance $I --timeout-ms 240000 --json > $R/build-$pf-$TAG.json 2>&1; ok $R/build-$pf-$TAG.json || exit 1
done
front; douyin-world authoring result archive gameplay_v29 --workspace-id workspace_l7e231w9 --instance $I --name "龙眠玩法v29" --timeout-ms 280000 --json > $R/archive-gameplay-$TAG.json 2>&1; ok $R/archive-gameplay-$TAG.json || exit 2
front; douyin-world authoring result archive actors_v29 --workspace-id workspace_l7e231w9 --instance $I --name "龙眠动物v29" --timeout-ms 280000 --json > $R/archive-actors-$TAG.json 2>&1; ok $R/archive-actors-$TAG.json || exit 2
[ "${ARCHIVE_ONLY:-}" = 1 ] && exit 0
front; douyin-world scene remove --args "{\"rootIDs\":[\"$OLDG\",\"$OLDA\"]}" --request-id v29-remove-$TAG --instance $I --timeout-ms 200000 --json > $R/remove-$TAG.json 2>&1; ok $R/remove-$TAG.json || exit 3
for k in actors gameplay; do
  URI=$(python3 -c "import json;print(json.load(open('$R/archive-$k-$TAG.json'))['data']['uri'])")
  front; douyin-world scene import --uri "$URI" --request-id v29-import-$k-$TAG --instance $I --timeout-ms 290000 --json > $R/import-$k-$TAG.json 2>&1; ok $R/import-$k-$TAG.json || exit 4
done
front; douyin-world scene save --request-id v29-save-$TAG --instance $I --timeout-ms 240000 --json > $R/save-$TAG.json 2>&1; ok $R/save-$TAG.json || exit 5
