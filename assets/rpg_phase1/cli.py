import subprocess,json,pathlib,sys
BASE=pathlib.Path(__file__).resolve().parent
CLI='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world'
INSTANCE='awc-9076ac9e-cc15-4861-8ce6-081cbca8de10'
WORKSPACE='workspace_zpuv5vvs'
PREFAB='dragon_rpg_v1'
def run(label,args,timeout=100):
 p=subprocess.run([CLI,*args,'--instance',INSTANCE,'--workspace-id',WORKSPACE],capture_output=True,text=True,timeout=timeout)
 (BASE/(label+'.json')).write_text(p.stdout or p.stderr)
 if p.returncode:raise RuntimeError(p.stderr or p.stdout)
 return json.loads(p.stdout)
if __name__=='__main__':print(json.dumps(run(sys.argv[1],sys.argv[2:]),ensure_ascii=False))
