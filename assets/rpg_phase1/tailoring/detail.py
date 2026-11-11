from pathlib import Path
p=Path(__file__).parent/'garments.lua';s=p.read_text()
s=s.replace("{{.19,.12,.32},{.045,.042,.065},{.68,.67,.77}}", "{{.34,.16,.48},{.065,.045,.09},{.72,.70,.80}}")
s=s.replace("{{.14,.19,.10},{.19,.115,.068},{.60,.43,.18}}", "{{.14,.23,.085},{.24,.13,.065},{.66,.46,.20}}")
s=s.replace("{{.14,.255,.23,0,0,.018},{.15,.235,.215},{.17,.155,.15}","{{.14,.38,.33,0,0,.028},{.15,.35,.305},{.17,.17,.16}")
s=s.replace("{{-.05,.15,.125},{.08,.19,.17},{.14,.19,.155}}", "{{-.04,.17,.14},{.03,.20,.18},{.075,.21,.18}}")
needle=" if kind~='melee'then\n"
new=""" if kind=='mage'then
  -- Split embroidered front stole, with an actual silver border and star motifs.
  for side=-1,1,2 do
   local v={{side*.014,.04,.173},{side*.10,.04,.176},{side*.12,-.48,.215},{side*.075,-.54,.22},{side*.014,-.48,.215}}
   local g=mesh('SilverStoleEdge'..side,v,{{1,2,3},{1,3,4},{1,4,5}},3,anchored('hips',{0,0,0},true))
   local inset={{side*.024,.025,.178},{side*.088,.025,.181},{side*.105,-.465,.221},{side*.075,-.515,.226},{side*.024,-.465,.221}}
   local q=mesh('PurpleStole'..side,inset,{{1,2,3},{1,3,4},{1,4,5}},1,nil);q.transform:SetParent(g.transform,false)
   for i=1,4 do star('StoleStar'..i,side*.065,-i*.10,.19+i*.01,.012,3,g.transform)end
  end
  rings('SilverRobeHem',{{-.54,.25,.217},{-.558,.25,.217}},3,anchored('hips',{0,0,0},true))
 elseif kind=='melee'then
  local cuirass=rings('SteelCuirass',{{-.17,.16,.145},{-.07,.185,.185},{.06,.20,.18},{.13,.13,.12}},1,anchored('chest',{0,0,0}))
  star('ArmourCrest',0,-.015,.19,.055,3,cuirass.transform)
  rings('WaistPlate',{{.03,.18,.16},{-.035,.185,.17},{-.07,.19,.17}},1,anchored('hips',{0,0,0}))
 end
 if kind~='melee'then
"""
s=s.replace(needle,new,1)
p.write_text(s)
