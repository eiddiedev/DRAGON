from cli import P,D,run
from pathlib import Path
import json,shutil
src=Path('/Users/bytedance/Documents/ChatGPT/createWLRD/output/backups/forest-authored-20261103-165638/ai-sessions/workspace_crystal-defense/assets/ui')
refs={}
for key,relative,name in [('Bow','ui-game/audio/hero-ranged.wav','原项目弓弦与箭声'),('Enemy','ui-audio-foes/audio/attack-basic.wav','影灵攻击'),('Hurt','ui-game/audio/hurt.wav','角色受伤')]:
 rid='audio-combat-original-'+key.lower();d=P/'assets/audio'/rid;d.mkdir(parents=True,exist_ok=True);shutil.copy2(src/relative,d/'audio.wav');(d/'meta.json').write_text(json.dumps(dict(schemaVersion=4,resourceId=rid,displayName=name,summary=name+'，复用参考项目原始音频'),ensure_ascii=False))
 refs[key]=run('audio-'+key,['authoring','resource','archive',rid,'--kind','audio','--prefab','dragon_rpg_restored','--workspace-id','workspace_jcb1a5xe'])
 print(key,refs[key],flush=True)
(D/'original-audio.json').write_text(json.dumps(refs))
f=D/'bind-audio.js';f.write_text('await scene.scripts.setParams('+json.dumps({'bindings':['n155:s:6329c644-9169-4c74-b1c2-6cf72ca3dae4'],'values':{k+'Sound':{'uri':v['uri']} for k,v in refs.items()}})+');return await scene.document.validate();')
print(run('bind-audio',['authoring','prefab','execute','dragon_rpg_restored','--file',str(f),'--workspace-id','workspace_jcb1a5xe']))
