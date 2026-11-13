-- mobile-v21: bounded discovery, shared authored materials, no generated mesh colliders.
function UI.discoverVegetation(f,limit,setup)
 local now=Time.realtimeSinceStartup
 f.started=f.started or now;f.seen=f.seen or {};f.next=f.next or 0
 if now-f.started>30 then
  if not f.ready then f.ready=true;report('mobile-v21 vegetation '..#f.items..'/'..#f.names..' ready; missing '..(#f.names-#f.items))end
  return
 end
 if now<(f.retryAt or 0)then return end
 for _=1,limit do
  f.next=f.next+1
  if f.next>#f.names then f.next=0;f.retryAt=now+1;break end
  local name=f.names[f.next]
  if not f.seen[name]then
   local go=GameObject.Find(name)
   if go then
    local ok,value=pcall(setup,go)
    if ok and value then f.seen[name]=true;f.items[#f.items+1]=value
    elseif not ok and not f.error then f.error=tostring(value);report('mobile-v21 vegetation error '..f.error)end
   end
  end
 end
end
function UI.updateFoliage(actor)
 local f=UI.foliage
 UI.discoverVegetation(f,2,function(go)
  local ts=go:GetComponentsInChildren(typeof(UnityEngine.Transform),true)
  local leaves=nil
  for i=0,ts.Length-1 do if ts[i].name=='Leaves'then leaves=ts[i];break end end
  if not leaves then return nil end
  -- Leaf proximity is mathematical. Trunk collision is untouched.
  local cols=leaves.gameObject:GetComponentsInChildren(typeof(UnityEngine.Collider),true)
  for i=0,cols.Length-1 do cols[i].enabled=false end
  local joints=leaves.gameObject:GetComponents(typeof(UnityEngine.ConfigurableJoint))
  for i=0,joints.Length-1 do UnityEngine.Object.Destroy(joints[i])end
  local rb=leaves.gameObject:GetComponent(typeof(UnityEngine.Rigidbody))
  if rb then rb.isKinematic=true;rb.detectCollisions=false end
  local rs=leaves.gameObject:GetComponentsInChildren(typeof(UnityEngine.Renderer),true)
  for i=0,rs.Length-1 do rs[i].shadowCastingMode=UnityEngine.Rendering.ShadowCastingMode.Off end
  -- Pivot around the authored branch attachment. Position never changes; max 2 degrees.
  return {t=leaves,rot=leaves.localRotation,home=leaves.localPosition,phase=go.transform.position.x*.32,x=0,z=0,nextAt=0}
 end)
 local now=Time.time
 if now<(f.updateAt or 0)then return end;f.updateAt=now+1/15
 local p=actor.position
 local select=now>=(f.selectAt or 0);if select then f.selectAt=now+.2 end
 for _,v in ipairs(f.items)do
  if select then local d=v.t.position-p;v.d2=d.x*d.x+d.z*d.z end
  if now>=v.nextAt then
   local d2=v.d2 or 1e9;v.nextAt=now+(d2<144 and 1/15 or .25)
   local tx,tz=0,0
   if d2<1600 then
    local wind=math.sin(now*.8+v.phase)*.35
    tx=wind;tz=wind*.4
    if d2<9 then
     local d=v.t:InverseTransformDirection(v.t.position-p)
     local k=math.max(0,1-math.sqrt(d2)/3)
     tx=tx+d.z*math.min(1,k)*.65;tz=tz-d.x*math.min(1,k)*.65
    end
   end
   v.x=v.x+(math.max(-2,math.min(2,tx))-v.x)*.35
   v.z=v.z+(math.max(-2,math.min(2,tz))-v.z)*.35
   v.t.localPosition=v.home;v.t.localRotation=v.rot*Quaternion.Euler(v.x,0,v.z)
  end
 end
end
function UI.updateReeds(actor)
 local f=UI.reeds
 UI.discoverVegetation(f,2,function(go)
  local ts=go:GetComponentsInChildren(typeof(UnityEngine.Transform),true)
  local lower,upper
  for j=0,ts.Length-1 do
   if ts[j].name=='reed_lower'then lower=ts[j]end
   if ts[j].name=='reed_upper'then upper=ts[j]end
  end
  if not lower or not upper then return nil end
  local an=go:GetComponentInChildren(typeof(UnityEngine.Animation),true)
  if an then an:Stop();an.enabled=false end
  local cols=go:GetComponentsInChildren(typeof(UnityEngine.Collider),true)
  for j=0,cols.Length-1 do cols[j].enabled=false end
  local rs=go:GetComponentsInChildren(typeof(UnityEngine.Renderer),true)
  f.materials=f.materials or {}
  local tone=(tonumber(go.name:match('(%d+)$'))or 0)%4
  for j=0,rs.Length-1 do
   rs[j].shadowCastingMode=UnityEngine.Rendering.ShadowCastingMode.Off
   local src=rs[j].sharedMaterial
   if src then
    local tex=src.mainTexture;local key=src.shader.name..':'..tostring(tex and tex:GetInstanceID()or 0)..':'..tone
    if not f.materials[key]then
     local m=UnityEngine.Material(src)
     local c=UnityEngine.Color(.58+tone*.035,.43+tone*.03,.21+tone*.023,1)
     for _,property in ipairs({'_BaseColor','_Color'})do if m:HasProperty(property)then m:SetColor(property,c)end end
     f.materials[key]=m
    end
    rs[j].sharedMaterial=f.materials[key]
   end
  end
  return {root=go.transform,lo=lower,hi=upper,lr=lower.localRotation,hr=upper.localRotation,x=0,z=0,phase=go.transform.position.x*.32+go.transform.position.z*.22,nextAt=0}
 end)
 local now=Time.time
 if now<(f.updateAt or 0)then return end;f.updateAt=now+1/15
 local p=actor.position;local select=now>=(f.selectAt or 0);if select then f.selectAt=now+.2 end
 for _,v in ipairs(f.items)do
  local rp=v.root.position
  if select then local dx,dz=rp.x-p.x,rp.z-p.z;v.d2=dx*dx+dz*dz end
  local d2=v.d2 or 1e9
  if now>=v.nextAt then
   v.nextAt=now+(d2<144 and 1/15 or .25)
   local tx,tz,wind=0,0,0
   if d2<1600 then
    wind=math.sin(now*1.1+v.phase)*2.2+math.sin(now*.43+v.phase*.45)*1.1
    if d2<4 and math.abs(rp.y-p.y)<2.5 then
     local dist=math.sqrt(d2);local dir=v.root:InverseTransformDirection(Vector3((rp.x-p.x)/math.max(.05,dist),0,(rp.z-p.z)/math.max(.05,dist)))
     local k=1-math.min(1,dist/2);tx=dir.z*32*k;tz=-dir.x*32*k
    end
   end
   v.x=v.x+(tx-v.x)*.35;v.z=v.z+(tz-v.z)*.35
   v.lo.localRotation=v.lr*Quaternion.Euler(v.x+wind,0,v.z+wind*.42)
   v.hi.localRotation=v.hr*Quaternion.Euler(v.x*.65+wind*1.4,0,v.z*.65+wind*.6)
  end
 end
end
