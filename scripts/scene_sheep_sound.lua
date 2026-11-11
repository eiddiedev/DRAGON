local U=CS.UnityEngine
local function makeClip(name,duration,fn)
 local rate=22050;local samples={};local count=math.floor(rate*duration)
 for i=1,count do samples[i]=fn((i-1)/rate) end
 local clip=U.AudioClip.Create(name,count,1,rate,false);clip:SetData(samples,0);return clip
end
local baa=nil
local source=nil
local nextCall=0
function Start()
 baa=makeClip('sheep_baa',1.05,function(t)
  local env=math.min(1,t/.07)*math.min(1,(1.05-t)/.18)
  local phase=2*math.pi*(185*t-32*t*t+1.3*math.sin(t*19))
  return env*.22*(math.sin(phase)+.55*math.sin(phase*3)+.22*math.sin(phase*5))
 end)
 source=self.gameObject:AddComponent(typeof(U.AudioSource))
 source.playOnAwake=false;source.loop=false;source.spatialBlend=1
 source.minDistance=2;source.maxDistance=14;source.volume=.55
end
function OnActorTriggerEnter(actor)
 if not actor or not actor.isLocal or not source then return end
 local now=U.Time.time
 if now<nextCall or now<U.Shader.GetGlobalFloat('_DragonNextBaa') or not baa then return end
 nextCall=now+10;U.Shader.SetGlobalFloat('_DragonNextBaa',now+2.5);source:PlayOneShot(baa)
end
function OnDestroy()
 if source then U.Object.Destroy(source);source=nil end
 if baa then U.Object.Destroy(baa) end
end
