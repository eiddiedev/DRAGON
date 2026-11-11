import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));from cli import run,D
out={}
for stem in ['burst','hit','slash','shield','tell','arena','bolt','arrow','frost','meteor']:
 a=['--prefab','dragon_rpg_restored','--workspace-id','workspace_jcb1a5xe']
 run('fx-check-'+stem,['authoring','resource','effect','check','effect-combat-'+stem,*a])
 r=run('fx-archive-'+stem,['authoring','resource','archive','effect-combat-'+stem,'--kind','effect',*a]);out[stem]=r;print(stem,json.dumps(r,ensure_ascii=False)[:900],flush=True)
 (D/'vfx/archives.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
