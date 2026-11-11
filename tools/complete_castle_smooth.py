"""Persist the verified continuous stone exterior replacement."""
import json, shutil, subprocess, zipfile
from pathlib import Path
from castle_smooth_cli import call, O, I
from castle_smooth_runtime_cli import call as rt
R=O.parents[1]
state=json.loads((O/'tone-state.json').read_text())['data']['result']
reload=json.loads((O/'reload-tone-state.json').read_text())['data']['result']
assert state==reload and state['exteriorMaterials']==12 and state['interiorMaterials']==8 and state['lights']==12
assert json.loads((O/'no-temp-final.json').read_text())['data']['residues']==[]
values=json.loads((O/'reload-values.json').read_text())['data']['result']
for g in values['roots']:
 for r in g['renderers']:
  inside=r['name'].startswith('castle_gi_')
  outside=g['name'] in ('城堡入口与钟塔精修样板','城堡塔楼与外围城墙精修')
  if inside or outside:
   expected=1.35 if inside else (.82 if r['name']=='clock_face_receiver.001' else .68)
   assert all(abs(m['power']-expected)<1e-5 for m in r['materials'])
rt(['runtime','stop'],'runtime-stop-final.json')
s=call(['scene','save','--request-id','castle-smooth-v7-final-20261111'],'save-final.json')
assert s['data']['status']=='committed' and not s['data']['hasUnsavedChanges']
subprocess.run(['python3',str(R/'tools/verify_castle_smooth.py')],check=True)
live=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project_lapv8fm0')
mirror=R/'editor_project/project_lapv8fm0'
shutil.copy2(live/'scene.data',O/'scene-final.data');shutil.copy2(live/'scene.data',mirror/'scene.data')
scene=json.loads(zipfile.ZipFile(live/'scene.data').read('SerializePcgData.json'))
for v in scene['runtimeScripts'].values():
 if v.get('referenceName') in ('castle_tone.lua','castle_smooth_display.lua') and v.get('referencePath'):
  p=mirror/'scripts'/v['referencePath'];p.parent.mkdir(parents=True,exist_ok=True);p.write_text(v['content'])
archives={k:json.loads((O/(k+'-archive.json')).read_text())['data'] for k in ('sample','expand','tone')}
roots={k:json.loads((O/(k+'-scene-import.json')).read_text())['data']['rootIDs'] for k in archives}
capacity=sum(d['artifact']['metadata']['capacity'] for d in archives.values())/1000
faces=sum(d['artifact']['metadata']['faceCount'] for d in archives.values())
call(['instance','stop'],'instance-stop-final.json')
report={'status':'complete_saved_verified','roots':roots,'archives':{k:d['uri'] for k,d in archives.items()},'capacity_points':capacity,'previous_replaced_capacity_points':157.097,'saved_capacity_points':157.097-capacity,'triangles':faces,'tone':state,'save_committed':True,'runtime_reload_verified':True,'own_instance_stopped':I,'paid_generation':False}
(O/'progress.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
note=f"""
## 2026-11-11 castle smooth continuous exterior v7
User rejected brick grid. Replaced ONLY previous sample -1910942728, expansion1525019778, tone81652010 with new smooth visual/tone packages. Roots{roots}. Archives{report['archives']}. Thin original-coordinate visual skins remove brick grid/individual wall bevels; side/rear main shell additionally covered. Original structural castle1743285643 and stairs -1788843370 remain; layout/collision/terrain/scripts verified. Windows/arch/roof slates/clock/trim preserved.
Sources tools/models/castle_smooth_*.py; assets/castle_smooth_v7 contains sources, full COLOR+DIRECT+INDIRECT baked textures, previews, receipts and native checks. No baked .68; fixed GI display selects12 exterior materials(.68 except clock .82), interior8at1.35 and12existinglights×1.4 preserved. Formal tone waits30secs and >=12 exterior. New authors castle_smooth_sample_v7/castle_smooth_expand_v7/castle_smooth_tone_v7 in workspace_vrztdtlb. Keep Chinese wrapper names for tone selection. All skins noncolliding, root world127,0,176 +180Y + exact imported normalization scale; wrappers identity.
Saved/reloaded verified, native exterior front/sides/rear and stair-to-hall passage checked, no temp hooks/camera. Replacement package total{capacity:.3f} capacity points and {faces} triangles vs157.097points previously, net reduction{157.097-capacity:.3f}; not whole-world total. No paid generation. Scene backup and repo mirror synced, own background instance stopped.
"""
h=R/'HANDOFF.md';h.write_text(h.read_text()+note)
(R/'docs/progress/2026-11-11-castle-smooth.md').write_text(note)
print(json.dumps(report,ensure_ascii=False))
