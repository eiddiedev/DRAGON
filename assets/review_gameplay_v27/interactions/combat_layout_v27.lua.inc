-- One screen-space layout for all combat controls, including native slots.
-- Pure math: points are pixels with a bottom-left origin, clamped inside safeArea.
local function computeCombatLayout(screenWidth,screenHeight,safe)
 local x0=math.max(0,safe.xMin or 0);local x1=math.min(screenWidth,safe.xMax or screenWidth)
 local y0=math.max(0,safe.yMin or 0);local y1=math.min(screenHeight,safe.yMax or screenHeight)
 if x1<=x0 or y1<=y0 then x0=0;x1=screenWidth;y0=0;y1=screenHeight end
 -- The established arc is retained. Skill 2 has an 18-unit hit-rectangle gap.
 -- Exit uses its own 128-unit design size, never the exploratory hand button size.
 local design={
  attack={x=-215,y=185,size=216,glyph=.5185},
  skill1={x=-235,y=422,size=136,glyph=.5735},
  skill2={x=-409,y=338,size=136,glyph=.5735},
  skill3={x=-464,y=165,size=136,glyph=.5735},
  exit={x=-76,y=392,size=128,glyph=.56}
 }
 local factor=math.min(screenHeight/1080,(x1-x0)*.55/544,(y1-y0)*.72/502)
 local result={scale=factor,safe={xMin=x0,xMax=x1,yMin=y0,yMax=y1},buttons={}}
 for key,p in pairs(design)do
  result.buttons[key]={x=x1+p.x*factor,y=y0+p.y*factor,size=p.size*factor,glyph=p.glyph}
 end
 return result
end
local function placeCombatRect(rt,p)
 local unit=math.max(.0001,math.abs(root.transform.lossyScale.x))
 rt.anchorMin=V2(1,0);rt.anchorMax=V2(1,0);rt.pivot=V2(.5,.5)
 rt.sizeDelta=V2(p.size/unit,p.size/unit)
 rt.anchoredPosition=V2((p.x-U.Screen.width)/unit,p.y/unit)
end
local function resizeCombatGlyph(button,fraction)
 local glyph=button.transform:Find('ActionGlyph')
 if glyph then glyph.sizeDelta=V2(button.transform.rect.width*fraction,button.transform.rect.height*fraction)end
end
local function layoutCombatControls()
 if not root or not toggle then return end
 local safe=U.Screen.safeArea
 local layout=computeCombatLayout(U.Screen.width,U.Screen.height,{xMin=safe.xMin,xMax=safe.xMax,yMin=safe.yMin,yMax=safe.yMax})
 C15.combatLayout=layout
 placeCombatRect(toggle.transform,layout.buttons.exit);resizeCombatGlyph(toggle,layout.buttons.exit.glyph)
 for i=2,3 do local slot=skillButtons[i]
  if slot then local p=layout.buttons['skill'..i];placeCombatRect(slot.button.transform,p);resizeCombatGlyph(slot.button,p.glyph)end
 end
 for i=1,2 do
  local p=layout.buttons[i==1 and 'attack'or'skill1']
  if not combatAnchors[i]then local _,rt=rect(root.transform,'CombatAnchor'..i,1,1,0,0,V2(1,0));combatAnchors[i]=rt end
  local anchor=combatAnchors[i];placeCombatRect(anchor,p)
  local slot=native[i]
  if slot then
   local rt=slot.button.transform
   -- Native canvases may have different parent AND local scale/pivots on phones.
   -- Match physical pixels, rather than copying our canvas's sizeDelta.
   local sx=math.max(.0001,math.abs(rt.lossyScale.x));local sy=math.max(.0001,math.abs(rt.lossyScale.y))
   rt:SetSizeWithCurrentAnchors(U.RectTransform.Axis.Horizontal,p.size/sx)
   rt:SetSizeWithCurrentAnchors(U.RectTransform.Axis.Vertical,p.size/sy)
   local shift=rt:TransformVector(V3((.5-rt.pivot.x)*rt.rect.width,(.5-rt.pivot.y)*rt.rect.height,0))
   rt.position=anchor.position-shift
   resizeCombatGlyph(slot.button,p.glyph)
  end
 end
end
