---------------------------------------------------------------- 界面：标题页、序章古书、地图（全部放在 UI 表里，主块只占一个局部变量）
-- 贴图来自藏在地下的 ui_* 方片模型，音效在运行时合成。
local UI = { state = "boot", t = 0, wait = 0, cardId = nil }
UI.L = --@@LAYOUT@@
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
    UI.cam.transform.rotation = Quaternion.LookRotation(UI.CAM_LOOK - p)
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
