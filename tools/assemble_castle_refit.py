from pathlib import Path
import json,zipfile
O=Path(__file__).resolve().parents[1]/'assets/castle_refit_v1'
s=json.loads(zipfile.ZipFile(O/'scene-before.data').read('SerializePcgData.json'));by={n['basic']['nodeName']:n for n in s['nodeTransformDatas']};layout=[];remove=[]
for f in sorted(O.glob('import-*.json')):
 d=json.loads(f.read_text())
 if not d.get('ok'):continue
 key=f.stem.removeprefix('import-');a=d['data']['assets'][0]
 if key=='castle_glow':continue
 source=key
 for group in ['gothic_main','gothic_towers']:
  if key.startswith(group):source=group
 if source not in by:continue
 b=by[source]['basic'];layout.append(dict(name=key,uri=a['resource']['uri'],pos=b['pos'],rot=b['rot'],scale=a['scale'],collision=source!='lamp_glow'))
 remove.append(by[source]['id'])
for name in ['tripo_castle_statue_0','tripo_castle_statue_1','tripo_castle_cornice_0','tripo_castle_cornice_1']:
 n=by[name];b=n['basic'];pos=dict(b['pos']);rot=dict(b['rot'])
 if 'statue' in name:rot=dict(x=0,y=0,z=0,w=1)
 else:pos['y']=78.2;pos['z']=167.6
 layout.append(dict(name=name,uri=json.loads((O.parent/'tripo/scene_install'/('import-castle_statue.json' if 'statue' in name else 'import-castle_cornice.json')).read_text())['data']['assets'][0]['resource']['uri'],pos=pos,rot=rot,scale=b['scale'],collision=True));remove.append(n['id'])
(O/'replacement-plan.json').write_text(json.dumps({'layout':layout,'remove':sorted(set(remove))},ensure_ascii=False,indent=2))
body='''const roots=[];for(const p of layout){const r=(await scene.assets.instantiateModel({resource:p.uri,parent:null,name:p.name})).root;await scene.transforms.set({nodes:[r],space:"world",scope:"subtree",value:{position:p.pos,rotation:p.rot,scale:p.scale}});await scene.components.set({nodes:[r],type:"physicsColliderData",values:{enableCollision:p.collision,enableRigidBody:false}});roots.push({name:p.name,root:r});}return {roots};'''
(O/'assemble.js').write_text('const layout='+json.dumps(layout)+';'+body)
print([(p['name'],p['scale']['x']) for p in layout])
