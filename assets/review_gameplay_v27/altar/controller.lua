local altarV27={group=nil,nextBind=0,nextUpdate=0,placed={},last={}}
local function setupAltar()
    runeGo,beamGo,runeGlow=runeGo or {},beamGo or {},runeGlow or {}
    local now=UnityEngine.Time.realtimeSinceStartup
    if now<altarV27.nextBind then return end
    altarV27.nextBind=now+1
    if not altarV27.group then altarV27.group=GameObject.Find('DragonAltarProgressVisuals') end
    -- Only this small owned subtree is traversed, including its initially inactive visuals.
    if altarV27.group then
        local ts=altarV27.group:GetComponentsInChildren(typeof(UnityEngine.Transform),true)
        for j=0,ts.Length-1 do
            local t=ts[j];local n=t.name
            for i=1,4 do if n=='beam_'..(i-1)then beamGo[i]=t.gameObject end end
            for i=1,3 do if n=='runeg_'..(i-1)then runeGlow[i]=t.gameObject end end
        end
    end
    for i=1,4 do
        local anchor=runeGo[i]
        if not anchor then anchor=GameObject.Find(i<4 and ('rune_'..(i-1))or 'altar3');runeGo[i]=anchor end
        local beam=beamGo[i]
        if anchor and beam and not altarV27.placed[i]then
            local rs=anchor:GetComponentsInChildren(typeof(UnityEngine.Renderer),true)
            local top=nil
            for j=0,rs.Length-1 do local r=rs[j]
                if r.bounds.size.y>0.01 then top=math.max(top or -math.huge,r.bounds.max.y)end
            end
            if top then
                -- Light starts at the loaded stone/altar surface, never an obsolete hardcoded Y.
                local p=anchor.transform.position
                beam.transform.position=Vector3(p.x,top+.04,p.z)
                local glow=runeGlow[i]
                if glow then glow.transform.position=p end
                altarV27.placed[i]=true
            end
        end
    end
    local done=altarV27.group~=nil
    for i=1,4 do if not beamGo[i]or not altarV27.placed[i]then done=false end end
    for i=1,3 do if not runeGlow[i]then done=false end end
    if done then altarV27.nextBind=math.huge end
end
local function resetAltar()
    litCount=0
    for i=1,4 do
        if i<4 then runeLit[i]=false end
        if beamGo and beamGo[i]then beamGo[i]:SetActive(false)end
        if runeGlow and runeGlow[i]then runeGlow[i]:SetActive(false)end
    end
end
local function updateAltar(p)
    local now=UnityEngine.Time.realtimeSinceStartup
    if now<altarV27.nextUpdate then return end
    altarV27.nextUpdate=now+.25
    setupAltar()
    local progress=beamGo and beamGo.progress
    local profile=nil
    if progress then local ok,value=pcall(progress.GetProfile);if ok then profile=value end end
    local deposits=profile and profile.deposited or {}
    for i,key in ipairs({'moon','ember','stardew'})do
        local lit=(tonumber(deposits[key])or 0)>0 and altarV27.placed[i]==true
        if beamGo[i]then beamGo[i]:SetActive(lit)end
        if runeGlow[i]then runeGlow[i]:SetActive(lit)end
        altarV27.last[i]=lit
    end
    local lit=profile~=nil and (profile.hatchReady==true or profile.pact==true)and altarV27.placed[4]==true
    if beamGo[4]then beamGo[4]:SetActive(lit)end
    altarV27.last[4]=lit
end
function GetAltarVisualDiagnostics()
    return {version='v27-progress-altar',group=altarV27.group~=nil,placed=altarV27.placed,lit=altarV27.last}
end
