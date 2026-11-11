"""Build replacement visual packages; preserve registration and disable collision."""
import json,sys
from castle_smooth_cli import call,O
kind=sys.argv[1]
name={'sample':'城堡入口与钟塔精修样板','expand':'城堡塔楼与外围城墙精修','tone':'城堡外暗内亮调色'}[kind]
author='castle_smooth_'+kind+'_v7'
assets=[]
if kind!='tone':
 for receipt in (['import-facade.json'] if kind=='sample' else ['import-towers.json','import-wall.json']):
  d=json.loads((O/receipt).read_text())['data'];assert not d['failedFiles'];assets+=d['assets']
 assert len(assets)==(4 if kind=='sample' else 7)
items=[{'name':a['name'],'uri':a['resource']['uri'],'scale':a['scale']} for a in assets]
script='castle_tone.lua' if kind=='tone' else 'castle_smooth_display.lua'
source='const items='+json.dumps(items)+';const content='+json.dumps((O/script).read_text())+''';
const group=await scene.nodes.create({name:'castle_smooth_visuals',parent:null});const roots=[];
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
const script=await scene.scripts.create({path:'''+json.dumps(script)+''',content});
await scene.scripts.bind({nodes:[group],script:script.handle});return {group,roots,script};'''
(O/(kind+'-assemble.js')).write_text(source)
d=call(['authoring','prefab','read',author,'nodes.query','--args','[{}, {"fields":["handle","name"],"limit":100}]'],kind+'-before-assemble.json',True)
assert not d['data']['result']['items'],'Do not append duplicate assets'
call(['authoring','prefab','execute',author,'--file',str(O/(kind+'-assemble.js')),'--revision',d['data']['revision']],kind+'-assemble.json',True)
for verb in ('validate','build'):call(['authoring','prefab',verb,author],kind+'-'+verb+'.json',True)
call(['authoring','result','archive',author,'--name',name],kind+'-archive.json',True)
