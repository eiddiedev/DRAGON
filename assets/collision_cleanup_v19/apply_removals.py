import json,subprocess
from pathlib import Path
c='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world';a=['--instance','ecd18598-94c9-43e9-ae42-cbdacfb6e2dc','--json']
n=json.load(open('assets/collision_cleanup_v19/remove-plan.json'))
for i in range(0,len(n),40):
 rid='v19-remove-'+str(i//40);args=json.dumps({'rootIDs':[str(x['id']) for x in n[i:i+40]]})
 r=subprocess.run([c,'scene','remove','--args',args,'--request-id',rid,*a],capture_output=True,text=True);j=json.loads(r.stdout)
 if not j.get('ok'):j=json.loads(subprocess.run([c,'scene','operation',rid,*a],capture_output=True,text=True).stdout)
 Path('assets/collision_cleanup_v19/'+rid+'.json').write_text(json.dumps(j));print(rid,j.get('data',{}).get('status'),flush=True)
 if j.get('data',{}).get('status')!='committed':raise SystemExit('unconfirmed stop')
