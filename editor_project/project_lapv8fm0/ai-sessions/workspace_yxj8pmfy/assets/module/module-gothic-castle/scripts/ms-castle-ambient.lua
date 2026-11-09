-- 让城头旗帜随风轻摆，并让大厅吊灯缓慢旋转
---@displayName 城堡氛围
---@start
---@var BannerSway:number=4.5
---@name 旗帜摆幅
---@desc 旗帜左右摆动的最大角度，单位为度
---@var BannerSpeed:number=1.1
---@name 旗帜摆动速度
---@desc 数值越大摆动越快
---@var ChandelierSpeed:number=6
---@name 吊灯转速
---@desc 大厅吊灯每秒旋转的角度，单位为度
---@end

local UnityEngine = CS.UnityEngine
local Time = CS.UnityEngine.Time
local RuntimeScope = require("official.core.runtime_scope")

local runtimeScope = RuntimeScope.from(self)

local bannerPaths = {
  "GothicCastle/Detail/Banners/BannerKeepLeft/Swing",
  "GothicCastle/Detail/Banners/BannerKeepRight/Swing",
  "GothicCastle/Detail/Banners/BannerGateLeft/Swing",
  "GothicCastle/Detail/Banners/BannerGateRight/Swing",
}
local bannerNodes = {}
local chandelierSwing = nil
local elapsed = 0

function Start()
  if runtimeScope == nil then return end
  for index = 1, #bannerPaths do
    local node = runtimeScope:GetTransformByPath(bannerPaths[index])
    if node ~= nil then
      bannerNodes[#bannerNodes + 1] = node
    end
  end
  chandelierSwing = runtimeScope:GetTransformByPath(
    "GothicCastle/Detail/InteriorDecor/Chandelier/Swing"
  )
end

function Update()
  elapsed = elapsed + Time.deltaTime
  local swayAngle = BannerSway * math.sin(elapsed * BannerSpeed)
  for index = 1, #bannerNodes do
    local phase = 0.85 + index * 0.08
    bannerNodes[index].localEulerAngles = UnityEngine.Vector3(
      swayAngle * 0.25 * index,
      0,
      swayAngle * phase
    )
  end
  if chandelierSwing ~= nil then
    chandelierSwing.localEulerAngles = UnityEngine.Vector3(0, elapsed * ChandelierSpeed, 0)
  end
end
