import json,pathlib,subprocess,sys
D=pathlib.Path(__file__).resolve().parent;CLI='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world';I='awc-05d11ea9-0bb0-497a-b8fb-afba17e533ce'
def run(label,args):
 p=subprocess.run([CLI,*args,'--instance',I,'--json'],capture_output=True,text=True,timeout=100);(D/(label+'.json')).write_text(p.stdout or p.stderr)
 if p.returncode:raise RuntimeError(p.stdout or p.stderr)
 v=json.loads(p.stdout)
 if not v['ok']:raise RuntimeError(v)
 return v['data']
if __name__=='__main__':print(json.dumps(run(sys.argv[1],sys.argv[2:]),ensure_ascii=False))
