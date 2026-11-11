---@displayName 龙眠本次游玩进度
---@start
---@var PreviewOnly:boolean=false
---@name 隔离验证档案
---@end
local scope=require('official.core.runtime_scope').from(self)
local rules,profile
local sequence=0
-- Explicitly requested unlimited-resource QA build; no persistent profile.
local function replenish()
 for _,key in ipairs({'moon','ember','stardew','mushroom','flower','wool','charred'})do profile[key]=99999 end
 for key in pairs(profile.potions)do profile.potions[key]=99 end
 profile.daily={mushroom=0,flower=0,wool=0,ember=0}
end
local stopped=false
local message=''
local function ready()
 if stopped then return false end
 if not rules then rules=scope:GetScript('dragon_progress_rules.lua')end
 if not rules then return false end
 if not profile then profile=rules.New();replenish()end
 return true
end
function IsLoaded()return ready()end
function GetProfile()if ready()then return rules.Copy(profile)end end
function CanRideDragon()return ready()and profile.pact==true end
function GetStatus()return{loaded=ready(),busy=false,pending=false,message=message,revision=profile and profile.revision,preview=PreviewOnly,persistent=false,testMode=true}end
function Submit(kind,args,callback)
 if not ready()then return false,'玩法正在初始化'end
 local t=CS.DouyinUtility.GetServerUnixTime()+CS.DouyinUtility.GetServerTime().Millisecond/1000
 sequence=sequence+1
 local op=rules.Copy(args or{});op.kind=kind;op.id='session:'..sequence;op.now=t;op.day=math.floor((t+28800)/86400)
 replenish()
 local updated,reason,repeated=rules.Apply(profile,op)
 if not updated then return false,reason end
 profile=updated;replenish();message=reason or ''
 if callback then callback(true,message,repeated)end
 return true,op.id
end
function SelectClass(kind,callback)return Submit('class',{class=kind},callback)end
function AwardBattle(battleId,amount,callback)return Submit('battle',{battleId=battleId,amount=amount},callback)end
function Retry()return ready()end
function Update()ready()end
function OnDestroy()stopped=true;profile=nil end
