-- Keep the imported sheep's skeletal animation in step with the existing pasture controller.
---@displayName 绵羊行走动画
local U = CS.UnityEngine
local previous, elapsed, current, warned = nil, 0, nil, false
function Start()
    previous = self.transform.position
end
function Update()
    elapsed = elapsed + U.Time.deltaTime
    if elapsed < 0.18 then return end
    local p = self.transform.position
    local distance = previous and U.Vector3.Distance(p, previous) or 0
    local desired = distance / elapsed > 0.08 and "Walk" or "Idle"
    previous, elapsed = p, 0
    if desired == current then return end
    local animator = self.gameObject:GetComponent(typeof(CS.ModularAnim.Runtime.UGCAnimator))
    if animator and animator.enabled and animator.Controller ~= nil then
        if animator:Play(desired) then current = desired end
    elseif not warned then
        U.Debug.LogWarning("Imported sheep animator is waiting for binding")
        warned = true
    end
end
