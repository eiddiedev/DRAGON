---@id 58efb022-0860-477c-8b70-991c35b1021f
---@sourceScriptId e3d6fae0-7eb5-419b-ba94-d312f39858de
---@referenceName dragon_progress.lua
---@displayName 龙眠本次游玩进度
---@start
---@var PreviewOnly:boolean=false
---@name 隔离验证档案
---@end
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

local rules,profile
local sequence=0
-- Session-only progression: materials and daily quotas follow normal rules.
local stopped=false
local message=''
local function ready()
 if stopped then return false end
 if not rules then rules=getDependency('dragon_progress_rules.lua')end
 if not rules then return false end
 if not profile then profile=rules.New()end
 return true
end
function IsLoaded()return ready()end
function GetProfile()if ready()then return rules.Copy(profile)end end
function CanRideDragon()return ready()and profile.pact==true end
function GetStatus()return{loaded=ready(),busy=false,pending=false,message=message,revision=profile and profile.revision,preview=PreviewOnly,persistent=false,testMode=false}end
function Submit(kind,args,callback)
 if not ready()then return false,'玩法正在初始化'end
 local t=CS.DouyinUtility.GetServerUnixTime()+CS.DouyinUtility.GetServerTime().Millisecond/1000
 sequence=sequence+1
 local op=rules.Copy(args or{});op.kind=kind;op.id='session:'..sequence;op.now=t;op.day=math.floor((t+28800)/86400)
 local updated,reason,repeated=rules.Apply(profile,op)
 if not updated then return false,reason end
 profile=updated;message=reason or ''
 if callback then callback(true,message,repeated)end
 return true,op.id
end
function SelectClass(kind,callback)return Submit('class',{class=kind},callback)end
function AwardBattle(battleId,amount,callback)return Submit('battle',{battleId=battleId,amount=amount},callback)end
function Retry()return ready()end
function Update()ready()end
function OnDestroy()stopped=true;profile=nil end

do local previous=OnDestroy;function OnDestroy()if previous then previous()end;ReleaseMobileDependencies()end end
