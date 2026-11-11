from pathlib import Path
D=Path(__file__).resolve().parent
s=(D/'outfits-before.lua').read_text()
s=s.replace('local function collectParts(entry)',(D/'garments.lua').read_text()+'\nlocal function collectParts(entry)')
s=s.replace('  local specList = PART_SPECS[entry.className]','  local specList = {}\n  for _,v in ipairs(PART_SPECS[entry.className]or{})do specList[#specList+1]=v end\n  for _,v in ipairs(entry.extraSpecs or{})do specList[#specList+1]=v end')
s=s.replace('  collectParts(entry)\n  return true','  tailor(entry)\n  collectParts(entry)\n  return true')
s=s.replace('      if spec.parent == "chest" then reference = chest end','      if spec.parent == "chest" then reference = chest elseif spec.parent == "head"then reference=head end')
s=s.replace('  entry.clone = nil\n  entry.posed=false','  for _,m in ipairs(entry.tailoredMeshes or{})do UnityEngine.Object.Destroy(m)end\n  for _,m in ipairs(entry.tailoredMaterials or{})do UnityEngine.Object.Destroy(m)end\n  entry.tailoredMeshes=nil;entry.tailoredMaterials=nil;entry.extraSpecs=nil\n  entry.clone = nil\n  entry.posed=false')
(D.parent/'dragon_outfits.lua').write_text(s)
