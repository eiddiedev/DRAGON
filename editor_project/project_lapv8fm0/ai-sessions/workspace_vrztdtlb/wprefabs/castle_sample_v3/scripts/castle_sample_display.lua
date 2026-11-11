---@id d0c57dfc-0a46-4558-9ca8-250715805706
---@referenceName castle_sample_display.lua
---@displayName 城堡入口钟塔样板烘焙显示
local U=CS.UnityEngine
local entries,records,seen={},{},{}
local unsupported,elapsed,attempts=0,0,0
local fields={'_BaseTex','_BaseColor','_ColorPower','_UseVertexColor','_RimPower','_EmissionTex','_EmissionMask','_EmissionColor','_EmissionPower','_ORM','_Metallic','_Smoothness','_AOIntensity'}
local function supports(m)
 if m.shader.name~='Douyin/AI/PBR/EnvLit_AI' then return false end
 for _,key in ipairs(fields) do if not m:HasProperty(key) then return false end end
 return true
end
local function process(root)
 local rs=root:GetComponentsInChildren(typeof(U.Renderer),true)
 for i=0,rs.Length-1 do
  local r=rs[i];local id=r:GetInstanceID()
  if not seen[id] then
   local originals=r.sharedMaterials;local changed=r.sharedMaterials;local touched=false
   for j=0,originals.Length-1 do
    local m=originals[j]
    if m and supports(m) and m:GetTexture('_BaseTex') then
     local c=U.Material(m)
     c:SetTexture('_EmissionTex',m:GetTexture('_BaseTex'))
     c:SetTextureScale('_EmissionTex',m:GetTextureScale('_BaseTex'))
     c:SetTextureOffset('_EmissionTex',m:GetTextureOffset('_BaseTex'))
     c:SetTexture('_EmissionMask',U.Texture2D.whiteTexture)
     c:SetColor('_EmissionColor',U.Color.white);c:SetFloat('_EmissionPower',1);c:EnableKeyword('_EMISSION')
     c:SetColor('_BaseColor',U.Color.black);c:SetFloat('_ColorPower',0);c:SetFloat('_UseVertexColor',0);c:SetFloat('_RimPower',0)
     c:SetTexture('_ORM',U.Texture2D.whiteTexture);c:SetFloat('_Metallic',1);c:SetFloat('_Smoothness',0);c:SetFloat('_AOIntensity',0)
     changed[j]=c;touched=true;entries[#entries+1]=c
    else unsupported=unsupported+1 end
   end
   if touched then r.sharedMaterials=changed;records[#records+1]={renderer=r,original=originals} end
   seen[id]=true
  end
 end
end
local function scan()
 process(self.gameObject)

end
function Start() scan() end
function Update()
 if attempts>=20 then return end
 elapsed=elapsed+U.Time.deltaTime
 if elapsed>=.5 then elapsed=0;attempts=attempts+1;scan() end
end
function GetDisplayState() return {materials=#entries,renderers=#records,unsupported=unsupported} end
function OnDestroy()
 for _,v in ipairs(records) do if v.renderer then v.renderer.sharedMaterials=v.original end end
 for _,m in ipairs(entries) do U.Object.Destroy(m) end
 entries,records,seen={},{},{}
end
