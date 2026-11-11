const actor=CS.DouyinActorService.GetLocalActor();
const U=CS.UnityEngine;
const cases={"mush": {"x": 82, "y": 51.55838394165, "z": 105.9348526001}, "mush_17": {"x": 80.000007629395, "y": 47.321971893311, "z": 102.64873504639}};
const results={};
for(const name of ['mush_17','mush']) {
 const p=cases[name];actor.Teleport(new U.Vector3(p.x,p.y+.45,p.z));
 const go=U.GameObject.Find(name);const renderer=go.GetComponentInChildren(puer.$typeof(U.Renderer));
 const source=go.GetComponent(puer.$typeof(U.AudioSource));const samples=[];
 for(let i=0;i<160;i++) {await awaitFrames(3);samples.push({t:U.Time.time,y:actor.position.y,grounded:actor.IsGrounded(),sound:source.isPlaying,meshHeight:renderer.bounds.size.y});}
 results[name]={capY:p.y,samples};
}
return results;
