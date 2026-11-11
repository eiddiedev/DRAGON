from pathlib import Path
import json,zipfile,random,math,io,base64
import numpy as np
from PIL import Image
O=Path('assets/layout_fix_v14');P=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0';
with zipfile.ZipFile(P/'scene.data') as z:
 ns=json.loads(z.read('SerializePcgData.json'))['nodeTransformDatas'];H=np.frombuffer(z.read('HeightMap_3193404.data'),'<f4').reshape(257,257)*256;cover=np.array(Image.open(io.BytesIO(z.read('MatCoverTex_3193404.png'))).convert('RGBA'))
# Measured renderer bounds, enlarged for visible plant radius and entrance clearances.
boxes=[(139,153,39,54),(153,171,35,52),(166,182,36,54),(157,175,45,63)]
def free(x,z):return not any(a<x<b and c<z<d for a,b,c,d in boxes) and (x-130.3)**2+(z-19.4)**2>17**2
old=json.loads(Path('assets/reeds_v21/layout.json').read_text());new=json.loads(Path('assets/layout_sw_v13/layout.json').read_text());r=random.Random(1411);fixed=[];moved=0
for i,g in enumerate(new):
 g['name']='golden_geometry_'+str(150+i);x,z=g['pos']['x'],g['pos']['z']
 if not free(x,z):
  moved+=1
  for _ in range(10000):
   a=r.uniform(0,math.tau);rho=math.sqrt(r.random());x=162+17*rho*math.cos(a);z=32+5*rho*math.sin(a)
   if free(x,z) and all((x-t['pos']['x'])**2+(z-t['pos']['z'])**2>1.1**2 for t in old+fixed):break
  else:raise RuntimeError('layout full')
 i0,j=int(x),int(z);a,b=x-i0,z-j;y=float((H[j,i0]*(1-a)+H[j,i0+1]*a)*(1-b)+(H[j+1,i0]*(1-a)+H[j+1,i0+1]*a)*b)
 g['pos']=dict(x=x,y=y-.025,z=z);fixed.append(g)
(O/'layout.json').write_text(json.dumps(fixed,indent=2));roots=json.loads(Path('assets/layout_sw_v13/execute.json').read_text())['data']['result']['roots']
code='await scene.scripts.setParams({bindings:["n155:s:313ebddc-058f-40f1-be60-76f6a590e9f8"],values:{ArenaX:130.3,ArenaZ:19.4,ArenaRadius:13.275}});\n'
for node,g in zip(roots,fixed):code+='await scene.transforms.set('+json.dumps(dict(nodes=[node],space='world',scope='subtree',value=dict(position=g['pos'])))+');\n'
(O/'layout.js').write_text(code)
remove=[]
for n in ns:
 b=n['basic'];q=b['pos']
 if b['nodeName'].startswith('pl_grass_') and ((q['x']-130.3)**2+(q['z']-19.4)**2<16**2 or any((q['x']-g['pos']['x'])**2+(q['z']-g['pos']['z'])**2<2.1**2 for g in fixed if g['kind']=='group')):remove.append(n['id'])
(O/'remove-grass.json').write_text(json.dumps(remove))
h,w=cover.shape[:2];yy,xx=np.mgrid[:h,:w];X=(xx+.5)*256/w;Z=256-(yy+.5)*256/h;mask=np.zeros((h,w))
for g in fixed:
 q=g['pos'];d=np.sqrt((X-q['x'])**2+(Z-q['z'])**2);f=4 if g['kind']=='group' else 2.8 if g['kind']=='small' else 1.5;t=np.clip((d-.4)/f,0,1);mask=np.maximum(mask,(1-t*t*(3-2*t))*(1 if g['kind']=='group' else .65 if g['kind']=='small' else .3))
for a,b,c,d in boxes:
 dx=np.maximum(np.maximum(a-X,0),X-b);dz=np.maximum(np.maximum(c-Z,0),Z-d);t=np.clip(np.sqrt(dx*dx+dz*dz)/2,0,1);mask*=t*t*(3-2*t)
rgb=cover[:,:,:3].astype(float);lum=rgb@np.array([.2126,.7152,.0722]);target=np.array([132,105,58])*np.clip(lum/75,.65,1.4)[:,:,None];cover[:,:,:3]=np.clip(rgb*(1-mask[:,:,None])+target*mask[:,:,None],0,255).round().astype('uint8');Image.fromarray(cover).save(O/'wheat-cover.png')
encoded=base64.b64encode((O/'wheat-cover.png').read_bytes()).decode()
code='''\n-- Runtime-only terrain cover clone; original scene texture remains intact.
function UI.applyWheatGroundV14()
 if UI.wheatGroundV14 then return end
 local t=UnityEngine.Terrain.activeTerrain;if not t or not t.materialTemplate then return end
 local tex=UnityEngine.Texture2D(2,2);local bytes=CS.System.Convert.FromBase64String("'''+encoded+'''")
 if not UnityEngine.ImageConversion.LoadImage(tex,bytes)then UnityEngine.Object.Destroy(tex);return end
 tex.wrapMode=UnityEngine.TextureWrapMode.Clamp
 local m=UnityEngine.Material(t.materialTemplate);m:SetTexture('_CoverTex',tex);t.materialTemplate=m
 UI.wheatGroundV14={texture=tex,material=m}
end
'''
(O/'ground.lua').write_text(code)
print(dict(moved=moved,clear=len(remove),texture_bytes=(O/'wheat-cover.png').stat().st_size))
