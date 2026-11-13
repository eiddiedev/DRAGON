const U=CS.UnityEngine;const g=U.GameObject.Find('B同马去动画保留骨骼');const a=CS.DouyinActorService.GetLocalActor();const bs=await lua.bindings();const b=bs.find(x=>x.referenceName==='horse_seat_v1.lua');
const before=await lua.eval(b.bindingKey,'return GetRidingDiagnostics()');const samples=[];
if(before.mounted){
 const p=g.transform.position;
 for(let i=1;i<=20;i++){
  g.transform.position=new U.Vector3(p.x+i*.2,p.y,p.z);
  await awaitFrames(2);
  samples.push({horse:[g.transform.position.x,g.transform.position.y,g.transform.position.z],rider:[a.position.x,a.position.y,a.position.z],parent:a.gameObject.transform.parent?.name});
 }
}
return {before,samples,after:await lua.eval(b.bindingKey,'return GetRidingDiagnostics()')};
