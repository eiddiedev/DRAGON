const items=[{"name": "castle_entry_stairs", "uri": "hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/oht7xhy085ruthge.glb", "scale": {"x": 4.599999904632568, "y": 4.599999904632568, "z": 4.599999904632568}, "collision": false}, {"name": "castle_entry_forecourt", "uri": "hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/oy0hn62tx72so1he.glb", "scale": {"x": 26, "y": 26, "z": 26}, "collision": false}, {"name": "castle_entry_collision", "uri": "hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/dcm2gfb15rj23h36.glb", "scale": {"x": 26, "y": 26, "z": 26}, "collision": true}];const roots=[];for(const p of items){
 const n=(await scene.assets.instantiateModel({resource:p.uri,parent:null,name:p.name})).root;
 await scene.transforms.set({nodes:[n],space:'world',scope:'subtree',value:{position:{x:127,y:0,z:176},rotation:{x:0,y:1,z:0,w:0},scale:p.scale}});
 const ns=(await scene.nodes.query({subtree:n},{fields:['handle','componentTypes'],limit:50}));if(ns.nextCursor)throw new Error('Unexpected large subtree');
 for(const node of ns.items){
  const input={nodes:[node.handle],type:'physicsColliderData',values:{enableCollision:p.collision,enableRigidBody:false}};
  if(node.componentTypes.includes('physicsColliderData'))await scene.components.set(input);else await scene.components.add(input);
  if(p.collision){const app={nodes:[node.handle],type:'appearanceData',values:{transparency:0,castShadows:false,isModified:true}};
   if(node.componentTypes.includes('appearanceData'))await scene.components.set(app);else await scene.components.add(app);}
 }
 roots.push({name:p.name,root:n,nodes:ns.items});
}return roots;