"""Assemble the separately imported facade and left clock tower once."""
import json
from castle_sample_cli import call,O
assets=[]
for f in ['import-entrance.json','import-clock.json']:
 assets+=json.loads((O/f).read_text())['data']['assets']
assert len(assets)==3,len(assets)
items=[{'name':'sample_'+a['name'].replace('-','_'),'uri':a['resource']['uri'],'scale':a['scale']} for a in assets]
source='const items='+json.dumps(items)+'; const content='+json.dumps((O/'castle_sample_display.lua').read_text())+''';
const group=await scene.nodes.create({name:'castle_sample_visuals',parent:null});
const roots=[];
for(const p of items){
 const n=(await scene.assets.instantiateModel({resource:p.uri,parent:group,name:p.name})).root;
 await scene.transforms.set({nodes:[n],space:'world',scope:'subtree',value:{position:{x:127,y:0,z:176},rotation:{x:0,y:1,z:0,w:0},scale:p.scale}});
 const ns=await scene.nodes.query({subtree:n},{fields:['handle','componentTypes'],limit:100});
 if(ns.nextCursor)throw new Error('Unexpected large model subtree');
 for(const node of ns.items){
  const input={nodes:[node.handle],type:'physicsColliderData',values:{enableCollision:false,enableRigidBody:false}};
  if(node.componentTypes.includes('physicsColliderData'))await scene.components.set(input);else await scene.components.add(input);
 }
 roots.push({name:p.name,root:n,nodes:ns.items});
}
const script=await scene.scripts.create({path:'castle_sample_display.lua',content});
await scene.scripts.bind({nodes:[group],script:script.handle});
return {group,roots,script};'''
(O/'assemble.js').write_text(source)
call(['authoring','prefab','execute','castle_sample_v3','--file',str(O/'assemble.js')],'assemble.json',True)
for verb in ['validate','build']:call(['authoring','prefab',verb,'castle_sample_v3'],verb+'.json',True)
a=call(['authoring','result','archive','castle_sample_v3','--name','城堡入口与钟塔精修样板'],'archive.json',True)
assert a['data']['artifact']['metadata']['capacity']<=60000,'Sample exceeds capacity allocation'
