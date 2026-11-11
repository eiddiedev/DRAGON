import json,subprocess,pathlib
D=pathlib.Path(__file__).resolve().parent
CLI='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world'
I='aedf143a-52aa-470d-9cdb-a14e500b1010';W='workspace_sbazsi67';F='dragon_noncombat'
P=pathlib.Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0/ai-sessions'/W/'wprefabs'/F
A=['--workspace-id',W]
def run(label,args):
 p=subprocess.run([CLI,*args,'--instance',I,'--json'],text=True,capture_output=True,timeout=100)
 (D/(label+'.json')).write_text(p.stdout or p.stderr)
 d=json.loads(p.stdout)
 if not d.get('ok'):raise RuntimeError(d)
 return d['data']
if __name__=='__main__':
 import sys
 print(json.dumps(run(sys.argv[1],sys.argv[2:]),ensure_ascii=False))
