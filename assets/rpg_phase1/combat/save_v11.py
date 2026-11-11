from scenario import call
from cli import D,P,run
import json,shutil,hashlib
p=call('v11-reward-once','lua','eval','return GetProfile()','--script','dragon_rpg.lua')['result'];assert p['moon']==30 and len(p['rewards'])==3
print('three wins, three rewards only',flush=True)
logs=call('v11-logs-final','logs','--args','{"limit":1000}')
errors=[e for e in logs['entries']if e['type']in[0,4] and any(x in e['message'].lower()for x in ['luaexception','lua error','dragon_','dragon-'])]
(D/'v11-errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2));print('gameplay errors',len(errors),flush=True)
assert not errors
print(call('v11-clean','verifyNoTempHooks'),flush=True)
print(call('v11-runtime-stop','stop'),flush=True)
print(run('v11-save',['scene','save','--request-id','dragon-rpg-six-combat-fixes-v11-save-20261111']),flush=True)
shutil.copy2(P/'package/prefab.wprefab',D.parent/'dragon-rpg-combat-preview.wprefab')
for src in (P/'assets/effects').glob('effect-combat-*'):
 if src.name=='effect-combat-trail':continue
 shutil.copytree(src,D/'vfx/effects'/src.name,dirs_exist_ok=True)
pack=D.parent/'dragon-rpg-combat-preview.wprefab';print('package',pack.stat().st_size,hashlib.sha256(pack.read_bytes()).hexdigest(),flush=True)
print(run('v11-saved-reopen',['runtime','start']),flush=True)
(D/'runtime.json').write_text((D/'v11-saved-reopen.json').read_text())
