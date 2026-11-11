"""Finalize only after actual sample visuals and native walking pass."""
import json,shutil,subprocess,zipfile
from pathlib import Path
from castle_sample_cli import call,O,I
from castle_sample_runtime_cli import call as runtime_call
R=O.parents[1]
walk=json.loads((O/'walk-final-position.json').read_text())['data']['result']
assert walk['z']>170 and abs(walk['y']-72.24)<.025,walk
display=json.loads((O/'display-state-final.json').read_text())['data']['result']
assert display['materials']==4 and display['unsupported']==0,display
assert json.loads((O/'no-temp-final.json').read_text())['data']['residues']==[]
runtime_call(['runtime','stop'],'runtime-stop-final.json')
saved=call(['scene','save','--request-id','castle-sample-entrance-clock-final-20261111'],'save-complete.json')
assert saved['data']['status']=='committed' and not saved['data']['hasUnsavedChanges']
subprocess.run(['python3',str(R/'tools/verify_castle_sample.py')],check=True)
live=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project_lapv8fm0')
shutil.copy2(live/'scene.data',O/'scene-final.data')
mirror=R/'editor_project/project_lapv8fm0';shutil.copy2(live/'scene.data',mirror/'scene.data')
scene=json.loads(zipfile.ZipFile(live/'scene.data').read('SerializePcgData.json'))
for v in scene['runtimeScripts'].values():
 if v.get('referenceName')=='castle_sample_display.lua' and v.get('referencePath'):
  dest=mirror/'scripts'/v['referencePath'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(v['content'])
a=json.loads((O/'archive-final.json').read_text())['data']
root=json.loads((O/'scene-import.json').read_text())['data']['rootIDs'][0]
call(['instance','stop'],'instance-stop-complete.json')
progress={'status':'sample_complete_saved_verified','scope':['entrance facade','left clock tower'],'scene_root':root,'archive_receipt':'archive-final.json','archive_uri':a['uri'],'package_capacity_points':a['artifact']['metadata']['capacity']/1000,'capacity_scope':'Additive sample package, not whole world total','triangles':a['artifact']['metadata']['faceCount'],'layout_and_collision_preserved':True,'native_walk_to_hall':walk,'display':display,'save_committed':True,'own_instance_stopped':I,'paid_generation':False,'pending':[]}
(O/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2))
note=f'''\n## 2026-11-11 entrance and LEFT clock tower lighter sample\nCompleted only the approved two-region sample; other towers/outerwall stay original. Additive visual wrapper {root}, author castle_sample_v3 workspace_vrztdtlb. Final archive {a['uri']}; receipt archive-final.json. Do not reuse initial archive with misplaced tall portal. Final entrance v4 follows original 4m jamb + pointed arch curve, real doorway unchanged. Clock v2 uses tighter slate color variation; same geometry as v1.\nFixed source BYTE_COLOR double-sRGB conversion, then real COLOR+DIRECT+INDIRECT GI rebaked using neutral sky approximation and existing fixtures. Models have no vertex colors. Formal castle_sample_display.lua handles only own4receivers; actual4materials, unsupported0. Fixed GI avoids repeated night shading; edit view retains standard PBR and can look darker than runtime. No global environment/old scripts altered. Old stairs and forecourt retain their original material display.\nAdded package {a['artifact']['metadata']['capacity']/1000:.3f} capacity points, {a['artifact']['metadata']['faceCount']}triangles. No paid generation. Native W walk ground→stairs→hall passed at {walk}. Saved committed/clean, scene-final.data backup + editor_project mirror synced; own instance stopped. All2097 authored roots,42 original castle/stair nodes, terrain bytes and prior script contents preserved. Host regenerates water/spawn/internal model IDs and serializes animated child poses; audit compares actual authored placement and spawn configuration, not generated ID equality.\nScreenshots final-portal.png / final-clock.png / final-wide.png are actual runtime inspection-camera views; final-native-stairs.png uses ordinary player camera. Inspector camera destroyed before cleanup. This is a review sample, not a claim that the whole castle now matches the concept.\n'''
h=R/'HANDOFF.md';h.write_text(h.read_text()+note)
(R/'docs/progress/2026-11-11-castle-sample.md').write_text(note)
