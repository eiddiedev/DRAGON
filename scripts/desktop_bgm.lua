-- Desktop preview fallback. Mobile keeps the platform's scene background music.
local M = {}
local alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
local values = {}
for i = 1, #alphabet do values[alphabet:byte(i)] = i - 1 end

function M.decode(encoded)
    local bytes = {}
    for i = 1, #encoded, 4 do
        local a, b, c, d = encoded:byte(i, i + 3)
        local n = values[a] * 262144 + values[b] * 4096
            + (values[c] or 0) * 64 + (values[d] or 0)
        bytes[#bytes + 1] = string.char(math.floor(n / 65536))
        if c ~= 61 then bytes[#bytes + 1] = string.char(math.floor(n / 256) % 256) end
        if d ~= 61 then bytes[#bytes + 1] = string.char(n % 256) end
    end
    local raw, samples = table.concat(bytes), {}
    for i = 1, #raw, 2 do
        local lo, hi = raw:byte(i, i + 1)
        local sample = lo + hi * 256
        if sample >= 32768 then sample = sample - 65536 end
        samples[#samples + 1] = sample / 32768
    end
    return samples
end

function M.new(parent)
    local data = require("modules.desktop_bgm_data")
    local go = UnityEngine.GameObject("dr_desktop_bgm")
    -- UI visibility and UI error recovery must not deactivate the music source.
    -- OnDestroy explicitly disposes this independent scene object.
    local source = go:AddComponent(typeof(UnityEngine.AudioSource))
    source.playOnAwake = false
    source.spatialBlend = 0
    source.loop = true
    source.volume = 0.65
    source.priority = 0
    source.dopplerLevel = 0
    source.ignoreListenerPause = true
    local clip = UnityEngine.AudioClip.Create("dragonrest_theme", data.frames, data.channels, data.rate, false)
    return { go = go, source = source, clip = clip, data = data, chunk = 1, offset = 0 }
end

function M.update(state)
    if state.data then
        -- Decode a bounded chunk each frame instead of blocking the title screen.
        local samples = M.decode(state.data.chunks[state.chunk])
        assert(state.clip:SetData(samples, state.offset), "background music SetData failed")
        state.offset = state.offset + #samples / state.data.channels
        state.chunk = state.chunk + 1
        if state.chunk > #state.data.chunks then
            state.data = nil
            state.source.clip = state.clip
            state.source:Play()
            CS.UnityEngine.Debug.LogError("[desktop_bgm] started: " .. tostring(state.clip.length) .. " seconds, loop=true")
        end
    elseif not state.verified and state.source.time > 1 then
        state.verified = true
        CS.UnityEngine.Debug.LogError("[desktop_bgm] verified playing=" .. tostring(state.source.isPlaying)
            .. " time=" .. tostring(state.source.time) .. " mute=" .. tostring(state.source.mute))
    end
    if not state.data and UnityEngine.Time then
        state.auditT = (state.auditT or 0) + UnityEngine.Time.unscaledDeltaTime
        if state.auditT >= 5 then
            state.auditT = 0
            local now = state.source.time
            if not state.source.isPlaying or (state.lastTime and math.abs(now-state.lastTime)<.1) then
                CS.UnityEngine.Debug.LogError("[desktop_bgm] interruption playing=" .. tostring(state.source.isPlaying)
                    .. " time=" .. tostring(now) .. " active=" .. tostring(state.go.activeInHierarchy)
                    .. " focused=" .. tostring(UnityEngine.Application.isFocused))
            end
            state.lastTime=now
        end
    end
end

function M.dispose(state)
    if not state then return end
    if state.source then state.source:Stop() end
    if state.go then UnityEngine.Object.Destroy(state.go) end
    if state.clip then UnityEngine.Object.Destroy(state.clip) end
end

return M
