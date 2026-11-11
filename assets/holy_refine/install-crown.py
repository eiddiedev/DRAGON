from pathlib import Path
import json,zipfile,copy,shutil,time
P=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0';O=Path('assets/holy_refine')
shutil.copy2(P/'scene.data',O/f'before-crown-{int(time.time())}.data')
with zipfile.ZipFile(P/'scene.data') as z:e={n:z.read(n) for n in z.namelist()}
d=json.loads(e['SerializePcgData.json']);before=copy.deepcopy(d)
assets={a['name'].replace('_crown',''):a for a in json.load(open(O/'import-crown.json'))['data']['assets']}
for n in d['nodeTransformDatas']:
 name=n['basic']['nodeName']
 if name in assets:
  a=assets[name];uri=a['resource']['uri'];n['basic']['scale']=a['scale'];n['editor']['assetData']={'uri':uri,'assetID':a['id']};n['resource']['aigcModelData']['uri']=uri;n['resource']['glbSliceData']['sourceUri']=uri
assert [n for n in before['nodeTransformDatas'] if n['basic']['nodeName'] not in assets]==[n for n in d['nodeTransformDatas'] if n['basic']['nodeName'] not in assets]
e['SerializePcgData.json']=json.dumps(d,ensure_ascii=False).encode()
with zipfile.ZipFile(P/'scene.data','w',zipfile.ZIP_DEFLATED) as z:
 for n,b in e.items():z.writestr(n,b)
print('Crown applied; user widened trunk and all other data preserved.')
