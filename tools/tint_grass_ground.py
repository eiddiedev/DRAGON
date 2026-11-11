"""Paint only the planted grass footprint in the terrain colour data, with a 5m feather."""
from pathlib import Path
import io,zipfile,json,datetime,shutil
import numpy as np
from PIL import Image

p=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data'
backup=p.parent/('scene.before-wheat-tint-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.data');shutil.copy2(p,backup)
with zipfile.ZipFile(p) as z:entries=[(i,z.read(i)) for i in z.infolist()]
data={i.filename:v for i,v in entries};d=json.loads(data['SerializePcgData.json'])
plants=[n['pos'] for n in d['nodeTransformDatas'] if n['nodeName'].startswith(('golden_geometry_','golden_sample_'))]
name='MatCoverTex_3193404.png';a=np.array(Image.open(io.BytesIO(data[name])).convert('RGBA'));h,w=a.shape[:2]
y,x=np.mgrid[:h,:w];X=(x+.5)*256/w;Z=256-(y+.5)*256/h
dist=np.full((h,w),1e6)
for q in plants:dist=np.minimum(dist,(X-q['x'])**2+(Z-q['z'])**2)
dist=np.sqrt(dist);noise=.35*np.sin(X*1.7+Z*.8)+.22*np.sin(Z*2.1-X*.6)
t=np.clip((dist+noise-.25)/5,0,1);mask=1-t*t*(3-2*t)
H=np.frombuffer(data['HeightMap_3193404.data'],'<f4').reshape(257,257)*256
ix=np.clip(X.astype(int),0,255);iz=np.clip(Z.astype(int),0,255);fx=X-ix;fz=Z-iz
heights=(H[iz,ix]*(1-fx)+H[iz,ix+1]*fx)*(1-fz)+(H[iz+1,ix]*(1-fx)+H[iz+1,ix+1]*fx)*fz;gate=np.clip((heights-37.8)/1.0,0,1);mask*=gate*gate*(3-2*gate)
# Preserve local shading/detail while replacing hue only in the footprint.
rgb=a[:,:,:3].astype(float);lum=rgb@np.array([.2126,.7152,.0722]);variation=np.clip(lum/75,.65,1.4)
target=np.array([132,105,58])*variation[:,:,None]
b=a.copy();b[:,:,:3]=np.clip(rgb*(1-mask[:,:,None])+target*mask[:,:,None],0,255).round().astype('uint8')
assert np.array_equal(a[mask==0],b[mask==0]);out=io.BytesIO();Image.fromarray(b).save(out,format='PNG')
with zipfile.ZipFile(p.with_suffix('.tmp'),'w',zipfile.ZIP_DEFLATED) as z:
 for i,v in entries:z.writestr(i,out.getvalue() if i.filename==name else v)
p.with_suffix('.tmp').replace(p)
print('Ground painted; feather5m; height unchanged; backup',backup,'pixels',int(np.count_nonzero(mask)))
