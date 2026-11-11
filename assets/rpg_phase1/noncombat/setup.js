const root=await scene.nodes.create({name:'DragonNoncombat',parent:null});
const scripts={};for(const name of ['dragon_progress_rules','dragon_progress','dragon_exploration','dragon_daycycle']) scripts[name]=await scene.scripts.create({path:name+'.lua'});
return {root,scripts};
