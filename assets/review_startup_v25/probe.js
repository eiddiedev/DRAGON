const bs=await lua.bindings();const b=bs.find(x=>x.referenceName==='dragon_world_bridge.lua');
if(!b)return {bindings:bs};
const U=CS.UnityEngine;const absent=[];
for(const n of ['ui_title','ui_book','ui_pages1','ui_pages2','ui_pages3','ui_atlas','tripo_witch','dragon_v8_live','flying_carpet'])if(!U.GameObject.Find(n))absent.push(n);
return {loading:await lua.eval(b.bindingKey,'return GetLoadingDiagnostics()'),ground:await lua.eval(b.bindingKey,'return GetGroundCoverDiagnostics()'),absentSceneObjects:absent,explicitSources:await lua.eval(b.bindingKey,"local UI;for i=1,20 do local n,v=debug.getupvalue(GetLoadingDiagnostics,i);if n=='UI'then UI=v;break end end;local out={};for _,n in ipairs(UI.TEX_NAMES)do local t=UI.tex and UI.tex[n];out[n]=t and {width=t.width,height=t.height}or false end;out.ground=UI.groundCover.texture and UI.groundCover.texture.width or 0;return out")};
