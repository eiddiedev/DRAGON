import json,pathlib,subprocess,concurrent.futures
D=pathlib.Path(__file__).resolve().parent;CLI='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world';I='awc-05d11ea9-0bb0-497a-b8fb-afba17e533ce'
def query(k):
 t=json.loads((D/(k+'-submit.json')).read_text())['data']['taskId']
 p=subprocess.run([CLI,'generation','status',t,'--instance',I,'--json'],text=True,capture_output=True,timeout=45)
 (D/(k+'-status.json')).write_text(p.stdout or p.stderr)
 return k,p.stdout or p.stderr
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as e:
 for k,s in e.map(query,['mage','ranger','warrior']):print(k,s)
