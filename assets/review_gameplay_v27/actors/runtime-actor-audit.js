// Read-only native runtime probe. Does not force animations or teleport actors.
const U=CS.UnityEngine;
const names=['tripo_horse',...Array.from({length:9},(_,i)=>`sheep_${i}`),'dragon_v8_live','dragon_peak'];
const rows=[];
function vec(v){return v?{x:v.x,y:v.y,z:v.z}:null;}
function snap(ts){const a=[];for(let i=0;i<ts.Length;i++){let t=ts.get_Item(i);a.push([t.localPosition.x,t.localPosition.y,t.localPosition.z,t.localRotation.x,t.localRotation.y,t.localRotation.z,t.localRotation.w]);}return a;}
const captured=[];
for (const name of names) {
 const go=U.GameObject.Find(name);
 if (!go){rows.push({name,found:false});continue;}
 const an=go.GetComponent(puer.$typeof(CS.ModularAnim.Runtime.UGCAnimator)) || go.GetComponentInChildren(puer.$typeof(CS.ModularAnim.Runtime.UGCAnimator),true);
 const rb=go.GetComponent(puer.$typeof(U.Rigidbody));
 const rs=go.GetComponentsInChildren(puer.$typeof(U.Renderer),true);
 const renderers=[];
 for(let i=0;i<rs.Length;i++){const r=rs.get_Item(i);renderers.push({name:r.name,enabled:r.enabled,active:r.gameObject.activeInHierarchy,center:vec(r.bounds.center),size:vec(r.bounds.size)});}
 const row={name,found:true,position:vec(go.transform.position),animator:!!an,controllerReady:!!(an && an.enabled && an.Controller),rigidbody:rb?{kinematic:rb.isKinematic,gravity:rb.useGravity,position:vec(rb.position)}:null,renderers};
 rows.push(row);
 if(an){const ts=go.GetComponentsInChildren(puer.$typeof(U.Transform),true);captured.push({row,ts,before:snap(ts)});}
}
await awaitFrames(12);
for(const r of captured){const after=snap(r.ts);r.row.changedTransforms=r.before.filter((a,i)=>a.some((v,j)=>Math.abs(v-after[i][j])>0.00001)).length;}
return {build:'v27-actor-audit',rows};
