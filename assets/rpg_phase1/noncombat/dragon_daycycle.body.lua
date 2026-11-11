---@displayName 龙眠共享昼夜
---@start
---@varSync DayState:string=""
---@hidden
---@end
local U=CS.UnityEngine
local scope=require('official.core.runtime_scope').from(self)
local state=nil
local net=false
local cooldown=0
local main,exploration
local function now()return CS.DouyinUtility.GetServerUnixTime()end
local function read(raw)local d=type(raw)=='string'and dkjson.decode(raw);if d and type(d.day)=='boolean'and type(d.at)=='number'then state=d end end
function OnNetSpawned()
 net=true;DayState:OnValueChange(read);read(DayState:GetValue())
end
function OnNetDestroy()net=false end
function OnOwnershipTransferred()if net then read(DayState:GetValue())end end
function IsDay()return state and state.day or false end
function GetStatus()return{ready=state~=nil,day=IsDay(),authority=net and self:HasOwnership(),at=state and state.at}end
function RequestToggle()
 if not net or not state then return false,'房间时间尚未同步'end
 if exploration and exploration.IsBattleActive()then return false,'战斗结束后才能切换昼夜'end
 local a=CS.DouyinActorService.GetLocalActor();if not a then return false,'角色尚未就绪'end
 self:SendMessageToOwner('ReceiveToggle',tostring(a.actorID));return true
end
function ReceiveToggle(actorId)
 if not net or not self:HasOwnership()or now()<cooldown then return end
 if exploration and exploration.IsBattleActive()then return end
 local a=CS.DouyinActorService.GetActorById(tonumber(actorId)or -1)
 local dial=U.GameObject.Find('time_dial');if not a or not dial or U.Vector3.Distance(a.position,dial.transform.position)>6 then return end
 cooldown=now()+5;state={day=not IsDay(),at=now(),version=(state and state.version or 0)+1};DayState:SetValue(dkjson.encode(state))
end
function Update()
 if not main then main=scope:GetScript('dragon_world_bridge.lua');exploration=scope:GetScript('dragon_exploration.lua')end
 if net and CS.DouyinNetService.isNetworkSettled and self:HasOwnership()and not state then state={day=false,at=now(),version=1};DayState:SetValue(dkjson.encode(state))end
 if state and main then main.SetSharedDay(state.day)end
 -- Existing sundial publishes this request only after its native interaction button is clicked.
 if U.Shader.GetGlobalFloat('_DragonDialRequest')>0 then
  U.Shader.SetGlobalFloat('_DragonDialRequest',0);local ok,why=RequestToggle();if not ok then CS.DouyinUtility.Toast(why)end
 end
end
