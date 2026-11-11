"""Budget-neutral expansion: 110 groups,20 small colonies,20 isolated plants."""
from pathlib import Path
import numpy as np,json,zipfile,math,random,shutil
O=Path('assets/reeds_v21');p=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data';shutil.copy2(p,O/'scene-before.data')
with zipfile.ZipFile(p) as z:H=np.frombuffer(z.read('HeightMap_3193404.data'),'<f4').reshape(257,257)*256

def height(x,z):
 i,j=int(x),int(z);a,b=x-i,z-j
 return float((H[j,i]*(1-a)+H[j,i+1]*a)*(1-b)+(H[j+1,i]*(1-a)+H[j+1,i+1]*a)*b)
uris={a['name']:a['resource']['uri'] for a in json.loads((O/'import-assets.json').read_text())['data']['assets']};uris['group']='hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/26rjifpwxdaw6ipb.glb'
r=random.Random(21011);layout=[]
for kind,count,lo,hi in [('group',110,0,.78),('small',20,.73,.96),('single',20,.94,1.12)]:
 for j in range(count):
  for attempt in range(5000):
   a=r.uniform(0,math.tau);rho=math.sqrt(r.uniform(lo*lo,hi*hi));ripple=1+.05*math.sin(a*5)+.03*math.cos(a*3)
   x=121+21.3*rho*math.cos(a)*ripple;z=41+8.4*rho*math.sin(a)*ripple;y=height(x,z)
   if y<38 or (x-130)**2+(z-48)**2<3.1**2:continue
   if max(abs(height(x+.5,z)-y),abs(height(x,z+.5)-y))>.5:continue
   spacing=.98 if kind=='group' else 1.05
   if any((n['pos']['x']-x)**2+(n['pos']['z']-z)**2<spacing**2 for n in layout):continue
   break
  else:raise RuntimeError('Cannot fit layout')
  yaw=r.uniform(-math.pi,math.pi);width=r.uniform(1.1,1.4) if kind=='group' else r.uniform(.8,1.15)
  sy=r.uniform(.7,1.1) if kind=='group' else r.uniform(.45,.8) if kind=='small' else r.uniform(.35,.65)
  layout.append({'name':f'golden_geometry_{len(layout)}','kind':kind,'uri':uris[kind],'pos':{'x':x,'y':y-.025,'z':z},'rot':{'x':0,'y':math.sin(yaw/2),'z':0,'w':math.cos(yaw/2)},'scale':{'x':width,'y':sy,'z':width}})
(O/'layout.json').write_text(json.dumps(layout,indent=2))
code='const layout='+json.dumps(layout)+';\nconst templates={};const roots=[];\n'
code+='for(const p of layout){let root;if(templates[p.kind])root=(await scene.nodes.clone({roots:[templates[p.kind]],parent:null})).roots[0];else{root=(await scene.assets.instantiateModel({resource:p.uri,parent:null,name:p.name})).root;templates[p.kind]=root;}await scene.nodes.update([root],{name:p.name});await scene.transforms.set({nodes:[root],space:"world",scope:"subtree",value:{position:p.pos,rotation:p.rot,scale:p.scale}});roots.push(root);}\nawait scene.components.set({nodes:roots,type:"physicsColliderData",values:{enableCollision:false,enableRigidBody:false}});return {roots,count:roots.length};'
(O/'assemble.js').write_text(code)
print('Triangles',110*2394+20*798+20*266,'v20',150*2394)
print('bounds',[(k,min(n['pos'][k] for n in layout),max(n['pos'][k] for n in layout)) for k in ['x','z']])
