local U=UnityEngine
local g=U.GameObject.Find('pl_tree_18');local ts=g:GetComponentsInChildren(typeof(U.Transform),true)
for i=0,ts.Length-1 do
 local t=ts[i]
 if t.name=='Leaves' then
  local c=t.gameObject:GetComponentInChildren(typeof(U.Collider),true);local b=c.bounds
  local a=DouyinActorService.GetLocalActor()
  a:Teleport(U.Vector3(b.center.x+1.2,b.center.y-1,b.center.z+1.2))
  return {distance=U.Vector3.Distance(c:ClosestPoint(a.position+U.Vector3(0,1,0)),a.position+U.Vector3(0,1,0)),trigger=c.isTrigger}
 end
end
