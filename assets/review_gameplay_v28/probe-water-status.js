const bs=await lua.bindings(); const out={bindings:bs.filter(x=>/water_diagnostics|dragon_world_bridge/.test(x.referenceName)).map(x=>({name:x.referenceName,path:x.targetPath}))};
for (const [name,code] of [['water_diagnostics.lua','return GetWaterDiagnostics()'],['dragon_world_bridge.lua','return {state=GetExplorationState(),loading=GetLoadingDiagnostics()}']]){
 const b=bs.find(x=>x.referenceName===name);try{out[name]=b?await lua.eval(b.bindingKey,code):'missing';}catch(e){out[name]={error:String(e)}}
}
return out;
