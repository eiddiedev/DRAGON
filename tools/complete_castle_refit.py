"""Finalize verified castle work, keeping saved scene and mirror consistent."""
from pathlib import Path
import json,shutil,zipfile,subprocess
from castle_cli import call,O,I
from castle_runtime_cli import call as runtime_call
R=O.parents[1]
p=json.loads((O/'level-road-native-position.json').read_text())['data']['result']
assert p['z']>170 and p['y']>72.2,p
assert json.loads((O/'no-temp-complete.json').read_text())['data']['residues']==[]
g=json.loads((O/'gi-display-complete.json').read_text())['data']['result'];assert g['materials']==8 and g['unsupported']==0,g
runtime_call(['runtime','stop'],'runtime-stop-complete.json')
saved=call(['scene','save','--request-id','castle-refit-final-flat-level-v10'],'save-complete.json')
assert saved['data']['status']=='committed' and not saved['data']['hasUnsavedChanges']
live=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project_lapv8fm0')
shutil.copy2(live/'scene.data',O/'scene-final.data')
mirror=R/'editor_project/project_lapv8fm0'
shutil.copy2(live/'scene.data',mirror/'scene.data')
d=json.loads(zipfile.ZipFile(live/'scene.data').read('SerializePcgData.json'))
for v in d['runtimeScripts'].values():
 if (v.get('referenceName')=='castle_baked_display.lua' or 'local CASTLE_NAMES' in (v.get('content') or '')) and v.get('referencePath'):
  dest=mirror/'scripts'/v['referencePath'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(v['content'])
subprocess.run(['python3',str(R/'tools/verify_castle_saved.py')],check=True)
a=json.loads((O/'archive-gate-level.json').read_text())['data'];root=json.loads((O/'import-scene-gate-level.json').read_text())['data']['rootIDs'][0]
call(['instance','stop'],'instance-stop-complete.json')
progress={'status':'complete_saved_verified','project':'project_lapv8fm0','scene_root':root,'author_workspace':'workspace_vrztdtlb','prefab':'castle_refit_v1','archive_uri':a['uri'],'archive_receipt':'archive-gate-level.json','wall_import':'import-gothic_wall-v5.json','wall_sha256':'0857b0da8812a5716a68c895354801de962175e6fb4d54793cbbbca618540a98','wall_scale':40.32526397705078,'user_latest_requirement':'Keep road flat; remove overhanging extension only. All terrain-following approach versions rejected.','road':{'front_z':159,'back_z':168.1,'top_y':72.24,'slope_degrees':0},'package_capacity':a['artifact']['metadata']['capacity']/1000,'capacity_scope':'Replacement assembly, not net increase or whole-world total','save_committed':True,'own_instance_stopped':I,'no_paid_generation':True,'verification':{'native_road_to_hall':p,'GI_materials':8,'GI_unsupported':0,'day_night_materials_equal':True,'unrelated_asset_roots_preserved':2102,'terrain_unchanged':True,'no_temp_hooks':True},'pending':[]}
(O/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2))
heading='\n## 2026-11-11 castle refit FINAL flat road\n'
text=f'''Latest user explicitly rejected warped terrain-following approach: ALL such ramp versions removed. Final wall uses flat road worldZ159..168.1, top72.24 (0°), rear extension0.45m closes threshold gap, top aligns interior to remove small lip. Left outer gate lower foot pulled back1m; no terrain edits. Final wall import-v5 and SHA0857b0da8812a5716a68c895354801de962175e6fb4d54793cbbbca618540a98, normalization40.325263977; do NOT reuse v1-v4. Main/tower resources remain main-v3 and original split towers.\nInstalled scene root{root}, archive-gate-level.json URI{a['uri']}. Scene save-complete.json committed/clean; scene-final.data backup and editor_project mirror synced. Native W from flat road161 passed intohall at {p}, no under-floorfall. GI display8 materials/unsupported0; day/night castle colors/emission stable, worlddaynightretained. verifyNoTempHooks clean. 2102 unrelated authored assets + all terrain bytes unchanged, including dragon and holy-tree/mushrooms. Own offscreen instance {I} stopped; other projects untouched.\nInterior old shelves/throne/backdrop/egg removed; original Tripo furniture retained. Statueorientation outwards, cornicesoverdoor, one blockinglamppost+glowremoved, warm4lights, actualGI8rooms. Allsource geometry preservedlayout; splitmodels<30k. Package capacity{progress['package_capacity']} (replacementassembly, NOT net or wholeworld). No paidgeneration/Tripo calls/starlight use. No gitcommit/push. Full details docs/progress/2026-11-11-castle-refit.md.\n'''
h=R/'HANDOFF.md';h.write_text(h.read_text()+heading+text)
doc=R/'docs/progress/2026-11-11-castle-refit.md';s=doc.read_text();s=s.replace('最终安装与验收状态见 assets/castle_refit_v1/progress.json；本段会在完成后更新。',f'最终版已安装并保存，根节点 {root}。从水平路面 z161 原生按 W 进入大厅，最终位置 {p}，未跌落地板。保存 committed 且无未保存修改；镜像已同步，本任务后台实例已停止。最终归档 archive-gate-level.json，墙体导入 import-gothic_wall-v5.json；历史 v1–v4 不再使用。')
doc.write_text(s)
print(json.dumps(progress,ensure_ascii=False,indent=2))
