import json
from castle_entry_cli import call,O
assets=json.loads((O/'import-entry.json').read_text())['data']['assets']
items=[]
for name in ['entry_stairs','entry_forecourt','entry_collision']:
 a=next(a for a in assets if a['name']==name)
 items.append({'name':'castle_'+name,'uri':a['resource']['uri'],'scale':a['scale'],'collision':name=='entry_collision'})
source='const items='+json.dumps(items)+''';const roots=[];for(const p of items){
 const n=(await scene.assets.instantiateModel({resource:p.uri,parent:null,name:p.name})).root;
 await scene.transforms.set({nodes:[n],space:'world',scope:'subtree',value:{position:{x:127,y:0,z:176},rotation:{x:0,y:1,z:0,w:0},scale:p.scale}});
 const ns=(await scene.nodes.query({subtree:n},{fields:['handle','componentTypes'],limit:50}));if(ns.nextCursor)throw new Error('Unexpected large subtree');
 for(const node of ns.items){
  const input={nodes:[node.handle],type:'physicsColliderData',values:{enableCollision:p.collision,enableRigidBody:false}};
  if(node.componentTypes.includes('physicsColliderData'))await scene.components.set(input);else await scene.components.add(input);
  if(p.collision){const app={nodes:[node.handle],type:'appearanceData',values:{visible:false,transparency:0,castShadows:false,isModified:true}};
   if(node.componentTypes.includes('appearanceData'))await scene.components.set(app);else await scene.components.add(app);}
 }
 roots.push({name:p.name,root:n,nodes:ns.items});
}return roots;'''
(O/'assemble.js').write_text(source)
call(['authoring','prefab','execute','castle_entry_v2','--file',str(O/'assemble.js')],'assemble.json',True)
for v in ['validate','build']:call(['authoring','prefab',v,'castle_entry_v2'],v+'.json',True)
call(['authoring','result','archive','castle_entry_v2','--name','城堡入口石阶与前庭'],'archive.json',True)
