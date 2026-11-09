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
    local k = (1 + .07 * math.sin(T * 11) + .05 * math.sin(T * 17.3)) * (1 + fireBoost * .9)
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
        if not runeLit[i] and dist2d(p, RUNES[i][1], RUNES[i][2]) < 3.6 then
            runeLit[i] = true
            litCount = litCount + 1
            if beamGo[i] then beamGo[i]:SetActive(true) end
            if litCount < 3 then
                toast("龙纹立石被唤醒 " .. litCount .. "/3")
            else
                if beamGo[4] then beamGo[4]:SetActive(true) end
                toast("巨龙回应了你的呼唤！抬头看！")
                summonT = 0
                altarReset = 75
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

local holyLight = nil
local holyTried = false
local function updateHolyLight()
    if not holyTried then
        holyTried = true
        holyLight = addLight(Vector3(153, 60, 71), Color(1, .86, .52, 1), 42, 3.2)
    end
    if holyLight then holyLight.intensity = (3.2 + .4 * math.sin(Time.time * .9)) * (1 - blend * .85) end
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

