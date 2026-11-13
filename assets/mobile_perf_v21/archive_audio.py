import json,subprocess
from pathlib import Path
O=Path('assets/mobile_perf_v21');c='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world'
m=json.loads((O/'audio-manifest.json').read_text())
for i,v in enumerate(m):
 p=O/(v['resource']+'.json')
 if not p.exists():
  r=subprocess.run([c,'authoring','resource','archive',v['resource'],'--kind','audio','--prefab','dragon_v17','--workspace-id','workspace_l7e231w9','--instance','ecd18598-94c9-43e9-ae42-cbdacfb6e2dc','--json'],capture_output=True,text=True,timeout=120)
  p.write_text(r.stdout)
 j=json.loads(p.read_text());assert j.get('ok'),j
 v['uri']=j['data']['uri'];print(i+1,v['resource'],'archived',flush=True)
(O/'audio-manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
vals={v['var']:{'uri':v['uri']}for v in m}
(O/'bind-audio.js').write_text('return scene.scripts.setParams('+json.dumps({'bindings':['n155:s:6329c644-9169-4c74-b1c2-6cf72ca3dae4'],'values':vals})+');')
