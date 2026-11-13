"""Run real candidate Lua lifecycle functions with engine stubs; never open a scene."""
from pathlib import Path
import json, re
from lupa import LuaRuntime
D=Path(__file__).parent
ROOT=D.parents[2]

def patched(source, patch):
    # Apply only exact unified-diff hunks in memory. Source drift fails closed.
    lines=source.splitlines(True); changes=patch.splitlines(True); out=[]; pos=0; i=2
    while i<len(changes):
        m=re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',changes[i])
        assert m, changes[i]
        target=int(m.group(1))-1; out.extend(lines[pos:target]);pos=target;i+=1
        while i<len(changes) and not changes[i].startswith('@@'):
            row=changes[i];i+=1
            if row[0] in ' -':
                assert pos<len(lines) and lines[pos]==row[1:], 'source drift'
                if row[0]==' ':out.append(lines[pos])
                pos+=1
            elif row[0]=='+':out.append(row[1:])
            else:raise AssertionError(row)
    out.extend(lines[pos:]); return ''.join(out)

PRELUDE='''
local vector={};vector.__index=vector
vector.__add=function(a,b)return setmetatable({x=a.x+b.x,y=a.y+b.y,z=a.z+b.z},vector)end
vector.__mul=function(a,b)return setmetatable({x=a.x*b,y=a.y*b,z=a.z*b},vector)end
local V=setmetatable({},{__call=function(_,x,y,z)return setmetatable({x=x,y=y,z=z},vector)end})
V.down=V(0,-1,0)
CS={UnityEngine={Vector3=V,Time={realtimeSinceStartup=0},Collider='Collider',
Debug={Log=function()end,LogWarning=function()end},QueryTriggerInteraction={Ignore=1},
Physics={RaycastAll=function()return {Length=0}end},Object={Destroy=function()end}}}
CS.ModularAnim={Runtime={UGCAnimator='UGC'}}
typeof=function(t)return t end
self={gameObject={GetComponent=function()return nil end},transform={position=V(1,2,3),right=V(1,0,0)},
DisableInteraction=function()end,RemoveInteractorButton=function()end}
DouyinCameraService={SetDistance=function()end}
local signal={RemoveListener=function()end}
DouyinInputService={onMoveInputPerform=signal,onMoveInputCancel=signal}
'''
SETUP='''
local originalParent={name='actor original parent'}
local good={enabled=false};local alreadyOff={enabled=false};local unrelated={enabled=false}
local removed=setmetatable({},{__newindex=function()error('destroyed collider')end})
local actor={isLocal=true,gameObject={transform={}},teleports=0,standups=0,immobilized=true,jumpHeight=0}
function actor.gameObject.transform:SetParent(parent,keepWorld)self.parent=parent end
function actor:Teleport(position,rotation)self.teleports=self.teleports+1;self.position=position end
function actor:Immobilize(value)self.immobilized=value end
function actor:StandUp(go)
 self.standups=self.standups+1
 if standMode=='sync' then OnSeatExited(self) elseif standMode=='throws' then error('native seat unavailable')end
end
local state={scale='originalScale',parent=originalParent,position=CS.UnityEngine.Vector3(4,5,6),rotation='originalRotation',jumpHeight=2.4,
colliders={{c=good,enabled=true},{c=removed,enabled=true},{c=alreadyOff,enabled=false}}}
'''
SEAT_TEST='''
saved[actor]=state;seated[actor]=true;passenger=actor
OnDisable()
assert(good.enabled and not alreadyOff.enabled and not unrelated.enabled,'collider ownership restore')
assert(actor.gameObject.transform.parent==originalParent and actor.gameObject.transform.localScale=='originalScale','original transform restore')
assert(saved[actor]==nil and seated[actor]==nil and passenger==nil,'local state released')
assert(actor.teleports==1,'one dismount position restore')
OnSeatExited(actor);OnDisable();OnDestroy()
assert(actor.teleports==1 and actor.standups==1,'duplicate/asynchronous callback is idempotent')
'''
BOAT_TEST='''
saved=state;driver=actor
OnDisable()
assert(good.enabled and not alreadyOff.enabled and not unrelated.enabled,'collider ownership restore')
assert(actor.gameObject.transform.parent==originalParent and actor.gameObject.transform.localScale=='originalScale','original transform restore')
assert(saved==nil and driver==nil,'local state released')
assert(actor.jumpHeight==2.4 and actor.immobilized==false,'boat-owned movement lock released')
assert(actor.teleports==1,'one dismount position restore')
OnDisable();OnDestroy();assert(actor.teleports==1,'repeat cleanup is idempotent')
'''

horse=(D/'horse_seat_v1.lua').read_text()
carpetSource=(ROOT/'editor_project/project_lapv8fm0/scripts/modules/imported/prefab_14/scene_vehicle_carpet.lua').read_text()
boatSource=(ROOT/'editor_project/project_lapv8fm0/scripts/scene_vehicle_boat.lua').read_text()
carpet=patched(carpetSource,(D/'carpet-lifecycle.patch').read_text())
boat=patched(boatSource,(D/'boat-lifecycle.patch').read_text())
checks=[]
for name,src in [('horse',horse),('carpet',carpet)]:
    for mode in ['sync','delayed','throws']:
        lua=LuaRuntime();lua.execute(PRELUDE+'\n'+src+'\n'+SETUP+'\nstandMode="'+mode+'"\n'+SEAT_TEST)
        checks.append(name+': disable with '+mode+' StandUp')
lua=LuaRuntime();lua.execute(PRELUDE+'\n'+boat+'\n'+SETUP+'\n'+BOAT_TEST)
checks.append('boat: disable returns captured colliders, jump height, immobilize lock, transform')
# Demonstrate these tests fail on currently saved v26 lifecycle implementations.
for name,src,tail in [('horse',(ROOT/'editor_project/project_lapv8fm0/scripts/modules/imported/prefab_14/horse_seat_v1.lua').read_text(),SEAT_TEST),('carpet',carpetSource,SEAT_TEST),('boat',boatSource,BOAT_TEST)]:
    try:LuaRuntime().execute(PRELUDE+'\n'+src+'\n'+SETUP+'\nstandMode="delayed"\n'+tail)
    except Exception as e:assert 'OnDisable' in str(e),(name,str(e))
    else:raise AssertionError(name+' baseline should reproduce missing cleanup')
result={'passed':checks,'regressionReproduced':['v26 horse missing OnDisable','v26 carpet missing OnDisable','v26 boat missing OnDisable'],'scope':'candidate Lua only; no scene opened or modified','notProven':'This does not establish the review-client river swimming failure cause.'}
(D/'vehicle-lifecycle-test-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
