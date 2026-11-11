"""Closed-project terrain pass and removal of replaced v20 subtree. Never run open."""
from pathlib import Path
import zipfile,json,io,shutil,math
import numpy as np
from PIL import Image
O=Path('assets/reeds_v21');p=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data'
with zipfile.ZipFile(p) as z:entries=[(i,z.read(i)) for i in z.infolist()]
raw={i.filename:v for i,v in entries};d=json.loads(raw['SerializePcgData.json']);old=d['nodeTransformDatas'];layout=json.loads((O/'layout.json').read_text())
remove={-1060845848}
for n in old:
 b=n['basic'];q=b['pos']
 if not b['nodeName'].startswith('pl_grass_'):continue
 # Clear the carpet beneath actual colonies; single edge plants blend into the original ground.
 if any((q['x']-g['pos']['x'])**2+(q['z']-g['pos']['z'])**2<(2.15 if g['kind']=='group' else .9)**2 for g in layout if g['kind']!='single'):remove.add(n['id'])
low=sum(n['id'] in remove and n['basic']['nodeName'].startswith('pl_grass_') for n in old)
while True:
 extra={n['id'] for n in old if n['basic']['parentId'] in remove};before=len(remove);remove|=extra
 if len(remove)==before:break
ns=[n for n in old if n['id'] not in remove];valid={n['id'] for n in ns}
assert all(not n['basic']['parentId'] or n['basic']['parentId'] in valid for n in ns)
assert sum(n['basic']['nodeName'].startswith('golden_geometry_') for n in ns)==150
# De-tint only the previous field before applying the wider, quieter continuous colour transition.
name='MatCoverTex_3193404.png';current=np.array(Image.open(io.BytesIO(raw[name])).convert('RGBA'))
basepath=p.parent/'scene.before-wheat-tint-20261110-163713.data'
with zipfile.ZipFile(basepath) as z:original=np.array(Image.open(io.BytesIO(z.read(name))).convert('RGBA'))
h,w=current.shape[:2];yy,xx=np.mgrid[:h,:w];X=(xx+.5)*256/w;Z=256-(yy+.5)*256/h
oldlayout=json.loads(Path('assets/reeds_v20/previous-layout.json').read_text());olddist=np.full((h,w),1e6)
for n in oldlayout:olddist=np.minimum(olddist,(X-n['pos']['x'])**2+(Z-n['pos']['z'])**2)
oldmask=np.sqrt(olddist)<5.9
rgb=current[:,:,:3].astype(float);rgb[oldmask]=original[:,:,:3][oldmask]
mask=np.zeros((h,w))
for g in layout:
 dist=np.sqrt((X-g['pos']['x'])**2+(Z-g['pos']['z'])**2)
 feather=6 if g['kind']=='group' else 4 if g['kind']=='small' else 2.5
 strength=1 if g['kind']=='group' else .65 if g['kind']=='small' else .25
 t=np.clip((dist-.3)/feather,0,1);mask=np.maximum(mask,strength*(1-t*t*(3-2*t)))
H=np.frombuffer(raw['HeightMap_3193404.data'],'<f4').reshape(257,257)*256
ix=np.clip(X.astype(int),0,255);iz=np.clip(Z.astype(int),0,255);fx=X-ix;fz=Z-iz
Y=(H[iz,ix]*(1-fx)+H[iz,ix+1]*fx)*(1-fz)+(H[iz+1,ix]*(1-fx)+H[iz+1,ix+1]*fx)*fz
t=np.clip((Y-37.8)/1,0,1);mask*=t*t*(3-2*t)
lum=rgb@np.array([.2126,.7152,.0722]);target=np.array([132,105,58])*np.clip(lum/75,.65,1.4)[:,:,None]
result=current.copy();result[:,:,:3]=np.clip(rgb*(1-mask[:,:,None])+target*mask[:,:,None],0,255).round().astype('uint8')
assert np.array_equal(result[(mask==0)&~oldmask],current[(mask==0)&~oldmask]);buf=io.BytesIO();Image.fromarray(result).save(buf,format='PNG')
shutil.copy2(p,O/'scene-before-finalize.data');d['nodeTransformDatas']=ns
with zipfile.ZipFile(p.with_suffix('.tmp'),'w',zipfile.ZIP_DEFLATED) as z:
 for i,v in entries:
  if i.filename=='SerializePcgData.json':v=json.dumps(d,ensure_ascii=False).encode()
  elif i.filename==name:v=buf.getvalue()
  z.writestr(i,v)
p.with_suffix('.tmp').replace(p)
(O/'finalize-report.json').write_text(json.dumps({'removed_nodes':len(remove),'removed_low_grass':low,'grass_roots':150,'triangles':284620,'old_triangles':359100,'feather':6,'all_parent_links_valid':True},indent=2))
print('Finalized150roots; removed lowgrass',low,'full obsolete subtree removed; height/other entries unchanged')
