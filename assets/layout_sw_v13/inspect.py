import zipfile,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
p=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data'
with zipfile.ZipFile(p) as z:
 H=np.frombuffer(z.read('HeightMap_3193404.data'),'<f4').reshape(257,257)*256
 d=json.loads(z.read('SerializePcgData.json'))
O=Path('assets/layout_sw_v13');ns=d['nodeTransformDatas']
a=H[0:76,70:191];v=np.clip((a-25)/30*255,0,255).astype('uint8');im=Image.fromarray(v).convert('RGB').resize((1210,760));im=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM);dr=ImageDraw.Draw(im)
def xy(x,z):return ((x-70)*10,(75-z)*10)
for n in ns:
 b=n['basic'];x,z=b['pos']['x'],b['pos']['z']
 if not(70<x<190 and 0<z<75):continue
 c='gold' if b['nodeName'].startswith('golden_geometry') else 'green' if b['nodeName'].startswith('pl_grass_') else None
 if c:
  q=xy(x,z);dr.ellipse((q[0]-2,q[1]-2,q[0]+2,q[1]+2),fill=c)
for x in range(70,191,10):
 for z in range(0,76,10):dr.text(xy(x,z),f'{x},{z}: {H[z,x]:.0f}',fill='white')
x,y=xy(133,27);dr.ellipse((x-100,y-100,x+100,y+100),outline='red',width=3)
im.save(O/'terrain.png')
print('height grid, south rows first')
for z in range(5,41,5):print(z,[(x,round(float(H[z,x]),1)) for x in range(95,151,5)])
