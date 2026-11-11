exec(open('assets/layout_sw_v13/inspect.py').read().split("a=H[")[0])
import random,math
r=random.Random(1311);old=json.loads(Path('assets/reeds_v21/layout.json').read_text());uris={g['kind']:g['uri'] for g in old};layout=[]
def h(x,z):
 i,j=int(x),int(z);a,b=x-i,z-j
 return float((H[j,i]*(1-a)+H[j,i+1]*a)*(1-b)+(H[j+1,i]*(1-a)+H[j+1,i+1]*a)*b)
for kind,count,lo,hi in [('group',70,0,.76),('small',20,.7,.96),('single',20,.93,1.12)]:
 for n in range(count):
  for _ in range(5000):
   a=r.uniform(0,math.tau);rho=math.sqrt(r.uniform(lo*lo,hi*hi));x=157+21*rho*math.cos(a);z=41+8.4*rho*math.sin(a)
   if x<139 or (x-128)**2+(z-17)**2<15**2:continue
   if any((x-g['pos']['x'])**2+(z-g['pos']['z'])**2<1.15**2 for g in old+layout):continue
   y=h(x,z)
   if max(abs(h(x+.5,z)-y),abs(h(x,z+.5)-y))>.55:continue
   break
  else:raise ValueError('fit')
  yaw=r.uniform(-math.pi,math.pi);w=r.uniform(1.15,1.45);sy=r.uniform(.7,1.1) if kind=='group' else r.uniform(.4,.75)
  layout.append(dict(name=f'golden_east_v13_{len(layout)}',kind=kind,uri=uris[kind],pos=dict(x=x,y=y-.025,z=z),rot=dict(x=0,y=math.sin(yaw/2),z=0,w=math.cos(yaw/2)),scale=dict(x=w,y=sy,z=w)))
remove=[]
for n in ns:
 b=n['basic'];q=b['pos']
 if not b['nodeName'].startswith('pl_grass_'):continue
 if (q['x']-128)**2+(q['z']-17)**2<13**2 or any((q['x']-g['pos']['x'])**2+(q['z']-g['pos']['z'])**2<(2.1 if g['kind']=='group' else 1)**2 for g in layout if g['kind']!='single'):remove.append(dict(id=n['id'],name=b['nodeName'],pos=q))
O.mkdir(exist_ok=True);(O/'layout.json').write_text(json.dumps(layout,indent=2));(O/'clear-grass.json').write_text(json.dumps(remove,indent=2))
code='await scene.scripts.setParams({bindings:["n155:s:313ebddc-058f-40f1-be60-76f6a590e9f8"],values:{ArenaX:128,ArenaZ:17,ArenaRadius:10}});\n'
code+='const layout='+json.dumps(layout)+';const templates={};const roots=[];\n'
code+='for(const p of layout){let root;if(templates[p.kind])root=(await scene.nodes.clone({roots:[templates[p.kind]],parent:"n155"})).roots[0];else{root=(await scene.assets.instantiateModel({resource:p.uri,parent:"n155",name:p.name})).root;templates[p.kind]=root;}await scene.nodes.update([root],{name:p.name});await scene.transforms.set({nodes:[root],space:"world",scope:"subtree",value:{position:p.pos,rotation:p.rot,scale:p.scale}});roots.push(root);} await scene.components.set({nodes:roots,type:"physicsColliderData",values:{enableCollision:false,enableRigidBody:false}});return {roots,count:roots.length};'
(O/'assemble.js').write_text(code)
print(json.dumps(dict(new_wheat=len(layout),clear_grass=len(remove),added_triangles=70*2394+20*798+20*266,arena=[128,17]),ensure_ascii=False))
