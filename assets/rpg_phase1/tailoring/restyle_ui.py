from pathlib import Path
D=Path(__file__).resolve().parent
s=(D/'ui-before.lua').read_text()
s=s.replace('local ringSprite,ringTexture','local ringSprite,ringTexture\nlocal getRing\nlocal detailLabel\nlocal ink=U.Color(.18,.13,.086,1)\nlocal cinnabar=U.Color(.61,.17,.12,1)')
s=s.replace('t.color=U.Color(1,.92,.75,1)','t.color=U.Color.white')
s=s.replace('im.color=U.Color(.16,.1,.2,.95)','im.color=U.Color(1,1,1,.035)')
s=s.replace('local function getRing()','getRing=function()')
s=s.replace('U.Color(1,.94,.8,.95)or U.Color(.13,.08,.17,.85)','U.Color(1,1,1,.9)or U.Color(1,1,1,.035)')
s=s.replace('"武器",108,84','"武器",92,92')
s=s.replace(' toggle.gameObject:SetActive(false)',' toggle.image.sprite=getRing();toggle.image.color=U.Color.white;toggleLabel.fontSize=23\n toggle.gameObject:SetActive(false)',1)
a=s.index(' contract=rect(root.transform,"ClassContract"');b=s.index(' local confirm\n',a)
s=s[:a]+''' contract=rect(root.transform,"ClassContract",1200,800,0,0)
 local book=scope:GetGameObjectByPath("ContractBook")
 local renderer=book and book:GetComponentInChildren(typeof(U.Renderer),true)
 local texture=nil
 if renderer then for _,key in ipairs({"_BaseTex","_BaseMap","_MainTex"})do if renderer.sharedMaterial:HasProperty(key)then texture=texture or renderer.sharedMaterial:GetTexture(key)end end;book:SetActive(false)end
 local background=contract:AddComponent(typeof(U.UI.RawImage));background.texture=texture;background.color=U.Color.white
 local title=label(contract.transform,"Title","守 夜 人 誓 约",39,470,70,-275,275);title.color=cinnabar
 local hint=label(contract.transform,"Hint","以此名立誓，守护龙的长梦。",22,460,55,-275,210);hint.color=ink
 local names={"melee","mage","ranged"}
 local descriptions={melee="剑誓 · 骑士\\n\\n身披铠甲，直面暗夜。\\n以利刃驱散影灵，以护盾守住同伴。\\n\\n近战 · 破晓守护",mage="星誓 · 法师\\n\\n将散落的星火聚于掌心。\\n用法杖唤醒魔力，让群星划破黑夜。\\n\\n远程 · 星火爆裂",ranged="风誓 · 游侠\\n\\n披林间的风，循月色而行。\\n拉弓追逐游影，让箭羽回应誓言。\\n\\n远程 · 月羽连射"}
 detailLabel=label(contract.transform,"OathText","三条道路，同一个誓言。\\n\\n在左页选定职业，\\n在此签下你的名字。",27,450,410,280,60);detailLabel.color=ink
 for i,kind in ipairs(names)do
  local c=rules.GetClasses()[kind]
  local button,text=makeButton(contract.transform,"Class_"..kind,({"剑誓  /  骑士","星誓  /  法师","风誓  /  游侠"})[i],420,88,-275,90-(i-1)*112,function()
   selection=kind
   for k,v in pairs(uiRefs)do v.image.color=k==kind and U.Color(.61,.17,.12,.13)or U.Color(1,1,1,0)end
   detailLabel.text=descriptions[kind];confirmLabel.text="立下誓约 · "..c.name
  end)
  button.image.color=U.Color(1,1,1,0);text.fontSize=29;text.color=ink;uiRefs[kind]=button
 end
''' +s[b:]
s=s.replace('"选择职业后签约",380,74,0,-105','"选择职业后签约",390,74,280,-240')
s=s.replace(' statusLabel=label(contract.transform,"Status","骑士守护近战 · 法师星火爆裂 · 游侠月羽连射",22,850,70,0,-205)',' confirm.image.color=U.Color(.61,.17,.12,.14);confirmLabel.color=cinnabar\n statusLabel=label(contract.transform,"Status","日后可在萤光古树下，重新立誓。",19,460,60,-275,-280);statusLabel.color=U.Color(.42,.34,.25,1)')
s=s.replace('if PreviewMode then makeButton(root.transform,"PreviewClassSwitch","重新签约",190,58,0,-115,function()OpenContract(true,nil)end,V2(.5,1))end','if PreviewMode then local btn,txt=makeButton(root.transform,"PreviewClassSwitch","誓约",86,86,100,-205,function()OpenContract(true,nil)end,V2(0,1));btn.image.sprite=getRing();btn.image.color=U.Color.white;txt.fontSize=22 end')
(D.parent/'dragon_rpg.body.lua').write_text(s)
