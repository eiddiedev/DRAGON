from pathlib import Path
import zipfile,json,copy,math,shutil,time,sys,numpy as np
P=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0';O=Path('assets/mushroom_grove')
with zipfile.ZipFile(P/'scene.data') as z:e={n:z.read(n) for n in z.namelist()}
d=json.loads(e['SerializePcgData.json']);before=copy.deepcopy(d);by={n['basic']['nodeName']:n for n in d['nodeTransformDatas']};template=by['mush']
hn=next(n for n in e if n.startswith('HeightMap_'));H=np.frombuffer(e[hn],'<f4').reshape(257,257)*256
spots=[(82,107,4.8),(73.5,113,4.0),(86,102.5,3.0),(78,102,1.25),(86.5,110.5,2.5),(77,108,2.8),(82,114,2.1),(74,103,1.8),(68.5,111,2.0),(69,117,2.2),(76,117,1.6),(87,116,1.5),(81,119,.85),(65.5,117,.85),(66,113,.9),(71,109,.75),(74,106,.8),(80,102.5,.65),(85,100.5,.8),(88,106,.7),(87,113,.75),(73,119,.7),(78.5,111,.75),(88,119,.65),(78,105,2.2),(78.5,108.5,3.2),(70,114.5,2.5),(71,117,1.1),(84.5,116.5,2.5),(84,119,1.2),(80,111,2.6),(68,108,.9)]
def ground(x,z):
 i,j=int(x),int(z);a,b=x-i,z-j;return float((H[j,i]*(1-a)+H[j,i+1]*a)*(1-b)+(H[j+1,i]*(1-a)+H[j+1,i+1]*a)*b)
report=[]
for i,(x,z,height) in enumerate(spots):
 name='mush' if i==0 else 'mush_'+str(i)
 n=by.get(name)
 if n is None:
  n=copy.deepcopy(template);n['id']=-1911001000-i;assert not any(v['id']==n['id'] for v in d['nodeTransformDatas']);d['nodeTransformDatas'].append(n)
 b=n['basic'];s=height/.901275634765625;y=ground(x,z)
 # Slightly embed feet on slopes; keep each whole cluster within fenced bounds.
 b['nodeName']=name;b['pos']={'x':x,'y':y-.04,'z':z};b['scale']=dict.fromkeys('xyz',s);ang=math.radians((i*137.5)%360);b['rot']={'x':0,'y':math.sin(ang/2),'z':0,'w':math.cos(ang/2)}
 n['physics']['triggerData']=[{'shape':'box','enabled':True,'center':{'x':0,'y':.5,'z':0},'size':{'x':1.7,'y':2,'z':1.9},'radius':.5,'height':2,'direction':1}]
 assert x-s*.5>61 and x+s*.5<91 and z-s*.5>98 and z+s*.5<122
 report.append({'name':name,'pos':b['pos'],'height':height,'jumpHeight':max(3,min(10,2+3*s/1.33144617))})
d['nodeTransformDatas']=[n for n in d['nodeTransformDatas'] if n['basic']['nodeName']!='beam_4']
sid='655bb578-1c21-4668-9bce-742316b5798b';s=(O/'scene_mushroom.lua').read_text()
d['runtimeScripts'][sid]['content']=s
mainid='a87ebe50-812d-4151-a056-727a118aecbd';main=d['runtimeScripts'][mainid]['content'];a=main.index('local function setupMush()');b=main.index('local function updateMush',a);part=main[a:b].replace('for i = 0, 5 do','for i = 0, 31 do').replace('for i = 0, 23 do','for i = 0, 31 do');main=main[:a]+part+main[b:];main=main.replace('---- 蘑菇林：踩中间的光圈被弹上天','---- 幽菇林：围栏内的蘑菇踩踏弹跳，越大弹得越高')
d['runtimeScripts'][mainid]['content']=main
for n in before['nodeTransformDatas']:
 if n['basic']['nodeName'] not in {'beam_4','mush',*[f'mush_{j}' for j in range(1,32)]}:assert n==next(v for v in d['nodeTransformDatas'] if v['id']==n['id'])
stage='--stage' in sys.argv
if not stage:shutil.copy2(P/'scene.data',O/f'before-{int(time.time())}.data')
e['SerializePcgData.json']=json.dumps(d,ensure_ascii=False).encode()
with zipfile.ZipFile(O/'scene-STAGED.data' if stage else P/'scene.data','w',zipfile.ZIP_DEFLATED) as z:
 for name,data in e.items():z.writestr(name,data)
for sid in ([] if stage else ['655bb578-1c21-4668-9bce-742316b5798b',mainid]):
 v=d['runtimeScripts'][sid];(P/'scripts'/v['referencePath']).write_text(v['content'])
if not stage:Path('assets/interactions_v1/main-sheep-tree-staged.lua').write_text(main)
(O/'layout.json').write_text(json.dumps(report,indent=2))
print('32 clusters; beam_4 removed; all unrelated nodes preserved. Heights',min(v['jumpHeight'] for v in report),max(v['jumpHeight'] for v in report))
