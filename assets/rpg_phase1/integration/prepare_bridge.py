from pathlib import Path
D=Path(__file__).resolve().parent
s='\n'.join(l for l in (D/'latest_world_main.lua').read_text().splitlines() if not l.startswith('---@id ') and not l.startswith('---@referenceName '))
s=s.replace('local DEBUG_TELEPORT = true','local DEBUG_TELEPORT = false',1)
for condition in ['if near and DR.jump and DR.cool<=0 then','if near and DR.jump and DR.cool <= 0 then']:
 assert condition in s
 s=s.replace(condition,condition+"\n            if not CanRideDragon()then DR.cool=2;toast('完成龙巢圣所主线、缔结龙契后才能骑龙');return end",1)
assert s.rstrip().endswith('return {}')
s=s.rstrip()[:-len('return {}')]+(D/'bridge_api.lua').read_text()+'\nreturn {}\n'
(D/'dragon_world_bridge.body.lua').write_text(s)
print('Prepared bridge against latest saved world; no scene mutation.')
