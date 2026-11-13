-- v27: bind only the two authored crowns. A late GLB/material replacement must
-- not leave our night colour on an abandoned renderer/material instance.
local holyTried = { groups = {}, materials = {}, bySource = {}, byOwned = {}, nextBind = 0, nextPaint = 0, binds = 0, errors = {} }
local holyLight = nil

function holyTried.materialFor(source)
    local rec = holyTried.byOwned[source] or holyTried.bySource[source]
    if rec then return rec end
    local m = UnityEngine.Material(source)
    m.name = source.name .. "_HolyNight_v27"
    rec = { source = source, material = m, base = {}, users = 0, renderers = {} }
    for _, key in ipairs({ "_BaseColor", "_Color" }) do
        if m:HasProperty(key) then rec.base[key] = m:GetColor(key) end
    end
    if m:HasProperty("_EmissionTex") then m:SetTexture("_EmissionTex", UnityEngine.Texture2D.whiteTexture) end
    if m:HasProperty("_EmissionMap") then m:SetTexture("_EmissionMap", UnityEngine.Texture2D.whiteTexture) end
    -- This is a leaf-surface emission, with no sprite/particle dot emitters.
    m:EnableKeyword("_EMISSION")
    holyTried.bySource[source], holyTried.byOwned[m] = rec, rec
    holyTried.materials[#holyTried.materials + 1] = rec
    return rec
end

function holyTried.releaseMaterial(rec)
    -- Find() intentionally omits inactive roots. They can still hold a clone;
    -- restore every surviving binding before disposing it, even when no longer
    -- in the active crown scan or when a renderer was detached by streaming.
    for renderer in pairs(rec.renderers) do
        pcall(function()
            local materials, changed = renderer.sharedMaterials, false
            for i = 0, materials.Length - 1 do
                if materials[i] == rec.material then materials[i] = rec.source; changed = true end
            end
            if changed then renderer.sharedMaterials = materials end
        end)
    end
    rec.renderers = {}
    UnityEngine.Object.Destroy(rec.material)
end

function holyTried.rebind(now)
    if now < holyTried.nextBind then return end
    holyTried.nextBind = now + 1
    holyTried.binds = holyTried.binds + 1
    for _, rec in ipairs(holyTried.materials) do rec.users = 0 end
    for _, name in ipairs({ "holy_canopy3", "holy_canopy4" }) do
        local group = holyTried.groups[name]
        if not group then group = {}; holyTried.groups[name] = group end
        local go = GameObject.Find(name)
        group.renderers = {}
        if go then
            local rs = go:GetComponentsInChildren(typeof(UnityEngine.Renderer), true)
            for i = 0, rs.Length - 1 do
                local renderer, changed = rs[i], false
                local materials = renderer.sharedMaterials
                for k = 0, materials.Length - 1 do
                    local source = materials[k]
                    if source then
                        local rec = holyTried.materialFor(source)
                        rec.users = rec.users + 1
                        rec.renderers[renderer] = true
                        if source ~= rec.material then materials[k] = rec.material; changed = true end
                    end
                end
                if changed then renderer.sharedMaterials = materials end
                group.renderers[#group.renderers + 1] = renderer
            end
            if rs.Length > 0 then
                if not group.light then group.light = addLight(rs[0].bounds.center, Color(1, .12, .24, 1), 16, 0) end
                group.light.transform.position = rs[0].bounds.center
            end
        end
        if group.light and #group.renderers == 0 then group.light.enabled = false end
    end
    -- Material replacement is uncommon, but never accumulate abandoned clones.
    for i = #holyTried.materials, 1, -1 do
        local rec = holyTried.materials[i]
        if rec.users == 0 then
            holyTried.bySource[rec.source], holyTried.byOwned[rec.material] = nil, nil
            holyTried.releaseMaterial(rec)
            table.remove(holyTried.materials, i)
        end
    end
    if not holyLight then
        local tree = GameObject.Find("holy_tree3")
        if tree then holyLight = addLight(tree.transform.position + Vector3(0, 19, 0), Color(1, .035, .065, 1), 25, 0) end
    end
end

local function updateHolyLight()
    local now = Time.realtimeSinceStartup
    if now < holyTried.nextPaint then return end
    holyTried.nextPaint = now + .1
    local ok, err = pcall(holyTried.rebind, now)
    if not ok then holyTried.errors.bind = tostring(err) end
    local night = math.max(0, math.min(1, 1 - blend))
    local glow = night * night * (2.6 + .12 * math.sin(Time.time * .65))
    holyTried.night, holyTried.glow = night, glow
    for _, rec in ipairs(holyTried.materials) do
        local painted, paintError = pcall(function()
            local m = rec.material
            for key, dayColor in pairs(rec.base) do
                m:SetColor(key, Color.Lerp(dayColor, Color(1, .12, .18, dayColor.a), night))
            end
            if m:HasProperty("_EmissionColor") then
                -- EnvLit_AI uses power separately; Standard/URP use HDR colour.
                local energy = m:HasProperty("_EmissionPower") and 1 or glow
                m:SetColor("_EmissionColor", Color(energy, .025 * energy, .055 * energy, 1))
            end
            if m:HasProperty("_EmissionPower") then m:SetFloat("_EmissionPower", glow) end
        end)
        if not painted then holyTried.errors.paint = tostring(paintError) end
    end
    for _, group in pairs(holyTried.groups) do
        if group.light then
            group.light.intensity = night * night * 1.8
            group.light.enabled = night > .01 and #group.renderers > 0
        end
    end
    if holyLight then
        holyLight.intensity = 1.35 * night * night
        holyLight.enabled = night > .01
    end
end

function holyTried.dispose()
    for _, group in pairs(holyTried.groups) do
        for _, renderer in ipairs(group.renderers or {}) do
            pcall(function()
                local materials, changed = renderer.sharedMaterials, false
                for i = 0, materials.Length - 1 do
                    local rec = holyTried.byOwned[materials[i]]
                    if rec then materials[i] = rec.source; changed = true end
                end
                if changed then renderer.sharedMaterials = materials end
            end)
        end
        if group.light then UnityEngine.Object.Destroy(group.light.gameObject) end
    end
    if holyLight then UnityEngine.Object.Destroy(holyLight.gameObject); holyLight = nil end
    for _, rec in ipairs(holyTried.materials) do holyTried.releaseMaterial(rec) end
    holyTried.groups, holyTried.materials, holyTried.bySource, holyTried.byOwned = {}, {}, {}, {}
    holyTried.nextBind, holyTried.nextPaint = 0, 0
end

function GetHolyGlowDiagnostics()
    local groups, materials = {}, {}
    for name, group in pairs(holyTried.groups) do
        local shaders = {}
        for _, renderer in ipairs(group.renderers or {}) do
            pcall(function()
                local materials = renderer.sharedMaterials
                for i = 0, materials.Length - 1 do
                    local m = materials[i]
                    shaders[#shaders + 1] = m and m.shader and m.shader.name or "missing"
                end
            end)
        end
        groups[name] = { renderers = #group.renderers, shaders = shaders, light = group.light and group.light.enabled or false }
    end
    for _, rec in ipairs(holyTried.materials) do
        local state = { name = rec.material.name, shader = rec.material.shader.name, users = rec.users }
        pcall(function()
            local m = rec.material
            if m:HasProperty("_EmissionPower") then state.emissionPower = m:GetFloat("_EmissionPower") end
            if m:HasProperty("_EmissionColor") then
                local c = m:GetColor("_EmissionColor"); state.emission = { r = c.r, g = c.g, b = c.b }
            end
        end)
        materials[#materials + 1] = state
    end
    return { build = "v27-live-holy-materials", binds = holyTried.binds, materials = #holyTried.materials,
        night = holyTried.night, glow = holyTried.glow, groups = groups, details = materials, errors = holyTried.errors }
end

