const U=CS.UnityEngine;let out=[];
for(let f=0;f<20;f++){
 await awaitFrames(1);const a=CS.DouyinActorService.GetLocalActor();const ps=U.Resources.FindObjectsOfTypeAll(puer.$typeof(U.ParticleSystem));
 for(let i=0;i<ps.Length;i++){const p=ps.get_Item(i);if(!p.gameObject.activeInHierarchy||!p.isPlaying||!p.particleCount)continue;const r=p.GetComponent(puer.$typeof(U.ParticleSystemRenderer));let mesh=null;try{mesh=r.mesh?{name:r.mesh.name,bounds:r.mesh.bounds.ToString()}:null;}catch(e){}
 out.push({f,name:p.name,count:p.particleCount,p:p.transform.position.ToString(),actor:a.position.ToString(),rot:p.transform.rotation.eulerAngles.ToString(),bounds:r.bounds.ToString(),mesh});}}
return out;
