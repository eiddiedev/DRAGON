const U=CS.UnityEngine;const out=[];
for(const name of ['tripo_horse','sheep_0','tripo_witch','flying_carpet','dragon_v8_live','golden_geometry_150','ShadowSpiritSource']){
 const go=U.GameObject.Find(name);if(!go){out.push({name,missing:true});continue;}
 const rs=go.GetComponentsInChildren(puer.$typeof(U.Renderer),true);let meshes=[];
 for(let i=0;i<rs.Length;i++){const r=rs.get_Item(i);meshes.push({name:r.name,enabled:r.enabled,size:{x:r.bounds.size.x,y:r.bounds.size.y,z:r.bounds.size.z},shader:r.sharedMaterial?.shader?.name});}
 const a=go.GetComponent(puer.$typeof(CS.ModularAnim.Runtime.UGCAnimator));
 out.push({name,active:go.activeInHierarchy,position:{x:go.transform.position.x,y:go.transform.position.y,z:go.transform.position.z},animator:!!a,controller:!!a?.Controller,meshes});
}
const mats=[];const rs=U.Object.FindObjectsOfType(puer.$typeof(U.Renderer));
for(let i=0;i<rs.Length;i++){const r=rs.get_Item(i);if(!/薰衣|Lavender|billboard|Plant|plant|花/.test(r.name))continue;const m=r.sharedMaterial;if(!m)continue;const props={};for(const p of ['_BaseColor','_Color','_BottomColor','_TopColor','_Cutoff','_AlphaClip','_EmissionPower'])if(m.HasProperty(p)){try{props[p]=/Color/.test(p)?m.GetColor(p).ToString():m.GetFloat(p)}catch{}}
 if(mats.length<12)mats.push({name:r.name,shader:m.shader.name,props,texture:m.mainTexture?.name});}
return {models:out,plants:mats};
