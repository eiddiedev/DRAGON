from pathlib import Path
from lupa import LuaRuntime
base=Path(__file__).parent
out=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project_lapv8fm0/ai-sessions/workspace_zpuv5vvs/wprefabs/dragon_rpg_v1/scripts')
compile=LuaRuntime().eval('function(s,n) local f,e=load(s,n);return f~=nil,e end')
for path in out.glob('*.lua'):
 body=base/(path.stem+'.body.lua');ready=base/path.name
 if body.exists():
  head='\n'.join(path.read_text().splitlines()[:2])+'\n';text=head+body.read_text();ready.write_text(text)
 else:text=ready.read_text()
 ok,error=compile(text,path.name)
 if not ok:raise RuntimeError(error)
 path.write_text(text)
 print(path.name,len(text),'syntax OK')
