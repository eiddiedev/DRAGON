"""Apply final coordinate-correct gate resource to its existing author assembly."""
import json
from castle_cli import call,O
receipt=O/'import-gothic_wall-v5.json'
a=json.loads(receipt.read_text())['data']['assets'][0]
js='await scene.nodes.remove({nodes:["n47"]});const p='+json.dumps({'uri':a['resource']['uri'],'scale':a['scale']})+";const n=(await scene.assets.instantiateModel({resource:p.uri,parent:null,name:'gothic_wall'})).root;await scene.transforms.set({nodes:[n],space:'world',scope:'subtree',value:{position:{x:127,y:0,z:176},rotation:{x:0,y:1,z:0,w:0},scale:p.scale}});await scene.components.set({nodes:[n],type:'physicsColliderData',values:{enableCollision:true,enableRigidBody:false}});return {root:n};"
(O/'gate-author-level.js').write_text(js)
call(['authoring','prefab','execute','castle_refit_v1','--file',str(O/'gate-author-level.js')],'gate-author-level.json',True)
for v in ['validate','build']:call(['authoring','prefab',v,'castle_refit_v1'],v+'-gate-level.json',True)
call(['authoring','result','archive','castle_refit_v1','--name','龙眠城堡精修'],'archive-gate-level.json',True)
