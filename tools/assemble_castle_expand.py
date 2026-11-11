"""Assemble only the new tower/perimeter visual refinements."""
import json
from castle_expand_cli import call, O

assets = []
for filename in ('import-towers.json', 'import-wall.json'):
    data = json.loads((O / filename).read_text())['data']
    assert not data['failedFiles']
    assets.extend(data['assets'])
assert len(assets) >= 5
items = [{'name': 'expand_' + a['name'].replace('-', '_'),
          'uri': a['resource']['uri'], 'scale': a['scale']} for a in assets]
assert sum(float(a['capacity']) for a in assets) <= 160000
source = 'const items=' + json.dumps(items) + '; const content=' + json.dumps(
    (O / 'castle_expand_display.lua').read_text()) + ''';
const group=await scene.nodes.create({name:'castle_expand_visuals',parent:null});
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
const script=await scene.scripts.create({path:'castle_expand_display.lua',content});
await scene.scripts.bind({nodes:[group],script:script.handle});
return {group,roots,script};'''
(O / 'assemble.js').write_text(source)
current = call(['authoring','prefab','read','castle_expand_v5','nodes.query',
                '--args','[{}, {"fields":["handle","name"],"limit":100}]'],
               'author-before-assemble.json', True)
assert not current['data']['result']['items'], 'Do not append duplicate models'
call(['authoring','prefab','execute','castle_expand_v5','--file',str(O/'assemble.js'),
      '--revision',current['data']['revision']], 'assemble.json', True)
for verb in ('validate','build'):
    call(['authoring','prefab',verb,'castle_expand_v5'],verb+'.json',True)
archive=call(['authoring','result','archive','castle_expand_v5',
              '--name','城堡塔楼与外围城墙精修'],'archive.json',True)
assert archive['data']['artifact']['metadata']['capacity'] <= 160000
