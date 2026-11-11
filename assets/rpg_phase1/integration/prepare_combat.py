"""Build integration-only sources from handed-off v14; never edit combat owner's sources."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;C=D.parent/'combat';N=D.parent/'noncombat'
def replace(s,a,b):
 assert s.count(a)==1, (a[:80],s.count(a))
 return s.replace(a,b,1)
r=(C/'dragon_rpg.body.lua').read_text()
r=replace(r,'local rules,outfits,weapons,fx,battle,combatRules','local rules,outfits,weapons,fx,battle,combatRules\nlocal progress,signPending')
a='''  local ok,why=rules.SelectClass(profile,selection,external.inBattle)
  if not ok then toast(why);return end
  context.class=profile.class
  contract:SetActive(false);backdrop:SetActive(false);if previewButton then previewButton.gameObject:SetActive(true)end;context.menu=false;ready=true
  local callback=contractCallback;contractCallback=nil
  if callback then callback(profile.class)else actor:Immobilize(false)end
  log:info("class contracted",profile.class)'''
b='''  if signPending then return end
  if not progress or not progress.IsLoaded()then toast("正在读取云端进度");return end
  if external.inBattle or external.mounted or actor:IsSitting()or actor:IsFlying()then toast("请先结束战斗或骑乘");return end
  signPending=true
  local ok,why=progress.SelectClass(selection,function(saved,message)
   signPending=false
   if not saved then toast(message);return end
   profile=progress.GetProfile();context.class=profile.class
   contract:SetActive(false);backdrop:SetActive(false);context.menu=false;ready=true
   local callback=contractCallback;contractCallback=nil
   if callback then callback(profile.class)else actor:Immobilize(false)end
   log:info("class saved",profile.class)
  end)
  if not ok then signPending=false;toast(why)end'''
r=replace(r,a,b)
r=replace(r,'if external.inBattle then toast("战斗结束后才能重新签约");return false end','if not progress or not progress.IsLoaded()then toast("正在读取云端进度");return false end\n if external.inBattle or external.mounted or actor:IsSitting()or actor:IsFlying()then toast("请先结束战斗或骑乘");return false end')
r=replace(r,'value.schema~=1','value.schema~=2')
r=replace(r,' if not profile then profile=rules.NewProfile();context={mode="explore",class=nil}end',''' if not progress then progress=scope:GetScript("dragon_progress.lua")end
 if not progress or not progress.IsLoaded()then return end
 profile=progress.GetProfile()
 if not context then context={mode="explore",class=profile.class}end
 context.class=profile.class''')
r=replace(r,'{GetProfile=GetProfile,SetMode=SetMode,SetContext=SetContext,ShowDamage=ShowDamage}','{GetProfile=GetProfile,SetMode=SetMode,SetContext=SetContext,ShowDamage=ShowDamage,AwardBattle=progress.AwardBattle}')
(D/'dragon_rpg.body.lua').write_text(r)
b=(C/'dragon_combat.body.lua').read_text()
a='''  resolved[state.epoch]=true;local p=rpg.GetProfile()
  if state.phase=='victory'then rules.RewardVictory(p,state.epoch,m.damage>0,m.hp>0)
  elseif not m.retreat then p.moon=math.floor(p.moon*.5)end'''
b=replace(b,a,'''  local epoch=state.epoch
  if state.phase=='victory'and m.damage>0 and m.hp>0 then
   -- Retry pending rewards on subsequent frames; storage transaction owns deduplication.
   if rpg.AwardBattle then
    resolved[epoch]='saving'
    local ok=rpg.AwardBattle(epoch,10,function(saved)
     resolved[epoch]=saved and true or nil
    end)
    if not ok then resolved[epoch]=nil end
   end
  else resolved[epoch]=true end''')
(D/'dragon_combat.body.lua').write_text(b)
for name in ['dragon_progress','dragon_progress_rules']:
 (D/(name+'.body.lua')).write_text((N/(name+'.body.lua')).read_text())
manifest={name:hashlib.sha256((D/(name+'.body.lua')).read_bytes()).hexdigest() for name in ['dragon_rpg','dragon_combat','dragon_progress','dragon_progress_rules']}
(D/'source-manifest.json').write_text(json.dumps(manifest,indent=2))
print('Prepared four integration modules; original combat source unchanged.')
