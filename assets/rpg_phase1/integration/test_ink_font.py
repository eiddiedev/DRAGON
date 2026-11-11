from pathlib import Path
import re,json
from lupa import LuaRuntime
s=Path(__file__).with_name('dragon_world_bridge.body.lua').read_text()
raw=re.search(r'UI.inkGlyphData=dkjson.decode\(\[==\[(.*?)\]==\]\)',s,re.S)[1]
d=json.loads(raw)
for c in '守夜人誓约选择职业后签约世界时间蘑菇月见花羊毛收起':
 assert c in d['glyphs'],c
 assert 0<=d['glyphs'][c][0]<d['cols']*d['rows']
assert '\\' in d['glyphs']
l=LuaRuntime();assert l.eval('function(s) return load(s)~=nil end')(s)
print('PASS: embedded glyph JSON escaping, class/quest/time glyph coverage, Lua syntax')
