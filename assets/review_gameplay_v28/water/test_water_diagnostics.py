#!/usr/bin/env python3
"""Bounded read-only diagnostics checks; no editor or real runtime connection."""
from pathlib import Path
import json
from lupa import LuaRuntime

HERE=Path(__file__).resolve().parent
SOURCE=(HERE/'water_diagnostics.lua').read_text()
MOCK=r'''
calls={find=0,overlap=0,ray=0,readCollider=0};clock=0;findAvailable=true;failOverlap=false
function array(t)local r={Length=#t};for i,v in ipairs(t)do r[i-1]=v end;return r end
function v3(x,y,z)return{x=x,y=y,z=z}end
local uid=0
function go(name,parent)
 uid=uid+1;local g={name=name,activeInHierarchy=true,layer=0,id=uid,cols={},components={}}
 function g:GetInstanceID()return self.id end
 function g:GetComponents(typ)return array(typ=='Collider'and self.cols or self.components)end
 local tr={gameObject=g,parent=parent and parent.transform or nil,children={}};g.transform=tr
 function tr:IsChildOf(p)local q=self.parent;while q do if q==p then return true end;q=q.parent end;return false end
 function tr:Find(p)return self.children[p]end
 return g
end
function component(name)return{GetType=function()return{Name=name}end}end
function collider(g,trigger)
 uid=uid+1;local c={gameObject=g,transform=g.transform,isTrigger=trigger,enabled=true,id=uid,
 bounds={center=v3(97.7,29.7,136.3),size=v3(2,3,2)}}
 function c:GetInstanceID()calls.readCollider=calls.readCollider+1;return self.id end
 function c:GetType()return{Name='BoxCollider'}end
 g.cols[#g.cols+1]=c;return c
end
function event()
 local e={list={}};function e:AddListener(cb)self.list[cb]=true end
 function e:RemoveListener(cb)self.list[cb]=nil end
 function e:fire()for cb in pairs(self.list)do cb()end end
 function e:count()local n=0;for _ in pairs(self.list)do n=n+1 end;return n end;return e
end
map=go('地图');terrain=go('地形',map);sea=go('海洋',terrain);river=go('PCGRiverEditor',terrain)
map.transform.children['地形']=terrain.transform
terrain.transform.children['海洋']=sea.transform
terrain.transform.children['水体/PCGRiverEditor']=river.transform
sea.components={component('Transform'),component('DouyinWaterArea')}
river.components={component('Transform'),component('DouyinWaterArea2')}
seaCol=collider(sea,true);riverCol=collider(river,false)
actorGo=go('Actor');actor={isLocal=true,gameObject=actorGo,position=v3(97.715,29.744,136.268),onSwimStart=event(),onSwimStop=event(),can=true,swim=false}
function actor:CanSwim()return self.can end;function actor:IsSwimming()return self.swim end
localActor=actor
actorCol=collider(actorGo,false);ground=go('地形块');groundCol=collider(ground,false)
near={actorCol};for i=1,39 do near[#near+1]=collider(go('Trigger_'..i,river),true)end
ray={
 {collider=actorCol,point=v3(97.715,29.7,136.268),normal=v3(0,1,0),distance=.1},
 {collider=groundCol,point=v3(97.715,28.177,136.268),normal=v3(0,1,0),distance=2.317}}
local V=setmetatable({down=v3(0,-1,0)},{__call=function(_,x,y,z)return v3(x,y,z)end})
CS={UnityEngine={Vector3=V,Time=setmetatable({},{__index=function(_,k)return clock end}),Component='Component',Collider='Collider',
 QueryTriggerInteraction={Collide='Collide',Ignore='Ignore'},GameObject={Find=function(name)calls.find=calls.find+1;if findAvailable then return map end end},
 Physics={OverlapSphere=function(p,r,m,q)calls.overlap=calls.overlap+1;assert(r==1.5 and m==-1 and q=='Collide');if failOverlap then error('mock overlap denied')end;return array(near)end,
 RaycastAll=function(p,d,r,m,q)calls.ray=calls.ray+1;assert(r==8 and m==-1 and q=='Ignore');return array(ray)end}},
 DouyinActorService={GetLocalActor=function()return localActor end}}
function typeof(t)return t end
function tick(t)clock=t;Update()end
'''

def env():
    runtime=LuaRuntime(unpack_returned_tuples=True)
    runtime.execute(MOCK)
    runtime.execute(SOURCE)
    return runtime, runtime.globals()

results=[]
def test(name,code):
    r,g=env()
    r.execute(code)
    results.append({'name':name,'passed':True})

LuaRuntime().execute('assert(load(...))',SOURCE)
results.append({'name':'lua-syntax','passed':True})
test('1-hz-getters-and-enable',r'''
 tick(0);assert(calls.overlap==1 and calls.ray==1)
 for i=1,99 do tick(i/100);GetWaterDiagnostics();GetWaterDiagnosticSummary()end
 assert(calls.overlap==1 and calls.ray==1)
 OnDisable();OnEnable();tick(.99);assert(calls.overlap==1)
 tick(1);assert(calls.overlap==2)
''')
test('first-12-only-and-real-support',r'''
 tick(0);local d=GetWaterDiagnostics()
 assert(d.status=='sampled' and d.version=='water-v28')
 assert(d.overlapTotal==40 and #d.nearby==12 and d.overlapTruncated)
 assert(d.observedWaterTriggers==11 and d.nearby[1].isActor)
 assert(d.support.name=='地形块' and math.abs(d.support.actorAboveSupport-1.567)<.001)
 assert(d.roots.river.components[2]=='DouyinWaterArea2')
 assert(string.find(d.summary,'water-v28',1,true) and string.find(d.summary,'脚下:地形块',1,true))
 d.nearby[1].name='changed';assert(GetWaterDiagnostics().nearby[1].name=='Actor')
''')
test('max-three-global-searches-across-lifecycle',r'''
 findAvailable=false
 for i=0,60 do tick(i)end
 assert(calls.find==3)
 OnDisable();OnEnable();for i=61,120 do tick(i)end
 assert(calls.find==3 and GetWaterDiagnostics().findAttempts==3)
 assert(GetWaterDiagnostics().reason=='water-root-not-loaded')
 assert(GetWaterDiagnostics().nearby[2].waterEvidence=='ancestor-name')
''')
test('far-away-no-physics',r'''
 actor.position=v3(132.5,39.05,49)
 for i=0,60 do tick(i)end
 assert(calls.overlap==0 and calls.ray==0)
 assert(GetWaterDiagnostics().status=='away')
''')
test('swim-events-disable-destroy',r'''
 tick(0);assert(actor.onSwimStart:count()==1 and actor.onSwimStop:count()==1)
 actor.onSwimStart:fire();actor.onSwimStop:fire();tick(1)
 local d=GetWaterDiagnostics();assert(d.events.started==1 and d.events.stopped==1)
 OnDisable();assert(actor.onSwimStart:count()==0 and actor.onSwimStop:count()==0)
 local n=calls.overlap;tick(10);assert(calls.overlap==n)
 OnEnable();tick(11);assert(actor.onSwimStart:count()==1)
 OnDestroy();assert(actor.onSwimStart:count()==0 and actor.onSwimStop:count()==0)
 OnEnable();tick(20);assert(calls.overlap==n+1)
''')
test('actor-replacement-unsubscribes-old',r'''
 tick(0);local old=actor
 localActor={isLocal=true,gameObject=go('Actor2'),position=v3(245,26.616,50),onSwimStart=event(),onSwimStop=event(),CanSwim=function()return false end,IsSwimming=function()return false end}
 tick(1);assert(old.onSwimStart:count()==0 and localActor.onSwimStart:count()==1)
 assert(GetWaterDiagnostics().zone=='sea' and GetWaterDiagnostics().canSwim==false)
''')
test('missing-player-and-query-error-visible',r'''
 localActor=nil;tick(0);assert(GetWaterDiagnostics().reason=='actor-missing')
 localActor=actor;failOverlap=true
 for i=1,20 do tick(i)end
 local d=GetWaterDiagnostics();assert(d.reason=='overlap-query')
 assert(#d.errors.recent==6 and d.errors.count==20)
 assert(string.find(d.summary,'overlap-query',1,true))
''')
test('ray-results-unsorted-and-truncation-labelled',r'''
 local far={collider=groundCol,point=v3(97.715,25,136.268),normal=v3(0,1,0),distance=5.494}
 local closer={collider=groundCol,point=v3(97.715,29,136.268),normal=v3(0,1,0),distance=1.494}
 ray={far,closer};for i=1,40 do ray[#ray+1]=far end
 tick(0);local d=GetWaterDiagnostics();assert(d.rayTruncated and d.rayTotal==42)
 assert(d.support.hitPoint.y==29)
''')
test('optional-small-ui-visibility-and-disposal',r'''
 ShowDiagnostics=true;created={};destroyCount=0;addedTypes={}
 setmetatable(CS.UnityEngine.GameObject,{__call=function(_,name)
  local g=go(name);created[name]=g
  function g:SetActive(v)self.activeInHierarchy=v end
  function g.transform:SetParent(p,world)self.parent=p end
  function g:AddComponent(typ)local c={};addedTypes[#addedTypes+1]=typ;return c end
  return g
 end})
 local U=CS.UnityEngine
 U.Canvas='Canvas';U.RectTransform='RectTransform';U.RenderMode={ScreenSpaceOverlay=0}
 U.Vector2=function(x,y)return{x=x,y=y}end;U.Color=function(r,g,b,a)return{r=r,g=g,b=b,a=a}end
 U.TextAnchor={MiddleCenter=1};U.UI={Text='Text',Image='Image',CanvasScaler={ScaleMode={ScaleWithScreenSize=1}}}
 U.Object={Destroy=function(g)destroyCount=destroyCount+1 end}
 CS.UIType={CustomMain=1,Jump=2,HoldHands=3}
 CS.DouyinUIService={GetInteractionButton=function()return{GetComponentInChildren=function()return{font={}}end}end}
 tick(0);assert(GetWaterDiagnostics().ui.created and created.WaterDiagnosticsV28.activeInHierarchy)
 for _,typ in ipairs(addedTypes)do assert(typ~='GraphicRaycaster')end
 actor.position=v3(132.5,39.05,49);tick(1);assert(not created.WaterDiagnosticsV28.activeInHierarchy)
 OnDisable();OnDestroy();assert(destroyCount==1)
''')
test('optional-ui-failure-retries-bounded',r'''
 ShowDiagnostics=true
 for i=0,60 do tick(i)end
 local d=GetWaterDiagnostics()
 assert(d.ui.attempts==3 and not d.ui.created and d.ui.reason=='diagnostic-ui-error')
 assert(d.status=='sampled' and d.support.name=='地形块')
''')
output={'version':'water-v28','passed':len(results),'tests':results,'scope':'mock and Lua syntax only; not device verification'}
(HERE/'test-results.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(output,ensure_ascii=False))
