-- review-v27: each successfully spawned model is owned before optional setup.
-- An unavailable animation component or health UI must never orphan a clone.
local shadowVisualStats={created=0,destroyed=0,setupFailures=0,healthFailures=0,animationFailures=0,lastError=nil}
local function destroyShadowVisual(v)
 if not v then return end
 if v.go then
  local go=v.go;v.go=nil
  pcall(function()go:SetActive(false)end)
  local ok=pcall(Spawn.destroy,go)
  if not ok then pcall(U.Object.Destroy,go) end
  shadowVisualStats.destroyed=shadowVisualStats.destroyed+1
 end
 for _,m in ipairs(v.materials or {})do pcall(U.Object.Destroy,m)end
 v.materials={}
end
local function buildShadowHealth(v)
 local bar=U.GameObject('Heartfire');v.bar=bar;bar:SetActive(false)
 local rt=bar:AddComponent(typeof(U.RectTransform));rt:SetParent(v.go.transform,false)
 rt.sizeDelta=U.Vector2(80,10);rt.localScale=V(.01,.01,.01)
 local canvas=bar:AddComponent(typeof(U.Canvas));canvas.renderMode=U.RenderMode.WorldSpace
 local track=U.GameObject('HealthTrack');local tr=track:AddComponent(typeof(U.RectTransform));tr:SetParent(rt,false)
 tr.sizeDelta=U.Vector2(80,10)
 local trackImage=track:AddComponent(typeof(U.UI.Image));trackImage.color=U.Color(.04,.025,.06,.9);trackImage.raycastTarget=false
 local fill=U.GameObject('HealthFill');local fr=fill:AddComponent(typeof(U.RectTransform));fr:SetParent(tr,false)
 fr.anchorMin=U.Vector2(0,.5);fr.anchorMax=U.Vector2(0,.5);fr.pivot=U.Vector2(0,.5)
 fr.anchoredPosition=U.Vector2(2,0);fr.sizeDelta=U.Vector2(76,6)
 local fillImage=fill:AddComponent(typeof(U.UI.Image));fillImage.color=U.Color(.8,.2,.5,1);fillImage.raycastTarget=false
 v.healthFill=fr;bar:SetActive(true)
end
local function prepareShadowVisual(v,e)
 local go=v.go;v.stage='model';go.name='BattleShadow_'..e.id;go:SetActive(false)
 -- Preserve the existing encounter's analytical hit/collision rules.
 local cols=go:GetComponentsInChildren(typeof(U.Collider),true)
 for i=0,cols.Length-1 do cols[i].enabled=false end
 v.stage='materials'
 local rs=go:GetComponentsInChildren(typeof(U.Renderer),true)
 for i=0,rs.Length-1 do local ms=rs[i].materials
  for j=0,ms.Length-1 do if ms[j]then v.materials[#v.materials+1]=ms[j]end end
 end
 v.stage='bones'
 local ts=go:GetComponentsInChildren(typeof(U.Transform),true)
 for bi=0,ts.Length-1 do local t=ts[bi]
  if t.name=='Chest'or t.name=='Head'or t.name=='UpperArm_L'or t.name=='UpperArm_R'or t.name=='Forearm_L'or t.name=='Forearm_R'then v.bones[t.name]={t=t}end
 end
 -- These are optional visuals. Neither can invalidate the registered model.
 local okHealth,healthError=pcall(buildShadowHealth,v)
 if not okHealth then
  if v.bar then U.Object.Destroy(v.bar);v.bar=nil;v.healthFill=nil end
  shadowVisualStats.healthFailures=shadowVisualStats.healthFailures+1
  shadowVisualStats.lastError='health: '..tostring(healthError)
 end
 local okAnim,anim=pcall(function()return go:GetComponentInChildren(typeof(CS.ModularAnim.Runtime.UGCAnimator),true)end)
 if okAnim then v.animator=anim else
  shadowVisualStats.animationFailures=shadowVisualStats.animationFailures+1
  shadowVisualStats.lastError='animation lookup: '..tostring(anim)
 end
 v.stage='ready'
end
local function updateShadowVisual(v,e)
 v.go:SetActive(e.hp>0 and active())
 if e.hp<=0 then return end
 local desired=V(e.x,state.y+.15+math.sin(state.t*2+e.id)*.04,e.z)
 local before=v.go.transform.position;v.go.transform.position=V.Lerp(before,desired,math.min(1,U.Time.deltaTime*14))
 if before.y<state.y-10 then v.go.transform.position=desired end
 -- Preserve the existing authored facing correction and per-stage scale.
 local d=V(e.faceX or 0,0,e.faceZ or 1)
 if d.sqrMagnitude>.001 then v.go.transform.rotation=Q.LookRotation(d,V.up)*Q.Euler(0,90,0)end
 local scale=e.boss and 1.75 or(e.elite and 1.25 or .95);v.go.transform.localScale=V.one*scale
 if v.bar then
  v.bar.transform.position=desired+V(0,scale*1.35,0)
  local cam=CS.DouyinCameraService.GetCamera()
  if cam then v.bar.transform.rotation=cam.transform.rotation end
  local fraction=math.max(0,math.min(1,e.hp/math.max(1,e.maxHP or 1)))
  v.healthFill.sizeDelta=U.Vector2(76*fraction,6)
 end
 v.enemy=e
 local desiredAnim=e.state=='chase'and 'FloatMove'or 'Idle'
 if v.animator and v.anim~=desiredAnim then
  local ok,played=pcall(function()return v.animator.Controller and v.animator:Play(desiredAnim)end)
  if ok then if played then v.anim=desiredAnim end
  else
   shadowVisualStats.animationFailures=shadowVisualStats.animationFailures+1
   shadowVisualStats.lastError='animation playback: '..tostring(played);v.animator=nil
  end
 end
 for _,mat in ipairs(v.materials)do if mat:HasProperty('_EmissionPower')then mat:SetFloat('_EmissionPower',e.hit>state.t and 2 or(e.state=='windup'and 1 or .08))end end
end
local function clearVisuals()
 for _,v in pairs(visuals)do destroyShadowVisual(v)end
 visuals={};shadowReady.spawnAttempts={}
end
function GetShadowVisualDiagnostics()
 local owned,visible=0,0
 for _,v in pairs(visuals)do if v.go then owned=owned+1;if v.go.activeInHierarchy then visible=visible+1 end end end
 local expected=0;if state and active()then for _,e in ipairs(state.enemies)do if e.hp>0 then expected=expected+1 end end end
 return {build='review-v27-atomic-shadow',expected=expected,owned=owned,visible=visible,created=shadowVisualStats.created,destroyed=shadowVisualStats.destroyed,setupFailures=shadowVisualStats.setupFailures,healthFailures=shadowVisualStats.healthFailures,animationFailures=shadowVisualStats.animationFailures,error=shadowVisualStats.lastError}
end
local function syncVisuals()
 if not state then return end
 local source=shadowSource();if not source then return end
 source.transform.localPosition=V(0,-500,0)
 for _,e in ipairs(state.enemies)do
  local v=visuals[e.id]
  if not v and e.hp>0 then
   local retry=shadowReady.spawnAttempts[e.id]or{count=0,nextAt=0};shadowReady.spawnAttempts[e.id]=retry
   local go=nil
   if retry.count<10 and U.Time.time>=retry.nextAt then
    retry.count=retry.count+1;retry.nextAt=U.Time.time+.5
    local ok,result=pcall(Spawn.spawn,self,'ShadowSpiritSource',{networked=false,position=V(e.x,state.y+.15,e.z)})
    if ok then go=result else shadowReady.error=tostring(result);print('[review-v27] shadow spawn '..shadowReady.error)end
   end
   if go then
    v={go=go,materials={},bones={},stage='spawned'}
    visuals[e.id]=v -- own immediately, before any optional component/material work
    shadowVisualStats.created=shadowVisualStats.created+1
    local ok,err=pcall(prepareShadowVisual,v,e)
    if not ok then
     shadowVisualStats.setupFailures=shadowVisualStats.setupFailures+1
     shadowVisualStats.lastError=tostring(v.stage)..': '..tostring(err)
     destroyShadowVisual(v);visuals[e.id]=nil;v=nil
     print('[review-v27] shadow setup '..shadowVisualStats.lastError)
    end
   end
  end
  if v and U.Time.time>=(v.nextUpdate or 0) then
   local ok,err=pcall(updateShadowVisual,v,e)
   if not ok then
    -- Keep ownership and process other enemies/events. Never spawn a second copy.
    v.nextUpdate=U.Time.time+1;shadowVisualStats.lastError='update: '..tostring(err)
    if not v.updateErrorReported then v.updateErrorReported=true;print('[review-v27] shadow update '..tostring(err))end
   end
  end
 end
