from pathlib import Path
from lupa import LuaRuntime
import json
A=Path(json.loads(Path('assets/mobile_failure_v22/no-quality-manifest.json').read_text())['source']);s=(A/'scripts/dragon_world_bridge.lua').read_text();L=LuaRuntime(unpack_returned_tuples=True)
L.execute('''
UI={dizzy={}};Time={time=0}
local mt={};mt.__add=function(a,b)return setmetatable({x=a.x+b.x,y=a.y+b.y,z=a.z+b.z},mt)end;mt.__mul=function(a,b)if type(a)=='number'then a,b=b,a end;return setmetatable({x=a.x*b,y=a.y*b,z=a.z*b},mt)end
Vector3=setmetatable({one=setmetatable({x=1,y=1,z=1},mt)},{__call=function(_,x,y,z)return setmetatable({x=x,y=y,z=z},mt)end})
local qmt={__mul=function(a,b)return {modified=true}end};Quaternion={Euler=function(...)return {}end}
main={fieldOfView=60,transform={position=Vector3(1,2,3),rotation=setmetatable({},qmt),right=Vector3(1,0,0),up=Vector3(0,1,0)},reset=0}
function main:ResetWorldToCameraMatrix()self.worldToCameraMatrix=nil;self.reset=self.reset+1 end
UnityEngine={Camera={main=main},Matrix4x4={Scale=function()return setmetatable({},{__mul=function(a,b)return {view=true}end})end,TRS=function(...)return {inverse={}}end}}
''')
a=s.index('function UI.restoreFxCamera()');b=s.index('function UI.fxOverlay()',a);L.execute(s[a:b])
a=s.index('function UI.dizzyLate()');b=s.index('\n----------------------------------------------------------------',a);L.execute(s[a:b])
L.execute('''
local pos,rot=main.transform.position,main.transform.rotation
for i=1,50 do
 UI.restoreFxCamera();assert(main.fieldOfView==60);assert(main.worldToCameraMatrix==nil)
 Time.time=i*.1;UI.dizzy.shakeT=Time.time;UI.dizzy.shakeA=1;UI.dizzy.shakeD=.3
 UI.dizzyLate();assert(UI.dizzy.cameraApplied);assert(main.worldToCameraMatrix.view)
 assert(main.transform.position==pos and main.transform.rotation==rot)
end
UI.restoreFxCamera();assert(main.fieldOfView==60 and main.worldToCameraMatrix==nil)
-- Effects expire without leaving the projection altered.
UI.dizzy.shakeT=0;Time.time=100;UI.dizzyLate();assert(not UI.dizzy.cameraApplied)
-- Another system's FOV change must not be overwritten during cleanup.
Time.time=101;UI.dizzy.shakeT=101;UI.dizzyLate();main.fieldOfView=75;UI.restoreFxCamera();assert(main.fieldOfView==75)
''')
base=Path('assets/mobile_perf_v21/baseline-scripts/dragon_fx.lua').read_text();fx=(A/'scripts/dragon_fx.lua').read_text()
a=base[base.index('local hurtFeel=nil'):base.index('function Update()')];b=fx[fx.index('local hurtFeel=nil'):fx.index('function Update()')];assert a==b
out={'cameraTests':'50 consecutive shakes; expiry; cleanup; external FOV preserved; transform unchanged','originalEffectDispatch':'byte-identical','nativeRuntimeVerified':False,'phoneVerified':False}
Path('assets/mobile_failure_v22/no-quality-tests.json').write_text(json.dumps(out,indent=2));print(out)
