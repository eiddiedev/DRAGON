-- Pull the local camera back while the local player is riding this horse.
---@displayName 骑乘镜头
---@start
---@var RideCameraDistance:number=7.5
---@name 骑乘镜头距离
---@desc 骑乘时相机与角色的距离，越大越靠后
---@group 镜头
---@var RideCameraPitch:number=14
---@name 骑乘镜头俯角
---@desc 骑乘时相机向下观察的角度
---@group 镜头
---@var RideCameraOffsetY:number=1.15
---@name 骑乘镜头高度
---@desc 骑乘时相机观察目标点向上偏移的高度
---@group 镜头
---@end

local DouyinCameraService = CS.DouyinCameraService
local Vector3 = CS.UnityEngine.Vector3

-- The platform has no getters for distance/offset, so keep the conventional
-- third-person defaults here and restore them explicitly when riding ends.
local defaultDistance = 4
local defaultPitch = 0
local defaultOffset = Vector3(0, 0, 0)
local isRiding = false

local function applyRideView()
    DouyinCameraService.SetDistance(RideCameraDistance)
    DouyinCameraService.SetPitch(RideCameraPitch)
    DouyinCameraService.SetOffset(Vector3(0, RideCameraOffsetY, 0))
end

local function restoreDefaultView()
    DouyinCameraService.SetDistance(defaultDistance)
    DouyinCameraService.SetPitch(defaultPitch)
    DouyinCameraService.SetOffset(defaultOffset)
end

function Start()
    local currentPitch = DouyinCameraService.GetPitch()
    if currentPitch ~= nil then
        defaultPitch = currentPitch
    end
end

function OnSeatEntered(actor)
    if actor == nil or not actor.isLocal then
        return
    end
    isRiding = true
    applyRideView()
end

function OnSeatExited(actor)
    if actor == nil or not actor.isLocal then
        return
    end
    isRiding = false
    restoreDefaultView()
end

function OnDisable()
    if isRiding then
        isRiding = false
        restoreDefaultView()
    end
end

function OnDestroy()
    if isRiding then
        isRiding = false
        restoreDefaultView()
    end
end
