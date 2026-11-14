#!/usr/bin/env python3
"""去掉河道节点下累积的空触发器壳子（__DouyinWaterArea2Triggers / Trigger_*）。用户已于 2026-11-14 明确同意。

这些子节点没有任何碰撞或触发器数据，编辑器每保存一次就多写一组（每组 1744 个）。
隔离副本里实测：删光后本地河、海照常游泳，运行时会自己生成真正的触发器。
官方 `scene remove` 拒绝删它们（scene-node-protected），所以只能在**编辑器关闭时**直接改 scene.data。
之后在编辑器里每保存一次会再写回一组；提审前最后一步运行本脚本。
用法：python3 tools/v30/strip_water_shells.py [scene.data 路径]
"""
import collections, hashlib, json, os, shutil, sys, time, zipfile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    '~/Library/Application Support/AI World Creator/projects/project-55a43370-8734-4825-92a8-b0de824a45e2/scene.data')
z = zipfile.ZipFile(P)
s = json.loads(z.read('SerializePcgData.json'))
ns = s['nodeTransformDatas']
kids = collections.defaultdict(list)
for n in ns:
    kids[n['basic']['parentId']].append(n)
drop = set()
for g in ns:
    if g['basic']['nodeName'] != '__DouyinWaterArea2Triggers':
        continue
    members = kids[g['id']]
    # 只删确认是空壳的：子节点都叫 Trigger_*、没有孙节点、没有任何碰撞 / 触发器 / 资源 / 脚本数据
    safe = all(k['basic']['nodeName'].startswith('Trigger_') and not kids[k['id']]
               and not (k.get('physics') or {}).get('physicsColliderData') and not (k.get('physics') or {}).get('triggerData')
               and not k.get('resource') and not k.get('runtimeScriptBindings') for k in members)
    if not safe:
        print('skip group', g['id'], '(not an empty shell)')
        continue
    drop.add(g['id'])
    drop.update(k['id'] for k in members)
if not drop:
    print('nothing to strip')
    sys.exit(0)
bdir = f'{REPO}/backups/before-strip'
os.makedirs(bdir, exist_ok=True)
bk = f'{bdir}/scene.{time.strftime("%Y%m%d-%H%M%S")}.data'
shutil.copy2(P, bk)
s['nodeTransformDatas'] = [n for n in ns if n['id'] not in drop]
tmp = P + '.tmp'
with zipfile.ZipFile(tmp, 'w') as out:
    for info in z.infolist():
        data = z.read(info.filename)
        if info.filename == 'SerializePcgData.json':
            data = json.dumps(s, ensure_ascii=False, separators=(',', ':')).encode('utf8')
        ni = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        ni.compress_type = info.compress_type
        ni.external_attr = info.external_attr
        out.writestr(ni, data)
assert zipfile.ZipFile(tmp).testzip() is None
os.replace(tmp, P)
print('nodes', len(ns), '->', len(s['nodeTransformDatas']), 'backup', bk)
print('sha256', hashlib.sha256(open(P, 'rb').read()).hexdigest(), os.path.getsize(P))
