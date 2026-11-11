import subprocess,json,pathlib,sys
D=pathlib.Path(__file__).resolve().parent
CLI='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world'
I='awc-a3512914-49fc-47be-a17f-2aeb590ceea8'
P=pathlib.Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-508139d3-e199-4b21-805c-0050141438e3/ai-sessions/workspace_jcb1a5xe/wprefabs/dragon_rpg_restored')
def run(label,args):
 r=subprocess.run([CLI,*args,'--instance',I,'--json'],text=True,capture_output=True,timeout=110);(D/(label+'.json')).write_text(r.stdout or r.stderr)
 if r.returncode:raise RuntimeError(r.stdout or r.stderr)
 d=json.loads(r.stdout)
 if not d['ok']:raise RuntimeError(d)
 return d['data']
if __name__=='__main__':print(json.dumps(run(sys.argv[1],sys.argv[2:]),ensure_ascii=False))
