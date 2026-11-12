#!/bin/bash
# 保存撞上编辑器 "table index is out of bounds" 故障后用：重启前台实例，删旧根→保存→导入→保存→运行。
# 用法：tools/v15/reimport.sh <归档回执json> <旧根ID> <标签>
set -uo pipefail
cd "$(dirname "$0")/../.."
S=${SCRATCH:-/tmp}; ARCH=$1; OLD=$2; TAG=$3
P="$HOME/Library/Application Support/AI World Creator/projects/project_lapv8fm0"; R=assets/layout_v15/receipts
I=$(cat $S/instance_id 2>/dev/null || true)
[ -n "$I" ] && douyin-world instance stop --instance $I --json >/dev/null 2>&1
until ! pgrep -f "造世界编辑器.app/Contents/MacOS" >/dev/null; do sleep 2; done
douyin-world instance start --project "$P" --mode foreground --startup-timeout 240 --json > $S/inst.json 2>&1
python3 -c "import json;d=json.load(open('$S/inst.json'));print(d['data']['instanceId'],file=open('$S/instance_id','w'))" || exit 1
I=$(cat $S/instance_id)
until douyin-world instance status --instance $I --json 2>&1 | grep -q '"ready":true'; do sleep 5; done
ok() { python3 -c "import json,sys;d=json.load(open('$1'));print('$1',json.dumps(d.get('data',d.get('error')),ensure_ascii=False)[:200]);sys.exit(0 if d['ok'] else 1)"; }
URI=$(python3 -c "import json;print(json.load(open('$ARCH'))['data']['uri'])")
douyin-world scene remove --args "{\"rootIDs\":[\"$OLD\"]}" --request-id v15-remove-$TAG --instance $I --timeout-ms 200000 --json > $R/remove-$TAG.json 2>&1; ok $R/remove-$TAG.json || exit 1
douyin-world scene save --request-id v15-save-$TAG-a --instance $I --timeout-ms 240000 --json > $R/save-$TAG-a.json 2>&1; ok $R/save-$TAG-a.json || exit 2
douyin-world scene import --uri "$URI" --request-id v15-import-$TAG --instance $I --timeout-ms 240000 --json > $R/import-$TAG.json 2>&1; ok $R/import-$TAG.json || exit 1
douyin-world scene save --request-id v15-save-$TAG-b --instance $I --timeout-ms 240000 --json > $R/save-$TAG-b.json 2>&1; ok $R/save-$TAG-b.json || exit 3
douyin-world runtime start --instance $I --timeout-ms 240000 --json > $R/run-$TAG.json 2>&1; ok $R/run-$TAG.json
