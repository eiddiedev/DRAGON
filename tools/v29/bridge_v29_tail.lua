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

---------------------------------------------------------------- v30：游玩时左下角的水域诊断小字（提审端没有日志，靠截图带回信息）
-- 内容：能否游泳 / 是否在游泳 / 身上碰到几个触发器及名字 / 脚下踩的是什么 / 高度
function UI.buildPlayDiag()
 if UI.playDiag or not UI.P_hud then return end
 local fonts=UnityEngine.Resources.FindObjectsOfTypeAll(typeof(UnityEngine.Font));local font=nil
 for i=0,fonts.Length-1 do if fonts[i].name=='NotoSansSC-Medium'then font=fonts[i];break end end
 if not font and fonts.Length>0 then font=fonts[0]end
 if not font then return end
 local go=UnityEngine.GameObject('PlayDiag');go.transform:SetParent(UI.P_hud.rt,false)
 local t=go:AddComponent(typeof(UnityEngine.UI.Text));t.font=font;t.fontSize=16;t.color=UnityEngine.Color(1,1,1,.36)
 t.alignment=UnityEngine.TextAnchor.LowerLeft;t.raycastTarget=false;t.horizontalOverflow=UnityEngine.HorizontalWrapMode.Overflow
 local rt=t.rectTransform;rt.anchorMin=UI.V2(0,0);rt.anchorMax=UI.V2(0,0);rt.pivot=UI.V2(0,0);rt.sizeDelta=UI.V2(1500,26);rt.anchoredPosition=UI.V2(28,8)
 UI.playDiag=t
end
function UI.updatePlayDiag(actor)
 if not UI.playDiag then return end
 local now=Time.realtimeSinceStartup
 if now<(UI.playDiagNext or 0)then return end;UI.playDiagNext=now+1
 local p=actor.position
 local can,swim='?','?'
 pcall(function()can=tostring(actor:CanSwim())end);pcall(function()swim=tostring(actor:IsSwimming())end)
 local trig,names=0,{}
 pcall(function()
  local hits=UnityEngine.Physics.OverlapSphere(Vector3(p.x,p.y+.8,p.z),1.2,-1,UnityEngine.QueryTriggerInteraction.Collide)
  for i=0,hits.Length-1 do local c=hits[i]
   if c.isTrigger then trig=trig+1;if #names<2 then names[#names+1]=c.name end end
  end
 end)
 local ground='-'
 pcall(function()
  local hits=UnityEngine.Physics.RaycastAll(Vector3(p.x,p.y+1,p.z),Vector3(0,-1,0),6,-1,UnityEngine.QueryTriggerInteraction.Ignore)
  local best=1e9
  for i=0,hits.Length-1 do local h=hits[i]
   if h.distance<best and not h.transform:IsChildOf(actor.gameObject.transform)then best=h.distance;ground=h.collider.name end
  end
 end)
 UI.playDiag.text=string.format('v30  水:can=%s swim=%s  触发器:%d %s  脚下:%s  y=%.1f',can,swim,trig,table.concat(names,'/'),ground,p.y)
end
UI.v30Update=Update
function Update()
 UI.v30Update()
 if UI.state=='play'then
  local a=DouyinActorService.GetLocalActor()
  if a then pcall(UI.buildPlayDiag);pcall(UI.updatePlayDiag,a)end
 end
end

---------------------------------------------------------------- v31：环境光兜底 + 地形细节距离
-- 提审端场景环境到得晚：开头抓到的「夜间基准」可能是黑的环境光、没有主光。白天混合时就按黑的算，背光处发黑。
-- 这里在世界铺开后核对基准，不对就换成作者场景的实际值（本地预览量到的），并重新套用。
UI.envGuard={checks=0}
function UI.guardEnv()
 local G=UI.envGuard;local now=Time.realtimeSinceStartup
 if not night or not envReady or now<(G.nextAt or 0)or G.checks>=40 then return end
 G.nextAt=now+3;G.checks=G.checks+1
 local changed=false
 local a=night.ambient
 if not G.ambientWas then G.ambientWas=string.format('%.2f',a.r+a.g+a.b)end
 if a.r+a.g+a.b<.6 then night.ambient=Color(.4196,.4196,.6196,1);changed=true end
 if not night.ambientIntensity or night.ambientIntensity<.6 then night.ambientIntensity=1;changed=true end
 local f=night.fog
 if f.r+f.g+f.b<.04 then night.fog=Color(.1098,.0706,.2392,1);changed=true end
 if not night.fogEnd or night.fogEnd<400 then night.fogEnd=1500;changed=true end
 if sunLight==nil then
  pcall(function()
   local lights=UnityEngine.Object.FindObjectsOfType(typeof(CS.UnityEngine.Light))
   for i=0,lights.Length-1 do local l=lights[i]
    if sunLight==nil and tostring(l.type):find('Directional')then sunLight=l;night.lightColor=Color(.6588,.7608,1,1);night.lightIntensity=.95;changed=true;G.sunLate=true end
   end
  end)
 end
 pcall(function()
  if tostring(RenderSettings.ambientMode)~=tostring(UnityEngine.Rendering.AmbientMode.Flat)then G.modeWas=tostring(RenderSettings.ambientMode);RenderSettings.ambientMode=UnityEngine.Rendering.AmbientMode.Flat;changed=true end
 end)
 if changed or G.checks==1 or not G.settled and UI.settle.done then
  if UI.settle.done then G.settled=true end
  G.fixed=(G.fixed or 0)+(changed and 1 or 0)
  pcall(applyEnv,blend*blend*(3-2*blend))
 end
end
function UI.applyTerrainQuality()
 local Q=UI.texQuality;local now=Time.realtimeSinceStartup
 if now<(Q.terrainNext or 0)or(Q.terrainChecks or 0)>=10 then return end
 Q.terrainNext=now+3;Q.terrainChecks=(Q.terrainChecks or 0)+1
 pcall(function()
  local t=UnityEngine.Terrain.activeTerrain;if not t then return end
  if not Q.baseWas then Q.baseWas=t.basemapDistance;Q.errWas=t.heightmapPixelError end
  if t.basemapDistance<1000 then t.basemapDistance=1000 end
  if t.heightmapPixelError>5 then t.heightmapPixelError=5 end
  if t.detailObjectDistance<250 then t.detailObjectDistance=250 end
 end)
 pcall(function()local q=UnityEngine.QualitySettings;if not Q.levelWas then Q.levelWas=q.GetQualityLevel();Q.lodWas2=q.lodBias end;if q.lodBias<2 then q.lodBias=2 end end)
end
-- 诊断行补充（标题页第二行）：环境光基准、主光、地形贴图距离、画质档
function UI.updateDiagLine2()
 if not UI.diagLabel then return end
 local G,Q=UI.envGuard,UI.texQuality
 UI.diagLabel.text=UI.diagLabel.text..string.format('  光:%s%s%s  地形:%s/%s  档:%s lod:%s',
  tostring(G.ambientWas),G.sunLate and'+迟到主光'or(sunLight and''or'+无主光'),G.modeWas and('+'..G.modeWas)or'',
  tostring(Q.baseWas),tostring(Q.errWas),tostring(Q.levelWas),tostring(Q.lodWas2))
end
UI.v31Update=Update
function Update()
 UI.v31Update()
 pcall(UI.guardEnv);pcall(UI.applyTerrainQuality)
 if UI.state=='title'and UI.diagLabel and Time.realtimeSinceStartup>=(UI.diag2Next or 0)then
  UI.diag2Next=Time.realtimeSinceStartup+1;UI.diagNext=0;pcall(UI.updateDiagLine);pcall(UI.updateDiagLine2)
 end
 if UI.state=='play'and UI.playDiag and Time.realtimeSinceStartup>=(UI.play2Next or 0)then
  UI.play2Next=Time.realtimeSinceStartup+1
  pcall(function()
   local h=UnityEngine.PlayerPrefs.GetString('dr_diag_horse','-');local s=UnityEngine.PlayerPrefs.GetString('dr_diag_sheep','-')
   local base=UI.playDiag.text;local cut=string.find(base,'  马:',1,true);if cut then base=string.sub(base,1,cut-1)end
   UI.playDiag.text=string.gsub(base,'^v30','v31')..'  马:'..h..'  羊:'..s
  end)
 end
end
