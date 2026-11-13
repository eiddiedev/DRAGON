from pathlib import Path
from lupa import LuaRuntime
source=(Path(__file__).resolve().parent/'dragon_exploration.lua').read_text()
def part(start,end):return source[source.index(start):source.index(end,source.index(start))]
math_helpers=part('local function targetPosition(t)','---------------------------------------------------------------- 药水与蘑菇')
discovery=part('local function objectAlive(go)','local function handleNativeClick(index)')
read=part('local function readLore(id)','\nlocal function witch()')
interact=part('local function interact()','local function buildUIInner()')
clicks=part('local function handleNativeClick(index)','\nfunction GetStatus()')
lua=LuaRuntime(unpack_returned_tuples=True)
lua.execute('''
local vmt={}
local function vector(x,y,z)return setmetatable({x=x,y=y,z=z},vmt)end
vmt.__add=function(a,b)return vector(a.x+b.x,a.y+b.y,a.z+b.z)end
vmt.__sub=function(a,b)return vector(a.x-b.x,a.y-b.y,a.z-b.z)end
vmt.__mul=function(a,b)return vector(a.x*b,a.y*b,a.z*b)end
local V=setmetatable({down=vector(0,-1,0)},{__call=function(_,x,y,z)return vector(x,y,z)end})
V.Distance=function(a,b)return math.sqrt((a.x-b.x)^2+(a.y-b.y)^2+(a.z-b.z)^2)end
local U={Time={realtimeSinceStartup=0,unscaledTime=10,frameCount=1},GameObject={},Object={},Transform={},Physics={},QueryTriggerInteraction={Ignore=1}}
U.Physics.RaycastAll=function()return{Length=0}end
U.Rect=function(x,y,w,h)return{x=x,y=y,w=w,h=h}end
function typeof(x)return x end
local actor={position=V(0,0,0)}
local objects={}
local function makeObject(name,p,scale,rot180)
 local go={name=name,scene={IsValid=function()return true end}}
 go.transform={position=p,localScale=V(scale or 1,scale or 1,scale or 1),lossyScale=V(scale or 1,scale or 1,scale or 1)}
 function go.transform:TransformPoint(q)
  local s=self.localScale;local sign=rot180 and -1 or 1
  return self.position+V(q.x*s.x*sign,q.y*s.y,q.z*s.z*sign)
 end
 function go:SetActive(v)self.active=v end
 return go
end
U.GameObject.Find=function(name)return objects[name]end
U.Object.Instantiate=function(go)return makeObject('copy',go.transform.position,go.transform.lossyScale.x)end
local discovery=nil
local targets,eggs={},{}
local eggStage=-1
local witchPlaced=false
local lore={got={},n=0}
local LORE_TOTAL=8
local current,nativeTarget,nativeExplore,nativePotion,queuedNative
local lastNativeClick=-10
local mode=nil
local K={L={lore={cols=4,w=640,h=720}},tex={lore={width=2560,height=1440}},play=function()end}
local reader={text={ri={}}}
local main={ShowNote=function(_,a,n,total)assert(total==8)end}
local function unavailable()return false end
local function open(kind)mode=kind;return true end
''' +math_helpers+discovery+read+interact+clicks+'''
-- Fixed lore fallbacks exist before models, but do not suppress late object registration.
for n=0,300 do U.Time.realtimeSinceStartup=n*.25;refreshDiscovery()end
objects.tripo_castle_bookshelf_0=makeObject('tripo_castle_bookshelf_0',V(114.7,72.3,177),3.57483959,true)
objects.tripo_castle_bookshelf_1=makeObject('tripo_castle_bookshelf_1',V(114.7,72.3,181),3.57483959,true)
objects['书库桌上烛光']=makeObject('书库桌上烛光',V(117,73.5,179))
objects.castle_gi_library=makeObject('castle_gi_library',V(127,0,176),1,true)
objects.tripo_camp_stele=makeObject('tripo_camp_stele',V(64.7,43.4681854,65))
objects.rune_0=makeObject('rune_0',V(48,51.4662,138),3.271)
objects.rune_1=makeObject('rune_1',V(58.3923,51.6759,156),3.271)
objects.rune_2=makeObject('rune_2',V(37.6077,50.7098,156),3.271)
for n=301,360 do U.Time.realtimeSinceStartup=n*.25;refreshDiscovery()end
local byId={}
for _,t in ipairs(targets)do if t.kind=='lore'then assert(not byId[t.id]);byId[t.id]=t end end
local names={'tripo_castle_bookshelf_0','tripo_castle_bookshelf_1','书库桌上烛光','tripo_camp_stele','rune_0','rune_1','rune_2','DragonPactMemorial'}
for id=1,8 do assert(byId[id]and byId[id].ref.name==names[id]and byId[id].go,id)end
-- Each of the eight actual target entries reaches readLore via deferred native dispatch.
for id=1,8 do
 local target=byId[id];local p=targetPosition(target);actor.position=p+V(1.2,-1,0)
 local best=1e9;current=nil
 for _,t in ipairs(targets)do if nearby(t)then local d=targetDistance(t,targetPosition(t));if d<best then current=t;best=d end end end
 assert(current==target,'wrong nearest lore target '..id)
 nativeTarget=current;nativeExplore={};mode=nil
 U.Time.unscaledTime=20+id
 queueNativeClick(1);assert(queuedNative and queuedNative.target==target)
 U.Time.frameCount=U.Time.frameCount+1
 local click=queuedNative;queuedNative=nil
 handleNativeClick(click.index)
 assert(mode=='lore'and lore.got[id]and lore.n==id,'entry failed '..id)
 local cell=reader.text.ri.uvRect
 assert(math.abs(cell.x-((id-1)%4)*.25)<.00001,'wrong page cell '..id)
 mode=nil
end
-- Independent horizontal and height gates: a readable shelf above a standing actor.
local p=targetPosition(byId[1]);actor.position=p+V(2.9,-2,0)
assert(nearby(byId[1]))
actor.position=p+V(0,6,0);assert(not nearby(byId[1])) -- adjacent floor cannot trigger it
-- Moving a bookshelf moves its entry, while preserving callback target identity.
local stable=byId[1];objects.tripo_castle_bookshelf_0.transform.position=objects.tripo_castle_bookshelf_0.transform.position+V(20,0,0)
assert(targetPosition(stable).x>135)
-- A disabled/missing candle falls back to the actual transformed library piece, not old world coordinates.
byId[3].go=nil
objects.castle_gi_library.transform.position=objects.castle_gi_library.transform.position+V(10,0,0)
assert(math.abs(targetPosition(byId[3]).x-127.6)<.001)
-- Re-reading a page is allowed without double-counting its completion.
current=byId[8];nativeTarget=current;actor.position=targetPosition(current)+V(1,-1,0);U.Time.unscaledTime=40
handleNativeClick(1);assert(lore.n==8)
assert(#GetLoreTargets()==8)
''')
print('PASS: all 8 exact lore references; delayed registration; native queue→interact→correct atlas page; one-time completion; moved bookshelf/library fallback; floor separation and reachable horizontal range')
