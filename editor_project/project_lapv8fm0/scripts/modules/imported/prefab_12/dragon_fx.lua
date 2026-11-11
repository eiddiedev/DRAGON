---@id b5cc4460-2fe5-4de6-b183-4f4cab2e73c8
---@sourceScriptId 6329c644-9169-4c74-b1c2-6cf72ca3dae4
---@referenceName dragon_fx.lua
---@displayName 龙眠职业粒子特效
---@var SlashEffect:UnityEngine.GameObject=nil
---@name 战士弧形刀光
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var ShieldEffect:UnityEngine.GameObject=nil
---@name 战士守护震波
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var BoltEffect:UnityEngine.GameObject=nil
---@name 法师飞弹拖尾
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var ArrowEffect:UnityEngine.GameObject=nil
---@name 游侠箭矢拖尾
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var BlastEffect:UnityEngine.GameObject=nil
---@name 奥术星爆
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var HitEffect:UnityEngine.GameObject=nil
---@name 命中火花
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var TellEffect:UnityEngine.GameObject=nil
---@name 敌袭地面预警
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var ArenaEffect:UnityEngine.GameObject=nil
---@name 试炼边界流光
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var FrostEffect:UnityEngine.GameObject=nil
---@name 霜星冲击
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var MeteorEffect:UnityEngine.GameObject=nil
---@name 陨星冲击
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var BowSound:UnityEngine.AudioClip=nil
---@name 射箭音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var BowSoundVolume:number=0.65
---@name 射箭音量
---@var BowSoundMaxDistance:number=25
---@name 射箭最大作用范围
---@var EnemySound:UnityEngine.AudioClip=nil
---@name 怪物攻击音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var EnemySoundVolume:number=0.65
---@name 怪物攻击音量
---@var EnemySoundMaxDistance:number=25
---@name 怪物攻击最大作用范围
---@var HurtSound:UnityEngine.AudioClip=nil
---@name 受伤音效
---@refFrom asset
---@assetCategory Music
---@dataType Audio
---@var HurtSoundVolume:number=0.65
---@name 受伤音量
---@var HurtSoundMaxDistance:number=25
---@name 受伤最大作用范围
local U=CS.UnityEngine
local V=U.Vector3
local Effect=require('official.effect.playback')
local AudioClip=U.AudioClip
local logger=require('official.core.logger').create('dragon-combat-audio')
local SAMPLE_RATE = 22050

local SOUND_NAMES = {
  "v2-sword-swing",
  "v2-sword-hit",
  "v2-giant-awaken",
  "v2-giant-hit",
  "v2-bow-release",
  "v2-arrow-hit",
  "v2-leaf-charge",
  "v2-leaf-whoosh",
  "v2-leaf-hit",
  "v2-rain-fall",
  "v2-rain-hit",
  "v2-magic-shot",
  "v2-magic-hit",
  "v2-magic-burst",
  "v2-meteor-fall",
  "v2-meteor-impact",
  "v2-cannon-fire",
  "v2-cannon-explode",
  "v2-time-hit",
  "v2-wall-break",
  "v2-coin",
  "v2-dash",
}

local DURATIONS = {
  ["v2-sword-swing"] = 0.24,
  ["v2-sword-hit"] = 0.28,
  ["v2-giant-awaken"] = 0.95,
  ["v2-giant-hit"] = 0.5,
  ["v2-bow-release"] = 0.22,
  ["v2-arrow-hit"] = 0.2,
  ["v2-leaf-charge"] = 0.6,
  ["v2-leaf-whoosh"] = 0.26,
  ["v2-leaf-hit"] = 0.18,
  ["v2-rain-fall"] = 0.75,
  ["v2-rain-hit"] = 0.14,
  ["v2-magic-shot"] = 0.26,
  ["v2-magic-hit"] = 0.3,
  ["v2-magic-burst"] = 0.6,
  ["v2-meteor-fall"] = 0.95,
  ["v2-meteor-impact"] = 0.75,
  ["v2-cannon-fire"] = 0.45,
  ["v2-cannon-explode"] = 0.75,
  ["v2-time-hit"] = 0.32,
  ["v2-wall-break"] = 0.55,
  ["v2-coin"] = 0.38,
  ["v2-dash"] = 0.22,
}

local PEAKS = {
  ["v2-sword-swing"] = 0.82,
  ["v2-sword-hit"] = 0.92,
  ["v2-giant-awaken"] = 0.78,
  ["v2-giant-hit"] = 0.94,
  ["v2-bow-release"] = 0.82,
  ["v2-arrow-hit"] = 0.86,
  ["v2-leaf-charge"] = 0.7,
  ["v2-leaf-whoosh"] = 0.82,
  ["v2-leaf-hit"] = 0.78,
  ["v2-rain-fall"] = 0.5,
  ["v2-rain-hit"] = 0.62,
  ["v2-magic-shot"] = 0.84,
  ["v2-magic-hit"] = 0.88,
  ["v2-magic-burst"] = 0.94,
  ["v2-meteor-fall"] = 0.8,
  ["v2-meteor-impact"] = 0.96,
  ["v2-cannon-fire"] = 0.93,
  ["v2-cannon-explode"] = 0.96,
  ["v2-time-hit"] = 0.76,
  ["v2-wall-break"] = 0.92,
  ["v2-coin"] = 0.7,
  ["v2-dash"] = 0.82,
}

local SEEDS = {
  ["v2-sword-swing"] = 101,
  ["v2-sword-hit"] = 211,
  ["v2-giant-awaken"] = 307,
  ["v2-giant-hit"] = 401,
  ["v2-bow-release"] = 503,
  ["v2-arrow-hit"] = 601,
  ["v2-leaf-charge"] = 709,
  ["v2-leaf-whoosh"] = 809,
  ["v2-leaf-hit"] = 907,
  ["v2-rain-fall"] = 1009,
  ["v2-rain-hit"] = 1103,
  ["v2-magic-shot"] = 1201,
  ["v2-magic-hit"] = 1301,
  ["v2-magic-burst"] = 1409,
  ["v2-meteor-fall"] = 1511,
  ["v2-meteor-impact"] = 1601,
  ["v2-cannon-fire"] = 1709,
  ["v2-cannon-explode"] = 1801,
  ["v2-time-hit"] = 1907,
  ["v2-wall-break"] = 2003,
  ["v2-coin"] = 2101,
  ["v2-dash"] = 2203,
}

local sources = {}
local clips = {}
local ready = false
local audioRootTransform = nil
local rngState = 1

local function setSeed(seed)
  rngState = seed % 2147483647
  if rngState <= 0 then
    rngState = 1
  end
end

local function randomUnit()
  rngState = (rngState * 48271) % 2147483647
  return rngState / 2147483647
end

local function noise()
  return randomUnit() * 2 - 1
end

local function envelope(t, duration, attack, release)
  local attackTime = attack or 0.004
  local releaseTime = release or 0.04
  if attackTime <= 0 then
    attackTime = 0.0005
  end
  if releaseTime <= 0 then
    releaseTime = 0.005
  end
  if t < attackTime then
    return t / attackTime
  end
  if t > duration - releaseTime then
    local remain = duration - t
    if remain <= 0 then
      return 0
    end
    return remain / releaseTime
  end
  return 1
end

local function addNoise(samples, startTime, duration, gain, cutoffStart, cutoffEnd, attack, release, highpass)
  local count = #samples
  local startIndex = math.floor(startTime * SAMPLE_RATE) + 1
  local endIndex = math.min(count, math.floor((startTime + duration) * SAMPLE_RATE))
  local lowpass = 0
  local highpassState = 0
  local previous = 0
  for index = startIndex, endIndex do
    local t = (index - 1) / SAMPLE_RATE - startTime
    local ratio = t / duration
    local cutoff = cutoffStart + (cutoffEnd - cutoffStart) * ratio
    local alpha = 1 - math.exp(-2 * math.pi * cutoff / SAMPLE_RATE)
    local white = noise()
    local value
    if highpass then
      highpassState = alpha * (highpassState + white - previous)
      previous = white
      value = highpassState
    else
      lowpass = lowpass + alpha * (white - lowpass)
      value = lowpass
    end
    samples[index] = samples[index] + value * gain * envelope(t, duration, attack, release)
  end
end

local function addTone(samples, startTime, duration, frequencyStart, frequencyEnd, gain, attack, release, vibratoHz, vibratoAmount)
  local count = #samples
  local startIndex = math.floor(startTime * SAMPLE_RATE) + 1
  local endIndex = math.min(count, math.floor((startTime + duration) * SAMPLE_RATE))
  local phase = 0
  for index = startIndex, endIndex do
    local t = (index - 1) / SAMPLE_RATE - startTime
    local ratio = t / duration
    local frequency = frequencyStart + (frequencyEnd - frequencyStart) * ratio
    if vibratoHz ~= nil then
      frequency = frequency + math.sin(2 * math.pi * vibratoHz * t) * vibratoAmount
    end
    phase = phase + 2 * math.pi * frequency / SAMPLE_RATE
    local value = math.sin(phase) + 0.3 * math.sin(phase * 2) + 0.12 * math.sin(phase * 3)
    samples[index] = samples[index] + value * gain * envelope(t, duration, attack, release)
  end
end

local function addMetal(samples, startTime, duration, baseFrequency, gain, decay)
  local count = #samples
  local startIndex = math.floor(startTime * SAMPLE_RATE) + 1
  local endIndex = math.min(count, math.floor((startTime + duration) * SAMPLE_RATE))
  local ratios = { 1, 2.37, 3.41, 4.73, 6.11 }
  local phases = { 0, 0.7, 1.9, 3.1, 4.4 }
  for index = startIndex, endIndex do
    local t = (index - 1) / SAMPLE_RATE - startTime
    local value = 0
    for partial = 1, 5 do
      local frequency = baseFrequency * ratios[partial]
      local partialDecay = math.exp(-t * decay * (1 + (partial - 1) * 0.35))
      value = value + math.sin(2 * math.pi * frequency * t + phases[partial]) * partialDecay / (partial * 0.8 + 1)
    end
    if t < 0.012 then
      value = value + noise() * math.exp(-t * 120) * 0.8
    end
    samples[index] = samples[index] + value * gain * envelope(t, duration, 0.002, 0.035)
  end
end

local function addThump(samples, startTime, duration, frequencyStart, frequencyEnd, gain, decay)
  local count = #samples
  local startIndex = math.floor(startTime * SAMPLE_RATE) + 1
  local endIndex = math.min(count, math.floor((startTime + duration) * SAMPLE_RATE))
  local phase = 0
  for index = startIndex, endIndex do
    local t = (index - 1) / SAMPLE_RATE - startTime
    local frequency = frequencyEnd + (frequencyStart - frequencyEnd) * math.exp(-t * 6)
    phase = phase + 2 * math.pi * frequency / SAMPLE_RATE
    local value = math.sin(phase) * math.exp(-t * decay)
    if t < 0.008 then
      value = value + noise() * 0.5
    end
    samples[index] = samples[index] + value * gain * envelope(t, duration, 0.003, 0.05)
  end
end

local function addSparkle(samples, startTime, duration, count, frequencyMin, frequencyMax, gain)
  local total = #samples
  for _ = 1, count do
    local offset = startTime + randomUnit() * duration * 0.8
    local frequency = frequencyMin + randomUnit() * (frequencyMax - frequencyMin)
    local length = 0.03 + randomUnit() * 0.06
    local startIndex = math.floor(offset * SAMPLE_RATE) + 1
    local endIndex = math.min(total, math.floor((offset + length) * SAMPLE_RATE))
    for index = startIndex, endIndex do
      local t = (index - 1) / SAMPLE_RATE - offset
      local value = math.sin(2 * math.pi * frequency * t) * math.exp(-t * 70)
      samples[index] = samples[index] + value * gain
    end
  end
end

local function addCrackle(samples, startTime, duration, count, gain)
  local total = #samples
  for _ = 1, count do
    local offset = startTime + randomUnit() * duration
    local length = 0.008 + randomUnit() * 0.02
    local startIndex = math.floor(offset * SAMPLE_RATE) + 1
    local endIndex = math.min(total, math.floor((offset + length) * SAMPLE_RATE))
    local lowpass = 0
    for index = startIndex, endIndex do
      local t = (index - 1) / SAMPLE_RATE - offset
      local white = noise()
      lowpass = lowpass + 0.55 * (white - lowpass)
      samples[index] = samples[index] + lowpass * gain * math.exp(-t * 160)
    end
  end
end

local function normalize(samples, peak)
  local maximum = 0
  for index = 1, #samples do
    local value = math.abs(samples[index])
    if value > maximum then
      maximum = value
    end
  end
  if maximum <= 0 then
    return
  end
  local scale = peak / maximum
  for index = 1, #samples do
    samples[index] = samples[index] * scale
  end
end

local function buildSamples(name)
  local duration = DURATIONS[name] or 0.3
  local count = math.floor(SAMPLE_RATE * duration)
  local samples = {}
  for index = 1, count do
    samples[index] = 0
  end
  setSeed(SEEDS[name] or 12345)

  if name == "v2-sword-swing" then
    addNoise(samples, 0, 0.22, 1.0, 2600, 600, 0.003, 0.18, false)
    addNoise(samples, 0.01, 0.16, 0.35, 6000, 1400, 0.003, 0.14, true)
    addTone(samples, 0, 0.16, 500, 220, 0.12, 0.004, 0.12)
  elseif name == "v2-sword-hit" then
    addNoise(samples, 0, 0.05, 0.6, 5000, 1500, 0.001, 0.04, false)
    addMetal(samples, 0, 0.26, 620, 0.9, 18)
    addThump(samples, 0, 0.18, 150, 55, 0.7, 16)
  elseif name == "v2-giant-awaken" then
    addThump(samples, 0, 0.9, 70, 38, 0.8, 4)
    addNoise(samples, 0, 0.95, 0.35, 300, 120, 0.25, 0.4, false)
    addMetal(samples, 0.25, 0.75, 150, 0.25, 3)
    addTone(samples, 0.2, 0.7, 55, 90, 0.25, 0.2, 0.3)
  elseif name == "v2-giant-hit" then
    addThump(samples, 0, 0.4, 120, 40, 1.0, 10)
    addMetal(samples, 0, 0.38, 180, 0.5, 12)
    addNoise(samples, 0, 0.3, 0.45, 900, 180, 0.002, 0.2, false)
  elseif name == "v2-bow-release" then
    addTone(samples, 0, 0.18, 260, 90, 0.35, 0.002, 0.15)
    addNoise(samples, 0, 0.2, 0.5, 3500, 900, 0.002, 0.16, false)
    addTone(samples, 0, 0.1, 820, 320, 0.18, 0.002, 0.08)
  elseif name == "v2-arrow-hit" then
    addNoise(samples, 0, 0.16, 0.55, 3000, 500, 0.001, 0.13, false)
    addThump(samples, 0, 0.16, 220, 80, 0.6, 22)
    addMetal(samples, 0, 0.14, 420, 0.35, 25)
  elseif name == "v2-leaf-charge" then
    addTone(samples, 0, 0.55, 300, 950, 0.3, 0.08, 0.2)
    addNoise(samples, 0.05, 0.5, 0.25, 900, 2800, 0.06, 0.16, false)
    addSparkle(samples, 0, 0.5, 6, 1200, 3200, 0.25)
  elseif name == "v2-leaf-whoosh" then
    addNoise(samples, 0, 0.24, 0.7, 1800, 400, 0.002, 0.2, false)
    addNoise(samples, 0.01, 0.2, 0.25, 6000, 1800, 0.002, 0.16, true)
    addTone(samples, 0, 0.15, 600, 260, 0.12, 0.003, 0.12)
  elseif name == "v2-leaf-hit" then
    addNoise(samples, 0, 0.14, 0.55, 2200, 600, 0.001, 0.11, false)
    addThump(samples, 0, 0.14, 200, 90, 0.4, 24)
    addCrackle(samples, 0, 0.12, 3, 0.4)
  elseif name == "v2-rain-fall" then
    addNoise(samples, 0, 0.7, 0.35, 4000, 1200, 0.1, 0.3, false)
    addSparkle(samples, 0.05, 0.6, 10, 1800, 5200, 0.18)
    addNoise(samples, 0.1, 0.6, 0.15, 900, 2000, 0.08, 0.24, true)
  elseif name == "v2-rain-hit" then
    addNoise(samples, 0, 0.12, 0.6, 5000, 1800, 0.001, 0.1, false)
    addTone(samples, 0, 0.08, 1400, 900, 0.15, 0.001, 0.06)
    addSparkle(samples, 0, 0.1, 2, 2500, 4500, 0.2)
  elseif name == "v2-magic-shot" then
    addTone(samples, 0, 0.22, 500, 1500, 0.4, 0.002, 0.16)
    addSparkle(samples, 0, 0.22, 5, 1500, 5000, 0.3)
    addNoise(samples, 0, 0.18, 0.25, 3000, 6000, 0.002, 0.14, true)
  elseif name == "v2-magic-hit" then
    addMetal(samples, 0, 0.26, 760, 0.55, 20)
    addSparkle(samples, 0, 0.28, 8, 1800, 6000, 0.35)
    addNoise(samples, 0, 0.2, 0.3, 4000, 800, 0.001, 0.16, false)
  elseif name == "v2-magic-burst" then
    addThump(samples, 0, 0.5, 140, 50, 0.7, 8)
    addMetal(samples, 0, 0.5, 420, 0.45, 7)
    addSparkle(samples, 0.02, 0.55, 14, 1200, 6000, 0.35)
    addNoise(samples, 0, 0.6, 0.45, 2600, 300, 0.004, 0.4, false)
  elseif name == "v2-meteor-fall" then
    addNoise(samples, 0, 0.9, 0.65, 600, 100, 0.3, 0.35, false)
    addThump(samples, 0, 0.9, 55, 75, 0.35, 3)
    addCrackle(samples, 0.1, 0.7, 8, 0.25)
    addTone(samples, 0.1, 0.8, 45, 70, 0.3, 0.3, 0.3)
  elseif name == "v2-meteor-impact" then
    addThump(samples, 0, 0.7, 80, 28, 1.2, 6)
    addNoise(samples, 0, 0.65, 0.8, 1500, 90, 0.002, 0.4, false)
    addMetal(samples, 0, 0.6, 220, 0.5, 6)
    addCrackle(samples, 0.02, 0.48, 12, 0.5)
  elseif name == "v2-cannon-fire" then
    addThump(samples, 0, 0.38, 160, 45, 1.0, 10)
    addNoise(samples, 0, 0.4, 0.65, 2600, 220, 0.002, 0.3, false)
    addMetal(samples, 0, 0.3, 380, 0.3, 16)
  elseif name == "v2-cannon-explode" then
    addThump(samples, 0, 0.65, 70, 24, 1.2, 6)
    addNoise(samples, 0, 0.7, 0.85, 1400, 70, 0.002, 0.45, false)
    addCrackle(samples, 0.02, 0.53, 10, 0.45)
    addMetal(samples, 0, 0.5, 240, 0.4, 8)
  elseif name == "v2-time-hit" then
    addMetal(samples, 0, 0.3, 980, 0.5, 18)
    addSparkle(samples, 0, 0.3, 5, 2000, 7000, 0.35)
    addTone(samples, 0, 0.12, 1200, 800, 0.2, 0.001, 0.1)
    addNoise(samples, 0, 0.1, 0.2, 5000, 1500, 0.001, 0.08, false)
  elseif name == "v2-wall-break" then
    addCrackle(samples, 0, 0.45, 12, 0.6)
    addNoise(samples, 0, 0.5, 0.7, 1800, 250, 0.002, 0.35, false)
    addThump(samples, 0, 0.4, 110, 45, 0.7, 12)
    addMetal(samples, 0, 0.4, 300, 0.35, 10)
  elseif name == "v2-coin" then
    addTone(samples, 0, 0.3, 1180, 1180, 0.35, 0.002, 0.25)
    addTone(samples, 0.06, 0.28, 1760, 1760, 0.3, 0.002, 0.22)
    addSparkle(samples, 0, 0.25, 3, 2500, 6000, 0.2)
    addMetal(samples, 0, 0.2, 1600, 0.2, 30)
  elseif name == "v2-dash" then
    addNoise(samples, 0, 0.2, 0.7, 3000, 700, 0.002, 0.16, false)
    addNoise(samples, 0.01, 0.18, 0.25, 7000, 2200, 0.002, 0.14, true)
    addTone(samples, 0, 0.18, 450, 180, 0.25, 0.003, 0.14)
  end

  normalize(samples, PEAKS[name] or 0.85)
  return duration, samples
end

local function buildClip(name)
  local ok, clip = pcall(function()
    local duration, samples = buildSamples(name)
    local count = math.floor(SAMPLE_RATE * duration)
    if count <= 0 then
      return nil
    end
    local made,created=pcall(function()return AudioClip.Create(name,count,1,SAMPLE_RATE,false)end)
    if not made or not created then created=AudioClip.Create(name,count,1,SAMPLE_RATE,false,false)end
    if created == nil then
      return nil
    end
    local filled = nil
    local arrayOk, data = pcall(function()
      return CS.System.Array.CreateInstance(typeof(CS.System.Single), count)
    end)
    if arrayOk and data ~= nil then
      local arraySetOk, arrayFilled = pcall(function()
        for index = 1, count do
          data[index - 1] = samples[index]
        end
        return created:SetData(data, 0)
      end)
      if arraySetOk then
        filled = arrayFilled
      end
    end
    if filled == nil or filled == false then
      local tableSetOk, tableFilled = pcall(function()
        return created:SetData(samples, 0)
      end)
      if tableSetOk then
        filled = tableFilled
      end
    end
    if filled == nil or filled == false then
      return nil
    end
    if created.samples ~= count or created.channels ~= 1 or created.frequency ~= SAMPLE_RATE then
      return nil
    end
    if false then
      pcall(function()
        created:LoadAudioData()
      end)
      if false then
        logger:warnOnce("clip-not-ready-" .. name, "clip is generated but not reported ready", name)
      end
    end
    if created.length <= 0 then
      return nil
    end
    return created
  end)
  if not ok or clip == nil then
    logger:warnOnce("clip-build-" .. name, "failed to synthesize audio clip", name)
    return nil
  end
  return clip
end


local audioClips={}
local audioPool={}
local audioRoot=nil
local audioPlayed=0
local audioFailed=0
local audioLast=nil
local audioLastTime={}
local warmIndex=1
local function sound(name,gain)
 local now=U.Time.time;if audioLastTime[name]and now-audioLastTime[name]<.07 then return end
 local clip=audioClips[name];if not clip then clip=buildClip(name);audioClips[name]=clip end
 if not clip then audioFailed=audioFailed+1;return end
 if not audioRoot then audioRoot=U.GameObject('DragonCombatAudio')end
 local source=nil
 for _,v in ipairs(audioPool)do if not v.isPlaying then source=v;break end end
 if not source and #audioPool<8 then local go=U.GameObject('CombatVoice'..#audioPool);go.transform:SetParent(audioRoot.transform,false);source=go:AddComponent(typeof(U.AudioSource));source.playOnAwake=false;source.spatialBlend=0;source.loop=false;audioPool[#audioPool+1]=source end
 if not source then return end
 source.volume=.48;source.mute=false;source.pitch=1;source:PlayOneShot(clip,gain or 1)
 audioLastTime[name]=now;audioPlayed=audioPlayed+1;audioLast=name
end
local originalSources={}
local function originalSound(kind,position)
 local config={Bow={BowSound,BowSoundVolume,BowSoundMaxDistance},Enemy={EnemySound,EnemySoundVolume,EnemySoundMaxDistance},Hurt={HurtSound,HurtSoundVolume,HurtSoundMaxDistance}}
 local c=config[kind];if not c or not c[1]or c[2]<=0 or c[3]<=0 then return end
 local v=originalSources[kind]
 if not v then local go=U.GameObject('OriginalCombatAudio_'..kind);local source=go:AddComponent(typeof(U.AudioSource));source.playOnAwake=false;source.spatialBlend=1;source.rolloffMode=U.AudioRolloffMode.Linear;v={go=go,source=source};originalSources[kind]=v end
 if v.clip~=c[1]then v.source:Stop();v.clip=c[1]end
 v.go.transform.position=position;v.source.volume=math.max(0,math.min(1,c[2]));v.source.minDistance=math.min(2,c[3]*.1);v.source.maxDistance=c[3];v.source:PlayOneShot(c[1]);audioPlayed=audioPlayed+1;audioLast='original-'..kind
end
function Hurt(p)originalSound('Hurt',p)end
local flying={}
local queued={}
local arena=nil
local arenaKey=nil
local wantedArena=nil
local arenaRetry=0
local emitted=0
local failed=0
local lastReason=nil
local function one(key,p,rotation,scale)
 if not key then return end
 local go,why=Effect.spawn(self,key,p,{rotation=rotation or U.Quaternion.identity,scale=scale or 1})
 if go then emitted=emitted+1 else failed=failed+1;lastReason=why end
end
local function projectile(key,p,d,speed,life,pierce)
 if not key or #flying>=18 then return end
 local h,why=Effect.create(self,key,p,{rotation=U.Quaternion.LookRotation(d,V.up),scale=1})
 if not h then failed=failed+1;lastReason=why;return end
 emitted=emitted+1
 flying[#flying+1]={h=h,p=p,d=d,speed=speed,start=U.Time.time,life=life,pierce=pierce,stop=false}
end
function Charge(kind,action,p,target)
 if action=='attack'then return end
 if kind=='mage'and action=='skill3'then
  sound('v2-meteor-fall');local start=target+V(-2,9,-1);projectile(BoltEffect,start,(target-start).normalized,10,.9)
 elseif kind=='ranged'and action=='skill3'then sound('v2-rain-fall')
 elseif kind=='melee'and action=='skill3'then sound('v2-giant-awaken',.8)
 elseif kind=='ranged'and action=='skill2'then sound('v2-leaf-charge',.75)end
end
function Area(kind,action,p,burst)
 if kind=='ranged'then
  sound('v2-rain-hit',.8)
  for i=1,7 do local a=i*2.39996;local radius=.6+(i%3)*.7;local at=p+V(math.cos(a)*radius,0,math.sin(a)*radius)
   projectile(ArrowEffect,at+V(0,4,0),V.down,25,.16);one(HitEffect,at,nil,.7)
  end
 elseif action=='skill2'then
  sound('v2-time-hit');one(FrostEffect,p,nil,1.1)
  for i=1,6 do local a=i*math.pi/3;projectile(BoltEffect,p,V(math.cos(a),.15,math.sin(a)),4,.45)end
 else sound(action=='skill3'and'v2-meteor-impact'or'v2-magic-burst');one(action=='skill3'and MeteorEffect or BlastEffect,p,nil,action=='skill3'and 1.8 or 1.4)
  if action=='skill3'then for i=1,7 do local a=i*2.39996;one(HitEffect,p+V(math.cos(a)*2,.1,math.sin(a)*2),nil,1.2)end end
 end
end
function Play(kind,action,origin,direction)
 local d=direction.sqrMagnitude>.001 and direction.normalized or V.forward
 local q=U.Quaternion.LookRotation(d,V.up)
 if action=='skill'then action='skill1'end
 if kind=='melee'then
  if action=='skill1'then sound('v2-giant-hit',.8);one(ShieldEffect,origin-V(0,.45,0),nil,1.5)
  elseif action=='skill2'then sound('v2-sword-swing');for i=0,2 do one(SlashEffect,origin,q*U.Quaternion.Euler(0,i*120,0),1.25)end
  elseif action=='skill3'then sound('v2-giant-hit');one(SlashEffect,origin,q*U.Quaternion.Euler(0,0,85),1.7);one(ShieldEffect,origin+d*2-V(0,.45,0),nil,1.2)
  else sound('v2-sword-swing');one(SlashEffect,origin+V(0,.05,0),q,1)end
 elseif kind=='mage'then
  if action~='attack'then Area(kind,action,origin+d*6,1)else sound('v2-magic-shot',.8);projectile(BoltEffect,origin,d,16,.75)end
 else
  if action=='skill3'then Area(kind,action,origin+d*6,1)
  elseif action=='skill1'then for i=0,4 do queued[#queued+1]={at=U.Time.time+i*.16,p=origin,d=d}end
  else originalSound('Bow',origin);projectile(ArrowEffect,origin,d,24,.75,action=='skill2');if action=='skill2'then projectile(ArrowEffect,origin+V(0,.1,0),d,24,.75,true)end end
 end
end
function Impact(kind,position,amount,class)
 if kind=='tell'then one(TellEffect,V(position.x,position.y-.5,position.z),nil,1.1)
 elseif kind=='blast'then one(BlastEffect,position,nil,1.25)
 elseif kind=='hit'then
  sound(class=='mage'and'v2-magic-hit'or(class=='ranged'and'v2-arrow-hit'or'v2-sword-hit'),.8)
  one(HitEffect,position,nil,1)
  -- End only nearby cosmetic flights; authoritative hit/damage lives in combat rules.
  for _,v in ipairs(flying)do
   if not v.stop then
    local age=U.Time.time-v.start;local p=v.p+v.d*(v.speed*math.min(age,v.life))
    if not v.pierce and (p-position).sqrMagnitude<1.5 then v.h:Stop();v.stop=true;v.release=U.Time.time+.35 end
   end
  end
 elseif kind=='strike'then originalSound('Enemy',position);one(HitEffect,V(position.x,position.y-.4,position.z),nil,.6)end
end
function SetArena(center,radius,visible)
 if not visible then wantedArena=nil;if arena then arena:Release();arena=nil;arenaKey=nil end;return end
 wantedArena={p=center,r=radius}
 if arenaKey~=ArenaEffect and arena then arena:Release();arena=nil end
 if not arena and ArenaEffect and U.Time.time>=arenaRetry then
  local why;arena,why=Effect.create(self,ArenaEffect,center,{scale=radius})
  arenaRetry=U.Time.time+.5
  if arena then arenaKey=ArenaEffect else lastReason=why end
 end
end
function Update()
 local now=U.Time.time
 if warmIndex<=#SOUND_NAMES then local name=SOUND_NAMES[warmIndex];audioClips[name]=audioClips[name]or buildClip(name);warmIndex=warmIndex+1 end
 for i=#queued,1,-1 do local q=queued[i];if now>=q.at then originalSound('Bow',q.p);projectile(ArrowEffect,q.p,q.d,24,.75);table.remove(queued,i)end end
 for i=#flying,1,-1 do
  local v=flying[i];local age=now-v.start
  if not v.stop then
   local go=v.h:GetGameObject()
   if go then go.transform.position=v.p+v.d*(v.speed*math.min(age,v.life))end
   if age>=v.life then v.h:Stop();v.stop=true;v.release=now+.4 end
  elseif now>=v.release then v.h:Release();table.remove(flying,i)end
 end
 if wantedArena and not arena then SetArena(wantedArena.p,wantedArena.r,true)end
end
function GetStatus()
 local playing=0;for _,s in ipairs(audioPool)do if s.isPlaying then playing=playing+1 end end
 return{audio={played=audioPlayed,failed=audioFailed,last=audioLast,playing=playing,warmed=warmIndex-1},available=Effect.isAvailable(),emitted=emitted,failed=failed,lastReason=lastReason,flying=#flying,arena=arena~=nil,refs={frost=FrostEffect~=nil,meteor=MeteorEffect~=nil,slash=SlashEffect~=nil,shield=ShieldEffect~=nil,bolt=BoltEffect~=nil,arrow=ArrowEffect~=nil,blast=BlastEffect~=nil,hit=HitEffect~=nil,tell=TellEffect~=nil}}
end
function Clear()
 for _,v in ipairs(flying)do v.h:Release()end;flying={}
 SetArena(V.zero,1,false);queued={}
end
function OnDisable()Clear()end
function OnDestroy()
 for _,v in pairs(originalSources)do v.source:Stop();U.Object.Destroy(v.go)end;originalSources={}
 Clear();if audioRoot then U.Object.Destroy(audioRoot)end
 for _,clip in pairs(audioClips)do U.Object.Destroy(clip)end;audioClips={};audioPool={}
end
