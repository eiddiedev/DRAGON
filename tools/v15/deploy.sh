#!/bin/bash
# v15 部署：作者包 validate → build → 归档 → 停预览 → 删旧根 → 导入 → 保存 → 运行
# 用法：tools/v15/deploy.sh <实例ID> <本次标签> <要删除的旧根ID，没有就写 none>
# 归档必须在前台实例里做（后台实例生成不了缩略图，会一直超时）。
set -uo pipefail
cd "$(dirname "$0")/../.."
I=$1; TAG=$2; OLD=$3
R=assets/layout_v15/receipts; mkdir -p $R
W="--workspace-id workspace_sbazsi67 --instance $I"
step() { echo "== $1"; }
ok() { python3 -c "import json,sys;d=json.load(open('$1'));print(json.dumps(d.get('data',d.get('error')),ensure_ascii=False)[:260]);sys.exit(0 if d['ok'] else 1)"; }
step validate; douyin-world authoring prefab validate dragon_phase1_merged $W --json > $R/validate-$TAG.json 2>&1; ok $R/validate-$TAG.json || exit 1
step build; douyin-world authoring prefab build dragon_phase1_merged $W --json > $R/build-$TAG.json 2>&1; ok $R/build-$TAG.json || exit 1
step archive; douyin-world authoring result archive dragon_phase1_merged $W --name "龙眠玩法与界面v15" --timeout-ms 240000 --json > $R/archive-$TAG.json 2>&1; ok $R/archive-$TAG.json || exit 1
URI=$(python3 -c "import json;print(json.load(open('$R/archive-$TAG.json'))['data']['uri'])")
step stop; douyin-world runtime stop --instance $I --json 2>&1 | head -c 160; echo
[ "$OLD" = none ] || { step remove; douyin-world scene remove --args "{\"rootIDs\":[\"$OLD\"]}" --request-id v15-remove-$TAG --instance $I --timeout-ms 200000 --json > $R/remove-$TAG.json 2>&1; ok $R/remove-$TAG.json || exit 1; }
step import; douyin-world scene import --uri "$URI" --request-id v15-import-$TAG --instance $I --timeout-ms 240000 --json > $R/import-$TAG.json 2>&1; ok $R/import-$TAG.json || exit 1
step save; douyin-world scene save --request-id v15-save-$TAG --instance $I --timeout-ms 240000 --json > $R/save-$TAG.json 2>&1; ok $R/save-$TAG.json || exit 1
step run; douyin-world runtime start --instance $I --timeout-ms 240000 --json > $R/run-$TAG.json 2>&1; ok $R/run-$TAG.json
