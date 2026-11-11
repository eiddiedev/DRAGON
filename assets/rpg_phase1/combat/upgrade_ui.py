from cli import D
from pathlib import Path
ref=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project_nuk7p7hj/scripts/modules/ui_31.lua').read_text()
art=ref[ref.index('local function installQuietArt()'):ref.index('local function artAt(')]
art=art.replace('local function installQuietArt()', 'local icons={}\nlocal iconAssets={}\nlocal function installIcons()').replace('S.art[key]=sp;S.cartoonAssets[#S.cartoonAssets+1]=tex;S.cartoonAssets[#S.cartoonAssets+1]=sp','icons[key]=sp;iconAssets[#iconAssets+1]=tex;iconAssets[#iconAssets+1]=sp')
art=art.replace(' local function sprite(key,lines,circle)', ''' shapes.frost={{32,5,32,59},{9,19,55,45},{9,45,55,19},{24,10,32,18},{32,18,40,10},{24,54,32,46},{32,46,40,54},{11,29,19,25},{19,25,19,15},{45,49,45,39},{45,39,55,35}}
 shapes.meteor={{13,40,17,52},{17,52,29,55},{29,55,40,44},{40,44,37,33},{37,33,26,29},{26,29,13,40},{26,29,43,9},{37,33,55,13},{42,23,52,6},{21,42,27,47}}
 shapes.rain={{13,9,13,45},{8,39,13,45},{13,45,18,39},{32,18,32,56},{27,50,32,56},{32,56,37,50},{51,7,51,44},{46,38,51,44},{51,44,56,38}}
 shapes.book={{9,12,31,18},{31,18,55,12},{9,12,9,49},{9,49,31,55},{31,55,55,49},{55,49,55,12},{31,18,31,55}}
 shapes.exit={{25,12,12,12},{12,12,12,52},{12,52,25,52},{25,32,55,32},{45,22,55,32},{55,32,45,42}}
 local function sprite(key,lines,circle)''')
p=D/'dragon_rpg.body.lua';r=p.read_text();r=r.replace('local getRing','local getRing\nlocal skillButtons={}\n'+art)
r=r.replace('local function buildUI()', '''local function setIcon(button,key,size)
 local tr=button.transform:Find("ActionGlyph");local go=tr and tr.gameObject
 if not go then go=rect(button.transform,"ActionGlyph",size,size,0,0);go:AddComponent(typeof(U.UI.Image))end
 local im=go:GetComponent(typeof(U.UI.Image));im.sprite=icons[key]or icons.sword;im.color=U.Color.white;im.raycastTarget=false;im.preserveAspect=true
 return im
end
local function buildUI()''')
r=r.replace(' if not sourceFont()then return false end',' if not sourceFont()then return false end\n installIcons()')
r=r.replace('toggleLabel.fontSize=23','toggleLabel.fontSize=23;toggleLabel.text="";setIcon(toggle,"sword",55)')
r=r.replace('battleLabel.fontSize=22','battleLabel.fontSize=22;battleLabel.text="";setIcon(battleButton,"shield",50)')
r=r.replace('txt.fontSize=22;previewButton=btn','txt.fontSize=22;txt.text="";setIcon(btn,"book",50);previewButton=btn')
r=r.replace(' return true\nend\ngetRing=', ''' for i=2,3 do
  local index=i
  local b,t=makeButton(root.transform,"Skill"..i,"",106,106,i==2 and -300 or -140,i==2 and 420 or 330,function()skillPressed=index end,V2(1,0))
  b.image.sprite=getRing();b.image.color=U.Color.white;t.fontSize=25
  skillButtons[i]={button=b,label=t};b.gameObject:SetActive(false)
 end
 return true
end
getRing=''')
r=r.replace(' for _,v in ipairs(native)do\n  if v.trigger', ' for _,v in pairs(skillButtons)do v.button.gameObject:SetActive(false)end\n for _,v in ipairs(native)do\n  local glyph=v.button and v.button.transform:Find("ActionGlyph");if glyph then U.Object.Destroy(glyph.gameObject)end\n  if v.trigger')
r=r.replace('bindSlot(CS.UIType.CustomMain,"普攻"','bindSlot(CS.UIType.CustomMain,""').replace('bindSlot(CS.UIType.CustomSub,"技能",function()skillPressed=true','bindSlot(CS.UIType.CustomSub,"",function()skillPressed=1')
r=r.replace('  hideExplore();context.mode="combat";toggleLabel.text="收起"', '''  local cls=rules.GetClasses()[profile.class]
  setIcon(native[1].button,profile.class=="melee"and "sword"or(profile.class=="mage"and "prism"or "bow"),80)
  setIcon(native[2].button,cls.skills[1].icon,62)
  for i=2,3 do local v=skillButtons[i];setIcon(v.button,cls.skills[i].icon,62);v.button.gameObject:SetActive(true)end
  hideExplore();context.mode="combat";toggleLabel.text="";setIcon(toggle,"exit",55)''')
r=r.replace('toggleLabel.text="武器"','toggleLabel.text="";setIcon(toggle,"sword",55)')
r=r.replace('kind=="skill"and"skill1"or"attack"','kind')
r=r.replace('if skillPressed then skillPressed=false;act("skill")','if skillPressed then local index=skillPressed;skillPressed=false;act("skill"..index)')
r=r.replace('battleLabel.text=battle and battle.IsParticipating()and "撤离"or "试炼";', 'battleLabel.text="";setIcon(battleButton,battle and battle.IsParticipating()and "exit"or "shield",50);')
a=r.index('  local left=math.max');b=r.index('\n end\n for i=#pending',a)
r=r[:a]+'''  for i=1,3 do
   local slot=i==1 and native[2]or skillButtons[i];local left=math.max(0,(context["skill"..i.."Until"]or 0)-U.Time.time)
   if slot then
    if slot.label then slot.label.text=left>0 and string.format("%.1f",left)or "";slot.label.transform:SetAsLastSibling()end
    local glyph=slot.button.transform:Find("ActionGlyph");if glyph then glyph:GetComponent(typeof(U.UI.Image)).color=left>0 and U.Color(1,1,1,.22)or U.Color.white end
    slot.button.image.color=left>0 and U.Color(1,1,1,.45)or U.Color.white
   end
  end''' +r[b:]
r=r.replace('nativeSlots=#native,', 'nativeSlots=#native,skills=rules and profile and profile.class and rules.GetClasses()[profile.class].skills,skillCooldowns=context and {context.skill1Until,context.skill2Until,context.skill3Until},')
r=r.replace(' if root then U.Object.Destroy(root)end', ' for _,a in ipairs(iconAssets)do U.Object.Destroy(a)end;iconAssets={}\n if root then U.Object.Destroy(root)end')
p.write_text(r)
print('native action icons, three individual skill buttons and cooldown masks')
