import pathlib,subprocess,json,sys
D=pathlib.Path(__file__).resolve().parent
CLI='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world'
def run(label,args,timeout=90):
 instance=json.loads((D/'test-instance.json').read_text())['instanceId']
 p=subprocess.run([CLI,*args,'--instance',instance],text=True,capture_output=True,timeout=timeout)
 (D/(label+'.json')).write_text(p.stdout or p.stderr)
 if p.returncode:raise RuntimeError(p.stderr or p.stdout)
 return json.loads(p.stdout)
if __name__=='__main__': print(json.dumps(run(sys.argv[1],sys.argv[2:]),ensure_ascii=False))
