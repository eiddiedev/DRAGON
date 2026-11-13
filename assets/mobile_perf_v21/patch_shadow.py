from pathlib import Path
import json
A=Path(json.load(open('assets/mobile_perf_v21/baseline.json'))['source']);p=A/'scripts/dragon_combat.lua';s=p.read_text()
marker='local visuals={}'
extra='''
local shadowReady={source=nil,attempts=0,nextAt=0,status='pending',error=nil,spawnAttempts={}}
local function shadowSource()
 if shadowReady.source then return shadowReady.source end
 local now=U.Time.realtimeSinceStartup
 if shadowReady.attempts>=30 or now<shadowReady.nextAt then return nil end
 shadowReady.attempts=shadowReady.attempts+1;shadowReady.nextAt=now+1
 local go=scope:GetGameObjectByPath('ShadowSpiritSource')
 if go then
  local rs=go:GetComponentsInChildren(typeof(U.Renderer),true)
  for i=0,rs.Length-1 do
   local skin=rs[i].gameObject:GetComponent(typeof(U.SkinnedMeshRenderer))
   local mesh=rs[i].gameObject:GetComponent(typeof(U.MeshFilter))
   if (skin and skin.sharedMesh)or(mesh and mesh.sharedMesh)then shadowReady.source=go;shadowReady.status='ready';return go end
  end
 end
 if shadowReady.attempts==30 then shadowReady.status='failed';shadowReady.error='shadow mesh not loaded';print('[mobile-v21] shadow source failed')end
 return nil
end
function GetShadowDiagnostics()
 local count=0;for _,v in pairs(visuals)do if v.go and v.go.activeInHierarchy then count=count+1 end end
 return {build='mobile-v21',source=shadowReady.status,error=shadowReady.error,attempts=shadowReady.attempts,visible=count}
end
'''
s=s.replace(marker,marker+extra,1)
s=s.replace("if not engine or not scope:GetGameObjectByPath('ShadowSpiritSource')then return false,'影灵正在准备'end", "if not engine or not shadowSource()then return false,shadowReady.status=='failed'and '影灵资源加载失败，请重新进入世界'or '影灵正在准备'end")
s=s.replace("local source=scope:GetGameObjectByPath('ShadowSpiritSource');if not source then return end", "local source=shadowSource();if not source then return end")
s=s.replace("local go=Spawn.spawn(self,'ShadowSpiritSource',{networked=false});if go then", """local retry=shadowReady.spawnAttempts[e.id]or{count=0,nextAt=0};shadowReady.spawnAttempts[e.id]=retry
   local go=nil
   if retry.count<10 and U.Time.time>=retry.nextAt then
    retry.count=retry.count+1;retry.nextAt=U.Time.time+.5
    local ok,result=pcall(Spawn.spawn,self,'ShadowSpiritSource',{networked=false,position=V(e.x,state.y+.15,e.z)})
    if ok then go=result else shadowReady.error=tostring(result);print('[mobile-v21] shadow spawn '..shadowReady.error)end
   end
   if go then""")
s=s.replace('v={go=go,materials=materials,bar=bar,bars=bars,bones={}}','v={go=go,materials=materials,bar=bar,bars=bars,bones={},animator=go:GetComponentInChildren(typeof(CS.ModularAnim.Runtime.UGCAnimator),true)}')
s=s.replace('local anim=v.go:GetComponentInChildren(typeof(CS.ModularAnim.Runtime.UGCAnimator),true)', 'local anim=v.animator')
s=s.replace('function Update()','function Update()\n shadowSource()',1)
s=s.replace('end;visuals={}','end;visuals={};shadowReady.spawnAttempts={}',1)
p.write_text(s)
