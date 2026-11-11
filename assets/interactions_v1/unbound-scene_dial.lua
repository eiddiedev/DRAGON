---@id 9c73064a-c29c-4053-bf4e-691ed112692c
---@referenceName scene_dial.lua
local U=CS.UnityEngine
local bus=require('modules.scene_interaction_bus')
local button=nil
local cooldown=0
function OnActorTriggerEnter(actor)
 if actor and actor.isLocal then self:EnableInteraction() end
end
function OnActorTriggerExit(actor)
 if actor and actor.isLocal then self:DisableInteraction() end
end
function OnFocus()
 if not button then button=self:AddInteractorButton() end
 if button then
  local text=button:GetComponentInChildren(typeof(U.UI.Text),true)
  if text then text.text='切换昼夜' end
 end
end
function OnLostFocus()
 if button then self:RemoveInteractorButton(button);button=nil end
end
function OnInteractorButtonClick(index)
 if index==1 and U.Time.time>=cooldown then
  cooldown=U.Time.time+1;bus.dialRequests=bus.dialRequests+1
 end
end
