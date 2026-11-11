"""Patch only the canopy block, with editor project closed."""
from pathlib import Path
import json,zipfile,shutil,re,datetime
from lupa import LuaRuntime
p=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0';f=p/'scene.data';shutil.copy2(f,'assets/foliage_anchor/scene-before-'+datetime.datetime.now().strftime('%H%M%S')+'.data')
with zipfile.ZipFile(f) as z:entries=[(i,z.read(i)) for i in z.infolist()]
d=json.loads(next(v for i,v in entries if i.filename=='SerializePcgData.json'));binding='a87ebe50-812d-4151-a056-727a118aecbd';s=d['runtimeScripts'][binding]['content'];a=s.index('UI.foliage =');b=s.index('UI.reeds=',a);names=re.search(r'names = (\{.*?\}) \}',s[a:b]).group(1);new=Path('scripts/foliage_contact.lua').read_text().replace('__TREE_NAMES__',names);s=s[:a]+new+'\n'+s[b:]
lua=LuaRuntime();ok,err=lua.eval('function(s) local f,e=load(s);return f~=nil,e end')(s);assert ok,err
d['runtimeScripts'][binding]['content']=s
with zipfile.ZipFile(f.with_suffix('.tmp'),'w',zipfile.ZIP_DEFLATED) as z:
 for i,v in entries:z.writestr(i,json.dumps(d,ensure_ascii=False).encode() if i.filename=='SerializePcgData.json' else v)
f.with_suffix('.tmp').replace(f);(p/'scripts/modules/world_main.lua').write_text(s)
print('Only canopy block updated; syntax valid; scene and PCM retained')
