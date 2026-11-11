from pathlib import Path
import json
from castle_cli import call,O
R=O.parents[1]
items=[]
for key,name in [('gothic_main-east-v3','gothic_main-east'),('gothic_main-west-v3','gothic_main-west'),('gothic_wall-v2','gothic_wall'),('castle_rooms','castle_rooms'),('castle_glow','castle_rooms_glow')]:
 a=json.loads((O/('import-'+key+'.json')).read_text())['data']['assets'][0]
 items.append(dict(name=name,uri=a['resource']['uri'],scale=a['scale'],collision=key!='castle_glow'))
source='await scene.nodes.remove({nodes:["n1","n4","n13"]});const items='+json.dumps(items)+''';const roots=[];let interior;for(const p of items){const n=(await scene.assets.instantiateModel({resource:p.uri,parent:null,name:p.name})).root;await scene.transforms.set({nodes:[n],space:'world',scope:'subtree',value:{position:{x:127,y:0,z:176},rotation:{x:0,y:1,z:0,w:0},scale:p.scale}});await scene.components.set({nodes:[n],type:'physicsColliderData',values:{enableCollision:p.collision,enableRigidBody:false}});roots.push({name:p.name,root:n});if(p.name==='castle_rooms')interior=n;}'''
source+='const script=await scene.scripts.create({path:"castle_baked_display.lua",content:'+json.dumps((R/'scripts/castle_baked_display.lua').read_text())+'});await scene.scripts.bind({nodes:[interior],script:script.handle});return {roots,script};'
(O/'finalize-author.js').write_text(source)
call(['authoring','prefab','execute','castle_refit_v1','--file',str(O/'finalize-author.js')],'finalize-author.json',True)
for v in ['validate','build']:call(['authoring','prefab',v,'castle_refit_v1'],v+'-final.json',True)
call(['authoring','result','archive','castle_refit_v1','--name','龙眠城堡精修'],'archive-final.json',True)
