const U=CS.UnityEngine;const tree=U.GameObject.Find('pl_tree_18');
const ts=tree.GetComponentsInChildren(puer.$typeof(U.Transform),true);let leaf=null;
for(let i=0;i<ts.Length;i++){const t=ts.get_Item(i);if(t.name==='Leaves')leaf=t;}
const home=leaf.localPosition;
const before=leaf.localRotation;
await lua.eval('-248776:a87ebe50-812d-4151-a056-727a118aecbd','local a=DouyinActorService.GetLocalActor();a:Teleport(UnityEngine.Vector3(130,39.043991,48));return true');
let drift=0;for(let i=0;i<8;i++){await awaitFrames(15);drift=Math.max(drift,U.Vector3.Distance(home,leaf.localPosition));}
const resting=leaf.localRotation;
const b=leaf.gameObject.GetComponentInChildren(puer.$typeof(U.Collider),true).bounds;
const x=b.center.x+1.2,y=b.center.y-1,z=b.center.z+1.2;
let maxAngle=0;
try{
 await lua.eval('-248776:a87ebe50-812d-4151-a056-727a118aecbd',`DouyinActorService.GetLocalActor():Teleport(UnityEngine.Vector3(${x},${y},${z}));return true`);
 for(let i=0;i<8;i++){await awaitFrames(5);maxAngle=Math.max(maxAngle,U.Quaternion.Angle(resting,leaf.localRotation));drift=Math.max(drift,U.Vector3.Distance(home,leaf.localPosition));}
}finally{await lua.eval('-248776:a87ebe50-812d-4151-a056-727a118aecbd','DouyinActorService.GetLocalActor():Teleport(UnityEngine.Vector3(130,39.043991,48));return true');}
await awaitFrames(120);
return {maxAnchorDrift:drift,contactAngle:maxAngle,returnErrorDegrees:U.Quaternion.Angle(resting,leaf.localRotation)};
