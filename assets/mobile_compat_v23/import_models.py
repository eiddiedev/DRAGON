import json,subprocess,pathlib
D=pathlib.Path('assets/mobile_compat_v23');items=json.loads((D/'model-conversion.json').read_text());cli='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world'
base=['--workspace-id','workspace_m293a9tg','--instance','1d1aa98e-dab4-4b8d-97c0-4ba4d2070f76','--prefab','dragon_fx_mobile_v22','--json']
for v in items:
 key='model-mobile-'+v['name']
 for op,args in [('import',['authoring','resource','model','import',key,'--glb',v['file']]),('archive',['authoring','resource','archive',key,'--kind','model'])]:
  r=subprocess.run([cli]+args+base,capture_output=True,text=True,timeout=180);(D/(v['name']+'-'+op+'.json')).write_text(r.stdout);d=json.loads(r.stdout);assert d.get('ok'),d
  if op=='archive':v['newUri']=d['data']['uri']
 print(v['name'],v['newUri'],flush=True)
 (D/'converted-uris.json').write_text(json.dumps(items,indent=2))
