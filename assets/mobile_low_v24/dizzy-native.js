const bs=await lua.bindings(),e=bs.find(b=>b.referenceName==='dragon_exploration.lua'),w=bs.find(b=>b.referenceName==='dragon_world_bridge.lua');
const U=CS.UnityEngine;const before=U.Camera.main.fieldOfView;const records=[];
for(const k of ['dizzy','speed','dizzy','speed']){
 await lua.eval(e.bindingKey,`DebugOpen('buff','${k}');return true`);
 let min=999,max=-1;
 for(let i=0;i<40;i++){await awaitFrames(1);const f=U.Camera.main.fieldOfView;min=Math.min(min,f);max=Math.max(max,f);}
 records.push({kind:k,min,max,dizzy:await lua.eval(w.bindingKey,'return IsDizzy()')});
}
await lua.eval(e.bindingKey,'ClearPotion();return true');await awaitFrames(4);
return {before,records,after:U.Camera.main.fieldOfView,dizzy:await lua.eval(w.bindingKey,'return IsDizzy()')};
