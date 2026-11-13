from pathlib import Path
from itertools import combinations
from lupa import LuaRuntime
ROOT=Path(__file__).resolve().parent
source=(ROOT/'dragon_rpg.lua').read_text()
start=source.index('local function computeCombatLayout(')
end=source.index('local function placeCombatRect',start)
lua=LuaRuntime(unpack_returned_tuples=True)
compute=lua.execute(source[start:end]+'\nreturn computeCombatLayout')
cases=[
 ('desktop',1920,1080,(0,0,1920,1080)),
 ('iphone16pro_left_notch',2622,1206,(177,63,2622,1206)),
 ('iphone16pro_right_notch',2622,1206,(0,63,2445,1206)),
 ('iphone_safe_both',2622,1206,(177,63,2445,1160)),
 ('16_9',1920,1080,(0,48,1920,1080)),
 ('4_3',1024,768,(40,40,984,748)),
 ('small_landscape',640,360,(30,18,610,360)),
 ('portrait',1206,2622,(0,102,1206,2445)),
 ('narrow_portrait',360,640,(0,34,360,600)),
]
for name,w,h,(x0,y0,x1,y1) in cases:
 result=compute(w,h,lua.table_from(dict(xMin=x0,yMin=y0,xMax=x1,yMax=y1)))
 buttons={k:dict(result['buttons'][k]) for k in ['attack','skill1','skill2','skill3','exit']}
 for key,p in buttons.items():
  r=p['size']/2
  assert p['x']-r>=x0 and p['x']+r<=x1,(name,key,'horizontal safe area')
  assert p['y']-r>=y0 and p['y']+r<=y1,(name,key,'vertical safe area')
  assert p['x']-r>=x0+(x1-x0)*.45,(name,key,'left joystick region')
 for (a,p),(b,q) in combinations(buttons.items(),2):
  gapx=abs(p['x']-q['x'])-(p['size']+q['size'])/2
  gapy=abs(p['y']-q['y'])-(p['size']+q['size'])/2
  assert max(gapx,gapy)>=18*result['scale']-.001,(name,a,b,gapx,gapy)
 assert buttons['exit']['x']>buttons['attack']['x'] and buttons['exit']['y']>buttons['attack']['y'],name
 assert buttons['attack']['size']>buttons['skill1']['size']>buttons['exit']['size'],name

# Exercise the actual transform adapter with native parent/local scaling and off-center pivots.
helper=source[source.index('-- One screen-space layout for all combat controls'):source.index('function SetMode(mode)')]
lua.execute('''
local mt={__sub=function(a,b)return{x=a.x-b.x,y=a.y-b.y,z=a.z-b.z}end}
local function V2(x,y)return{x=x,y=y}end
local function V3(x,y,z)return setmetatable({x=x,y=y,z=z},mt)end
local U={Screen={width=2622,height=1206,safeArea={xMin=177,xMax=2445,yMin=63,yMax=1206}},RectTransform={Axis={Horizontal=0,Vertical=1}}}
local root={transform={lossyScale={x=1.1166667,y=1.1166667}}}
local function rectTransform(sx,sy,pivot,own)
 local t={lossyScale={x=sx,y=sy},pivot=pivot or V2(.5,.5),rect={width=100,height=100},_position=V3(0,0,0),glyph={}}
 local meta={}
 meta.__index=function(self,k)
  if k=='position'then return self._position end
  if k=='sizeDelta'then return self._size end
 end
 meta.__newindex=function(self,k,v)
  if k=='sizeDelta'then self._size=v;self.rect.width=v.x;self.rect.height=v.y
  elseif k=='anchoredPosition'then self._position=V3(U.Screen.width+v.x*root.transform.lossyScale.x,v.y*root.transform.lossyScale.x,0)
  elseif k=='position'then self._position=v
  else rawset(self,k,v)end
 end
 setmetatable(t,meta)
 function t:Find(name)if name=='ActionGlyph'then return self.glyph end end
 function t:SetSizeWithCurrentAnchors(axis,n)if axis==0 then self.rect.width=n else self.rect.height=n end end
 function t:TransformVector(v)return V3(v.x*self.lossyScale.x,v.y*self.lossyScale.y,0)end
 return t
end
local toggle={transform=rectTransform(1.1166667,1.1166667)}
local skillButtons={[2]={button={transform=rectTransform(1.1166667,1.1166667)}},[3]={button={transform=rectTransform(1.1166667,1.1166667)}}}
local native={{button={transform=rectTransform(.63*.77,1.2*.75,V2(.2,.7))}},{button={transform=rectTransform(1.3*.83,.8*1.1,V2(.8,.1))}}}
local combatAnchors={}
local C15={}
local function rect()return{},rectTransform(root.transform.lossyScale.x,root.transform.lossyScale.x)end
''' +helper+'''
layoutCombatControls()
for i=1,2 do
 local p=C15.combatLayout.buttons[i==1 and 'attack'or'skill1']
 local rt=native[i].button.transform
 assert(math.abs(rt.rect.width*rt.lossyScale.x-p.size)<.0001)
 assert(math.abs(rt.rect.height*rt.lossyScale.y-p.size)<.0001)
 local shift=rt:TransformVector(V3((.5-rt.pivot.x)*rt.rect.width,(.5-rt.pivot.y)*rt.rect.height,0))
 assert(math.abs(rt.position.x+shift.x-p.x)<.0001)
 assert(math.abs(rt.position.y+shift.y-p.y)<.0001)
 assert(rt.pivot.x==(i==1 and .2 or .8)) -- do not break native restore lifecycle
end
-- Safe-area rotation is picked up without rebuilding buttons or changing style.
U.Screen.safeArea={xMin=0,xMax=2445,yMin=63,yMax=1206}
layoutCombatControls()
assert(C15.combatLayout.safe.xMin==0)
''')
print('PASS: 9 screen/safe-area profiles; all 5 hit rectangles separated and inside right safe area; exit stays upper-right; native local/parent scale and noncenter pivots match physical pixels')
