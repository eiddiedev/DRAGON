#!/usr/bin/env python3
"""把 scripts/ui_v1.lua（填好排版数据）嵌进 world_main_v5.lua 的 UI 标记之间。"""
import json, re
ROOT = '/Users/bytedance/Documents/ChatGPT/DRAGON'
L = json.load(open(f'{ROOT}/assets/ui/layout.json'))


def lua(v, ind=''):
    if isinstance(v, dict):
        return '{ ' + ', '.join(f'{k} = {lua(x)}' if re.match(r'^[A-Za-z_]\w*$', k) else f'["{k}"] = {lua(x)}' for k, x in v.items()) + ' }'
    if isinstance(v, list):
        return '{ ' + ', '.join(lua(x) for x in v) + ' }'
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, bool):
        return 'true' if v else 'false'
    return repr(round(v, 6)) if isinstance(v, float) else str(v)


ui = open(f'{ROOT}/scripts/ui_v1.lua').read().replace('--@@LAYOUT@@', lua(L))
p = f'{ROOT}/scripts/world_main_v5.lua'
s = open(p).read()
A, B = '-- @@UI BEGIN\n', '-- @@UI END\n'
if A in s:
    s = s[:s.index(A)] + A + ui + B + s[s.index(B) + len(B):]
else:
    i = s.index('function Update()')
    s = s[:i] + A + ui + B + '\n' + s[i:]
open(p, 'w').write(s)
print('embedded', len(ui))
