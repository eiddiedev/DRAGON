---@id 6329c644-9169-4c74-b1c2-6cf72ca3dae4
---@referenceName dragon_fx.lua
-- 有体积的短时魔法网格；固定池复用，不堆积粒子或逐帧创建材质。
---@displayName 龙眠武器立体特效
local U=CS.UnityEngine
local V=U.Vector3
local Scope=require("official.core.runtime_scope")
local scope=Scope.from(self)
local pool={}
local palette={melee=U.Color(1,.59,.12,1),mage=U.Color(.29,.5,1,1),ranged=U.Color(.24,1,.73,1)}
local function tube(points,radius)
 local sides=6;local count=#points
 local vs=CS.System.Array.CreateInstance(typeof(V),count*sides)
 local tris=CS.System.Array.CreateInstance(typeof(CS.System.Int32),(count-1)*sides*6)
 for i,p in ipairs(points)do
  local nextP=points[math.min(i+1,count)];local prevP=points[math.max(1,i-1)]
  local direction=V(nextP.x-prevP.x,nextP.y-prevP.y,nextP.z-prevP.z).normalized
  local ref=math.abs(direction.y)>.9 and V.right or V.up
  local right=V.Cross(direction,ref).normalized;local up=V.Cross(right,direction).normalized
  for j=0,sides-1 do
   local a=j*math.pi*2/sides;local x,y=math.cos(a)*radius,math.sin(a)*radius
   vs[(i-1)*sides+j]=V(p.x+right.x*x+up.x*y,p.y+right.y*x+up.y*y,p.z+right.z*x+up.z*y)
   if i<count then
    local a0=(i-1)*sides+j;local b0=(i-1)*sides+(j+1)%sides;local c0=a0+sides;local d0=b0+sides
    local k=((i-1)*sides+j)*6
    tris[k]=a0;tris[k+1]=c0;tris[k+2]=b0;tris[k+3]=b0;tris[k+4]=c0;tris[k+5]=d0
   end
  end
 end
 local mesh=U.Mesh();mesh.vertices=vs;mesh.triangles=tris;mesh:RecalculateNormals();mesh:RecalculateBounds();return mesh
end
local function init()
 if #pool>0 then return true end
 local source=scope and scope:GetGameObjectByPath("DragonStaff")
 local renderer=source and source:GetComponentInChildren(typeof(U.Renderer),true)
 if not renderer or not renderer.sharedMaterial then return false end
 for i=1,20 do
  local go=U.GameObject("DragonSpell_"..i);go.transform:SetParent(self.transform,false)
  local mf=go:AddComponent(typeof(U.MeshFilter));local mr=go:AddComponent(typeof(U.MeshRenderer))
  local mat=U.Material(renderer.sharedMaterial)
  for _,key in ipairs({"_BaseTex","_MainTex","_BaseMap"})do if mat:HasProperty(key)then mat:SetTexture(key,nil)end end
  mat:EnableKeyword("_EMISSION");mr.sharedMaterial=mat;go:SetActive(false)
  pool[i]={go=go,mf=mf,mat=mat,untilTime=-1}
 end
 return true
end
local function acquire(points,radius,kind,origin,rotation,life,velocity)
 if not init()then return end
 local now=U.Time.time;local item=nil
 for _,v in ipairs(pool)do if v.untilTime<=now then item=v;break end end
 if not item then return end -- bounded visual budget; combat result never depends on this pool.
 if item.mesh then U.Object.Destroy(item.mesh)end
 item.mesh=tube(points,radius);item.mf.sharedMesh=item.mesh
 item.color=palette[kind];item.start=now;item.untilTime=now+life;item.life=life;item.velocity=velocity
 item.origin=origin;item.go.transform.position=origin;item.go.transform.rotation=rotation;item.go.transform.localScale=V.one
 for _,key in ipairs({"_Color","_BaseColor"})do if item.mat:HasProperty(key)then item.mat:SetColor(key,item.color)end end
 item.go:SetActive(true)
end
function Play(kind,action,origin,direction)
 local rotation=U.Quaternion.LookRotation(direction,V.up)
 if kind=="melee"then
  local ring=action=="skill";local points={};local count=ring and 40 or 24
  for i=0,count do
   local a=(ring and i/count*2*math.pi or -.95+i/count*1.9)
   points[#points+1]=V(math.sin(a)*(ring and 1.3 or 2),ring and .1 or .55+math.sin(i/count*math.pi)*.25,math.cos(a)*(ring and 1.3 or 2))
  end
  acquire(points,ring and .065 or .09,kind,origin,rotation,ring and .9 or .32,nil)
 elseif kind=="mage"then
  local points={};for i=0,36 do local a=i/36*math.pi*4;points[#points+1]=V(math.cos(a)*.2,math.sin(a)*.2, i/36*.9)end
  acquire(points,action=="skill"and .075 or .045,kind,origin,rotation,.65,V(direction.x*16,direction.y*16,direction.z*16))
  if action=="skill"then
   for axis=1,2 do local ring={};for i=0,32 do local a=i/32*2*math.pi;ring[#ring+1]=V(math.cos(a)*.8,axis==1 and math.sin(a)*.8 or 0,axis==2 and math.sin(a)*.8 or 0)end
    acquire(ring,.045,kind,origin,rotation,.55,nil)
   end
  end
 else
  local count=action=="skill"and 5 or 1
  for i=1,count do
   local angle=(i-(count+1)/2)*4
   local rot=U.Quaternion.AngleAxis(angle,V.up)*rotation
   local d=rot*V.forward
   acquire({V(0,0,-1.1),V(0,0,.12),V(.08,0,-.04),V(0,0,.12),V(-.08,0,-.04)},.025,kind,origin,rot,.65,V(d.x*24,d.y*24,d.z*24))
  end
 end
end
function Update()
 local now=U.Time.time
 for _,v in ipairs(pool)do
  if v.go.activeSelf then
   if now>=v.untilTime then v.go:SetActive(false)
   else
    local age=now-v.start;local energy=3*(1-age/v.life)
    if v.mat:HasProperty("_EmissionPower")then v.mat:SetFloat("_EmissionPower",energy)end
    if v.mat:HasProperty("_EmissionColor")then v.mat:SetColor("_EmissionColor",U.Color(v.color.r*energy,v.color.g*energy,v.color.b*energy,1))end
    if v.velocity then v.go.transform.position=V(v.origin.x+v.velocity.x*age,v.origin.y+v.velocity.y*age,v.origin.z+v.velocity.z*age)end
   end
  end
 end
end
function Clear()
 for _,v in ipairs(pool)do v.go:SetActive(false);v.untilTime=-1 end
end
function OnDestroy()
 for _,v in ipairs(pool)do if v.mesh then U.Object.Destroy(v.mesh)end;U.Object.Destroy(v.mat);U.Object.Destroy(v.go)end;pool={}
end
