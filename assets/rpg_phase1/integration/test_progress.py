from pathlib import Path
from lupa import LuaRuntime
D=Path(__file__).resolve().parent
L=LuaRuntime(unpack_returned_tuples=True)
L.execute((D/'dragon_progress_rules.body.lua').read_text())
L.execute('''
local a,b=New(),New()
local n=0
local function op(kind,args,day,now)
 n=n+1;local x=args or{};x.kind=kind;x.id='session:'..n;x.day=day or 10;x.now=now or n;return x
end
local function apply(p,kind,args,day,now)
 local q,err=Apply(p,op(kind,args,day,now));assert(q,err);return q
end
a=apply(a,'class',{class='mage'});assert(b.class==nil)
for i=1,5 do a=apply(a,'gather',{material='mushroom',isDay=true})end
assert(not Apply(a,op('gather',{material='mushroom',isDay=true})))
assert(not Apply(a,op('gather',{material='flower',isDay=false})))
a=apply(a,'gather',{material='mushroom',isDay=true},11)
assert(a.mushroom==6 and a.daily.mushroom==1 and b.mushroom==0)
local reward=op('battle',{battleId='round-unique',amount=10},11)
a=assert(Apply(a,reward));a=assert(Apply(a,reward));assert(a.moon==10)
a=apply(a,'battle',{battleId='round-unique',amount=10},11);assert(a.moon==10)
a=apply(a,'class',{class='melee'},11);assert(a.moon==10 and a.mushroom==6)
for i=1,2 do a=apply(a,'battle',{battleId='round-'..i,amount=10},11)end
-- First partial offering and repeated clicks cannot spend already offered resources.
a=apply(a,'deposit',{},11);assert(a.deposited.moon==30 and a.moon==0 and not a.pact)
assert(not Apply(a,op('deposit',{},11)))
-- Cooking thresholds use distinct isolated profiles; exact endpoints checked.
for _,case in ipairs({{.54,0,0},{.55,1,0},{.68,1,0},{.69,0,0},{.85,0,0},{.86,0,1}})do
 local p=New();p.mushroom=1
 local start=op('cookStart',{duration=5},11,100)
 p=assert(Apply(p,start))
 p=apply(p,'cookFinish',{token=start.id},11,100+case[1]*5)
 assert(p.ember==case[2] and p.charred==case[3])
 assert(not Apply(p,op('cookFinish',{token=start.id},11,105)))
end
-- Durable profile round-trip preserves rewards and counters.
local copied=Copy(a);assert(Validate(copied));assert(copied.battles['round-unique'])
assert(b.moon==0 and b.deposited.moon==0)
''')
print('PASS: player isolation, day quotas, night refusal, class retention, reward retry dedupe, partial offerings, six cooking boundaries')
for p in D.glob('*.body.lua'):
 err=L.eval('function(s) local f,e=load(s);return e end')(p.read_text())
 assert err is None,(p.name,err)
print('PASS: integration source syntax')
