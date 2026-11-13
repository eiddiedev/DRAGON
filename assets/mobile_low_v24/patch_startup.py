from pathlib import Path
A=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9/ai-sessions/workspace_m293a9tg/wprefabs/dragon_fx_mobile_v22/scripts/dragon_world_bridge.lua')
s=A.read_text()
s=s.replace('UnityEngine.TextureFormat.RGBA32, true)','UnityEngine.TextureFormat.RGBA32, false)')
s=s.replace('if not t:LoadImage(bytes) then','if not t:LoadImage(bytes,true) then')
s=s.replace('t.filterMode = UnityEngine.FilterMode.Trilinear','t.filterMode = UnityEngine.FilterMode.Bilinear')
s=s.replace('local dt = Time.unscaledDeltaTime\n    UI.t = UI.t + dt','local dt = Time.unscaledDeltaTime\n    UI.t = UI.t + dt')
s=s.replace('if kitReady and (UI.tryT', 'if kitReady and UI.requiredModelsReady() and (UI.tryT')
s=s.replace('''            elseif UI.wait > 45 then
                UI.log("textures missing, skip ui")
                UI.cover.target = 0
                UI.state = "off"
''','''            elseif UI.wait > 45 then
                UI.loading.error="书页资源准备超时，请退出世界后重试"
''')
s=s.replace('''            pcall(function() UI.root:SetActive(false) end)''','''            UI.loading.error="开场资源加载失败，请退出世界后重试"
            pcall(function() UI.cover.cg.alpha=.35 end)''')
s=s.replace('''    updateSky()
    if skyReady then UI.updateMotion() end''','''    UI.updateLoadingStatus()
    updateSky()
    if skyReady then UI.updateMotion() end''')
# Avoid a second full scene render during intro. Restore original camera afterwards.
s=s.replace('''    UI.cam = cam
    UI.main = main''','''    UI.cam = cam
    UI.main = main
    UI.mainWasEnabled=main.enabled
    main.enabled=false''')
s=s.replace('''function UI.camEnd()
    if UI.cam ~= nil then''','''function UI.camEnd()
    if UI.main and UI.mainWasEnabled~=nil then UI.main.enabled=UI.mainWasEnabled;UI.mainWasEnabled=nil end
    if UI.cam ~= nil then''')
s+='''
-- v24 low rendering and bounded startup diagnostics. No resource grants.
UI.loading={started=nil,nextAt=0,missing={},checks=0}
function UI.requiredModelsReady()
 local st=UI.loading;local now=Time.realtimeSinceStartup
 if now<st.nextModels then return #st.missing==0 end
 st.nextModels=now+1;st.missing={};st.checks=st.checks+1
 for _,name in ipairs({'tripo_horse','tripo_witch','dragon_v8_live','flying_carpet','golden_geometry_150','ShadowSpiritSource'})do
  local go=UnityEngine.GameObject.Find(name)
  local rs=go and go:GetComponentsInChildren(typeof(UnityEngine.Renderer),true)
  if not rs or rs.Length==0 then st.missing[#st.missing+1]=name end
 end
 return #st.missing==0
end
UI.loading.nextModels=0
function UI.updateLoadingStatus()
 local st=UI.loading;local now=Time.realtimeSinceStartup
 if not st.started then st.started=now end
 if now<st.nextAt then return end;st.nextAt=now+.5
 if UI.state~='boot'and not UI.failed then if st.label then st.label.gameObject:SetActive(false)end;return end
 if not st.label and UI.cover then
  local fonts=UnityEngine.Resources.FindObjectsOfTypeAll(typeof(UnityEngine.Font));local font=nil
  for i=0,fonts.Length-1 do if fonts[i].name=='NotoSansSC-Medium'then font=fonts[i];break end end
  if not font and fonts.Length>0 then font=fonts[0]end
  if font then
   local go=UnityEngine.GameObject('WorldLoadingStatus');go.transform:SetParent(UI.cover.rt,false)
   local t=go:AddComponent(typeof(UnityEngine.UI.Text));t.font=font;t.fontSize=26;t.color=UnityEngine.Color(.9,.86,.72,1);t.alignment=UnityEngine.TextAnchor.MiddleCenter;t.raycastTarget=false
   t.rectTransform.sizeDelta=UI.V2(1050,120);t.rectTransform.anchoredPosition=UI.V2(0,-120);st.label=t
  end
 end
 local actor=DouyinActorService.GetLocalActor();local elapsed=math.floor(now-st.started)
 local stage=not DouyinNetService.isNetworkSettled and '正在连接房间' or(not actor and '正在准备角色' or(not UI.K.ready and '正在展开古书' or '正在准备世界资源'))
 if st.label then st.label.text=st.error or(elapsed>45 and (stage..'超时，请退出世界后重试')or(stage..' · '..elapsed..'秒'))end
 -- Never hide the only progress text behind an opaque black cover indefinitely.
 if elapsed>45 and UI.cover then UI.cover.cg.alpha=.4 end
end
UI.lowRender={started=false,nextAt=0,passes=0,cameras={},errors={}}
function UI.applyLowRender()
 local s=UI.lowRender;local now=Time.realtimeSinceStartup
 if now<s.nextAt then return end;s.nextAt=now+1
 local Q=UnityEngine.QualitySettings
 if not s.started then
  s.started=true;s.old={fps=UnityEngine.Application.targetFrameRate,aa=Q.antiAliasing,shadows=Q.shadows,distance=Q.shadowDistance,pixel=Q.pixelLightCount}
  UnityEngine.Application.targetFrameRate=30;Q.antiAliasing=0;Q.shadows=UnityEngine.ShadowQuality.Disable;Q.shadowDistance=0;Q.pixelLightCount=1
  local ok,err=pcall(function()local p=Q.renderPipeline;if p then s.pipeline=p;s.oldScale=p.renderScale;p.renderScale=math.min(p.renderScale,.6);s.renderScale=p.renderScale end end)
  if not ok then s.errors.renderScale=tostring(err)end
 end
 if s.passes>=45 then return end;s.passes=s.passes+1
 local cams=UnityEngine.Camera.allCameras
 for i=0,cams.Length-1 do local c=cams[i]
  if not s.cameras[c]then
   local saved={hdr=c.allowHDR,msaa=c.allowMSAA};s.cameras[c]=saved;c.allowHDR=false;c.allowMSAA=false
   local ok=pcall(function()local d=c:GetComponent(typeof(CS.UnityEngine.Rendering.Universal.UniversalAdditionalCameraData));if d then saved.data=d;saved.post=d.renderPostProcessing;saved.shadow=d.renderShadows;d.renderPostProcessing=false;d.renderShadows=false end end)
  end
 end
end
function UI.restoreLowRender()
 local s=UI.lowRender;if not s.started then return end
 pcall(function()local q=UnityEngine.QualitySettings;UnityEngine.Application.targetFrameRate=s.old.fps;q.antiAliasing=s.old.aa;q.shadows=s.old.shadows;q.shadowDistance=s.old.distance;q.pixelLightCount=s.old.pixel;if s.pipeline and s.oldScale then s.pipeline.renderScale=s.oldScale end end)
 for c,v in pairs(s.cameras)do pcall(function()c.allowHDR=v.hdr;c.allowMSAA=v.msaa;if v.data then v.data.renderPostProcessing=v.post;v.data.renderShadows=v.shadow end end)end
 s.cameras={};s.started=false
end
UI.v24Update=Update;UI.v24Destroy=OnDestroy;UI.v24Disable=OnDisable
function Update()UI.applyLowRender();UI.v24Update()end
function OnDisable()UI.restoreLowRender();UI.v24Disable()end
function OnDestroy()UI.restoreLowRender();UI.v24Destroy()end
function GetMobileRenderStatus()return {build='v24-low-render',fps=UnityEngine.Application.targetFrameRate,aa=UnityEngine.QualitySettings.antiAliasing,shadows=tostring(UnityEngine.QualitySettings.shadows),renderScale=UI.lowRender.renderScale,errors=UI.lowRender.errors}end
function GetLoadingDiagnostics()return {build='v24',state=UI.state,uiFailed=UI.failed,error=UI.loading.error,missing=UI.loading.missing,checks=UI.loading.checks,atlas=UI.K.at,net=DouyinNetService.isNetworkSettled,actor=DouyinActorService.GetLocalActor()~=nil}end
'''
A.write_text(s)
from lupa import LuaRuntime
L=LuaRuntime()
for p in A.parent.glob('*.lua'):
 ok,err=L.eval('function(s)local f,e=load(s);return f~=nil,e end')(p.read_text());assert ok,(p.name,err)
print('Lua compile passed')
