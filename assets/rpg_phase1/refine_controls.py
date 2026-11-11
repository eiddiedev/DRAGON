from pathlib import Path
p=Path(__file__).parent/'dragon_rpg.body.lua';s=p.read_text()
s=s.replace('local held=false','local held=false\nlocal attackPressed=false\nlocal ringSprite,ringTexture')
s=s.replace('local function clearSlots()','''local function getRing()
 if ringSprite then return ringSprite end
 ringTexture=U.Texture2D(96,96,U.TextureFormat.RGBA32,false)
 local pixels=CS.System.Array.CreateInstance(typeof(U.Color),96*96)
 for y=0,95 do for x=0,95 do
  local d=math.sqrt((x-47.5)^2+(y-47.5)^2)
  pixels[y*96+x]=d>46 and U.Color.clear or(d>42 and U.Color(1,.94,.8,.95)or U.Color(.13,.08,.17,.85))
 end end
 ringTexture:SetPixels(pixels);ringTexture:Apply()
 ringSprite=U.Sprite.Create(ringTexture,U.Rect(0,0,96,96),V2(.5,.5),100)
 return ringSprite
end
local function clearSlots()''')
s=s.replace(' held=false;skillPressed=false;pending={}',' held=false;attackPressed=false;skillPressed=false;pending={}')
s=s.replace('  if v.button then v.button.gameObject:SetActive(false)end','''  if v.button then
   v.button.gameObject:SetActive(false)
   if v.old then
    v.button.image.sprite=v.old.sprite;v.button.image.color=v.old.color
    local rt=v.button.transform;rt.localPosition=v.old.position;rt.sizeDelta=v.old.size
    if v.label then v.label.text=v.old.text;v.label.font=v.old.font;v.label.fontSize=v.old.fontSize;v.label.alignment=v.old.alignment;v.label.rectTransform.localPosition=v.old.labelPosition;v.label.rectTransform.sizeDelta=v.old.labelSize end
   end
  end''')
s=s.replace('local function bindSlot(kind,text,down,up)','local function bindSlot(kind,text,down,up,targetType)')
s=s.replace(' local t=btn:GetComponentInChildren(typeof(U.UI.Text),true)\n if t then t.gameObject:SetActive(true);t.text=text end\n btn.gameObject:SetActive(true)\n local entry={button=btn,trigger=trigger,label=t};',''' local t=btn:GetComponentInChildren(typeof(U.UI.Text),true)
 local rt=btn.transform
 local old={sprite=btn.image.sprite,color=btn.image.color,position=rt.localPosition,size=rt.sizeDelta}
 if t then
  old.text=t.text;old.font=t.font;old.fontSize=t.fontSize;old.alignment=t.alignment;old.labelPosition=t.rectTransform.localPosition;old.labelSize=t.rectTransform.sizeDelta
  t.gameObject:SetActive(true);t.text=text;t.font=font;t.fontSize=25;t.alignment=U.TextAnchor.MiddleCenter;t.rectTransform.localPosition=V3.zero;t.rectTransform.sizeDelta=V2(120,65)
 end
 btn.image.sprite=getRing();btn.image.color=U.Color.white
 local target=CS.DouyinUIService.GetInteractionButton(CS.HandType.Right,targetType)
 if target then rt.position=target.transform.position;rt.sizeDelta=target.transform.sizeDelta end
 btn.gameObject:SetActive(true)
 local entry={button=btn,trigger=trigger,label=t,old=old};''')
s=s.replace('bindSlot(CS.UIType.CustomMain,"普攻",function()held=true end,function()held=false end)','bindSlot(CS.UIType.CustomMain,"普攻",function()held=true;attackPressed=true end,function()held=false end,CS.UIType.Jump)')
s=s.replace('bindSlot(CS.UIType.CustomSub,rules.GetClasses()[profile.class].skill,function()skillPressed=true end,function()end)','bindSlot(CS.UIType.CustomSub,"技能",function()skillPressed=true end,function()end,CS.UIType.HoldHands)')
s=s.replace('elseif held then act("attack")end','elseif held or attackPressed then attackPressed=false;act("attack")end')
s=s.replace('or rules.GetClasses()[profile.class].skill end','or "技能" end')
s=s.replace('(safe.yMin)*scale+350','(safe.yMin)*scale+(context.mode=="combat"and 550 or 450)')
s=s.replace('if not focused then held=false;skillPressed=false end','if not focused then held=false;attackPressed=false;skillPressed=false end')
s=s.replace(' if root then U.Object.Destroy(root);root=nil end',' if root then U.Object.Destroy(root);root=nil end\n if ringSprite then U.Object.Destroy(ringSprite);U.Object.Destroy(ringTexture);ringSprite=nil;ringTexture=nil end')
s=s.replace('ready=ready,contract=contract and contract.activeSelf,','ready=ready,sequence=context and context.sequence,contract=contract and contract.activeSelf,')
p.write_text(s)
