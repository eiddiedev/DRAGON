---@id 87a26c94-24ec-421a-9398-eca7a4141139
---@referenceName castle_tone.lua
---@displayName 城堡外暗内亮调色
-- Display exposure only: retains the existing full-GI textures and all geometry.
local U=CS.UnityEngine
local exteriorRoots={'城堡入口与钟塔精修样板','城堡塔楼与外围城墙精修'}
local interiorNames={castle_gi_hall_front=true,castle_gi_hall_rear=true,castle_gi_library=true,castle_gi_dining=true,castle_gi_armory=true,castle_gi_kitchen=true,castle_gi_sanctuary=true,castle_gi_bedchamber=true}
local fixtureNames={['城堡火盆左']=true,['城堡火盆右']=true,['书库桌上烛光']=true,['宴厅壁炉光']=true}
local roomPositions={{127,78,172},{117,77,179},{137,77,179},{117.6,75.5,168},{135.7,75.5,168},{127,74.8,193},{127,80.5,193},{127,78,184}}
local materials,lights,seenMaterials,seenLights={},{},{},{}
local exteriorCount,interiorCount,elapsed,total=0,0,0,0
local exteriorPower,interiorPower,lightGain=.68,1.35,1.4
local function adjustMaterial(m,inside,clock)
 if not m or seenMaterials[m:GetInstanceID()] then return end
 if m.shader.name~='Douyin/AI/PBR/EnvLit_AI' or not m:HasProperty('_EmissionPower') or not m:HasProperty('_BaseColor') then return end
 -- Wait for the owning GI display script to finish cloning and configuring it.
 local c=m:GetColor('_BaseColor')
 if not m:GetTexture('_EmissionTex') or c.r+c.g+c.b>.001 or m:GetFloat('_ColorPower')~=0 then return end
 local power=inside and interiorPower or (clock and .82 or exteriorPower)
 local id=m:GetInstanceID();seenMaterials[id]=true
 materials[#materials+1]={material=m,original=m:GetFloat('_EmissionPower'),power=power}
 m:SetFloat('_EmissionPower',power)
 if inside then interiorCount=interiorCount+1 else exteriorCount=exteriorCount+1 end
end
local function process(root,inside)
 if not root then return end
 local rs=root:GetComponentsInChildren(typeof(U.Renderer),true)
 for i=0,rs.Length-1 do
  local r=rs[i]
  if not inside or interiorNames[r.name] then
   local ms=r.sharedMaterials
   for j=0,ms.Length-1 do adjustMaterial(ms[j],inside,r.name=='clock_face_receiver.001') end
  end
 end
end
local function roomLight(l)
 if l.name~='site_light' then return false end
 local p=l.transform.position
 for _,v in ipairs(roomPositions) do
  if math.abs(p.x-v[1])<.025 and math.abs(p.y-v[2])<.025 and math.abs(p.z-v[3])<.025 then return true end
 end
 return false
end
local function scan()
 for _,name in ipairs(exteriorRoots) do process(U.GameObject.Find(name),false) end
 process(U.GameObject.Find('龙眠城堡精修'),true)
 local ls=U.Object.FindObjectsOfType(typeof(U.Light))
 for i=0,ls.Length-1 do
  local l=ls[i];local id=l:GetInstanceID()
  if not seenLights[id] and l.type==U.LightType.Point and (fixtureNames[l.name] or roomLight(l)) then
   lights[#lights+1]={light=l,original=l.intensity}
   l.intensity=l.intensity*lightGain;seenLights[id]=true
  end
 end
end
function Update()
 if total>30 and exteriorCount>=12 and interiorCount==8 and #lights==12 then return end
 total=total+U.Time.deltaTime;elapsed=elapsed+U.Time.deltaTime
 if total>.75 and elapsed>(total<30 and .5 or 5) then elapsed=0;scan() end
end
function GetToneState()
 return {exteriorMaterials=exteriorCount,interiorMaterials=interiorCount,lights=#lights,exteriorPower=exteriorPower,interiorPower=interiorPower,lightGain=lightGain}
end
function OnDestroy()
 for _,v in ipairs(materials) do if v.material then v.material:SetFloat('_EmissionPower',v.original) end end
 for _,v in ipairs(lights) do if v.light then v.light.intensity=v.original end end
 materials,lights,seenMaterials,seenLights={},{},{},{}
end
