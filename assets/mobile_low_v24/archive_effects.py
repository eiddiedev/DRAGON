from pathlib import Path
import subprocess,json
cli='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world';out=Path('assets/mobile_low_v24')
for name in ['slash','shield','hit','bolt','arrow','burst','frost','meteor']:
 p=subprocess.run([cli,'authoring','resource','archive','effect-combat-'+name,'--kind','effect','--prefab','dragon_fx_mobile_v22','--workspace-id','workspace_m293a9tg','--instance','awc-9b20f992-2970-49d0-81a6-b9162214102a','--json'],capture_output=True,text=True)
 (out/('effect-'+name+'-archive.json')).write_text(p.stdout)
 j=json.loads(p.stdout);print(name,j.get('ok'),flush=True)
 if not j.get('ok'):print(p.stdout,flush=True);break
