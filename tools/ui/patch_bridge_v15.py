#!/usr/bin/env python3
"""把 v15 的改动打进作者包里的 dragon_world_bridge.lua（一次性补丁，可重复运行：已打过就只更新数据段和尾段）。

改动：界面区整体换成 assets/v15/bridge_ui_region.lua；骑龙状态机改成「唤龙 → 飞到祭坛 → 骑」；
去掉运行时染麦田底色；文件末尾追加 assets/v15/bridge_tail.lua 和 assets/ui2/ui2_data.lua。
"""
import os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJ = os.path.expanduser('~/Library/Application Support/AI World Creator/projects/project_lapv8fm0')
PATH = f'{PROJ}/ai-sessions/workspace_sbazsi67/wprefabs/dragon_phase1_merged/scripts/dragon_world_bridge.lua'
src = open(PATH, encoding='utf8').read()
MARK = '\n-- @@V15 TAIL BEGIN\n'


def rep(s, old, new, count=1):
    assert s.count(old) == count, (s.count(old), old[:80])
    return s.replace(old, new)


if MARK in src:
    src = src[:src.index(MARK)]
else:
    # 1. 界面区
    a = src.index('---------------------------------------------------------------- 搭建\nfunction UI.buildCanvas()')
    b = src.index('-- @@UI END')
    src = src[:a] + '-- @@V15 UI REGION\n' + src[b:]
    # 2. 骑龙
    src = rep(src, """        local near=dist2d(p,DR.ALTAR[1],DR.ALTAR[2])<20
        if near and not DR.said then DR.said=true;toast("在唤龙祭坛按跳跃键，召唤巨龙") end
        if not near then DR.said=false end
        if near and DR.jump and DR.cool<=0 then
            if not CanRideDragon()then DR.cool=2;toast('在祭坛供奉龙蛋、缔结龙契后才能骑龙');return end
            DR.cool,DR.speed=2,0
            actor:Immobilize(true);DR.mount(actor)
            DouyinCameraService.SetDistance(42)
            DR.takeoff(false)
            toast("巨龙载你起飞！摇杆控制方向，按跳跃键降落")
        end
""", """        local near=dist2d(p,DR.ALTAR[1],DR.ALTAR[2])<20
        if near and not DR.said then DR.said=true;toast(CanRideDragon() and "点屏幕左侧的龙印，唤墨曜降临祭坛" or "龙魂之卵在等月辉、火种与星露") end
        if not near then DR.said=false end
""")
    src = rep(src, """    local dt = math.min(Time.deltaTime, .1)
    if Input.GetKeyDown("space") then DR.jump=true end
    DR.cool=DR.cool-dt
    DR.phaseT=(DR.phaseT or 0)+dt
""", """    local dt = math.min(Time.deltaTime, .1)
    if Input.GetKeyDown("space") then DR.jump=true end
    DR.cool=DR.cool-dt
    DR.phaseT=(DR.phaseT or 0)+dt
    if DR.remoteOn and DR.state=="perch" then DR.jump=false;return end
""")
    src = rep(src, """        if DR.homeLanding then DR.homePose(u) end
        if not DR.homeLanding then DR.align(actor) end
        if DR.phaseT>=2.8 then
            if DR.homeLanding then
                DR.yaw=DR.homeYaw;DR.place(0);DR.homePose(1);DR.cool=2
                DR.phase("perch","idle",true)
            else""", """        if DR.homeLanding then DR.homePose(u) end
        if not DR.homeLanding and DR.rider then DR.align(actor) end
        if DR.phaseT>=2.8 then
            if DR.homeLanding then
                DR.yaw=DR.homeYaw;DR.place(0);DR.homePose(1);DR.cool=2
                DR.summoning=false
                DR.phase("perch","idle",true)
            elseif DR.arriving then
                -- 唤龙落地：在祭坛边等骑手
                DR.arriving=false;DR.summoning=false;DR.cool=1;DR.saidRide=false;DR.nearAwait=false
                DR.phase("await","idle",true);toast("墨曜已降临唤龙祭坛")
            else""")
    src = rep(src, """        if DR.phaseT>=1.5 then DR.takeoff(true) end
    elseif DR.state=="return_fly" then
        local to=DR.home-DR.pos""", """        if DR.phaseT>=1.5 then DR.goHome() end
    elseif DR.state=="await" then
        DR.play("idle",true)
        local r=math.rad(DR.yaw)
        DR.nearAwait=dist2d(p,DR.pos.x+math.sin(r)*14,DR.pos.z+math.cos(r)*14)<26
        if DR.nearAwait and not DR.saidRide then DR.saidRide=true;toast("墨曜在等你：点龙印或按跳跃键，骑上龙背") end
        if DR.nearAwait and (DR.jump or DR.rideTap) and DR.cool<=0 then
            DR.cool,DR.speed=2,0
            actor:Immobilize(true);DR.mount(actor)
            DouyinCameraService.SetDistance(42)
            DR.takeoff(false)
            toast("巨龙载你起飞！摇杆控制方向，按跳跃键降落")
        elseif DR.phaseT>90 then
            toast("墨曜等了很久，先飞回雪山了")
            DR.goHome()
        end
        DR.rideTap=false
    elseif DR.state=="return_fly" then
        if not DR.dest then DR.dest,DR.destHome,DR.destYaw=DR.home,true,DR.homeYaw end
        local to=DR.dest-DR.pos""")
    src = rep(src, """        local h=flat>25 and math.max(DR.home.y+25,DR.flightClearance(x,z)+30) or DR.home.y+3
        DR.pos=Vector3(x,DR.pos.y+(h-DR.pos.y)*math.min(1,dt*.9),z)
        DR.roll=0;DR.place(0)
        if flat<1 and math.abs(DR.pos.y-DR.home.y-3)<.3 then
            DR.yaw=DR.homeYaw;DR.landAt(DR.home,true)
        end""", """        local h=flat>25 and math.max(DR.dest.y+25,DR.flightClearance(x,z)+30) or DR.dest.y+3
        DR.pos=Vector3(x,DR.pos.y+(h-DR.pos.y)*math.min(1,dt*(flat>25 and .9 or 1.6)),z)
        DR.roll=0;DR.place(0)
        if flat<1 and math.abs(DR.pos.y-DR.dest.y-3)<.4 then
            if DR.destHome then
                DR.yaw=DR.homeYaw;DR.landAt(DR.home,true)
            else
                DR.yaw=DR.destYaw or DR.yaw;DR.arriving=true;DR.landAt(DR.dest,false)
            end
        end""")
    src = rep(src, "    if lo<29 or hi-lo>2.5 then return nil end", "    if lo<29 or hi-lo>(DR.slack or 2.5) then return nil end")
    # 3. 去掉运行时染麦田（底色已直接写进地形）
    src = rep(src, " if not UI.wheatGroundAttemptV14 then UI.wheatGroundAttemptV14=true;local ok,err=pcall(UI.applyWheatGroundV14);if not ok then report(\"wheat ground: \"..tostring(err))end end\n", "")
    a = src.index('-- Runtime-only terrain cover clone; original scene texture remains intact.')
    src = src[:a].rstrip() + '\n'
    # 旧的誓约入口里会把旧书页重新显示出来（合书时闪一下），由尾段里的新实现取代
region = open(f'{REPO}/assets/v15/bridge_ui_region.lua', encoding='utf8').read()
a = src.index('-- @@V15 UI REGION\n')
b = src.index('-- @@UI END')
src = src[:a] + '-- @@V15 UI REGION\n' + region + src[b:]
tail = open(f'{REPO}/assets/v15/bridge_tail.lua', encoding='utf8').read()
data = open(f'{REPO}/assets/ui2/ui2_data.lua', encoding='utf8').read()
src = src + MARK + tail + '\n' + data
open(PATH, 'w', encoding='utf8').write(src)

import lupa
lua = lupa.LuaRuntime()
check = lua.eval('function(s) local f,e=load(s,"bridge","t",{}) if f then return "ok" else return e end end')
print('syntax:', check(src), 'size MB', round(len(src.encode()) / 1e6, 2))
