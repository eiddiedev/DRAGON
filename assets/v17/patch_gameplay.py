from pathlib import Path
p=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-55a43370-8734-4825-92a8-b0de824a45e2/ai-sessions/workspace_l7e231w9/wprefabs/dragon_v17/scripts')
f=p/'dragon_combat.lua';s=f.read_text();assert 'showSigil(arenaCenter,ArenaRadius,night)' in s;s=s.replace('showSigil(arenaCenter,ArenaRadius,night)','showSigil(arenaCenter,ArenaRadius,true)');s=s.replace("return false,'影灵只在夜晚出现'","return false,'晚上才能挑战影灵'");f.write_text(s)
f=p/'dragon_rpg.lua';s=f.read_text();assert '(nearArena and battle.IsNight())' in s;s=s.replace('(nearArena and battle.IsNight())','(nearArena)');f.write_text(s)
f=p/'dragon_world_bridge.lua';s=f.read_text();a=s.index('---------------------------------------------------------------- v15：裂隙之门的漩涡');b=s.index('---------------------------------------------------------------- v15：眩晕',a)
s=s[:a]+'''---------------------------------------------------------------- 裂隙之门：门洞固定平面，纹理在门内旋转
UI.vortex={}
function UI.gateFrame(gate)
 local tr=gate.transform
 local lo,hi=nil,nil
 local rs=gate:GetComponentsInChildren(typeof(UnityEngine.Renderer),true)
 for i=0,rs.Length-1 do
  local r=rs[i];local bounds=r.localBounds
  for x=0,1 do for y=0,1 do for z=0,1 do
   local p=Vector3(x==0 and bounds.min.x or bounds.max.x,y==0 and bounds.min.y or bounds.max.y,z==0 and bounds.min.z or bounds.max.z)
   p=tr:InverseTransformPoint(r.transform:TransformPoint(p))
   lo=lo and Vector3.Min(lo,p)or p;hi=hi and Vector3.Max(hi,p)or p
  end end end
 end
 if not lo or hi.y-lo.y<.01 then return nil end
 local height=hi.y-lo.y
 -- This gate's authored opening is centered at 54% of its height; the
 -- arch plane is just behind the mid-depth of its staircase bounds.
 local localCenter=Vector3((lo.x+hi.x)*.5,lo.y+height*.54,(lo.z+hi.z)*.5+height*.02)
 return {anchor=tr,localCenter=localCenter,center=tr:TransformPoint(localCenter),rotation=tr.rotation,size=height*math.abs(tr.lossyScale.y)*.62}
end
function UI.setupVortex()
 if UI.vortex.ready or UI.vortex.failed or not UI.K.ready then return end
 local gate=GameObject.Find('arena_gate');if not gate then return end
 local first=UI.gateFrame(gate);if not first then return end
 local tex=UI.K.tex.vortex;UI.vortex.list={}
 local frames={first,{center=Vector3(ARENA_EXIT.x,ARENA_EXIT.y+1.7,ARENA_EXIT.z),rotation=Quaternion.identity,size=5.4}}
 for i,v in ipairs(frames)do
  v.layers={}
  for k,spec in ipairs({{1,UnityEngine.Color(.55,.35,1,.55),26},{.78,UnityEngine.Color(.5,.85,1,.8),-48},{.48,UnityEngine.Color(1,1,1,.95),95}})do
   local q=UI.fxQuad('RiftVortex'..i..'_'..k,tex,spec[2],v.size*spec[1])
   if not q then UI.vortex.failed=true;report('vortex: no shader');return end
   if q.mat:HasProperty('_Cull')then q.mat:SetFloat('_Cull',0)end
   q.speed=spec[3];q.base=v.size*spec[1];v.layers[k]=q
  end
  local lg=UnityEngine.GameObject('RiftVortexLight'..i);local light=lg:AddComponent(typeof(UnityEngine.Light))
  light.type=UnityEngine.LightType.Point;light.color=UnityEngine.Color(.55,.5,1,1);light.range=9;light.intensity=2.2;light.shadows=UnityEngine.LightShadows.None
  lg.transform.position=v.center;v.light=light;UI.vortex.list[i]=v
 end
 UI.vortex.ready=true
end
function UI.updateVortex()
 if not UI.vortex.ready then UI.setupVortex();return end
 local t=Time.time
 for _,v in ipairs(UI.vortex.list)do
  if v.anchor then
   v.center=v.anchor:TransformPoint(v.localCenter);v.rotation=v.anchor.rotation
   ARENA_GATE=Vector3(v.center.x,v.anchor.position.y,v.center.z)
   local out=v.center+v.anchor.forward*4
   ARENA_OUT={out.x,v.anchor.position.y+.6,out.z,v.anchor.eulerAngles.y}
  end
  for k,q in ipairs(v.layers)do
   local size=q.base*(1+.025*math.sin(t*2.3+k))
   q.go.transform.position=v.center+(v.rotation*Vector3.forward)*(.025*k)
   q.go.transform.rotation=v.rotation*Quaternion.Euler(0,0,t*q.speed)
   q.go.transform.localScale=Vector3(size,size,1)
  end
  v.light.transform.position=v.center;v.light.intensity=2+.6*math.sin(t*3.1)
 end
end

'''+s[b:]
s=s.replace('if p.y > 38 and flatDistance(p, ARENA_GATE) < PORTAL_RADIUS then','if math.abs(p.y-ARENA_GATE.y)<5 and flatDistance(p, ARENA_GATE) < PORTAL_RADIUS then')
# Search only the 175 retained tufts, avoiding missing-node lookups after reduction.
import json,re
names=[r['name'] for r in json.loads(Path('assets/v17/wheat-plan.json').read_text())['rows']]
s=re.sub(r'UI.reeds=\{names=\{[^\n]*?\},items=\{\},next=0,tick=0\}', 'UI.reeds={names={'+','.join(json.dumps(x) for x in names)+'},items={},next=0,tick=0}',s,count=1)
s=s.replace("function UI.addReedNames()for i=260,349 do UI.reeds.names[#UI.reeds.names+1]='golden_geometry_'..i end end","function UI.addReedNames()end -- v17: names already contain all 175 retained tufts")
f.write_text(s)
from lupa import LuaRuntime
lua=LuaRuntime(unpack_returned_tuples=True)
for f in p.glob('*.lua'):
 result=lua.eval('load')(f.read_text());assert not isinstance(result,tuple), (f.name,result)
print('Patched persistent arena + daytime entry, portal frame/trigger, and 175-tuft scan; all Lua syntax valid.')
