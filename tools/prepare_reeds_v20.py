"""Prepare public Scene SDK layout; never writes the live project."""
import json,zipfile,copy,math
from pathlib import Path
import numpy as np
out=Path('assets/reeds_v20');old=json.loads((out/'previous-layout.json').read_text())
with zipfile.ZipFile(out/'scene-before-cli.data') as z:H=np.frombuffer(z.read('HeightMap_3193404.data'),'<f4').reshape(257,257)*256

def height(x,z):
 ix,iz=int(x),int(z);a,b=x-ix,z-iz
 return float((H[iz,ix]*(1-a)+H[iz,ix+1]*a)*(1-b)+(H[iz+1,ix]*(1-a)+H[iz+1,ix+1]*a)*b)
new=copy.deepcopy(old)
for n in new:
 x,z=n['pos']['x'],n['pos']['z'];nx=122+(x-122)*1.15;nz=40+(z-40)*1.12
 # Keep steep slope and the rear hollow out of the expanded footprint.
 if height(nx,nz)<38 or max(abs(height(nx+.6,nz)-height(nx,nz)),abs(height(nx,nz+.6)-height(nx,nz)))>.5:nx,nz=x,z
 n['pos']={'x':nx,'y':height(nx,nz)-.025,'z':nz}
 # Wide, continuous transition to shorter and narrower isolated edge tufts.
 edge=max(abs(nx-122)/16.5,abs(nz-40)/6.3);t=max(0,min(1,(edge-.55)/.5));s=t*t*(3-2*t)
 n['scale']['y']*=1-.36*s
 n['scale']['x']*=1-.16*s;n['scale']['z']*=1-.16*s
(out/'layout.json').write_text(json.dumps(new,indent=2))
uri='hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/26rjifpwxdaw6ipb.glb'
code='const layout='+json.dumps(new)+';\n'
code+='const first=await scene.assets.instantiateModel({resource:'+json.dumps(uri)+',parent:null,name:layout[0].nodeName});\nconst roots=[];\n'
code+='for(let i=0;i<layout.length;i++){const p=layout[i];const root=i===0?first.root:(await scene.nodes.clone({roots:[first.root],parent:null})).roots[0]; await scene.nodes.update([root],{name:p.nodeName}); await scene.transforms.set({nodes:[root],space:"world",scope:"subtree",value:{position:p.pos,rotation:p.rot,scale:p.scale}}); roots.push(root);}\n'
code+='await scene.components.set({nodes:roots,type:"physicsColliderData",values:{enableCollision:false,enableRigidBody:false}});return {roots,count:roots.length};\n'
(out/'assemble.js').write_text(code)
print('Prepared',len(new),'patches, same leaf count; triangle budget',len(new)*2394,'previous',len(old)*3582)
