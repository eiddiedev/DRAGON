from pathlib import Path
import shutil,json
base=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-55a43370-8734-4825-92a8-b0de824a45e2/ai-sessions/workspace_l7e231w9/wprefabs/dragon_v17/scripts')
out=Path('assets/vegetation_reduce_v18/source-before');out.mkdir(exist_ok=True)
for name in ['dragon_exploration.lua','dragon_world_bridge.lua']:shutil.copy2(base/name,out/name)
p=base/'dragon_exploration.lua';s=p.read_text();s=s.replace('local contractSession=nil','local contractSession=nil\nlocal queuedNative=nil')
s=s.replace('function OnInteractorButtonClick(index)handleNativeClick(index)end','''local function queueNativeClick(index)
 -- Keep the native button alive until the engine has completed click dispatch.
 if queuedNative or not nativeTarget or nativeTarget~=current then return end
 queuedNative={index=index,target=nativeTarget,frame=U.Time.frameCount}
end
function OnInteractorButtonClick(index)queueNativeClick(index)end''')
s=s.replace("local world=main.GetExplorationState();",'''if queuedNative and U.Time.frameCount>queuedNative.frame then
  local click=queuedNative;queuedNative=nil
  if click.target==nativeTarget and click.target==current then handleNativeClick(click.index)end
 end
 local world=main.GetExplorationState();''')
s=s.replace('function()handleNativeClick(1)end','function()queueNativeClick(1)end').replace('function()handleNativeClick(2)end','function()queueNativeClick(2)end')
s=s.replace('function OnDisable()contractSession=nil;','function OnDisable()queuedNative=nil;contractSession=nil;')
p.write_text(s)
p=base/'dragon_world_bridge.lua';s=p.read_text();idx=s.index('\n');s=s[:idx+1]+'''---@start
---@var BackgroundMusic:UnityEngine.AudioClip=nil
---@name 背景音乐
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BackgroundMusicVolume:number=0.65
---@name 开场音量
---@var BackgroundMusicMaxDistance:number=1000
---@name 最大作用范围
---@var ExplorationMusicVolume:number=0.18
---@name 游览音量
---@end
'''+s[idx+1:]
start=s.index('local alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ');end=s.index('function M.dispose(state)',start)
s=s[:start]+'''function M.new(parent)
 local go=UnityEngine.GameObject("dr_desktop_bgm")
 local source=go:AddComponent(typeof(UnityEngine.AudioSource))
 source.playOnAwake=false;source.loop=true;source.spatialBlend=1
 source.rolloffMode=UnityEngine.AudioRolloffMode.Linear
 source.priority=0;source.dopplerLevel=0;source.ignoreListenerPause=true
 return {go=go,source=source}
end
function M.update(state)
 local clip=BackgroundMusic
 if clip~=state.clip then state.source:Stop();state.clip=clip;state.source.clip=clip end
 local distance=BackgroundMusicMaxDistance or 1000
 state.source.minDistance=math.min(1,distance*.1);state.source.maxDistance=math.max(.01,distance)
 local listener=UnityEngine.Object.FindObjectOfType(typeof(UnityEngine.AudioListener))
 if listener then state.go.transform.position=listener.transform.position end
 if UI.state=="play"or UI.state=="map"then state.fadeStarted=true end
 if state.fadeStarted then state.fadeElapsed=math.min(10,(state.fadeElapsed or 0)+UnityEngine.Time.unscaledDeltaTime)end
 local t=(state.fadeElapsed or 0)/10;local e=t*t*(3-2*t)
 state.source.volume=math.max(0,math.min(1,(BackgroundMusicVolume or .65)+((ExplorationMusicVolume or .18)-(BackgroundMusicVolume or .65))*e))
 if not clip or distance<=0 or state.source.volume<=0 then state.source:Stop()
 elseif not state.source.isPlaying then state.source:Play()end
end

'''+s[end:]
s=s.replace('    if state.clip then UnityEngine.Object.Destroy(state.clip) end','    -- Injected AudioClip belongs to the asset service; do not destroy it.')
p.write_text(s)
print('bridge bytes',len(s.encode()))
