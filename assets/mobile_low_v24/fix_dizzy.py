from pathlib import Path
import shutil
A=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9/ai-sessions/workspace_m293a9tg/wprefabs/dragon_fx_mobile_v22/scripts')
p=A/'dragon_world_bridge.lua';s=p.read_text()
s=s.replace('if D.cam.fieldOfView==D.appliedFov then D.cam.fieldOfView=D.baseFov end',"if D.appliedFov then D.cam.fieldOfView=math.max(35,math.min(85,D.baseFov or 60)) end")
s=s.replace('D.cam=main;D.baseFov=main.fieldOfView','D.cam=main')
s=s.replace('(math.sin(t*1.7)*13+math.sin(t*4.1)*4)*k','(math.sin(t*1.7)*2+math.sin(t*4.1)) *k')
s=s.replace('math.sin(t*1.1+1)*5*k','math.sin(t*1.1+1)*1.2*k').replace('math.sin(t*1.9)*4*k','math.sin(t*1.9)*1.0*k')
s=s.replace('D.appliedFov=D.baseFov+(math.sin(t*2.6)*16+math.sin(t*5.3)*5)*k-2.5*sh\n D.cam.fieldOfView=D.appliedFov;D.cameraApplied=true','-- FOV belongs to the player camera: never accumulate or compete with its controller.\n D.cameraApplied=true')
s=s.replace('function IsDizzy()', '''function ClearDizzy()
 local D=UI.dizzy;D.untilT=nil;D.shakeT=nil;D.shakeLeft=0;D.flashT=nil
 UI.restoreFxCamera()
 if D.overlay then D.overlay:SetActive(false)end
end
function IsDizzy()''')
p.write_text(s)
p=A/'dragon_exploration.lua';shutil.copy2(p,'assets/mobile_low_v24/before/dragon_exploration.lua');s=p.read_text().replace('local function restoreBuff()\n if not buff then return end','local function restoreBuff()\n if main and main.ClearDizzy then main.ClearDizzy()end\n if not buff then return end');p.write_text(s)
from lupa import LuaRuntime
for p in A.glob('*.lua'):LuaRuntime().execute('assert(load(...))',p.read_text())
print('Dizzy no longer writes FOV. Buff replacement cancels dizziness. All Lua syntax passed.')
