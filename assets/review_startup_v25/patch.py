from pathlib import Path
import json,zipfile,shutil
A=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9/ai-sessions/workspace_m293a9tg/wprefabs/dragon_fx_mobile_v22/scripts/dragon_world_bridge.lua')
O=Path('assets/review_startup_v25');shutil.copy2(A,O/'bridge-before.lua');s=A.read_text()
d=json.loads(zipfile.ZipFile('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-55a43370-8734-4825-92a8-b0de824a45e2/scene.data').read('SerializePcgData.json'))
refs={};names={}
for n in d['nodeTransformDatas']:
 name=n['basic']['nodeName']
 if name.startswith('ui_') or name.startswith('InkCarrier_') or name=='MobileGroundColorSource':
  param='TextureSource_'+name;uri=n['resource']['glbSliceData']['sourceUri'];refs[param]={'uri':uri};names[name]=param
ann=''
for name,param in names.items():ann+=f'---@var {param}:UnityEngine.GameObject=nil\n---@name 纹理依赖_{name}\n---@refFrom asset\n'
s=s.replace('---@end\n',ann+'---@end\n',1)
s=s.replace('if kitReady and UI.requiredModelsReady() and (UI.tryT','if kitReady and (UI.tryT',1)
a=s.index('function UI.findTextures()');b=s.index('\nfunction UI.makeGrain()',a)
s=s[:a]+'''-- Explicit asset parameters are loaded without waiting for distant streamed objects.
function UI.textureFromAsset(go)
 if not go then return nil end
 local rs=go:GetComponentsInChildren(typeof(UnityEngine.Renderer),true)
 for i=0,rs.Length-1 do
  local mats=rs[i].sharedMaterials
  for j=0,mats.Length-1 do local m=mats[j]
   if m then for _,p in ipairs({'_BaseTex','_BaseMap','_MainTex'})do
    if m:HasProperty(p)then local t=m:GetTexture(p);if t and t.width>1 and t.height>1 then return t end end
   end end
  end
 end
end
function UI.textureSource(name)
 local sources={'''+','.join("['%s']=%s"%(n,p)for n,p in names.items())+'''}
 return sources[name]
end
function UI.findTextures()
 UI.tex=UI.tex or {};UI.loading.missingUI={}
 for _,n in ipairs(UI.TEX_NAMES)do
  if not UI.tex[n]then
   local t=UI.textureFromAsset(UI.textureSource(n))
   if t then UI.tex[n]=t;t.wrapMode=UnityEngine.TextureWrapMode.Clamp end
  end
  if not UI.tex[n]then UI.loading.missingUI[#UI.loading.missingUI+1]=n end
 end
 for _,k in ipairs({'oath','font','map'})do
  if not GetInkTexture(k)then UI.loading.missingUI[#UI.loading.missingUI+1]='InkCarrier_'..k end
 end
 return #UI.loading.missingUI==0
end
''' +s[b:]
a=s.index('function GetInkTexture(key)');b=s.index('\nfunction GetMapEntrySprite()',a)
s=s[:a]+'''function GetInkTexture(key)
 if UI.inkAssets[key]then return UI.inkAssets[key]end
 local t=UI.textureFromAsset(UI.textureSource('InkCarrier_'..key))
 if t then t.wrapMode=UnityEngine.TextureWrapMode.Clamp;UI.inkAssets[key]=t end
 return t
end
'''+s[b:]
a=s.index('UI.groundCover={');b=s.index('\nUI.v23GroundUpdate=Update',a)
s=s[:a]+'''UI.groundCover={attempts=0,nextAt=0,scans=0,patched=0,status='pending',seen=setmetatable({},{__mode='k'})}
function UI.bindMobileFlowerGround()
 local s=UI.groundCover;local now=Time.realtimeSinceStartup
 if now<s.nextAt then return end;s.nextAt=now+5
 if not s.texture then
  if s.attempts>=12 then s.status='source unavailable';return end
  s.attempts=s.attempts+1
  s.texture=UI.textureFromAsset(TextureSource_MobileGroundColorSource)
  if not s.texture then return end
 end
 -- Streamed vegetation can arrive after the first two scans. Keep a low-frequency
 -- material check, shared by all instances, without creating any material copies.
 local mats=UnityEngine.Resources.FindObjectsOfTypeAll(typeof(UnityEngine.Material))
 for i=0,mats.Length-1 do local m=mats[i]
  if m and m.shader and m.shader.name=='ParaSpace/World/ENV/EnvGrass03' and m:HasProperty('_GroundTex')then
   if m:GetTexture('_GroundTex')~=s.texture then m:SetTexture('_GroundTex',s.texture);s.patched=s.patched+1 end
  end
 end
 s.scans=s.scans+1;s.status='bound'
end
'''+s[b:]
s=s.replace("UI.v23GroundUpdate();UI.bindMobileFlowerGround()","UI.v23GroundUpdate();local ok,err=pcall(UI.bindMobileFlowerGround);if not ok then UI.groundCover.status=tostring(err)end ")
s=s.replace("'正在准备世界资源'","'正在准备界面资源'")
s=s.replace("UI.loading.error=\"书页资源准备超时，请退出世界后重试\"","UI.loading.error=\"书页资源准备超时：\"..table.concat(UI.loading.missingUI or {},',')")
s=s.replace("return {build='v24',state=UI.state","return {build='v25-streaming-ui',missingUI=UI.loading.missingUI,state=UI.state")
s=s.replace("return {build='v23',status=UI.groundCover.status","return {build='v25-ground-streaming',status=UI.groundCover.status")
A.write_text(s);shutil.copy2(A,O/'dragon_world_bridge.lua')
(O/'bind-textures.js').write_text('await scene.scripts.setParams('+json.dumps({'bindings':['n155:s:4325a686-5236-4f81-972a-e9d055389cac'],'values':refs})+'); return {bound:13};')
(O/'texture-dependencies.json').write_text(json.dumps(refs,indent=2))
from lupa import LuaRuntime
l=LuaRuntime();f,e=l.eval('function(s)local f,e=load(s);return f~=nil,e end')(s);assert f,e
print('Lua syntax passed; explicit texture dependencies',len(refs))
