const U=CS.UnityEngine, all=await lua.bindings(),out={};
for(const [name,code] of [
 ['dragon_world_bridge.lua','return {loading=GetLoadingDiagnostics(),altar=GetAltarVisualDiagnostics(),camera=GetRoamingCameraDiagnostics(),quality=GetMobileRenderStatus(),glow=GetHolyGlowDiagnostics()}'],
 ['dragon_combat.lua','return {status=GetStatus(),visuals=GetShadowVisualDiagnostics()}'],
 ['dragon_exploration.lua','return {status=GetStatus(),lore=GetLoreTargets()}']]){
 const b=all.find(x=>x.referenceName===name);try{out[name]=b?await lua.eval(b.bindingKey,code):'missing';}catch(e){out[name]={error:String(e)}}
}
const tr=U.Object.FindObjectsOfType(puer.$typeof(U.Transform),true),roots=[];
for(let i=0;i<tr.Length;i++){const t=tr.get_Item(i);if(t.name==='windmill_rotor_pivot'||/^(beam_|runeg_|cl_|sheep_)/.test(t.name))roots.push({id:t.GetInstanceID(),name:t.name,active:t.gameObject.activeInHierarchy,pos:[t.position.x,t.position.y,t.position.z],rot:[t.localRotation.x,t.localRotation.y,t.localRotation.z,t.localRotation.w]});}
out.objects=roots;await awaitFrames(12);out.windmillAfter=roots.filter(x=>x.name==='windmill_rotor_pivot').map(x=>{for(let i=0;i<tr.Length;i++){let t=tr.get_Item(i);if(t.GetInstanceID()===x.id)return {id:x.id,rot:[t.localRotation.x,t.localRotation.y,t.localRotation.z,t.localRotation.w]};}});return out;
