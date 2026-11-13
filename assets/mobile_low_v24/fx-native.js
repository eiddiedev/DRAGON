const bindings=await lua.bindings();const b=bindings.find(x=>x.referenceName==='dragon_fx.lua');
const U=CS.UnityEngine;function sample(){const p=U.Object.FindObjectsOfType(puer.$typeof(U.ParticleSystem));let live=0,max=0;for(let i=0;i<p.Length;i++){live+=p.get_Item(i).particleCount;max+=p.get_Item(i).main.maxParticles;}return {systems:p.Length,particles:live,maxParticles:max,cameras:U.Camera.allCamerasCount};}
const samples=[{phase:'before',...sample()}];
for(const kind of ['melee','mage','ranged']){
 for(const action of ['attack','skill1','skill2','skill3']){
 await lua.eval(b.bindingKey,`local a=CS.DouyinActorService.GetLocalActor();Play('${kind}','${action}',a.position+CS.UnityEngine.Vector3(0,.6,0),CS.UnityEngine.Vector3.forward);return GetStatus()`);
 await awaitFrames(5);samples.push({phase:kind+':'+action,...sample()});await awaitFrames(20);
 }
}
await awaitFrames(60);samples.push({phase:'settled',...sample()});return {samples,fx:await lua.eval(b.bindingKey,'return GetStatus()')};
