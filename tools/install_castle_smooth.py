"""Replace only the three accepted visual/tone packages."""
import json,zipfile
from pathlib import Path
from castle_smooth_cli import call,O
packages=[('sample','-1910942728','城堡入口与钟塔精修样板'),('expand','1525019778','城堡塔楼与外围城墙精修'),('tone','81652010','城堡外暗内亮调色')]
archives={k:json.loads((O/(k+'-archive.json')).read_text())['data'] for k,_,_ in packages}
capacity=sum(d['artifact']['metadata']['capacity'] for d in archives.values())
assert capacity<=157097,capacity
live=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data')
assert json.loads(zipfile.ZipFile(live).read('SerializePcgData.json'))==json.loads(zipfile.ZipFile(O/'scene-before.data').read('SerializePcgData.json')),'Saved scene changed since baseline; re-read before modifying'
s=call(['runtime','status'],'runtime-before-install.json')
if s['data']['status']!='not_started':call(['runtime','stop','--runtime-id',s['data']['runtimeId']],'runtime-stop-before-install.json')
for k,old,name in packages:
 call(['scene','remove','--request-id','castle-smooth-v7-remove-'+k,'--',old],k+'-scene-remove.json')
 call(['scene','import','--uri',archives[k]['uri'],'--name',name,'--position','0,0,0','--request-id','castle-smooth-v7-import-'+k],k+'-scene-import.json')
call(['scene','save','--request-id','castle-smooth-v7-first-save'],'save-initial.json')
call(['runtime','start'],'runtime.json')
call(['runtime','lua','targets'],'targets.json')
