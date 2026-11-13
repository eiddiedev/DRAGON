---------------------------------------------------------------- v29：提审端（流式加载）加固
-- 运行时天空层：场景里的漩涡 / 月亮节点没被加载进来时，用随脚本带的贴图建一张朝南的大方片顶上
UI.skyFallback={made={},specs={sky_swirl_a={128,235,455,560},sky_swirl_b={128,235,440,470},sky_swirl_c={128,235,425,330},sky_moon2={30,225,480,150}}}
function RuntimeSkyLayer(name)
 local F=UI.skyFallback
 if F.made[name]then return F.made[name]end
 local spec=F.specs[name];local b64=UI.SKYB and UI.SKYB[name]
 if not spec or not b64 then return nil end
 local t=UnityEngine.Texture2D(2,2,UnityEngine.TextureFormat.RGBA32,true)
 if not t:LoadImage(CS.System.Convert.FromBase64String(b64),true)then UnityEngine.Object.Destroy(t);error('sky image '..name)end
 t.wrapMode=UnityEngine.TextureWrapMode.Clamp;t.name='RuntimeSky_'..name
 UI.SKYB[name]=nil
 local shader=UnityEngine.Shader.Find('Universal Render Pipeline/Unlit')
 local urp=shader~=nil
 if not shader then shader=UnityEngine.Shader.Find('Sprites/Default')or UnityEngine.Shader.Find('Unlit/Transparent')end
 if not shader then error('no sky shader')end
 local m=UnityEngine.Material(shader)
 if urp then
  m:SetTexture('_BaseMap',t);m:SetFloat('_Surface',1);m:SetFloat('_Blend',0)
  m:SetFloat('_SrcBlend',5);m:SetFloat('_DstBlend',10);m:SetFloat('_ZWrite',0);m:SetFloat('_Cull',0)
  m:EnableKeyword('_SURFACE_TYPE_TRANSPARENT')
 else m.mainTexture=t end
 m.renderQueue=({sky_moon2=2991,sky_swirl_a=2992,sky_swirl_b=2993,sky_swirl_c=2994})[name]or 3000
 local go=UnityEngine.GameObject.CreatePrimitive(UnityEngine.PrimitiveType.Quad);go.name=name
 local col=go:GetComponent(typeof(UnityEngine.Collider));if col then col.enabled=false;UnityEngine.Object.Destroy(col)end
 local r=go:GetComponent(typeof(UnityEngine.Renderer));r.sharedMaterial=m
 r.shadowCastingMode=UnityEngine.Rendering.ShadowCastingMode.Off;r.receiveShadows=false
 go.transform.position=Vector3(spec[1],spec[2],spec[3]);go.transform.localScale=Vector3(spec[4],spec[4],1)
 F.made[name]=go;F.count=(F.count or 0)+1
 report('runtime sky layer '..name)
 return go
end
-- 运行时层已经顶上之后，原节点才被加载进来：把后来的那个关掉，免得叠两层
function UI.skyDedupe()
 local F=UI.skyFallback;local now=Time.realtimeSinceStartup
 if not F.count or now<(F.nextAt or 0)then return end;F.nextAt=now+3
 for name,made in pairs(F.made)do
  local go=UnityEngine.GameObject.Find(name)
  if go and go~=made then go:SetActive(false);F.hidden=(F.hidden or 0)+1 end
 end
end

-- 开场门控：世界里的渲染物体数量连续 2.5 秒不再变化、地形和天空都就绪，才算世界铺开；最多等 30 秒
UI.settle={count=-1,nextAt=0}
function UI.worldSettled()
 local W=UI.settle;if W.done then return true end
 local now=Time.realtimeSinceStartup
 W.from=W.from or now
 if now-W.from>30 then W.done=true;W.why='timeout';W.took=now-W.from;return true end
 if now>=W.nextAt then
  W.nextAt=now+.5
  local ok,n=pcall(function()return UnityEngine.Object.FindObjectsOfType(typeof(UnityEngine.Renderer)).Length end)
  if not ok then W.done=true;W.why='count failed';return true end
  if n~=W.count then W.count=n;W.since=now end
 end
 if UnityEngine.Terrain.activeTerrain~=nil and skyReady and W.count>=150 and W.since and now-W.since>=2.5 then
  W.done=true;W.why='stable';W.took=now-W.from;return true
 end
 return false
end

-- 画质：只往高调。贴图用最高一级 mip，开各向异性过滤，LOD 切换推远
UI.texQuality={}
function UI.applyTextureQuality()
 local Q=UI.texQuality;if Q.done then return end;Q.done=true
 local q=UnityEngine.QualitySettings
 pcall(function()Q.mipWas=q.globalTextureMipmapLimit;if q.globalTextureMipmapLimit>0 then q.globalTextureMipmapLimit=0 end end)
 if Q.mipWas==nil then pcall(function()Q.mipWas=q.masterTextureLimit;if q.masterTextureLimit>0 then q.masterTextureLimit=0 end end)end
 pcall(function()Q.anisoWas=tostring(q.anisotropicFiltering);q.anisotropicFiltering=UnityEngine.AnisotropicFiltering.ForceEnable end)
 pcall(function()Q.lodWas=q.lodBias;if q.lodBias<1.5 then q.lodBias=1.5 end end)
end

-- 标题页左下角一行很淡的小字：版本和加载情况。提审端看不到日志，截图里带上它就能知道走的是哪条路
function UI.buildDiagLine()
 if UI.diagLabel or not UI.P_title then return end
 local fonts=UnityEngine.Resources.FindObjectsOfTypeAll(typeof(UnityEngine.Font));local font=nil
 for i=0,fonts.Length-1 do if fonts[i].name=='NotoSansSC-Medium'then font=fonts[i];break end end
 if not font and fonts.Length>0 then font=fonts[0]end
 if not font then return end
 local go=UnityEngine.GameObject('BuildDiag');go.transform:SetParent(UI.P_title.rt,false)
 local t=go:AddComponent(typeof(UnityEngine.UI.Text));t.font=font;t.fontSize=18;t.color=UnityEngine.Color(1,1,1,.38)
 t.alignment=UnityEngine.TextAnchor.LowerLeft;t.raycastTarget=false;t.horizontalOverflow=UnityEngine.HorizontalWrapMode.Overflow
 local rt=t.rectTransform;rt.anchorMin=UI.V2(0,0);rt.anchorMax=UI.V2(0,0);rt.pivot=UI.V2(0,0);rt.sizeDelta=UI.V2(1400,30);rt.anchoredPosition=UI.V2(28,14)
 UI.diagLabel=t
end
function UI.updateDiagLine()
 if not UI.diagLabel then return end
 local now=Time.realtimeSinceStartup
 if now<(UI.diagNext or 0)then return end;UI.diagNext=now+1
 local W,F,Q,B=UI.settle,UI.skyFallback,UI.texQuality,UI.bundled
 local n=0;for _,v in pairs(B.status or{})do if v=='bundled'then n=n+1 end end
 UI.diagLabel.text=string.format('v29  世界:%s %.0fs/%d  天空:%s  备份图:%d  mip:%s  aniso:%s',
  tostring(W.why or '-'),W.took or 0,W.count or 0,(F.count and('补'..F.count)or '原')..(SWIRL_LAYERS.missing and SWIRL_LAYERS.missing>0 and('缺'..SWIRL_LAYERS.missing)or ''),
  n,tostring(Q.mipWas),tostring(Q.anisoWas))
end

UI.v29Update=Update
function Update()
 UI.v29Update()
 pcall(UI.applyTextureQuality)
 pcall(UI.skyDedupe)
 if UI.state=='title'then pcall(UI.buildDiagLine);pcall(UI.updateDiagLine)end
end
function GetV29Diagnostics()
 return {build='v29-streaming-hardening',settle=UI.settle,skyRuntime=UI.skyFallback.count or 0,skyMissing=SWIRL_LAYERS.missing,skyError=SWIRL_LAYERS.fallbackError,texQuality=UI.texQuality}
end
