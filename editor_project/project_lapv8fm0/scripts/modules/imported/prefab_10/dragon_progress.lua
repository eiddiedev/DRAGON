---@id e3d6fae0-7eb5-419b-ba94-d312f39858de
---@referenceName dragon_progress.lua
---@displayName 龙眠玩家进度
---@start
---@var PreviewOnly:boolean=false
---@name 隔离验证档案
---@end
local U=CS.UnityEngine
local scope=require('official.core.runtime_scope').from(self)
local rules,store,profile,identity
local loaded=false
local pending=nil
local busy=false
local retryAt=0
local sequence=0
local session=nil
local message='正在读取云端进度…'
local lastError=nil
local stopped=false
local loadAt=0
local function now()return CS.DouyinUtility.GetServerUnixTime()+CS.DouyinUtility.GetServerTime().Millisecond/1000 end
local function day(t)return math.floor((t+28800)/86400)end
local function decode(raw)
 if raw==nil then return rules.New()end
 local p=type(raw)=='string'and dkjson.decode(raw)or raw
 if rules.Validate(p)then return p end
 return nil
end
function IsLoaded()return loaded end
function GetProfile()return profile and rules.Copy(profile)or nil end
function CanRideDragon()return loaded and profile.pact==true end
function GetStatus()return{loaded=loaded,busy=busy,pending=pending~=nil,message=message,error=lastError,revision=profile and profile.revision,preview=PreviewOnly}end
local function fail(code)
 lastError=tostring(code);message='进度待保存（'..lastError..'）';busy=false;retryAt=U.Time.unscaledTime+5
end
local function flush()
 if not pending or busy or not store or stopped then return end
 busy=true;local job=pending
 DATASTORE(function()
  local result,reason,repeated=nil,nil,false
  local code,value=store:UpdateData('profile',function(raw)
   local current=decode(raw);if not current then reason='存档异常，已保留原数据';return raw end
   result,reason,repeated=rules.Apply(current,job.op)
   if not result then return raw end
   local encoded=dkjson.encode(result)
   if #encoded>5800 then result=nil;reason='存档已接近容量上限，未扣除材料';return raw end
   return encoded
  end)
  if stopped then return end
  if code~=0 then fail(code);return end
  busy=false;pending=nil;lastError=nil
  local saved=decode(value)
  if saved then profile=saved end
  message=reason or '进度已保存'
  if job.callback then job.callback(result~=nil,message,repeated)end
 end)
end
function Submit(kind,args,callback)
 if not loaded then return false,'进度尚未加载'end
 if pending then return false,'上一笔进度正在保存，请稍候'end
 local t=now();sequence=sequence+1
 local op=rules.Copy(args or{});op.kind=kind;op.id=session..':'..sequence;op.now=t;op.day=day(t)
 local candidate,reason=rules.Apply(profile,op);if not candidate then return false,reason end
 pending={op=op,callback=callback};message='正在保存…';flush();return true,op.id
end
function SelectClass(kind,callback)return Submit('class',{class=kind},callback)end
function AwardBattle(battleId,amount,callback)return Submit('battle',{battleId=battleId,amount=amount},callback)end
function Retry()retryAt=0;loadAt=0 end
function Update()
 if not rules then rules=scope:GetScript('dragon_progress_rules.lua')end
 if not rules or not CS.DouyinNetService.isNetworkSettled then return end
 if not loaded and not busy and U.Time.unscaledTime>=loadAt then
  local p=CS.DouyinPlayerService.GetLocalPlayer();if not p or not p.playerOpenID or p.playerOpenID==''then return end
  identity=p.playerOpenID;session=tostring(now())..':'..tostring(math.random(100000,999999));busy=true;loadAt=U.Time.unscaledTime+5
  DATASTORE(function()
   local code,s=CS.DouyinDataService.GetDataStore(PreviewOnly and 'dr_preview_v2'or 'dr_progress_v2',identity,false)
   if code~=0 then busy=false;lastError=tostring(code);message='读档失败，请重试';return end
   store=s;local rc,raw=store:GetData('profile')
   if rc~=0 and rc~=-10001 then busy=false;lastError=tostring(rc);message='读档失败，暂不开放材料操作';return end
   local value=rc==-10001 and rules.New()or decode(raw)
   if not value then busy=false;lastError='schema';message='存档格式异常，未覆盖';loadAt=math.huge;return end
   if rc==-10001 then
    local wc,saved=store:UpdateData('profile',function(existing)return existing or dkjson.encode(value)end)
    if wc~=0 then busy=false;lastError=tostring(wc);message='新档案待保存';return end
    value=decode(saved);if not value then busy=false;message='读档校验失败';return end
   end
   if stopped then return end
   profile=value;loaded=true;busy=false;lastError=nil;message='进度已加载'
   -- A disconnected cooking attempt consumed its ingredient; it cannot be redeemed later.
   if profile.cook then Submit('cookCancel')end
  end)
 end
 if pending and not busy and U.Time.unscaledTime>=retryAt then flush()end
end
function OnDestroy()stopped=true end
