from pathlib import Path
import os
from lupa import LuaRuntime
p=Path(__file__).resolve().parents[1]/'editor_project/project_lapv8fm0/ai-sessions/workspace_sbazsi67/wprefabs/dragon_phase1_merged/scripts'
p=Path(os.environ.get('DRAGON_SCRIPT_DIR',str(p)))
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute((p/'dragon_progress_rules.lua').read_text())
lua.execute('''rules={New=New,Copy=Copy,Apply=Apply}
self={};package.preload['official.core.runtime_scope']=function()return{from=function()return{GetScript=function()return rules end}end}end
CS={DouyinUtility={GetServerUnixTime=function()return 1794400000 end,GetServerTime=function()return{Millisecond=0}end}}
''')
lua.execute((p/'dragon_progress.lua').read_text())
lua.execute('''
assert(IsLoaded());assert(not GetStatus().testMode and not GetStatus().persistent)
local p=GetProfile();assert(p.moon==0 and p.mushroom==0 and p.ember==0 and p.stardew==0)
assert(not Submit('stardew',{}));assert(not Submit('roast',{hit=true}))
for i=1,5 do assert(Submit('gather',{material='mushroom',isDay=true}))end
assert(not Submit('gather',{material='mushroom',isDay=true}))
assert(Submit('roast',{hit=true}));assert(GetProfile().mushroom==4 and GetProfile().ember==1)
assert(SelectClass('mage'));assert(GetProfile().mushroom==4 and GetProfile().daily.mushroom==5)
for i=1,3 do assert(Submit('gather',{material='flower',isDay=true}))end
assert(Submit('gather',{material='wool',isDay=true}));assert(Submit('stardew',{}))
p=GetProfile();assert(p.mushroom==1 and p.flower==0 and p.wool==0 and p.stardew==1)
assert(AwardBattle('battle-test',30));assert(AwardBattle('battle-test',30));assert(GetProfile().moon==30)
assert(Submit('deposit',{}));p=GetProfile();assert(p.moon==0 and p.stardew==0 and p.ember==0)
assert(p.deposited.moon==30 and p.deposited.stardew==1 and p.deposited.ember==1)
assert(not Submit('hatch',{}));assert(Submit('brew',{potion='sheep'}))
for i=1,100 do Update();GetProfile()end
assert(GetProfile().moon==0 and GetProfile().daily.mushroom==5)
''')
print('PASS: zero starting resources, real recipe/roast costs, daily quota retained, class change preserves balance, battle deduplication, deposits, free mystery potion, no periodic refills')
