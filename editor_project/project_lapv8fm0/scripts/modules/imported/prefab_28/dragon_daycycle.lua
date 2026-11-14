---@id 8d930cce-71ff-437d-abc4-8f01f7eb1b72
---@sourceScriptId 1df9f054-e0d2-43ca-8ad0-daac450d7806
---@referenceName dragon_daycycle.lua
---@displayName 龙眠共享昼夜
---@start
---@varSync DayState:string=""
---@hidden
---@varSync DragonState:string=""
---@hidden
---@end
local U=CS.UnityEngine
local scope=require('official.core.runtime_scope').from(self)
-- review-v27: private cache. Never replace the shared runtime-scope resolver.
local getDependency
local dependencyMemo,dependencyAttempts,dependencyNextAt,dependencyFailures={},{},{},{}
getDependency=function(name)
 if dependencyMemo[name] then return dependencyMemo[name] end
 local now=CS.UnityEngine.Time.realtimeSinceStartup
 if now<(dependencyNextAt[name] or 0) then return nil end
 local attempt=(dependencyAttempts[name] or 0)+1
 dependencyAttempts[name]=attempt
 -- Fast initial readiness checks, then bounded slow recovery for streamed resources.
 dependencyNextAt[name]=now+(attempt<30 and 1 or 5)
 local ok,value=pcall(function()return scope:GetScript(name)end)
 if ok and value then
  dependencyMemo[name]=value;dependencyFailures[name]=nil
  if attempt>=30 then print('[review-v27] dependency recovered: '..name) end
  return value
 end
 dependencyFailures[name]=tostring(value or 'not loaded')
 if attempt==30 then print('[review-v27] dependency waiting: '..name..' '..dependencyFailures[name]) end
 return nil
end
function GetDependencyDiagnostics()return{build='review-v27',attempts=dependencyAttempts,failures=dependencyFailures}end
local function ReleaseMobileDependencies()
 dependencyMemo={};dependencyAttempts={};dependencyNextAt={};dependencyFailures={}
end

local state=nil
local net=false
local cooldown=0
local main,exploration
local function now()return CS.DouyinUtility.GetServerUnixTime()end
local function read(raw)local d=type(raw)=='string'and dkjson.decode(raw);if d and type(d.day)=='boolean'and type(d.at)=='number'then state=d end end
-- v15 唤龙同步：同一时间只有一位龙骑能唤龙；龙的位置由唤龙的人上报，房主写进同步变量
local dragon=nil
local battleWas=false
local dragonRegistered=false
local function readDragon(raw)local d=type(raw)=='string'and raw~=''and dkjson.decode(raw);if d and type(d.id)=='string'then dragon=d end end
local function me()local a=CS.DouyinActorService.GetLocalActor();return a and tostring(a.actorID)or nil end
local function dragonBusy(by)return dragon and dragon.id~=''and dragon.id~=by and now()-(dragon.at or 0)<25 end
function ReceiveDragon(raw)
 if not net or not self:HasOwnership()or type(raw)~='string'or #raw>400 then return end
 local q=dkjson.decode(raw);if not q or type(q.id)~='string'then return end
 if q.k=='claim'then
  if dragonBusy(q.id)then return end
  dragon={id=q.id,at=now(),x=q.x or 0,y=q.y or 0,z=q.z or 0,yaw=q.yaw or 0,idle=1}
 elseif q.k=='pose'then
  if not dragon or dragon.id~=q.id then return end
  dragon={id=q.id,at=now(),x=q.x,y=q.y,z=q.z,yaw=q.yaw,idle=q.idle}
 elseif q.k=='release'then
  if not dragon or dragon.id~=q.id then return end
  dragon={id='',at=now()}
 else return end
 DragonState:SetValue(dkjson.encode(dragon))
end
local function sendDragon(q)
 if not net then if q.k=='release'then dragon=nil else dragon=q;dragon.at=now()end;return end
 local raw=dkjson.encode(q)
 if self:HasOwnership()then ReceiveDragon(raw)else self:SendMessageToOwner('ReceiveDragon',raw)end
end
function DragonClaim()
 local id=me();if not id then return false,'角色尚未就绪'end
 if dragonBusy(id)then return false,'墨曜正在回应另一位龙骑，请稍后'end
 sendDragon({k='claim',id=id});return true
end
function DragonPose(x,y,z,yaw,idle)
 local id=me();if not id then return end
 local r=function(v)return math.floor(v*10+.5)/10 end
 sendDragon({k='pose',id=id,x=r(x),y=r(y),z=r(z),yaw=r(yaw),idle=idle})
end
function DragonRelease()local id=me();if id then sendDragon({k='release',id=id})end end
function DragonOwner()return dragon and now()-(dragon.at or 0)<25 and dragon.id or ''end
function DragonRemote()local id=me();if id and dragonBusy(id)and dragon.x then return dragon end end
function OnNetSpawned()
 net=true;DayState:OnValueChange(read);read(DayState:GetValue())
 DragonState:OnValueChange(readDragon);readDragon(DragonState:GetValue())
end
function OnNetDestroy()net=false end
function OnOwnershipTransferred()if net then read(DayState:GetValue());readDragon(DragonState:GetValue())end end
function IsDay()return state and state.day or false end
function GetWorldClock()
 if not state then return nil end
 local minutes=((state.day and 360 or 1080)+math.min(720,math.max(0,now()-state.at)))%1440
 return string.format('%02d:%02d',math.floor(minutes/60),math.floor(minutes%60))
end
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
 if not main then main=getDependency('dragon_world_bridge.lua')end
 if not exploration then exploration=getDependency('dragon_exploration.lua')end
 if net and CS.DouyinNetService.isNetworkSettled and self:HasOwnership()and not state then state={day=false,at=now(),version=1};DayState:SetValue(dkjson.encode(state))end
 local fighting=exploration and exploration.IsBattleActive()
 if state and net and self:HasOwnership()and battleWas and not fighting and not state.day and now()-state.at>=600 then
  -- 刚打完一场：黑夜至少再留两分钟，魔法阵不会一退出就消失
  state={day=false,at=now()-600,version=state.version+1};DayState:SetValue(dkjson.encode(state))
 end
 battleWas=fighting
 if state and net and self:HasOwnership()and now()-state.at>=720 and not fighting then
  state={day=not state.day,at=now(),version=state.version+1};DayState:SetValue(dkjson.encode(state))
 end
 if main and not dragonRegistered then dragonRegistered=true;main.RegisterScript('cycle',{IsDay=IsDay,GetWorldClock=GetWorldClock,DragonClaim=DragonClaim,DragonPose=DragonPose,DragonRelease=DragonRelease,DragonOwner=DragonOwner,DragonRemote=DragonRemote})end
 if state and main then main.SetSharedDay(state.day)end
 -- Existing sundial publishes this request only after its native interaction button is clicked.
 if U.Shader.GetGlobalFloat('_DragonDialRequest')>0 then
  U.Shader.SetGlobalFloat('_DragonDialRequest',0);local ok,why=RequestToggle();if not ok then CS.DouyinUtility.Toast(why)end
 end
end

do local previous=OnDestroy;function OnDestroy()if previous then previous()end;ReleaseMobileDependencies()end end
