-- Insert after UI.clip is declared, before Update. Clips are generated once.
UI.interactions=require('modules.scene_interaction_bus')
function UI.prepareInteractionAudio()
 local clips=UI.interactions.clips
 if not clips.bounce then
  clips.bounce=UI.clip('mushroom_spring',.48,function(t)
   local env=math.min(1,t/.012)*math.exp(-t*8)
   local phase=2*math.pi*(420*t-310*t*t)
   return .5*env*(math.sin(phase)+.22*math.sin(phase*2))
  end)
 end
 if not clips.baa then
  clips.baa=UI.clip('sheep_baa',1.05,function(t)
   local env=math.min(1,t/.07)*math.min(1,(1.05-t)/.18)
   local phase=2*math.pi*(185*t-32*t*t+1.3*math.sin(t*19))
   return env*.22*(math.sin(phase)+.55*math.sin(phase*3)+.22*math.sin(phase*5))
  end)
 end
end
