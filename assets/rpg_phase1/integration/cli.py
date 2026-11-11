from pathlib import Path
import subprocess,json,sys
D=Path(__file__).resolve().parent
CLI='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world'
I='214221c6-60f7-4a9b-86f5-6195094e46ee'
W='workspace_sbazsi67';F='dragon_phase1_merged'
P=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0/ai-sessions'/W/'wprefabs'/F

def run(label,args):
 r=subprocess.run([CLI,*args,'--instance',I,'--json'],capture_output=True,text=True,timeout=120)
 (D/(label+'.json')).write_text(r.stdout or r.stderr)
 j=json.loads(r.stdout);assert j.get('ok'),j
 return j['data']
if __name__=='__main__': print(json.dumps(run(sys.argv[1],sys.argv[2:]),ensure_ascii=False)[:6000])
