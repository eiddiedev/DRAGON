local function updateHolyLight()
    -- Only the leaf surface emits light. No floating particles or red point lights.
    for _, name in ipairs({ "holy_canopy3", "holy_canopy4" }) do
        if not holyTried.found[name] then
            local go = GameObject.Find(name)
            if go then
                local rs = go:GetComponentsInChildren(typeof(UnityEngine.Renderer), true)
                if rs.Length > 0 then
                    for i = 0, rs.Length - 1 do
                        local m = rs[i].material
                        m:SetColor("_BaseColor", Color(1, 1, 1, 1))
                        m:SetTexture("_EmissionTex", m:GetTexture("_BaseTex") or m:GetTexture("_BaseMap") or m:GetTexture("_MainTex"))
                        m:SetColor("_EmissionColor", Color(.32, .42, .32, 1))
                        m:SetFloat("_EmissionPower", 0)
                        holyTried.materials[#holyTried.materials + 1] = m
                    end
                    holyTried.found[name] = true
                end
            end
        end
    end
    local night = math.max(0, math.min(1, 1 - blend))
    -- Fade with the existing day/night transition; exactly zero at full day.
    local glow = .45 * night * night
    for _, m in ipairs(holyTried.materials) do m:SetFloat("_EmissionPower", glow) end
end

