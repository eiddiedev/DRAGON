const U=CS.UnityEngine, a=CS.DouyinActorService.GetLocalActor(), b=(await lua.bindings()).find(x=>x.referenceName==='water_diagnostics.lua');
if(!a||!b)throw new Error('actor or diagnostic binding missing');
const out=[];
for(const point of [{name:'river',p:[97.715,33,136.268]},{name:'bank',p:[132.5,40,49]},{name:'sea',p:[245,29,50]}]){
 a.Teleport(new U.Vector3(...point.p),U.Quaternion.identity);await awaitFrames(100);
 out.push({name:point.name,diagnostic:await lua.eval(b.bindingKey,'return GetWaterDiagnostics()')});
}
return out;
