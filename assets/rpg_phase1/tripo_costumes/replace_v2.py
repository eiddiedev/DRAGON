from cli import run,D
from pathlib import Path
import shutil,json
P=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-508139d3-e199-4b21-805c-0050141438e3/ai-sessions/workspace_jcb1a5xe/wprefabs/dragon_rpg_ui_v2')
a=['--workspace-id','workspace_jcb1a5xe'];new=[]
for k,root in [('mage','n163'),('ranger','n183'),('warrior','n203')]:
 inspection=run(k+'-old-inspect-v2',['authoring','prefab','read','dragon_rpg_ui_v2','assets.inspectModel','--args',json.dumps([{'root':root}]),*a])
 res=P/'assets/models'/('model-tripo-'+k);shutil.copy2(res/'blender/rigged.glb',res/'topology/model.glb')
 archived=run(k+'-archive-v2',['authoring','resource','archive','model-tripo-'+k,'--kind','model','--prefab','dragon_rpg_ui_v2',*a]);new.append((root,archived['uri']))
 print(k,archived['uri'],flush=True)
read=run('read-v2',['authoring','prefab','read','dragon_rpg_ui_v2',*a]);s='const result=[];\n'
for root,uri in new:s+='result.push(await scene.assets.replaceModel('+json.dumps({'root':root,'replacement':uri})+'));\n'
s+='return result;';(D/'replace-v2.js').write_text(s)
print(run('replace-v2',['authoring','prefab','execute','dragon_rpg_ui_v2','--file',str(D/'replace-v2.js'),'--revision',read['revision'],*a]))
print(run('validate-v2',['authoring','prefab','validate','dragon_rpg_ui_v2',*a]))
print(run('build-v2',['authoring','prefab','build','dragon_rpg_ui_v2',*a]))
print(run('archive-v2',['authoring','result','archive','dragon_rpg_ui_v2','--name','龙眠职业服饰验证',*a]))
