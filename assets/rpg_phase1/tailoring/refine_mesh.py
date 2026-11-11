from pathlib import Path
D=Path(__file__).parent
p=D/'garments.lua';s=p.read_text().replace('local m=U.Material(seed)','local m=U.Material(U.Shader.Find("Universal Render Pipeline/Lit"))')
s=s.replace("  mats[i]=m;", "  if m:HasProperty('_Cull')then m:SetFloat('_Cull',0)end\n  m:DisableKeyword('_EMISSION')\n  mats[i]=m;")
s=s.replace('typeof(CS.System.Int32),#faces*6','typeof(CS.System.Int32),#faces*3')
s=s.replace('local k=(i-1)*6;t[k]=f[1]-1;t[k+1]=f[2]-1;t[k+2]=f[3]-1;t[k+3]=f[3]-1;t[k+4]=f[2]-1;t[k+5]=f[1]-1','local k=(i-1)*3;t[k]=f[1]-1;t[k+1]=f[2]-1;t[k+2]=f[3]-1')
s=s.replace(" if kind=='mage'then\n  local hat", " if kind=='mage'then\n  rings('RobeBodice',{{-.18,.155,.145},{-.06,.18,.17},{.10,.19,.17},{.14,.13,.12}},2,anchored('chest',{0,0,0}))\n  rings('LongRobe',{{.035,.17,.16},{-.18,.19,.17},{-.43,.23,.2},{-.55,.245,.21}},2,anchored('hips',{0,0,0},true))\n  rings('RobeBorder',{{-.51,.24,.205},{-.55,.246,.212}},1,anchored('hips',{0,0,0},true))\n  for _,side in ipairs({'L','R'})do rings('BellSleeve'..side,{{-.11,.10,.10},{-.06,.11,.11},{.02,.095,.095},{.07,.075,.075}},1,{kind='forearm',side=side})end\n  local hat")
s=s.replace(" elseif kind=='ranged'then\n  local hood", " elseif kind=='ranged'then\n  rings('LeatherTunic',{{-.17,.16,.15},{-.05,.17,.16},{.09,.18,.17},{.13,.12,.11}},2,anchored('chest',{0,0,0}))\n  rings('LeatherBelt',{{-.055,.171,.161},{-.09,.171,.161}},3,anchored('hips',{0,.04,0}))\n  local hood")
p.write_text(s)
