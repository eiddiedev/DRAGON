from cli import P,D
for name in ['dragon_rpg','dragon_rules','dragon_combat','dragon_combat_rules','dragon_fx']:
 p=P/'scripts'/(name+'.lua');body=(D/'vfx'/(name+'.body.lua'))if name=='dragon_fx'else D/(name+'.body.lua')
 header='\n'.join(p.read_text().splitlines()[:2])+'\n';p.write_text(header+body.read_text());(D/p.name).write_text(p.read_text());(D.parent/p.name).write_text(p.read_text())
