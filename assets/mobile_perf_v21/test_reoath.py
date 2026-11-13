import subprocess,json
from pathlib import Path
c='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world';a=['--runtime-id','75598f1d-358c-4ac1-8c97-17c1e25834fc','--instance','awc-174c9874-132a-4d8d-a51c-9d3f7510bf60','--json']
def run(args):
 j=json.loads(subprocess.run([c,'runtime',*args,*a],capture_output=True,text=True,timeout=35).stdout);assert j.get('ok'),j;return j['data']
def wait():run(['input','keys','wait:450'])
def probe():return run(['js','eval','--file','assets/mobile_perf_v21/contract_probe.js'])['result']
records=[]
for i,(x,name)in enumerate([(.35,'mage'),(.44,'ranged'),(.26,'melee'),(.35,'mage'),(.26,'melee')]):
 if i:run(['input','mouse','click:0.63,0.505']);wait()
 before=probe();assert before['open'],before
 run(['input','mouse',f'click:{x},0.45']);wait();run(['input','mouse','click:0.65,0.78']);wait()
 after=probe();records.append({'iteration':i+1,'before':before,'after':after});print(records[-1],flush=True)
 Path('assets/mobile_perf_v21/reoath-input-results.json').write_text(json.dumps(records,indent=2));assert not after['open']and after['class']==name,after
