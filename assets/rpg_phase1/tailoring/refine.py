from pathlib import Path
D=Path(__file__).parent
p=D/'garments.lua';s=p.read_text()
s=s.replace("  mats[i]=m;", "  for _,key in ipairs({'_UseVertexColor','_RimPower','_FresnelInt','_UseTriplanarSample'})do if m:HasProperty(key)then m:SetFloat(key,0)end end\n  if m:HasProperty('_ColorPower')then m:SetFloat('_ColorPower',1)end\n  for _,key in ipairs({'_Normalmap','_ORM','_EmissionMask','_EmissionTex'})do if m:HasProperty(key)then m:SetTexture(key,nil)end end\n  if m:HasProperty('_EmissionColor')then m:SetColor('_EmissionColor',U.Color.black)end\n  mats[i]=m;")
s=s.replace("2,anchored('head',{0,0,0}))", "2,anchored('head',{0,.35,0}))")
s=s.replace("1,anchored('head',{0,0,0}),.72)","1,anchored('head',{0,.17,0}),.72)")
s=s.replace("3,anchored('head',{0,0,0}),.72)","3,anchored('head',{0,.17,0}),.72)")
s=s.replace("{.12,.23,.24,0,-.015},{.25,.17,.19,0,-.025},{.31,.055,.07,0,-.05},{.315,.002,.002,0,-.075}","{.12,.29,.29,0,-.015},{.32,.24,.25,0,-.025},{.46,.08,.10,0,-.05},{.49,.002,.002,0,-.075}")
p.write_text(s)
p=D/'restyle_ui.py';s=p.read_text().replace('toggle.image.sprite=getRing();toggleLabel','toggle.image.sprite=getRing();toggle.image.color=U.Color.white;toggleLabel').replace('btn.image.sprite=getRing();txt.fontSize','btn.image.sprite=getRing();btn.image.color=U.Color.white;txt.fontSize');p.write_text(s)
