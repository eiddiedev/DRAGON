-- Narrow integration appended to the latest world script, not an old scene snapshot.
DR.phase1={}
function IsMounted()
 local a=DouyinActorService.GetLocalActor()
 return DR.rider~=nil or (a and (a:IsSitting()or a:IsFlying())) or false
end
function CanRideDragon()
 local p=DR.phase1.progress
 return p~=nil and p.CanRideDragon()
end
function GetBookTexture()return UI.tex and UI.tex.ui_book end
function GetExplorationState()return UI.state end
function ApplySavedClass(kind)
 local r,p=DR.phase1.rpg,DR.phase1.progress
 if r and p and p.IsLoaded()then r.SetProfile(p.GetProfile())end
end
function SetExplorationMenu(open)
 DR.phase1.menu=open
 local a=DouyinActorService.GetLocalActor();if a then UI.lockPlayer(a,open)end
end
function ReplayPrologue()
 if UI.P_book then UI.setSpread(1);UI.show(UI.P_book,true);UI.state='book';UI.st=UI.t
  local a=DouyinActorService.GetLocalActor();if a then UI.lockPlayer(a,true)end
 end
end
function SetSharedDay(day)if isDay~=day then setDay(day)end end
function GetWorldTime()return {day=isDay,elapsed=clock,duration=isDay and DAY_SECONDS or NIGHT_SECONDS}end
DR.phase1.originalUpdate=Update
function Update()
 DR.phase1.originalUpdate()
 local s=DR.phase1
 if not s.scope then s.scope=require('official.core.runtime_scope').from(self)end
 if not s.rpg then s.rpg=s.scope:GetScript('dragon_rpg.lua')end
 if not s.progress then s.progress=s.scope:GetScript('dragon_progress.lua')end
 if not s.rpg or not s.progress then return end
 local a=DouyinActorService.GetLocalActor();if not a then return end
 local playing=UI.state=='play'
 s.rpg.SetContext({menu=not playing or s.menu==true,mounted=IsMounted()})
 s.rpg.SetExplorationReady(playing and not s.menu and s.progress.IsLoaded())
 if playing and s.progress.IsLoaded()and not s.progress.GetProfile().class and not s.contract then
  s.contract=s.rpg.OpenContract(false,function()s.contract=false;UI.lockPlayer(a,false)end)
 end
end
