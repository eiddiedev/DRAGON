---@id a87ebe50-812d-4151-a056-727a118aecbd

local Input = UnityEngine.Input
local Vector3 = UnityEngine.Vector3
local Quaternion = UnityEngine.Quaternion
local Color = UnityEngine.Color
local RenderSettings = UnityEngine.RenderSettings
local Time = UnityEngine.Time

-- 测试用按键：1~7 传送，8 量高度，9 记录位置，0 切换昼夜。发布前改成 false
local DEBUG_TELEPORT = false

local function dbg(msg)
    if DEBUG_TELEPORT then
        CS.UnityEngine.Debug.LogError("[world_main] " .. msg)
    end
end
local function report(msg)
    CS.UnityEngine.Debug.LogError("[world_main] " .. msg)
end

---------------------------------------------------------------- 出生视角
local SPAWN_PITCH = -11
local SPAWN_YAW = 12        -- 略偏东：左边城堡，右边发光树
local RELEASE_DISTANCE = 4  -- 走开多远后回到普通视角
local RELEASE_SPEED = 12    -- 度/秒
local holdFrames = 30       -- 连续设置 30 帧，避免被相机自身的初始化覆盖
local defaultPitch, spawnPos
local camState = "waiting"

local function updateSpawnCamera(actor)
    if camState == "waiting" then
        defaultPitch = DouyinCameraService.GetPitch()
        spawnPos = actor.position
        camState = "holding"
    end
    if camState == "holding" then
        DouyinCameraService.SetPitch(SPAWN_PITCH)
        DouyinCameraService.SetYaw(SPAWN_YAW)
        holdFrames = holdFrames - 1
        if holdFrames <= 0 then
            camState = "looking"
        end
    elseif camState == "looking" then
        if Vector3.Distance(actor.position, spawnPos) > RELEASE_DISTANCE then
            camState = "releasing"
        end
    elseif camState == "releasing" then
        local pitch = DouyinCameraService.GetPitch()
        local step = RELEASE_SPEED * Time.deltaTime
        if math.abs(defaultPitch - pitch) <= step then
            DouyinCameraService.SetPitch(defaultPitch)
            camState = "done"
        elseif defaultPitch > pitch then
            DouyinCameraService.SetPitch(pitch + step)
        else
            DouyinCameraService.SetPitch(pitch - step)
        end
    end
end

---------------------------------------------------------------- 天空
local SWIRL_LAYERS = {
    { name = "sky_swirl_a", speed = -1.1 },
    { name = "sky_swirl_b", speed = -2.2 },
    { name = "sky_swirl_c", speed = -4.0 },
}
local nightObjects = {}   -- 夜里才显示的天空物体
local dayObjects = {}     -- 白天才显示的天空物体
local skyReady = false

local function setupSky()
    if skyReady then
        return
    end
    for _, layer in ipairs(SWIRL_LAYERS) do
        local go = UnityEngine.GameObject.Find(layer.name)
        if go == nil then
            return
        end
        layer.transform = go.transform
        table.insert(nightObjects, go)
    end
    local moon = UnityEngine.GameObject.Find("sky_moon2")
    local nightDome = UnityEngine.GameObject.Find("sky_dome2")
    local dayDome = UnityEngine.GameObject.Find("sky_day")
    if moon ~= nil then table.insert(nightObjects, moon) end
    if nightDome ~= nil then table.insert(nightObjects, nightDome) end
    if dayDome ~= nil then
        table.insert(dayObjects, dayDome)
        dayDome:SetActive(false)
    end
    skyReady = true
end

local function updateSky()
    setupSky()
    if not skyReady then
        return
    end
    local dt = Time.deltaTime
    for _, layer in ipairs(SWIRL_LAYERS) do
        layer.transform:Rotate(0, 0, layer.speed * dt)
    end
end

---------------------------------------------------------------- 昼夜：默认黑夜，自动慢慢循环，踩时之晷可以立刻切换
local NIGHT_SECONDS = 240
local DAY_SECONDS = 240
local FADE_SECONDS = 5
local DIALS = { { 121, 57 }, { 117.5, 162.5 } }  -- 出生点旁、城堡钟楼下
local DIAL_RADIUS = 2.2

local isDay = false
local blend = 0            -- 0 夜 1 昼
local clock = 0
local dialCooldown = 0
local sunLight = nil
local night = nil          -- 启动时记录的夜间参数
local envReady = false
local skyIsDay = false

local function lerpColor(a, b, t)
    return Color(a.r + (b.r - a.r) * t, a.g + (b.g - a.g) * t, a.b + (b.b - a.b) * t, 1)
end

local function setupEnv()
    if envReady then
        return
    end
    local ok, err = pcall(function()
        local lights = UnityEngine.Object.FindObjectsOfType(typeof(CS.UnityEngine.Light))
        dbg("lights=" .. tostring(lights.Length))
        for i = 0, lights.Length - 1 do
            local l = lights[i]
            dbg("light " .. l.gameObject.name .. " type=" .. tostring(l.type) .. " i=" .. tostring(l.intensity))
            if tostring(l.type):find("Directional") and sunLight == nil then
                sunLight = l
            end
        end
    end)
    if not ok then dbg("light probe failed: " .. tostring(err)) end
    dbg("SceneEnvironment=" .. tostring(rawget(_G, "DouyinSceneEnvironment")))
    night = {
        fog = RenderSettings.fogColor,
        fogEnd = RenderSettings.fogEndDistance,
        ambient = RenderSettings.ambientLight,
        ambientIntensity = RenderSettings.ambientIntensity,
        ambientMode = tostring(RenderSettings.ambientMode),
        lightColor = sunLight and sunLight.color or Color(.66, .76, 1, 1),
        lightIntensity = sunLight and sunLight.intensity or 1,
    }
    dbg("night fog=" .. tostring(night.fog) .. " ambient=" .. tostring(night.ambient) .. " ai=" .. tostring(night.ambientIntensity) .. " mode=" .. night.ambientMode .. " li=" .. tostring(night.lightIntensity))
    envReady = true
    applyCastle(0)
end


---------------------------------------------------------------- 城堡昼夜变色：夜里变成深色魔法城堡
local CASTLE_NAMES = { "gothic_main", "gothic_towers", "gothic_wall" }
local CASTLE_NIGHT = Color(.24, .21, .36, 1)
local CASTLE_DAY = Color(1, 1, 1, 1)
local castleMats = nil
local function setupCastle()
    castleMats = {}
    for _, nm in ipairs(CASTLE_NAMES) do
        local go = UnityEngine.GameObject.Find(nm)
        if go ~= nil then
            local rs = go:GetComponentsInChildren(typeof(CS.UnityEngine.Renderer))
            for i = 0, rs.Length - 1 do
                if rs[i].gameObject.name == "main" then
                    castleMats[#castleMats + 1] = rs[i].material
                end
            end
        end
    end
end
local function applyCastle(t)
    if castleMats == nil or #castleMats < 3 then setupCastle() end
    local c = lerpColor(CASTLE_NIGHT, CASTLE_DAY, t)
    for _, m in ipairs(castleMats) do
        m:SetColor("_BaseColor", c)
    end
end


---------------------------------------------------------------- 地形细节层：把重复贴图放进发光通道，近看才有草叶和岩石纹理
local DETAIL_DAY, DETAIL_NIGHT = .55, .18
local DETAIL_GRASS_SCALE, DETAIL_ROCK_SCALE = 12, 9
local detailMats = nil
local function setupDetail()
    local function texOf(name)
        local go = UnityEngine.GameObject.Find(name)
        if go == nil then return nil end
        local rs = go:GetComponentsInChildren(typeof(CS.UnityEngine.Renderer))
        local t = rs[0].material:GetTexture("_BaseTex")
        go:SetActive(false)
        return t
    end
    local grassTex, rockTex = texOf("detail_grass"), texOf("detail_rock")
    if grassTex == nil or rockTex == nil then
        return false
    end
    detailMats = {}
    for _, x in ipairs({ "000", "064", "128", "192" }) do
        for _, z in ipairs({ "000", "064", "128", "192" }) do
            local go = UnityEngine.GameObject.Find("t" .. x .. "_" .. z)
            if go then
                local rock = z == "192"
                local rs = go:GetComponentsInChildren(typeof(CS.UnityEngine.Renderer))
                for i = 0, rs.Length - 1 do
                    local m = rs[i].material
                    local tx = rock and rockTex or grassTex
                    m:SetTexture("_EmissionTex", tx)
                    local sc = rock and DETAIL_ROCK_SCALE or DETAIL_GRASS_SCALE
                    m:SetTextureScale("_EmissionTex", UnityEngine.Vector2(sc, sc))
                    m:SetColor("_EmissionColor", Color(1, 1, 1, 1))
                    m:EnableKeyword("_EMISSION")
                    detailMats[#detailMats + 1] = m
                end
            end
        end
    end
    dbg("detail mats " .. #detailMats)
    return true
end
local function applyDetail(t)
    if detailMats == nil then return end
    local p = DETAIL_NIGHT + (DETAIL_DAY - DETAIL_NIGHT) * t
    for _, m in ipairs(detailMats) do m:SetFloat("_EmissionPower", p) end
end

local DAY = {
    fog = Color(.72, .86, .98, 1),
    lightColor = Color(1, .95, .86, 1),
    lightIntensity = 1.5,
    ambientScale = 2.2,
    fogEnd = 4000,
}

local function applyEnv(t)
    if sunLight ~= nil then
        sunLight.color = lerpColor(night.lightColor, DAY.lightColor, t)
        sunLight.intensity = night.lightIntensity + (DAY.lightIntensity - night.lightIntensity) * t
    end
    RenderSettings.fogColor = lerpColor(night.fog, DAY.fog, t)
    RenderSettings.fogEndDistance = night.fogEnd + (DAY.fogEnd - night.fogEnd) * t
    RenderSettings.ambientIntensity = night.ambientIntensity * (1 + (DAY.ambientScale - 1) * t)
    local a = night.ambient
    local s = 1 + (DAY.ambientScale - 1) * t
    RenderSettings.ambientLight = Color(math.min(a.r * s, 1), math.min(a.g * s, 1), math.min(a.b * s, 1), 1)
    applyCastle(t)
    applyDetail(t)
    local wantDay = t > .5
    if wantDay ~= skyIsDay then
        skyIsDay = wantDay
        for _, go in ipairs(nightObjects) do go:SetActive(not wantDay) end
        for _, go in ipairs(dayObjects) do go:SetActive(wantDay) end
    end
end

local function setDay(day)
    isDay = day
    clock = 0
end

local function updateDayNight(actor)
    setupEnv()
    if not skyReady then
        return
    end
    clock = clock + Time.deltaTime
    if clock > (isDay and DAY_SECONDS or NIGHT_SECONDS) then
        setDay(not isDay)
    end
    dialCooldown = dialCooldown - Time.deltaTime
    if dialCooldown <= 0 then
        local p = actor.position
        for _, d in ipairs(DIALS) do
            if math.sqrt((p.x - d[1]) ^ 2 + (p.z - d[2]) ^ 2) < DIAL_RADIUS then
                dbg("dial triggered")
                setDay(not isDay)
                dialCooldown = 8  -- 站在上面不会反复切换
                break
            end
        end
    end
    local target = isDay and 1 or 0
    if blend ~= target then
        local step = Time.deltaTime / FADE_SECONDS
        if math.abs(target - blend) <= step then
            blend = target
        elseif target > blend then
            blend = blend + step
        else
            blend = blend - step
        end
        applyEnv(blend)
    end
end

---------------------------------------------------------------- 夜里的烟花和蝙蝠
local FIREWORK_NAMES = { "fw_gold_0", "fw_gold_1", "fw_pink_0", "fw_pink_1", "fw_blue_0", "fw_blue_1" }
local fireworks = {}
local bats = {}
local fxReady = false
local nextFirework = 3

local function setupFx()
    if fxReady then
        return
    end
    for _, name in ipairs(FIREWORK_NAMES) do
        local go = UnityEngine.GameObject.Find(name)
        if go ~= nil then
            go:SetActive(false)
            table.insert(fireworks, { go = go, t = -1 })
        end
    end
    for i = 0, 9 do
        local go = UnityEngine.GameObject.Find("bat_" .. i)
        if go ~= nil then
            table.insert(bats, {
                go = go,
                r = 22 + math.random() * 24,
                h = 88 + math.random() * 34,
                speed = (.22 + math.random() * .25) * (i % 2 == 0 and 1 or -1),
                phase = math.random() * 6.28,
                flap = 9 + math.random() * 5,
                size = 2.4 + math.random() * 1.6,
            })
        end
    end
    fxReady = true
end

local function updateFx()
    setupFx()
    local dt = Time.deltaTime
    local now = Time.time
    -- 蝙蝠只在夜里出现
    local showBats = blend < .5
    for _, b in ipairs(bats) do
        if b.visible ~= showBats then
            b.visible = showBats
            b.go:SetActive(showBats)
        end
        if showBats then
            local a = now * b.speed + b.phase
            local t = b.go.transform
            t.position = Vector3(127 + math.cos(a) * b.r, b.h + math.sin(a * 2.3) * 4, 176 + math.sin(a) * b.r)
            local face = -math.deg(a) + (b.speed > 0 and 0 or 180)
            t.rotation = Quaternion.Euler(Vector3(0, face, 0))
            t.localScale = Vector3(b.size, b.size * math.sin(now * b.flap), b.size)
        end
    end
    -- 烟花
    for _, f in ipairs(fireworks) do
        if f.t >= 0 then
            f.t = f.t + dt
            if f.t > 1.7 then
                f.t = -1
                f.go:SetActive(false)
            else
                local e = 1 - (1 - math.min(f.t / 1.1, 1)) ^ 3
                f.go.transform.localScale = Vector3.one * (2 + f.size * e)
            end
        end
    end
    if blend < .5 then
        nextFirework = nextFirework - dt
        if nextFirework <= 0 then
            nextFirework = 1.8 + math.random() * 3.2
            local n = #fireworks
            if n > 0 then
                local f = fireworks[math.random(1, n)]
                if f.t < 0 then
                    f.t = 0
                    f.size = 26 + math.random() * 22
                    f.go.transform.position = Vector3(60 + math.random() * 140, 118 + math.random() * 62, 225 + math.random() * 70)
                    f.go.transform.localScale = Vector3.one * 2
                    f.go:SetActive(true)
                end
            end
        end
    end
end

---------------------------------------------------------------- 竞技场入口
local ARENA_GATE = Vector3(125, 42, 134.5)
local ARENA_IN = { 127, 33.5, 163, 0 }
local ARENA_EXIT = Vector3(127, 33, 159.8)
local ARENA_OUT = { 125, 42.5, 130, 180 }
local PORTAL_RADIUS = 2.6
local portalCooldown = 0

local function flatDistance(a, b)
    return math.sqrt((a.x - b.x) ^ 2 + (a.z - b.z) ^ 2)
end

local function moveTo(actor, t)
    actor:Teleport(Vector3(t[1], t[2], t[3]), Quaternion.Euler(Vector3(0, t[4], 0)))
    DouyinCameraService.SetYaw(t[4])
    portalCooldown = 2
end

local function updatePortals(actor)
    if portalCooldown > 0 then
        portalCooldown = portalCooldown - Time.deltaTime
        return
    end
    local p = actor.position
    if p.y > 38 and flatDistance(p, ARENA_GATE) < PORTAL_RADIUS then
        moveTo(actor, ARENA_IN)
    elseif p.y < 38 and flatDistance(p, ARENA_EXIT) < PORTAL_RADIUS then
        moveTo(actor, ARENA_OUT)
    end
end

---------------------------------------------------------------- 测试键
local TELEPORTS = {
    ["1"] = { 162, 43, 93, 0 },      -- 桥南头，朝北
    ["2"] = { 150, 53, 151, 90 },    -- 盘山路第二段东头
    ["3"] = { 127, 74, 153, 0 },     -- 山顶南门外，朝北
    ["4"] = { 171, 41, 136, 0 },     -- 药水铺门前
    ["5"] = { 165, 42, 130, 300 },   -- 桥北头，上山路起点
    ["6"] = { 127, 73, 168, 0 },     -- 庭院，正对大门
    ["7"] = { 127, 34, 165, 0 },     -- 竞技场里面
    ["o"] = { 121, 41, 54.5, 0 },    -- 出生点旁的时之晷南边，往前走就踩上
    ["h"] = { 150, 42, 62, 310 },    -- 花海中央
    ["j"] = { 62, 46, 53, 0 },       -- 营地南边
    ["k"] = { 86, 49, 90, 0 },       -- 蘑菇林南边
    ["l"] = { 48, 54, 133, 0 },      -- 祭坛南边
    ["u"] = { 96, 43, 22, 0 },       -- 飞龙驿站南边
    ["y"] = { 120, 52, 110, 0 },     -- 河南岸，望城堡
    ["t"] = { 140, 44, 140, 330 },   -- 山脚
}


-- 自动走山路（测试用）：按 p 回到桥北头，按住 W 就会沿路走
local WALK = {{161.26,128.89},{158,134},{150.74,137.56},{140.44,140.15},{128,142},{115.56,143.7},{105.04,147.07},{98,152},{97.93,156.85},{103.56,157.11},{114,153},{127.41,149.85},{140.04,149.04},{150,151},{154.78,155.96},{153.15,158.76},{146,158.5},{137.74,156.72},{131.04,155.96},{127,156.5},{127,160},{127,165},{127,170}}
local walkI, walkLog, walkLast = nil, 0, nil
local function updateWalk(actor)
    if Input.GetKeyDown("p") then
        actor:Teleport(Vector3(162, 41.5, 127), Quaternion.Euler(Vector3(0, 0, 0)))
        walkI = 1
        dbg("walk start")
    end
    if walkI == nil then return end
    local p = actor.position
    local t = WALK[walkI]
    local dx, dz = t[1] - p.x, t[2] - p.z
    if math.sqrt(dx * dx + dz * dz) < 1.4 then
        walkI = walkI + 1
        dbg(string.format("walk reached #%d pos=%.1f,%.1f,%.1f", walkI - 1, p.x, p.y, p.z))
        if walkI > #WALK then
            dbg("walk done")
            walkI = nil
        end
        return
    end
    DouyinCameraService.SetYaw(math.deg(math.atan(dx, dz)))
    walkLog = walkLog + Time.deltaTime
    if walkLog > 2 then
        walkLog = 0
        dbg(string.format("walk #%d pos=%.1f,%.1f,%.1f", walkI, p.x, p.y, p.z))
    end
end


local function probeTex()
    for _, nm in ipairs({ "t128_000", "t128_192", "grass_x", "pines_0_0", "gr_5", "altar" }) do
        local go = UnityEngine.GameObject.Find(nm)
        if go then
            local rs = go:GetComponentsInChildren(typeof(CS.UnityEngine.Renderer))
            for i = 0, rs.Length - 1 do
                local m = rs[i].material
                local t = m:GetTexture("_BaseTex")
                local n = m:GetTexture("_Normalmap")
                local mf = rs[i].gameObject:GetComponent(typeof(CS.UnityEngine.MeshFilter))
                dbg(string.format("%s shader=%s base=%s %sx%s fmt=%s filt=%s aniso=%s mip=%s norm=%s %sx%s nscale=%s kw=%s verts=%s", nm, m.shader.name, tostring(t and t.name), tostring(t and t.width), tostring(t and t.height), tostring(t and t.format), tostring(t and t.filterMode), tostring(t and t.anisoLevel), tostring(t and t.mipmapCount), tostring(n and n.name), tostring(n and n.width), tostring(n and n.height), tostring(m:GetFloat("_NormalScale")), tostring(m.shaderKeywords.Length), tostring(mf and mf.sharedMesh.vertexCount)))
                local kws = {}
                for k = 0, m.shaderKeywords.Length - 1 do kws[#kws + 1] = m.shaderKeywords[k] end
                dbg("  kw " .. table.concat(kws, " ") .. " cut=" .. tostring(m:GetFloat("_AlphaCutoff")) .. " rq=" .. tostring(m.renderQueue) .. " tri=" .. tostring(m:GetFloat("_UseTriplanarSample")))
            end
        else
            dbg(nm .. " not found")
        end
    end
    dbg("quality master=" .. tostring(UnityEngine.QualitySettings.globalTextureMipmapLimit) .. " masterTex=" .. tostring(UnityEngine.QualitySettings.masterTextureLimit))
end


local fpsT, fpsN = 0, 0
local function updateDebug(actor)
    fpsT, fpsN = fpsT + Time.unscaledDeltaTime, fpsN + 1
    if fpsT > 4 then
        dbg(string.format("fps=%.1f pos=%.0f,%.0f", fpsN / fpsT, actor.position.x, actor.position.z))
        fpsT, fpsN = 0, 0
    end
    if Input.GetKeyDown("b") then
        actor:Teleport(Vector3(46, 96, 100), Quaternion.Euler(Vector3(0, 0, 0)))
        DouyinCameraService.SetYaw(0)
    end
    if Input.GetKeyDown("v") then
        runeTest = (runeTest or 0) % 3 + 1
        local T_ = ({ { 48, 141 }, { 55.8, 154.5 }, { 40.2, 154.5 } })[runeTest]
        actor:Teleport(Vector3(T_[1], 54, T_[2]))
    end
    if Input.GetKeyDown("x") then
        local ok, err = pcall(probeTex)
        if not ok then dbg("probeTex failed " .. tostring(err)) end
    end
    if Input.GetKeyDown("[") or Input.GetKeyDown("]") then
        local k = Input.GetKeyDown("]") and 1.3 or (1 / 1.3)
        DETAIL_DAY, DETAIL_NIGHT = DETAIL_DAY * k, DETAIL_NIGHT * k
        applyDetail(blend)
        dbg("detail power day=" .. DETAIL_DAY)
    end
    if Input.GetKeyDown("-") or Input.GetKeyDown("=") then
        local k = Input.GetKeyDown("=") and 1.4 or (1 / 1.4)
        DETAIL_GRASS_SCALE, DETAIL_ROCK_SCALE = DETAIL_GRASS_SCALE * k, DETAIL_ROCK_SCALE * k
        for _, m in ipairs(detailMats or {}) do
            local s_ = m:GetTextureScale("_EmissionTex").x
            m:SetTextureScale("_EmissionTex", UnityEngine.Vector2(s_ * k, s_ * k))
        end
        dbg("detail scale grass=" .. DETAIL_GRASS_SCALE)
    end
    updateWalk(actor)
    for key, t in pairs(TELEPORTS) do
        if Input.GetKeyDown(key) then
            actor:Teleport(Vector3(t[1], t[2], t[3]), Quaternion.Euler(Vector3(0, t[4], 0)))
            DouyinCameraService.SetYaw(t[4])
        end
    end
    if Input.GetKeyDown("0") then
        setDay(not isDay)
        dbg("toggle day=" .. tostring(isDay))
    end
    if Input.GetKeyDown("8") then
        local p = actor.position
        local list = UnityEngine.Object.FindObjectsOfType(typeof(CS.UnityEngine.MeshRenderer))
        dbg("renderers=" .. list.Length)
        local seen = {}
        for i = 0, list.Length - 1 do
            local r = list[i]
            local c = r.bounds.center
            local e = r.bounds.extents
            local d = math.sqrt((c.x - p.x) ^ 2 + (c.z - p.z) ^ 2)
            local name = r.gameObject.name
            local parent = r.transform.parent and r.transform.parent.gameObject.name or "-"
            if d < 60 and e.x + e.z < 90 then
                dbg(string.format("near %s < %s d=%.0f c=%.0f,%.0f,%.0f e=%.1f,%.1f,%.1f mat=%s", name, parent, d, c.x, c.y, c.z, e.x, e.y, e.z, tostring(r.sharedMaterial and r.sharedMaterial.name)))
            end
        end
    end
    if Input.GetKeyDown("9") then
        local p = actor.position
        dbg(string.format("pos=%.1f,%.1f,%.1f pitch=%.1f yaw=%.1f", p.x, p.y, p.z, DouyinCameraService.GetPitch(), DouyinCameraService.GetYaw()))
    end
end


---------------------------------------------------------------- 会晃的草：离玩家近的才显示，更近的才晃
local GameObject = UnityEngine.GameObject
local GRASS_SHOW = 48
local GRASS_SWAY = 26
local WIND_YAW = 35
local grass = {}
local grassNext = 0
local grassMiss = 0
local grassCursor = 1
local swayList = {}
local swayCursor = 1
local LUT_N = 40
local LUT_MAX = .42
local lutParentRot, lutParentScale, lutChild = nil, nil, nil

local function buildLut()
    lutParentRot, lutParentScale, lutChild = {}, {}, {}
    local yaw = Quaternion.Euler(Vector3(0, WIND_YAW, 0))
    local yawInv = Quaternion.Inverse(yaw)
    for i = 0, LUT_N do
        local k = -LUT_MAX + 2 * LUT_MAX * i / LUT_N
        local s1 = (k + math.sqrt(k * k + 4)) / 2
        if k < 0 then s1 = (-k + math.sqrt(k * k + 4)) / 2 end
        local tu = .5 * math.atan(2, k)
        local tv = .5 * math.atan(2, -k)
        -- 剪切 = 旋转(tu) · 缩放(σ1, σ2) · 旋转(tv)⁻¹，σ1 始终对应靠近 tu 的轴
        local Rz = Quaternion.Euler(Vector3(0, 0, math.deg(tu)))
        local Rv = Quaternion.Euler(Vector3(0, 0, -math.deg(tv)))
        lutParentRot[i] = yaw * Rz
        lutParentScale[i] = Vector3(s1, 1 / s1, 1)
        lutChild[i] = Rv * yawInv
    end
end

local function setupGrassStep()
    if grassMiss > 30 then return end
    for _ = 1, 10 do
        local go = GameObject.Find("gr_" .. grassNext)
        if go == nil then
            grassMiss = grassMiss + 1
        else
            grassMiss = 0
            local t = go.transform
            local pivot = GameObject("gp")
            local pt = pivot.transform
            local pos = t.position
            pt.position = pos
            local orig = t.rotation
            t:SetParent(pt, true)
            grass[#grass + 1] = { pivot = pivot, pt = pt, t = t, x = pos.x, z = pos.z, orig = orig, on = true, sway = false, ph = (pos.x * .31 + pos.z * .17) }
            pivot:SetActive(false)
            grass[#grass].on = false
        end
        grassNext = grassNext + 1
    end
end

local function updateGrass(actor)
    setupGrassStep()
    local n = #grass
    if n == 0 then return end
    local p = actor.position
    -- 每帧检查一部分：显示范围和晃动范围
    for _ = 1, 24 do
        local g = grass[grassCursor]
        grassCursor = grassCursor % n + 1
        local dx, dz = g.x - p.x, g.z - p.z
        local d2 = dx * dx + dz * dz
        local show = d2 < GRASS_SHOW * GRASS_SHOW
        if show ~= g.on then
            g.on = show
            g.pivot:SetActive(show)
        end
        local sway = d2 < GRASS_SWAY * GRASS_SWAY
        if sway ~= g.sway then
            g.sway = sway
            if sway then swayList[#swayList + 1] = g end
        end
    end
    -- 晃动：一半一半轮流更新，波从西南往东北推
    local m = #swayList
    if m == 0 then return end
    local T = Time.time
    for _ = 1, math.max(1, math.ceil(m / 2)) do
        if swayCursor > m then swayCursor = 1 end
        local g = swayList[swayCursor]
        if not g.sway then
            swayList[swayCursor] = swayList[m]
            swayList[m] = nil
            m = m - 1
            if m == 0 then return end
        else
            swayCursor = swayCursor + 1
            local wave = math.sin(T * .9 + g.x * .11 + g.z * .07)
            local k = .07 + .13 * math.sin(T * 1.9 + g.ph) + .05 * math.sin(T * 3.3 + g.ph * 1.7) + .16 * math.max(0, wave)
            local i = math.floor((k + LUT_MAX) / (2 * LUT_MAX) * LUT_N + .5)
            if i < 0 then i = 0 elseif i > LUT_N then i = LUT_N end
            g.pt.rotation = lutParentRot[i]
            g.pt.localScale = lutParentScale[i]
            g.t.localRotation = lutChild[i] * g.orig
        end
    end
end

local DRAGON_YAW, MOUNT_YAW, MOUNT_SEAT = -90, -90, 4.4
local CAMERA_DIST = 5
---------------------------------------------------------------- 森林互动点
local SITE = {
    camp = { 62, 62 },
    mush = { 86, 98 },
    altar = { 48, 150 },
    perch = { 96, 30 },
}
local function toast(msg)
    pcall(function() DouyinUtility.Toast(msg) end)
end
local function dist2d(p, x, z)
    return math.sqrt((p.x - x) ^ 2 + (p.z - z) ^ 2)
end
local function matsOf(go)
    local out = {}
    if go == nil then return out end
    local rs = go:GetComponentsInChildren(typeof(CS.UnityEngine.Renderer))
    for i = 0, rs.Length - 1 do out[#out + 1] = rs[i].material end
    return out
end
local function addLight(parent, color, range, intensity)
    local ok, l = pcall(function()
        local go = GameObject("site_light")
        go.transform.position = parent
        local li = go:AddComponent(typeof(CS.UnityEngine.Light))
        li.type = CS.UnityEngine.LightType.Point
        li.color = color
        li.range = range
        li.intensity = intensity
        li.shadows = CS.UnityEngine.LightShadows.None
        return li
    end)
    if ok then return l end
    dbg("light failed " .. tostring(l))
    return nil
end

---- 篝火：走近时火势变旺
local fire, sparks, fireBase, sparkBase, fireLight
local fireBoost = 0
local fireSaid = false
local fireReady = false
local function setupFire()
    fireReady = true
    local f = GameObject.Find("fire_fx")
    local s = GameObject.Find("spark_fx")
    if f then
        fire = f.transform
        fireBase = fire.localScale
        fireLight = addLight(fire.position + Vector3(0, 1.4, 0), Color(1, .55, .2, 1), 22, 3)
    end
    if s then
        sparks = s.transform
        sparkBase = sparks.localScale
    end
end
local function updateFire(p)
    if not fireReady then setupFire() end
    if not fire then return end
    local near = dist2d(p, SITE.camp[1], SITE.camp[2]) < 7
    local tgt = near and 1 or 0
    fireBoost = fireBoost + (tgt - fireBoost) * math.min(1, Time.deltaTime * 2)
    if near and not fireSaid then
        fireSaid = true
        toast("冒险者的营地：篝火为你燃得更旺了")
    elseif not near and fireBoost < .05 then
        fireSaid = false
    end
    local T = Time.time
    local k = (1 + .07 * math.sin(T * 11) + .05 * math.sin(T * 17.3)) * (1 + fireBoost * .45)
    fire.localScale = fireBase * k
    fire.rotation = Quaternion.Euler(Vector3(0, T * 40, 0))
    if fireLight then fireLight.intensity = (2.6 + .7 * math.sin(T * 13) + .4 * math.sin(T * 23)) * (1 + fireBoost) end
    if sparks then
        sparks.rotation = Quaternion.Euler(Vector3(0, T * 26, 0))
        local c = (T * .35) % 1
        sparks.localScale = sparkBase * (1 + c * .5 + fireBoost * .6)
    end
end

---- 蘑菇林：踩中间的光圈被弹上天
local MUSH_R = 2.6
local bounceT = nil
local bounceY0 = 0
local mushMats = nil
local function setupMush()
    mushMats = {}
    for i = 0, 5 do
        local name = i == 0 and "mush" or ("mush_" .. i)
        for _, m in ipairs(matsOf(GameObject.Find(name))) do mushMats[#mushMats + 1] = m end
    end
end
local function updateMush(actor, p)
    if mushMats == nil then setupMush() end
    local T = Time.time
    -- 夜里蘑菇呼吸发光
    if #mushMats > 0 then
        local g = (.25 + .2 * math.sin(T * 1.6)) * (1 - blend)
        local c = Color(.25 * g, .75 * g, 1 * g, 1)
        for _, m in ipairs(mushMats) do
            m:SetColor("_EmissionColor", c)
            m:SetFloat("_EmissionPower", 1)
        end
    end
    if bounceT == nil then
        if dist2d(p, SITE.mush[1], SITE.mush[2]) < MUSH_R and p.y < 52 then
            bounceT = 0
            bounceY0 = p.y
            dbg("bounce")
            toast("蘑菇把你弹上了天！")
        end
        return
    end
    bounceT = bounceT + Time.deltaTime
    local V, G_ = 15, 12
    local y = bounceY0 + V * bounceT - .5 * G_ * bounceT * bounceT
    if bounceT > V / G_ then
        bounceT = nil  -- 过了最高点交给重力
        return
    end
    actor:Teleport(Vector3(p.x, y, p.z))
end

---- 唤龙祭坛：点亮三块龙纹立石，巨龙回应
local RUNES = { { 48, 138 }, { 58.39, 156 }, { 37.61, 156 } }
local runeLit = { false, false, false }
local runeGo, beamGo = nil, nil
local litCount = 0
local summonT = nil
local altarReset = 0
local function setupAltar()
    runeGo, beamGo = {}, {}
    for i = 1, 3 do
        runeGo[i] = GameObject.Find("rune_" .. (i - 1))
        beamGo[i] = GameObject.Find("beam_" .. (i - 1))
        if beamGo[i] then beamGo[i]:SetActive(false) end
    end
    beamGo[4] = GameObject.Find("beam_3")
    if beamGo[4] then beamGo[4]:SetActive(false) end
    dbg("altar setup beams=" .. tostring(beamGo[1] ~= nil) .. "," .. tostring(beamGo[2] ~= nil) .. "," .. tostring(beamGo[3] ~= nil) .. "," .. tostring(beamGo[4] ~= nil) .. " runes=" .. tostring(runeGo[1] ~= nil))
    if beamGo[1] then
        local t = beamGo[1].transform
        dbg("beam0 pos=" .. tostring(t.position) .. " scale=" .. tostring(t.localScale))
    end
end
local function resetAltar()
    litCount = 0
    for i = 1, 3 do
        runeLit[i] = false
        if beamGo[i] then beamGo[i]:SetActive(false) end
    end
    if beamGo[4] then beamGo[4]:SetActive(false) end
end
local function updateAltar(p)
    if runeGo == nil then setupAltar() end
    if summonT ~= nil then return end
    if altarReset > 0 then
        altarReset = altarReset - Time.deltaTime
        if altarReset <= 0 then resetAltar() end
        return
    end
    for i = 1, 3 do
        if not runeLit[i] and dist2d(p, RUNES[i][1], RUNES[i][2]) < 4.3 then
            runeLit[i] = true
            litCount = litCount + 1
            dbg("rune lit " .. i .. " count=" .. litCount)
            if beamGo[i] then beamGo[i]:SetActive(true) end
            if litCount < 3 then
                toast("龙纹立石被唤醒 " .. litCount .. "/3")
            else
                if beamGo[4] then beamGo[4]:SetActive(true) end
                toast("巨龙回应了你的呼唤！抬头看！")
                summonT = 0
                altarReset = 75
                dbg("dragon summoned")
            end
        end
    end
end

---- 巨龙：白天绕城堡盘旋；被祭坛召唤时低空飞过祭坛
local flyDragon, flyOk = nil, false
local function setupDragon()
    local d = GameObject.Find("dragon_fly")
    flyOk = true
    if d then flyDragon = d end
end
local function placeDragon(x, y, z, dirx, dirz, bank)
    local t = flyDragon.transform
    t.position = Vector3(x, y, z)
    local yaw = math.deg(math.atan(dirx, dirz))
    t.rotation = Quaternion.Euler(Vector3(0, yaw + DRAGON_YAW, bank))
end
local function updateDragon()
    if not flyOk then setupDragon() end
    if not flyDragon then return end
    if summonT ~= nil then
        summonT = summonT + Time.deltaTime
        local S = summonT / 28
        if S >= 1 then
            summonT = nil
        else
            flyDragon:SetActive(true)
            -- 从北面俯冲过来，绕祭坛一圈半，再拉升飞走
            local cx, cz = 48, 150
            local ang = -1.2 + S * 9.4
            local r = 40 + 110 * (2 * S - 1) ^ 4
            local y = 72 + 80 * (2 * S - 1) ^ 2
            local x, z = cx + math.cos(ang) * r, cz + math.sin(ang) * r
            placeDragon(x, y, z, -math.sin(ang), math.cos(ang), -18)
            return
        end
    end
    local show = blend > .5
    if show ~= flyDragon.activeSelf then flyDragon:SetActive(show) end
    if show then
        local a = Time.time * .16
        local x, z = 127 + math.cos(a) * 82, 176 + math.sin(a) * 82
        local y = 118 + 10 * math.sin(a * 2.3)
        placeDragon(x, y, z, -math.sin(a), math.cos(a), -14)
    end
end

---- 飞龙驿站：靠近坐骑龙就起飞，环游全图后落回原处
local FLIGHT = {
    { 96, 44, 30 }, { 112, 60, 38 }, { 150, 86, 62 }, { 175, 74, 104 }, { 196, 84, 140 }, { 180, 104, 186 },
    { 130, 126, 216 }, { 82, 108, 196 }, { 92, 94, 150 }, { 120, 98, 126 }, { 86, 78, 96 }, { 44, 84, 128 }, { 28, 84, 80 }, { 62, 64, 44 }, { 96, 46, 30 },
}
local FLIGHT_SPEED = 16
local rideT, rideS = nil, 0
local rideCool = 0
local mountGo, mountHome, mountHomeRot = nil, nil, nil
local function catmull(a, b, c, d, t)
    local t2, t3 = t * t, t * t * t
    return .5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (3 * b - a - 3 * c + d) * t3)
end
local function flightAt(s)
    local n = #FLIGHT
    local f = s * (n - 1)
    local i = math.floor(f)
    if i >= n - 1 then i = n - 2 end
    local t = f - i
    local p0, p1, p2, p3 = FLIGHT[math.max(i, 1)], FLIGHT[i + 1], FLIGHT[i + 2], FLIGHT[math.min(i + 3, n)]
    return catmull(p0[1], p1[1], p2[1], p3[1], t), catmull(p0[2], p1[2], p2[2], p3[2], t), catmull(p0[3], p1[3], p2[3], p3[3], t)
end
local function updateMount(actor, p)
    if mountGo == nil then
        mountGo = GameObject.Find("dragon_mount") or false
        if mountGo then
            mountHome = mountGo.transform.position
            mountHomeRot = mountGo.transform.rotation
        end
    end
    if not mountGo then return end
    local T = mountGo.transform
    if rideT == nil then
        T.position = mountHome + Vector3(0, .25 * math.sin(Time.time * 1.3), 0)
        rideCool = rideCool - Time.deltaTime
        if rideCool <= 0 and dist2d(p, SITE.perch[1], SITE.perch[2]) < 3.6 then
            rideT = 0
            rideS = 0
            actor:Immobilize(true)
            DouyinCameraService.SetDistance(11)
            toast("抓紧了！飞龙带你环游龙眠之境")
        end
        return
    end
    rideT = rideT + Time.deltaTime
    rideS = rideS + Time.deltaTime * FLIGHT_SPEED / 620
    if rideS >= 1 then
        rideT = nil
        rideCool = 12
        T.position, T.rotation = mountHome, mountHomeRot
        actor:Immobilize(false)
        DouyinCameraService.SetDistance(CAMERA_DIST)
        actor:Teleport(Vector3(SITE.perch[1] + 4.5, mountHome.y + 1, SITE.perch[2]))
        toast("平安落地")
        return
    end
    local x, y, z = flightAt(rideS)
    local x2, y2, z2 = flightAt(math.min(rideS + .004, .9999))
    local dx, dz = x2 - x, z2 - z
    local yaw = math.deg(math.atan(dx, dz))
    T.position = Vector3(x, y, z)
    T.rotation = Quaternion.Euler(Vector3(0, yaw + MOUNT_YAW, 0))
    actor:Teleport(Vector3(x, y + MOUNT_SEAT, z), Quaternion.Euler(Vector3(0, yaw, 0)))
    DouyinCameraService.SetYaw(yaw)
    DouyinCameraService.SetPitch(12)
end

local holyLight, hallLight = nil, nil
local holyTried = false
local function updateHolyLight()
    if not holyTried then
        holyTried = true
        holyLight = addLight(Vector3(153, 60, 71), Color(1, .86, .52, 1), 42, 3.2)
        hallLight = addLight(Vector3(127, 79, 180), Color(1, .72, .4, 1), 26, 2.6)
    end
    if holyLight then holyLight.intensity = (3.2 + .4 * math.sin(Time.time * .9)) * (1 - blend * .85) end
    if hallLight then hallLight.intensity = 2.6 - blend * 1.2 end
end

local function updateSites(actor)
    local p = actor.position
    updateFire(p)
    updateMush(actor, p)
    updateAltar(p)
    updateDragon()
    updateMount(actor, p)
    updateHolyLight()
end

local castleRetry = 0
function Update()
    updateSky()
    if envReady and (castleMats == nil or #castleMats < 3) then
        castleRetry = castleRetry + Time.deltaTime
        if castleRetry > 1 then
            castleRetry = 0
            applyCastle(blend)
        end
    end
    if skyReady then
        updateFx()
    end
    if not DouyinNetService.isNetworkSettled then
        return
    end
    local actor = DouyinActorService.GetLocalActor()
    if actor == nil then
        return
    end
    if camState ~= "done" then
        updateSpawnCamera(actor)
    end
    updateDayNight(actor)
    updatePortals(actor)
    if detailMats == nil then
        detailRetry = (detailRetry or 0) - Time.deltaTime
        if detailRetry <= 0 then
            detailRetry = 1
            local okd, errd = pcall(setupDetail)
            if okd and errd then applyDetail(blend) elseif not okd then report("detail failed " .. tostring(errd)) end
        end
    end
    if lutParentRot == nil then
        buildLut()
        actor.speed = 4.5
    end
    local oks, errs = pcall(updateSites, actor)
    if not oks and not sitesFailed then
        sitesFailed = true
        report("sites failed " .. tostring(errs))
    end
    local okg, errg = pcall(updateGrass, actor)
    if not okg and not grassFailed then
        grassFailed = true
        report("grass failed " .. tostring(errg))
    end
    if DEBUG_TELEPORT then
        updateDebug(actor)
    end
end

return {}
