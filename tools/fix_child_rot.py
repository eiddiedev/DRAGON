#!/usr/bin/env python3
"""把模型根节点的旋转写到它的子节点（main、glow）上。子节点存的是世界变换，只转父节点不生效。
用法：fix_child_rot.py <输入 scene.data> <输出 scene.data>
"""
import json
import sys
import zipfile

src, out = sys.argv[1:3]
z = zipfile.ZipFile(src)
d = json.loads(z.read('SerializePcgData.json'))
N = d['nodeTransformDatas']
by_id = {n['id']: n for n in N}
fixed = 0
for n in N:
    parent = by_id.get(n['parentId'])
    if parent is None or parent['parentId'] != 0 or n['nodeName'] not in ('main', 'glow'):
        continue
    if n['rot'] != parent['rot']:
        n['rot'] = dict(parent['rot'])
        fixed += 1
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as w:
    for i in z.infolist():
        data = z.read(i.filename)
        if i.filename == 'SerializePcgData.json':
            data = json.dumps(d, ensure_ascii=False, separators=(',', ':')).encode()
        ni = zipfile.ZipInfo(i.filename, i.date_time)
        ni.compress_type = zipfile.ZIP_DEFLATED
        ni.external_attr = i.external_attr
        w.writestr(ni, data)
print('fixed', fixed, 'nodes', len(N))
