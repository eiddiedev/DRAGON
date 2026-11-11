"""Save and record the verified, separate entrance addition."""
import json, shutil, subprocess
from pathlib import Path
from castle_entry_cli import call, O, I
from castle_entry_runtime_cli import call as runtime_call

R=O.parents[1]
def result(name): return json.loads((O/name).read_text())['data']['result']
walk=result('walk-final-position.json')
left=result('forecourt-left-short-position.json')
right=result('forecourt-right-short-position.json')
assert walk['z']>170 and abs(walk['y']-72.24)<.02
assert all(abs(p['y']-72.24)<.02 and p['z']>164 for p in (left,right))
assert json.loads((O/'no-temp-final.json').read_text())['data']['residues']==[]
runtime_call(['runtime','stop'],'runtime-stop-complete.json')
saved=call(['scene','save','--request-id','castle-entry-stairs-forecourt-final-20261111'],'save-complete.json')
assert saved['data']['status']=='committed' and not saved['data']['hasUnsavedChanges']
live=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data')
shutil.copy2(live,O/'scene-final.data')
shutil.copy2(live,R/'editor_project/project_lapv8fm0/scene.data')
subprocess.run(['python3',str(R/'tools/verify_castle_entry.py')],check=True)
a=json.loads((O/'archive-hidden.json').read_text())['data']
root=json.loads((O/'scene-import.json').read_text())['data']['rootIDs'][0]
call(['instance','stop'],'instance-stop-complete.json')
progress={'status':'complete_saved_verified','project':'project_lapv8fm0','scene_root':root,'archive_uri':a['uri'],'archive_receipt':'archive-hidden.json','prefab':'castle_entry_v2','author_workspace':'workspace_vrztdtlb','addition_capacity':a['artifact']['metadata']['capacity']/1000,'triangles':a['artifact']['metadata']['faceCount'],'stairs':{'width':4.6,'rise':.12,'count':12,'start_z':155.7,'landing_z':159,'landing_y':72.24},'forecourt_y':72.24,'removed_sundial':-1084074086,'preserved_spawn_sundial':194003353,'native_walk':walk,'left_floor_walk':left,'right_floor_walk':right,'save_committed':True,'paid_generation':False,'own_instance_stopped':I,'pending':[]}
(O/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2))
note=f'''\n## 2026-11-11 castle entrance stairs and stone forecourt\nAdded a separate entry assembly root {root}; existing castle root1743285643 untouched. Final archive archive-hidden.json URI{a['uri']}. Twelve low .12m risers (last rise meets existing landing), width4.6m, connects ground to flat road72.24. Two clipped flat stone forecourt sides fill the area before statues, including old sundial position117.5,162.5. Removed ONLY castle sundial -1084074086; original spawn sundial194003353 retained.\nVisible stairs/floor collision OFF; separate collision node n3 physics ON, appearance visible:false. Transparency:0 alone DID NOT hide the renderer; initial archive.json is superseded. Native W4500 from ground155.3 through stairs to hall175 passed, y72.242. Left and right native forward walks on forecourt passed at y72.242. Actual stairs-final.png and forecourt-left-inspect.png visually inspected. A long lateral probe ran outside the clipped forecourt edge atz159.44; that is not a floor traversal pass, and the perimeter is not enclosed by this addition. No temp hooks.\nSave committed/clean, scene-final.data and editor_project mirror synced. 2097 original asset roots, terrain bytes and runtime script contents unchanged. New package4.592capacity points,4392triangles; this is addition package cost, not total world capacity. No paid generation. Own instance stopped. Source tools/models/castle_entry_v2.py and assembly helper preserved.\n'''
h=R/'HANDOFF.md';h.write_text(h.read_text()+note)
(R/'docs/progress/2026-11-11-castle-entry.md').write_text(note)
