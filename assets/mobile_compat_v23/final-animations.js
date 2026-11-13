const U=CS.UnityEngine;const all=U.Object.FindObjectsOfType(puer.$typeof(CS.ModularAnim.Runtime.UGCAnimator));const out=[];
for(const [name,clips] of [['tripo_horse',['Idle','Run']],['sheep_0',['Idle','Walk']],['tripo_witch',['idle']],['flying_carpet',['ripple']],['dragon_v8_live',['perch','takeoff','fly','land']],['ShadowSpiritSource',['Idle','FloatMove']]]){
 let an=null;for(let i=0;i<all.Length;i++){const v=all.get_Item(i);if(v.gameObject.name===name){an=v;break;}}
 if(!an){out.push({name,missing:true});continue;}
 const ts=an.GetComponentsInChildren(puer.$typeof(U.Transform),true);const snap=()=>{let a=[];for(let i=0;i<ts.Length;i++){const t=ts.get_Item(i);a.push([t.localPosition.x,t.localPosition.y,t.localPosition.z,t.localRotation.x,t.localRotation.y,t.localRotation.z,t.localRotation.w]);}return a;};
 for(const clip of clips){const played=an.Play(clip);await awaitFrames(3);const a=snap();await awaitFrames(8);const b=snap();out.push({name,clip,played,changedBones:a.filter((v,i)=>v.some((x,j)=>Math.abs(x-b[i][j])>.00001)).length});}
 an.Play(clips[0]);
}
return out;
