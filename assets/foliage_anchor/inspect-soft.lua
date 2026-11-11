local UE=CS.UnityEngine
local actor=DouyinActorService.GetLocalActor()
local best,bestDistance=nil,1e9
local count,anchored,solid,triggers=0,0,0,0
for i=0,172 do
 local g=UE.GameObject.Find('pl_tree_'..i)
 if g then
  local ts=g:GetComponentsInChildren(typeof(UE.Transform),true)
  for j=0,ts.Length-1 do
   local t=ts[j]
   if t.name=='Leaves' then
    local rb=t.gameObject:GetComponent(typeof(UE.Rigidbody))
    local col=t.gameObject:GetComponentInChildren(typeof(UE.Collider),true)
    count=count+1
    if col and col.enabled and col.isTrigger then triggers=triggers+1 end
    if rb and rb.isKinematic then anchored=anchored+1 end
    if col and col.enabled and not col.isTrigger then solid=solid+1 end
    local dist=UE.Vector3.Distance(t.position,actor.position)
    if rb and rb.isKinematic and dist<bestDistance then bestDistance=dist;best={tree=g.name,x=t.position.x,y=t.position.y,z=t.position.z,id=t.gameObject:GetInstanceID()} end
   end
  end
 end
end
return {count=count,anchored=anchored,solid=solid,triggers=triggers,nearest=best,actor={x=actor.position.x,y=actor.position.y,z=actor.position.z}}
