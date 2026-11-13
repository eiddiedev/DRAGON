#!/usr/bin/env python3
"""v29：针对提审端（流式加载）做的加固，打进作者包 gameplay_v27 / actors_v27 的脚本。可重复运行。

1. 天空：漩涡 / 月亮节点 8 秒内没被加载进来，就用随脚本带的贴图在运行时建一份；
   「天空就绪」不再无限等待（昼夜光照、环境色、特效更新都挂在它后面）。
2. 开场：标题要等世界里的物体数量稳定下来再出现（最多等 30 秒），不再只看界面贴图。
3. 内存：去掉脚本里 9 张已不用的旧界面图备份（约 10 MB 文本 / 40 MB 贴图内存），地表底色图改存 JPG。
4. 画质：贴图最高一级 mip、各向异性过滤、LOD 偏移，只往高调不往低调。
5. 马：动画控制器不再 60 秒超时放弃；根节点上找不到时到子节点里找。
6. 特效：三档（1 精简 / 2 均衡 / 3 完整），默认均衡。
"""
import base64, io, os, re, sys
import numpy as np
from PIL import Image
import lupa

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJ = os.path.expanduser('~/Library/Application Support/AI World Creator/projects/project-55a43370-8734-4825-92a8-b0de824a45e2')
W = f'{PROJ}/ai-sessions/workspace_amfuq048/wprefabs'
chk = lupa.LuaRuntime().eval('function(s) local f,e=load(s,"chunk","t",{}) return f and "ok" or e end')
MARK = '\n-- @@V29 BEGIN\n'
BK = f'{REPO}/assets/review_v29/v27_scripts'      # 打补丁前的 v27 原脚本（补丁每次都从这里重新生成）


def rep(s, old, new, n=1):
    assert s.count(old) == n, (s.count(old), old[:90])
    return s.replace(old, new)


def b64img(im, fmt, **kw):
    buf = io.BytesIO(); im.save(buf, fmt, **kw)
    return base64.b64encode(buf.getvalue()).decode()


# ------------------------------------------------------------------ 主脚本
p = f'{W}/gameplay_v27/scripts/dragon_world_bridge.lua'
s = open(f'{BK}/{os.path.basename(p)}', encoding='utf8').read()

# 3. 备份图瘦身
keep = ['ui_title', 'ui_book', 'ui_atlas', 'MobileGroundColorSource']
m = re.search(r"UI\.bundled\.bytes=\{(.*?)\}\n", s, re.S)
entries = dict(re.findall(r"\['(\w+)'\]='([A-Za-z0-9+/=]+)'", m.group(1)))
ground = Image.open(io.BytesIO(base64.b64decode(entries['MobileGroundColorSource']))).convert('RGB')
entries['MobileGroundColorSource'] = b64img(ground, 'JPEG', quality=90)
new_bytes = 'UI.bundled.bytes={' + ','.join(f"['{k}']='{entries[k]}'" for k in keep) + '}\n'
s = s[:m.start()] + new_bytes + s[m.end():]
s = rep(s, "UI.bundled.order={'ui_title','ui_book','ui_pages1','ui_pages2','ui_pages3','ui_map','ui_atlas','ui_cards1','ui_cards2','InkCarrier_oath','InkCarrier_font','InkCarrier_map','MobileGroundColorSource'}",
        "UI.bundled.order={'ui_title','ui_book','ui_atlas','MobileGroundColorSource'}")
s = rep(s, 'UI.TEX_NAMES = { "ui_title", "ui_book", "ui_pages1", "ui_pages2", "ui_pages3", "ui_map", "ui_atlas", "ui_cards1", "ui_cards2" }',
        'UI.TEX_NAMES = { "ui_title", "ui_book", "ui_atlas" }')
s = rep(s, """ for _,k in ipairs({'oath','font','map'})do
  if not GetInkTexture(k)then UI.loading.missingUI[#UI.loading.missingUI+1]='InkCarrier_'..k end
 end
""", "")
for name in ('ui_pages1', 'ui_pages2', 'ui_pages3', 'ui_map', 'ui_cards1', 'ui_cards2', 'InkCarrier_oath', 'InkCarrier_font', 'InkCarrier_map'):
    s = rep(s, f"---@var TextureSource_{name}:UnityEngine.GameObject=nil\n---@name 纹理依赖_{name}\n---@refFrom asset\n", "")
    s = s.replace(f"['{name}']=TextureSource_{name},", "").replace(f",['{name}']=TextureSource_{name}", "")
assert 'TextureSource_ui_map' not in s and 'TextureSource_InkCarrier_font' not in s

# 1. 天空
a = s.index("local function setupSky()")
b = s.index("local function updateSky()")
s = s[:a] + '''local function setupSky()
    if skyReady then
        return
    end
    -- v29：提审端是流式加载，远处的漩涡和月亮可能很晚才到、甚至不到。
    -- 8 秒内没等到就用随脚本带的贴图现建一份；12 秒后无论如何都算天空就绪，
    -- 不让昼夜光照、环境色和特效更新一直卡在后面。
    local now = Time.realtimeSinceStartup
    SWIRL_LAYERS.waitFrom = SWIRL_LAYERS.waitFrom or now
    local waited = now - SWIRL_LAYERS.waitFrom
    local function resolve(name)
        local go = UnityEngine.GameObject.Find(name)
        if go ~= nil then
            local rs = go:GetComponentsInChildren(typeof(UnityEngine.Renderer), true)
            if rs == nil or rs.Length == 0 then go = nil end
        end
        if go == nil and waited > 8 and RuntimeSkyLayer then
            local ok, made = pcall(RuntimeSkyLayer, name)
            if ok and made then go = made else SWIRL_LAYERS.fallbackError = tostring(made) end
        end
        return go
    end
    local found, missing = {}, 0
    for _, layer in ipairs(SWIRL_LAYERS) do
        found[layer.name] = resolve(layer.name)
        if found[layer.name] == nil then missing = missing + 1 end
    end
    if missing > 0 and waited <= 12 then
        return
    end
    for _, layer in ipairs(SWIRL_LAYERS) do
        local go = found[layer.name]
        if go ~= nil then
            layer.transform = go.transform
            table.insert(nightObjects, go)
        end
    end
    local moon = resolve("sky_moon2")
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
    SWIRL_LAYERS.missing = missing
    skyReady = true
end

''' + s[b:]
s = rep(s, """    for _, layer in ipairs(SWIRL_LAYERS) do
        layer.transform:Rotate(0, 0, layer.speed * dt)
    end""", """    for _, layer in ipairs(SWIRL_LAYERS) do
        if layer.transform then layer.transform:Rotate(0, 0, layer.speed * dt) end
    end""")
s = rep(s, "(state.skyAttempts or 0)<10 then", "(state.skyAttempts or 0)<900 then")

# 2. 开场门控
s = rep(s, """        if kitReady then kitReady=UI.bundledStep() end
        if kitReady and (UI.tryT == nil or UI.t - UI.tryT > .5) then""", """        if kitReady then kitReady=UI.bundledStep() end
        if kitReady then kitReady=UI.worldSettled() end
        if kitReady and (UI.tryT == nil or UI.t - UI.tryT > .5) then""")
s = rep(s, "(not UI.K.ready and '正在展开古书' or '正在准备界面资源'))", "(not UI.K.ready and '正在展开古书' or(not UI.settle.done and '正在铺开世界' or '正在准备界面资源')))")
s = rep(s, "st.label.text=st.error or(elapsed>45 and (stage..'超时，请退出世界后重试')or(stage..' · '..elapsed..'秒'))", "st.label.text=st.error or(elapsed>75 and (stage..'超时，请退出世界后重试')or(stage..' · '..elapsed..'秒'))")
s = rep(s, "            elseif UI.wait > 45 then", "            elseif UI.wait > 75 then")

# 尾段
if MARK in s:
    s = s[:s.index(MARK)]
sky = {}
for name, path, size in (('sky_swirl_a', 'tex2/sky_swirl_a', 1024), ('sky_swirl_b', 'tex2/sky_swirl_b', 1024), ('sky_swirl_c', 'tex2/sky_swirl_c', 1024), ('sky_moon2', 'tex/sky_moon', 512)):
    im = Image.open(f'{REPO}/assets/sky/{path}.png').convert('RGBA').resize((size, size), Image.LANCZOS)
    im = im.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    sky[name] = b64img(im, 'PNG', optimize=True)
tail = open(f'{REPO}/tools/v29/bridge_v29_tail.lua', encoding='utf8').read()
s = s + MARK + tail + '\nUI.SKYB={}\n' + ''.join(f'UI.SKYB["{k}"]="{v}"\n' for k, v in sky.items())
open(p, 'w', encoding='utf8').write(s)
print('bridge', chk(s), round(len(s.encode()) / 1e6, 2), 'MB', 'sky KB', {k: len(v) // 1024 for k, v in sky.items()})

# ------------------------------------------------------------------ 特效三档
p = f'{W}/gameplay_v27/scripts/dragon_fx.lua'
s = open(f'{BK}/{os.path.basename(p)}', encoding='utf8').read()
s = rep(s, "---@var MobileBudget:boolean=true\n---@name 手机特效预算\n", "---@var MobileBudget:boolean=true\n---@name 手机特效预算\n---@var FxLevel:number=2\n---@name 特效档位（1精简 2均衡 3完整）\n")
s = rep(s, "local Effect=require('official.effect.playback')\n", "local Effect=require('official.effect.playback')\n-- v29：三档特效。1 = 原来的精简版；2 = 均衡（保留叠层和余爆，但限制同屏数量、不放大、不震屏）；3 = 完整版。\nlocal LOW=(tonumber(FxLevel) or 2)<=1\nlocal MID=(tonumber(FxLevel) or 2)==2\n")
head, body = s.split("local Effect=require('official.effect.playback')\n", 1)
body = body.replace('MobileBudget', 'LOW')
s = head + "local Effect=require('official.effect.playback')\n" + body
s = rep(s, "local BOOM=LOW and 1 or 1.55", "local BOOM=LOW and 1 or(MID and 1.15 or 1.55)")
s = rep(s, """ if bridge then pcall(function()bridge.ScreenFx(flash,shake,duration or .35)end)end
end""", """ if bridge then pcall(function()bridge.ScreenFx(MID and flash*.7 or flash,MID and 0 or shake,duration or .35)end)end
end
local midTimes={}
local midFrame,midFrameCount,midDropped=-1,0,0""")
s = rep(s, """ local go,why=Effect.spawn(self,key,p,{rotation=rotation or U.Quaternion.identity,scale=(scale or 1)*BOOM})""", """ if MID then
  -- 均衡档：每帧最多 3 个、半秒内最多 10 个一次性特效，超出的直接丢弃
  local frame=U.Time.frameCount;local now=U.Time.time
  if frame~=midFrame then midFrame=frame;midFrameCount=0 end
  while #midTimes>0 and now-midTimes[1]>.5 do table.remove(midTimes,1)end
  if midFrameCount>=3 or #midTimes>=10 then midDropped=midDropped+1;return end
  midFrameCount=midFrameCount+1;midTimes[#midTimes+1]=now
 end
 local go,why=Effect.spawn(self,key,p,{rotation=rotation or U.Quaternion.identity,scale=math.min((scale or 1)*BOOM,MID and 2.4 or 9)})""")
s = rep(s, "hurtFeel=function()if LOW then return end;", "hurtFeel=function()if LOW or MID then return end;")
s = rep(s, " for i=1,count do local a=i*math.pi*2/count+radius;one(key,", " if MID then count=math.min(count,4)end\n for i=1,count do local a=i*math.pi*2/count+radius;one(key,")
s = rep(s, " local cap=LOW and 2 or 26", " local cap=LOW and 2 or(MID and 8 or 26)")
s = rep(s, " if not key or #flying>=(LOW and 2 or 26) then return end", " if not key or #flying>=(LOW and 2 or(MID and 8 or 26)) then return end")
s = rep(s, " if LOW then if arena then arena:Release();arena=nil end;wantedArena=nil;return end", " if LOW or MID then if arena then arena:Release();arena=nil end;wantedArena=nil;return end")
open(p, 'w', encoding='utf8').write(s)
print('fx', chk(s))

# ------------------------------------------------------------------ 马
p = f'{W}/actors_v27/scripts/horse_seat_v1.lua'
s = open(f'{BK}/{os.path.basename(p)}', encoding='utf8').read()
s = rep(s, """  if now>s.deadline and s.anim==nil then
   s.status='controller timeout';warn(s.status,s.status..' for '..s.wanted);return
  end""", """  -- v29：提审端资源到得晚，不再超时放弃，一直按 1 秒一次的节奏等动画组件和控制器
  if now>s.deadline and s.anim==nil then s.status='waiting animator';s.deadline=now+60 end""")
s = rep(s, """    return owner:GetComponent(typ)
   end)""", """    local found=owner:GetComponent(typ)
    if found==nil then
     -- 提审端组件可能挂在模型子节点上；跳过骑在上面的玩家
     local all=owner:GetComponentsInChildren(typ,true)
     for i=0,all.Length-1 do local c=all[i]
      if c and not(passenger and (c.transform==passenger.gameObject.transform or c.transform:IsChildOf(passenger.gameObject.transform)))then found=c;break end
     end
    end
    return found
   end)""")
s = rep(s, """  if now>s.deadline then
   s.status=controller and 'clip timeout' or 'controller timeout'
   warn(s.status,s.status..' for '..s.wanted);return
  end""", """  if now>s.deadline then s.deadline=now+60;s.attempts=0 end""")
s = rep(s, "play(speed<.2 and 'Idle' or speed<2.4 and 'Walk' or speed<5.5 and 'Trot' or speed<8 and 'Run' or 'RunFast')", "play(speed<.2 and 'Idle' or speed<2.4 and 'Walk' or speed<5.5 and 'Trot' or 'Run')")
open(p, 'w', encoding='utf8').write(s)
print('horse', chk(s))

# ------------------------------------------------------------------ 羊（同一套动画请求器，同样不再超时放弃）
p = f'{W}/actors_v27/scripts/tripo_sheep_motion.lua'
s = open(f'{BK}/{os.path.basename(p)}', encoding='utf8').read()
s = rep(s, """  if now>s.deadline and s.anim==nil then
   s.status='controller timeout';warn(s.status,s.status..' for '..s.wanted);return
  end""", "  if now>s.deadline and s.anim==nil then s.status='waiting animator';s.deadline=now+60 end")
s = rep(s, """  if now>s.deadline then
   s.status=controller and 'clip timeout' or 'controller timeout'
   warn(s.status,s.status..' for '..s.wanted);return
  end""", "  if now>s.deadline then s.deadline=now+60;s.attempts=0 end")
open(p, 'w', encoding='utf8').write(s)
print('sheep', chk(s))
