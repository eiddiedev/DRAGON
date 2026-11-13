import json,zipfile,re,struct
from pathlib import Path
D=Path('assets/mobile_compat_v23');A=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9/ai-sessions/workspace_m293a9tg/wprefabs/mobile_actors_v23')
s=json.loads(zipfile.ZipFile(D/'main-before.scene.data').read('SerializePcgData.json'));roots=json.loads((D/'actor-originals.json').read_text());uris=json.loads((D/'actor-uris.json').read_text());byname={v['name']:v for v in uris}
def anim(name):
 v=byname[name];b=(A/'assets/models'/('model-'+name.replace('_','-'))/'topology/model.glb').read_bytes();l=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+l]);clips=[{'animationIndex':i,'animationName':x['name'],'loop':x['name'] not in ['takeoff','land','perch_takeoff','perch_land'],'skipFirstFrame':None} for i,x in enumerate(g.get('animations',[]))];aid='mobile/'+name;key='mobile-controller/'+name;default='perch' if name=='dragon_v8_live' else clips[0]['animationName']
 nodes={f'state:{i}':{'id':f'state:{i}','type':'state','name':c['animationName'],'stateMachine':'sm:External','speed':1,'motion':{'kind':'clip','animationSetName':'ModelExternalAnimations','assetId':aid,'clipName':c['animationName']}} for i,c in enumerate(clips)}
 graph={'schemaVersion':2,'animationSetName':'ModelExternalAnimations','controller':{'name':key,'layers':[{'name':'External','index':0,'weight':1,'stateMachine':'sm:External'}]},'graph':{'parameters':{},'stateMachines':{'sm:External':{'id':'sm:External','name':'External','defaultNode':next(k for k,n in nodes.items() if n['name']==default),'childNodes':list(nodes)}},'nodes':nodes,'transitions':[]}}
 return {'schemaVersion':2,'controllerKey':key,'overrides':[],'animationAssets':[{'assetId':aid,'assetData':{'uri':v['oldUri']},'resourceRefId':0,'clips':clips}],'animationSet':{'name':'ModelExternalAnimations','guid':'mobile/'+name,'embed':True,'defaultControllerKey':key,'defaultAssetId':aid,'defaultClip':default,'controllers':[{'key':key,'json':json.dumps(graph)}],'assetIds':[]},'embeddedAnimationAssetId':aid,'bindOnLoad':True}
scripts={};items=[]
for r in roots:
 name=r['basic']['nodeName'];kind='sheep' if name.startswith('sheep_') else name
 child=next(n for n in s['nodeTransformDatas'] if n['basic']['parentId']==r['id'])
 binds=[]
 for b in r.get('runtimeScriptBindings',[]):
  sid=b['scriptId']
  if sid=='d6f83b17-d36c-4840-ae2a-b896be27b101':continue
  src=s['runtimeScripts'][sid];content=re.sub(r'^---@(?:id|referenceName).*\n','',src['content'],flags=re.M)
  if sid=='e59fb775-946f-4711-be95-857448a20f46':
   # Avoid convex mesh cooking: a simple root capsule provides push contact.
   start=content.index(' -- Existing generated colliders')
   end=content.index(' rb.constraints=',start)
   content=content[:start]+''' local c=self.gameObject:GetComponent(typeof(U.CapsuleCollider))
 if not c then c=self.gameObject:AddComponent(typeof(U.CapsuleCollider));c.center=U.Vector3(0,.45,0);c.radius=.28;c.height=1.05;c.direction=2 end
'''+content[end:]
  scripts[sid]={'path':src.get('referencePath') or src.get('referenceName') or sid+'.lua','content':content};binds.append({'id':sid,'params':json.loads(b.get('paramsJson','{}'))})
 items.append({'oldId':r['id'],'name':name,'uri':byname[kind]['newUri'],'childName':child['basic']['nodeName'],'childScale':child['basic']['scale'],'transform':{'position':r['basic']['pos'],'rotation':r['basic']['rot'],'scale':r['basic']['scale']},'physics':r['physics'],'anim':r.get('animation',{}).get('ugcAnimatorData') or (anim(kind) if kind in ['dragon_v8_live','flying_carpet'] else None),'binds':binds})
for i,v in enumerate(scripts.values()):v['path']=Path(v['path']).name if str(v['path']).endswith('.lua') else 'actor_'+str(i)+'.lua'
code='const items='+json.dumps(items)+';\nconst sources='+json.dumps(scripts)+';\n'+'''
const group=await scene.nodes.create({name:'手机兼容动态模型',parent:null});
const registered={};for(const [id,s] of Object.entries(sources))registered[id]=await scene.scripts.create(s);
const out=[];
for(const v of items){
 const root=await scene.nodes.create({name:v.name,parent:group});
 const m=await scene.assets.instantiateModel({resource:v.uri,parent:root,name:v.childName});
 await scene.transforms.set({nodes:[m.root],space:'local',value:{position:{x:0,y:0,z:0},rotation:{x:0,y:0,z:0,w:1},scale:v.childScale}});
 await scene.components.set({nodes:[m.root],type:'physicsColliderData',values:{enableCollision:false,enableRigidBody:false}});
 if(v.physics.physicsColliderData)await scene.components.add({nodes:[root],type:'physicsColliderData',values:v.physics.physicsColliderData});
 if(v.physics.triggerData?.length)await scene.components.add({nodes:[root],type:'triggerData',values:v.physics.triggerData});
 if(v.anim)await scene.components.add({nodes:[root],type:'ugcAnimatorData',values:v.anim});
 if(v.binds.length){await scene.scripts.setScopeRole({nodes:[root],role:'resource'});for(const b of v.binds)await scene.scripts.bind({nodes:[root],script:registered[b.id].handle,params:b.params});}
 await scene.transforms.set({nodes:[root],space:'world',value:v.transform});
 out.push({name:v.name,root,geometry:m.root,oldId:v.oldId});
}
return {group,actors:out};
'''
(D/'assemble-actors.js').write_text(code);(D/'actor-configs.json').write_text(json.dumps(items,indent=2));print('Prepared',len(items),'actors and',len(scripts),'scripts')
