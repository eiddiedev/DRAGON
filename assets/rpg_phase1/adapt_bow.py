from pathlib import Path
p=Path(__file__).parent/'dragon_weapons.lua';s=p.read_text()
s=s.replace('local function buildRig(actor)','local function buildRig(actor, className)')
s=s.replace('local ok, bones = pcall(function()\n    return {','local left=className=="ranged"\n  local ok, bones = pcall(function()\n    return {',1)
for limb in ['UpperArm','LowerArm','Hand']:
 s=s.replace('animator:GetBoneTransform(HumanBodyBones.Right'+limb+')','animator:GetBoneTransform(left and HumanBodyBones.Left'+limb+' or HumanBodyBones.Right'+limb+')',1)
s=s.replace('  bones.reach = upperLength + lowerLength\n  return bones','''  bones.reach = upperLength + lowerLength
  if left then
    local upper=animator:GetBoneTransform(HumanBodyBones.RightUpperArm)
    local lower=animator:GetBoneTransform(HumanBodyBones.RightLowerArm)
    local hand=animator:GetBoneTransform(HumanBodyBones.RightHand)
    if upper and lower and hand then
      local a=vLength(vSub(lower.position,upper.position));local b=vLength(vSub(hand.position,lower.position))
      bones.draw={upper=upper,lower=lower,hand=hand,upperLength=a,lowerLength=b,reach=a+b}
    end
  end
  return bones''')
s=s.replace('buildRig(entry.actor)','buildRig(entry.actor, entry.className)').replace('buildRig(actor)','buildRig(actor, className)')
s=s.replace('entry.actor:CalculatePalmTransform(false)','entry.actor:CalculatePalmTransform(entry.className=="ranged")')
s=s.replace('local rig=buildRig(actor, className)','local rig=buildRig(actor, className)')
s=s.replace('for _,key in ipairs({"upper","lower","hand","spine"})do\n  local bone=entry.rig[key];if bone then entry.basePose[bone]=bone.localRotation end\n end','''for _,key in ipairs({"upper","lower","hand","spine"})do
  local bone=entry.rig[key];if bone then entry.basePose[bone]=bone.localRotation end
 end
 if entry.rig.draw then for _,key in ipairs({"upper","lower","hand"})do
  local bone=entry.rig.draw[key];entry.basePose[bone]=bone.localRotation
 end end''')
start=s.index('local function applyHoldingPose(entry)')
s=s[:start]+'''-- The DRAGON bow is held in the left hand; the right hand draws to the cheek.
local function applyBowPose(entry,now)
 local rig=entry.rig;local root=actorRoot(entry.actor)
 if not rig or not rig.draw or not root then return end
 local attack=entry.attack;local draw=.12;local weight=.8
 if attack then
  local elapsed=now-attack.startTime
  if elapsed>=attack.duration then clearAttack(entry);attack=nil
  else
   -- Release occurs at 0.33s, shared with the attack hit/effect window.
   draw=elapsed<.33 and math.min(1,elapsed/.3)or math.max(.12,1-(elapsed-.33)/.09)
   weight=1
  end
 end
 local aim=attack and attack.aimWorld or root.forward
 local leftTarget=vAdd(rig.upper.position,vAdd(vScale(aim,rig.reach*.9),vScale(root.up,-rig.reach*.12)))
 solveArm(rig,leftTarget,vScale(root.right,-1),weight)
 if entry.weaponLocalRotation then rig.hand.rotation=Quaternion.LookRotation(aim,root.up)*Quaternion.Inverse(entry.weaponLocalRotation)end
 local nearString=vAdd(rig.hand.position,vScale(root.right,.08))
 local cheek=vAdd(rig.draw.upper.position,vAdd(vScale(root.up,.14),vScale(root.forward,.12)))
 solveArm(rig.draw,vLerp(nearString,cheek,draw),vAdd(root.right,vScale(root.forward,-.4)),weight)
end

'''+s[start:]
s=s.replace('if not moving or entry.attack~=nil then applyHoldingPose(entry)end\n      if entry.attack ~= nil then applyAttack(entry, now)end','''if entry.className=="ranged" then
        applyBowPose(entry,now)
      else
        if not moving or entry.attack~=nil then applyHoldingPose(entry)end
        if entry.attack ~= nil then applyAttack(entry, now)end
      end''')
p.write_text(s)
