await scene.nodes.update(['n163'],{name:'ShadowSpiritSource'});
await scene.nodes.reparent({nodes:['n163'],parent:'n155',preserve:'local'});
const scripts={};for(const path of ['dragon_combat.lua','dragon_combat_rules.lua'])scripts[path]=await scene.scripts.create({path});return scripts;
