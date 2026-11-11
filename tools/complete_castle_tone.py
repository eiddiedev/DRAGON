"""Persist the verified castle-only exposure and indoor light adjustment."""
import json, shutil, subprocess, zipfile
from pathlib import Path
from castle_tone_cli import call, O, I
from castle_tone_runtime_cli import call as rt
R=O.parents[1]
state=json.loads((O/'tone-state.json').read_text())['data']['result']
reload=json.loads((O/'reload-tone-state.json').read_text())['data']['result']
assert state==reload and state['exteriorMaterials']==11 and state['interiorMaterials']==8 and state['lights']==12
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
s=call(['scene','save','--request-id','castle-tone-v6-final-20261111'],'save-final.json')
assert s['data']['status']=='committed' and not s['data']['hasUnsavedChanges']
subprocess.run(['python3',str(R/'tools/verify_castle_tone.py')],check=True)
live=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project_lapv8fm0')
mirror=R/'editor_project/project_lapv8fm0'
shutil.copy2(live/'scene.data',O/'scene-final.data');shutil.copy2(live/'scene.data',mirror/'scene.data')
scene=json.loads(zipfile.ZipFile(live/'scene.data').read('SerializePcgData.json'))
for v in scene['runtimeScripts'].values():
 if v.get('referenceName')=='castle_tone.lua' and v.get('referencePath'):
  p=mirror/'scripts'/v['referencePath'];p.parent.mkdir(parents=True,exist_ok=True);p.write_text(v['content'])
archive=json.loads((O/'archive.json').read_text())['data']
root=json.loads((O/'scene-import.json').read_text())['data']['rootIDs'][0]
call(['instance','stop'],'instance-stop-final.json')
report={'status':'complete_saved_verified','root':root,'author':'castle_tone_v6','workspace':'workspace_vrztdtlb','archive':archive['uri'],'capacity_points':archive['artifact']['metadata']['capacity']/1000,'triangles':0,'new_textures':0,'tone':state,'preserved_original_layout_and_scripts':True,'save_committed':True,'runtime_reload_verified':True,'own_instance_stopped':I,'paid_generation':False}
(O/'progress.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
note=f'''\n## 2026-11-11 castle exterior darker / interior brighter\nUser requested a modest darkening of the accepted facade/towers/wall and brighter indoor lights. Added zero-geometry formal controller {root}, author castle_tone_v6, archive {archive['uri']}. Preserve this controller when reimporting castle groups; it selects their exact Chinese wrapper names and the eight explicit castle_gi_* receivers. Exterior GI power0.68, clock face0.82, interior GI power1.35; twelve existing indoor PointLights multiplied1.4 (eight site_light positions + four named fixtures), no additional lights. Existing private GI clones are adjusted after owners initialize; originals restored on destroy; stops scanning after all19materials+12lights found. This is runtime fixed-GI display exposure using existing full-GI textures, not a texture rebake or edit-view material change.\nAll2097 authored asset roots,56 protected castle nodes, terrain and original script definitions preserved. Only environment change from host serialization is session-local characterCubemap.m_FileID; GUID/path and all actual environment settings unchanged. Original world day/night untouched. Formal restart verified same selected counts and actual emission powers; no temp hooks. Before/after hall and wide same camera, library checked. Added archive capacity1.21points,0faces,no new textures,no paid generation. Saved committed/clean and repo mirror synced; own background instance stopped. Foreground RPG test instance was identified via runtime targets and not edited or stopped.\n'''
h=R/'HANDOFF.md';h.write_text(h.read_text()+note)
(R/'docs/progress/2026-11-11-castle-tone.md').write_text(note)
print(json.dumps(report,ensure_ascii=False))
