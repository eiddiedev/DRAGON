---@id cf8cdf7f-2be6-49bb-b9a6-ca99581d3704
---@referenceName scene_sheep_sound.lua
local U=CS.UnityEngine
local bus=require('modules.scene_interaction_bus')
local source=nil
local nextCall=0
function Start()
 source=self.gameObject:AddComponent(typeof(U.AudioSource))
 source.playOnAwake=false;source.loop=false;source.spatialBlend=1
 source.minDistance=2;source.maxDistance=14;source.volume=.55
end
function OnActorTriggerEnter(actor)
 if not actor or not actor.isLocal or not source then return end
 local now=U.Time.time
 if now<nextCall or now-bus.lastBaa<2.5 or not bus.clips.baa then return end
 nextCall=now+10;bus.lastBaa=now;source:PlayOneShot(bus.clips.baa)
end
function OnDestroy()
 if source then U.Object.Destroy(source);source=nil end
end
