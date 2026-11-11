const m=await scene.assets.instantiateModel({resource:'hamlet-ugc/aigc_editor/dev/unity/9754990109442.glb',parent:'n1',name:'低模刺柏'});
await scene.transforms.set({nodes:[m.root],space:'local',value:{position:{x:112,y:10.104,z:44},scale:{x:4.221518,y:4.221518,z:4.221518},rotation:{x:0,y:0,z:0,w:1}}});
const script=await scene.scripts.create({path:'dragon_world_bridge.lua'});return {model:m,script};
