#!/usr/bin/env python3
"""A terrain-blended, asymmetric snow crag with a broad dragon perch."""
from pathlib import Path
import sys,zipfile,math,random,json
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/models'));sys.path.insert(0,str(ROOT/'tools'))
from glbw import Geo,write_glb
from refit_scene import sample
scene=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data'
with zipfile.ZipFile(scene) as z:
 hn=next(n for n in z.namelist() if n.startswith('HeightMap_'))
 terrain=np.frombuffer(z.read(hn),'<f4').reshape(257,257)*256
out=ROOT/'assets/refit_v8/dragon_peak_v8.glb'
# Stop inside the actual northern terrain edge rather than extending a floating
# circular skirt past z=256. Shared grid vertices keep the mountain watertight.
xs=np.linspace(112,216,97);zs=np.linspace(184,254.8,73)
x,z=np.meshgrid(xs,zs);base=sample(terrain,x,z)
xx=x-165;zz=z-234
angle=np.arctan2(zz,xx)
r=np.sqrt((xx/22)**2+(zz/15)**2)
# The perch has stable foot contact; irregularity increases down the rock face.
edge=r*(1+.09*np.sin(angle*3+.4)+.055*np.cos(angle*7))
t=np.clip((edge-.72)/1.25,0,1);fall=t*t*(3-2*t)
# Uphill along the dragon's facing direction: hind feet low, forefeet high.
yaw=math.radians(145)
forward=(x-157.7213109426018)*math.sin(yaw)+(z-244.39503658510694)*math.cos(yaw)
crest=111.8+np.clip((forward-5.4)/16.2,0,1)*6.48
peak=crest+(base-crest)*fall
# A pair of lower shoulder ridges breaks the old cone/cylinder silhouette.
for cx,cz,rx,rz,height in [(145,236,16,12,99),(186,231,17,14,93),(165,211,15,18,86)]:
 rr=((x-cx)/rx)**2+((z-cz)/rz)**2
 shoulder=base+(height-base)*np.maximum(0,1-rr)**1.5
 peak=np.maximum(peak,shoulder)
rocknoise=(np.sin(x*.65+z*.19)*.8+np.sin(x*1.31-z*.7)*.4+np.sin(z*1.9)*.22)
noise_weight=np.clip((edge-.72)*3,0,1)*np.clip((peak-base)/8,0,1)
# Broad fractured shelves read as rock at gameplay distance, rather than a
# smooth bell-shaped mound. Keep the inner perch perfectly level for feet.
terrace=1.35*np.sin(peak*.78+np.sin(angle*3)*.8)
flutes=1.6*np.cos(angle*11+peak*.025)
y=peak+(rocknoise+terrace+flutes)*noise_weight
# Fade the boundary into today's terrain, including the clipped north edge.
border=np.minimum.reduce([(x-xs[0])/5,(xs[-1]-x)/5,(z-zs[0])/5,(zs[-1]-z)/3])
blend=np.clip(border,0,1);blend=blend*blend*(3-2*blend)
y=base-.12+(y-base+.12)*blend
verts=np.stack((x-165,z-234,y),axis=-1)
dz,dx=np.gradient(y,zs,xs);normal=np.stack((-dx,-dz,np.ones_like(y)),axis=-1);normal/=np.linalg.norm(normal,axis=-1)[...,None]
geo=Geo([[(0,'#20262f'),(.30,'#4a5564'),(.55,'#7b8b9c'),(.73,'#b4c4ce'),(.86,'#d5e4ea'),(1,'#f3f6f6')]])
for j in range(len(zs)-1):
 for i in range(len(xs)-1):
  ids=[(j,i),(j,i+1),(j+1,i+1),(j+1,i)]
  if max(y[a,b]-base[a,b] for a,b in ids)<.12:continue
  ps=[verts[a,b] for a,b in ids];ns=[normal[a,b] for a,b in ids]
  tone=[]
  for a,b in ids:
   snow=np.clip((y[a,b]-88)/15,0,1)*np.clip((normal[a,b,2]-.45)/.4,0,1)
   strata=.03*np.sin(y[a,b]*1.5+x[a,b]*.08)
   tone.append(float(np.clip(.28+.15*normal[a,b,2]+snow*.53+strata,.08,.96)))
  geo.tri(ps[0],ps[1],ps[2],tuple(tone[:3]),0,normals=ns[:3])
  geo.tri(ps[0],ps[2],ps[3],(tone[0],tone[2],tone[3]),0,normals=[ns[0],ns[2],ns[3]])
# Fractured outcrops: irregular tilted faces, recessed seams and snow caps.
# Foreclaw supports follow the exact authored contact offsets at home yaw 145.
rng=random.Random(310)
def block(cx,cz,top,rx,rz,depth,seed):
 local=random.Random(seed);n=11
 angles=np.arange(n)*math.tau/n
 radii=[local.uniform(.83,1.1) for _ in range(n)]
 rings=[]
 for factor,drop in [( .82,0),(1,.7),(1.25,depth*.65),(1.6,depth)]:
  rings.append([np.array([cx-165+math.cos(a)*rx*r*factor,cz-234+math.sin(a)*rz*r*factor,top-drop]) for a,r in zip(angles,radii)])
 center=np.array([cx-165,cz-234,top])
 for k in range(n):
  q=(k+1)%n
  geo.tri(center,rings[0][k],rings[0][q],(.77,.62+rng.random()*.18,.65+rng.random()*.15),0)
 for j in range(3):
  for k in range(n):
   q=(k+1)%n;t=.17+rng.random()*.24
   geo.quad(rings[j][k],rings[j+1][k],rings[j+1][q],rings[j][q],t,0,ref=center-np.array([0,0,depth*.5]))
 # Thin snow crust, broken at a few edge sectors rather than uniform icing.
 for k in range(n):
  if k%4==seed%4:continue
  q=(k+1)%n
  a=center+np.array([0,0,.035]);b=center+(rings[0][k]-center)*.78+np.array([0,0,.035]);c=center+(rings[0][q]-center)*.78+np.array([0,0,.035])
  geo.tri(a,b,c,.92,0)
r=math.radians(145)
contacts=[]
for side in [-1,1]:
 a,b=side*.08*54,.40*54
 cx=157.7213109426018+a*math.cos(r)+b*math.sin(r)
 cz=244.39503658510694-a*math.sin(r)+b*math.cos(r)

 contacts.append([cx,118.28,cz])
# A connected, broad outcrop supports both foreclaws; its flared base blends
# into the crest instead of reading as isolated cylinders attached to the wall.
cx=sum(p[0] for p in contacts)/2;cz=sum(p[2] for p in contacts)/2
# The support is part of the continuous sloping crest, without a separate pedestal.
write_glb(out,geo,name='dragon_peak_v8',rough=.96)
print('Wrote',out)

(out.parent/'peak-contact-plan.json').write_text(json.dumps({'foreclaws':contacts,'root':[157.7213109426018,111.8,244.39503658510694],'yaw':145},indent=2))
