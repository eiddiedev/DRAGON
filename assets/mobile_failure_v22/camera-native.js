const bindings=await lua.bindings();const b=bindings.find(x=>x.referenceName==='dragon_world_bridge.lua');
if(!b)return {error:'bridge not found'};
function cameras(){const a=CS.UnityEngine.Camera.allCameras;let names=[];for(let i=0;i<a.Length;i++)names.push(a.get_Item(i).gameObject.name);return names;}
const before=cameras();const start=await lua.eval(b.bindingKey,'ScreenFx(.2,1,2,false);return GetMobileRenderStatus()');
await awaitFrames(5);const during=cameras();const active=await lua.eval(b.bindingKey,'return GetMobileRenderStatus()');
await awaitFrames(55);const after=cameras();const ended=await lua.eval(b.bindingKey,'return GetMobileRenderStatus()');
return {before,start,during,active,after,ended};
