"""Replace only the two sample facade resources; original castle is untouched."""
import json
from castle_sample_cli import call,O
assets=json.loads((O/'import-entrance-final.json').read_text())['data']['assets']
original=json.loads((O/'assemble.json').read_text())['data']['result']['roots']
items=[]
for a in assets:
 name='sample_'+a['name']
 items.append({'root':next(r['root'] for r in original if r['name']==name),'name':name,'uri':a['resource']['uri'],'scale':a['scale']})
source='const items='+json.dumps(items)+''';const out=[];for(const p of items){
 const n=(await scene.assets.replaceModel({root:p.root,replacement:p.uri,name:p.name})).root;
 await scene.transforms.set({nodes:[n],space:'world',scope:'subtree',value:{position:{x:127,y:0,z:176},rotation:{x:0,y:1,z:0,w:0},scale:p.scale}});
 const ns=await scene.nodes.query({subtree:n},{fields:['handle','componentTypes'],limit:100});if(ns.nextCursor)throw new Error('Unexpected subtree');
 for(const node of ns.items){const v={nodes:[node.handle],type:'physicsColliderData',values:{enableCollision:false,enableRigidBody:false}};if(node.componentTypes.includes('physicsColliderData'))await scene.components.set(v);else await scene.components.add(v);}
 out.push({name:p.name,root:n});
}return out;'''
(O/'replace-portal.js').write_text(source)
call(['authoring','prefab','execute','castle_sample_v3','--file',str(O/'replace-portal.js')],'replace-portal.json',True)
for verb in ['validate','build']:call(['authoring','prefab',verb,'castle_sample_v3'],verb+'-final.json',True)
a=call(['authoring','result','archive','castle_sample_v3','--name','城堡入口与钟塔精修样板'],'archive-final.json',True)['data']
assert a['artifact']['metadata']['capacity']<=60000
old=json.loads((O/'scene-import.json').read_text())['data']['rootIDs'][0]
(O/'scene-import-initial.json').write_bytes((O/'scene-import.json').read_bytes())
call(['scene','remove','--request-id','castle-sample-remove-misaligned-portal','--',old],'scene-remove-initial.json')
call(['scene','import','--uri',a['uri'],'--name','城堡入口与钟塔精修样板','--position','0,0,0','--request-id','castle-sample-v4-aligned-portal'],'scene-import.json')
call(['scene','save','--request-id','castle-sample-v4-aligned-save'],'save-aligned.json')
call(['runtime','start'],'runtime.json')
call(['runtime','lua','targets'],'targets.json')
