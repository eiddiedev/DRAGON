from pathlib import Path
from lupa import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True);lua.execute((Path(__file__).parent/'dragon_rules.body.lua').read_text())
g=lua.globals();p=g.NewProfile();assert g.SelectClass(p,'mage',False) is True
ctx=lua.table_from({'class':'mage','mode':'combat'})
a=g.TryAction(ctx,'skill',0);assert a['hitAt']==.3
assert g.TryAction(ctx,'skill',1)[0] is None
ctx['mode']='explore';assert g.TryAction(ctx,'attack',2)[0] is None
ctx['mode']='combat';ctx['mounted']=True;assert g.TryAction(ctx,'attack',3)[0] is None
ctx['mounted']=False;ctx['class']='melee';assert g.TryAction(ctx,'skill',5)[0]is None # respec cannot reset prior cooldown
assert g.TryAction(ctx,'skill',6)['class']=='melee'
assert g.RewardVictory(p,'battle-1',True,True) is True
assert g.RewardVictory(p,'battle-1',True,True) is False
assert g.RewardVictory(p,'battle-2',False,True) is False
assert g.RewardVictory(p,'battle-3',True,False) is False
assert p['moon']==10
p['ember']=3;p['stardew']=1;_,pact=g.Deposit(p);assert not pact and p['deposited']['moon']==10
p['moon']=25;_,pact=g.Deposit(p);assert pact and p['moon']==5
assert g.Deposit(p)[0]==0
assert g.SelectClass(p,'ranged',True)[0]is False
assert g.InsideCircle(167,27,157,27,10)
x,z=g.ClampCircle(157,47,157,27,10);assert abs(x-157)<1e-9 and abs(z-37)<1e-9
print('PASS: action cooldowns, menu/mount guards, respec cooldown carry-over, reward idempotency/eligibility, partial deposit/pact, arena boundary')
