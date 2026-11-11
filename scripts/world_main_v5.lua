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
    local lampGlow = UnityEngine.GameObject.Find("lamp_glow")   -- 路灯的灯罩光，白天关掉
    if lampGlow ~= nil then table.insert(nightObjects, lampGlow) end
    if nightDome ~= nil then table.insert(nightObjects, nightDome) end
    if dayDome ~= nil then
        table.insert(dayObjects, dayDome)
        dayDome:SetActive(false)
    end
    for _, layer in ipairs(SWIRL_LAYERS) do   -- 夜空漩涡加亮
        pcall(function()
            local rs = layer.transform.gameObject:GetComponentsInChildren(typeof(UnityEngine.Renderer))
            for i = 0, rs.Length - 1 do
                local m = rs[i].material
                local tx = m:GetTexture("_BaseTex")
                if tx then m:SetTexture("_EmissionTex", tx) end
                m:SetColor("_EmissionColor", Color(1, 1, 1, 1))
                m:SetFloat("_EmissionPower", 1.6)
            end
        end)
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
local FADE_SECONDS = 12
local DIALS = { { 121, 57 }, { 117.5, 162.5 } }  -- 出生点旁、城堡钟楼下
local DIAL_RADIUS = 2.2

local isDay = false
local blend = 0            -- 0 夜 1 昼
local clock = 0
local dialCooldown = 0
local sunLight = nil
local night = nil          -- 启动时记录的夜间参数
local envReady = false
local applyCastle
local dialInside = false

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
local castleGlowMats = {}
local function setupCastle()
    castleMats = {}
    castleGlowMats = {}
    for _, nm in ipairs(CASTLE_NAMES) do
        local go = UnityEngine.GameObject.Find(nm)
        if go ~= nil then
            local rs = go:GetComponentsInChildren(typeof(CS.UnityEngine.Renderer))
            for i = 0, rs.Length - 1 do
                if rs[i].gameObject.name == "main" then
                    castleMats[#castleMats + 1] = rs[i].material
                elseif rs[i].gameObject.name == "glow" then
                    local m=rs[i].material
                    castleGlowMats[#castleGlowMats+1]={m=m,p=m:GetFloat("_EmissionPower"),c=m:GetColor("_BaseColor")}
                end
            end
        end
    end
end
applyCastle = function(t)
    if castleMats == nil or #castleMats < 3 then setupCastle() end
    local c = lerpColor(CASTLE_NIGHT, CASTLE_DAY, t)
    for _, m in ipairs(castleMats) do
        m:SetColor("_BaseColor", c)
    end
    for _,v in ipairs(castleGlowMats) do
        local k=1-.9*t
        v.m:SetFloat("_EmissionPower",v.p*k)
        v.m:SetColor("_BaseColor",Color(v.c.r*k,v.c.g*k,v.c.b*k,1))
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
    lightColor = Color(1, .93, .82, 1),
    lightIntensity = 1.15,   -- 白天光照收一点、环境光少提一点，草地显得更深
    ambientScale = 1.4,
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
    if SWIRL_LAYERS.fade then SWIRL_LAYERS.fade(t) end
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
    local entered = false
    local p = actor.position
    for _, d in ipairs(DIALS) do
        if (p.x-d[1])^2+(p.z-d[2])^2 < DIAL_RADIUS^2 then entered=true;break end
    end
    if entered and not dialInside and dialCooldown<=0 then
        setDay(not isDay);dialCooldown=1
    end
    dialInside=entered
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
        applyEnv(blend*blend*(3-2*blend))
    end
end

---------------------------------------------------------------- 骨骼动画
-- 蒙皮模型内部有一个同名的网格子节点，Find 可能先找到它，这里统一取根节点
local function skinnedRoot(go)
    if go == nil then return nil end
    local p = go.transform.parent
    if p ~= nil and p.name == "rig" and p.parent ~= nil then
        return p.parent.gameObject
    end
    return go
end
local animPending = {}
local function tryAnim(job)
    local an = job.go:GetComponent(typeof(UnityEngine.Animation))
    if an == nil then return false end
    local ok, err = pcall(function()
        an.wrapMode = UnityEngine.WrapMode.Loop
        local c = an:GetClip(job.clip)
        c.wrapMode = UnityEngine.WrapMode.Loop
        local st = an:get_Item(job.clip)
        st.wrapMode = UnityEngine.WrapMode.Loop
        if job.speed then st.speed = job.speed end
        if job.cull then an.cullingType = UnityEngine.AnimationCullingType.AlwaysAnimate end
        an:Play(job.clip)
    end)
    if not ok then report("anim " .. tostring(job.go.name) .. " " .. job.clip .. " " .. tostring(err)) end
    if job.done then job.done(an) end
    return true
end
local function loopAnim(go, clip, speed, cull, done)
    local job = { go = go, clip = clip, speed = speed, cull = cull, done = done }
    if not tryAnim(job) then animPending[#animPending + 1] = job end
end
local animRetry = 0
local function updateAnimPending()
    if #animPending == 0 then return end
    animRetry = animRetry - Time.deltaTime
    if animRetry > 0 then return end
    animRetry = .3
    for i = #animPending, 1, -1 do
        if tryAnim(animPending[i]) then table.remove(animPending, i) end
    end
end
local function fadeAnim(go, an, clip)
    local ok, err = pcall(function()
        local st = an:get_Item(clip)
        st.wrapMode = UnityEngine.WrapMode.Loop
        an:CrossFade(clip, .3)
    end)
    if not ok then report("fade " .. clip .. " " .. tostring(err)) end
end

---------------------------------------------------------------- 夜里的烟花和蝙蝠
local fireworks = {}
local bats = {}
local fxReady = false

local function setupFx()
    if fxReady then
        return
    end
    for i = 0, 5 do
        local go = skinnedRoot(UnityEngine.GameObject.Find("fw_" .. i))
        if go ~= nil then
            table.insert(fireworks, { go = go, on = true })
            loopAnim(go, "idle", nil, true, function(an)
                pcall(function()
                    an:get_Item("idle").time = i * 1.7
                    local r = go:GetComponentInChildren(typeof(UnityEngine.SkinnedMeshRenderer), true)
                    r.updateWhenOffscreen = true
                    r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off
                    local m = r.material
                    local tx = m:GetTexture("_BaseTex")
                    if tx then
                        m:SetTexture("_EmissionTex", tx)
                        m:SetColor("_EmissionColor", Color(1, 1, 1, 1))
                        m:SetFloat("_EmissionPower", 2.2)
                    end
                end)
            end)
        else
            report("no fw_" .. i)
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
                size = 1.5 + math.random() * 1.0,
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
            if not b.flapOn then
                b.flapOn = true
                t.localScale = Vector3.one * b.size
                loopAnim(b.go, "flap", 1 + math.random() * .4)
            end
        end
    end
    -- 烟花：只在夜里显示
    local showFw = blend < .5
    for _, f in ipairs(fireworks) do
        if f.on ~= showFw then
            f.on = showFw
            f.go:SetActive(showFw)
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
    ["2"] = { 150, 69, 151, 90 },    -- 盘山路第二段东头
    ["3"] = { 127, 74, 153, 0 },     -- 山顶南门外，朝北
    ["4"] = { 171, 41, 136, 0 },     -- 药水铺门前
    ["5"] = { 165, 42, 130, 300 },   -- 桥北头，上山路起点
    ["6"] = { 127, 73, 168, 0 },     -- 庭院，正对大门
    ["7"] = { 127, 34, 165, 0 },     -- 竞技场里面
    ["o"] = { 121, 41, 54.5, 0 },    -- 出生点旁的时之晷南边，往前走就踩上
    ["h"] = { 150, 42, 62, 310 },    -- 花海中央
    ["j"] = { 62, 46, 53, 0 },       -- 营地南边
    ["k"] = { 86, 49, 84, 0 },       -- 蘑菇林南边
    ["l"] = { 48, 54, 133, 0 },      -- 祭坛南边
    ["n"] = { 92, 44, 52, 40 },      -- 羊群
    [","] = { 200, 31, 90, 90 },      -- 码头
    ["."] = { 210, 34, 30, 0 },      -- 东南海边
    ["m"] = { 127, 73.5, 171, 0 },   -- 王座大厅门内
    ["i"] = { 118, 73.5, 179, -90 }, -- 书库
    ["g"] = { 136, 73.5, 179, 90 },  -- 宴会厅
    ["c"] = { 118.5, 73.5, 168, -90 }, -- 军械库
    ["r"] = { 135, 73.5, 168, 90 },  -- 厨房
    ["f"] = { 127, 73.5, 191.5, 0 }, -- 龙巢圣所
    ["e"] = { 127, 77.5, 191.5, 0 }, -- 寝殿
    ["q"] = { 132, 78, 183, 0 },     -- 大楼梯上
    ["z"] = { 150, 84, 196, 20 },    -- 近看冰龙
    ["u"] = { 96, 43, 22, 0 },       -- 飞毯驿站南边
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
local HV = { at = nil }
HV.list = {
    ["k"] = { 76, 51, 88, 0, 12 },       -- 墓园铁栏接地检查
    ["j"] = { 184, 48, 47, 0, 8 },       -- 村庄地基检查
    ["h"] = { 147, 49, 46, 25, -18 },    -- 查看树的昼夜叶色
    ["y"] = { 196, 126, 172, 335, 6 },     -- 看龙
    ["u"] = { 106, 66, 146, 40, 14 },      -- 看山坡上的草
    ["t"] = { 188, 58, 112, 43, 0 },       -- 灯塔石基近景
    ["q"] = { 60, 70, 60, 200, 2 },        -- 高处看西南海天相接
    ["z"] = { 70, 50, 52, 20, 10 },        -- 看新松树
}
local audioProbe = 0
local function updateDebug(actor)
    fpsT, fpsN = fpsT + Time.unscaledDeltaTime, fpsN + 1
    audioProbe = audioProbe + Time.unscaledDeltaTime
    if audioProbe > 45 and audioProbe < 1000 then
        audioProbe = 2000
        pcall(function()
            local list = UnityEngine.Object.FindObjectsOfType(typeof(UnityEngine.AudioSource))
            for i = 0, list.Length - 1 do
                local a = list[i]
                dbg("audio " .. a.gameObject.name .. " playing=" .. tostring(a.isPlaying) .. " clip=" .. tostring(a.clip and a.clip.name) .. " len=" .. tostring(a.clip and a.clip.length) .. " vol=" .. tostring(a.volume))
            end
        end)
    end
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
            if HV.at then
                HV.at = nil
                actor:Immobilize(false)
            end
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
    for key, h in pairs(HV.list) do
        if Input.GetKeyDown(key) then
            HV.at = h
            actor:Immobilize(true)
        end
    end
    if HV.at then
        actor:Teleport(Vector3(HV.at[1], HV.at[2], HV.at[3]), Quaternion.Euler(Vector3(0, HV.at[4], 0)))
        DouyinCameraService.SetYaw(HV.at[4])
        DouyinCameraService.SetPitch(HV.at[5])
    end
    if Input.GetKeyDown("9") then
        local p = actor.position
        dbg(string.format("pos=%.1f,%.1f,%.1f pitch=%.1f yaw=%.1f", p.x, p.y, p.z, DouyinCameraService.GetPitch(), DouyinCameraService.GetYaw()))
    end
end


---------------------------------------------------------------- 会晃的草：离玩家近的才显示，更近的才晃
local GameObject = UnityEngine.GameObject
local GRASS_SHOW = 40
local GRASS_SWAY = 34
local WIND_YAW = 35
local grass = {}
local grassNext = 0
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

local GRASS_CHUNKS = {{99.00,42.51,9.00,0.101,0.973,0.206},{81.00,41.77,27.00,0.095,0.995,0.017},{99.00,41.09,27.00,0.022,0.999,-0.024},{117.00,37.86,27.00,0.218,0.967,-0.131},{135.00,36.32,27.00,-0.045,0.978,-0.205},{153.00,38.47,27.00,-0.089,0.995,-0.042},{45.00,39.08,45.00,-0.381,0.910,-0.160},{63.00,42.69,45.00,0.035,0.992,-0.124},{81.00,42.46,45.00,0.071,0.995,-0.076},{99.00,41.33,45.00,0.051,0.996,-0.067},{117.00,39.66,45.00,0.097,0.993,-0.072},{135.00,38.79,45.00,0.000,0.998,-0.070},{153.00,39.03,45.00,-0.006,1.000,-0.025},{171.00,38.48,45.00,0.054,0.999,-0.002},{45.00,41.72,63.00,-0.266,0.964,0.002},{63.00,43.51,63.00,-0.000,1.000,-0.002},{81.00,44.34,63.00,-0.027,0.990,-0.140},{99.00,42.67,63.00,0.144,0.987,-0.074},{117.00,40.46,63.00,0.098,0.995,-0.019},{135.00,39.47,63.00,0.017,1.000,-0.006},{153.00,39.36,63.00,0.000,1.000,-0.002},{171.00,39.75,63.00,-0.071,0.994,-0.087},{189.00,43.61,63.00,-0.276,0.948,-0.159},{63.00,45.63,81.00,-0.149,0.945,-0.292},{81.00,47.53,81.00,0.166,0.986,0.021},{99.00,43.75,81.00,0.262,0.963,-0.064},{117.00,40.10,81.00,0.137,0.988,0.072},{135.00,38.59,81.00,0.039,0.993,0.108},{153.00,38.69,81.00,-0.068,0.995,0.070},{171.00,40.95,81.00,-0.193,0.981,-0.037},{81.00,46.74,99.00,0.021,1.000,-0.009},{99.00,44.99,99.00,0.358,0.933,0.025},{117.00,37.51,99.00,0.175,0.965,0.195},{135.00,35.28,99.00,0.040,0.972,0.233},{153.00,37.86,99.00,-0.254,0.967,-0.028},{171.00,40.74,99.00,0.047,0.997,0.057},{63.00,48.86,117.00,0.297,0.953,0.064},{81.00,43.54,117.00,0.134,0.933,0.333},{153.00,39.38,117.00,0.040,0.999,-0.019},{171.00,39.32,117.00,-0.028,0.998,-0.065},{27.00,54.20,135.00,0.021,0.949,0.313},{45.00,52.16,135.00,0.064,0.984,0.165},{63.00,49.77,135.00,0.355,0.932,-0.077},{135.00,40.78,135.00,-0.091,0.850,-0.519},{153.00,39.29,135.00,0.042,0.999,-0.029},{171.00,39.52,135.00,-0.047,0.998,0.029},{189.00,41.09,135.00,-0.109,0.994,0.027},{27.00,50.59,153.00,-0.067,0.996,0.053},{45.00,51.46,153.00,-0.078,0.995,0.067},{63.00,51.06,153.00,0.187,0.982,0.010},{117.00,60.72,153.00,-0.297,0.598,-0.745},{135.00,65.29,153.00,0.018,0.751,-0.660},{171.00,40.64,153.00,0.003,0.937,-0.350},{45.00,47.78,171.00,-0.077,0.903,0.424},{99.00,55.69,171.00,-0.795,0.597,-0.107},{117.00,71.83,171.00,-0.025,1.000,0.003},{135.00,72.15,171.00,0.008,1.000,-0.025},{153.00,62.84,171.00,0.789,0.604,-0.113},{171.00,42.57,171.00,0.625,0.768,0.139},{99.00,54.08,189.00,-0.534,0.845,0.039},{171.00,37.14,189.00,0.651,0.736,0.187},{99.00,44.18,207.00,-0.290,0.794,0.534},{117.00,48.22,207.00,-0.021,0.907,0.421},{135.00,52.43,207.00,-0.056,0.716,0.696},{153.00,44.30,207.00,0.500,0.719,0.483},{117.00,43.02,225.00,0.044,0.993,0.111}}
local function setupGrassStep()
    if grassNext >= #GRASS_CHUNKS then return end
    for _ = 1, 6 do
        grassNext = grassNext + 1
        local c = GRASS_CHUNKS[grassNext]
        if c == nil then break end
        local go = GameObject.Find("gc_" .. (grassNext - 1))
        if go ~= nil then
            local t = go.transform
            local pivot = GameObject("gp")
            local pt = pivot.transform
            pt.position = t.position
            local orig = t.rotation
            t:SetParent(pt, true)
            local tilt = Quaternion.FromToRotation(Vector3.up, Vector3(c[4], c[5], c[6]))
            grass[#grass + 1] = { pivot = pivot, pt = pt, t = t, x = c[1], z = c[3], tilt = tilt, childBase = Quaternion.Inverse(tilt) * orig, on = true, sway = false, ph = (c[1] * .31 + c[3] * .17) }
            pivot:SetActive(false)
            grass[#grass].on = false
        end
    end
end

local function updateGrass(actor)
    setupGrassStep()
    local n = #grass
    if n == 0 then return end
    local p = actor.position
    -- 每帧检查一部分：显示范围和晃动范围
    for _ = 1, 12 do
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
            g.pt.rotation = g.tilt * lutParentRot[i]
            g.pt.localScale = lutParentScale[i]
            g.t.localRotation = lutChild[i] * g.childBase
        end
    end
end

local MOUNT_YAW, MOUNT_SEAT = 180, .55
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
local runeGo, beamGo, runeGlow = nil, nil, nil
local litCount = 0
local iceParts
local function roarDragon()
    for _, an in ipairs(iceParts or {}) do
        pcall(function() an:get_Item("idle").time = 8.6 end)
    end
end
local summonT = nil
local altarReset = 0
local function setupAltar()
    runeGo, beamGo, runeGlow = {}, {}, {}
    for i = 1, 3 do
        runeGo[i] = GameObject.Find("rune_" .. (i - 1))
        runeGlow[i] = GameObject.Find("runeg_" .. (i - 1))
        if runeGlow[i] then runeGlow[i]:SetActive(false) end
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
        if runeGlow and runeGlow[i] then runeGlow[i]:SetActive(false) end
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
            if runeGlow and runeGlow[i] then runeGlow[i]:SetActive(true) end
            if litCount < 3 then
                toast("龙纹立石被唤醒 " .. litCount .. "/3")
            else
                if beamGo[4] then beamGo[4]:SetActive(true) end
                toast("雪山之巅的冰龙回应了你的呼唤！")
                roarDragon()
                altarReset = 45
                dbg("dragon summoned")
            end
        end
    end
end

---- 冰龙：站在雪山之巅，翅膀、脖子、头、尾巴都在动，10 秒左右怒吼一次
local dragonTried = false
iceParts = {}
local function updateDragon()
    if dragonTried then return end
    dragonTried = true
    if GameObject.Find("dragon_v8_live") then return end
    for _, nm in ipairs({ "shd_wa", "shd_wb", "shd_body", "shd_tail", "shd_head", "shd_legs" }) do
        local go = skinnedRoot(GameObject.Find(nm))
        if go == nil then
            report("no " .. nm)
        else
            loopAnim(go, "idle", nil, true, function(an)
                iceParts[#iceParts + 1] = an
                -- 三个部件用同一时间，保持同步
                for _, other in ipairs(iceParts) do
                    pcall(function() other:get_Item("idle").time = 0 end)
                end
                pcall(function()
                    local r = go:GetComponentInChildren(typeof(UnityEngine.SkinnedMeshRenderer), true)
                    r.updateWhenOffscreen = true
                    local m = r.material
                    local tx = m:GetTexture("_BaseTex")
                    if tx then
                        m:SetTexture("_EmissionTex", tx)
                        m:SetColor("_EmissionColor", Color(1, 1, 1, 1))
                        m:SetFloat("_EmissionPower", .45)
                    end
                    m:SetColor("_RimColor", Color(.5, .25, 1, 1))
                end)
            end)
        end
    end
end

---- 飞毯驿站：踏上飞毯就起飞，环游全图后落回原处
local FLIGHT = {
    { 96, 44, 30 }, { 112, 60, 38 }, { 150, 86, 62 }, { 175, 74, 104 }, { 196, 84, 140 }, { 196, 110, 188 }, { 166, 122, 196 },
    { 128, 118, 204 }, { 82, 108, 196 }, { 92, 94, 150 }, { 120, 98, 126 }, { 86, 78, 96 }, { 44, 84, 128 }, { 28, 84, 80 }, { 62, 64, 44 }, { 96, 46, 30 },
}
local FLIGHT_SPEED = 16
local rideT, rideS = nil, 0
local treeLogged = false
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
        mountGo = skinnedRoot(GameObject.Find("flying_carpet")) or false
        if mountGo then
            mountHome = mountGo.transform.position
            mountHomeRot = mountGo.transform.rotation
            loopAnim(mountGo, "ripple", nil, true, function(an)
                pcall(function()
                    local r = mountGo:GetComponentInChildren(typeof(UnityEngine.SkinnedMeshRenderer), true)
                    r.updateWhenOffscreen = true
                end)
            end)
        end
    end
    if not mountGo then return end
    local T = mountGo.transform
    if rideT == nil then
        T.position = mountHome + Vector3(0, .12 * math.sin(Time.time * 1.3), 0)
        rideCool = rideCool - Time.deltaTime
        if rideCool <= 0 and dist2d(p, SITE.perch[1], SITE.perch[2]) < 2.6 then
            rideT = 0
            rideS = 0
            actor:Immobilize(true)
            DouyinCameraService.SetDistance(7)
            toast("站稳了！飞毯带你环游龙眠之境")
        end
        return
    end
    rideT = rideT + Time.deltaTime
    rideS = rideS + Time.deltaTime * FLIGHT_SPEED / 640
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
    if DEBUG_TELEPORT and rideT > 3 and not treeLogged then
        treeLogged = true
        local function walk(tr, d)
            local comps = tr:GetComponents(typeof(UnityEngine.Component))
            local names = ""
            for i = 0, comps.Length - 1 do names = names .. " " .. tostring(comps[i]:GetType().Name) end
            dbg(string.rep(" ", d) .. tr.name .. " pos=" .. tostring(tr.position) .. " parent=" .. tostring(tr.parent and tr.parent.name) .. names)
            if d < 2 then for i = 0, tr.childCount - 1 do walk(tr:GetChild(i), d + 1) end end
        end
        pcall(walk, T, 0)
        pcall(function()
            local r = mountGo:GetComponentInChildren(typeof(UnityEngine.SkinnedMeshRenderer), true)
            dbg("rootBone=" .. tostring(r.rootBone and r.rootBone.name) .. " b0=" .. tostring(r.bones[0].name) .. " b0pos=" .. tostring(r.bones[0].position) .. " b0parent=" .. tostring(r.bones[0].parent.name))
        end)
    end
    if DEBUG_TELEPORT and math.floor(rideT) ~= math.floor(rideT - Time.deltaTime) then
        pcall(function()
            local r = mountGo:GetComponentInChildren(typeof(UnityEngine.SkinnedMeshRenderer), true)
            dbg("ride pos=" .. tostring(T.position) .. " actor=" .. tostring(actor.position) .. " rend=" .. tostring(r and r.enabled) .. " vis=" .. tostring(r and r.isVisible) .. " bounds=" .. tostring(r and r.bounds.center) .. " active=" .. tostring(mountGo.activeInHierarchy))
        end)
    end
    local dx3, dz3 = dx, dz
    local x3, _, z3 = flightAt(math.min(rideS + .012, .9999))
    local turn = (x3 - x2) * dz - (z3 - z2) * dx
    T.rotation = Quaternion.Euler(Vector3(0, yaw + MOUNT_YAW, math.max(-16, math.min(16, turn * 2.2))))
    actor:Teleport(Vector3(x, y + MOUNT_SEAT, z), Quaternion.Euler(Vector3(0, yaw, 0)))
    -- 飞近巨龙时镜头转过去看它
    local ddx, ddz = 165 - x, 240 - z
    local dd = math.sqrt(ddx * ddx + ddz * ddz)
    local look = yaw
    if dd < 85 then
        local toDragon = math.deg(math.atan(ddx, ddz))
        local diff = (toDragon - yaw + 540) % 360 - 180
        local k = math.min(1, (85 - dd) / 25)
        look = yaw + diff * k
    end
    DouyinCameraService.SetYaw(look)
    DouyinCameraService.SetPitch(dd < 85 and 2 or 12)
end

local holyLight = nil
local holyTried = { materials = {}, found = {} }
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
                        m:SetTexture("_EmissionTex", UnityEngine.Texture2D.whiteTexture)
                        m:SetColor("_EmissionColor", Color(1, .025, .055, 1))
                        holyTried.materials[#holyTried.materials + 1] = m
                    end
                    holyTried.found[name] = true
                end
            end
        end
    end
    local night = 1 - blend
    local glow = night * night * (.68 + .045 * math.sin(Time.time * .65))
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

---- 城堡的房间：走进去时提示房间名，灯只在城堡里才开
local ROOMS = {
    { "王座大厅", 120.8, 133.2, 168, 190, 71, 90, 127, 78, 172, 1, .74, .46, 30, 5.0 },
    { "书库", 114, 120.8, 175, 183, 71, 84, 117, 77, 179, 1, .78, .5, 14, 2.6 },
    { "宴会厅", 133.2, 140, 175, 183, 71, 84, 137, 77, 179, 1, .66, .36, 14, 2.8 },
    { "军械库", 115.4, 120.8, 165.9, 170.2, 71, 77, 117.6, 75.5, 168, 1, .72, .46, 9, 2.4 },
    { "厨房", 133.2, 138.3, 165.9, 170.2, 71, 77, 135.7, 75.5, 168, 1, .62, .32, 9, 2.6 },
    { "龙巢圣所", 120.6, 133.4, 190, 197, 71, 76.1, 127, 74.8, 193, .55, .82, 1, 12, 3.0 },
    { "寝殿", 120.6, 133.4, 190, 197, 76.1, 86, 127, 80.5, 193, 1, .74, .5, 12, 2.6 },
}
local hallLight2 = nil
local roomLights, curRoom, lightsOn = nil, nil, false
local function updateRooms(p)
    if roomLights == nil then
        roomLights = {}
        for i, r in ipairs(ROOMS) do
            roomLights[i] = addLight(Vector3(r[8], r[9], r[10]), Color(r[11], r[12], r[13], 1), r[14], r[15])
            if roomLights[i] then roomLights[i].enabled = false end
        end
        hallLight2 = addLight(Vector3(127, 78, 184), Color(1, .72, .44, 1), 28, 4.6)
        if hallLight2 then hallLight2.enabled = false end
    end
    local near = dist2d(p, 127, 180) < 32 and p.y > 66
    if near ~= lightsOn then
        lightsOn = near
        for _, l in pairs(roomLights) do if l then l.enabled = near end end
        if hallLight2 then hallLight2.enabled = near end
    end
    if not near then curRoom = nil; return end
    local here = nil
    for _, r in ipairs(ROOMS) do
        if p.x > r[2] and p.x < r[3] and p.z > r[4] and p.z < r[5] and p.y > r[6] and p.y < r[7] then
            here = r[1]
            break
        end
    end
    if here ~= curRoom then
        curRoom = here
        if here then toast(here) end
    end
end

---- 白天的云：绕地图缓慢飘动
local cloudPivot, cloudReady = nil, false
local function updateClouds()
    if not cloudReady then
        cloudReady = true
        cloudPivot = GameObject("cloud_pivot")
        cloudPivot.transform.position = Vector3(128, 0, 128)
        for i = 0, 15 do
            local go = GameObject.Find("cl_" .. i)
            if go then
                go.transform:SetParent(cloudPivot.transform, true)
            end
        end
    end
    local show = blend > .5
    if show ~= cloudPivot.activeSelf then cloudPivot:SetActive(show) end
    if show then
        cloudPivot.transform.rotation = Quaternion.Euler(Vector3(0, Time.time * .35, 0))
    end
end

---- 开船：走到码头边按跳跃上船，摇杆开船，靠岸再按跳跃下船
local SEA_GRID = {"1111111111111110000100000000000000000000000001111111111111111111","1111111110000000000000000000000000000000000000001111111111111111","1111111100000000000000000000000000000000000000001111111111111111","1111111000000000000000000000000000000000000000001111111111111111","1110000000000000000000000000000000000000000000001111111111111111","1100000000000000000000000000000000000000000000001111111111111111","1100000000000000000000000000000000000000000000000111111111111111","1100000000000000000000000000000000000000000000000111111111111111","1100000000000000000000000000000000000000000000000111111111111111","1100000000000000000000000000000000000000000000000111111111111111","1100000000000000000000000000000000000000000000000111111111111111","1110000000000000000000000000000000000000000000000011111111111111","1110000000000000000000000000000000000000000000000011111111111111","1100000000000000000000000000000000000000000000000011111111111111","1110000000000000000000000000000000000000000000000011111111111111","1110000000000000000000000000000000000000000000000001111111111111","1111000000000000000000000000000000000000000000000001111111111111","1111000000000000000000000000000000000000000000000000111111111111","1110000000000000000000000000000000000000000000000000111111111111","1000000000000000000000000000000000000000000000000001111111111111","1000000000000000000000000000000000000000000000000011111111111111","0000000000000000000000000000000000000000000000000111111111111111","0000000000000000000000000000000000000000000000001111111111111111","0000000000000000000000000000000000000000000000111111111111111111","0000000000000000000000000000000000000000000000111111111111111111","0000000000000000000000000000000000000000000001111111111111111111","0000000000000000000000000000000000000000000001111111111111111111","0000000000000000000000000000000000000000000000111111111111111111","0000000000000000000000000000000000000000000000011000000111111111","0000000000000000000000000000110000000000000000000000000011111111","0000000000000000000000000011110000000000000000000000000001111111","0000000000000000000000000111100000000000000000000000000001111111","0000000000000000000000000011000000000000000000000000000001111111","0000000000000000000000000000000000000000000000000000000001111111","0000000000000000000000000000000000000000000000000000000001111111","0000000000000000000000000000000000000000000000000000000001111111","0000000000000000000000000000000000000000000000000000000011111111","0000000000000000000000000000000000000000000000000000000111111111","0000000000000000000000000000000000000000000000000000001111111111","0000000000000000000000000000000000000000000000000000011111111111","0000000000000000000000000000000000000000000000000000011111111111","0000000000000000000000000000000000000000000000000000011111111111","0000000000000000000000000000000000000000000000000000011111111111","0000000000000000000000000000000000000000000000000000011111111111","0000000000000000000000000000000000000000000000000000001111111111","0000000000000000000000000000000000000000000000000000001111111111","0000000000000000000000000000000000000000000000000000001111111111","0000000000000000000000000000000000000000000000000000001111111111","0000000000000000000000000000000000000000000000000000001111111111","0000000000000000000000000000000000000000000000000000001111111111","0000000000000000000000000000000000000000000000000000000011111111","0000000000000000000000000000000000000000000000000000000001111111","0000000000000000000000000000000000000000000000000000000001111111","0000000000000000000000000000000000000000000000000000000001111111","0000000000000000000000000000000000000000000000000000000001111111","0000000000000000000000000000000000000000000000000000000000111111","0000000000000000000000000000000000000000000000000000000000111111","0000000000000000000000000000000000000000000000000000000001111111","0000000000000000000000000000000000000000000000000000000000111111","0000000000000000000000000000000000000000000000000000000001111111","0000000000000000000000000000000000000000000000000000000011111111","0000000000000000000000000000000000000000000000000000000111111111","0000000000000000000000000000000000000000000000000000001111111111","0000000000000000000000000000000000000000000000000000011111111111"}
local SEA_Y, BOAT_SEAT = 26.9, 2.4
local boats = nil
local boatOn, boatJump, boatSaid, boatSpeed = nil, false, false, 0
local BT = { log = 0, cool = 0, input = false }
local moveX, moveY = 0, 0
local function boatSetup()
    boats = {}
    for i = 0, 2 do
        local go = GameObject.Find("sailboat_" .. i)
        if go then
            local t = go.transform
            local e = t.rotation.eulerAngles
            boats[#boats + 1] = { go = go, t = t, x = t.position.x, z = t.position.z, yaw = e.y - 180, ph = i * 1.7 }
        end
    end
    if #boats == 0 or BT.input then return end
    BT.input = true
    pcall(function()
        DouyinInputService.onMoveInputPerform:AddListener(function(v) moveX, moveY = v.x, v.y end)
        DouyinInputService.onMoveInputCancel:AddListener(function() moveX, moveY = 0, 0 end)
        DouyinInputService.onJumpInputStart:AddListener(function() boatJump = true end)
    end)
end
local function isSea(x, z)
    if x < 1 or z < 1 or x > 254 or z > 254 then
        return math.sqrt((x - 128) ^ 2 + (z - 128) ^ 2) < 420
    end
    local i, j = math.floor(x / 4), math.floor(z / 4)
    local row = SEA_GRID[j + 1]
    return row ~= nil and string.sub(row, i + 1, i + 1) == "1"
end
local function nearLand(x, z)
    for a = 0, 7 do
        for r = 6, 22, 4 do
            local xx, zz = x + math.cos(a * .785) * r, z + math.sin(a * .785) * r
            if xx > 1 and zz > 1 and xx < 254 and zz < 254 and not isSea(xx, zz) then
                return xx, zz
            end
        end
    end
    return nil
end
local function updateBoats(actor, p)
    if boats == nil or #boats == 0 then boatSetup() end
    local dt = Time.deltaTime
    local T = Time.time
    BT.cool = BT.cool - dt
    if Input.GetKeyDown("space") then
        boatJump = true
        if DEBUG_TELEPORT then
            local msg = "boat jump boats=" .. #boats .. " on=" .. tostring(boatOn ~= nil) .. string.format(" p=%.1f,%.1f,%.1f", p.x, p.y, p.z)
            for _, b in ipairs(boats) do msg = msg .. string.format(" d=%.1f", dist2d(p, b.x, b.z)) end
            report(msg)
        end
    end
    for _, b in ipairs(boats) do
        if b ~= boatOn then
            b.t.position = Vector3(b.x, SEA_Y + .12 * math.sin(T * .9 + b.ph), b.z)
            b.t.rotation = Quaternion.Euler(Vector3(1.2 * math.sin(T * .7 + b.ph), b.yaw + 180, 1.6 * math.sin(T * .55 + b.ph)))
        end
    end
    if boatOn == nil then
        local near = nil
        for _, b in ipairs(boats) do
            if dist2d(p, b.x, b.z) < 11 and p.y < 34 then near = b end
        end
        if near and not boatSaid then
            boatSaid = true
            toast("按跳跃键上船")
        elseif not near then
            boatSaid = false
        end
        if near and boatJump and BT.cool <= 0 then
            boatOn = near
            boatSpeed = 0
            near.sx, near.sz = near.x, near.z   -- 只允许从停泊点往外开 16 米找海面
            BT.cool = .8   -- 跳跃键下一帧还会再触发一次，不能当成下船
            actor:Immobilize(true)
            DouyinCameraService.SetDistance(8)
            toast("摇杆开船，靠岸后按跳跃键下船")
        end
        boatJump = false
        return
    end
    local b = boatOn
    local mag = math.min(1, math.sqrt(moveX * moveX + moveY * moveY))
    if Input.GetKey("w") then moveY = 1; mag = 1 end
    if mag > .05 then
        local camYaw = DouyinCameraService.GetYaw()
        local want = camYaw + math.deg(math.atan(moveX, moveY))
        local diff = (want - b.yaw + 540) % 360 - 180
        b.yaw = b.yaw + math.max(-46 * dt, math.min(46 * dt, diff))
    end
    boatSpeed = boatSpeed + (mag * 11 - boatSpeed) * math.min(1, dt * .9)
    local nx = b.x + math.sin(math.rad(b.yaw)) * boatSpeed * dt
    local nz = b.z + math.cos(math.rad(b.yaw)) * boatSpeed * dt
    -- 停在码头边时脚下算陆地，允许从停泊点开出 16 米去找海；到了海上就不能再开上岸
    if isSea(nx, nz) then
        b.x, b.z = nx, nz
    else
        boatSpeed = 0
    end
    local y = SEA_Y + .16 * math.sin(T * 1.1 + b.ph)
    b.t.position = Vector3(b.x, y, b.z)
    if DEBUG_TELEPORT then
        BT.log = (BT.log or 0) + dt
        if BT.log > 2 then
            BT.log = 0
            local r = b.go:GetComponentInChildren(typeof(UnityEngine.Renderer), true)
            report(string.format("boat b=%.1f,%.1f speed=%.1f yaw=%.0f root=%s rend=%s actor=%s", b.x, b.z, boatSpeed, b.yaw, tostring(b.t.position), r and tostring(r.bounds.center) or "nil", tostring(actor.position)))
        end
    end
    b.t.rotation = Quaternion.Euler(Vector3(1.6 * math.sin(T * .9), b.yaw + 180, -boatSpeed * .2 * math.sin(T * .6)))
    actor:Teleport(Vector3(b.x, y + BOAT_SEAT, b.z), Quaternion.Euler(Vector3(0, b.yaw, 0)))
    DouyinCameraService.SetDistance(8)
    if boatJump and BT.cool > 0 then boatJump = false end
    if boatJump then
        boatJump = false
        local lx, lz = nearLand(b.x, b.z)
        if lx then
            boatOn = nil
            BT.cool = .8
            boatSpeed = 0
            moveX, moveY = 0, 0
            actor:Immobilize(false)
            DouyinCameraService.SetDistance(CAMERA_DIST)
            actor:Teleport(Vector3(lx, 45, lz))
            toast("上岸了")
        else
            toast("靠岸后才能下船")
        end
    end
end

---- 骑龙：在唤龙祭坛按跳跃，被送上山顶的龙背；摇杆控制飞行，按跳跃降落下龙，龙自己飞回山顶
local DR = { state = "perch", cool = 0, said = false, jump = false, speed = 0, roll = 0 }
DR.PARTS = { "shd_wa", "shd_wb", "shd_body", "shd_tail", "shd_head", "shd_legs" }
DR.ALTAR = { 48, 150 }
DR.SEAT = Vector3(0, 29.6, 4.4)   -- 龙背两肩之间（模型实测）
function DR.ground(x, z)
    local ok, h = pcall(function()
        local t = UnityEngine.Terrain.activeTerrain
        return t:SampleHeight(Vector3(x, 0, z)) + t.transform.position.y
    end)
    if ok and h then return h end
    return 40
end
-- Mesh mountains and buildings can stand far above the terrain heightmap.
function DR.flightSurface(x,z)
    local height=DR.ground(x,z)
    local ok, result=pcall(function()
        local hits=UnityEngine.Physics.RaycastAll(Vector3(x,400,z),Vector3(0,-1,0),500,-1,UnityEngine.QueryTriggerInteraction.Ignore)
        local top=height
        for i=0,hits.Length-1 do
            local hit=hits[i]
            local riderHit=DR.rider and hit.transform:IsChildOf(DR.rider.gameObject.transform)
            if not riderHit then top=math.max(top,hit.point.y) end
        end
        return top
    end)
    return ok and result or height
end
function DR.flightClearance(x,z)
    DR.clearanceTimer=(DR.clearanceTimer or 0)-Time.deltaTime
    if DR.clearanceTimer<=0 or not DR.surfaceY then
        local r=math.rad(DR.yaw)
        DR.surfaceY=math.max(DR.flightSurface(x,z),DR.flightSurface(x+math.sin(r)*25,z+math.cos(r)*25),
            DR.flightSurface(x+math.cos(r)*15,z-math.sin(r)*15),DR.flightSurface(x-math.cos(r)*15,z+math.sin(r)*15))
        DR.clearanceTimer=.2
    end
    return DR.surfaceY
end
function DR.setup()
    DR.parts = {}
    local rig = GameObject.Find("dragon_v8_live")
    if rig then
        local an = rig:GetComponentInChildren(typeof(UnityEngine.Animation), true)
        local bones = rig:GetComponentsInChildren(typeof(UnityEngine.Transform), true)
        local socket = nil
        for i=0,bones.Length-1 do
            if bones[i].name=="rider_socket" then socket=bones[i];break end
        end
        if not an or not socket then DR.parts=nil;return end
        for _,clip in ipairs({"idle","takeoff","fly","land"}) do
            if not an:GetClip(clip) then DR.parts=nil;return end
        end
        DR.v8,DR.an,DR.socket=true,an,socket
        DR.perchClips=an:GetClip("perch") and an:GetClip("perch_takeoff") and an:GetClip("perch_land") and true or false
        an.cullingType=UnityEngine.AnimationCullingType.AlwaysAnimate
        DR.parts={rig.transform}
        dbg("dragon_v8 ready: four clips and rider_socket")
    else
        for _, nm in ipairs(DR.PARTS) do
            local go = skinnedRoot(GameObject.Find(nm))
            if go then DR.parts[#DR.parts + 1] = go.transform end
        end
    end
    if #DR.parts == 0 then DR.parts = nil return end
    local t = DR.parts[1]
    DR.home, DR.homeRot = t.position, t.rotation
    DR.homeYaw = t.rotation.eulerAngles.y      -- 根节点的朝向角就是龙头朝向
    DR.pos, DR.yaw = DR.home, DR.homeYaw
    DR.seat = GameObject("dragon_seat")
    if DR.v8 then
        -- Skeleton scale is 54. A world-space proxy must never inherit that
        -- scale or the bone's local axes as a seat/camera transform.
        DR.seat.transform.localScale = Vector3.one
        DR.seat.transform.position = DR.socket.position + Vector3(0,.35,0)
        local cols=rig:GetComponentsInChildren(typeof(UnityEngine.Collider),true)
        for i=0,cols.Length-1 do cols[i].enabled=false end
    else
        DR.seat.transform:SetParent(DR.parts[1], false)
        DR.seat.transform.localPosition = DR.SEAT
    end
    pcall(function()
        DouyinInputService.onJumpInputStart:AddListener(function() DR.jump = true end)
    end)
end
function DR.place(pitch)
    local rot = Quaternion.Euler(Vector3(pitch or 0, DR.yaw, DR.roll))
    for _, t in ipairs(DR.parts) do
        t.position = DR.pos
        t.rotation = rot
    end
end
function DR.mount(actor)
    DR.align(actor)
    local ok,err=pcall(function() actor:SitDown(DR.seat) end)
    if not ok then report("dragon sit: "..tostring(err)) end
    if DR.v8 then
        DR.actorAnimator=actor.gameObject:GetComponentInChildren(typeof(UnityEngine.Animator),true)
        DR.cameraWarm=0
        DR.rider=actor
        actor.gameObject.transform:SetParent(DR.seat.transform,true)
        local main=DouyinCameraService.GetCamera()
        if main then
            local go=GameObject("dragon_ride_camera")
            DR.camera=go:AddComponent(typeof(UnityEngine.Camera))
            DR.camera:CopyFrom(main)
            DR.camera.depth=main.depth+3
            DR.camera.fieldOfView=60
            pcall(function()
                local T=typeof(CS.UnityEngine.Rendering.Universal.UniversalAdditionalCameraData)
                local a=main:GetComponent(T)
                local b=go:AddComponent(T)
                if a then b.renderPostProcessing=a.renderPostProcessing;b.renderShadows=a.renderShadows end
            end)
        end
    end
    DR.align(actor)
end
function DR.align(actor)
    local t = DR.seat.transform
    local offset=Vector3.zero
    if DR.v8 then
        t.position=DR.socket.position+Vector3(0,.35,0)
        t.rotation=Quaternion.Euler(Vector3(0,DR.yaw,0))
        if DR.actorAnimator then
            local hips=DR.actorAnimator:GetBoneTransform(UnityEngine.HumanBodyBones.Hips)
            if hips then offset=hips.position-actor.gameObject.transform.position end
        end
        DouyinCameraService.SetDistance(42)
        DR.cameraWarm=(DR.cameraWarm or 0)+Time.deltaTime
        if DR.cameraWarm<1 then DouyinCameraService.SetPitch(22) end
    end
    if DR.v8 and DR.rider then
        local trans=actor.gameObject.transform
        trans.position=t.position-offset
        trans.rotation=t.rotation
        if DR.camera then
            local yaw=math.rad(DouyinCameraService.GetYaw())
            local target=t.position+Vector3(0,2,0)
            local eye=target+Vector3(-math.sin(yaw)*40,19,-math.cos(yaw)*40)
            DR.camera.transform.position=eye
            DR.camera.transform.rotation=Quaternion.LookRotation(target-eye)
        end
        DR.seatLog=(DR.seatLog or 0)+Time.deltaTime
        if DR.seatLog>3 then
            DR.seatLog=0
            dbg("seat socket="..tostring(DR.socket.position).." root="..tostring(trans.position).." offset="..tostring(offset).." camera="..tostring(DR.camera and DR.camera.transform.position))
        end
    else
        actor:Teleport(t.position-offset, Quaternion.Euler(Vector3(0, DR.yaw, 0)))
    end
end
function DR.dismount(actor, x, z)
    if DR.v8 then
        DR.rider=nil
        actor.gameObject.transform:SetParent(nil,true)
        if DR.camera then UnityEngine.Object.Destroy(DR.camera.gameObject);DR.camera=nil end
    end
    pcall(function() actor:StandUp(DR.seat) end)
    actor:Immobilize(false)
    actor:Teleport(Vector3(x, DR.ground(x, z) + 1.2, z))
    DouyinCameraService.SetDistance(CAMERA_DIST)
end
-- New rig: animation timings are authored at 30 fps and use in-place clips.
function DR.play(clip, loop)
    if not DR.an then return end
    if DR.clip == clip and DR.an:IsPlaying(clip) then return end
    local ok, err = pcall(function()
        DR.an.enabled = true
        DR.an.wrapMode = loop and UnityEngine.WrapMode.Loop or UnityEngine.WrapMode.ClampForever
        local st = DR.an:get_Item(clip)
        st.wrapMode = loop and UnityEngine.WrapMode.Loop or UnityEngine.WrapMode.ClampForever
        st.speed, st.time = 1, 0
        DR.an:CrossFade(clip, .18)
    end)
    if ok then DR.clip = clip; dbg("dragon_v8 clip=" .. clip)
    else report("dragon_v8 animation: " .. tostring(err)) end
end
function DR.homePose(weight)
    for _, t in ipairs(DR.parts) do
        t.rotation = Quaternion.Slerp(Quaternion.Euler(Vector3(0,DR.homeYaw,0)),DR.homeRot,weight)
    end
end
function DR.ease(u)
    u = math.max(0, math.min(1, u))
    return u*u*(3-2*u)
end
function DR.phase(state, clip, loop)
    DR.state, DR.phaseT = state, 0
    DR.play(clip, loop)
    dbg("dragon_v8 state=" .. state)
end
function DR.landingHeight(x, z)
    -- The four-foot support footprint extends forward of the model origin.
    local r, lo, hi = math.rad(DR.yaw), 1e9, -1e9
    for _, a in ipairs({-5,5}) do
        for _, b in ipairs({7,24}) do
            local sx, sz = x+a*math.cos(r)+b*math.sin(r), z-a*math.sin(r)+b*math.cos(r)
            if sx<3 or sx>253 or sz<3 or sz>253 then return nil end
            local h=DR.ground(sx,sz)
            lo,hi=math.min(lo,h),math.max(hi,h)
        end
    end
    if lo<29 or hi-lo>2.5 then return nil end
    return hi+.08
end
function DR.takeoff(returning)
    DR.from = DR.pos
    DR.returning = returning
    DR.fromHome = DR.state=="perch"
    DR.phase("takeoff", "takeoff", false)
end
function DR.landAt(target, home)
    DR.from, DR.target, DR.homeLanding = DR.pos, target, home
    DR.phase("touchdown", "land", false)
end
function DR.updateV8(actor, p)
    local dt = math.min(Time.deltaTime, .1)
    if Input.GetKeyDown("space") then DR.jump=true end
    DR.cool=DR.cool-dt
    DR.phaseT=(DR.phaseT or 0)+dt
    if DR.state=="perch" then
        -- The user fitted the imported rest pose to the slope. The authored
        -- perch clip adds 6.48m of forefoot lift and must not be layered on it.
        DR.play("idle",true)
        DR.pos=DR.home
        for _,t in ipairs(DR.parts) do t.position=DR.home;t.rotation=DR.homeRot end
        local near=dist2d(p,DR.ALTAR[1],DR.ALTAR[2])<20
        if near and not DR.said then DR.said=true;toast("在唤龙祭坛按跳跃键，召唤巨龙") end
        if not near then DR.said=false end
        if near and DR.jump and DR.cool<=0 then
            DR.cool,DR.speed=2,0
            actor:Immobilize(true);DR.mount(actor)
            DouyinCameraService.SetDistance(42)
            DR.takeoff(false)
            toast("巨龙载你起飞！摇杆控制方向，按跳跃键降落")
        end
    elseif DR.state=="takeoff" then
        local u=DR.phaseT/1.8
        DR.pos=Vector3(DR.from.x,DR.from.y+14*DR.ease((u-.25)/.75),DR.from.z)
        DR.place(0)
        if DR.fromHome then DR.homePose(1-DR.ease((u-.25)/.75)) end
        if not DR.returning then DR.align(actor) end
        if u>=1 then DR.phase(DR.returning and "return_fly" or "ride","fly",true) end
    elseif DR.state=="ride" then
        local mx,my=moveX,moveY
        if Input.GetKey("w") then my=1 end
        if Input.GetKey("s") then my=-1 end
        if Input.GetKey("a") then mx=-1 end
        if Input.GetKey("d") then mx=1 end
        local mag=math.min(1,math.sqrt(mx*mx+my*my))
        local turn=0
        if mag>.1 then
            local want=DouyinCameraService.GetYaw()+math.deg(math.atan(mx,my))
            local diff=(want-DR.yaw+540)%360-180
            turn=math.max(-55*dt,math.min(55*dt,diff));DR.yaw=DR.yaw+turn
        end
        DR.speed=DR.speed+((mag>.1 and 26 or 7)-DR.speed)*math.min(1,dt*.8)
        local r=math.rad(DR.yaw)
        local x,z=DR.pos.x+math.sin(r)*DR.speed*dt,DR.pos.z+math.cos(r)*DR.speed*dt
        -- Keep the entire dragon near the playable terrain. Turn back toward
        -- the island before the root reaches the edge, including idle flight.
        if x<24 or x>232 or z<24 or z>232 then
            local inward=math.deg(math.atan(128-DR.pos.x,128-DR.pos.z))
            local diff=(inward-DR.yaw+540)%360-180
            DR.yaw=DR.yaw+math.max(-90*dt,math.min(90*dt,diff))
            r=math.rad(DR.yaw)
            x=math.max(8,math.min(248,DR.pos.x+math.sin(r)*DR.speed*dt))
            z=math.max(8,math.min(248,DR.pos.z+math.cos(r)*DR.speed*dt))
        end
        local surface=DR.flightClearance(x,z)
        local want=math.max(surface+30,62)
        local y=math.max(surface+8,DR.pos.y+(want-DR.pos.y)*math.min(1,dt*.7))
        DR.roll=DR.roll+((-turn/math.max(dt,.001))*.25-DR.roll)*math.min(1,dt*2)
        local climb=(y-DR.pos.y)/math.max(dt,.001)
        DR.pos=Vector3(x,y,z);DR.place(math.max(-12,math.min(12,-climb*.8)));DR.align(actor)
        if DR.jump and DR.cool<=0 then
            local h=DR.landingHeight(x,z)
            DR.cool=1
            if h then
                DR.target=Vector3(x,h,z);DR.from=DR.pos
                DR.phase("approach","fly",true);toast("巨龙正在降落")
            else toast("请飞到平坦陆地上空再降落") end
        end
    elseif DR.state=="approach" then
        local u=DR.ease(DR.phaseT/3)
        DR.pos=Vector3(DR.target.x,DR.from.y+(DR.target.y+3-DR.from.y)*u,DR.target.z)
        DR.roll=DR.roll*(1-math.min(1,dt*4));DR.place(0);DR.align(actor)
        if DR.phaseT>=3 then DR.landAt(DR.target,false) end
    elseif DR.state=="touchdown" then
        -- Feet extend first; terrain contact coincides with the baked IK phase.
        local u=DR.ease(DR.phaseT/(2.8*.65))
        DR.pos=Vector3(DR.target.x,DR.from.y+(DR.target.y-DR.from.y)*u,DR.target.z)
        DR.roll=0;DR.place(0)
        if DR.homeLanding then DR.homePose(u) end
        if not DR.homeLanding then DR.align(actor) end
        if DR.phaseT>=2.8 then
            if DR.homeLanding then
                DR.yaw=DR.homeYaw;DR.place(0);DR.homePose(1);DR.cool=2
                DR.phase("perch","idle",true)
            else
                local r=math.rad(DR.yaw)
                DR.dismount(actor,DR.pos.x+math.cos(r)*12,DR.pos.z-math.sin(r)*12)
                DR.phase("rest","idle",true);toast("已安全落地，巨龙稍后返回雪山")
            end
        end
    elseif DR.state=="rest" then
        if DR.phaseT>=1.5 then DR.takeoff(true) end
    elseif DR.state=="return_fly" then
        local to=DR.home-DR.pos
        local flat=math.sqrt(to.x*to.x+to.z*to.z)
        if flat>1 then
            local want=math.deg(math.atan(to.x,to.z))
            local diff=(want-DR.yaw+540)%360-180
            DR.yaw=DR.yaw+math.max(-70*dt,math.min(70*dt,diff))
        end
        local step=math.min(flat,28*dt)
        local x=DR.pos.x+(flat>0 and to.x/flat*step or 0)
        local z=DR.pos.z+(flat>0 and to.z/flat*step or 0)
        local h=flat>25 and math.max(DR.home.y+25,DR.flightClearance(x,z)+30) or DR.home.y+3
        DR.pos=Vector3(x,DR.pos.y+(h-DR.pos.y)*math.min(1,dt*.9),z)
        DR.roll=0;DR.place(0)
        if flat<1 and math.abs(DR.pos.y-DR.home.y-3)<.3 then
            DR.yaw=DR.homeYaw;DR.landAt(DR.home,true)
        end
    end
    DR.jump=false
end

function DR.update(actor, p)
    if DR.parts == nil then
        DR.setup()
        if DR.parts == nil then return end
    end
    if DR.v8 then DR.updateV8(actor,p);return end
    local dt = Time.deltaTime
    if Input.GetKeyDown("space") then DR.jump = true end
    DR.cool = DR.cool - dt
    if DR.state == "perch" then
        local near = dist2d(p, DR.ALTAR[1], DR.ALTAR[2]) < 20
        if near and not DR.said then
            DR.said = true
            toast("在唤龙祭坛按跳跃键，召唤巨龙")
        elseif not near then
            DR.said = false
        end
        if near and DR.jump and DR.cool <= 0 then
            DR.state, DR.speed, DR.cool = "ride", 0, 1.0
            actor:Immobilize(true)
            DR.mount(actor)
            DouyinCameraService.SetDistance(26)
            toast("巨龙载你起飞！摇杆控制方向，按跳跃键降落")
        end
    elseif DR.state == "ride" then
        local mag = math.min(1, math.sqrt(moveX * moveX + moveY * moveY))
        if Input.GetKey("w") then moveY = 1; mag = 1 end
        local turn = 0
        if mag > .1 then
            local want = DouyinCameraService.GetYaw() + math.deg(math.atan(moveX, moveY))
            local diff = (want - DR.yaw + 540) % 360 - 180
            turn = math.max(-55 * dt, math.min(55 * dt, diff))
            DR.yaw = DR.yaw + turn
        end
        DR.speed = DR.speed + ((mag > .1 and 26 or 7) - DR.speed) * math.min(1, dt * .8)
        local r = math.rad(DR.yaw)
        local nx, nz = DR.pos.x + math.sin(r) * DR.speed * dt, DR.pos.z + math.cos(r) * DR.speed * dt
        local d0 = math.sqrt((nx - 128) ^ 2 + (nz - 128) ^ 2)
        if d0 > 230 then nx, nz = DR.pos.x, DR.pos.z end
        local want = math.min(170, math.max(DR.ground(nx, nz) + 30, 62))
        local ny = DR.pos.y + (want - DR.pos.y) * math.min(1, dt * .7)
        DR.roll = DR.roll + ((-turn / math.max(dt, .001)) * .35 - DR.roll) * math.min(1, dt * 2)
        local climb = (ny - DR.pos.y) / math.max(dt, .001)
        DR.pos = Vector3(nx, ny, nz)
        DR.place(math.max(-12, math.min(12, -climb * .8)))
        DR.align(actor)
        if DR.jump and DR.cool <= 0 then
            local gx, gz = DR.pos.x, DR.pos.z
            if gx > 6 and gz > 6 and gx < 250 and gz < 250 and DR.ground(gx, gz) > 28.5 then
                DR.state, DR.landT, DR.cool = "land", 0, 1.0
                toast("巨龙正在降落")
            else
                DR.cool = 1.0
                toast("飞到陆地上空再降落")
            end
        end
    elseif DR.state == "land" then
        DR.landT = DR.landT + dt
        DR.speed = DR.speed * (1 - math.min(1, dt * 1.5))
        local r = math.rad(DR.yaw)
        local nx, nz = DR.pos.x + math.sin(r) * DR.speed * dt, DR.pos.z + math.cos(r) * DR.speed * dt
        local g = DR.ground(nx, nz)
        local ny = DR.pos.y + (g + 2 - DR.pos.y) * math.min(1, dt * 1.2)
        DR.roll = DR.roll * (1 - math.min(1, dt * 2))
        DR.pos = Vector3(nx, ny, nz)
        DR.place(0)
        DR.align(actor)
        if ny - g < 4 or DR.landT > 6 then
            local ox, oz = nx + math.cos(r) * 14, nz - math.sin(r) * 14   -- 下到龙身侧面
            DR.dismount(actor, ox, oz)
            DR.state, DR.waitT = "return", 0
            toast("巨龙飞回了雪山之巅")
        end
    elseif DR.state == "return" then
        DR.waitT = DR.waitT + dt
        if DR.waitT > 1.5 then
            local to = DR.home - DR.pos
            local flat = math.sqrt(to.x * to.x + to.z * to.z)
            if flat > 2 then
                local want = math.deg(math.atan(to.x, to.z))
                local diff = (want - DR.yaw + 540) % 360 - 180
                DR.yaw = DR.yaw + math.max(-70 * dt, math.min(70 * dt, diff))
            end
            local step = math.min(flat, 28 * dt)
            local hy = flat > 30 and math.max(DR.home.y + 25, DR.ground(DR.pos.x, DR.pos.z) + 30) or DR.home.y
            local nx = DR.pos.x + (flat > 0 and to.x / flat * step or 0)
            local nz = DR.pos.z + (flat > 0 and to.z / flat * step or 0)
            local ny = DR.pos.y + (hy - DR.pos.y) * math.min(1, dt * .9)
            DR.pos = Vector3(nx, ny, nz)
            DR.place(0)
            if flat < 1.5 and math.abs(DR.pos.y - DR.home.y) < 1 then
                DR.pos, DR.yaw, DR.roll = DR.home, DR.homeYaw, 0
                for _, t in ipairs(DR.parts) do
                    t.position, t.rotation = DR.home, DR.homeRot
                end
                DR.state, DR.cool = "perch", 2
            end
        end
    end
    DR.jump = false
end

---- 绵羊：在草地上走走停停、低头吃草
local PAST = {{42.1,42.1,42.1,42.0,41.9,41.7,41.5,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.0,40.4,39.4,38.5,38.0,37.8,37.5,37.3,37.1},{42.0,41.9,41.9,41.9,41.9,41.8,41.6,41.2,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.0,40.4,39.5,38.7,38.4,38.1,37.9,37.7,37.5},{41.9,41.8,41.8,41.8,42.0,42.1,41.7,41.3,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,40.9,40.4,39.6,38.9,38.6,38.4,38.2,38.0,37.8},{41.8,41.8,41.8,41.8,42.1,42.3,42.0,41.4,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,40.8,40.3,39.6,39.1,38.9,38.7,38.5,38.3,38.1},{41.8,41.8,41.8,41.9,42.3,42.6,42.2,41.6,41.2,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.0,40.7,40.2,39.6,39.3,39.1,38.9,38.7,38.6,38.4},{41.8,41.8,41.8,42.0,42.4,42.7,42.4,41.8,41.4,41.2,41.1,41.1,41.1,41.1,41.1,41.1,41.1,41.0,40.8,40.5,40.1,39.7,39.5,39.3,39.1,39.0,38.8,38.7},{41.7,41.7,41.7,42.0,42.5,42.8,42.6,42.0,41.6,41.4,41.2,41.1,41.1,41.1,41.1,41.1,41.0,40.9,40.7,40.4,40.1,39.9,39.7,39.5,39.3,39.2,39.0,38.9},{41.7,41.6,41.7,42.1,42.7,42.8,42.6,42.2,41.9,41.7,41.5,41.4,41.3,41.2,41.2,41.1,41.1,40.9,40.7,40.5,40.3,40.1,39.9,39.7,39.5,39.3,39.2,39.0},{42.2,42.0,42.0,42.4,42.9,42.9,42.6,42.2,42.1,42.0,41.9,41.7,41.6,41.5,41.4,41.3,41.2,41.0,40.8,40.6,40.4,40.2,40.0,39.8,39.6,39.5,39.3,39.2},{42.9,42.7,42.6,42.8,43.1,43.0,42.7,42.4,42.3,42.2,42.2,42.1,41.9,41.8,41.7,41.5,41.3,41.1,40.9,40.7,40.5,40.3,40.1,39.9,39.8,39.6,39.5,39.3},{43.4,43.2,43.1,43.2,43.3,43.1,42.8,42.5,42.5,42.4,42.3,42.2,42.1,42.0,41.8,41.7,41.5,41.3,41.1,40.8,40.6,40.4,40.2,40.1,39.9,39.7,39.6,39.4},{43.5,43.4,43.3,43.4,43.5,43.3,43.0,42.8,42.7,42.6,42.5,42.4,42.3,42.1,42.0,41.8,41.6,41.4,41.2,41.0,40.7,40.5,40.3,40.2,40.0,39.8,39.7,39.5},{43.5,43.5,43.5,43.5,43.6,43.6,43.2,43.0,42.9,42.9,42.7,42.6,42.5,42.3,42.1,41.9,41.7,41.5,41.3,41.1,40.8,40.6,40.4,40.2,40.1,39.9,39.7,39.6},{43.5,43.5,43.5,43.6,43.8,43.8,43.5,43.3,43.2,43.1,43.0,42.8,42.7,42.5,42.3,42.1,41.8,41.6,41.4,41.2,40.9,40.7,40.5,40.3,40.1,40.0,39.8,39.7},{43.5,43.5,43.5,43.6,43.9,44.0,43.9,43.6,43.5,43.4,43.2,43.1,42.9,42.7,42.4,42.2,42.0,41.7,41.5,41.2,41.0,40.8,40.6,40.4,40.2,40.0,39.9,39.7},{43.5,43.5,43.5,43.6,43.9,44.3,44.2,44.0,43.8,43.7,43.5,43.3,43.1,42.8,42.6,42.3,42.1,41.8,41.6,41.3,41.1,40.9,40.6,40.4,40.2,40.1,39.9,39.8},{43.5,43.5,43.5,43.6,44.1,44.5,44.6,44.4,44.2,44.0,43.7,43.5,43.3,43.0,42.8,42.5,42.2,41.9,41.7,41.4,41.2,40.9,40.7,40.5,40.3,40.1,40.0,39.8},{43.5,43.5,43.5,43.7,44.3,44.9,45.0,44.8,44.5,44.3,44.0,43.8,43.5,43.2,42.9,42.6,42.3,42.0,41.8,41.5,41.2,41.0,40.8,40.5,40.3,40.2,40.0,39.9},{43.5,43.5,43.5,43.8,44.7,45.3,45.5,45.1,44.8,44.6,44.3,44.0,43.7,43.4,43.1,42.8,42.4,42.1,41.8,41.6,41.3,41.0,40.8,40.6,40.4,40.2,40.0,39.9},{43.5,43.5,43.5,44.2,45.1,45.8,45.9,45.6,45.2,44.9,44.5,44.2,43.9,43.5,43.2,42.9,42.5,42.2,41.9,41.6,41.3,41.1,40.8,40.6,40.4,40.2,40.1,39.9},{43.5,43.5,43.8,44.7,45.7,46.4,46.4,46.0,45.5,45.2,44.8,44.4,44.1,43.7,43.3,43.0,42.6,42.3,42.0,41.7,41.4,41.1,40.9,40.6,40.4,40.2,40.1,39.9},{43.5,43.7,44.4,45.6,46.7,47.1,46.8,46.4,45.9,45.4,45.0,44.6,44.2,43.8,43.4,43.1,42.7,42.4,42.0,41.7,41.4,41.1,40.9,40.6,40.4,40.2,40.0,39.9},{43.8,44.5,45.8,47.2,48.1,47.8,47.2,46.8,46.2,45.7,45.2,44.8,44.4,43.9,43.5,43.2,42.8,42.4,42.1,41.7,41.4,41.1,40.8,40.6,40.4,40.2,40.0,39.8},{44.9,46.2,47.8,49.4,49.7,48.7,47.7,47.1,46.5,45.9,45.4,44.9,44.5,44.0,43.6,43.2,42.8,42.4,42.1,41.7,41.4,41.1,40.8,40.5,40.3,40.1,39.9,39.7},{46.6,48.1,49.8,50.9,51.0,49.6,48.1,47.4,46.8,46.1,45.5,45.0,44.6,44.1,43.7,43.2,42.8,42.4,42.0,41.7,41.3,41.0,40.7,40.5,40.2,40.0,39.8,39.6},{47.8,49.2,50.3,51.1,51.2,49.6,48.0,47.4,46.9,46.4,45.8,45.2,44.6,44.2,43.7,43.3,42.8,42.4,42.0,41.6,41.3,40.9,40.6,40.3,40.1,39.8,39.6,39.4},{48.1,49.0,49.9,50.3,49.8,48.4,47.5,47.1,46.9,46.6,46.2,45.6,45.0,44.3,43.7,43.2,42.8,42.4,41.9,41.5,41.2,40.8,40.5,40.2,39.9,39.7,39.4,39.2},{48.3,48.8,49.2,49.0,48.2,47.4,47.0,46.8,46.8,46.7,46.5,46.2,45.7,44.9,44.0,43.2,42.7,42.3,41.9,41.4,41.0,40.7,40.3,40.0,39.7,39.5,39.2,39.0},{48.6,48.4,48.2,47.8,47.3,46.9,46.7,46.7,46.7,46.7,46.7,46.6,46.3,45.6,44.6,43.5,42.7,42.2,41.7,41.3,40.9,40.5,40.2,39.8,39.5,39.2,39.0,38.8},{49.2,48.1,47.4,47.1,46.8,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.3,45.4,44.1,42.8,42.1,41.6,41.2,40.7,40.3,39.9,39.6,39.3,39.0,38.7,38.5},{50.2,48.2,47.1,46.8,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.6,46.0,44.8,43.2,42.0,41.5,41.0,40.6,40.1,39.7,39.3,39.0,38.6,38.4,38.1},{51.3,48.4,46.9,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.5,45.4,43.7,42.1,41.3,40.8,40.4,39.9,39.5,39.0,38.7,38.3,38.0,37.7},{51.9,48.3,46.8,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,45.8,44.1,42.2,41.2,40.6,40.1,39.6,39.2,38.7,38.3,37.9,37.6,37.3},{52.2,48.2,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.1,44.5,42.4,41.0,40.4,39.9,39.4,38.9,38.4,37.9,37.5,37.1,36.8},{52.5,48.1,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.7,46.1,44.6,42.7,41.2,40.4,39.7,39.1,38.5,38.0,37.5,37.0,36.7,36.3}}
local function pastH(x, z)
    local fx, fz = (x - 70) / 2, (z - 30) / 2
    local ix = math.max(0, math.min(26, math.floor(fx)))
    local iz = math.max(0, math.min(33, math.floor(fz)))
    fx, fz = fx - ix, fz - iz
    local a, b = PAST[iz + 1], PAST[iz + 2]
    return (a[ix + 1] * (1 - fx) + a[ix + 2] * fx) * (1 - fz) + (b[ix + 1] * (1 - fx) + b[ix + 2] * fx) * fz
end
local sheep = nil
local function setupSheep()
    sheep = {}
    for i = 0, 8 do
        local go = GameObject.Find("sheep_" .. i)
        if go then
            local t = go.transform
            local pos = t.position
            local s = { go = go, t = t, an = nil, x = pos.x, z = pos.z, hx = pos.x, hz = pos.z, yaw = math.random() * 360, state = "idle", timer = 1 + math.random() * 3 }
            sheep[#sheep + 1] = s
        end
    end
end
local function sheepNext(s)
    local r = math.random()
    if r < .45 then
        s.state = "graze"
        s.timer = 8
        if s.an then fadeAnim(s.go, s.an, "graze") end
    elseif r < .68 then
        s.state = "idle"
        s.timer = 3 + math.random() * 4
        if s.an then fadeAnim(s.go, s.an, "idle") end
    else
        s.state = "walk"
        local a, d = math.random() * 6.283, 3 + math.random() * 8
        s.tx = math.max(72, math.min(122, s.hx + math.cos(a) * d))
        s.tz = math.max(32, math.min(96, s.hz + math.sin(a) * d))
        s.timer = 20
        if s.an then fadeAnim(s.go, s.an, "walk") end
    end
end
local function updateSheep(p)
    if sheep == nil then setupSheep() end
    local dt = Time.deltaTime
    for _, s in ipairs(sheep) do
        if s.an == nil then
            s.an = s.go:GetComponent(typeof(UnityEngine.Animation))
            if s.an then
                pcall(function()
                    s.an.wrapMode = UnityEngine.WrapMode.Loop
                    for _, c in ipairs({ "idle", "walk", "graze" }) do
                        s.an:GetClip(c).wrapMode = UnityEngine.WrapMode.Loop
                    end
                end)
                fadeAnim(s.go, s.an, "idle")
            end
        end
        s.timer = s.timer - dt
        if s.state == "walk" then
            local dx, dz = s.tx - s.x, s.tz - s.z
            local d = math.sqrt(dx * dx + dz * dz)
            if d < .25 or s.timer <= 0 then
                sheepNext(s)
            else
                local want = math.deg(math.atan(dx, dz))
                local diff = (want - s.yaw + 540) % 360 - 180
                s.yaw = s.yaw + math.max(-100 * dt, math.min(100 * dt, diff))
                local sp = .85 * dt * (math.abs(diff) < 50 and 1 or .3)
                s.x = s.x + math.sin(math.rad(s.yaw)) * sp
                s.z = s.z + math.cos(math.rad(s.yaw)) * sp
            end
        elseif s.timer <= 0 then
            sheepNext(s)
        end
        s.t.position = Vector3(s.x, pastH(s.x, s.z), s.z)
        s.t.rotation = Quaternion.Euler(Vector3(0, s.yaw + 180, 0))
    end
end

---- 松林：近处显示细致的真实松枝，远处只留低模
local PINE_CHUNKS = {{42.7,21.0},{36.5,38.4},{24.3,67.5},{41.0,67.8},{16.1,93.5},{18.9,115.1},{41.5,96.5},{42.2,119.6},{70.0,11.3},{67.4,28.9},{73.5,63.8},{68.1,116.2},{100.5,14.3},{160.1,28.4},{94.3,89.6},{137.6,102.0},{11.5,144.7},{12.1,170.5},{41.9,154.6},{46.8,177.6},{24.5,193.2},{54.3,193.5},{23.2,211.0},{55.3,214.3},{75.5,156.7},{124.6,161.8},{75.9,228.2},{108.1,215.7},{184.2,165.1},{187.6,183.1},{183.8,200.3},{203.8,205.9}}
local pineList = nil
local pineNext = 0
local function updateForest(p)
    if pineList == nil then
        pineList = {}
        for i, c in ipairs(PINE_CHUNKS) do
            local go = GameObject.Find("pn_" .. (i - 1))
            if go then
                pineList[#pineList + 1] = { go = go, x = c[1], z = c[2], on = true }
            end
        end
    end
    pineNext = pineNext - Time.deltaTime
    if pineNext > 0 then return end
    pineNext = .4
    for _, c in ipairs(pineList) do
        local on = dist2d(p, c.x, c.z) < 70
        if on ~= c.on then
            c.on = on
            c.go:SetActive(on)
        end
    end
end


local function updateSites(actor)
    local p = actor.position
    updateAnimPending()
    updateFire(p)
    updateMush(actor, p)
    updateAltar(p)
    updateDragon()
    updateMount(actor, p)
    updateHolyLight()
    updateRooms(p)
    updateSheep(p)
    updateForest(p)
    updateClouds()
    updateBoats(actor, p)
    DR.update(actor, p)
end

local castleRetry = 0
-- @@UI BEGIN
---------------------------------------------------------------- 界面：标题页、序章古书、地图（全部放在 UI 表里，主块只占一个局部变量）
-- 贴图来自藏在地下的 ui_* 方片模型，音效在运行时合成。
local UI = { state = "boot", t = 0, wait = 0, cardId = nil }
-- Loaded inline into the existing UI table to avoid Lua's top-level local limit.
UI.foliage = { items = {}, next = 0, names = {"pl_tree_0","pl_tree_1","pl_tree_2","pl_tree_3","pl_tree_4","pl_tree_5","pl_tree_6","pl_tree_7","pl_tree_8","pl_tree_9","pl_tree_10","pl_tree_11","pl_tree_12","pl_tree_13","pl_tree_14","pl_tree_15","pl_tree_16","pl_tree_17","pl_tree_18","pl_tree_19","pl_tree_20","pl_tree_21","pl_tree_22","pl_tree_23","pl_tree_24","pl_tree_25","pl_tree_26","pl_tree_27","pl_tree_28","pl_tree_29","pl_tree_30","pl_tree_31","pl_tree_32","pl_tree_33","pl_tree_34","pl_tree_35","pl_tree_36","pl_tree_37","pl_tree_38","pl_tree_39","pl_tree_40","pl_tree_41","pl_tree_42","pl_tree_43","pl_tree_44","pl_tree_45","pl_tree_46","pl_tree_47","pl_tree_48","pl_tree_49","pl_tree_50","pl_tree_51","pl_tree_52","pl_tree_53","pl_tree_54","pl_tree_55","pl_tree_56","pl_tree_57","pl_tree_58","pl_tree_59","pl_tree_60","pl_tree_61","pl_tree_62","pl_tree_63","pl_tree_64","pl_tree_65","pl_tree_66","pl_tree_67","pl_tree_68","pl_tree_69","pl_tree_70","pl_tree_71","pl_tree_72","pl_tree_73","pl_tree_74","pl_tree_75","pl_tree_76","pl_tree_77","pl_tree_78","pl_tree_79","pl_tree_80","pl_tree_81","pl_tree_82","pl_tree_83","pl_tree_84","pl_tree_85","pl_tree_86","pl_tree_87","pl_tree_88","pl_tree_89","pl_tree_90","pl_tree_91","pl_tree_92","pl_tree_93","pl_tree_94","pl_tree_95","pl_tree_96","pl_tree_97","pl_tree_98","pl_tree_99","pl_tree_100","pl_tree_101","pl_tree_102","pl_tree_103","pl_tree_104","pl_tree_105","pl_tree_106","pl_tree_107","pl_tree_108","pl_tree_109","pl_tree_110","pl_tree_111","pl_tree_112","pl_tree_113","pl_tree_114","pl_tree_115","pl_tree_116","pl_tree_117","pl_tree_118","pl_tree_119","pl_tree_120","pl_tree_121","pl_tree_122","pl_tree_123","pl_tree_124","pl_tree_125","pl_tree_126","pl_tree_127","pl_tree_128","pl_tree_129","pl_tree_130","pl_tree_131","pl_tree_132","pl_tree_133","pl_tree_134","pl_tree_135","pl_tree_136","pl_tree_137","pl_tree_138","pl_tree_139","pl_tree_140","pl_tree_141","pl_tree_142","pl_tree_143","pl_tree_144","pl_tree_145","pl_tree_146","pl_tree_147","pl_tree_148","pl_tree_149","pl_tree_150","pl_tree_151","pl_tree_152","pl_tree_153","pl_tree_154","pl_tree_155","pl_tree_156","pl_tree_157","pl_tree_158","pl_tree_159","pl_tree_160","pl_tree_161","pl_tree_162","pl_tree_163","pl_tree_164","pl_tree_165","pl_tree_166","pl_tree_167","pl_tree_168","pl_tree_169","pl_tree_170","pl_tree_171","pl_tree_172"} }
function UI.updateFoliage(actor)
    local f=UI.foliage
    for _=1,2 do
        if f.next>=#f.names then break end
        f.next=f.next+1
        local go=GameObject.Find(f.names[f.next])
        if go then
            local ts=go:GetComponentsInChildren(typeof(UnityEngine.Transform),true)
            for i=0,ts.Length-1 do
                local t=ts[i]
                if t.name=='Leaves' then
                    -- Leaf volumes only sense proximity: triggers never block the player.
                    -- Trunk colliders are outside this subtree and stay solid.
                    local meshes=t.gameObject:GetComponentsInChildren(typeof(UnityEngine.MeshFilter),true)
                    for j=0,meshes.Length-1 do
                        local mf=meshes[j]
                        if mf.sharedMesh and not mf.gameObject:GetComponent(typeof(UnityEngine.Collider)) then
                            local mc=mf.gameObject:AddComponent(typeof(UnityEngine.MeshCollider))
                            mc.sharedMesh=mf.sharedMesh;mc.convex=true;mc.isTrigger=true
                        end
                    end
                    local cols=t.gameObject:GetComponentsInChildren(typeof(UnityEngine.Collider),true)
                    for j=0,cols.Length-1 do
                        local mc=cols[j].gameObject:GetComponent(typeof(UnityEngine.MeshCollider))
                        if mc then mc.convex=true end
                        cols[j].enabled=true;cols[j].isTrigger=true
                    end
                    -- Keep the authored attachment rigidly anchored. A dynamic canopy
                    -- with a world spring can drift after controller/physics contacts.
                    local joints=t.gameObject:GetComponents(typeof(UnityEngine.ConfigurableJoint))
                    for j=0,joints.Length-1 do UnityEngine.Object.Destroy(joints[j]) end
                    local rb=t.gameObject:GetComponent(typeof(UnityEngine.Rigidbody))
                    if not rb then rb=t.gameObject:AddComponent(typeof(UnityEngine.Rigidbody)) end
                    rb.useGravity=false;rb.isKinematic=true;rb.detectCollisions=true
                    f.items[#f.items+1]={t=t,rb=rb,cols=cols,home=t.localPosition,rot=t.localRotation,x=0,z=0,vx=0,vz=0}
                end
            end
        end
    end
    if f.next>=#f.names and not f.ready then f.ready=true;report('soft anchored canopies ready '..#f.items) end
    local p=actor.position+Vector3(0,1,0)
    local dt=math.min(Time.deltaTime,.033)
    for _,v in ipairs(f.items) do
        local tx,tz=0,0
        -- Always restore the local attachment, even after external teleports or bumps.
        v.t.localPosition=v.home
        if Vector3.Distance(v.t.position,p)<24 then
            local distance=100
            for j=0,v.cols.Length-1 do
                if v.cols[j].enabled then distance=math.min(distance,Vector3.Distance(v.cols[j]:ClosestPoint(p),p)) end
            end
            if distance<.7 then
                local away=v.t.position-p;away.y=0
                if away.sqrMagnitude>.001 then
                    local dir=v.t.parent and v.t.parent:InverseTransformDirection(away.normalized) or away.normalized
                    local amount=(1-distance/.7)*7
                    if not f.contactLogged then f.contactLogged=true;report("foliage soft contact active") end
                    tx=dir.z*amount;tz=-dir.x*amount
                end
            end
        end
        -- Damped angular response only: no translation or accumulating impulses.
        v.vx=v.vx+((tx-v.x)*55-v.vx*15)*dt
        v.vz=v.vz+((tz-v.z)*55-v.vz*15)*dt
        v.x=math.max(-7,math.min(7,v.x+v.vx*dt))
        v.z=math.max(-7,math.min(7,v.z+v.vz*dt))
        v.t.localRotation=v.rot*Quaternion.Euler(v.x,0,v.z)
    end
end

UI.reeds={names={"golden_geometry_0","golden_geometry_1","golden_geometry_2","golden_geometry_3","golden_geometry_4","golden_geometry_5","golden_geometry_6","golden_geometry_7","golden_geometry_8","golden_geometry_9","golden_geometry_10","golden_geometry_11","golden_geometry_12","golden_geometry_13","golden_geometry_14","golden_geometry_15","golden_geometry_16","golden_geometry_17","golden_geometry_18","golden_geometry_19","golden_geometry_20","golden_geometry_21","golden_geometry_22","golden_geometry_23","golden_geometry_24","golden_geometry_25","golden_geometry_26","golden_geometry_27","golden_geometry_28","golden_geometry_29","golden_geometry_30","golden_geometry_31","golden_geometry_32","golden_geometry_33","golden_geometry_34","golden_geometry_35","golden_geometry_36","golden_geometry_37","golden_geometry_38","golden_geometry_39","golden_geometry_40","golden_geometry_41","golden_geometry_42","golden_geometry_43","golden_geometry_44","golden_geometry_45","golden_geometry_46","golden_geometry_47","golden_geometry_48","golden_geometry_49","golden_geometry_50","golden_geometry_51","golden_geometry_52","golden_geometry_53","golden_geometry_54","golden_geometry_55","golden_geometry_56","golden_geometry_57","golden_geometry_58","golden_geometry_59","golden_geometry_60","golden_geometry_61","golden_geometry_62","golden_geometry_63","golden_geometry_64","golden_geometry_65","golden_geometry_66","golden_geometry_67","golden_geometry_68","golden_geometry_69","golden_geometry_70","golden_geometry_71","golden_geometry_72","golden_geometry_73","golden_geometry_74","golden_geometry_75","golden_geometry_76","golden_geometry_77","golden_geometry_78","golden_geometry_79","golden_geometry_80","golden_geometry_81","golden_geometry_82","golden_geometry_83","golden_geometry_84","golden_geometry_85","golden_geometry_86","golden_geometry_87","golden_geometry_88","golden_geometry_89","golden_geometry_90","golden_geometry_91","golden_geometry_92","golden_geometry_93","golden_geometry_94","golden_geometry_95","golden_geometry_96","golden_geometry_97","golden_geometry_98","golden_geometry_99","golden_geometry_100","golden_geometry_101","golden_geometry_102","golden_geometry_103","golden_geometry_104","golden_geometry_105","golden_geometry_106","golden_geometry_107","golden_geometry_108","golden_geometry_109","golden_geometry_110","golden_geometry_111","golden_geometry_112","golden_geometry_113","golden_geometry_114","golden_geometry_115","golden_geometry_116","golden_geometry_117","golden_geometry_118","golden_geometry_119","golden_geometry_120","golden_geometry_121","golden_geometry_122","golden_geometry_123","golden_geometry_124","golden_geometry_125","golden_geometry_126","golden_geometry_127","golden_geometry_128","golden_geometry_129","golden_geometry_130","golden_geometry_131","golden_geometry_132","golden_geometry_133","golden_geometry_134","golden_geometry_135","golden_geometry_136","golden_geometry_137","golden_geometry_138","golden_geometry_139","golden_geometry_140","golden_geometry_141","golden_geometry_142","golden_geometry_143","golden_geometry_144","golden_geometry_145","golden_geometry_146","golden_geometry_147","golden_geometry_148","golden_geometry_149"},items={},next=0,tick=0}
function UI.updateReeds(actor)
    local f=UI.reeds
    if f.next<#f.names then
        for _=1,5 do
            f.next=f.next+1
            local name=f.names[f.next]
            if not name then break end
            local go=GameObject.Find(name)
            if go then
                local an=go:GetComponentInChildren(typeof(UnityEngine.Animation),true)
                if an then an:Stop();an.enabled=false end
                if name:match('^golden_geometry_') then
                    local rs=go:GetComponentsInChildren(typeof(UnityEngine.Renderer),true)
                    local tone=(tonumber(name:match('(%d+)$')) or 0)%4
                    f.geometryMats=f.geometryMats or {}
                    for ri=0,rs.Length-1 do
                        if not f.geometryMats[tone] then
                            local sh=UnityEngine.Shader.Find('Universal Render Pipeline/Lit')
                            local m=sh and UnityEngine.Material(sh) or UnityEngine.Material(rs[ri].sharedMaterial)
                            local c=UnityEngine.Color(.58+tone*.035,.43+tone*.03,.21+tone*.023,1)
                            for _,key in ipairs({'_BaseColor','_Color'}) do if m:HasProperty(key) then m:SetColor(key,c) end end
                            m:SetFloat('_Cull',0);m:SetFloat('_Smoothness',.1)
                            f.geometryMats[tone]=m
                        end
                        rs[ri].sharedMaterial=f.geometryMats[tone]
                    end
                end
                if not name:match('^golden_geometry_') then
                -- The editor replaces imported glTF cutout materials with its opaque shader.
                -- Preserve the atlas and explicitly restore alpha clipping for runtime foliage.
                local rs=go:GetComponentsInChildren(typeof(UnityEngine.Renderer),true)
                for ri=0,rs.Length-1 do
                    local src=rs[ri].sharedMaterial
                    local tex=nil
                    for _,key in ipairs({'_BaseTex','_BaseMap','_MainTex'}) do
                        if src:HasProperty(key) then tex=src:GetTexture(key);if tex then break end end
                    end
                    if not f.material and tex then
                        local sh=UnityEngine.Shader.Find('Universal Render Pipeline/Lit')
                        if not sh then sh=UnityEngine.Shader.Find('Legacy Shaders/Transparent/Cutout/Diffuse') end
                        if sh then
                            local m=UnityEngine.Material(sh)
                            for _,key in ipairs({'_BaseMap','_MainTex'}) do if m:HasProperty(key) then m:SetTexture(key,tex) end end
                            for _,key in ipairs({'_BaseColor','_Color'}) do if m:HasProperty(key) then m:SetColor(key,UnityEngine.Color(1,1,1,1)) end end
                            m:SetFloat('_AlphaClip',1);m:SetFloat('_Cutoff',.35);m:SetFloat('_Cull',0);m:SetFloat('_Surface',0)
                            m:SetFloat('_ZWrite',1);m:SetFloat('_Smoothness',.15)
                            m:EnableKeyword('_ALPHATEST_ON');m:SetOverrideTag('RenderType','TransparentCutout');m.renderQueue=2450
                            f.material=m;report('reed cutout shader '..sh.name)
                        end
                    end
                    if f.material then rs[ri].sharedMaterial=f.material end
                end
                end
                local ts=go:GetComponentsInChildren(typeof(UnityEngine.Transform),true)
                local lower,upper
                for j=0,ts.Length-1 do
                    if ts[j].name=='reed_lower' then lower=ts[j] end
                    if ts[j].name=='reed_upper' then upper=ts[j] end
                end
                if lower and upper then
                    local cols=go:GetComponentsInChildren(typeof(UnityEngine.Collider),true)
                    for j=0,cols.Length-1 do cols[j].enabled=false end
                    f.items[#f.items+1]={root=go.transform,lo=lower,hi=upper,lr=lower.localRotation,hr=upper.localRotation,x=0,z=0,vx=0,vz=0,phase=go.transform.position.x*.32+go.transform.position.z*.22}
                end
            end
        end
        if f.next>=#f.names then report('reeds ready '..#f.items..'/'..#f.names) end
    end
    f.tick=f.tick+1
    local p=actor.position
    local dt=math.min(Time.deltaTime,.033)
    for i,v in ipairs(f.items) do
        local rp=v.root.position
        local dx,dz=rp.x-p.x,rp.z-p.z
        local d2=dx*dx+dz*dz
        if d2<144 or (i+f.tick)%6==0 then
            local tx,tz=0,0
            if d2<4 and math.abs(rp.y-p.y)<2.5 then
                local dist=math.sqrt(d2)
                local dir=v.root:InverseTransformDirection(Vector3(dx/math.max(.05,dist),0,dz/math.max(.05,dist)))
                local strength=(1-math.min(1,dist/2))
                tx=dir.z*32*strength;tz=-dir.x*32*strength
                if not f.contactLogged and strength>.3 then f.contactLogged=true;report('reeds contact bend active') end
            end
            v.vx=v.vx+((tx-v.x)*45-v.vx*10)*dt
            v.vz=v.vz+((tz-v.z)*45-v.vz*10)*dt
            v.x=v.x+v.vx*dt;v.z=v.z+v.vz*dt
            local wind=math.sin(Time.time*1.1+v.phase)*2.2+math.sin(Time.time*.43+v.phase*.45)*1.1
            v.lo.localRotation=v.lr*Quaternion.Euler(v.x+wind,0,v.z+wind*.42)
            v.hi.localRotation=v.hr*Quaternion.Euler(v.x*.65+wind*1.4,0,v.z*.65+math.sin(Time.time*1.6+v.phase)*1.7)
        end
    end
end

-- Runtime-only visual changes: retain every authored scene transform.
UI.motion={}
function UI.setupMotion()
    local state=UI.motion
    if not skyReady then return end
    if not state.sky then
        local shader=UnityEngine.Shader.Find('Universal Render Pipeline/Unlit')
        local urp=shader~=nil
        if not shader then shader=UnityEngine.Shader.Find('Unlit/Transparent') end
        assert(shader,'No transparent sky shader available')
        state.sky={}
        for _,go in ipairs(dayObjects) do go:SetActive(true) end
        for _,go in ipairs(nightObjects) do
            go:SetActive(true)
            local isSwirl=string.sub(go.name,1,10)=='sky_swirl_'
            if isSwirl then go.transform.localScale=go.transform.localScale*1.25 end
            local rs=go:GetComponentsInChildren(typeof(UnityEngine.Renderer),true)
            for i=0,rs.Length-1 do
                local old=rs[i].material
                local m=UnityEngine.Material(shader)
                local tex=nil
                for _,key in ipairs({'_BaseTex','_BaseMap','_MainTex'}) do
                    if old:HasProperty(key) then tex=old:GetTexture(key);if tex then break end end
                end
                if not tex then tex=old.mainTexture end
                assert(tex,'Missing sky texture: '..go.name)
                m:SetTexture(urp and '_BaseMap' or '_MainTex',tex)
                m:SetColor(urp and '_BaseColor' or '_Color',Color(1,1,1,1))
                if urp then
                    m:SetFloat('_Surface',1);m:SetFloat('_Blend',0)
                    m:SetFloat('_SrcBlend',5);m:SetFloat('_DstBlend',10);m:SetFloat('_ZWrite',0)
                    m:SetFloat('_Cull',0);m:EnableKeyword('_SURFACE_TYPE_TRANSPARENT')
                end
                -- Dome bounds are centred near the camera, so distance sorting can
                -- incorrectly draw the opaque night dome over the distant vortex.
                local queues={sky_dome2=2990,sky_moon2=2991,sky_swirl_a=2992,sky_swirl_b=2993,sky_swirl_c=2994}
                m.renderQueue=queues[go.name] or 3000
                if isSwirl then report('sky layer '..go.name..' tex='..tex.name..' bounds='..tostring(rs[i].bounds)..' shader='..old.shader.name) end
                rs[i].material=m
                state.sky[#state.sky+1]={m=m,prop=urp and '_BaseColor' or '_Color',gain=isSwirl and 1.8 or 1}
            end
        end
        SWIRL_LAYERS.fade=function(t)
            for _,v in ipairs(state.sky) do v.m:SetColor(v.prop,Color(v.gain,v.gain,v.gain,1-t)) end
        end
        SWIRL_LAYERS.fade(blend*blend*(3-2*blend))
        report('sky crossfade ready '..#state.sky)
    end
    if not state.rotor then
        local go=GameObject.Find('windmill')
        if not go then return end
        local fs=go:GetComponentsInChildren(typeof(UnityEngine.MeshFilter),true)
        for k=0,fs.Length-1 do
            local mf=fs[k]
            if mf.gameObject.name=='main' then
                local mesh=mf.mesh
                local vertices=mesh.vertices
                local tris=mesh.triangles
                local factor=mesh.bounds.size.y/22.301563262939453
                local oy=mesh.bounds.min.y+2*factor
                local oz=mesh.bounds.center.z
                -- Identify disconnected boxes, welding UV seams for connectivity.
                local parents,keys={},{}
                local function find(i)
                    while parents[i]~=i do parents[i]=parents[parents[i]];i=parents[i] end
                    return i
                end
                for i=0,vertices.Length-1 do
                    local v=vertices[i]
                    local key=string.format('%.5f,%.5f,%.5f',v.x/factor,(v.y-oy)/factor,(v.z-oz)/factor)
                    parents[i]=keys[key] or i;keys[key]=parents[i]
                end
                for i=0,tris.Length-1,3 do
                    local a,b,c=find(tris[i]),find(tris[i+1]),find(tris[i+2]);parents[b]=a;parents[c]=a
                end
                local bounds={}
                for i=0,vertices.Length-1 do
                    local id=find(i);local v=vertices[i];local z=(v.z-oz)/factor;local y=(v.y-oy)/factor
                    local b=bounds[id] or {lo=1e9,hi=-1e9,y=1e9};bounds[id]=b
                    b.lo=math.min(b.lo,z);b.hi=math.max(b.hi,z);b.y=math.min(b.y,y)
                end
                local fixed,moving={},{}
                for i=0,tris.Length-1,3 do
                    local b=bounds[find(tris[i])]
                    local dst=(((b.lo>3.79 and b.hi<4.11) or (b.lo> -4.11 and b.hi< -3.79)) and b.y>2.4) and moving or fixed
                    dst[#dst+1]=tris[i];dst[#dst+1]=tris[i+1];dst[#dst+1]=tris[i+2]
                end
                assert(#moving>100 and #fixed>100,'Rotor geometry not identified')
                local function array(t)
                    local a=CS.System.Array.CreateInstance(typeof(CS.System.Int32),#t)
                    for i=1,#t do a[i-1]=t[i] end
                    return a
                end
                local rotating=UnityEngine.Object.Instantiate(mesh)
                mesh.triangles=array(fixed);rotating.triangles=array(moving)
                local rotorZ=0
                for _,idx in ipairs(moving) do rotorZ=rotorZ+vertices[idx].z end
                rotorZ=rotorZ/#moving
                local pivot=GameObject('windmill_rotor_pivot');pivot.transform:SetParent(mf.transform,false)
                pivot.transform.localPosition=Vector3(mesh.bounds.center.x,oy+11.4*factor,rotorZ)
                local rotor=GameObject('windmill_rotor');rotor.transform:SetParent(pivot.transform,false)
                rotor.transform.localPosition=-pivot.transform.localPosition
                rotor:AddComponent(typeof(UnityEngine.MeshFilter)).sharedMesh=rotating
                rotor:AddComponent(typeof(UnityEngine.MeshRenderer)).sharedMaterials=mf.gameObject:GetComponent(typeof(UnityEngine.MeshRenderer)).sharedMaterials
                local coll=mf.gameObject:GetComponent(typeof(UnityEngine.MeshCollider));if coll then coll.sharedMesh=mesh end
                state.rotor=pivot.transform
                report('windmill rotor ready triangles='..#moving/3)
                break
            end
        end
    end
end
function UI.updateMotion()
    if not UI.motion.ready and not UI.motion.failed then
        local ok,err=pcall(UI.setupMotion)
        if not ok then UI.motion.failed=true;report('motion failed '..tostring(err))
        elseif UI.motion.rotor then UI.motion.ready=true end
    end
    if UI.motion.rotor then UI.motion.rotor:Rotate(0,0,18*Time.deltaTime) end
end

UI.L = { title = { frames = { { 0, 0.707031, 1, 0.292969 }, { 0, 0.414062, 1, 0.292969 }, { 0, 0.121094, 1, 0.292969 } }, sub = { 0, 0, 1, 0.121094 }, aspect = 3.413333, sub_aspect = 8.258065 }, book = { aspect = 1.505882, left = { 0.0625, 0.058824, 0.433594, 0.876471 }, right = { 0.503906, 0.058824, 0.433594, 0.876471 } }, map = { M = 120, S = 5, size = 1520 }, atlas = { mapbtn = { 0.0, 0.75, 0.25, 0.25 }, arrow = { 0.25, 0.875, 0.125, 0.125 }, ring = { 0.375, 0.875, 0.125, 0.125 }, skip = { 0.5, 0.917969, 0.21875, 0.082031 }, close = { 0.75, 0.917969, 0.21875, 0.082031 }, hint_flip = { 0.0, 0.6875, 0.5, 0.0625 }, hint_map = { 0.5, 0.6875, 0.5, 0.0625 }, vignette = { 0.0, 0.375, 0.25, 0.25 }, grain = { 0.25, 0.375, 0.25, 0.25 } }, cards = { castle = { 1, 0.0, 0.800781, 0.5, 0.199219 }, dragon_peak = { 1, 0.5, 0.800781, 0.5, 0.199219 }, altar = { 1, 0.0, 0.601562, 0.5, 0.199219 }, spawn = { 1, 0.5, 0.601562, 0.5, 0.199219 }, village = { 1, 0.0, 0.402344, 0.5, 0.199219 }, rift_gate = { 1, 0.5, 0.402344, 0.5, 0.199219 }, arena = { 1, 0.0, 0.203125, 0.5, 0.199219 }, bridge = { 1, 0.5, 0.203125, 0.5, 0.199219 }, witch = { 1, 0.0, 0.003906, 0.5, 0.199219 }, windmill = { 1, 0.5, 0.003906, 0.5, 0.199219 }, camp = { 2, 0.0, 0.800781, 0.5, 0.199219 }, mushroom = { 2, 0.5, 0.800781, 0.5, 0.199219 }, flowers = { 2, 0.0, 0.601562, 0.5, 0.199219 }, glow_tree = { 2, 0.5, 0.601562, 0.5, 0.199219 }, carpet = { 2, 0.0, 0.402344, 0.5, 0.199219 }, lighthouse = { 2, 0.5, 0.402344, 0.5, 0.199219 }, harbor = { 2, 0.0, 0.203125, 0.5, 0.199219 }, meadow = { 2, 0.5, 0.203125, 0.5, 0.199219 }, lake = { 2, 0.0, 0.003906, 0.5, 0.199219 } }, card_aspect = 2.509804, poi = { { id = "castle", x = 127, z = 182, lx = 45.4, ly = 15.5, lw = 43.6, lh = 21.2 }, { id = "dragon_peak", x = 165, z = 234, lx = 41.4, ly = -5.5, lw = 43.6, lh = 21.2 }, { id = "altar", x = 48, z = 150, lx = 52.6, ly = -5.5, lw = 54.7, lh = 21.2 }, { id = "spawn", x = 121, z = 57, lx = 44.1, ly = -16.1, lw = 43.6, lh = 21.2 }, { id = "village", x = 184, z = 80, lx = -44.1, ly = 8.9, lw = 43.6, lh = 21.2 }, { id = "rift_gate", x = 125, z = 135, lx = -61.8, ly = 2.1, lw = 46.8, lh = 19.2 }, { id = "arena", x = 127, z = 160, lx = -46.1, ly = -1.8, lw = 37.6, lh = 19.2 }, { id = "bridge", x = 162, z = 110, lx = 26.3, ly = -3.2, lw = 28.4, lh = 19.2 }, { id = "witch", x = 171, z = 146, lx = 44.7, ly = -3.2, lw = 46.8, lh = 19.2 }, { id = "windmill", x = 84, z = 66, lx = 35.5, ly = -3.2, lw = 37.6, lh = 19.2 }, { id = "camp", x = 62, z = 62, lx = -13.2, ly = -20.3, lw = 56.1, lh = 19.2 }, { id = "mushroom", x = 86, z = 98, lx = 35.5, ly = -3.2, lw = 37.6, lh = 19.2 }, { id = "flowers", x = 150, z = 62, lx = 55.3, ly = -8.4, lw = 56.1, lh = 19.2 }, { id = "glow_tree", x = 160, z = 74, lx = 46.1, ly = -13.7, lw = 46.8, lh = 19.2 }, { id = "carpet", x = 96, z = 30, lx = 44.7, ly = -3.2, lw = 46.8, lh = 19.2 }, { id = "lighthouse", x = 209, z = 134, lx = 35.5, ly = -3.2, lw = 37.6, lh = 19.2 }, { id = "harbor", x = 192, z = 86, lx = 27.6, ly = -15.0, lw = 28.4, lh = 19.2 }, { id = "meadow", x = 96, z = 50, lx = -44.7, ly = -17.6, lw = 37.6, lh = 19.2 }, { id = "lake", x = 116, z = 124, lx = 38.2, ly = -15.0, lw = 28.4, lh = 19.2 } } }
UI.TEX_NAMES = { "ui_title", "ui_book", "ui_pages1", "ui_pages2", "ui_pages3", "ui_map", "ui_atlas", "ui_cards1", "ui_cards2" }
UI.CAM_A = Vector3(148, 52, 86)
UI.CAM_B = Vector3(112, 57, 96)
UI.CAM_LOOK = Vector3(127, 95, 186)

function UI.log(msg)
    CS.UnityEngine.Debug.LogError("[ui] " .. msg)
end

function UI.V2(x, y)
    return UnityEngine.Vector2(x, y)
end

function UI.R(u)
    return UnityEngine.Rect(u[1], u[2], u[3], u[4])
end

-- 屏幕点 → 以画面中心为原点、高 1080 的画布坐标
function UI.canvasPos(m)
    local s = 1080 / UnityEngine.Screen.height
    return (m.x - UnityEngine.Screen.width / 2) * s, (m.y - UnityEngine.Screen.height / 2) * s
end

function UI.halfW()
    return UnityEngine.Screen.width * 540 / UnityEngine.Screen.height
end

function UI.tapped()
    if Input.GetMouseButtonDown(0) then
        return UI.canvasPos(Input.mousePosition)
    end
    return nil
end

---------------------------------------------------------------- 贴图
function UI.findTextures()
    UI.tex = UI.tex or {}
    local all = true
    for _, n in ipairs(UI.TEX_NAMES) do
        if UI.tex[n] == nil then
            local go = UnityEngine.GameObject.Find(n)
            local t = nil
            if go ~= nil then
                local r = go:GetComponentInChildren(typeof(UnityEngine.Renderer))
                if r ~= nil then
                    local m = r.sharedMaterial
                    for _, p in ipairs({ "_BaseTex", "_BaseMap", "_MainTex" }) do
                        if t == nil and m:HasProperty(p) then t = m:GetTexture(p) end
                    end
                end
            end
            if t ~= nil then
                UI.tex[n] = t
                t.wrapMode = UnityEngine.TextureWrapMode.Clamp
                go:SetActive(false)
            else
                all = false
            end
        end
    end
    return all
end

function UI.makeGrain()
    local n = 128
    local t = UnityEngine.Texture2D(n, n)
    local cols = {}
    for i = 1, n * n do
        local v = math.random()
        local c = v > .5 and 1 or 0
        cols[i] = UnityEngine.Color(c, c, c, math.abs(v - .5) * 1.2)
    end
    t:SetPixels(cols)
    t:Apply()
    t.wrapMode = UnityEngine.TextureWrapMode.Repeat
    t.filterMode = UnityEngine.FilterMode.Point
    return t
end

---------------------------------------------------------------- 搭界面的小工具
function UI.node(parent, name, full)
    local go = UnityEngine.GameObject(name)
    local rt = go:AddComponent(typeof(UnityEngine.RectTransform))
    rt:SetParent(parent, false)
    if full then
        rt.anchorMin = UI.V2(0, 0)
        rt.anchorMax = UI.V2(1, 1)
        rt.sizeDelta = UI.V2(0, 0)
    end
    return go, rt
end

function UI.panel(name)
    local go, rt = UI.node(UI.root.transform, name, true)
    local cg = go:AddComponent(typeof(UnityEngine.CanvasGroup))
    cg.alpha = 0
    cg.blocksRaycasts = false
    go:SetActive(false)
    return { go = go, rt = rt, cg = cg }
end

-- 图片：tex 为空时是纯色块；uv 为 {x,y,w,h}；默认以父节点中心为锚点
function UI.img(parent, tex, uv, w, h, x, y, color)
    local go, rt = UI.node(parent, "img", false)
    local ri = go:AddComponent(typeof(UnityEngine.UI.RawImage))
    if tex ~= nil then ri.texture = tex end
    if uv ~= nil then ri.uvRect = UI.R(uv) end
    ri.color = color or UnityEngine.Color(1, 1, 1, 1)
    ri.raycastTarget = false
    rt.anchorMin = UI.V2(.5, .5)
    rt.anchorMax = UI.V2(.5, .5)
    rt.sizeDelta = UI.V2(w or 100, h or 100)
    rt.anchoredPosition = UI.V2(x or 0, y or 0)
    return { go = go, rt = rt, ri = ri }
end

function UI.fullImg(parent, tex, color)
    local go, rt = UI.node(parent, "full", true)
    local ri = go:AddComponent(typeof(UnityEngine.UI.RawImage))
    if tex ~= nil then ri.texture = tex end
    ri.color = color
    ri.raycastTarget = true    -- 挡住下面平台的摇杆和按钮
    return { go = go, rt = rt, ri = ri }
end

function UI.atlas(parent, key, w, h, x, y)
    return UI.img(parent, UI.tex.ui_atlas, UI.L.atlas[key], w, h, x, y)
end

function UI.alpha(e, a)
    local c = e.ri.color
    c.a = a
    e.ri.color = c
end

function UI.ease(t)
    t = math.max(0, math.min(1, t))
    return t * t * (3 - 2 * t)
end

---------------------------------------------------------------- 音效（运行时合成，22050Hz 单声道）
UI.SR = 22050

function UI.clip(name, dur, fn)
    local n = math.floor(UI.SR * dur)
    local data = {}
    local st = { lp = 0, lp2 = 0, hp = 0, prev = 0, g = 1, gn = 0 }
    for i = 1, n do
        data[i] = fn((i - 1) / UI.SR, st, dur)
    end
    local c = UnityEngine.AudioClip.Create(name, n, 1, UI.SR, false)
    c:SetData(data, 0)
    return c
end

-- 纸张摩擦：带通噪声 + 随机颗粒感
function UI.paperFn(attack, cutoff, gain)
    return function(t, st, dur)
        st.gn = st.gn - 1
        if st.gn <= 0 then
            st.gn = math.random(60, 420)
            st.g = .25 + math.random() * .75
        end
        local x = math.random() * 2 - 1
        local k = cutoff + (1 - cutoff) * 0
        st.lp = st.lp + (x - st.lp) * k
        local hp = st.lp - st.lp2
        st.lp2 = st.lp2 + (st.lp - st.lp2) * .08
        local env = math.min(1, t / attack) * math.exp(-(t - attack) * 9 / dur) * (1 - t / dur)
        return hp * env * st.g * gain
    end
end

function UI.buildSounds()
    local S = {}
    S.open = UI.clip("ui_open", .5, UI.paperFn(.08, .35, 1.6))
    S.close = UI.clip("ui_close", .32, UI.paperFn(.03, .45, 1.3))
    S.flip = UI.clip("ui_flip", .34, function(t, st, dur)
        local x = math.random() * 2 - 1
        local sweep = .12 + .6 * math.sin(math.pi * t / dur)
        st.lp = st.lp + (x - st.lp) * sweep
        local env = math.sin(math.pi * math.min(1, t / dur)) ^ 1.5
        return (st.lp - st.lp2 * .6) * env * 1.4
    end)
    S.tap = UI.clip("ui_tap", .14, function(t)
        local e = math.exp(-t * 55)
        return (math.sin(2 * math.pi * 520 * t) * .6 + math.sin(2 * math.pi * 1310 * t) * .2) * e * .7 + (math.random() * 2 - 1) * math.exp(-t * 400) * .25
    end)
    S.card = UI.clip("ui_card", .9, function(t)
        local e1 = math.exp(-t * 5)
        local click = (math.random() * 2 - 1) * math.exp(-t * 300) * .3
        return (math.sin(2 * math.pi * 880 * t) * .25 + math.sin(2 * math.pi * 1318.5 * t) * .15 + math.sin(2 * math.pi * 1760 * t) * .06) * e1 + click
    end)
    S.stamp = UI.clip("ui_stamp", .35, function(t)
        local f = 70 + 60 * math.exp(-t * 30)
        return math.sin(2 * math.pi * f * t) * math.exp(-t * 14) * .9 + (math.random() * 2 - 1) * math.exp(-t * 120) * .35
    end)
    -- 入梦：低沉的钟声 + 一层慢慢起来的风声
    S.start = UI.clip("ui_start", 3.2, function(t, st)
        local partials = { { 98, 1, 1.1 }, { 196.4, .55, 1.6 }, { 293.1, .35, 2.2 }, { 466.2, .22, 3 }, { 587.3, .14, 3.6 }, { 784.9, .08, 4.5 } }
        local s = 0
        for _, p in ipairs(partials) do
            s = s + math.sin(2 * math.pi * p[1] * t + math.sin(t * 3 * p[3]) * .3) * p[2] * math.exp(-t * p[3] * .55)
        end
        local x = math.random() * 2 - 1
        st.lp = st.lp + (x - st.lp) * .02
        local wind = st.lp * math.sin(math.pi * math.min(1, t / 3.2)) * 3
        return (s * .34 + wind * .5) * math.min(1, t * 60)
    end)
    local go = UnityEngine.GameObject("dr_ui_audio")
    local src = go:AddComponent(typeof(UnityEngine.AudioSource))
    src.spatialBlend = 0
    src.playOnAwake = false
    UI.src = src
    UI.sfx = S
end

function UI.play(name, vol)
    if UI.src ~= nil and UI.sfx ~= nil and UI.sfx[name] ~= nil then
        pcall(function() UI.src:PlayOneShot(UI.sfx[name], vol or 1) end)
    end
end

---------------------------------------------------------------- 搭建
function UI.buildCanvas()
    local root = UnityEngine.GameObject("dr_ui")
    local cv = root:AddComponent(typeof(UnityEngine.Canvas))
    cv.renderMode = UnityEngine.RenderMode.ScreenSpaceOverlay
    cv.sortingOrder = 900
    local sc = root:AddComponent(typeof(UnityEngine.UI.CanvasScaler))
    sc.uiScaleMode = CS.UnityEngine.UI.CanvasScaler.ScaleMode.ScaleWithScreenSize
    sc.referenceResolution = UI.V2(1920, 1080)
    sc.matchWidthOrHeight = 1
    root:AddComponent(typeof(UnityEngine.UI.GraphicRaycaster))
    UI.root = root
    -- 加载遮罩：贴图没到之前先黑屏，免得先看到游戏画面再跳标题
    UI.cover = UI.panel("cover")
    UI.cover.go:SetActive(true)
    UI.cover.cg.alpha = 1
    UI.fullImg(UI.cover.rt, nil, UnityEngine.Color(0, 0, 0, 1))
end

function UI.buildAll()
    local L, T = UI.L, UI.tex
    UI.grainTex = UI.makeGrain()
    -- 标题
    local P = UI.panel("title")
    P.grain = UI.fullImg(P.rt, UI.grainTex, UnityEngine.Color(1, 1, 1, .16))
    P.grain.ri.raycastTarget = false
    P.vig = UI.fullImg(P.rt, T.ui_atlas, UnityEngine.Color(1, 1, 1, .92))
    P.vig.ri.uvRect = UI.R(L.atlas.vignette)
    local tw = 1240
    P.title = UI.img(P.rt, T.ui_title, L.title.frames[1], tw, tw / L.title.aspect, 0, 70)
    P.sub = UI.img(P.rt, T.ui_title, L.title.sub, 600, 600 / L.title.sub_aspect, 0, -190)
    UI.P_title = P
    -- 古书
    local B = UI.panel("book")
    B.dim = UI.fullImg(B.rt, nil, UnityEngine.Color(.02, .015, .03, .72))
    local bh = 900
    local bw = bh * L.book.aspect
    B.book = UI.img(B.rt, T.ui_book, nil, bw, bh, 0, 10)
    local function page(r, half)
        local e = UI.img(B.book.rt, T.ui_pages1, { half, 0, .5, 1 }, r[3] * bw, r[4] * bh,
            (r[1] + r[3] / 2 - .5) * bw, (r[2] + r[4] / 2 - .5) * bh)
        return e
    end
    B.left = page(L.book.left, 0)
    B.right = page(L.book.right, .5)
    B.skip = UI.atlas(B.rt, "skip", 224, 84, 0, 0)
    B.skip.rt.anchorMin = UI.V2(1, 1)
    B.skip.rt.anchorMax = UI.V2(1, 1)
    B.skip.rt.anchoredPosition = UI.V2(-170, -80)
    B.hint = UI.atlas(B.rt, "hint_flip", 384, 48, 0, -505)
    UI.P_book = B
    -- 地图按钮（左上角）
    local G = UI.panel("hud")
    G.btn = UI.atlas(G.rt, "mapbtn", 150, 150, 0, 0)
    G.btn.rt.anchorMin = UI.V2(0, 1)
    G.btn.rt.anchorMax = UI.V2(0, 1)
    G.btn.rt.anchoredPosition = UI.V2(UI.BTN_X, -UI.BTN_Y)
    UI.P_hud = G
    -- 地图
    local M = UI.panel("map")
    M.dim = UI.fullImg(M.rt, nil, UnityEngine.Color(.02, .015, .03, .66))
    local ms = 1000
    M.size = ms
    M.map = UI.img(M.rt, T.ui_map, nil, ms, ms, 0, 0)
    M.rings = {}
    for i, p in ipairs(L.poi) do
        local x, y = UI.mapXY(p.x, p.z)
        local r = UI.atlas(M.map.rt, "ring", 64, 64, x, y)
        M.rings[i] = r
    end
    M.arrow = UI.atlas(M.map.rt, "arrow", 54, 54, 0, 0)
    M.close = UI.atlas(M.rt, "close", 224, 84, ms / 2 + 150, ms / 2 - 60)
    M.hint = UI.atlas(M.rt, "hint_map", 384, 48, 0, -ms / 2 - 8)
    M.card = UI.img(M.rt, T.ui_cards1, nil, 600, 600 / L.card_aspect, 0, 0)
    M.card.go:SetActive(false)
    UI.P_map = M
end

UI.BTN_X = 120
UI.BTN_Y = 110

-- 世界坐标 → 地图图片上的位置（图片中心为原点）
function UI.mapXY(x, z)
    local m = UI.L.map
    local u = (m.M + x * m.S) / m.size
    local v = (m.M + (256 - z) * m.S) / m.size
    local s = UI.P_map and UI.P_map.size or 1000
    return (u - .5) * s, (.5 - v) * s
end

function UI.show(P, on)
    P.go:SetActive(true)
    P.target = on and 1 or 0
    P.cg.blocksRaycasts = on
end

function UI.fadePanels(dt)
    for _, P in ipairs({ UI.P_title, UI.P_book, UI.P_hud, UI.P_map, UI.cover }) do
        if P ~= nil and P.target ~= nil then
            local a = P.cg.alpha
            local sp = P.fade or 3
            if a < P.target then a = math.min(P.target, a + dt * sp) elseif a > P.target then a = math.max(P.target, a - dt * sp) end
            P.cg.alpha = a
            if a <= 0 and P.target == 0 then P.go:SetActive(false) end
        end
    end
end

---------------------------------------------------------------- 标题镜头：另开一台相机盖在主相机上
function UI.camStart()
    local main = UnityEngine.Camera.main
    if main == nil then return end
    local go = UnityEngine.GameObject("dr_title_cam")
    local cam = go:AddComponent(typeof(UnityEngine.Camera))
    cam:CopyFrom(main)
    cam.depth = main.depth + 5
    pcall(function()
        local T = typeof(CS.UnityEngine.Rendering.Universal.UniversalAdditionalCameraData)
        local s = main:GetComponent(T)
        local d = go:GetComponent(T)
        if d == nil then d = go:AddComponent(T) end
        if s ~= nil and d ~= nil then
            d.renderPostProcessing = s.renderPostProcessing
            d.antialiasing = s.antialiasing
            d.renderShadows = s.renderShadows
        end
    end)
    UI.cam = cam
    UI.main = main
end

function UI.camTitle(t)
    if UI.cam == nil then return end
    local k = UI.ease((math.sin(t * .09 - 1.57) + 1) / 2)
    local p = Vector3.Lerp(UI.CAM_A, UI.CAM_B, k)
    p.y = p.y + math.sin(t * .3) * .6
    UI.cam.transform.position = p
    -- Aim at the authored vortex centre, independent of the slow camera drift.
    local vortex=SWIRL_LAYERS[2].transform
    local target=vortex and vortex.position or Vector3(128,235,440)
    UI.cam.transform.rotation = Quaternion.LookRotation(target - p)
end

function UI.camFly(k)
    if UI.cam == nil or UI.main == nil then return end
    local e = UI.ease(k)
    local mt = UI.main.transform
    UI.cam.transform.position = Vector3.Lerp(UI.flyFrom, mt.position, e)
    UI.cam.transform.rotation = Quaternion.Slerp(UI.flyRot, mt.rotation, e)
end

function UI.camEnd()
    if UI.cam ~= nil then
        UnityEngine.Object.Destroy(UI.cam.gameObject)
        UI.cam = nil
    end
end

---------------------------------------------------------------- 状态
function UI.lockPlayer(actor, on)
    pcall(function() actor:Immobilize(on) end)
    pcall(function() DouyinUIService.SetUIVisible(not on) end)
    pcall(function() DouyinUIService.SetNativeUIVisible(not on) end)
end

function UI.setSpread(k)
    local B = UI.P_book
    local tex = UI.tex["ui_pages" .. k]
    B.left.ri.texture = tex
    B.right.ri.texture = tex
end

function UI.openMap()
    local M = UI.P_map
    UI.show(M, true)
    M.fade = 5
    M.card.go:SetActive(false)
    UI.cardId = nil
    UI.state = "map"
    UI.play("open")
end

function UI.closeMap(actor)
    UI.show(UI.P_map, false)
    UI.state = "play"
    UI.lockPlayer(actor, false)
    UI.play("close")
end

function UI.showCard(i)
    local M, L = UI.P_map, UI.L
    local p = L.poi[i]
    local c = L.cards[p.id]
    M.card.ri.texture = UI.tex["ui_cards" .. c[1]]
    M.card.ri.uvRect = UnityEngine.Rect(c[2], c[3], c[4], c[5])
    local x, y = UI.mapXY(p.x, p.z)
    local cw, ch = 600, 600 / L.card_aspect
    local cx = x + (x < 0 and cw / 2 + 30 or -cw / 2 - 30)
    local cy = math.max(-M.size / 2 + ch / 2 + 20, math.min(M.size / 2 - ch / 2 - 20, y + 40))
    M.card.rt.anchoredPosition = UI.V2(cx, cy)
    M.card.go:SetActive(true)
    M.cardT = 0
    UI.cardId = p.id
    UI.play("card", .8)
end

function UI.update(actor)
    local dt = Time.unscaledDeltaTime
    UI.t = UI.t + dt
    if UI.state == "boot" then
        UI.wait = UI.wait + dt
        if UI.tryT == nil or UI.t - UI.tryT > .5 then
            UI.tryT = UI.t
            if UI.findTextures() then
                UI.buildAll()
                local oks, errs = pcall(UI.buildSounds)
                if not oks then UI.log("sounds failed " .. tostring(errs)) end
                UI.camStart()
                UI.lockPlayer(actor, true)
                UI.show(UI.P_title, true)
                UI.P_title.fade = 1.2
                UI.cover.target = 0
                UI.cover.fade = 1.2
                UI.state = "title"
                UI.st = UI.t
                UI.log("ready")
            elseif UI.wait > 12 then
                UI.log("textures missing, skip ui")
                UI.cover.target = 0
                UI.state = "off"
            end
        end
    elseif UI.state == "title" then
        local P = UI.P_title
        local lt = UI.t - UI.st
        UI.camTitle(lt)
        P.title.ri.uvRect = UI.R(UI.L.title.frames[math.floor(lt * 8) % 3 + 1])
        UI.alpha(P.sub, .45 + .55 * (math.sin(lt * 2.2) * .5 + .5))
        P.grain.ri.uvRect = UnityEngine.Rect(math.random(), math.random(), UI.halfW() / 64, 540 / 64)
        if lt > 1 and UI.tapped() ~= nil then
            UI.play("start")
            UI.state = "fly"
            UI.st = UI.t
            UI.flyFrom = UI.cam and UI.cam.transform.position or Vector3.zero
            UI.flyRot = UI.cam and UI.cam.transform.rotation or Quaternion.identity
            P.fade = 1.6
            UI.show(P, false)
        end
    elseif UI.state == "fly" then
        local P = UI.P_title
        local k = (UI.t - UI.st) / 2.6
        local s = 1 + UI.ease(k * 2) * .12
        P.title.rt.localScale = Vector3(s, s, 1)
        P.grain.ri.uvRect = UnityEngine.Rect(math.random(), math.random(), UI.halfW() / 64, 540 / 64)
        UI.camFly(k)
        if k >= 1 then
            UI.camEnd()
            local seen = 0
            pcall(function() seen = UnityEngine.PlayerPrefs.GetInt("dr_prologue_v1", 0) end)
            if seen == 1 then
                UI.enterPlay(actor)
            else
                UI.spread = 1
                UI.setSpread(1)
                UI.show(UI.P_book, true)
                UI.P_book.fade = 3
                UI.state = "book"
                UI.play("open")
            end
        end
    elseif UI.state == "book" then
        local B = UI.P_book
        UI.alpha(B.hint, .4 + .4 * (math.sin(UI.t * 2.5) * .5 + .5))
        if B.flipT ~= nil then
            B.flipT = B.flipT + dt
            local k = B.flipT / .35
            local a = k < .5 and (1 - k * 2) or ((k - .5) * 2)
            if k >= .5 and not B.swapped then
                B.swapped = true
                UI.setSpread(UI.spread)
            end
            UI.alpha(B.left, math.max(0, math.min(1, a)))
            UI.alpha(B.right, math.max(0, math.min(1, a)))
            if k >= 1 then B.flipT = nil end
        end
        local x, y = UI.tapped()
        if x ~= nil and B.flipT == nil then
            local hw = UI.halfW()
            if x > hw - 290 and y > 540 - 130 then
                UI.finishBook(actor)
            elseif UI.spread < 3 then
                UI.spread = UI.spread + 1
                B.flipT = 0
                B.swapped = false
                UI.play("flip")
            else
                UI.finishBook(actor)
            end
        end
    elseif UI.state == "settle" then
        -- 地图按钮从屏幕中央飞到左上角
        local G = UI.P_hud
        local k = UI.ease((UI.t - UI.st) / .8)
        local hw = UI.halfW()
        local sx, sy = hw, -540 + 40
        local ex, ey = UI.BTN_X, -UI.BTN_Y
        G.btn.rt.anchoredPosition = UI.V2(sx + (ex - sx) * k, sy + (ey - sy) * k)
        local s = 2.2 - 1.2 * k
        G.btn.rt.localScale = Vector3(s, s, 1)
        if k >= 1 then
            UI.play("stamp")
            UI.state = "play"
            UI.lockPlayer(actor, false)
        end
    elseif UI.state == "play" then
        local x, y = UI.tapped()
        if x ~= nil then
            local bx, by = -UI.halfW() + UI.BTN_X, 540 - UI.BTN_Y
            if math.abs(x - bx) < 80 and math.abs(y - by) < 80 then
                UI.lockPlayer(actor, true)
                UI.openMap()
            end
        end
        if Input.GetKeyDown("tab") then
            UI.lockPlayer(actor, true)
            UI.openMap()
        end
    elseif UI.state == "map" then
        UI.updateMap(actor, dt)
    end
    UI.fadePanels(dt)
end

function UI.enterPlay(actor)
    UI.show(UI.P_hud, true)
    UI.P_hud.fade = 2
    UI.P_hud.btn.rt.anchoredPosition = UI.V2(UI.BTN_X, -UI.BTN_Y)
    UI.P_hud.btn.rt.localScale = Vector3(1, 1, 1)
    UI.state = "play"
    UI.lockPlayer(actor, false)
end

function UI.finishBook(actor)
    pcall(function()
        UnityEngine.PlayerPrefs.SetInt("dr_prologue_v1", 1)
        UnityEngine.PlayerPrefs.Save()
    end)
    UI.show(UI.P_book, false)
    UI.play("close")
    UI.show(UI.P_hud, true)
    UI.P_hud.fade = 4
    UI.P_hud.btn.rt.anchoredPosition = UI.V2(UI.halfW(), -500)
    UI.state = "settle"
    UI.st = UI.t
end

function UI.updateMap(actor, dt)
    local M, L = UI.P_map, UI.L
    -- 玩家箭头：位置 + 镜头朝向
    local p = actor.position
    local ax, ay = UI.mapXY(p.x, p.z)
    M.arrow.rt.anchoredPosition = UI.V2(ax, ay)
    local yaw = 0
    pcall(function() yaw = DouyinCameraService.GetYaw() end)
    M.arrow.rt.localEulerAngles = Vector3(0, 0, -yaw)
    local s = 1 + math.sin(UI.t * 4) * .08
    M.arrow.rt.localScale = Vector3(s, s, 1)
    -- 地点光圈呼吸
    for i, r in ipairs(M.rings) do
        local on = L.poi[i].id == UI.cardId
        UI.alpha(r, on and 1 or (.35 + .3 * (math.sin(UI.t * 2 + i) * .5 + .5)))
        local rs = on and 1.35 or 1
        r.rt.localScale = Vector3(rs, rs, 1)
    end
    if M.card.go.activeSelf then
        M.cardT = (M.cardT or 0) + dt
        local k = UI.ease(M.cardT / .22)
        M.card.rt.localScale = Vector3(.92 + .08 * k, .92 + .08 * k, 1)
        UI.alpha(M.card, k)
    end
    local x, y = UI.tapped()
    if x == nil then
        if Input.GetKeyDown("tab") or Input.GetKeyDown("escape") then UI.closeMap(actor) end
        return
    end
    local h = M.size / 2
    local cx, cy = h + 150, h - 60
    if math.abs(x - cx) < 115 and math.abs(y - cy) < 45 then
        UI.closeMap(actor)
        return
    end
    if math.abs(x) > h or math.abs(y) > h then
        UI.closeMap(actor)
        return
    end
    local best, bd = nil, 52
    for i, q in ipairs(L.poi) do
        local px, py = UI.mapXY(q.x, q.z)
        local d = math.sqrt((px - x) ^ 2 + (py - y) ^ 2)
        if math.abs(x - px - q.lx) < q.lw and math.abs(y - py - q.ly) < q.lh then d = 0 end
        if d < bd then best, bd = i, d end
    end
    if best ~= nil then
        UI.showCard(best)
    elseif M.card.go.activeSelf then
        M.card.go:SetActive(false)
        UI.cardId = nil
        UI.play("tap", .6)
    end
end
-- @@UI END

function UI.updateDesktopBgm()
    if UI.desktopBgmDisabled or UI.root == nil then return end
    if not UI.desktopBgmModule then
        -- The editor runs WebGL on desktop; native/mobile keeps scene audioData.
        if UnityEngine.Application.isMobilePlatform
            or UnityEngine.Application.platform ~= UnityEngine.RuntimePlatform.WebGLPlayer then
            UI.desktopBgmDisabled = true
            return
        end
        UI.desktopBgmModule = require("modules.desktop_bgm")
        UI.desktopBgm = UI.desktopBgmModule.new(UI.root)
    end
    UI.desktopBgmModule.update(UI.desktopBgm)
end

function OnDestroy()
    if DR.camera then UnityEngine.Object.Destroy(DR.camera.gameObject);DR.camera=nil end
    if DR.rider then pcall(function() DR.rider.gameObject.transform:SetParent(nil,true);DR.rider:StandUp(DR.seat);DR.rider:Immobilize(false) end);DR.rider=nil end
    if UI.desktopBgmModule then
        UI.desktopBgmModule.dispose(UI.desktopBgm)
        UI.desktopBgm = nil
    end
end

function Update()
    if UI.root == nil and not UI.failed then
        local okc, errc = pcall(UI.buildCanvas)
        if not okc then UI.failed = true; report("ui canvas failed " .. tostring(errc)) end
    end
    if not UI.desktopBgmDisabled then
        local okb, errb = pcall(UI.updateDesktopBgm)
        if not okb then
            UI.desktopBgmDisabled = true
            if UI.desktopBgmModule then pcall(UI.desktopBgmModule.dispose, UI.desktopBgm) end
            report("desktop music failed " .. tostring(errb))
        end
    end
    updateSky()
    if skyReady then UI.updateMotion() end
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
    if not UI.failed and UI.state ~= "off" then
        local oku, erru = pcall(UI.update, actor)
        if not oku then
            UI.failed = true
            report("ui failed " .. tostring(erru))
            pcall(function() UI.root:SetActive(false) end)
            pcall(UI.camEnd)
            pcall(UI.lockPlayer, actor, false)
        end
    end
    updateDayNight(actor)
    updatePortals(actor)
    if not UI.reeds.failed then
        local ok,err=pcall(UI.updateReeds,actor)
        if not ok then UI.reeds.failed=true;report("reeds failed "..tostring(err)) end
    end
    if not UI.foliage.failed then
        local ok,err=pcall(UI.updateFoliage,actor)
        if not ok then UI.foliage.failed=true;report("foliage failed "..tostring(err)) end
    end
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

function LateUpdate()
    if DR.v8 and DR.rider then DR.align(DR.rider) end
end

return {}
