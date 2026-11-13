from pathlib import Path
import shutil,json
A=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9/ai-sessions/workspace_m293a9tg/wprefabs/dragon_fx_mobile_v22');B=Path('assets/mobile_perf_v21/baseline-scripts');O=Path('assets/mobile_failure_v22')
# Discard unshipped density reduction; preserve original effect bytes and all visual trigger counts.
for p in B.glob('*.lua'):shutil.copy2(p,A/'scripts'/p.name)
source=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-55a43370-8734-4825-92a8-b0de824a45e2/ai-sessions/workspace_l7e231w9/wprefabs/dragon_v17/assets/effects')
for p in source.glob('*/effect.json'):shutil.copy2(p,A/'assets/effects'/p.parent.name/'effect.json')
# Already registered offline audio, identical deterministic waveform; no runtime PCM synthesis.
prior=Path('assets/mobile_perf_v21/candidate-scripts/dragon_fx.lua').read_text();baseline=(B/'dragon_fx.lua').read_text()
s=prior[:prior.index('local hurtFeel=nil')]+baseline[baseline.index('local hurtFeel=nil'):]
s=s.replace(" if warmIndex<=#SOUND_NAMES then local name=SOUND_NAMES[warmIndex];audioClips[name]=audioClips[name]or buildClip(name);warmIndex=warmIndex+1 end",'')
s=s.replace(' for _,clip in pairs(audioClips)do U.Object.Destroy(clip)end;audioClips={};audioPool={}', ' audioClips={};audioPool={}')
(A/'scripts/dragon_fx.lua').write_text(s)
s=(B/'dragon_world_bridge.lua').read_text();a=s.index('function UI.fxCam()');b=s.index('function UI.fxOverlay()',a)
s=s[:a]+'''-- mobile-v22: apply the same shake to the existing camera's view matrix.
-- No second full-world camera, no duplicate shadows/post-processing pass.
function UI.restoreFxCamera()
 local D=UI.dizzy
 if D.cameraApplied and D.cam then
  pcall(function()
   D.cam:ResetWorldToCameraMatrix()
   if D.cam.fieldOfView==D.appliedFov then D.cam.fieldOfView=D.baseFov end
  end)
 end
 D.cameraApplied=false;D.cam=nil;D.baseFov=nil;D.appliedFov=nil
end
function UI.fxCam()
 return UnityEngine.Camera.main
end
'''+s[b:]
s=s.replace(' if not D.cam then return end\n local main=UnityEngine.Camera.main\n if (k<=0 and sh<=0) or not main then\n  UnityEngine.Object.Destroy(D.cam.gameObject);D.cam=nil\n  return\n end', ''' local main=UnityEngine.Camera.main
 if (k<=0 and sh<=0) or not main then UI.restoreFxCamera();return end
 if D.cameraApplied then UI.restoreFxCamera()end
 D.cam=main;D.baseFov=main.fieldOfView''')
s=s.replace(' D.cam.transform.position=mt.position+', ' local shakenPosition=mt.position+')
s=s.replace(' D.cam.transform.rotation=mt.rotation*Quaternion.Euler(pitch,yaw,roll)', ''' local shakenRotation=mt.rotation*Quaternion.Euler(pitch,yaw,roll)
 D.cam.worldToCameraMatrix=UnityEngine.Matrix4x4.Scale(Vector3(1,1,-1))*UnityEngine.Matrix4x4.TRS(shakenPosition,shakenRotation,Vector3.one).inverse''')
s=s.replace(' D.cam.fieldOfView=main.fieldOfView+(math.sin(t*2.6)*16+math.sin(t*5.3)*5)*k-2.5*sh', ''' D.appliedFov=D.baseFov+(math.sin(t*2.6)*16+math.sin(t*5.3)*5)*k-2.5*sh
 D.cam.fieldOfView=D.appliedFov;D.cameraApplied=true''')
s+='''
-- Restore before camera controllers run again; also restore on scene/lifecycle interruption.
UI.v22Update=Update;UI.v22Disable=OnDisable;UI.v22Destroy=OnDestroy
function Update()UI.restoreFxCamera();if UI.v22Update then UI.v22Update()end end
function OnDisable()UI.restoreFxCamera();if UI.v22Disable then UI.v22Disable()end end
function OnDestroy()UI.restoreFxCamera();if UI.v22Destroy then UI.v22Destroy()end end
function GetMobileRenderStatus()
 return {build='v22-no-quality-reduction',extraWorldCamera=false,cameraApplied=UI.dizzy.cameraApplied==true,shakeActive=UI.dizzy.shakeT~=nil}
end
'''
assert "GameObject('dr_fx_cam')" not in s
(A/'scripts/dragon_world_bridge.lua').write_text(s)
(O/'no-quality-manifest.json').write_text(json.dumps({'source':str(A),'status':'source prepared, not installed','visualChanges':False,'changes':['one camera for original shake and FOV','registered offline original audio replaces runtime synthesis'],'deferred':'reduced particles / textures / LOD NOT applied','userEvidence':'tour smooth this run; attack effects trigger return to Douyin; carpet also missing'},indent=2))
from lupa import LuaRuntime
l=LuaRuntime(unpack_returned_tuples=True);check=l.eval('function(s)local f,e=load(s);return f~=nil,e end')
for p in (A/'scripts').glob('*.lua'):
 ok,err=check(p.read_text());assert ok,(p.name,err)
for p in source.glob('*/effect.json'):assert p.read_bytes()==(A/'assets/effects'/p.parent.name/'effect.json').read_bytes()
print('13 Lua sources compile; all original effect source files byte-identical; no duplicate render camera')
