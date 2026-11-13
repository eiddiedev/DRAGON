"""Run the actual bridge camera/input-lease functions, without the editor."""
from pathlib import Path
from lupa import LuaRuntime
SOURCE=(Path(__file__).resolve().parent/'dragon_world_bridge.lua').read_text()
def chunk(start,end):
 p=SOURCE.index(start);return SOURCE[p:SOURCE.index(end,p)]
vm=LuaRuntime(unpack_returned_tuples=True)
assert not isinstance(vm.eval('load')(SOURCE),tuple)
functions=chunk('function UI.camStart()','function UI.camTitle(t)')+chunk('function UI.camEnd()','function UI.setSpread(k)')
cleanup=SOURCE[SOURCE.index('-- review-v28: presentation teardown'):]
vm.execute('''
local destroyed,locks,unlocks,shows,hides=0,0,0,0,0
local main={enabled=true,depth=2}
local UI={}
local DR={phase1={scope={}}}
local participating,preparing=false,false
local battle={IsParticipating=function()return participating end,GetStatus=function()return{member=preparing,phase=preparing and 'ready' or 'idle'}end}
function DR.phase1.scope:GetScript()return battle end
local UnityEngine={Camera={main=main},Object={Destroy=function(go)assert(not go.destroyed);go.destroyed=true;destroyed=destroyed+1 end}}
UnityEngine.GameObject=function(name)
 local go={name=name}
 function go:AddComponent()
  local cam={gameObject=go,CopyFrom=function()end};return cam
 end
 function go:GetComponent()return nil end
 return go
end
local CS={}
function typeof(v)return v end
local DouyinUIService={
 SetUIVisible=function(show)if show then shows=shows+1 else hides=hides+1 end end,
 SetNativeUIVisible=function(show)if show then shows=shows+1 else hides=hides+1 end end,
}
local actor={gameObject={transform={parent=nil}},sitting=false,flying=false,locked=false}
function actor:IsSitting()return self.sitting end
function actor:IsFlying()return self.flying end
function actor:Immobilize(on)self.locked=on;if on then locks=locks+1 else unlocks=unlocks+1 end end
'''+functions+'''
local disableCalls,destroyCalls=0,0
function OnDisable()disableCalls=disableCalls+1 end
function OnDestroy()destroyCalls=destroyCalls+1 end
'''+cleanup+'''
-- 1. Normal title end and book completion restore the exact captured camera flag.
UI.camStart();assert(main.enabled==false and UI.cam)
assert(UI.lockPlayer(actor,true));assert(actor.locked and UI.inputLease)
assert(UI.lockPlayer(actor,true));assert(locks==1) -- repeat acquisition is idempotent
UI.camEnd();assert(main.enabled and destroyed==1)
assert(UI.lockPlayer(actor,false));assert(not actor.locked and unlocks==1 and shows==2)
UI.releasePresentation();assert(destroyed==1 and unlocks==1)
-- An originally disabled main camera must remain disabled.
main.enabled=false;UI.camStart();UI.camEnd();assert(main.enabled==false and destroyed==2)
main.enabled=true
-- 2. Abnormal Disable followed by Destroy returns the owned lease/camera once.
UI.camStart();UI.lockPlayer(actor,true)
OnDisable();assert(main.enabled and not actor.locked and destroyed==3 and unlocks==2)
OnDestroy();assert(destroyed==3 and unlocks==2 and disableCalls==1 and destroyCalls==1)
-- 3. Repeated lifecycle calls do not touch an unrelated lock/main-camera change.
main.enabled=false;actor.locked=true
local beforeShows=shows
OnDisable();OnDestroy()
assert(main.enabled==false and actor.locked and unlocks==2 and shows==beforeShows)
assert(not UI.lockPlayer(actor,false))
-- 4. No lease: even an explicit close cannot release another controller.
actor.sitting=true;assert(not UI.lockPlayer(actor,true));OnDisable()
assert(actor.locked and unlocks==2)
actor.sitting=false;actor.locked=false;main.enabled=true
-- Riding, boat reparenting, live combat and battle preparation can supersede a lease.
for _,mode in ipairs({'riding','flying','dragon','boat','combat','preparation'})do
 actor.gameObject.transform.parent=nil;actor.sitting=false;actor.flying=false;DR.rider=nil;participating=false;preparing=false
 assert(UI.lockPlayer(actor,true));local beforeUnlock=unlocks;local beforeVisible=shows
 if mode=='riding'then actor.sitting=true elseif mode=='flying'then actor.flying=true elseif mode=='dragon'then DR.rider=actor elseif mode=='boat'then actor.gameObject.transform.parent={} elseif mode=='combat'then participating=true elseif mode=='preparation'then preparing=true end
 OnDisable()
 assert(actor.locked and unlocks==beforeUnlock and shows==beforeVisible and UI.inputLease==nil,mode)
end
''')
print('PASS: normal completion, interrupted Disable/Destroy, repeated cleanup, no lease, originally-disabled camera, and six foreign-owner handoffs')
