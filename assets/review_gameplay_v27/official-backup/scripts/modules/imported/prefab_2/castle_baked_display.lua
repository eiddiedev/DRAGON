---@id e635d9d6-ebb9-47ed-b52d-4f1a8c27d866
---@referenceName castle_baked_display.lua
---@displayName 城堡室内烘焙光照
local U=CS.UnityEngine
local names={castle_gi_hall_front=true,castle_gi_hall_rear=true,castle_gi_library=true,castle_gi_dining=true,castle_gi_armory=true,castle_gi_kitchen=true,castle_gi_sanctuary=true,castle_gi_bedchamber=true}
local entries,records={},{}
local unsupported=0
function Start()
 unsupported=0
 local rs=self.gameObject:GetComponentsInChildren(typeof(U.Renderer),true)
 for i=0,rs.Length-1 do
  local r=rs[i]
  if names[r.name] then
   local original=r.sharedMaterials
   local changed=r.sharedMaterials
   local m=original[0]
   if m and m.shader.name=='Douyin/AI/PBR/EnvLit_AI' and m:HasProperty('_EmissionTex') and m:GetTexture('_BaseTex') then
    local c=U.Material(m)
    c:SetTexture('_EmissionTex',m:GetTexture('_BaseTex'))
    c:SetTextureScale('_EmissionTex',m:GetTextureScale('_BaseTex'))
    c:SetTextureOffset('_EmissionTex',m:GetTextureOffset('_BaseTex'))
    c:SetTexture('_EmissionMask',U.Texture2D.whiteTexture)
    c:SetColor('_EmissionColor',U.Color.white)
    c:SetFloat('_EmissionPower',1)
    c:EnableKeyword('_EMISSION')
    c:SetColor('_BaseColor',U.Color.black)
    c:SetFloat('_ColorPower',0)
    c:SetFloat('_UseVertexColor',0)
    c:SetFloat('_RimPower',0)
    c:SetTexture('_ORM',U.Texture2D.whiteTexture)
    c:SetFloat('_Metallic',1)
    c:SetFloat('_Smoothness',0)
    c:SetFloat('_AOIntensity',0)
    changed[0]=c;r.sharedMaterials=changed
    entries[#entries+1]=c;records[#records+1]={r=r,original=original}
   else unsupported=unsupported+1 end
  end
 end
end
local retryElapsed,retryTotal=0,0
function Update()
 if #entries>0 or retryTotal>10 then return end
 retryElapsed=retryElapsed+U.Time.deltaTime;retryTotal=retryTotal+U.Time.deltaTime
 if retryElapsed>.5 then retryElapsed=0;Start() end
end
function GetDisplayState() return {materials=#entries,unsupported=unsupported} end
function OnDestroy()
 for _,v in ipairs(records) do if v.r then v.r.sharedMaterials=v.original end end
 for _,m in ipairs(entries) do U.Object.Destroy(m) end
 entries,records={},{}
end
