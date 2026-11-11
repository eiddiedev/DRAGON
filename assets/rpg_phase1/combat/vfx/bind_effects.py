import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));from cli import D,run
refs=json.loads((D/'vfx/archives.json').read_text());names={'slash':'SlashEffect','shield':'ShieldEffect','bolt':'BoltEffect','arrow':'ArrowEffect','burst':'BlastEffect','hit':'HitEffect','tell':'TellEffect','arena':'ArenaEffect','frost':'FrostEffect','meteor':'MeteorEffect'}
f=D/'vfx/bind.js';f.write_text('await scene.scripts.setParams('+json.dumps({'bindings':['n155:s:6329c644-9169-4c74-b1c2-6cf72ca3dae4'],'values':{names[k]:{'uri':v['uri']}for k,v in refs.items()}})+');return await scene.document.validate();')
print(run('fx-bind',['authoring','prefab','execute','dragon_rpg_restored','--file',str(f),'--workspace-id','workspace_jcb1a5xe']))
