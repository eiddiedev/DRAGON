const U=CS.UnityEngine,Q=U.QualitySettings;
const bindings=await lua.bindings();const b=bindings.find(x=>x.referenceName==='dragon_world_bridge.lua');
const cams=[];for(let i=0;i<U.Camera.allCameras.Length;i++){let c=U.Camera.allCameras.get_Item(i);cams.push({name:c.name,hdr:c.allowHDR,msaa:c.allowMSAA});}
return {quality:{fps:U.Application.targetFrameRate,aa:Q.antiAliasing,shadows:Q.shadows,shadowDistance:Q.shadowDistance,renderScale:(Q.renderPipeline||CS.UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline).renderScale,cams},bridge:b?await lua.eval(b.bindingKey,'return {loading=GetLoadingDiagnostics(),render=GetMobileRenderStatus()}'):null};
