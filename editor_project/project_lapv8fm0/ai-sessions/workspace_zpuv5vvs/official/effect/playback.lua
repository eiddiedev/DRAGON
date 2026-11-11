local Logger = require("official.core.logger")

local logger = Logger.create("official-effect")

local Effect = {}

Effect.Reason = {
    Unavailable = "effect-system-unavailable",
    InvalidContext = "effect-invalid-context",
    InvalidKey = "effect-invalid-key",
    NotFound = "effect-not-found",
    AmbiguousTemplate = "effect-ambiguous-template",
    NotReady = "effect-not-ready",
    -- spawn 已能播放循环特效、不再返回；保留供旧脚本比较。
    Looping = "effect-spawn-rejected-looping",
    SpawnFailed = "effect-spawn-failed",
    Inactive = "effect-inactive-hierarchy",
}

-- 占位表是 xLua 对缺失 C# 类型返回的伪对象（带 .fqn），不能当作真实类型或实例。
local function isRealCsValue(value)
    if value == nil then
        return false
    end
    if type(value) ~= "table" then
        return true
    end
    local ok, fqn = pcall(rawget, value, ".fqn")
    return ok and fqn == nil
end

local function resolveGameObject(value)
    if value == nil then
        return nil
    end

    local ok, gameObject = pcall(function()
        return value.gameObject
    end)
    if ok and gameObject ~= nil then
        return gameObject
    end

    ok, gameObject = pcall(function()
        return value.transform ~= nil and value or nil
    end)
    if ok then
        return gameObject
    end
    return nil
end

local function resolveTransform(value)
    local gameObject = resolveGameObject(value)
    if gameObject == nil then
        return nil
    end

    local ok, transform = pcall(function()
        return gameObject.transform
    end)
    if ok then
        return transform
    end
    return nil
end

local function destroyObject(gameObject, delay)
    if gameObject == nil then
        return
    end
    pcall(function()
        if delay == nil then
            CS.UnityEngine.Object.Destroy(gameObject)
        else
            CS.UnityEngine.Object.Destroy(gameObject, delay)
        end
    end)
end

-- 引用可能指向预制体外层；只接受其子树中的唯一效果根，不拆分根内的粒子。
local function findMarkedRoot(gameObject, isRoot)
    local pending = { gameObject }
    local found = nil
    while #pending > 0 do
        local candidate = table.remove(pending)
        if isRoot(candidate) then
            if found ~= nil then
                return nil, Effect.Reason.AmbiguousTemplate
            end
            found = candidate
        else
            local transform = candidate.transform
            for i = 0, transform.childCount - 1 do
                pending[#pending + 1] = transform:GetChild(i).gameObject
            end
        end
    end
    return found, found == nil and Effect.Reason.NotFound or nil
end

-- 编辑器宿主：转调 C# EffectSystem。
local Studio = {}

function Studio.resolve(gameObject, key)
    return Studio.system:ResolvePoolTemplate(gameObject, key)
end

function Studio.resolveReferenced(gameObject)
    return findMarkedRoot(gameObject, function(candidate)
        return Studio.system:GetComponent(candidate) ~= nil
    end)
end

function Studio.isReady(template)
    return Studio.system:IsPoolTemplateReady(template)
end

function Studio.isLooping(template)
    return Studio.system:IsPoolTemplateLooping(template)
end

-- 副本激活时由 MonoChain.Awake 按复制来源接管特效资源，这里不必处理。
function Studio.adopt()
end

function Studio.play(template)
    return Studio.system:PlayTemplate(template)
end

function Studio.stop(template, immediate)
    Studio.system:StopTemplate(template, immediate)
end

function Studio.spawn(gameObject, template, key, position, options)
    if type(key) ~= "string" then
        -- 公开池接口按名称解析；确认仍是引用对象，避免同名模板导致误播。
        gameObject = template
        key = template.name
        local resolved, exact = pcall(function()
            local candidate = Studio.system:ResolvePoolTemplate(gameObject, key)
            return candidate ~= nil and candidate:Equals(template)
        end)
        if not resolved or not exact then
            return nil, Effect.Reason.NotFound
        end
    end
    if position == nil then
        return Studio.system:Spawn(gameObject, key)
    end
    local rotation = options ~= nil and options.rotation or template.transform.rotation
    local scale = options ~= nil and options.scale or 1
    local parent = options ~= nil and resolveTransform(options.parent) or nil
    return Studio.system:SpawnAt(gameObject, key, position, rotation, scale, parent)
end

-- 预览端与发布态没有 EffectSystem：特效是原生 ParticleSystem（发布态已烘焙），这里直接用 Lua 驱动。
-- 官方库没有逐帧驱动：spawn 副本不复用，spawn 与 Stop 按宿主定时器检查粒子是否结束；副本另有引擎销毁兜底。
local Native = {
    CopyCapacity = 8,
    FadeGraceSeconds = 0.1,
    FadePollSeconds = 0.25,
    -- 与 studio 一致：发射时长 ≤30 秒是生成侧硬预算，超时只可能是配置异常，强制收尾。
    FadeTimeoutSeconds = 30,
    PoolRootName = "__EffectPool",
    -- 发布转换（WorldSdkEffectPublisher）移除 EffectRuntimeRoot 时在效果根下留的空子节点，两边按此名字对齐。
    RootMarkerName = "__EffectRoot",
    copies = {},
    fades = {},
    -- 预览端效果根是热更类型，发布态没有该程序集（取到占位表）。按 System.Type 取组件：
    -- 按名字取要带命名空间，否则直接报错，且每次调用都会打 deprecated 警告。
    runtimeRootType = nil,
}
do
    local ok, value = pcall(function()
        return CS.Hamlet.AIEffects.EffectRuntimeRoot
    end)
    if ok and isRealCsValue(value) and typeof ~= nil then
        local typed, systemType = pcall(typeof, value)
        if typed then
            Native.runtimeRootType = systemType
        end
    end
end

-- 被销毁的 UnityEngine.Object 在 xLua 里不等于 nil，只能靠 Equals(nil)；访问出错同样视为已销毁。
function Native.isDestroyed(object)
    if object == nil then
        return true
    end
    local ok, destroyed = pcall(function()
        return object:Equals(nil)
    end)
    return not ok or destroyed == true
end

function Native.particleType()
    local particleSystem = CS.UnityEngine.ParticleSystem
    if typeof ~= nil then
        return typeof(particleSystem)
    end
    return particleSystem
end

-- 子发射器目标只由父系统触发，不能单独 Play。
function Native.classify(all)
    local targets = {}
    for _, system in ipairs(all) do
        pcall(function()
            local module = system.subEmitters
            if not module.enabled then
                return
            end
            for subIndex = 0, module.subEmittersCount - 1 do
                local target = module:GetSubEmitterSystem(subIndex)
                if target ~= nil then
                    targets[target:GetInstanceID()] = true
                end
            end
        end)
    end
    local playable = {}
    for _, system in ipairs(all) do
        if not targets[system:GetInstanceID()] then
            playable[#playable + 1] = system
        end
    end
    return { all = all, playable = playable }
end

-- 整棵子树（含 inactive 与自身）的粒子：Stop 与收尾用这个范围，同 C# StopTemplate。
function Native.collect(gameObject)
    local array = gameObject:GetComponentsInChildren(Native.particleType(), true)
    local all = {}
    for index = 0, array.Length - 1 do
        if array[index] ~= nil then
            all[#all + 1] = array[index]
        end
    end
    return Native.classify(all)
end

-- 预览端效果根带 EffectRuntimeRoot；发布态已被移除，类型也不存在，返回 nil。
function Native.runtimeRoot(gameObject)
    local rootType = Native.runtimeRootType
    if rootType == nil then
        return nil
    end
    local ok, root = pcall(function()
        return gameObject:GetComponent(rootType)
    end)
    if ok and isRealCsValue(root) and not Native.isDestroyed(root) then
        return root
    end
    return nil
end

-- 预览端认 EffectRuntimeRoot，发布态认发布转换留下的标记子节点；层级结构本身分不清效果根与外层容器。
function Native.isEffectRoot(gameObject)
    if Native.runtimeRoot(gameObject) ~= nil then
        return true
    end
    local ok, marker = pcall(function()
        return gameObject.transform:Find(Native.RootMarkerName)
    end)
    return ok and marker ~= nil
end

-- 效果根自己拥有的粒子：Play / IsLooping 只作用于这些，同 C# EffectRuntimeRoot，嵌套的独立效果根各管各的。
-- 预览端直接取 EffectRuntimeRoot.Systems；发布态没有该组件，沿子树收集、遇到嵌套效果根即停。
function Native.owned(template)
    local root = Native.runtimeRoot(template)
    if root ~= nil then
        local ok, array = pcall(function()
            return root.Systems
        end)
        if ok and array ~= nil then
            local all = {}
            for index = 0, array.Length - 1 do
                if array[index] ~= nil then
                    all[#all + 1] = array[index]
                end
            end
            return Native.classify(all)
        end
    end
    local all, pending = {}, { template.transform }
    while #pending > 0 do
        local node = table.remove(pending)
        local system = node.gameObject:GetComponent(Native.particleType())
        if system ~= nil then
            all[#all + 1] = system
        end
        for index = node.childCount - 1, 0, -1 do
            local child = node:GetChild(index)
            if not Native.isEffectRoot(child.gameObject) then
                pending[#pending + 1] = child
            end
        end
    end
    return Native.classify(all)
end

-- 预览端副本按复制来源接管效果资源（studio 由 MonoChain.Awake 完成），否则 IsReady 恒为 false、不持有模板资源。
-- Instantiate 保留层级顺序，按位置逐节点配对，与 C# AdoptHierarchy 同规则；发布态没有效果根，什么也不做。
function Native.adopt(template, copy)
    local pending = { { template.transform, copy.transform } }
    while #pending > 0 do
        local pair = table.remove(pending)
        local source, target = pair[1], pair[2]
        local sourceRoot = Native.runtimeRoot(source.gameObject)
        if sourceRoot ~= nil then
            local targetRoot = Native.runtimeRoot(target.gameObject)
            if targetRoot == nil then
                error("effect copy lost its runtime root: " .. tostring(target.gameObject.name))
            end
            targetRoot:AdoptClone(sourceRoot)
        end
        for index = 0, source.childCount - 1 do
            pending[#pending + 1] = { source:GetChild(index), target:GetChild(index) }
        end
    end
end

-- 与 C# ResolvePoolTemplate 同规则：沿父链逐层找同名直接子节点，只认效果根，同名的容器或发射节点跳过。
function Native.resolve(gameObject, key)
    local normalized = key:match("^%s*(.-)%s*$")
    if normalized == "" then
        return nil
    end
    local node = gameObject.transform
    while node ~= nil do
        for index = 0, node.childCount - 1 do
            local child = node:GetChild(index).gameObject
            if child.name == normalized and Native.isEffectRoot(child) then
                return child
            end
        end
        node = node.parent
    end
    return nil
end

-- 与 studio 同规则：引用自身或子树里的唯一效果根，多个返回歧义；没有身份信息就是找不到，不按结构猜。
function Native.resolveReferenced(gameObject)
    return findMarkedRoot(gameObject, Native.isEffectRoot)
end

-- 预览端效果资源异步加载，未就绪前粒子还没还原；发布态粒子已落盘，始终就绪。
function Native.isReady(template)
    local root = Native.runtimeRoot(template)
    if root == nil then
        return true
    end
    local ok, ready = pcall(function()
        return root.IsReady
    end)
    return not ok or ready == true
end

function Native.isLooping(template)
    for _, system in ipairs(Native.owned(template).all) do
        if system.main.loop == true then
            return true
        end
    end
    return false
end

-- 先整体 Stop+Clear 再逐个 Play，对应 C# EffectRuntimeRoot.Play；只碰根自己的粒子，不重置嵌套的效果根。
function Native.restart(gameObject, info)
    local clear = CS.UnityEngine.ParticleSystemStopBehavior.StopEmittingAndClear
    for _, system in ipairs(info.all) do
        system:Stop(false, clear)
    end
    for _, system in ipairs(info.playable) do
        if system.gameObject.activeInHierarchy then
            system:Play(false)
        end
    end
end

-- 预览端与发布版客户端都在 Lua 全局提供 setTimeout / clearTimeout，按 Time.time 在主循环派发。
-- 宿主没有时返回 nil，收尾退回 sweep，在下次调用本模块时补做。
function Native.schedule(callback, seconds)
    local set = setTimeout
    if set == nil then
        return nil
    end
    local ok, id = pcall(set, callback, math.max(1, math.ceil(seconds * 1000)))
    return ok and id or nil
end

function Native.unschedule(id)
    if id ~= nil and clearTimeout ~= nil then
        pcall(clearTimeout, id)
    end
end

function Native.removeFade(fade)
    Native.unschedule(fade.timer)
    fade.timer = nil
    for index = #Native.fades, 1, -1 do
        if Native.fades[index] == fade then
            table.remove(Native.fades, index)
        end
    end
end

function Native.cancelFade(gameObject)
    local id = gameObject:GetInstanceID()
    for index = #Native.fades, 1, -1 do
        local fade = Native.fades[index]
        if fade.id == id then
            Native.removeFade(fade)
        end
    end
end

-- 粒子飞完或超时就隐藏模板；返回这条收尾是否已了结。
function Native.settleFade(fade, now)
    if Native.isDestroyed(fade.go) then
        return true
    end
    local age = now - fade.startTime
    if age < Native.FadeGraceSeconds or (age < Native.FadeTimeoutSeconds and Native.isAlive(fade.info)) then
        return false
    end
    pcall(function()
        fade.go:SetActive(false)
    end)
    return true
end

-- 已被重播或立即停止取消的收尾不在表里，迟到的回调据此放弃，不会隐藏重新播放的模板。
function Native.watchFade(fade)
    local function tick()
        fade.timer = nil
        local pending = false
        for _, entry in ipairs(Native.fades) do
            pending = pending or entry == fade
        end
        if not pending then
            return
        end
        local ok, settled = pcall(Native.settleFade, fade, CS.UnityEngine.Time.time)
        if not ok or settled then
            Native.removeFade(fade)
            return
        end
        fade.timer = Native.schedule(tick, Native.FadePollSeconds)
    end
    fade.timer = Native.schedule(tick, Native.FadeGraceSeconds)
end

-- 与 C# PlayTemplate 一致：资源未就绪时不激活、不播放，避免露出尚未还原参数的粒子。
function Native.play(template)
    if not Native.isReady(template) then
        return false
    end
    Native.cancelFade(template)
    if not template.activeSelf then
        template:SetActive(true)
    end
    Native.restart(template, Native.owned(template))
    return true
end

-- 与 C# StopTemplate 一致：自然收尾先停发射，粒子飞完后隐藏，否则附属节点常显、祖先重新激活时还会重播。
function Native.stop(template, immediate)
    Native.cancelFade(template)
    local info = Native.collect(template)
    local behavior = CS.UnityEngine.ParticleSystemStopBehavior
    if immediate then
        for _, system in ipairs(info.all) do
            system:Stop(false, behavior.StopEmittingAndClear)
        end
        template:SetActive(false)
        return
    end
    if not template.activeSelf then
        return
    end
    for _, system in ipairs(info.all) do
        system:Stop(false, behavior.StopEmitting)
    end
    local fade = { go = template, id = template:GetInstanceID(), info = info, startTime = CS.UnityEngine.Time.time }
    Native.fades[#Native.fades + 1] = fade
    Native.watchFade(fade)
end

function Native.isAlive(info)
    for _, system in ipairs(info.all) do
        local ok, alive = pcall(function()
            return system:IsAlive(true)
        end)
        if ok and alive then
            return true
        end
    end
    return false
end

-- 倍率不是曲线寿命的上界，副本必须等整棵子树的粒子结束；与 C# 非循环池一样保留 30 秒超时。
-- 引擎先登记销毁兜底，宿主没有定时器、收集失败或后续调度失败时也不会永久留下副本。
function Native.finishSpawn(copy)
    destroyObject(copy, Native.FadeTimeoutSeconds)
    local info = Native.collect(copy)
    local startTime = CS.UnityEngine.Time.time
    local function tick()
        if Native.isDestroyed(copy) then
            return
        end
        local ok, finished = pcall(function()
            return CS.UnityEngine.Time.time - startTime >= Native.FadeTimeoutSeconds or not Native.isAlive(info)
        end)
        if not ok then
            return
        end
        if finished then
            destroyObject(copy)
            return
        end
        Native.schedule(tick, Native.FadePollSeconds)
    end
    Native.schedule(tick, Native.FadeGraceSeconds)
end

-- 每次调用本模块时补做：宿主没有定时器时由这里收尾，并清掉已销毁副本的记录。
function Native.sweep()
    local now = CS.UnityEngine.Time.time
    for index = #Native.fades, 1, -1 do
        local fade = Native.fades[index]
        if fade ~= nil and Native.settleFade(fade, now) then
            Native.removeFade(fade)
        end
    end
    for id, live in pairs(Native.copies) do
        for index = #live, 1, -1 do
            if Native.isDestroyed(live[index]) then
                table.remove(live, index)
            end
        end
        if #live == 0 then
            Native.copies[id] = nil
        end
    end
end

-- 未指定 parent 的副本挂到调用方所在世界根下的池节点，随世界一起销毁，不留在场景根上跨会话存活。
function Native.copyParent(context)
    local transform = resolveTransform(context)
    if transform == nil then
        return nil
    end
    local root = transform.root
    if not root.gameObject.activeInHierarchy then
        return nil
    end
    local pool = root:Find(Native.PoolRootName)
    if pool == nil then
        pool = CS.UnityEngine.GameObject(Native.PoolRootName).transform
        pool:SetParent(root, false)
    end
    return pool
end

-- 每个模板最多保留 8 个在播副本，超出时销毁最早的，等效于 C# 池满后重启最早一个。
function Native.track(template, copy)
    local id = template:GetInstanceID()
    local live = Native.copies[id]
    if live == nil then
        live = {}
        Native.copies[id] = live
    end
    live[#live + 1] = copy
    while #live > Native.CopyCapacity do
        destroyObject(table.remove(live, 1))
    end
end

-- 加载时一次性选定后端；两者都没有时整个模块降级为空操作，绝不能让 require 或调用打断 chunk。
local backend = nil
do
    local ok, value = pcall(function()
        return CS.EffectSystem.Ins
    end)
    if ok and isRealCsValue(value) then
        Studio.system = value
        backend = Studio
    else
        local typeOk, particleSystem = pcall(function()
            return CS.UnityEngine.ParticleSystem
        end)
        if typeOk and isRealCsValue(particleSystem) then
            backend = Native
        end
    end
end

-- 收尾和副本记录的清理不能打断调用方，失败只留到下次再试。
local function sweep()
    if backend ~= nil and backend.sweep ~= nil then
        pcall(backend.sweep)
    end
end

local function resolveTemplate(context, key)
    if backend == nil then
        logger:warnOnce(Effect.Reason.Unavailable, "effect playback disabled: host has no EffectSystem")
        return nil, Effect.Reason.Unavailable
    end
    sweep()

    local gameObject = resolveGameObject(context)
    if gameObject == nil then
        return nil, Effect.Reason.InvalidContext
    end
    if type(key) ~= "string" then
        local valid, isGameObject = pcall(function()
            return typeof(CS.UnityEngine.GameObject):IsInstanceOfType(key)
        end)
        if not valid or not isGameObject then
            return nil, Effect.Reason.InvalidKey
        end
        local ok, template, reason = pcall(backend.resolveReferenced, key)
        if not ok then
            return nil, Effect.Reason.NotFound
        end
        return template, reason
    end
    if key == "" then
        return nil, Effect.Reason.InvalidKey
    end

    local ok, template = pcall(backend.resolve, gameObject, key)
    if not ok or template == nil then
        logger:warnOnce("not-found:" .. key, "effect not found in this resource:", key)
        return nil, Effect.Reason.NotFound
    end
    return template
end

local function isReady(template)
    local ok, ready = pcall(backend.isReady, template)
    return ok and ready == true
end

local function isLooping(template)
    local ok, looping = pcall(backend.isLooping, template)
    return ok and looping == true
end

local function isActiveInHierarchy(gameObject)
    local ok, active = pcall(function()
        return gameObject.activeInHierarchy
    end)
    return ok and active == true
end

-- 与生成侧「发射时长 ≤30 秒」预算及宿主池的超时回收一致。
local PLAYBACK_LIMIT_SECONDS = 30
local PLAYBACK_MARGIN_SECONDS = 1

--- 复制模板并摆好后播放；失败时销毁副本并返回原因。
local function playCopy(context, template, key, position, options)
    local copy = nil
    local ok, failure = pcall(function()
        local source = template.transform
        local rotation = options ~= nil and options.rotation or source.rotation
        local scale = options ~= nil and options.scale or 1
        local parent = options ~= nil and resolveTransform(options.parent) or nil
        if parent == nil and backend.copyParent ~= nil then
            -- 取不到池节点时退回场景根，不让收纳失败挡住播放。
            local found, pool = pcall(backend.copyParent, context)
            parent = found and pool or nil
        end
        copy = CS.UnityEngine.Object.Instantiate(template, position or source.position, rotation)
        backend.adopt(template, copy)
        local transform = copy.transform
        if parent ~= nil then
            transform:SetParent(parent, true)
        end
        local baseScale = source.localScale
        transform.localScale = CS.UnityEngine.Vector3(baseScale.x * scale, baseScale.y * scale, baseScale.z * scale)
        -- 副本沿用模板的激活状态；studio 激活时由 MonoChain.Awake 按复制来源接管特效资源。
        copy:SetActive(true)
    end)
    if ok and copy ~= nil then
        local played, result = pcall(backend.play, copy)
        if played and result == true and isActiveInHierarchy(copy) then
            return copy
        end
        failure = "instance did not play"
    end
    local inactive = ok and copy ~= nil and not isActiveInHierarchy(copy)
    destroyObject(copy)
    if inactive then
        return nil, Effect.Reason.Inactive
    end
    logger:warnOnce("copy-failed:" .. tostring(key), "effect copy failed:", key, failure)
    return nil, Effect.Reason.SpawnFailed
end

--- 循环特效没有结束信号：关闭副本自身粒子的循环，完整发射一个周期后停止、自然消散。
--- 只改副本，共享模板仍是循环特效。
local function stopLoopingAfterOneCycle(copy)
    pcall(function()
        local systems = copy:GetComponentsInChildren(typeof(CS.UnityEngine.ParticleSystem), true)
        for index = 0, systems.Length - 1 do
            local system = systems[index]
            system.main.loop = false
            -- 预热把开播时刻推到周期末尾，关闭循环后会立即停发；拨回起点以保留预热外观并完整发射一个周期。
            if system.isPlaying then
                system.time = 0
            end
        end
    end)
end

-- Studio 循环副本的延时销毁估算：延迟 + 发射时长 + 寿命倍率，按 simulationSpeed 换算并累加子发射器。
local function playbackSeconds(copy)
    local ok, seconds = pcall(function()
        local array = copy:GetComponentsInChildren(typeof(CS.UnityEngine.ParticleSystem), true)
        local systems, spans, parents = {}, {}, {}
        for index = 0, array.Length - 1 do
            local system = array[index]
            local main = system.main
            local simulated = main.startDelayMultiplier + main.duration + main.startLifetimeMultiplier
            -- 下限与特效预览采样一致。
            spans[system] = simulated / math.max(0.01, main.simulationSpeed)
            systems[#systems + 1] = system
        end
        for _, system in ipairs(systems) do
            pcall(function()
                local module = system.subEmitters
                if not module.enabled then
                    return
                end
                for subIndex = 0, module.subEmittersCount - 1 do
                    local target = module:GetSubEmitterSystem(subIndex)
                    if target ~= nil and spans[target] ~= nil then
                        parents[target] = parents[target] or {}
                        table.insert(parents[target], system)
                    end
                end
            end)
        end
        local finish = {}
        local function finishOf(system, depth)
            if finish[system] == nil then
                local start = 0
                -- 深度上限挡住异常数据里的子发射器环。
                if depth < #systems then
                    for _, parent in ipairs(parents[system] or {}) do
                        start = math.max(start, finishOf(parent, depth + 1))
                    end
                end
                finish[system] = start + spans[system]
            end
            return finish[system]
        end
        local longest = 0
        for _, system in ipairs(systems) do
            longest = math.max(longest, finishOf(system, 0))
        end
        return longest + PLAYBACK_MARGIN_SECONDS
    end)
    if not ok or type(seconds) ~= "number" then
        return PLAYBACK_LIMIT_SECONDS
    end
    return math.min(seconds, PLAYBACK_LIMIT_SECONDS)
end

--- 播放一次，结束后自动回收，调用方不销毁返回的副本。
--- studio 非循环特效从宿主池取副本；Native 副本按粒子实际结束销毁，Studio 循环副本沿用延时销毁。
--- key 支持效果根名称或 GameObject 引用；position 省略时使用模板位置，此时忽略 options。
--- options 支持 rotation / scale / parent。
function Effect.spawn(context, key, position, options)
    local template, reason = resolveTemplate(context, key)
    if template == nil then
        return nil, reason
    end
    if not isReady(template) then
        logger:warnOnce("not-ready:" .. tostring(key), "effect is still loading:", key)
        return nil, Effect.Reason.NotReady
    end
    local looping = isLooping(template)
    if looping or backend.spawn == nil then
        local copy, failure = playCopy(context, template, key, position, position ~= nil and options or nil)
        if copy == nil then
            return nil, failure
        end
        if looping then
            stopLoopingAfterOneCycle(copy)
        end
        if backend.finishSpawn ~= nil then
            pcall(backend.finishSpawn, copy)
        else
            destroyObject(copy, playbackSeconds(copy))
        end
        if backend.track ~= nil then
            pcall(backend.track, template, copy)
        end
        return copy
    end

    local gameObject = resolveGameObject(context)
    local ok, instance, failure = pcall(backend.spawn, gameObject, template, key, position, options)
    if ok and instance == nil and failure ~= nil then
        return nil, failure
    end
    if not ok or instance == nil then
        logger:warnOnce("spawn-failed:" .. tostring(key), "effect spawn failed:", key, ok and "pool exhausted" or instance)
        return nil, Effect.Reason.SpawnFailed
    end
    return instance
end

local Handle = {}
Handle.__index = Handle

--- 播放句柄控制的那一个对象；重复调用会打断上一次。返回是否实际在播放。
--- 宿主只激活对象自身：祖先未激活时返回 false，祖先激活后对象按 OnEnable 自行播放。
--- 资产引用模板挂在关闭的缓存层级下，因此 find 句柄对它始终返回 false。
function Handle:Play()
    local target = self.target
    if target == nil then
        return false
    end
    sweep()
    local ok, played = pcall(backend.play, target)
    return ok and played == true and isActiveInHierarchy(target)
end

--- 默认停止发射，粒子消散后隐藏；immediate=true 立即清空粒子并隐藏。
function Handle:Stop(immediate)
    local target = self.target
    if target == nil then
        return false
    end
    sweep()
    return pcall(backend.stop, target, immediate == true)
end

--- 销毁 Effect.create 创建的实例，残留粒子一并清除。find 句柄不拥有模板，调用无效果并返回 false。
function Handle:Release()
    local target = self.target
    if not self.owned or target == nil then
        return false
    end
    self.target = nil
    destroyObject(target)
    return true
end

function Handle:IsReady()
    return self.target ~= nil and isReady(self.target)
end

function Handle:IsLooping()
    return self.target ~= nil and isLooping(self.target)
end

function Handle:GetGameObject()
    return self.target
end

--- 按名称或 GameObject 引用取模板自身的句柄，用于控制场景中已有的效果根。
--- 资产引用模板位于关闭的缓存层级，Play 返回 false；需要播放时用 Effect.create。
function Effect.find(context, key)
    local template, reason = resolveTemplate(context, key)
    if template == nil then
        return nil, reason
    end
    return setmetatable({ key = key, target = template }, Handle)
end

--- 复制模板得到调用方独占的实例，摆好后立即播放；循环与一次性特效都可用。
--- 实例不进池，不再需要时调用 handle:Release()；跟随的 parent 被销毁时实例随之销毁。
--- position 省略时使用模板位置；options 支持 rotation / scale / parent，parent 须处于激活层级。
function Effect.create(context, key, position, options)
    local template, reason = resolveTemplate(context, key)
    if template == nil then
        return nil, reason
    end
    if not isReady(template) then
        logger:warnOnce("not-ready:" .. tostring(key), "effect is still loading:", key)
        return nil, Effect.Reason.NotReady
    end
    local copy, failure = playCopy(context, template, key, position, options)
    if copy == nil then
        return nil, failure
    end
    return setmetatable({ key = key, target = copy, owned = true }, Handle)
end

--- 宿主是否提供特效播放能力（编辑器 EffectSystem，或预览端、发布态的原生 ParticleSystem）。
function Effect.isAvailable()
    return backend ~= nil
end

return Effect
