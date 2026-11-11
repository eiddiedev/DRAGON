local u=CS.UnityEngine
local result={}
for _,name in ipairs({'mush','mush_17'}) do
 local go=u.GameObject.Find(name);local rs=go:GetComponentsInChildren(typeof(u.Renderer));local b=rs[0].bounds
 for i=1,rs.Length-1 do b:Encapsulate(rs[i].bounds) end
 local best=nil
 for ix=0,8 do for iz=0,8 do
  local x=b.min.x+(b.max.x-b.min.x)*(.1+.8*ix/8);local z=b.min.z+(b.max.z-b.min.z)*(.1+.8*iz/8)
  local hits=u.Physics.RaycastAll(u.Vector3(x,b.max.y+1,z),u.Vector3.down,10,-1,u.QueryTriggerInteraction.Ignore)
  for k=0,hits.Length-1 do local h=hits[k];if (h.collider.transform==go.transform or h.collider.transform:IsChildOf(go.transform)) and h.normal.y>.7 and (not best or h.point.y>best.y) then best={x=h.point.x,y=h.point.y,z=h.point.z} end end
 end end
 result[name]=best or false
end
return result
