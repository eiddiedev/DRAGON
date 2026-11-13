import json
from pathlib import Path
from lupa import LuaRuntime
from patch_camera import patch, remove_cloud_controller

ROOT = Path(__file__).resolve().parent
BRIDGE = Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-55a43370-8734-4825-92a8-b0de824a45e2/scripts/modules/imported/prefab_20/dragon_world_bridge.lua')
CHECKS = []


def fixture(extra=''):
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''
UI={state='play',dizzy={}}
Time={time=100,realtimeSinceStartup=100}
camState='done'
calls={pitch={},late=0,disable=0,resolve=0,errors={}}
actor={sitting=false,flying=false,swimming=false}
function actor:IsSitting()return self.sitting end
function actor:IsFlying()return self.flying end
function actor:IsSwimming()return self.swimming end
state={loaded=true}
exploration={GetStatus=function()return state end}
battle={IsParticipating=function()return battleActive==true end}
scope={GetScript=function(self,name) calls.resolve=calls.resolve+1;if dependenciesMissing then return nil end;return name=='dragon_exploration.lua'and exploration or battle end}
DR={phase1={scope=scope}}
camera={enabled=true}
pitch=-40
DouyinActorService={GetLocalActor=function()return actor end}
DouyinCameraService={
 IsPhotographMode=function()return photograph==true end,
 GetCamera=function()return camera end,
 GetPitch=function()return pitch end,
 SetPitch=function(p)if setterError then error('camera rejected') end;pitch=p;table.insert(calls.pitch,p)end}
function report(err)table.insert(calls.errors,err)end
function LateUpdate()calls.late=calls.late+1 end
function OnDisable()calls.disable=calls.disable+1 end
''')
    lua.execute((ROOT / 'camera-guard.lua').read_text())
    if extra:
        lua.execute(extra)
    return lua


def check(name, extra, expression):
    lua=fixture(extra)
    lua.execute('LateUpdate()')
    assert lua.eval(expression), name
    CHECKS.append(name)


check('negative orbit corrected through SDK', '', '#calls.pitch==1 and pitch==0 and calls.late==1')
check('valid pitch remains user-owned', 'pitch=12', '#calls.pitch==0 and pitch==12')
check('boundary avoids repeated SetPitch', 'pitch=0', '#calls.pitch==0')
check('title cinematic untouched', "UI.state='title';UI.cam={}", '#calls.pitch==0')
check('book untouched', "UI.state='book'", '#calls.pitch==0')
check('map untouched', "UI.state='map'", '#calls.pitch==0')
check('exploration menu untouched', 'DR.phase1.menu=true', '#calls.pitch==0')
check('spawn holding untouched', "camState='holding'", '#calls.pitch==0')
check('spawn release untouched', "camState='releasing'", '#calls.pitch==0')
check('dragon ride untouched', 'DR.rider={}', '#calls.pitch==0')
check('summon cinematic untouched', 'DR.soul={}', '#calls.pitch==0')
check('horse seat untouched', 'actor.sitting=true', '#calls.pitch==0')
check('carpet flight untouched', 'actor.flying=true', '#calls.pitch==0')
check('swimming underwater camera untouched', 'actor.swimming=true', '#calls.pitch==0')
check('photo untouched', 'photograph=true', '#calls.pitch==0')
check('potion untouched', "state.potion='grow'", '#calls.pitch==0')
check('food buff untouched', "state.buff='speed'", '#calls.pitch==0')
check('dizzy matrix untouched', 'UI.dizzy.untilT=110', '#calls.pitch==0')
check('skill shake untouched', 'UI.dizzy.shakeT=99', '#calls.pitch==0')
check('battle untouched', 'battleActive=true', '#calls.pitch==0')
check('loading untouched', 'state.loaded=false', '#calls.pitch==0')
check('nil actor guarded', 'actor=nil', '#calls.pitch==0')
check('nil camera guarded', 'camera=nil', '#calls.pitch==0')
check('disabled camera guarded', 'camera.enabled=false', '#calls.pitch==0')
check('nil pitch guarded', 'pitch=nil', '#calls.pitch==0')
check('nonfinite pitch guarded', 'pitch=0/0', '#calls.pitch==0')
check('dependencies fail closed', 'dependenciesMissing=true', '#calls.pitch==0')

lua=fixture()
lua.execute('LateUpdate();LateUpdate();LateUpdate()')
assert lua.eval('#calls.pitch==1 and calls.resolve==2 and calls.late==3')
CHECKS.append('cached dependencies and correction only once')
lua.execute("state.potion='grow';pitch=-20;LateUpdate();state.potion=nil;LateUpdate()")
assert lua.eval('#calls.pitch==2 and pitch==0')
CHECKS.append('potion exit safely re-enables guard')
lua.execute('OnDisable()')
assert lua.eval('calls.disable==1 and UI.roamCameraGuard.exploration==nil and UI.roamCameraGuard.battle==nil')
CHECKS.append('lifecycle release preserves existing callback')
lua=fixture('dependenciesMissing=true')
lua.execute('for i=1,500 do Time.realtimeSinceStartup=i*2;LateUpdate()end')
assert lua.eval('calls.resolve==60 and UI.roamCameraGuard.resolveAttempts==30')
CHECKS.append('dependency retry bounded at 30 each')
lua=fixture('setterError=true')
lua.execute('LateUpdate();LateUpdate();LateUpdate()')
assert lua.eval('#calls.errors==1 and UI.roamCameraGuard.failed and calls.late==3')
CHECKS.append('failure is visible once, existing camera loop continues')

source=BRIDGE.read_text()
candidate=patch(remove_cloud_controller(source))
lua=LuaRuntime(unpack_returned_tuples=True)
fn=lua.eval('load')(candidate,'v27-camera-cloud-candidate')
assert not isinstance(fn,tuple),str(fn)
CHECKS.append('complete bridge candidate compiles')
assert 'GameObject("cloud_pivot")' not in candidate
assert 'GameObject.Find("cl_" .. i)' not in candidate
assert candidate.count('local function updateClouds()end')==1
CHECKS.append('cloud controller cannot recreate or enable cards')
for symbol in ['updateSky','UI.updateVortex','updateHolyLight']:
    assert candidate.count(symbol)==source.count(symbol)
CHECKS.append('sky vortex and holy tree code retained')

result={'passed':len(CHECKS),'checks':CHECKS,'runtimeVerified':False,'mobileVerified':False,'limitation':'0-degree roaming pitch floor; not a full terrain/architecture collision solver'}
(ROOT/'test-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
