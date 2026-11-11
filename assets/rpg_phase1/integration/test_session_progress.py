"""Verify session-only integration without any cloud API mock."""
from lupa import LuaRuntime
from pathlib import Path
D=Path(__file__).resolve().parent
lua=LuaRuntime(unpack_returned_tuples=True)
rules=lua.execute('local _ENV=setmetatable({}, {__index=_G}); '+(D/'dragon_progress_rules.body.lua').read_text()+'\nreturn _ENV')
lua.globals().rulesMock=rules
lua.execute("self={}; PreviewOnly=false; CS={DouyinUtility={GetServerUnixTime=function() return 1794384000 end,GetServerTime=function() return {Millisecond=0} end}}; package.preload['official.core.runtime_scope']=function() return {from=function()return {GetScript=function()return rulesMock end}end}end")
source=(D/'dragon_progress.body.lua').read_text()
assert 'DATASTORE' not in source and 'GetDataStore' not in source
lua.execute(source)
assert lua.eval('IsLoaded()')
assert lua.eval("SelectClass('mage')")[0]
assert lua.eval("AwardBattle('round-1',10)")[0]
assert lua.eval("AwardBattle('round-1',10)")[0]
assert lua.eval('GetProfile().moon')==99999
assert lua.eval("GetProfile().battles['round-1']") is True
assert lua.eval('GetProfile().potions.sheep')==99
assert lua.eval('GetStatus().persistent') is False
lua.execute(source)
assert lua.eval('GetProfile().moon')==99999
assert lua.eval('GetProfile().class') is None
print('PASS: no cloud dependency, immediate ready, class selection, battle reward dedupe, fresh session reset and explicit unlimited-resource QA mode')
