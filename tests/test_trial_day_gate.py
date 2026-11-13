from pathlib import Path
from lupa import LuaRuntime
import os
p=Path(os.environ['DRAGON_SCRIPT_DIR']);s=(p/'dragon_combat.lua').read_text()
a=s.index('function Begin(duel)');b=s.index('\nfunction ',a+1)
function=s[a:b]
l=LuaRuntime(unpack_returned_tuples=True)
l.execute('''local night=false;local requested=0
local actor={};local function localActor()return actor end
local rpg={GetProfile=function()return{class='mage'}end,SetMode=function()error('daytime must not enable combat')end}
local function IsNight()return night end
'''+function+'''
local ok,msg=Begin(false);assert(ok==false and msg=='晚上才能挑战影灵')
''')
assert 'showSigil(arenaCenter,ArenaRadius,true)' in s
r=(p/'dragon_rpg.lua').read_text();line=next(x for x in r.splitlines() if 'local showTrial=' in x)
assert 'nearArena' in line and 'IsNight' not in line
print('PASS: daytime click gives night requirement before combat activation; sigil and nearby entry are not night-gated')
