const U=CS.UnityEngine;
const tree=U.GameObject.Find('pl_tree_18');
const ts=tree.GetComponentsInChildren(puer.$typeof(U.Transform),true);
let leaf=null;
for(let i=0;i<ts.Length;i++){const t=ts.get_Item(i);if(t.name==='Leaves'){leaf=t;break;}}
if(!leaf)throw Error('Missing leaf');
const col=leaf.gameObject.GetComponentInChildren(puer.$typeof(U.Collider),true);
const rb=leaf.gameObject.GetComponent(puer.$typeof(U.Rigidbody));
const home=leaf.localPosition;const b=col.bounds;
let ball=null;
try{
 ball=U.GameObject.CreatePrimitive(U.PrimitiveType.Sphere);ball.name='__foliage_collision_test';
 ball.transform.localScale=new U.Vector3(.4,.4,.4);
 ball.transform.position=new U.Vector3(b.max.x+1,b.center.y,b.center.z);
 const body=ball.AddComponent(puer.$typeof(U.Rigidbody));body.useGravity=false;body.mass=1;
 body.velocity=new U.Vector3(-6,0,0);
 const start=ball.transform.position.x;let maxDrift=0;let samples=[];
 for(let i=0;i<8;i++){await awaitFrames(15);maxDrift=Math.max(maxDrift,U.Vector3.Distance(home,leaf.localPosition));samples.push({x:ball.transform.position.x,speed:body.velocity.magnitude});}
 return {kinematic:rb.isKinematic,solid:col.enabled&&!col.isTrigger,maxAnchorDrift:maxDrift,start,samples};
}finally{if(ball)U.Object.Destroy(ball);}
