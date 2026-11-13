from pathlib import Path
A=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9/ai-sessions/workspace_m293a9tg/wprefabs/dragon_fx_mobile_v22/scripts/dragon_world_bridge.lua');s=A.read_text();Path('assets/mobile_compat_v23/bridge-before-models.lua').write_text(s)
s=s.replace('local an = rig:GetComponentInChildren(typeof(UnityEngine.Animation), true)','local ugc = rig:GetComponent(typeof(CS.ModularAnim.Runtime.UGCAnimator))\n        local an = ugc or rig:GetComponentInChildren(typeof(UnityEngine.Animation), true)',1)
a=s.index('        for _,clip in ipairs({"idle","takeoff","fly","land"}) do');b=s.index('        DR.parts={rig.transform}',a)
s=s[:a]+'''        if ugc then
            if not ugc.enabled or ugc.Controller==nil then DR.parts=nil;return end
            DR.ugc=true;DR.perchClips=true
        else
            for _,clip in ipairs({"idle","takeoff","fly","land"}) do
                if not an:GetClip(clip) then DR.parts=nil;return end
            end
            DR.ugc=false
            DR.perchClips=an:GetClip("perch") and an:GetClip("perch_takeoff") and an:GetClip("perch_land") and true or false
            an.cullingType=UnityEngine.AnimationCullingType.AlwaysAnimate
        end
        DR.v8,DR.an,DR.socket=true,an,socket
'''+s[b:]
s=s.replace('    if DR.clip == clip and DR.an:IsPlaying(clip) then return end','''    if DR.ugc then
        if DR.clip==clip then return end
        if DR.an:Play(clip) then DR.clip=clip;dbg("dragon_v23 clip="..clip) else report("dragon animation unavailable: "..clip) end
        return
    end
    if DR.clip == clip and DR.an:IsPlaying(clip) then return end''',1)
# Match original gold tones, but clone only the already-loaded supported material once per source/tone.
s=s.replace("local sh=UnityEngine.Shader.Find('Universal Render Pipeline/Lit')\n                            local m=sh and UnityEngine.Material(sh) or UnityEngine.Material(rs[ri].sharedMaterial)","local m=UnityEngine.Material(rs[ri].sharedMaterial)")
A.write_text(s)
print('external dragon animation controller; retained wheat shader')
