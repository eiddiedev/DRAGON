import json
from pathlib import Path
from lupa import LuaRuntime
from patch_enemy import patch

ROOT=Path(__file__).resolve().parent
BASELINE=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-55a43370-8734-4825-92a8-b0de824a45e2/scripts/modules/imported/prefab_20/dragon_combat.lua')
SOURCE=BASELINE.read_text()
assert 'review-v27: each successfully spawned model' not in SOURCE, 'old baseline was replaced; choose an unchanged v26 backup'
CHECKS=[]
MOCK=r'''
objects={};spawned={};destroyed={};primitiveCount=0
local vecmeta={}
function vec(x,y,z)return setmetatable({x=x,y=y,z=z,sqrMagnitude=x*x+y*y+z*z},vecmeta)end
vecmeta.__add=function(a,b)return vec(a.x+b.x,a.y+b.y,a.z+b.z)end
vecmeta.__mul=function(a,b)return vec(a.x*b,a.y*b,a.z*b)end
V=setmetatable({one=vec(1,1,1),up=vec(0,1,0),Lerp=function(a,b,t)return b end},{__call=function(_,x,y,z)return vec(x,y,z)end})
local quat=setmetatable({},{__mul=function(a,b)return a end})
Q={LookRotation=function()return quat end,Euler=function()return quat end}
function arr(values)local a={Length=#values};for i,v in ipairs(values)do a[i-1]=v end;return a end
function material()
 return {HasProperty=function()return true end,SetTexture=function()end,SetColor=function()end,SetFloat=function()end}
end
function makeGO(name)
 local g={name=name,activeInHierarchy=true,components={},children={}}
 local t={name=name,gameObject=g,position=vec(0,0,0),localPosition=vec(0,0,0),localScale=V.one,rotation=quat}
 function t:SetParent(parent)local old=self.parent;self.parent=parent;if parent then table.insert(parent.gameObject.children,g)end end
 g.transform=t
 function g:SetActive(on)self.activeInHierarchy=on end
 function g:AddComponent(kind)
  if failHealth and kind=='Canvas'then error('canvas unavailable')end
  local c=kind=='RectTransform'and t or {gameObject=g}
  self.components[kind]=c;return c
 end
 function g:GetComponent(kind)
  if kind=='Collider'then return self.collider end
  if kind=='Renderer'then return self.renderer end
  return self.components[kind]
 end
 function g:GetComponentInChildren(kind)
  if failAnimation and kind=='UGCAnimator'then error('animation type unavailable')end
  return {Controller=true,Play=function()if failPlay then error('animation playback unavailable')end;return true end}
 end
 function g:GetComponentsInChildren(kind)
  if failCore and kind=='Renderer'then error('renderer unreadable')end
  if kind=='Collider'then return arr({self.collider})end
  if kind=='Renderer'then return arr({self.renderer})end
  if kind=='Transform'then return arr({self.transform})end
  return arr({})
 end
 g.collider={enabled=true};g.renderer={materials=arr({material()})}
 table.insert(objects,g);return g
end
local gofactory=setmetatable({},{__call=function(_,name)return makeGO(name)end})
gofactory.CreatePrimitive=function()primitiveCount=primitiveCount+1;return makeGO('Cube')end
U={GameObject=gofactory,PrimitiveType={Cube='Cube'},Collider='Collider',Renderer='Renderer',Transform='Transform',RectTransform='RectTransform',Canvas='Canvas',RenderMode={WorldSpace='WorldSpace'},UI={Image='Image'},Rendering={ShadowCastingMode={Off='Off'}},Camera={main={transform={rotation=quat}}},Time={time=10,deltaTime=.03}}
U.Vector2=function(x,y)return{x=x,y=y}end
U.Color=function(r,g,b,a)return{r=r,g=g,b=b,a=a}end
U.Material=function()return material()end
U.Object={Destroy=function(go)go.destroyed=true;go.activeInHierarchy=false;table.insert(destroyed,go)end}
CS={ModularAnim={Runtime={UGCAnimator='UGCAnimator'}},DouyinCameraService={GetCamera=function()return{transform={rotation=quat}}end}}
function typeof(x)return x end
Spawn={spawn=function(...)local go=makeGO('Shadow');table.insert(spawned,go);return go end,destroy=function(go)U.Object.Destroy(go)end}
self={};visuals={};shadowReady={spawnAttempts={}};state={y=0,t=1,phase='active',enemies={{id=1,x=2,z=3,hp=100,maxHP=100,state='chase',hit=0}}}
source=makeGO('Source')
function shadowSource()return source end
function active()return state.phase=='active'end
'''


def fixture(candidate=True, flags=''):
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute(MOCK)
    lua.execute(flags)
    if candidate:
        body=(ROOT/'enemy-visuals.lua').read_text()
    else:
        begin=SOURCE.index('local function clearVisuals()')
        end=SOURCE.index(' fx.SetArena(V(state.x,state.y+.08,state.z),state.radius,false)',begin)
        body=SOURCE[begin:end]
    lua.execute(body+'\nend\nrunVisuals=syncVisuals;resetVisuals=clearVisuals')
    return lua


old=fixture(False,'failAnimation=true')
old.execute('for i=1,12 do U.Time.time=10+i;state.enemies[1].x=i;pcall(runVisuals)end')
assert old.eval('#spawned==10 and primitiveCount==20 and next(visuals)==nil and not spawned[1].destroyed')
CHECKS.append('original reproduces 10 orphan models and 20 full-size cubes after animation lookup exception')

new=fixture(True,'failAnimation=true')
new.execute('for i=1,12 do U.Time.time=10+i;state.enemies[1].x=i;runVisuals()end')
assert new.eval('#spawned==1 and primitiveCount==0 and visuals[1].go~=nil and GetShadowVisualDiagnostics().animationFailures==1')
CHECKS.append('same animation exception keeps one visible owned model and no cubes')
assert new.eval('visuals[1].go.collider.enabled==false and visuals[1].enemy==state.enemies[1]')
CHECKS.append('existing analytical collision and hit state preserved')
assert new.eval('visuals[1].healthFill.sizeDelta.x==76')
new.execute('state.enemies[1].hp=50;runVisuals()')
assert new.eval('visuals[1].healthFill.sizeDelta.x==38')
CHECKS.append('health canvas fill tracks actual HP')
new.execute('state.enemies[1].hp=0;runVisuals()')
assert new.eval('not visuals[1].go.activeInHierarchy and #spawned==1')
CHECKS.append('dead visual hidden without respawning')
new.execute('resetVisuals()')
assert new.eval('next(visuals)==nil and spawned[1].destroyed and GetShadowVisualDiagnostics().destroyed==1')
CHECKS.append('encounter clear destroys registered model and materials')

new=fixture(True,'failHealth=true')
new.execute('for i=1,12 do U.Time.time=10+i;runVisuals()end')
assert new.eval('#spawned==1 and primitiveCount==0 and visuals[1].bar==nil and GetShadowVisualDiagnostics().healthFailures==1')
CHECKS.append('health canvas failure never aborts or duplicates enemy')

new=fixture(True,'failCore=true')
new.execute('for i=1,12 do U.Time.time=10+i;runVisuals()end')
assert new.eval('#spawned==10 and GetShadowVisualDiagnostics().destroyed==10 and next(visuals)==nil')
assert new.eval('(function()for _,g in ipairs(spawned)do if not g.destroyed then return false end end;return true end)()')
CHECKS.append('core setup failure destroys every attempted model, zero orphan survivors, retry remains bounded')

new=fixture(True,'failPlay=true')
new.execute('for i=1,12 do U.Time.time=10+i;runVisuals()end')
assert new.eval('#spawned==1 and visuals[1].animator==nil and GetShadowVisualDiagnostics().animationFailures==1')
CHECKS.append('native animation playback failure does not stop visual update or repeat spawn')

new=fixture(True)
new.execute('for id=2,4 do table.insert(state.enemies,{id=id,x=id,z=id,hp=100,maxHP=100,state="chase",hit=0})end;for i=1,12 do U.Time.time=10+i;runVisuals()end')
assert new.eval('#spawned==4 and GetShadowVisualDiagnostics().expected==4 and GetShadowVisualDiagnostics().visible==4')
CHECKS.append('first wave remains exactly four enemy models after repeated sync')

candidate=patch(SOURCE)
lua=LuaRuntime(unpack_returned_tuples=True)
compiled=lua.eval('load')(candidate,'enemy-visual-candidate')
assert not isinstance(compiled,tuple),str(compiled)
CHECKS.append('full combat script compiles')
begin=SOURCE.index('local function clearVisuals()');end=SOURCE.index(' fx.SetArena(V(state.x,state.y+.08,state.z),state.radius,false)',begin)
assert candidate.startswith(SOURCE[:begin]) and candidate.endswith(SOURCE[end:])
CHECKS.append('combat network, engine updates, attack events, bone attacks and reward code byte-preserved')

result={'passed':len(CHECKS),'checks':CHECKS,'baseline':str(BASELINE),'phoneExceptionStackAvailable':False,'actualCulprit':'original post-spawn setup is not transactional; exact failing phone API unconfirmed','runtimeVerified':False}
(ROOT/'test-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
