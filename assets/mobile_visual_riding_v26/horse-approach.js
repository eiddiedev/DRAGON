const U=CS.UnityEngine;const bs=await lua.bindings();const h=bs.find(b=>b.referenceName==='horse_seat_v1.lua');const b=bs.find(b=>b.referenceName==='dragon_world_bridge.lua');
const out={loading:await lua.eval(b.bindingKey,'return GetLoadingDiagnostics()'),horseBinding:h};
const g=U.GameObject.Find('B同马去动画保留骨骼');const a=CS.DouyinActorService.GetLocalActor();
if(g&&a){a.Teleport(new U.Vector3(g.transform.position.x,g.transform.position.y,g.transform.position.z+2),U.Quaternion.identity);out.horse=String(g.transform.position);out.actor=String(a.position);}
return out;
