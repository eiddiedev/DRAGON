UI.lowRender={started=false,nextAt=0,passes=0,cameras={},errors={}}
function UI.applyLowRender()
 local s=UI.lowRender;local now=Time.realtimeSinceStartup
 if now<s.nextAt then return end;s.nextAt=now+1
 local Q=UnityEngine.QualitySettings
 if not s.started then
  s.started=true;s.old={fps=UnityEngine.Application.targetFrameRate,aa=Q.antiAliasing,shadows=Q.shadows,distance=Q.shadowDistance,pixel=Q.pixelLightCount}
  UnityEngine.Application.targetFrameRate=30;Q.antiAliasing=0;Q.shadows=UnityEngine.ShadowQuality.Disable;Q.shadowDistance=0;Q.pixelLightCount=1
  local ok,err=pcall(function()local p=Q.renderPipeline or UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline;if p then s.pipeline=p;s.oldScale=p.renderScale;p.renderScale=math.min(p.renderScale,.6);s.renderScale=p.renderScale end end)
  if not ok then s.errors.renderScale=tostring(err)end
 end
 -- The platform resets the frame cap during actor startup; keep the requested cap.
 if UnityEngine.Application.targetFrameRate~=30 then UnityEngine.Application.targetFrameRate=30 end
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
function Update()local ok,err=pcall(UI.applyLowRender);if not ok then UI.lowRender.errors.apply=tostring(err)end;UI.v24Update()end
function OnDisable()UI.restoreLowRender();UI.v24Disable()end
function OnDestroy()UI.restoreLowRender();UI.v24Destroy()end
function GetMobileRenderStatus()return {build='v24-low-render',fps=UnityEngine.Application.targetFrameRate,aa=UnityEngine.QualitySettings.antiAliasing,shadows=tostring(UnityEngine.QualitySettings.shadows),renderScale=UI.lowRender.renderScale,errors=UI.lowRender.errors}end
