local holyTried = { materials = {}, found = {} }
local holyLight = nil
local function updateHolyLight()
    -- Imported foliage can arrive after the first frame. Retry each canopy
    -- independently, and retain its material instead of instantiating per frame.
    for _, name in ipairs({ "holy_canopy3", "holy_canopy4" }) do
        if not holyTried.found[name] then
            local go = GameObject.Find(name)
            if go then
                local rs = go:GetComponentsInChildren(typeof(UnityEngine.Renderer), true)
                if rs.Length > 0 then
                    for i = 0, rs.Length - 1 do
                        local m = rs[i].material
                        m:SetColor("_BaseColor", Color(1, 1, 1, 1))
                        m:SetTexture("_EmissionTex", m:GetTexture("_BaseMap") or m:GetTexture("_MainTex") or UnityEngine.Texture2D.whiteTexture)
                        m:SetColor("_EmissionColor", Color(1, .025, .055, 1))
                        holyTried.materials[#holyTried.materials + 1] = m
                    end
                    holyTried.found[name] = true
                    holyTried.lights=holyTried.lights or {}
                    local center=rs[0].bounds.center
                    holyTried.lights[#holyTried.lights+1]=addLight(center,Color(1,.12,.24,1),16,0)


                end
            end
        end
    end
    local night = 1 - blend
    local glow = night * night * (2.6 + .12 * math.sin(Time.time * .65))
    for _,light in ipairs(holyTried.lights or {}) do
        light.intensity=night*night*1.8;light.enabled=night>.01
    end
    for _, m in ipairs(holyTried.materials) do m:SetFloat("_EmissionPower", glow) end
    if not holyLight then
        local tree = GameObject.Find("holy_tree3")
        if tree then holyLight = addLight(tree.transform.position + Vector3(0, 19, 0), Color(1, .035, .065, 1), 25, 0) end
    end
    if holyLight then
        holyLight.intensity = 1.35 * night * night
        holyLight.enabled = night > .01
    end
end

