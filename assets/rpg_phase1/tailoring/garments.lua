-- Tailored accessories use curved meshes; original limb-following armor remains.
local function tailor(entry)
 local U=UnityEngine;local V=Vector3
 local kind=entry.className
 local palette=kind=='mage' and {{.34,.16,.48},{.065,.045,.09},{.72,.70,.80}} or kind=='ranged' and {{.14,.23,.085},{.24,.13,.065},{.66,.46,.20}} or {{.22,.27,.34},{.055,.085,.16},{.66,.58,.35}}
 entry.tailoredMeshes={};entry.tailoredMaterials={};entry.extraSpecs={}
 local renderers=entry.clone:GetComponentsInChildren(typeof(U.Renderer),true)
 local seed=renderers[0].sharedMaterial
 local mats={}
 for i,c in ipairs(palette)do
  local m=U.Material(U.Shader.Find("Universal Render Pipeline/Lit"))
  for _,key in ipairs({'_MainTex','_BaseMap','_BaseTex'})do if m:HasProperty(key)then m:SetTexture(key,nil)end end
  for _,key in ipairs({'_Color','_BaseColor'})do if m:HasProperty(key)then m:SetColor(key,U.Color(c[1],c[2],c[3],1))end end
  if m:HasProperty('_EmissionPower')then m:SetFloat('_EmissionPower',0)end
  if m:HasProperty('_Metallic')then m:SetFloat('_Metallic',i==3 and .65 or(kind=='melee'and i==1 and .7 or 0))end
  if m:HasProperty('_Smoothness')then m:SetFloat('_Smoothness',i==3 and .45 or .23)end
  for _,key in ipairs({'_UseVertexColor','_RimPower','_FresnelInt','_UseTriplanarSample'})do if m:HasProperty(key)then m:SetFloat(key,0)end end
  if m:HasProperty('_ColorPower')then m:SetFloat('_ColorPower',1)end
  for _,key in ipairs({'_Normalmap','_ORM','_EmissionMask','_EmissionTex'})do if m:HasProperty(key)then m:SetTexture(key,nil)end end
  if m:HasProperty('_EmissionColor')then m:SetColor('_EmissionColor',U.Color.black)end
  if m:HasProperty('_Cull')then m:SetFloat('_Cull',0)end
  m:DisableKeyword('_EMISSION')
  m:EnableKeyword('_ENVIRONMENTREFLECTIONS_OFF');m:EnableKeyword('_SPECULARHIGHLIGHTS_OFF')
  if m:HasProperty('_EnvironmentReflections')then m:SetFloat('_EnvironmentReflections',0)end
  if m:HasProperty('_SpecularHighlights')then m:SetFloat('_SpecularHighlights',0)end
  mats[i]=m;entry.tailoredMaterials[#entry.tailoredMaterials+1]=m
 end
 -- Preserve trim assignment; recolour existing shell materials by their brightness.
 for i=0,renderers.Length-1 do
  local r=renderers[i];local original=r.sharedMaterial;local color=original.color
  local luminance=(color.r+color.g+color.b)/3
  r.sharedMaterial=mats[luminance>.65 and 3 or(luminance<.15 and 2 or 1)]
 end
 local function mesh(name,verts,faces,material,spec)
  local go=U.GameObject(name);go.transform:SetParent(entry.clone.transform,false)
  local v=CS.System.Array.CreateInstance(typeof(V),#verts)
  local t=CS.System.Array.CreateInstance(typeof(CS.System.Int32),#faces*3)
  for i,p in ipairs(verts)do v[i-1]=V(p[1],p[2],p[3])end
  for i,f in ipairs(faces)do local k=(i-1)*3;t[k]=f[1]-1;t[k+1]=f[3]-1;t[k+2]=f[2]-1 end
  local m=U.Mesh();m.vertices=v;m.triangles=t;m:RecalculateNormals();m:RecalculateBounds()
  go:AddComponent(typeof(U.MeshFilter)).sharedMesh=m;go:AddComponent(typeof(U.MeshRenderer)).sharedMaterial=mats[material]
  entry.tailoredMeshes[#entry.tailoredMeshes+1]=m
  if spec then spec.name=name;entry.extraSpecs[#entry.extraSpecs+1]=spec end
  return go
 end
 local function rings(name,levels,mat,spec,opening)
  local v,f={},{};local n=32
  for k,p in ipairs(levels)do for j=0,n do
   local a=(opening or 0)+(2*math.pi-2*(opening or 0))*j/n
   v[#v+1]={math.sin(a)*p[2]+(p[4]or 0),p[1]+(p[6]or 0)*math.cos(a),math.cos(a)*p[3]+(p[5]or 0)}
   if k>1 and j<n then local q=(k-2)*(n+1)+j+1;f[#f+1]={q,q+n+1,q+1};f[#f+1]={q+1,q+n+1,q+n+2}end
  end end
  return mesh(name,v,f,mat,spec)
 end
 local function anchored(parent,offset,hem)
  return {kind=hem and 'hem'or'torsoOffset',parent=parent,offset=offset,basePitch=0,forwardLimit=7,backLimit=18,rollLimit=8,phase=.8}
 end
 local function star(name,x,y,z,r,mat,parent)
  local v={{x,y,z}};local f={}
  for j=0,7 do local a=j*math.pi/4;local rad=j%2==0 and r or r*.28;v[#v+1]={x+math.sin(a)*rad,y+math.cos(a)*rad,z}end
  for j=1,8 do f[#f+1]={1,j+1,j%8+2}end
  local g=mesh(name,v,f,mat,nil);g.transform:SetParent(parent,false)
 end
 if kind=='mage'then
  rings('RobeBodice',{{-.18,.155,.145},{-.06,.18,.17},{.10,.19,.17},{.14,.13,.12}},2,anchored('chest',{0,0,0}))
  rings('LongRobe',{{.035,.17,.16},{-.18,.19,.17},{-.43,.23,.2},{-.55,.245,.21}},2,anchored('hips',{0,0,0},true))
  rings('RobeBorder',{{-.51,.24,.205},{-.55,.246,.212}},1,anchored('hips',{0,0,0},true))
  for _,side in ipairs({'L','R'})do rings('BellSleeve'..side,{{-.11,.10,.10},{-.06,.11,.11},{.02,.095,.095},{.07,.075,.075}},1,{kind='forearm',side=side})end
  local hat=rings('WizardHat',{{.14,.38,.33,0,0,.028},{.15,.35,.305},{.17,.17,.16},{.29,.125,.125},{.42,.075,.08,-.025},{.51,.025,.035,-.10},{.50,.002,.002,-.17}},2,anchored('head',{0,.35,0}))
  local band=rings('HatRibbon',{{.175,.158,.153},{.218,.146,.143}},1,nil);band.transform:SetParent(hat.transform,false)
  for i=-2,2 do star('HatStar'..i,i*.043,.195,.15- math.abs(i)*.009,.009,3,hat.transform)end
  rings('HighCollar',{{-.04,.17,.14},{.03,.20,.18},{.075,.21,.18}},1,anchored('chest',{0,0,0}),.55)
  for _,name in ipairs({'HoodBack','CloakSideL','CloakSideR'})do local p=entry.clone.transform:Find(name);if p then p.gameObject:SetActive(false)end end
 elseif kind=='ranged'then
  rings('LeatherTunic',{{-.17,.16,.15},{-.05,.17,.16},{.09,.18,.17},{.13,.12,.11}},2,anchored('chest',{0,0,0}))
  rings('LeatherBelt',{{-.055,.171,.161},{-.09,.171,.161}},3,anchored('hips',{0,.04,0}))
  local hood=rings('ForestHood',{{-.15,.19,.19,0,-.035},{-.035,.225,.235,0,-.02},{.12,.29,.29,0,-.015},{.32,.24,.25,0,-.025},{.46,.08,.10,0,-.05},{.49,.002,.002,0,-.075}},1,anchored('head',{0,.17,0}),.72)
  rings('HoodSeam',{{-.15,.194,.194,0,-.035},{-.14,.195,.195,0,-.035}},3,anchored('head',{0,.17,0}),.72)
  rings('LeafMantle',{{.07,.16,.13},{-.04,.25,.17},{-.13,.275,.19}},1,anchored('chest',{0,0,0}),.58)
 end
 if kind=='mage'then
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
  -- Long, split cloth panels are anchored at the upper back and respond to movement.
  for side=-1,1,2 do
   local v,f={},{};local cols,rows=7,10
   for r=0,rows do for c=0,cols do local u=c/cols;local t=r/rows
    v[#v+1]={side*(.008+u*(.15+t*.07)),-t*.56,-.02-t*.08-.017*math.sin(u*math.pi*4)}
    if r>0 and c<cols then local q=(r-1)*(cols+1)+c+1;f[#f+1]={q,q+cols+1,q+1};f[#f+1]={q+1,q+cols+1,q+cols+2}end
   end end
   local cloak=mesh('TailoredCape'..side,v,f,1,anchored('chest',{0,.055,-.15},true))
   for i=1,5 do star('CapeEmblem'..i,side*(.04+i*.024),-.055-i*.075,-.03-i*.014,.012,3,cloak.transform)end
  end
 else
  rings('Gorget',{{-.035,.15,.12},{.035,.14,.12}},3,anchored('chest',{0,.045,0}))
  for _,side in ipairs({'L','R'})do
   rings('LayeredPauldrons'..side,{{-.055,.105,.10},{-.012,.125,.115},{.035,.11,.1},{.065,.07,.07}},1,{kind='upperArm',side=side})
   rings('GoldPauldronRim'..side,{{-.054,.108,.103},{-.041,.113,.108}},3,{kind='upperArm',side=side})
  end
 end
end
