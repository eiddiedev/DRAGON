import concurrent.futures,subprocess,json,pathlib
C='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world'
def one(i):
 r=subprocess.run([C,'asset','search',f'holy_canopy{i}_real','--scope','personal','--search-mode','name','--instance','55c37f10-22fb-496a-930a-07e79637a6cd','--json'],capture_output=True,text=True);x=json.loads(r.stdout);return x.get('data',{}).get('assets',[])
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as e:rows=list(e.map(one,range(3,11)))
a=sum(rows,[]);pathlib.Path('assets/holy_refine/import-real-verified.json').write_text(json.dumps({'ok':True,'data':{'assets':a}}));print([(x['name'],x['id']) for x in a])
