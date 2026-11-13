-- v27: retain authored platform quality. Only frame pacing is capped; no
-- render-scale/texture/AA/HDR/post-processing/shadow setting is downgraded.
UI.framePacing = { started = false, nextAt = 0 }
function UI.applyFramePacing()
 local s = UI.framePacing; local now = Time.realtimeSinceStartup
 if now < s.nextAt then return end; s.nextAt = now + 1
 if not s.started then s.started = true; s.originalFPS = UnityEngine.Application.targetFrameRate end
 if UnityEngine.Application.targetFrameRate ~= 30 then UnityEngine.Application.targetFrameRate = 30 end
end
function UI.restoreFramePacing()
 local s = UI.framePacing
 if s.started then UnityEngine.Application.targetFrameRate = s.originalFPS; s.started = false end
end
UI.v27VisualUpdate = Update; UI.v27VisualDestroy = OnDestroy; UI.v27VisualDisable = OnDisable
function Update() UI.applyFramePacing(); UI.v27VisualUpdate() end
function OnDisable()
 UI.restoreFramePacing(); holyTried.dispose()
 if UI.v27VisualDisable then UI.v27VisualDisable() end
end
function OnDestroy()
 UI.restoreFramePacing(); holyTried.dispose()
 if UI.v27VisualDestroy then UI.v27VisualDestroy() end
end
function GetMobileRenderStatus()
 local q = UnityEngine.QualitySettings
 local status = { build = 'v27-authored-quality', fps = UnityEngine.Application.targetFrameRate,
  aa = q.antiAliasing, shadows = tostring(q.shadows), shadowDistance = q.shadowDistance,
  pixelLights = q.pixelLightCount, qualityModified = false, cameras = {} }
 pcall(function()
  local pipeline = q.renderPipeline or UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline
  if pipeline then status.renderScale = pipeline.renderScale end
 end)
 local cameras = UnityEngine.Camera.allCameras
 for i = 0, cameras.Length - 1 do
  local c = cameras[i]; local saved = { name = c.name, hdr = c.allowHDR, msaa = c.allowMSAA }
  pcall(function()
   local data = c:GetComponent(typeof(CS.UnityEngine.Rendering.Universal.UniversalAdditionalCameraData))
   if data then saved.post = data.renderPostProcessing; saved.shadows = data.renderShadows end
  end)
  status.cameras[#status.cameras + 1] = saved
 end
 return status
end

