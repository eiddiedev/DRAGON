#!/usr/bin/env python3
"""Install runtime scripts with the project closed: install_lua5.py [debug|release]."""
import argparse
import json
import os
from pathlib import Path
import zipfile
from music.build_desktop_bgm import build_module

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('mode', nargs='?', choices=['debug', 'release'], default='debug')
parser.add_argument('--project', type=Path, default=Path.home() / 'Library/Application Support/AI World Creator/projects/project_lapv8fm0')
args = parser.parse_args()
src = (ROOT / 'scripts/world_main_v5.lua').read_text()
if args.mode == 'debug':
    src = src.replace('local DEBUG_TELEPORT = false', 'local DEBUG_TELEPORT = true', 1)
# The editor only registers its bound script reliably. Bundle helper code and
# PCM into that script; do not depend on dynamic user-module discovery.
player = (ROOT / 'scripts/desktop_bgm.lua').read_text()
player = player.replace('require("modules.desktop_bgm_data")', '(function()\n' + build_module() + '\nend)()')
src = src.replace('require("modules.desktop_bgm")', '(function()\n' + player + '\nend)()')
modules = {'modules/world_main.lua': src}
scene = args.project / 'scene.data'
with zipfile.ZipFile(scene) as archive:
    entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
data = json.loads(next(raw for info, raw in entries if info.filename == 'SerializePcgData.json'))
data['runtimeScripts']['a87ebe50-812d-4151-a056-727a118aecbd']['content'] = src
for old in ('modules/desktop_bgm.lua', 'modules/desktop_bgm_data.lua'):
    data['runtimeScripts'].pop(old, None)
    path = args.project / 'scripts' / old
    if path.exists():
        path.unlink()
tmp = scene.with_suffix('.data.tmp')
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as archive:
    for info, raw in entries:
        if info.filename == 'SerializePcgData.json':
            raw = json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode()
        archive.writestr(info, raw)
for name, content in modules.items():
    path = args.project / 'scripts' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
os.replace(tmp, scene)
print('installed', args.mode, 'with desktop background music:', args.project)
