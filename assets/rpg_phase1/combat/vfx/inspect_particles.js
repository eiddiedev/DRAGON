await awaitFrames(12);
const ps=CS.UnityEngine.Resources.FindObjectsOfTypeAll(puer.$typeof(CS.UnityEngine.ParticleSystem));const out=[];
for(let i=0;i<ps.Length;i++){const p=ps.get_Item(i);if(!p.gameObject.activeInHierarchy)continue;const r=p.GetComponent(puer.$typeof(CS.UnityEngine.ParticleSystemRenderer));out.push({name:p.name,parent:p.transform.parent?.name,n:p.particleCount,playing:p.isPlaying,position:[p.transform.position.x,p.transform.position.y,p.transform.position.z],enabled:r?.enabled,material:r?.sharedMaterial?.name,shader:r?.sharedMaterial?.shader?.name,bounds:r?[r.bounds.size.x,r.bounds.size.y,r.bounds.size.z]:null});}
return out;
