from pathlib import Path
from lupa import LuaRuntime
D=Path(__file__).resolve().parent
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute((D/'dragon_progress_rules.body.lua').read_text())
lua.execute('''
for _,kind in ipairs({'grow','shrink','sheep'})do
 local p=New();local op={id='free:'..kind,kind='brew',potion=kind,day=1,now=1}
 local q,msg=Apply(p,op);assert(q,msg)
 assert(q.mushroom==0 and q.flower==0 and q.wool==0 and q.charred==0)
 local repeatQ,_,repeated=Apply(q,op);assert(repeated and repeatQ.revision==q.revision)
end
for _,kind in ipairs({'wind','glow'})do assert(not Apply(New(),{id=kind,kind='brew',potion=kind,day=1,now=1}))end
local p=New();local q,msg=Apply(p,{id='star',kind='stardew',day=1,now=1})
assert(not q and msg:find('蘑菇 3份') and msg:find('月见花 3份') and msg:find('羊毛 1份'))
p.mushroom=3;p.flower=3;p.wool=1
q=assert(Apply(p,{id='star',kind='stardew',day=1,now=1}));assert(q.stardew==1 and q.mushroom==0 and q.flower==0 and q.wool==0)
local again,_,duplicate=Apply(q,{id='star',kind='stardew',day=1,now=1});assert(duplicate and again.stardew==1)
''')
print('PASS: free mystery drinks with zero materials; removed effects rejected; exact stardew shortages; atomic cost/reward and duplicate receipt')
