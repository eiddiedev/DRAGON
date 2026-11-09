-- 灯祭者的逐骨骼关键帧动作：待机 / 行走 / 攻击 / 受击
---@displayName 灯祭者动作
---@start
---@var DefaultAction:string="Idle"
---@name 默认动作
---@desc 启用、重置或动作结束回到的动作
---@enum Idle=待机,Walk=行走,Attack=攻击,Hit=受击
---@var PlaybackSpeed:number=1
---@name 播放速度
---@desc 所有动作的播放倍速，1 为正常速度
---@end

local Logger = require("official.core.logger")
local RuntimeScope = require("official.core.runtime_scope")

local logger = Logger.create("ms-healer-anim")

local UnityEngine = CS.UnityEngine
local Quaternion = CS.UnityEngine.Quaternion
local Vector3 = CS.UnityEngine.Vector3
local Time = CS.UnityEngine.Time

local runtimeScope, scopeReason = RuntimeScope.from(self)

-- 骨骼节点路径均来自 inspect_resource_nodes 的真实层级，与 BONE_ORDER 一一对应
local BONE_PATHS = {
  "Armature/root.x",
  "Armature/root.x/spine_01.x",
  "Armature/root.x/spine_01.x/spine_02.x",
  "Armature/root.x/spine_01.x/spine_02.x/spine_03.x",
  "Armature/root.x/spine_01.x/spine_02.x/spine_03.x/neck.x",
  "Armature/root.x/spine_01.x/spine_02.x/spine_03.x/neck.x/head.x",
  "Armature/root.x/spine_01.x/spine_02.x/spine_03.x/shoulder.l",
  "Armature/root.x/spine_01.x/spine_02.x/spine_03.x/shoulder.l/arm_stretch.l",
  "Armature/root.x/spine_01.x/spine_02.x/spine_03.x/shoulder.l/arm_stretch.l/forearm_stretch.l",
  "Armature/root.x/spine_01.x/spine_02.x/spine_03.x/shoulder.l/arm_stretch.l/forearm_stretch.l/hand.l",
  "Armature/root.x/spine_01.x/spine_02.x/spine_03.x/shoulder.r",
  "Armature/root.x/spine_01.x/spine_02.x/spine_03.x/shoulder.r/arm_stretch.r",
  "Armature/root.x/spine_01.x/spine_02.x/spine_03.x/shoulder.r/arm_stretch.r/forearm_stretch.r",
  "Armature/root.x/spine_01.x/spine_02.x/spine_03.x/shoulder.r/arm_stretch.r/forearm_stretch.r/hand.r",
  "Armature/root.x/thigh_stretch.l",
  "Armature/root.x/thigh_stretch.l/leg_stretch.l",
  "Armature/root.x/thigh_stretch.l/leg_stretch.l/foot.l",
  "Armature/root.x/thigh_stretch.l/leg_stretch.l/foot.l/toes_01.l",
  "Armature/root.x/thigh_stretch.r",
  "Armature/root.x/thigh_stretch.r/leg_stretch.r",
  "Armature/root.x/thigh_stretch.r/leg_stretch.r/foot.r",
  "Armature/root.x/thigh_stretch.r/leg_stretch.r/foot.r/toes_01.r",
}

local BONE_ORDER = {
  "root", "spine_01", "spine_02", "spine_03", "neck", "head", "shoulder.l", "arm.l", "forearm.l", "hand.l", "shoulder.r", "arm.r", "forearm.r", "hand.r", "thigh.l", "leg.l", "foot.l", "toes.l", "thigh.r", "leg.r", "foot.r", "toes.r"
}

-- 每个关键帧: { 时间, 根节点竖直偏移, { 22 根骨骼各 3 个局部欧拉角增量 } }
local ACTIONS = {
  Idle = {
    duration = 3.00, loop = true, hitTime = 0.00,
    keys = {
      {0.00, 0.0000, {0, 0, 0, -0, 0, -0, -0, 0, -0, 0, -0, 0, 0, -0, 0, -0, 0, -0, -0, 0, 0, -3.1, 0.1, -5.5, 6, 1, 12, -3.2, 0.2, -6.4, -0, 0, 0, -6, -0.3, 5.3, 17.5, -0.2, -8.6, -10.3, -0.5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}},
      {0.25, 0.0000, {0, 0, 0, 0.6, 0, 0.4, -0.4, 0.2, 0.3, 0.5, 0.2, 0.2, -0.5, -0.2, -0.3, -0.3, -0.2, -0.2, 0.4, 0, -0.4, -5.8, 0.4, -5.1, 6, 1, 12, -2.1, 0.1, -6.3, 0.3, 0, 0.3, -5, -0, 9.5, 22.4, -1.8, -16.4, -14.6, -1.1, 8.9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}},
      {0.50, 0.0000, {0, 0, 0, 1, -0, 0.8, -0.7, 0.4, 0.5, 0.8, 0.3, 0.4, -0.8, -0.4, -0.6, -0.4, -0.3, -0.4, 0.7, 0, -0.7, -8.1, 0.6, -4.8, 6, 0.9, 12, -1.1, 0.1, -6.2, 0.6, 0, 0.6, -3.9, 0.2, 12.7, 26, -3.7, -22.5, -18.1, -1.9, 12, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}},
      {0.75, 0.0000, {0, 0, 0, 1.1, -0, 1.1, -0.8, 0.6, 0.7, 0.9, 0.4, 0.6, -0.9, -0.6, -0.8, -0.5, -0.4, -0.5, 0.8, 0, -0.8, -9.7, 1, -4.5, 6, 0.9, 12, -0.3, 0, -6.1, 0.7, -0, 0.7, -2.6, 0.2, 14.4, 27.9, -5.2, -26.1, -20.5, -2.5, 13.8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}},
      {1.00, 0.0000, {0, 0, 0, 1, -0, 1.3, -0.7, 0.8, 0.9, 0.8, 0.5, 0.7, -0.8, -0.8, -1, -0.4, -0.5, -0.6, 0.7, 0, -0.7, -10.3, 1.4, -4.3, 6, 0.9, 12, 0.1, -0, -6.1, 0.6, 0, 0.6, -1.4, -0.1, 14.9, 28.8, -6.1, -27.8, -22, -2.9, 14.8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}},
      {1.25, 0.0000, {0, 0, 0, 0.6, -0, 1.4, -0.4, 0.9, 1, 0.5, 0.6, 0.8, -0.5, -0.9, -1.1, -0.3, -0.6, -0.7, 0.4, 0, -0.4, -10.1, 1.8, -4.2, 6, 0.8, 12, 0.3, -0, -6.1, 0.3, 0, 0.3, -0.4, -0.6, 14.4, 28.9, -6.3, -28, -22.6, -3, 15.1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}},
      {1.50, 0.0000, {0, 0, 0, 0, 0, 1.5, -0, 0.9, 1, -0, 0.6, 0.8, 0, -0.9, -1.1, -0, -0.6, -0.7, -0, 0, 0, -9.2, 2.3, -4.2, 6, 0.8, 12, 0.1, -0, -6.2, -0, 0, 0, 0.2, -1.2, 13.2, 28.4, -6, -27.1, -22.4, -3, 15, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}},
      {1.75, 0.0000, {0, 0, 0, -0.6, -0, 1.4, 0.4, 0.9, 1, -0.5, 0.6, 0.8, 0.5, -0.9, -1.1, 0.3, -0.6, -0.7, -0.4, 0, 0.4, -7.9, 2.6, -4.3, 6, 0.9, 12, -0.2, 0, -6.3, -0.3, 0, -0.3, 0.2, -1.8, 11.7, 27.3, -5.2, -25.2, -21.5, -2.8, 14.4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}},
      {2.00, 0.0000, {0, 0, 0, -1, -0, 1.3, 0.7, 0.8, 0.9, -0.8, 0.5, 0.7, 0.8, -0.8, -0.9, 0.4, -0.5, -0.6, -0.7, 0, 0.7, -6.4, 2.6, -4.5, 6, 0.9, 12, -0.7, 0, -6.4, -0.6, 0, -0.6, -0.2, -2.2, 10, 26, -4.2, -22.7, -20.1, -2.4, 13.3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}},
      {2.25, 0.0000, {0, 0, 0, -1.1, 0, 1.1, 0.8, 0.6, 0.7, -0.9, 0.4, 0.6, 0.9, -0.6, -0.8, 0.5, -0.4, -0.5, -0.8, 0, 0.8, -5.2, 2.4, -4.7, 6, 0.9, 12, -1.3, 0.1, -6.5, -0.7, 0, -0.7, -1.1, -2.2, 8.5, 24.2, -3.1, -19.7, -18.1, -1.9, 11.7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}},
      {2.50, 0.0000, {0, 0, 0, -1, -0, 0.8, 0.7, 0.4, 0.5, -0.8, 0.3, 0.4, 0.8, -0.4, -0.5, 0.4, -0.3, -0.3, -0.7, 0, 0.7, -4.2, 1.8, -5, 6, 0.9, 12, -1.9, 0.1, -6.5, -0.6, 0, -0.6, -2.5, -1.8, 7.2, 22.1, -2, -16.1, -15.7, -1.3, 9.7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}},
      {2.75, 0.0000, {0, 0, 0, -0.6, 0, 0.4, 0.4, 0.2, 0.3, -0.5, 0.2, 0.2, 0.5, -0.2, -0.3, 0.3, -0.2, -0.2, -0.4, 0, 0.4, -3.6, 1, -5.2, 6, 1, 12, -2.6, 0.1, -6.5, -0.3, 0, -0.3, -4, -1.1, 5.8, 19.3, -0.9, -11.6, -12.8, -0.8, 6.9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}},
      {3.00, 0.0000, {0, 0, 0, -0, 0, 0, 0, 0, -0, 0, -0, 0, 0, -0, 0, 0, -0, -0, -0, 0, 0, -3.1, 0.1, -5.5, 6, 1, 12, -3.2, 0.2, -6.4, -0, 0, 0, -6, -0.3, 5.3, 17.5, -0.2, -8.6, -10.3, -0.5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}},
    },
  },
  Walk = {
    duration = 1.20, loop = true, hitTime = 0.00,
    keys = {
      {0.00, -0.0096, {0, 0, 0, 2.8, 0, -0, -0.4, 0, -0, 0.8, 0, -0, -1, -0, -0, -0.6, 0, 0, -1.2, 0, -0, 0.7, -2.1, -2.9, 6, 0.9, 12, -7.8, 0.7, -9.9, 0.8, 0, 0, -4.4, 2.6, 10.6, 18.3, -0.5, -9.9, -11.6, -0.3, 3, -5.8, 0.5, -10.2, -8.3, -4.9, 16.1, 2.5, 10.4, 4, 0, 0, 0, 5.7, 0.1, 1.1, 3.5, -1.4, -4, -5.2, -0.6, 7.7, 0, 0, 0}},
      {0.10, -0.0011, {0, 0, 0, 2.4, -0, 0.6, -0.4, 1.2, 0.5, 0.8, 0.7, 0.3, -1, -1.1, -0.5, -0.6, -0.7, -0.3, -1, -0, 0.4, -4.4, -0.1, -5.1, 6, 0.9, 12, -4.2, 0.3, -8.4, 0.7, 0, -0.2, -2.7, 2.4, 11.3, 24.7, -3.1, -20.4, -17.4, -1.8, 11.7, -8.4, 0.4, -5, -3.1, -2.5, 5.6, 1.4, 6.1, 9, 0, 0, 0, 0.8, 0.1, 11, 14.7, -4.9, -17.1, -5.1, -4.5, 7.1, 0, 0, 0}},
      {0.20, -0.0002, {0, 0, 0, 1.6, -0, 1, -0.4, 2.1, 0.8, 0.8, 1.3, 0.6, -1, -1.9, -0.9, -0.6, -1.2, -0.5, -0.6, 0, 0.7, -8.4, 1.9, -7.7, 6, 0.9, 12, -1.3, 0.1, -5.9, 0.4, 0, -0.3, 0.1, 1.9, 11, 28.5, -5.9, -27.3, -22.5, -3.5, 17.3, -5.6, 0.2, -4.3, -3.1, -1.8, 5.7, 1.3, 5.7, 7.5, 0, 0, 0, -1.1, -0.1, 13.4, 17.1, -5.8, -19.9, -9.3, -5.1, 15.1, 0, 0, 0}},
      {0.30, -0.0006, {0, 0, 0, 1.2, 0, 1.1, -0.4, 2.4, 0.9, 0.8, 1.5, 0.7, -1, -2.2, -1, -0.6, -1.4, -0.6, -0, 0, 0.8, -11.6, 2.9, -9.9, 6, 1, 12, 1.2, -0, -3.6, -0, 0, -0.4, 1.8, 1.4, 10.2, 29.9, -7.4, -30.4, -25.1, -4.6, 20.3, -1.5, 0, -3.3, -3.1, -0.9, 5.7, 1.1, 4.3, 3.6, 0, 0, 0, -14.7, -4, 30.3, 32.2, -14.4, -37.9, -11, -9.5, 19.1, 0, 0, 0}},
      {0.40, -0.0036, {0, 0, 0, 1.6, -0, 1, -0.4, 2.1, 0.8, 0.8, 1.3, 0.6, -1, -1.9, -0.9, -0.6, -1.2, -0.5, 0.6, -0, 0.7, -13.3, 2.4, -11.4, 6, 1.1, 12, 2.3, -0, -2.1, -0.4, 0, -0.3, 2, 1.5, 10.7, 30.4, -8, -31.5, -26, -4.9, 21.2, 3.3, -0.1, -2.2, -3, 0.1, 5.6, 0.8, 2.7, -1, 0, 0, 0, -22.8, -7.7, 36.7, 36, -15.1, -43.5, -8.2, -9.8, 15.1, 0, 0, 0}},
      {0.50, -0.0092, {0, 0, 0, 2.4, -0, 0.6, -0.4, 1.2, 0.5, 0.8, 0.7, 0.3, -1, -1.1, -0.5, -0.6, -0.7, -0.3, 1, 0, 0.4, -15.8, 1.4, -15.1, 12.4, 2.9, 19, -1.9, 0.1, -5.5, -0.7, 0, -0.2, 0.5, 1.8, 12.4, 30, -7.5, -30.5, -25.1, -4.4, 19.7, 7.9, -0.1, -1.4, -3, 1.1, 5.9, 0.3, 1.2, -5.4, 0, 0, 0, -26.1, -8.7, 36.2, 33.7, -10.9, -42.3, -5.2, -9, 10.6, 0, 0, 0}},
      {0.60, -0.0152, {0, 0, 0, 2.8, 0, -0, -0.4, 0, 0, 0.8, 0, -0, -1, -0, -0, -0.6, -0, -0, 1.2, -0, -0, -16.4, 0, -18.3, 20.1, 6.4, 27.4, -8.6, 0.8, -11, -0.8, 0, 0, -2.2, 1.7, 13.6, 27.7, -5.3, -25.8, -21.6, -2.9, 15.1, 11.5, -0.1, -0.8, -2.9, 1.9, 5.9, -0.1, 0.1, -8.9, 0, 0, 0, -15.8, -1.9, 14, 12.2, 0.4, -15.2, -0.8, -3.4, 3.5, 0, 0, 0}},
      {0.70, -0.0043, {0, 0, 0, 2.4, -0, -0.6, -0.4, -1.2, -0.5, 0.8, -0.7, -0.3, -1, 1.1, 0.5, -0.6, 0.7, 0.3, 1, -0, -0.4, -11, -2.4, -13.2, 16.8, 4.6, 23.8, -8.3, 0.8, -11.4, -0.7, 0, 0.2, -7.2, 1.1, 7.7, 17.5, -0.2, -8.6, -9.9, -0.4, 5.1, 18, -1, -6.5, -10, 2.2, 19.2, 2.7, 8.4, -3.9, 0, 0, 0, -10.2, -0.5, 5.6, 3.3, 1.2, -4.3, 3.6, -1.7, -4.7, 0, 0, 0}},
      {0.80, -0.0026, {0, 0, 0, 1.6, 0, -1, -0.4, -2.1, -0.8, 0.8, -1.3, -0.6, -1, 1.9, 0.9, -0.6, 1.2, 0.5, 0.6, 0, -0.7, -4.6, -3.7, -8.5, 14.5, 3.7, 21.2, -9.9, 1.1, -12.3, -0.4, 0, 0.3, -11.7, -0.1, 10.4, 17.5, 0.3, -8.7, -6.9, -0.2, 3.8, 18.6, -1.4, -8.3, -12, 1.7, 22.9, 2.8, 7.6, -11.5, 0, 0, 0, -7.9, -0.3, 4.8, 3.3, 0.8, -4.2, 2.8, -1.6, -3.9, 0, 0, 0}},
      {0.90, -0.0017, {0, 0, 0, 1.2, -0, -1.1, -0.4, -2.4, -0.9, 0.8, -1.5, -0.7, -1, 2.2, 1, -0.6, 1.4, 0.6, -0, 0, -0.8, 3.2, -4.1, -1.6, 6.7, 1.1, 12.8, -8.1, 0.7, -9.7, -0, -0, 0.4, -13.8, -0.6, 12.1, 17.5, 0.5, -8.7, -5.2, -0.1, 2.7, 22.9, -4.5, -21.7, -24.5, -7.1, 48.7, 7.4, 21.9, -9.1, 0, 0, 0, -4.7, -0.2, 3.8, 3.4, 0.3, -4.1, 0.9, -1.2, -1.1, 0, 0, 0}},
      {1.00, -0.0027, {0, 0, 0, 1.6, 0, -1, -0.4, -2.1, -0.8, 0.8, -1.3, -0.6, -1, 1.9, 0.9, -0.6, 1.2, 0.5, -0.6, -0, -0.7, 4.9, -3.9, -0.1, 6, 0.9, 12, -9, 0.8, -10.7, 0.4, -0, 0.3, -13.1, 0, 12.8, 17.5, 0.5, -8.7, -5.5, -0.1, 2.2, 17.6, -4.2, -26.8, -25.8, -14.9, 54.7, 7.8, 29, -1.8, 0, 0, 0, -0.8, -0, 2.7, 3.4, -0.3, -4, -1.4, -0.9, 2.1, 0, 0, 0}},
      {1.10, -0.0058, {0, 0, 0, 2.4, -0, -0.6, -0.4, -1.2, -0.5, 0.8, -0.7, -0.3, -1, 1.1, 0.5, -0.6, 0.7, 0.3, -1, 0, -0.4, 3.7, -3.4, -0.9, 6, 0.9, 12, -9.1, 0.9, -10.9, 0.7, -0, 0.2, -9.6, 1.4, 12.1, 17.5, 0.2, -8.6, -7.6, -0.1, 2.1, 9.2, -2.2, -26.7, -22.8, -17.2, 50.7, 6.4, 29.8, 3.7, 0, 0, 0, 2.8, 0, 1.8, 3.5, -0.9, -4, -3.5, -0.7, 5.3, 0, 0, 0}},
      {1.20, -0.0096, {0, 0, 0, 2.8, 0, -0, -0.4, -0, -0, 0.8, 0, -0, -1, -0, -0, -0.6, 0, 0, -1.2, 0, -0, 0.7, -2.1, -2.9, 6, 0.9, 12, -7.8, 0.7, -9.9, 0.8, 0, 0, -4.4, 2.6, 10.6, 18.3, -0.5, -9.9, -11.6, -0.3, 3, -5.8, 0.5, -10.2, -8.3, -4.9, 16.1, 2.5, 10.4, 4, 0, 0, 0, 5.7, 0.1, 1.1, 3.5, -1.4, -4, -5.2, -0.6, 7.7, 0, 0, 0}},
    },
  },
  Attack = {
    duration = 1.60, loop = false, hitTime = 0.70,
    keys = {
      {0.00, 0.0000, {0, 0, 0, -0, 0, -0, -0, 0, -0, 0, -0, 0, 0, -0, 0, -0, 0, -0, -0, 0, 0, -3.1, 0.2, -5.6, 6, 1, 12, -3.2, 0.2, -6.3, -0, 0, 0, -5.9, -0.3, 5.3, 17.5, -0.2, -8.6, -10.4, -0.5, 5.1, 0.5, -0, -0.6, -0.8, -0, 1.4, 0.2, 0.8, 0.1, 0, 0, 0, -0.2, -0, 0.4, 0.4, -0, -0.5, -0.1, -0.1, 0.2, 0, 0, 0}},
      {0.15, -0.0300, {0, 0, 0, -3, 0, 0, -1.4, 0, 0, -0.7, 0, -0, -4, 0, -0, -2.4, 0, 0, -0.6, 0, 0, -16.4, 5.8, -14.1, 28.6, 9.6, 36.6, -10.5, 1.9, -20.2, -0.9, -0, 0, -23.1, -1.2, -14.6, 36.5, -1.1, -32.2, -20.2, -3.3, 51.1, 11.2, -1.5, -14.8, -16.6, -4.7, 32, 4.8, 17.4, 0.9, 0, 0, 0, -12.3, -2.2, 20, 21.7, -5.3, -25.7, -4.3, -6.2, 7.7, 0, 0, 0}},
      {0.35, -0.0150, {0, 0, 0, 1, -0, 0, 0.5, 0, 0, 0.2, 0, -0, -6, 0, 0, -3.6, 0, 0, 0.2, 0, 0, -42.1, 19.2, -51, 57.1, 48, 60.4, -29.5, 5.3, -19.9, 0.3, -0, -0, 38.7, 21.3, 52.2, -9.8, -53.7, -103.4, -76.7, -14.2, 31.9, 7.2, -0.6, -9.5, -11, -2, 20.8, 3.1, 11.3, 0.8, 0, 0, 0, -7.9, -0.9, 12.6, 14.1, -2.2, -16.6, -2.9, -4.1, 5, 0, 0, 0}},
      {0.52, -0.0060, {0, 0, 0, -5, 0, 0, -2.3, 0, 0, -1.2, -0, -0, -8, -0, -0, -4.8, 0, 0, -1, 0, -0, -49.6, 30.5, -48, 91.1, 63.6, 30.9, -41, 2.7, -7.3, -1.5, 0, -0, 60.4, 23.9, 54.1, 8.8, -59.4, -51.2, -102.1, 10.1, 4.4, 3.8, -0.2, -5, -6, -0.6, 11.1, 1.7, 6.1, 0.5, 0, 0, 0, -4.2, -0.2, 6.6, 7.5, -0.6, -8.8, -1.6, -2.2, 2.7, 0, 0, 0}},
      {0.70, -0.0400, {0, 0, 0, 11, 0, 0, 5, 0, -0, 2.7, -0, 0, 5, -0, 0, 3, 0, -0, 2.2, -0, -0, -31.2, -7.4, -25.8, 24.4, 7.7, 32, -10.1, 1.5, -16.8, 3.3, 0, -0, -2.3, 15.2, 61.1, 19, 1, -7.6, -18.9, -13.4, -60.5, 13.5, -2.1, -17.7, -19.4, -6.6, 37.9, 5.7, 20.6, 0.9, 0, 0, 0, -14.6, -3.1, 24, 25.6, -7.5, -30.3, -5.1, -7.3, 9.1, 0, 0, 0}},
      {0.88, -0.0320, {0, 0, 0, 9, -0, 0, 4.1, 0, 0, 2.2, 0, -0, 3, 0, 0, 1.8, 0, -0, 1.8, -0, -0, -28.4, -5.7, -24.6, 25.2, 8.4, 32.9, -10.9, 1.6, -17, 2.7, -0, -0, 0.3, 13.8, 55.5, 19, 0.5, -7.5, -18.2, -10.5, -53.7, 11.7, -1.6, -15.4, -17.2, -5.1, 33.2, 4.9, 18.1, 0.9, 0, 0, 0, -12.8, -2.4, 20.8, 22.5, -5.8, -26.7, -4.5, -6.4, 8, 0, 0, 0}},
      {1.10, -0.0140, {0, 0, 0, 5, -0, -0, 2.3, 0, -0, 1.2, -0, 0, 0, -0, 0, -0, 0, -0, 1, -0, -0, -17.2, -3.9, -16.3, 17.5, 4.8, 24.6, -8.2, 0.9, -12.3, 1.5, 0, 0, -6.4, 4.9, 40, 30.7, -6.1, -29.1, -16.2, -7.5, -7.6, 6.9, -0.5, -9, -10.6, -1.8, 19.8, 3, 10.8, 0.8, 0, 0, 0, -7.6, -0.8, 12.1, 13.5, -2, -15.9, -2.7, -3.9, 4.8, 0, 0, 0}},
      {1.35, -0.0030, {0, 0, 0, 1.5, -0, 0, 0.7, 0, -0, 0.4, -0, -0, -1.5, -0, -0, -0.9, 0, 0, 0.3, -0, -0, -5.5, -1.5, -6.6, 6, 1, 12, -2.9, 0.2, -6.2, 0.4, -0, -0, -5.4, 1.7, 11.3, 17.5, -0, -8.6, -9.5, -2.4, -1, 2.2, -0.1, -2.9, -3.5, -0.2, 6.6, 1, 3.6, 0.3, 0, 0, 0, -2.5, -0.1, 3.8, 4.4, -0.2, -5.2, -0.9, -1.3, 1.6, 0, 0, 0}},
      {1.60, 0.0000, {0, 0, 0, -0, 0, -0, -0, 0, -0, 0, -0, 0, 0, -0, 0, -0, 0, -0, -0, 0, 0, -3.1, 0.2, -5.6, 6, 1, 12, -3.2, 0.2, -6.3, -0, 0, 0, -5.9, -0.3, 5.3, 17.5, -0.2, -8.6, -10.4, -0.5, 5.1, 0.5, -0, -0.6, -0.8, -0, 1.4, 0.2, 0.8, 0.1, 0, 0, 0, -0.2, -0, 0.4, 0.4, -0, -0.5, -0.1, -0.1, 0.2, 0, 0, 0}},
    },
  },
  Hit = {
    duration = 0.65, loop = false, hitTime = 0.00,
    keys = {
      {0.00, 0.0000, {0, 0, 0, -0, 0, -0, -0, 0, 1.2, 0, -1.2, 0.8, 0, 0, -1.2, 0, 0, -0.8, -0, 0, 0, -5, 0.2, -1.1, 6, 0.8, 12, -2.1, 0.2, -8.5, -0, 0, 0, -1.6, -1.8, 9.2, 17.5, -0.5, -8.6, -12.6, -0.2, 1.7, 0.5, -0, -0.6, -0.8, -0, 1.4, 0.2, 0.8, 0.1, 0, 0, 0, -0.2, -0, 0.4, 0.4, -0, -0.5, -0.1, -0.1, 0.2, 0, 0, 0}},
      {0.08, -0.0280, {0, 0, 0, -8, -0, -0, -4, 0, 1.2, -2.4, -1.2, 0.7, -8, 0, -1.2, -4.8, 0, -0.8, -2.4, 0, 0, -21.4, 17.9, -31.4, 47.1, 36.6, 55, -28.7, 5, -19.4, -2.4, 0, -0, 5.4, -12.9, 32, 34.8, -32.8, -64.1, -47.8, -8.8, 31.4, 10.8, -1.3, -14.2, -16, -4.3, 30.7, 4.6, 16.7, 0.9, 0, 0, 0, -11.8, -2, 19.1, 20.8, -4.9, -24.6, -4.2, -6, 7.4, 0, 0, 0}},
      {0.20, -0.0480, {0, 0, 0, -12, 0, 0, -6, 0, 1.2, -3.6, -1.2, 0.7, -11, -0, -1.2, -6.6, 0, -0.8, -3.6, 0, 0, -22.5, 26.4, -37.7, 58.5, 55.2, 54.5, -41.4, 6, -15.7, -3.6, -0, 0, 15.7, -15.8, 39.8, 24, -43.7, -75.6, -60.3, -9.8, 32.1, 15, -2.6, -19.8, -21.3, -8.1, 42.2, 6.3, 22.8, 0.8, 0, 0, 0, -16.3, -3.9, 26.9, 28.3, -9.3, -33.6, -5.6, -8, 10, 0, 0, 0}},
      {0.34, -0.0220, {0, 0, 0, -4, 0, 0, -2, 0, 1.2, -1.2, -1.2, 0.8, -6, -0, -1.2, -3.6, 0, -0.8, -1.2, 0, -0, -19.2, 9.6, -24, 38.7, 22.6, 47.8, -21.7, 4, -20.8, -1.2, 0, -0, 1.1, -7.8, 27.3, 36.5, -20.2, -48.5, -36.6, -4.8, 23.2, 9.2, -1, -12.2, -13.9, -3.2, 26.5, 3.9, 14.4, 0.9, 0, 0, 0, -10.2, -1.5, 16.3, 18, -3.6, -21.2, -3.6, -5.2, 6.4, 0, 0, 0}},
      {0.48, -0.0040, {0, 0, 0, 1, -0, 0, 0.5, -0, 1.2, 0.3, -1.2, 0.8, -1, 0, -1.2, -0.6, 0, -0.8, 0.3, -0, -0, -6.6, -1, -2.1, 6, 0.8, 12, -2, 0.1, -8.2, 0.3, -0, -0, -1.2, -0.3, 14.3, 22, -2.2, -15.8, -16.3, -1.1, 4.8, 2.8, -0.1, -3.7, -4.4, -0.3, 8.2, 1.2, 4.5, 0.4, 0, 0, 0, -3.1, -0.1, 4.8, 5.5, -0.3, -6.5, -1.2, -1.6, 2, 0, 0, 0}},
      {0.65, 0.0000, {0, 0, 0, -0, 0, -0, -0, 0, 1.2, 0, -1.2, 0.8, 0, 0, -1.2, 0, 0, -0.8, -0, 0, 0, -5, 0.2, -1.1, 6, 0.8, 12, -2.1, 0.2, -8.5, -0, 0, 0, -1.6, -1.8, 9.2, 17.5, -0.5, -8.6, -12.6, -0.2, 1.7, 0.5, -0, -0.6, -0.8, -0, 1.4, 0.2, 0.8, 0.1, 0, 0, 0, -0.2, -0, 0.4, 0.4, -0, -0.5, -0.1, -0.1, 0.2, 0, 0, 0}},
    },
  },
}

local BLEND_TIME = 0.18
local boneCount = 0
local rigReady = false
local missingList = {}
local bones = {}
local restRot = {}
local restPos = nil
local clips = {}
local current = "Idle"
local actionTime = 0
local actionSpeed = 1
local playing = false
local started = false
local blendT = BLEND_TIME
local blendFrom = {}
local blendRootY = 0
local pendingName = nil
local pendingOpts = nil

local function smoothstep(x)
  if x <= 0 then return 0 end
  if x >= 1 then return 1 end
  return x * x * (3 - 2 * x)
end

local function buildClips()
  clips = {}
  for name, def in pairs(ACTIONS) do
    local built = { duration = def.duration, loop = def.loop, hitTime = def.hitTime, keys = {} }
    for _, key in ipairs(def.keys) do
      local quats = {}
      for i = 2, #BONE_ORDER do
        local base = i * 3 - 2
        local rest = restRot[i]
        if rest ~= nil then
          local euler = Quaternion.Euler(key[3][base], key[3][base + 1], key[3][base + 2])
          quats[i] = rest * euler
        end
      end
      built.keys[#built.keys + 1] = { t = key[1], dy = key[2], quats = quats }
    end
    clips[name] = built
  end
end

local function resolveBones()
  bones = {}
  restRot = {}
  missingList = {}
  boneCount = 0
  if runtimeScope == nil then
    logger:error("骨骼查找失败：当前脚本没有取得资源 Scope")
    return
  end
  for i, path in ipairs(BONE_PATHS) do
    local tr, reason = runtimeScope:GetTransformByPath(path)
    if tr == nil then
      missingList[#missingList + 1] = BONE_ORDER[i] .. "(" .. tostring(reason) .. ")"
    else
      bones[i] = tr
      restRot[i] = tr.localRotation
      boneCount = boneCount + 1
      if i == 1 then
        restPos = tr.localPosition
      end
    end
  end
  if #missingList > 0 then
    logger:error("骨骼缺失 " .. tostring(#missingList) .. " 根：" .. table.concat(missingList, ", "))
  end
end

local function applyRestPose()
  for i, tr in pairs(bones) do
    local rest = restRot[i]
    if rest ~= nil then
      tr.localRotation = rest
    end
  end
  if bones[1] ~= nil and restPos ~= nil then
    bones[1].localPosition = restPos
  end
end

local function captureBlend()
  blendFrom = {}
  for i, tr in pairs(bones) do
    blendFrom[i] = tr.localRotation
  end
  blendT = 0
  if bones[1] ~= nil and restPos ~= nil then
    blendRootY = bones[1].localPosition.y - restPos.y
  end
end

local function sampleClip(clip, t)
  local keys = clip.keys
  local idx = 1
  local n = #keys
  for i = 1, n - 1 do
    if t >= keys[i].t and t <= keys[i + 1].t then
      idx = i
      break
    end
    if t > keys[i + 1].t then idx = i + 1 end
  end
  if idx >= n then
    return keys[n], keys[n], 0
  end
  local a = keys[idx]
  local b = keys[idx + 1]
  local span = b.t - a.t
  local alpha = 0
  if span > 0.00001 then
    alpha = smoothstep((t - a.t) / span)
  end
  return a, b, alpha
end

local function applyPose()
  local clip = clips[current]
  if clip == nil then return end
  local a, b, alpha = sampleClip(clip, actionTime)
  local blend = 1
  if blendT < BLEND_TIME then
    blend = smoothstep(blendT / BLEND_TIME)
  end
  for i = 2, #BONE_ORDER do
    local tr = bones[i]
    if tr ~= nil then
      local target = a.quats[i]
      if alpha > 0 then
        target = Quaternion.Slerp(a.quats[i], b.quats[i], alpha)
      end
      if blend < 1 and blendFrom[i] ~= nil then
        target = Quaternion.Slerp(blendFrom[i], target, blend)
      end
      tr.localRotation = target
    end
  end
  if bones[1] ~= nil and restPos ~= nil then
    local dy = a.dy + (b.dy - a.dy) * alpha
    if blend < 1 then
      dy = blendRootY + (dy - blendRootY) * blend
    end
    bones[1].localPosition = Vector3(restPos.x, restPos.y + dy, restPos.z)
  end
end

function Start()
  if runtimeScope == nil then
    logger:error("动画初始化失败：没有取得资源 Scope（" .. tostring(scopeReason) .. "）")
    return
  end
  resolveBones()
  if boneCount == 0 then
    logger:error("动画初始化失败：没有找到任何骨骼，动作不会播放")
    return
  end
  buildClips()
  rigReady = boneCount == #BONE_ORDER
  if not rigReady then
    logger:warn("骨骼不完整，仅驱动已找到的 " .. tostring(boneCount) .. " 根骨骼")
  end
  actionSpeed = PlaybackSpeed
  started = true
  current = clips[DefaultAction] ~= nil and DefaultAction or "Idle"
  actionTime = 0
  if pendingName ~= nil and clips[pendingName] ~= nil then
    current = pendingName
    if pendingOpts ~= nil and pendingOpts.startTime ~= nil then
      actionTime = pendingOpts.startTime
    end
  end
  pendingName = nil
  pendingOpts = nil
  playing = true
  blendT = BLEND_TIME
  applyPose()
  logger:info("动作就绪：骨骼 " .. tostring(boneCount) .. "/" .. tostring(#BONE_ORDER) .. "，当前动作 " .. current)
end

function OnEnable()
  if started and rigReady then
    current = clips[DefaultAction] ~= nil and DefaultAction or "Idle"
    actionTime = 0
    playing = true
    captureBlend()
  end
end

function OnDisable()
  playing = false
  actionTime = 0
  blendT = BLEND_TIME
  applyRestPose()
end

function Update()
  if not rigReady then return end
  local dt = Time.deltaTime
  if dt > 0.2 then dt = 0.2 end
  if blendT < BLEND_TIME then
    blendT = blendT + dt
  end
  local clip = clips[current]
  if clip == nil then return end
  if playing then
    actionTime = actionTime + dt * actionSpeed
    if clip.loop then
      if actionTime >= clip.duration then
        actionTime = actionTime % clip.duration
      end
    elseif actionTime >= clip.duration then
      actionTime = clip.duration
      playing = false
      Play("Idle", { restart = true })
      return
    end
  end
  applyPose()
end

-- 供预览面板与局内逻辑调用：切换动作，opts = { restart, speed, startTime }
function Play(name, opts)
  if not started then
    pendingName = name
    pendingOpts = opts
    return true
  end
  local clip = clips[name]
  if clip == nil then
    logger:warnOnce("unknown-action", "未知动作 " .. tostring(name))
    return false
  end
  opts = opts or {}
  if current == name and playing and opts.restart ~= true then
    if opts.speed ~= nil then actionSpeed = opts.speed end
    return true
  end
  captureBlend()
  current = name
  actionTime = opts.startTime or 0
  playing = true
  if opts.speed ~= nil then actionSpeed = opts.speed end
  applyPose()
  return true
end

function SetSpeed(value)
  if type(value) ~= "number" then return end
  if value < 0.05 then value = 0.05 end
  if value > 5 then value = 5 end
  actionSpeed = value
  PlaybackSpeed = value
end

function GetAction()
  return current
end

function GetActionTime()
  return actionTime
end

function GetRigStatus()
  return {
    ready = rigReady,
    boneCount = boneCount,
    expected = #BONE_ORDER,
    missing = table.concat(missingList, ", "),
    action = current,
    message = rigReady and "ok" or "bone-missing",
  }
end

function GetActionDuration(name)
  local clip = clips[name]
  if clip == nil then return 0 end
  return clip.duration
end

function GetHitTime(name)
  local clip = clips[name]
  if clip == nil then return 0 end
  return clip.hitTime
end