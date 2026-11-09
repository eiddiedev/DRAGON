#!/usr/bin/env python3
"""把脚本写进工程：install_lua5.py [debug|release]。只能在编辑器回到主页时运行。"""
import json, os, re, sys, zipfile
mode = sys.argv[1] if len(sys.argv) > 1 else 'debug'
P = os.path.expanduser('~/Library/Application Support/AI World Creator/projects/project_lapv8fm0')
src = open('/Users/a1234/Documents/awesomeWRLD/scripts/world_main_v5.lua').read()
if mode == 'debug':
    src = src.replace('local DEBUG_TELEPORT = false', 'local DEBUG_TELEPORT = true', 1)
open(f'{P}/scripts/modules/world_main.lua', 'w').write(src)
sc = f'{P}/scene.data'
z = zipfile.ZipFile(sc)
d = json.loads(z.read('SerializePcgData.json'))
d['runtimeScripts']['a87ebe50-812d-4151-a056-727a118aecbd']['content'] = src
tmp = sc + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as w:
    for i in z.infolist():
        data = z.read(i.filename)
        if i.filename == 'SerializePcgData.json':
            data = json.dumps(d, ensure_ascii=False, separators=(',', ':')).encode()
        ni = zipfile.ZipInfo(i.filename, i.date_time)
        ni.compress_type = zipfile.ZIP_DEFLATED
        ni.external_attr = i.external_attr
        w.writestr(ni, data)
os.replace(tmp, sc)
print('installed', mode, len(src))
