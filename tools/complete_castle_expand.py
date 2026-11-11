"""Save and mirror the verified tower/perimeter extension."""
import json, shutil, subprocess, zipfile
from pathlib import Path
from castle_expand_cli import call, O, I
from castle_expand_runtime_cli import call as runtime_call

R=O.parents[1]
walk=json.loads((O/'walk-final-position.json').read_text())['data']['result']
assert walk['z']>170 and abs(walk['y']-72.24)<.025
display=json.loads((O/'display-state-final.json').read_text())['data']['result']
assert display['unsupported']==0 and display['materials']>=7
assert json.loads((O/'no-temp-final.json').read_text())['data']['residues']==[]
assert json.loads((O/'reload-display-state.json').read_text())['data']['result']==display
runtime_call(['runtime','stop'],'runtime-stop-final.json')
saved=call(['scene','save','--request-id','castle-expand-towers-walls-final-20261111'],
           'save-complete.json')
assert saved['data']['status']=='committed' and not saved['data']['hasUnsavedChanges']
subprocess.run(['python3',str(R/'tools/verify_castle_expand.py')],check=True)
live=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project_lapv8fm0')
shutil.copy2(live/'scene.data',O/'scene-final.data')
mirror=R/'editor_project/project_lapv8fm0'
shutil.copy2(live/'scene.data',mirror/'scene.data')
scene=json.loads(zipfile.ZipFile(live/'scene.data').read('SerializePcgData.json'))
for v in scene['runtimeScripts'].values():
    if v.get('referenceName')=='castle_expand_display.lua' and v.get('referencePath'):
        dest=mirror/'scripts'/v['referencePath']
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(v['content'])
archive=json.loads((O/'archive.json').read_text())['data']
root=json.loads((O/'scene-import.json').read_text())['data']['rootIDs'][0]
capacity=archive['artifact']['metadata']['capacity']/1000
faces=archive['artifact']['metadata']['faceCount']
call(['instance','stop'],'instance-stop-complete.json')
progress=json.loads((O/'progress.json').read_text())
progress.update(status='complete_saved_verified',scene_root=root,archive_uri=archive['uri'],
    package_capacity_points=capacity,capacity_scope='Additive package, not whole world total',
    triangles=faces,layout_and_collision_preserved=True,native_walk_to_hall=walk,
    display=display,save_committed=True,own_instance_stopped=I,pending=[])
(O/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2))
note=f'''\n## 2026-11-11 remaining castle towers and perimeter extension\n
User accepted the entrance/left clock sample and requested the same style on remaining towers and outer walls.
Separate additive visual wrapper {root}; author castle_expand_v5/workspace_vrztdtlb.
Archive: {archive['uri']}. Actual added capacity {capacity:.3f} points; {faces} triangles.
Independent GLBs in assets/castle_expand_v5/towers and wall; unbaked Blender mothers, true COLOR+DIRECT+INDIRECT GI and bake evidence retained. Fixed display script applies only to this extension, not previous sample, stairs or interior. No paid generation.
Original castle1743285643, stairs-1788843370 and accepted sample-1910942728 protected; author transforms/physics, terrain, old scripts/settings unchanged by invariant audit. No new collision. Native stairs→gate→hall walk ended {walk}. Original windows, doors and left gate cutback preserved. Actual front/side/back/gate runtime views and reload checked. New GI runtime state {display}. Temporary camera destroyed before save.
Saved committed/clean; scene-final.data and editor_project mirror synced. Own background instance {I} stopped. This change does not reconstruct other main-body surfaces or room furnishings beyond the requested tower/perimeter scope.
'''
h=R/'HANDOFF.md';h.write_text(h.read_text()+note)
(R/'docs/progress/2026-11-11-castle-expand.md').write_text(note)
