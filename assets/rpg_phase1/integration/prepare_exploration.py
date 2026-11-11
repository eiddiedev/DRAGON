from pathlib import Path
D=Path(__file__).resolve().parent;N=D.parent/'noncombat'
s=(N/'dragon_exploration.body.lua').read_text()
a=s.index('local function battleScript()');b=s.index('\nfunction IsBattleActive()',a)
s=s[:a]+"local function battleScript()return scope:GetScript('dragon_combat.lua')end\n"+s[b:]
a=s.index('function OpenContract(');b=s.index('\nlocal function openTasks()',a)
s=s[:a]+'''function OpenContract(respec,continuation)
 local rpg=scope:GetScript('dragon_rpg.lua')
 if unavailable()or not rpg then return false end
 return rpg.OpenContract(respec,function()
  if actor then actor:Immobilize(false)end
  if continuation then continuation()end
 end)
end
'''+s[b:]
# Avoid stacking two Graphic components on the same object.
s=s.replace("panel=rect(root.transform,'QuestBook',1100,740,0,0);panel:AddComponent(typeof(U.UI.Image)).color=U.Color(.91,.85,.72,1)","panel=rect(root.transform,'QuestBook',1100,740,0,0)")
s=s.replace("im.texture=tex;im.color=U.Color.white end","im.texture=tex;im.color=U.Color.white else panel:AddComponent(typeof(U.UI.Image)).color=U.Color(.91,.85,.72,1)end")
s=s.replace("V2(86,-215)","V2(86,-320)")
# Find inactive egg stages without reactivating unrelated assets.
s=s.replace("for i=0,3 do local go=U.GameObject.Find('tripo_egg_stage_'..i);if go then eggs[i]={go=go,scale=go.transform.localScale}end end",'''local all=U.Resources.FindObjectsOfTypeAll(typeof(U.Transform))
 for j=0,all.Length-1 do local t=all[j];local i=tonumber(string.match(t.name,'^tripo_egg_stage_(%d)$'))
  if i and i<=3 and t.gameObject.scene.IsValid and t.gameObject.scene:IsValid()then eggs[i]={go=t.gameObject,scale=t.localScale}end
 end''')
# Egg interaction follows a stable location instead of the hidden stage-zero object.
s=s.replace("add('tripo_egg_stage_0','egg',4,'龙蛋 · 供奉')","local egg=U.GameObject.Find('tripo_egg_stage_0');if egg then targets[#targets+1]={position=egg.transform.position,kind='egg',radius=5,height=5,label='龙蛋 · 供奉'}end")
(D/'dragon_exploration.body.lua').write_text(s)
s=(N/'dragon_daycycle.body.lua').read_text()
s=s.replace("function GetStatus()",'''function GetWorldClock()
 if not state then return nil end
 local minutes=((state.day and 360 or 1080)+math.min(240,math.max(0,now()-state.at))*3)%1440
 return string.format('%02d:%02d',math.floor(minutes/60),math.floor(minutes%60))
end
function GetStatus()''')
s=s.replace(' if state and main then main.SetSharedDay(state.day)end', ''' if state and net and self:HasOwnership()and now()-state.at>=240 and not(exploration and exploration.IsBattleActive())then
  state={day=not state.day,at=now(),version=state.version+1};DayState:SetValue(dkjson.encode(state))
 end
 if state and main then main.SetSharedDay(state.day)end''')
(D/'dragon_daycycle.body.lua').write_text(s)
p=D/'dragon_world_bridge.body.lua';s=p.read_text()
a=s.index('    clock = clock + Time.deltaTime',s.index('local function updateDayNight'))
b=s.index('    local target = isDay and 1 or 0',a)
s=s[:a]+'    clock = clock + Time.deltaTime\n'+s[b:]
p.write_text(s)
print('Prepared exploration and shared day/night bridge')
