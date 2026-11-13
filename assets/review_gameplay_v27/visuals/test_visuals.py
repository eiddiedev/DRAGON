"""Run the actual replacement Lua against a deterministic Unity API test double.

Checks asynchronous material replacement and teardown, not phone-render quality.
"""
import json
from pathlib import Path
from lupa import LuaRuntime
from patch_visuals import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BRIDGE = ROOT / "editor_project/project_lapv8fm0/scripts/modules/imported/prefab_20/dragon_world_bridge.lua"

MOCK = r'''
Time={realtimeSinceStartup=0,time=0}
local blend=0
Color=setmetatable({}, {__call=function(_,r,g,b,a)return {r=r,g=g,b=b,a=a}end})
function Color.Lerp(a,b,t)return Color(a.r+(b.r-a.r)*t,a.g+(b.g-a.g)*t,a.b+(b.b-a.b)*t,a.a+(b.a-a.a)*t)end
Vector3=setmetatable({}, {__call=function(_,x,y,z)return {x=x,y=y,z=z}end})
function typeof(x)return x end
local objects={}; local destroyed={}; local clones=0
local api={}
local function arr(...)
 local x={...};local a={Length=#x};for i,v in ipairs(x)do a[i-1]=v end;return a
end
local function material(name,power)
 local m={name=name,shader={name=power and 'Douyin/AI/PBR/EnvLit_AI' or 'Universal Render Pipeline/Lit'},props={_BaseColor=Color(.6,.8,.5,1),_EmissionColor=Color(0,0,0,1)},textures={},keywords={}}
 if power then m.props._EmissionPower=0;m.props._EmissionTex=true else m.props._EmissionMap=true end
 function m:HasProperty(k)return self.props[k]~=nil end
 function m:GetColor(k)return self.props[k] end
 function m:SetColor(k,v)self.props[k]=v end
 function m:SetFloat(k,v)self.props[k]=v end
 function m:GetFloat(k)return self.props[k]end
 function m:SetTexture(k,v)self.textures[k]=v end
 function m:EnableKeyword(k)self.keywords[k]=true end
 return m
end
GameObject={Find=function(name)local go=objects[name];return go and go.active~=false and go or nil end}
UnityEngine={Renderer='Renderer',Texture2D={whiteTexture={name='white'}},Object={Destroy=function(x)destroyed[x]=true end},
 Application={targetFrameRate=60}, QualitySettings={antiAliasing=4,shadows='All',shadowDistance=60,pixelLightCount=4,renderPipeline={renderScale=1.25}},
 Rendering={GraphicsSettings={}},Camera={allCameras=arr()}}
function UnityEngine.Material(src)
 clones=clones+1;local m=material(src.name,src:HasProperty('_EmissionPower'))
 for k,v in pairs(src.props)do m.props[k]=v end
 return m
end
CS={UnityEngine=UnityEngine};UnityEngine.Rendering.Universal={UniversalAdditionalCameraData='additional'}
function addLight(position,color,range,power)
 local go={};return {gameObject=go,transform={position=position},color=color,range=range,intensity=power,enabled=false}
end
UI={};local prior={update=0,disable=0,destroy=0}
function Update()prior.update=prior.update+1 end
function OnDisable()prior.disable=prior.disable+1 end
function OnDestroy()prior.destroy=prior.destroy+1 end
function api.spawn(name, ...)
 local renderers={};for _,m in ipairs({...})do renderers[#renderers+1]={sharedMaterials=arr(m),bounds={center={x=0,y=50,z=0}}}end
 objects[name]={GetComponentsInChildren=function()return arr(table.unpack(renderers))end}
 return renderers
end
api.material=material;api.arr=arr;api.objects=objects;api.destroyed=destroyed;api.prior=prior
function api.clones()return clones end
function api.at(t,b)Time.realtimeSinceStartup=t;Time.time=t;blend=b end
function api.camera(hdr,msaa,post,shadow)
 local data={renderPostProcessing=post,renderShadows=shadow}
 return {name='Player',allowHDR=hdr,allowMSAA=msaa,GetComponent=function()return data end,data=data}
end
'''

TESTS = r'''
local passes={}
local function check(ok,name)assert(ok,name);passes[#passes+1]=name end
api.at(0,0);updateHolyLight()
check(#holyTried.materials==0,'empty startup does not mark crowns permanently ready')
local custom=api.material('custom',true);local urp=api.material('urp',false)
local rs=api.spawn('holy_canopy3',custom,urp)
rs[2].sharedMaterials=api.arr(urp,custom)
api.spawn('holy_canopy4',custom)
api.at(1.1,0);updateHolyLight()
check(api.clones()==2 and #holyTried.materials==2,'shared source clones once across crowns and all slots are bound')
local cm=rs[1].sharedMaterials[0];local um=rs[2].sharedMaterials[0]
check(rs[2].sharedMaterials[1]==cm,'secondary material slot shares the existing holy clone')
check(cm.props._EmissionPower>2.5 and um.props._EmissionColor.r>2.5,'custom power and URP HDR paths both emit at night')
check(cm.keywords._EMISSION and um.keywords._EMISSION,'emission keyword enabled')
check(GetHolyGlowDiagnostics().details[1].emissionPower>2.5,'diagnostics expose actual live emission power')
check(custom.props._EmissionPower==0 and custom.props._BaseColor.g==.8,'original source material unchanged')
local replacement=api.material('streamed',false)
rs[2].sharedMaterials=api.arr(replacement)
api.at(2.2,0);updateHolyLight()
check(rs[2].sharedMaterials[0]~=replacement and rs[2].sharedMaterials[0].props._EmissionColor.r>2.5,'late asset material replacement gets night state')
check(api.destroyed[um] and #holyTried.materials==2,'abandoned owned clone retired after replacement')
cm.props._BaseColor=Color(.5,.8,.5,1)
api.at(2.4,0);updateHolyLight()
check(cm.props._BaseColor.r==1 and cm.props._BaseColor.g==.12,'night tint recovers when another material writer resets colour')
api.at(3.3,1);updateHolyLight()
check(cm.props._EmissionPower==0 and rs[2].sharedMaterials[0].props._EmissionColor.r==0,'daytime has zero self emission on both shaders')
check(cm.props._BaseColor.g==.8,'daytime restores original leaf tint')
for _,group in pairs(holyTried.groups)do check(not group.light.enabled,'daytime crown light disabled')end
holyTried.dispose()
check(rs[1].sharedMaterials[0]==custom and rs[2].sharedMaterials[0]==replacement,'teardown restores currently valid source materials')
check(api.destroyed[cm] and #holyTried.materials==0,'teardown releases all owned clones')
holyTried.dispose()
api.at(4.5,0);updateHolyLight()
check(#holyTried.materials==2,'re-enable rebinds after cleanup')
local beforeInactive=rs[1].sharedMaterials[0]
api.objects.holy_canopy3.active=false;api.objects.holy_canopy4.active=false
api.at(5.6,0);updateHolyLight()
check(rs[1].sharedMaterials[0]==custom and rs[2].sharedMaterials[0]==replacement,'inactive renderers restore source before clone retirement')
check(api.destroyed[beforeInactive] and #holyTried.materials==0,'inactive crown clones release without dangling material references')
api.objects.holy_canopy3.active=true;api.objects.holy_canopy4.active=true
api.at(6.7,0);updateHolyLight()
check(#holyTried.materials==2 and not api.destroyed[rs[1].sharedMaterials[0]],'reactivated crowns bind live clones')
check(rs[1].sharedMaterials[0].props._EmissionPower>2.4,'reactivated crown resumes current night glow')
local camera=api.camera(true,true,true,true)
UnityEngine.Camera.allCameras=api.arr(camera)
api.at(7.8,0);Update()
local q=UnityEngine.QualitySettings
check(q.renderPipeline.renderScale==1.25 and q.antiAliasing==4 and q.shadows=='All' and q.shadowDistance==60 and q.pixelLightCount==4,'authored pipeline and quality settings untouched')
check(camera.allowHDR and camera.allowMSAA and camera.data.renderPostProcessing and camera.data.renderShadows,'authored camera HDR MSAA post and shadows untouched')
check(UnityEngine.Application.targetFrameRate==30 and api.prior.update==1,'30 FPS pacing retained and prior Update called')
OnDisable()
check(UnityEngine.Application.targetFrameRate==60 and api.prior.disable==1,'disable restores original frame cap and lifecycle chain')
OnDestroy()
check(api.prior.destroy==1,'destroy chain remains callable after disable')
return passes
'''

lua = LuaRuntime(unpack_returned_tuples=True)
candidate = patch(BRIDGE.read_text())
compiled = lua.eval("function(s) local f,e=load(s); return f~=nil,e end")(candidate)
assert compiled[0], compiled[1]
result = lua.execute(MOCK + (HERE / "holy-after.lua").read_text() + (HERE / "quality-after.lua").read_text() + TESTS)
report = {
    "test": "v27 isolated visual Lua regression",
    "whole_bridge_syntax": "pass",
    "checks": list(result.values()),
    "limitations": ["Mocks validate Lua state/lifecycle only; actual mobile bloom, shader rendering and performance require review package validation.",
                    "No editor instance or live project was modified by this test."],
}
(HERE / "test-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(report, ensure_ascii=False, indent=2))
