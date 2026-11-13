const b=(await lua.bindings()).find(x=>x.referenceName==='horse_seat_v1.lua');const samples=[];
for(let i=0;i<20;i++){
 await lua.eval(b.bindingKey,'self.transform.position=self.transform.position+UnityEngine.Vector3(.2,0,0);return true');
 await awaitFrames(2);
 samples.push(await lua.eval(b.bindingKey,'local a=DouyinActorService.GetLocalActor();local p=self.transform.position;local r=a.position;return {horse={p.x,p.y,p.z},rider={r.x,r.y,r.z},mounted=a:IsSitting(),diag=GetRidingDiagnostics()}'));
}
return samples;
