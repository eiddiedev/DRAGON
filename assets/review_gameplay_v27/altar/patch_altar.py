from pathlib import Path
ROOT=Path(__file__).resolve().parent
def patch(s):
 a=s.index('local function setupAltar()');b=s.index('---- 冰龙：',a)
 if 'v27-progress-altar' in s[a:b]:raise ValueError('Already applied')
 return s[:a]+(ROOT/'controller.lua').read_text()+'\n'+s[b:]
