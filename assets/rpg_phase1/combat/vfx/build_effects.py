import sys,json,copy,shutil,math
from pathlib import Path
import numpy as np,trimesh
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));from cli import P,D
ROOT=P/'assets/effects';OUT=D/'vfx'
for stem in ['burst','trail']:
 b=OUT/(stem+'-template.json')
 if not b.exists():b.write_text((ROOT/f'effect-combat-{stem}/effect.json').read_text())
BASE=json.loads((OUT/'burst-template.json').read_text());TRAIL=json.loads((OUT/'trail-template.json').read_text())
def const(c,v):c.update(mode='constant',min=v,max=v,multiplier=v)
def col(g,c):g.update(mode='color',minColor=c,maxColor=c)
def fade(g,c):
 g['mode']='gradient'
 for k in ['minGradient','maxGradient']:
  g[k]['colorKeys']=[{'time':0,'color':c[:3]},{'time':1,'color':c[:3]}];g[k]['alphaKeys']=[{'time':0,'alpha':0},{'time':.08,'alpha':1},{'time':.35,'alpha':.8},{'time':1,'alpha':0}]
def subset(base,ids,name):
 j=copy.deepcopy(base);ns=j['nodeTransformDatas'];root=ns[0];root['basic']['nodeName']=name
 if 1 not in ids:root['effects'].pop('particleSystemData',None)
 j['nodeTransformDatas']=[root]+[n for n in ns[1:] if n['id'] in ids]
 return j
def compact(j,d,source):
 ed=j['nodeTransformDatas'][0]['effects']['effectData'];ps=[n['effects']['particleSystemData'] for n in j['nodeTransformDatas'] if 'particleSystemData'in n.get('effects',{})]
 mi=set();meshes=set()
 for p in ps:
  for k in ['material','trailMaterial']:
   if p['renderer'].get(k)is not None:mi.add(p['renderer'][k])
  for m in p['renderer'].get('meshes',[]):meshes.add(m['mesh'])
  if p['shape'].get('mesh')is not None:meshes.add(p['shape']['mesh'])
 mmap={m:i for i,m in enumerate(sorted(mi))};ed['materials']=[ed['materials'][m]for m in sorted(mi)]
 for i,m in enumerate(ed['materials']):m['material']=i
 for p in ps:
  for k in ['material','trailMaterial']:
   if p['renderer'].get(k)is not None:p['renderer'][k]=mmap[p['renderer'][k]]
 tex=set()
 def scan(x,remap=None):
  if isinstance(x,dict):
   if isinstance(x.get('texture'),int):
    if remap is None:tex.add(x['texture'])
    else:x['texture']=remap[x['texture']]
   for v in x.values():scan(v,remap)
  elif isinstance(x,list):
   for v in x:scan(v,remap)
 scan(ed['materials']);tm={m:i for i,m in enumerate(sorted(tex))};scan(ed['materials'],tm);ed['textures']=[ed['textures'][m]for m in sorted(tex)]
 mm={m:i for i,m in enumerate(sorted(meshes))};ed['meshes']=[ed['meshes'][m]for m in sorted(meshes)]
 for p in ps:
  for m in p['renderer'].get('meshes',[]):m['mesh']=mm[m['mesh']]
  if p['shape'].get('mesh')is not None:p['shape']['mesh']=mm[p['shape']['mesh']]
 refs={t['textureRefId']for t in ed['textures']}|{m['meshRefId']for m in ed['meshes']};j['resourceRefs']=[r for r in j['resourceRefs']if r['id']in refs]
 for r in j['resourceRefs']:
  f=d/r['pathOrUrl'];f.parent.mkdir(parents=True,exist_ok=True)
  if not f.exists():shutil.copy2(source/r['pathOrUrl'],f)
def prepare(j,color):
 for n in j['nodeTransformDatas']:
  p=n.get('effects',{}).get('particleSystemData')
  if not p:continue
  m=p['main'];m['maxParticles']=64;m['loop']=False;m['prewarm']=False;m['playOnAwake']=True
  col(m['startColor'],color);p['colorOverLifetime']['enabled']=True;fade(p['colorOverLifetime']['color'],[1,1,1,1])
  for b in p['emission']['bursts']:const(b['count'],min(20,b['count']['max']))
 def recolor(x):
  if isinstance(x,dict):
   if 'colorKeys'in x:
    for k in x['colorKeys']:k['color']=[1,1,1]
   for v in x.values():recolor(v)
  elif isinstance(x,list):
   for v in x:recolor(v)
 # Trail template has rainbow gradients: neutralise before tint.
 for n in j['nodeTransformDatas']:
  p=n.get('effects',{}).get('particleSystemData')
  if p:recolor(p['trails']);recolor(p['colorOverLifetime'])
def arcmesh(path):
 vs=[];uv=[];faces=[]
 for i in range(49):
  t=i/48;a=-1.2+t*2.4;width=.46*math.sin(math.pi*t)**.7+.015
  for r,v in [(1.5-width,0),(1.5,1)]:vs.append([math.sin(a)*r,.15*math.sin(a),math.cos(a)*r]);uv.append([t,v])
  if i<48:
   a0=2*i;faces.extend([[a0,a0+2,a0+1],[a0+1,a0+2,a0+3]])
 mesh=trimesh.Trimesh(vertices=vs,faces=faces,process=False);mesh.visual=trimesh.visual.TextureVisuals(uv=np.array(uv));path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(trimesh.Scene(mesh).export(file_type='glb'))
configs=[('burst','奥术星爆',[2,3,4,5,9,10],[.58,.07,1,1]),('hit','命中火花',[2,3,5],[1,.66,.22,1]),('slash','金色弧刃',[5,9],[1,.28,.035,1]),('shield','守护震波',[5,9,10],[1,.42,.04,1]),('tell','敌袭预警',[9],[1,.22,.08,.7]),('arena','试炼法阵边界',[9],[.25,.65,1,.65]),('bolt','奥术飞弹',None,[.22,.12,1,1]),('arrow','疾风箭迹',None,[.06,1,.38,1]),('frost','霜星冲击',[2,3,4,5,9,10],[.04,.75,1,1]),('meteor','陨星冲击',[2,3,4,5,9,10],[1,.16,.025,1])]
for stem,name,ids,color in configs:
 d=ROOT/f'effect-combat-{stem}';d.mkdir(parents=True,exist_ok=True)
 istrail=ids is None;j=copy.deepcopy(TRAIL)if istrail else subset(BASE,ids,name);j['nodeTransformDatas'][0]['basic']['nodeName']=name;prepare(j,color)
 for n in j['nodeTransformDatas']:
  p=n.get('effects',{}).get('particleSystemData')
  if not p:continue
  m=p['main'];nid=n['id']
  if istrail:
   m['loop']=True;m['duration']=.8;m['maxParticles']=64
   const(m['startLifetime'],.20 if stem=='arrow'else .3)
   if nid==1:const(p['emission']['rateOverDistance'],8);const(m['startSizeX'],.045)
   if nid==2:const(p['emission']['rateOverTime'],30);const(m['startSizeX'],.2 if stem=='arrow'else .5);const(m['startSpeed'],.15)
   if nid==3:
    p['renderer']['renderMode']='none';p['renderer']['material']=0
    p['trails']['sizeAffectsWidth']=False;const(m['startLifetime'],1);const(m['startSizeX'],.2)
    const(p['trails']['lifetime'],.16 if stem=='arrow'else .25);const(p['trails']['widthOverTrail'],.13 if stem=='arrow'else .28)
   continue
  if stem=='hit':
   const(m['startLifetime'],.28 if nid!=5 else .45);const(m['startSizeX'],.08 if nid==5 else(.28 if nid==3 else .12));const(m['startSpeed'],3 if nid!=3 else 0)
   for b in p['emission']['bursts']:const(b['count'],1 if nid==3 else 9)
  if stem in ['slash','tell','arena'] and nid==9:
   m['startRotation3D']=True
   for k in ['startRotationX','startRotationY','startRotationZ']:const(m[k],0)
   p['rotationOverLifetime']['enabled']=False;p['renderer']['alignment']='local'
   const(m['startSizeX'],1);p['sizeOverLifetime']['enabled']=False
   const(m['startLifetime'],.38 if stem=='slash' else(.8 if stem=='tell'else 1.1))
   m['maxParticles']=4
  if stem=='arena':m['loop']=True;m['duration']=1
 if stem=='slash':
  ed=j['nodeTransformDatas'][0]['effects']['effectData'];arcmesh(d/'meshes/crescent.glb');rid=max(r['id']for r in j['resourceRefs'])+1
  j['resourceRefs'].append({'id':rid,'resourceType':1,'pathOrUrl':'meshes/crescent.glb'});ed['meshes'][0]={'meshRefId':rid,'meshIndex':0}
  mat=ed['materials'][7];mat['properties']['base']['rotation']=0;mat['properties']['base']['strength']=3.2;mat['properties']['base2']['texture']['texture']=None;mat['properties']['disturbance1']['uStrength']=.08
  mat['properties']['disturbance1']['vStrength']=0;mat['properties']['disturbance1']['uStrength']=0;mat['properties']['base']['texture']['texture']=None
 if istrail:
  ed=j['nodeTransformDatas'][0]['effects']['effectData'];bed=copy.deepcopy(BASE['nodeTransformDatas'][0]['effects']['effectData']);off=len(ed['textures']);rid=max(r['id']for r in j['resourceRefs']);refmap={r['id']:rid+i+1 for i,r in enumerate(BASE['resourceRefs'])}
  for r in BASE['resourceRefs']:
   rr=copy.deepcopy(r);rr['id']=refmap[r['id']];j['resourceRefs'].append(rr);f=d/rr['pathOrUrl'];f.parent.mkdir(parents=True,exist_ok=True)
   if not f.exists():shutil.copy2(ROOT/'effect-combat-burst'/rr['pathOrUrl'],f)
  for t in bed['textures']:t['textureRefId']=refmap[t['textureRefId']]
  ed['textures']+=bed['textures'];mat=copy.deepcopy(TRAIL['nodeTransformDatas'][0]['effects']['effectData']['materials'][0]);mat['properties']['base']['texture']['texture']=BASE['nodeTransformDatas'][0]['effects']['effectData']['materials'][1]['properties']['base']['texture']['texture'];mat['material']=len(ed['materials'])
  def shifttex(x):
   if isinstance(x,dict):
    if isinstance(x.get('texture'),int):x['texture']+=off
    for v in x.values():shifttex(v)
   elif isinstance(x,list):
    for v in x:shifttex(v)
  shifttex(mat);ed['materials'].append(mat)
  n=copy.deepcopy(BASE['nodeTransformDatas'][2]);n['id']=4;n['basic']['nodeName']='CometCore';p=n['effects']['particleSystemData'];p['renderer']['material']=mat['material'];p['main']['loop']=True;p['main']['duration']=.8;p['main']['maxParticles']=4;p['main']['simulationSpace']='local';const(p['main']['startLifetime'],1);const(p['main']['startSizeX'],.65 if stem=='bolt'else .22);const(p['main']['startSpeed'],0);col(p['main']['startColor'],color);p['shape']['enabled']=False
  p['colorOverLifetime']['enabled']=True;fade(p['colorOverLifetime']['color'],[1,1,1,1]);j['nodeTransformDatas'].append(n)
 for mat in j['nodeTransformDatas'][0]['effects']['effectData']['materials']:
  mat['properties']['base']['color']=color[:3]+[1]
  mat['properties']['base']['strength']=1.6 if stem in ['burst','bolt','arrow']else 1.25
  if istrail:mat['properties']['base']['desaturate']=1
 if stem=='slash':
  for n in j['nodeTransformDatas']:
   p=n.get('effects',{}).get('particleSystemData')
   if p and n['id']==5:
    const(p['main']['startLifetime'],.42);const(p['main']['startSpeed'],3.5);const(p['main']['startSizeX'],.1);p['shape']['radius']=.55
    for b in p['emission']['bursts']:const(b['count'],16)
  second=copy.deepcopy(next(n for n in j['nodeTransformDatas']if n['id']==9));second['id']=12;second['basic']['nodeName']='BladeEcho';second['basic']['pos']['y']=.10
  p=second['effects']['particleSystemData'];const(p['main']['startDelay'],.045);const(p['main']['startSizeX'],.92);const(p['main']['startLifetime'],.3);col(p['main']['startColor'],[1,.9,.65,.65]);j['nodeTransformDatas'].append(second)
 if stem in ['burst','frost','meteor']:
  for n in j['nodeTransformDatas']:
   p=n.get('effects',{}).get('particleSystemData')
   if not p:continue
   if n['id']==5:
    col(p['main']['startColor'],[.15,.8,1,1]if stem!='meteor'else[1,.6,.025,1]);const(p['main']['startSpeed'],5)
    const(p['main']['startSizeX'],.2)
    for b in p['emission']['bursts']:const(b['count'],40)
   if n['id']==3:const(p['main']['startSizeX'],2.2)
   if n['id']==9:const(p['main']['startSizeX'],2.4)
 if istrail:
  ed=j['nodeTransformDatas'][0]['effects']['effectData'];old=ed['materials'][2];safe=copy.deepcopy(ed['materials'][0]);safe['material']=2;safe['properties']['base']=copy.deepcopy(old['properties']['base']);safe['properties']['mask']=copy.deepcopy(old['properties']['mask']);safe['properties']['base']['strength']=1.3;ed['materials'][2]=safe
 compact(j,d,ROOT/('effect-combat-trail'if istrail else 'effect-combat-burst'))
 (d/'effect.json').write_text(json.dumps(j,ensure_ascii=False));(d/'meta.json').write_text(json.dumps({'resourceId':d.name,'displayName':name},ensure_ascii=False))
 print(d.name,len(j['nodeTransformDatas']),len(j['resourceRefs']))
