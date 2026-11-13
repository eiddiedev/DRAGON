"""Exercise contract ownership and native-entry recovery with the real Lua functions."""
from pathlib import Path
import os
from lupa import LuaRuntime

SOURCE = Path(__file__).resolve().parents[1] / 'editor_project/project_lapv8fm0/ai-sessions/workspace_sbazsi67/wprefabs/dragon_phase1_merged/scripts/dragon_exploration.lua'
SOURCE = Path(os.environ.get('DRAGON_SCRIPT_DIR',str(SOURCE.parent))) / SOURCE.name
source = SOURCE.read_text()
lua = LuaRuntime(unpack_returned_tuples=True)
assert lua.eval('load')(source) is not None
clear = source[source.index('local function clearNativeInteraction()'):source.index('local witchPlaced=')]
contract = source[source.index('function OpenContract(respec,continuation)'):source.index('---------------------------------------------------------------- 誓约之书')]
lua.execute('''
local mode,contractSession,nativeExplore,nativePotion,nativeTarget
local removes,opens,continuations=0,0,0
local blocked=false
local actor={locked=false,Immobilize=function(self,value)self.locked=value end}
local main={menu=false,SetExplorationMenu=function(v)mainMenu=v;actor.locked=v end}
local self={RemoveInteractorButton=function(_,button)assert(button);removes=removes+1 end}
local rpg={}
local scope={GetScript=function()return rpg end}
local function unavailable()return blocked end
local function toast(_)end
''' + clear + contract + '''
local callback
rpg.OpenContract=function(_,cb)opens=opens+1;callback=cb;return true end
-- The player remains beside the tree throughout three successive contracts.
for i=1,3 do
 nativeExplore={};nativeTarget={}
 assert(OpenContract(true,function()continuations=continuations+1 end))
 assert(mode=='class' and contractSession and nativeExplore==nil and nativeTarget==nil)
 assert(mainMenu and actor.locked)
 assert(not OpenContract(true,nil)) -- duplicate native click cannot replace callback
 local previous=callback;callback()
 assert(mode==nil and contractSession==nil and not mainMenu and not actor.locked)
 previous() -- late/duplicate completion must not run the continuation twice
 assert(continuations==i)
end
assert(opens==3 and removes==3)
-- Failed opens release menu/player ownership and permit the next attempt.
for _,behavior in ipairs({'false','error'})do
 rpg.OpenContract=function()if behavior=='error'then error('not ready')end;return false end
 nativeExplore={};nativeTarget={}
 assert(not OpenContract(true,nil))
 assert(mode==nil and contractSession==nil and not mainMenu and not actor.locked)
end
blocked=true;assert(not OpenContract(true,nil));assert(mode==nil)
''')
print('PASS: Lua syntax, 3 consecutive contracts, duplicate clicks/completions, failure rollback, mounted/battle rejection')
