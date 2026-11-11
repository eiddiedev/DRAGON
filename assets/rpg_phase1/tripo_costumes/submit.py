import subprocess,json,pathlib,sys
D=pathlib.Path(__file__).resolve().parent
CLI='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world'
INSTANCE='awc-05d11ea9-0bb0-497a-b8fb-afba17e533ce'
k=sys.argv[1];receipt=D/(k+'-submit.json')
if receipt.exists():raise SystemExit('Receipt already exists; inspect task before resubmission')
cmd=[CLI,'generation','start','model','--prompt',(D/(k+'-prompt.txt')).read_text(),'--args',(D/(k+'-args.json')).read_text(),'--request-id','dragon-rpg-tripo-'+k+'-20261111-v1','--instance',INSTANCE,'--json']
if k!='warrior':cmd+=['--image',str(D/(k+'-reference.png'))]
p=subprocess.run(cmd,text=True,capture_output=True,timeout=120)
receipt.write_text(p.stdout or p.stderr)
print(p.stdout or p.stderr);raise SystemExit(p.returncode)
