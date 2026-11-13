
-- review-v27: prevent extreme upward orbit from taking the roaming camera
-- underneath one-sided terrain. This is a pitch limit, not a second camera
-- controller or a promise of collision avoidance on every steep slope.
UI.roamCameraGuard={minPitch=0,corrections=0,status='waiting',nextResolve=0,resolveAttempts=0}
function UI.roamCameraContext()
 local s=UI.roamCameraGuard
 if UI.state~='play' or UI.cam or (DR.phase1 and DR.phase1.menu) then return nil,'menu-or-intro' end
 if camState=='holding' or camState=='releasing' then return nil,'spawn-camera' end
 if DR.rider or DR.camera or DR.soul then return nil,'dragon-camera' end
 local d=UI.dizzy
 if d and ((d.untilT and d.untilT>Time.time) or d.shakeT or d.cameraApplied) then return nil,'screen-effect' end
 if DouyinCameraService.IsPhotographMode() then return nil,'photo' end
 local actor=DouyinActorService.GetLocalActor()
 if not actor then return nil,'no-actor' end
 if actor:IsSitting() or actor:IsFlying() or actor:IsSwimming() then return nil,'actor-camera' end
 -- Cache script handles locally; never replace runtime_scope.GetScript.
 if not s.exploration or not s.battle then
  local now=Time.realtimeSinceStartup
  if now>=s.nextResolve and s.resolveAttempts<30 then
   s.resolveAttempts=s.resolveAttempts+1;s.nextResolve=now+1
   local scope=DR.phase1 and DR.phase1.scope
   if scope then
    if not s.exploration then s.exploration=scope:GetScript('dragon_exploration.lua') end
    if not s.battle then s.battle=scope:GetScript('dragon_combat.lua') end
   end
  end
  if not s.exploration or not s.battle then return nil,'dependencies' end
 end
 local state=s.exploration.GetStatus()
 if not state or not state.loaded then return nil,'not-ready' end
 if state.mode or state.potion or state.buff then return nil,'exploration-effect' end
 if s.battle.IsParticipating() then return nil,'battle' end
 local camera=DouyinCameraService.GetCamera()
 if not camera or not camera.enabled then return nil,'no-camera' end
 return camera,'roaming'
end
function UI.guardRoamingPitch()
 local s=UI.roamCameraGuard
 if s.failed then return end
 local camera,reason=UI.roamCameraContext();s.status=reason
 if not camera then return end
 local pitch=DouyinCameraService.GetPitch()
 if type(pitch)~='number' or pitch~=pitch or pitch==math.huge or pitch==-math.huge then s.status='no-pitch';return end
 s.lastPitch=pitch
 -- Do not pull the user's valid angle toward a preset. Write only when
 -- crossing the lower bound; yaw, distance, offset, FOV and matrices stay owned
 -- by the platform and the existing gameplay camera lifecycles.
 if pitch<s.minPitch then
  DouyinCameraService.SetPitch(s.minPitch)
  s.corrections=s.corrections+1;s.lastPitch=s.minPitch;s.status='corrected'
 end
end
UI.roamCameraPreviousLate=LateUpdate
function LateUpdate()
 if UI.roamCameraPreviousLate then UI.roamCameraPreviousLate() end
 local ok,err=pcall(UI.guardRoamingPitch)
 if not ok then
  UI.roamCameraGuard.failed=true;UI.roamCameraGuard.status='error';UI.roamCameraGuard.error=tostring(err)
  report('roaming camera guard '..tostring(err))
 end
end
UI.roamCameraPreviousDisable=OnDisable
function OnDisable()
 -- No temporary camera transform or projection was installed. Do not restore
 -- a previously unsafe angle over the next mode's camera settings.
 UI.roamCameraGuard.exploration=nil;UI.roamCameraGuard.battle=nil
 UI.roamCameraGuard.resolveAttempts=0;UI.roamCameraGuard.nextResolve=0
 if UI.roamCameraPreviousDisable then UI.roamCameraPreviousDisable() end
end
function GetRoamingCameraDiagnostics()
 local s=UI.roamCameraGuard
 return {build='review-v27-roaming-pitch',minPitch=s.minPitch,pitch=s.lastPitch,status=s.status,corrections=s.corrections,failed=s.failed==true,error=s.error,dependencyAttempts=s.resolveAttempts}
end
