---------------------------------------------------------------- 第二版界面工具（贴图以 base64 随脚本带入，LoadImage 载入，不受导入贴图压到 1024 的限制）
UI.K = { tex = {}, spr = {}, at = 1 }
function UI.K.step()
    local K = UI.K
    if K.ready then return true end
    if not K.order then
        K.order = {}
        for name in pairs(UI.K2L.tex) do K.order[#K.order + 1] = name end
        table.sort(K.order)
    end
    local name = K.order[K.at]
    if name == nil then
        K.ready = true
        UI.K2B = nil
        return true
    end
    local t = UnityEngine.Texture2D(2, 2, UnityEngine.TextureFormat.RGBA32, true)
    local bytes = CS.System.Convert.FromBase64String(UI.K2B[name])
    if not t:LoadImage(bytes) then error("ui2 texture " .. name) end
    t.wrapMode = UnityEngine.TextureWrapMode.Clamp
    t.filterMode = UnityEngine.FilterMode.Trilinear
    K.tex[name] = t
    UI.K2B[name] = nil
    K.at = K.at + 1
    return false
end

function UI.K.rect(name)
    local r = UI.K2L.atlas[name]
    if not r then error("ui2 sprite " .. tostring(name)) end
    local t = UI.K.tex["atlas" .. (r[1] + 1)]
    return t, UnityEngine.Rect(r[2] / t.width, 1 - (r[3] + r[5]) / t.height, r[4] / t.width, r[5] / t.height), r[4], r[5]
end

-- 只给 w 时按原图比例算高；都不给时用原图大小
function UI.K.img(parent, name, w, h, x, y)
    local t, uv, nw, nh = UI.K.rect(name)
    if w and not h then h = w * nh / nw elseif not w then w, h = nw, nh end
    local e = UI.img(parent, t, nil, w, h, x or 0, y or 0)
    e.ri.uvRect = uv
    e.w, e.h = w, h
    return e
end

function UI.K.set(e, name, scale)
    local t, uv, nw, nh = UI.K.rect(name)
    e.ri.texture = t
    e.ri.uvRect = uv
    if scale then e.rt.sizeDelta = UI.V2(nw * scale, nh * scale) end
end

function UI.K.sprite(name)
    local s = UI.K.spr[name]
    if s then return s end
    local r = UI.K2L.atlas[name]
    local t = UI.K.tex["atlas" .. (r[1] + 1)]
    s = UnityEngine.Sprite.Create(t, UnityEngine.Rect(r[2], t.height - r[3] - r[5], r[4], r[5]), UI.V2(.5, .5), 100)
    UI.K.spr[name] = s
    return s
end

function UI.K.button(parent, name, w, x, y, fn)
    local e = UI.K.img(parent, name, w, nil, x, y)
    e.ri.raycastTarget = true
    local b = e.go:AddComponent(typeof(UnityEngine.UI.Button))
    b.targetGraphic = e.ri
    b.onClick:AddListener(function() UI.play("tap", .7); fn() end)
    e.btn = b
    return e
end

-- 数字：style 为 "w"（白字描边）或 "i"（墨字）；align -1 左对齐、0 居中、1 右对齐
function UI.K.num(parent, style, scale, x, y, align)
    local go, rt = UI.node(parent, "num", false)
    rt.anchoredPosition = UI.V2(x or 0, y or 0)
    local o = { go = go, rt = rt, items = {}, style = style, scale = scale or 1, align = align or 0 }
    function o.set(s)
        s = tostring(s)
        if o.text == s then return end
        o.text = s
        local total, n, ws = 0, 0, {}
        for i = 1, #s do
            local c = s:sub(i, i)
            local key = (c == "/" and "slash") or (c == ":" and "colon") or c
            local name = "d" .. o.style .. "_" .. key
            local r = UI.K2L.atlas[name]
            if r then
                n = n + 1
                local e = o.items[n]
                if not e then
                    e = UI.K.img(rt, name)
                    o.items[n] = e
                end
                UI.K.set(e, name, o.scale)
                e.go:SetActive(true)
                ws[n] = r[4] * o.scale * .8
                total = total + ws[n]
            end
        end
        local x0 = (o.align == 0 and -total / 2) or (o.align < 0 and 0) or -total
        for i = 1, n do
            o.items[i].rt.anchoredPosition = UI.V2(x0 + ws[i] / 2, 0)
            x0 = x0 + ws[i]
        end
        for i = n + 1, #o.items do o.items[i].go:SetActive(false) end
    end
    return o
end

function UI.K.anchor(e, ax, ay, x, y)
    e.rt.anchorMin = UI.V2(ax, ay)
    e.rt.anchorMax = UI.V2(ax, ay)
    e.rt.anchoredPosition = UI.V2(x, y)
end

UI.K.node = UI.node
UI.K.raw = UI.img
UI.K.V2 = UI.V2
UI.K.play = UI.play
UI.K.ease = UI.ease

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

UI.BTN_X = 120
UI.BTN_Y = 165
UI.BTN_GAP = 190
UI.MAP_OX = -150
-- 主线每一步要去的地方（世界坐标 x, z），下标与 dragon_progress_rules.ObjectiveIndex 一致
UI.OBJ_POS = { { 121, 57 }, { 168, 140.5 }, { 62, 62 }, { 130.3, 19.4 }, { 48, 150 }, { 48, 150 }, { 48, 150 } }
-- 走到多近算「到过」
UI.VISIT_R = { castle = 24, dragon_peak = 34, village = 18, altar = 16, wheat = 13, trial = 13, lake = 14, meadow = 14, flowers = 13, mushroom = 14 }
UI.visit = { n = 0, got = {} }

function UI.buildAll()
    local L, T, K = UI.L, UI.tex, UI.K
    local KL = UI.K2L
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
    -- 古书：三个对开页都用新贴图，第三个对开页是「你」和龙魂之卵
    local B = UI.panel("book")
    B.dim = UI.fullImg(B.rt, nil, UnityEngine.Color(.02, .015, .03, .72))
    local bh = 900
    local bw = bh * L.book.aspect
    B.book = UI.img(B.rt, T.ui_book, nil, bw, bh, 0, 10)
    local function page(r, half)
        return UI.img(B.book.rt, K.tex.pages1, { half, 0, .5, 1 }, r[3] * bw, r[4] * bh,
            (r[1] + r[3] / 2 - .5) * bw, (r[2] + r[4] / 2 - .5) * bh)
    end
    B.left = page(L.book.left, 0)
    B.right = page(L.book.right, .5)
    B.hint = K.img(B.rt, "hint_flip", nil, nil, 0, -505)
    UI.P_book = B
    -- 左上角三个同样大小的按钮：地图、誓约之书、唤龙
    local G = UI.panel("hud")
    local function hudButton(e, label, row)
        K.anchor(e, 0, 1, UI.BTN_X, -(UI.BTN_Y + row * UI.BTN_GAP))
        local lb = K.img(e.rt, label, nil, nil, 0, -84)
        return lb
    end
    G.btn = UI.atlas(G.rt, "mapbtn", 150, 150, 0, 0)
    hudButton(G.btn, "lbl_map", 0)
    G.quest = K.img(G.rt, "btn_quest", 150, 150, 0, 0)
    hudButton(G.quest, "lbl_quest", 1)
    G.dragon = K.img(G.rt, "btn_dragon", 150, 150, 0, 0)
    G.dragonLabel = hudButton(G.dragon, "lbl_dragon", 2)
    G.dragon.go:SetActive(false)
    -- 当前誓约（主线引导）：一句话 + 指向目的地的箭头 + 距离
    G.trk = K.img(G.rt, "trk_bg", nil, nil, 0, 0)
    G.trk.rt.pivot = UI.V2(.5, .5)
    K.anchor(G.trk, .5, 1, 40, -92)
    local head = K.img(G.trk.rt, "trk_head", nil, nil, 0, 0)
    head.rt.pivot = UI.V2(0, .5)
    head.rt.anchoredPosition = UI.V2(-236, 24)
    G.obj = K.img(G.trk.rt, "obj_1", nil, nil, 0, 0)
    G.obj.rt.pivot = UI.V2(0, .5)
    G.obj.rt.anchoredPosition = UI.V2(-190, -14)
    G.ptr = K.img(G.trk.rt, "ptr", 40, 40, -214, -14)
    G.dist = K.num(G.trk.rt, "w", .8, -100, 24, -1)
    UI.P_hud = G
    -- 探访 / 抄录提示条（屏幕上方正中，不挡操作）
    local N = UI.panel("note")
    N.bg = K.img(N.rt, "toast_bg", nil, nil, 0, 0)
    K.anchor(N.bg, .5, 1, 0, -235)
    N.head = K.img(N.bg.rt, "toast_new", nil, nil, -190, 24)
    N.name = K.img(N.bg.rt, "nm_castle", nil, nil, -40, -10)
    N.count = K.num(N.bg.rt, "i", 1, 220, -8, 0)
    UI.P_note = N
    -- 地图
    local M = UI.panel("map")
    M.dim = UI.fullImg(M.rt, nil, UnityEngine.Color(.024, .016, .031, .93))
    local ms = 1000
    M.size = ms
    M.map = UI.img(M.rt, K.tex.map, nil, ms, ms, UI.MAP_OX, 0)
    M.rings, M.stamps = {}, {}
    for i, p in ipairs(KL.poi) do
        local x, y = UI.mapXY(p.x, p.z)
        M.rings[i] = K.img(M.map.rt, "ring", 60, 60, x, y)
        M.stamps[i] = K.img(M.map.rt, "stamp", 46, 46, x + 4, y + 2)
        M.stamps[i].go:SetActive(false)
    end
    M.flag = K.img(M.map.rt, "flag", 58, 58, 0, 0)
    M.arrow = K.img(M.map.rt, "arrow", 54, 54, 0, 0)
    local sx = UI.MAP_OX + ms / 2 + 205
    M.sx = sx
    M.close = K.img(M.rt, "btn_x", 104, nil, sx + 110, 430)
    M.clockBg = K.img(M.rt, "clock_bg", nil, nil, sx, 250)
    M.sun = K.img(M.clockBg.rt, "ic_sun", 84, 84, -98, 0)
    M.dayLabel = K.img(M.clockBg.rt, "lbl_day", nil, nil, 44, 26)
    M.clock = K.num(M.clockBg.rt, "i", 1.25, 44, -28, 0)
    M.progBg = K.img(M.rt, "prog_bg", nil, nil, sx, 70)
    K.img(M.progBg.rt, "lbl_visit", nil, nil, -70, 28)
    M.visitNum = K.num(M.progBg.rt, "i", 1, 72, 28, 0)
    K.img(M.progBg.rt, "lbl_lore", nil, nil, -62, -28)
    M.loreNum = K.num(M.progBg.rt, "i", 1, 86, -28, 0)
    M.sealAll = K.img(M.rt, "seal_all", 190, 190, sx, -130)
    M.sealAll.rt.localEulerAngles = Vector3(0, 0, -12)
    M.sealAll.go:SetActive(false)
    M.hint = K.img(M.rt, "hint_map", 520, nil, UI.MAP_OX, -ms / 2 - 17)
    M.card = K.img(M.rt, "card_bg", 600, nil, 0, 0)
    M.cardText = UI.img(M.card.rt, K.tex.cards, nil, 600, M.card.h, 0, 0)
    M.card.go:SetActive(false)
    UI.P_map = M
end

-- 世界坐标 → 地图图片上的位置（图片中心为原点）
function UI.mapXY(x, z)
    local m = UI.K2L.map
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
    local tex = UI.K.tex["pages" .. k]
    B.left.ri.texture = tex
    B.right.ri.texture = tex
    B.left.go:SetActive(true)
    B.right.go:SetActive(true)
    UI.alpha(B.left, 1)
    UI.alpha(B.right, 1)
    B.hint.go:SetActive(true)
end

function UI.openMap()
    local M = UI.P_map
    UI.show(M, true)
    M.fade = 5
    M.card.go:SetActive(false)
    UI.cardId = nil
    UI.state = "map"
    UI.play("open")
    for i, p in ipairs(UI.K2L.poi) do M.stamps[i].go:SetActive(UI.visit.got[p.id] == true) end
    local total = #UI.K2L.poi
    M.visitNum.set(UI.visit.n .. "/" .. total)
    M.sealAll.go:SetActive(UI.visit.n >= total)
    local ex = DR.phase1.explore
    local lore, loreTotal = 0, UI.K2L.lore.n
    if ex then pcall(function() lore = ex.GetLoreCount() end) end
    M.loreNum.set(lore .. "/" .. loreTotal)
end

function UI.closeMap(actor)
    UI.show(UI.P_map, false)
    UI.state = "play"
    UI.lockPlayer(actor, false)
    UI.play("close")
end

function UI.showCard(i)
    local M = UI.P_map
    local p = UI.K2L.poi[i]
    local c = UI.K2L.cards[p.id]
    local t = UI.K.tex.cards
    M.cardText.ri.uvRect = UnityEngine.Rect(c[1] / t.width, 1 - (c[2] + c[4]) / t.height, c[3] / t.width, c[4] / t.height)
    local x, y = UI.mapXY(p.x, p.z)
    x = x + UI.MAP_OX
    local cw, ch = 600, M.card.h
    local cx = x + (x < UI.MAP_OX and cw / 2 + 36 or -cw / 2 - 36)
    local cy = math.max(-M.size / 2 + ch / 2 + 20, math.min(M.size / 2 - ch / 2 - 20, y + 40))
    M.card.rt.anchoredPosition = UI.V2(cx, cy)
    M.card.go:SetActive(true)
    M.cardT = 0
    UI.cardId = p.id
    UI.play("card", .8)
end

-- 提示条：kind = "visit"（探访新地点）/ "all"（全境踏遍）/ "lore"（抄录了新的文字）
function UI.note(kind, nameKey, n, total)
    local N, K = UI.P_note, UI.K
    if not N then return end
    K.set(N.head, kind == "lore" and "toast_lore" or "toast_new", 1)
    N.head.rt.anchoredPosition = UI.V2(kind == "lore" and -60 or -190, kind == "lore" and 0 or 24)
    N.name.go:SetActive(kind ~= "lore")
    if kind == "all" then
        K.set(N.name, "toast_all", 1)
        N.name.rt.anchoredPosition = UI.V2(-30, -12)
    elseif kind == "visit" then
        K.set(N.name, nameKey, 1)
        N.name.rt.anchoredPosition = UI.V2(-70, -12)
    end
    N.count.set(n .. "/" .. total)
    UI.show(N, true)
    N.cg.blocksRaycasts = false
    N.fade = 4
    N.cg.alpha = 0
    UI.noteT = UI.t
    UI.play("stamp", .8)
    UI.play("card", .7)
end

function UI.checkVisits(p)
    UI.visitT = (UI.visitT or 0) - Time.unscaledDeltaTime
    if UI.visitT > 0 then return end
    UI.visitT = .4
    local V = UI.visit
    local total = #UI.K2L.poi
    for _, q in ipairs(UI.K2L.poi) do
        if not V.got[q.id] then
            local r = UI.VISIT_R[q.id] or 10
            if (p.x - q.x) ^ 2 + (p.z - q.z) ^ 2 < r * r then
                V.got[q.id] = true
                V.n = V.n + 1
                if V.n >= total then
                    UI.note("all", nil, V.n, total)
                    toast("龙眠之境的每一处你都到过了")
                else
                    UI.note("visit", "nm_" .. q.id, V.n, total)
                end
                return
            end
        end
    end
end

function UI.updateHud(actor)
    local G, K = UI.P_hud, UI.K
    local s = DR.phase1
    local pact = CanRideDragon()
    G.dragon.go:SetActive(pact == true)
    if pact then
        local key = (DR.state == "await" and "lbl_ride") or ((DR.state == "summon" or DR.summoning) and "lbl_summoning") or "lbl_dragon"
        if G.dragonKey ~= key then
            G.dragonKey = key
            K.set(G.dragonLabel, key, 1)
        end
        local pulse = DR.state == "await" and (1 + .06 * math.sin(UI.t * 5)) or 1
        G.dragon.rt.localScale = Vector3(pulse, pulse, 1)
    end
    -- 主线引导
    local idx = nil
    if s.prules and s.progress and s.progress.IsLoaded() then
        local okp, v = pcall(function() return s.prules.ObjectiveIndex(s.progress.GetProfile()) end)
        if okp then idx = v end
    end
    local inBattle = s.explore and s.explore.IsBattleActive()
    G.trk.go:SetActive(idx ~= nil and not inBattle)
    if idx and not inBattle then
        if G.objIdx ~= idx then
            G.objIdx = idx
            K.set(G.obj, "obj_" .. idx, 1)
        end
        local q = UI.OBJ_POS[idx]
        local p = actor.position
        local dx, dz = q[1] - p.x, q[2] - p.z
        local d = math.sqrt(dx * dx + dz * dz)
        G.dist.set(math.floor(d + .5) .. "m")
        local yaw = 0
        pcall(function() yaw = DouyinCameraService.GetYaw() end)
        G.ptr.rt.localEulerAngles = Vector3(0, 0, -(math.deg(math.atan(dx, dz)) - yaw))
        G.ptr.go:SetActive(d > 6)
        UI.objIdx = idx
    end
    -- 提示条停留三秒后淡出
    local N = UI.P_note
    if N and N.go.activeSelf and UI.noteT then
        local a = UI.t - UI.noteT
        N.cg.alpha = math.min(1, a * 4) * math.min(1, math.max(0, (3.4 - a) * 2))
        N.bg.rt.anchoredPosition = UI.V2(0, -235 + 40 * (1 - UI.ease(a * 3)))
        if a > 3.4 then N.go:SetActive(false) end
    end
end

function UI.hudTap(actor, x, y)
    local bx = -UI.halfW() + UI.BTN_X
    for row = 0, 2 do
        local by = 540 - UI.BTN_Y - row * UI.BTN_GAP
        if math.abs(x - bx) < 82 and math.abs(y - by) < 88 then
            if row == 0 then
                UI.lockPlayer(actor, true)
                UI.openMap()
            elseif row == 1 then
                local ex = DR.phase1.explore
                if ex then UI.play("open"); ex.OpenTasks() end
            elseif CanRideDragon() then
                UI.play("tap")
                DR.summon(actor)
            end
            return true
        end
    end
    return false
end

function UI.update(actor)
    local dt = Time.unscaledDeltaTime
    UI.t = UI.t + dt
    if UI.state == "boot" then
        UI.wait = UI.wait + dt
        local kitReady = UI.K.step()
        if kitReady and (UI.tryT == nil or UI.t - UI.tryT > .5) then
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
            elseif UI.wait > 45 then
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
            UI.spread = 1
            UI.setSpread(1)
            UI.show(UI.P_book, true)
            UI.P_book.fade = 3
            UI.state = "book"
            UI.play("open")
        end
    elseif UI.state == "book" then
        local B = UI.P_book
        UI.alpha(B.hint, .4 + .4 * (math.sin(UI.t * 2.5) * .5 + .5))
        if B.flipT ~= nil then
            -- 翻页：旧页淡出到看不见，再换图，再淡入。换到誓约页时书页保持隐藏，不会闪回旧页
            B.flipT = B.flipT + dt
            local k = B.flipT / .4
            if k >= .5 and not B.swapped then
                B.swapped = true
                if UI.spread <= 3 then
                    UI.setSpread(UI.spread)
                else
                    B.left.go:SetActive(false)
                    B.right.go:SetActive(false)
                    B.hint.go:SetActive(false)
                    if not UI.showOath() then UI.leaveBook(actor) end
                end
            end
            if UI.spread <= 3 or not B.swapped then
                local a = k < .5 and (1 - k * 2) or ((k - .5) * 2)
                a = math.max(0, math.min(1, a))
                UI.alpha(B.left, a)
                UI.alpha(B.right, a)
            end
            if k >= 1 then B.flipT = nil end
        end
        local x = UI.tapped()
        if x ~= nil and B.flipT == nil and UI.spread <= 3 then
            if UI.spread < 3 then
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
        local busy = DR.phase1.menu == true
        if not busy then
            local x, y = UI.tapped()
            if x ~= nil then UI.hudTap(actor, x, y) end
            if Input.GetKeyDown("tab") then
                UI.lockPlayer(actor, true)
                UI.openMap()
            end
        end
        UI.checkVisits(actor.position)
    elseif UI.state == "map" then
        UI.updateMap(actor, dt)
    end
    if UI.P_hud and (UI.state == "play" or UI.state == "map") then
        local okh, errh = pcall(UI.updateHud, actor)
        if not okh and not UI.hudErr then UI.hudErr = true; report("hud " .. tostring(errh)) end
        local hide = DR.phase1.menu == true or UI.state == "map"
        local want = hide and 0 or 1
        if UI.P_hud.target ~= want then UI.P_hud.target = want; UI.P_hud.fade = 6; UI.P_hud.go:SetActive(true) end
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

-- 读完第三个对开页：没签过誓约就翻到誓约页，签过（重读序章）就直接合上
function UI.finishBook(actor)
    local B = UI.P_book
    if DR.phase1.progress and not DR.phase1.progress.GetProfile().class then
        UI.spread = 4
        B.flipT = 0
        B.swapped = false
        UI.play("flip")
        return
    end
    UI.leaveBook(actor)
end

function UI.leaveBook(actor)
    UI.show(UI.P_book, false)
    UI.play("close")
    if UI.P_hud.cg.alpha > 0 then
        UI.enterPlay(actor)
        return
    end
    UI.show(UI.P_hud, true)
    UI.P_hud.fade = 4
    UI.P_hud.btn.rt.anchoredPosition = UI.V2(UI.halfW(), -500)
    UI.state = "settle"
    UI.st = UI.t
end

function UI.updateMap(actor, dt)
    local M, KL, K = UI.P_map, UI.K2L, UI.K
    local cycle = DR.phase1.cycle
    if cycle then
        local day = cycle.IsDay()
        if M.dayShown ~= day then
            M.dayShown = day
            K.set(M.sun, day and "ic_sun" or "ic_moon")
            K.set(M.dayLabel, day and "lbl_day" or "lbl_night", 1)
        end
        M.clock.set(cycle.GetWorldClock() or "")
    end
    -- 玩家箭头：位置 + 镜头朝向
    local p = actor.position
    local ax, ay = UI.mapXY(p.x, p.z)
    M.arrow.rt.anchoredPosition = UI.V2(ax, ay)
    local yaw = 0
    pcall(function() yaw = DouyinCameraService.GetYaw() end)
    M.arrow.rt.localEulerAngles = Vector3(0, 0, -yaw)
    local s = 1 + math.sin(UI.t * 4) * .08
    M.arrow.rt.localScale = Vector3(s, s, 1)
    -- 当前誓约的小旗
    local q = UI.objIdx and UI.OBJ_POS[UI.objIdx]
    M.flag.go:SetActive(q ~= nil)
    if q then
        local fx, fy = UI.mapXY(q[1], q[2])
        M.flag.rt.anchoredPosition = UI.V2(fx + 14, fy + 22 + math.abs(math.sin(UI.t * 3)) * 6)
    end
    -- 地点光圈：没去过的呼吸，去过的盖着印
    for i, r in ipairs(M.rings) do
        local id = KL.poi[i].id
        local on = id == UI.cardId
        local seen = UI.visit.got[id]
        UI.alpha(r, on and 1 or (seen and .22 or (.4 + .35 * (math.sin(UI.t * 2 + i) * .5 + .5))))
        local rs = on and 1.35 or 1
        r.rt.localScale = Vector3(rs, rs, 1)
    end
    if M.card.go.activeSelf then
        M.cardT = (M.cardT or 0) + dt
        local k = UI.ease(M.cardT / .22)
        M.card.rt.localScale = Vector3(.92 + .08 * k, .92 + .08 * k, 1)
        UI.alpha(M.card, k)
        UI.alpha(M.cardText, k)
    end
    local x, y = UI.tapped()
    if x == nil then
        if Input.GetKeyDown("tab") or Input.GetKeyDown("escape") then UI.closeMap(actor) end
        return
    end
    local h = M.size / 2
    if math.abs(x - (M.sx + 110)) < 70 and math.abs(y - 430) < 70 then
        UI.closeMap(actor)
        return
    end
    local mx = x - UI.MAP_OX
    if math.abs(mx) > h or math.abs(y) > h then
        if x < UI.MAP_OX - h or math.abs(y) > h then UI.closeMap(actor) end
        return
    end
    local k = M.size / KL.map.size
    local best, bd = nil, 46
    for i, c in ipairs(KL.poi) do
        local px, py = UI.mapXY(c.x, c.z)
        local d = math.sqrt((px - mx) ^ 2 + (py - y) ^ 2)
        local b = c.box
        if math.abs(mx - px - b[1] * k) < b[3] * k and math.abs(y - py - b[2] * k) < b[4] * k then d = 0 end
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
