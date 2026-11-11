import pathlib,subprocess,json,shutil
D=pathlib.Path(__file__).resolve().parent;W=pathlib.Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-508139d3-e199-4b21-805c-0050141438e3/ai-sessions/workspace_jcb1a5xe');P=W/'wprefabs/dragon_rpg_ui_v2';CLI='/Applications/造世界编辑器.app/Contents/Resources/addon/awc-cli/bin/douyin-world';I='awc-05d11ea9-0bb0-497a-b8fb-afba17e533ce'
def run(label,args):
 p=subprocess.run([CLI,*args,'--instance',I,'--json'],capture_output=True,text=True,timeout=100);(D/(label+'.json')).write_text(p.stdout or p.stderr)
 if p.returncode:raise RuntimeError(p.stdout or p.stderr)
 return json.loads(p.stdout)['data']
for k in ['mage','ranger','warrior']:
 res=P/'assets/models'/('model-tripo-'+k)
 if k!='mage':run(k+'-skin-check',['authoring','skill','run','inspect-model','--workspace',str(W),'--argv',json.dumps(['--model-path',str(res.relative_to(W)/'blender/rigged.glb'),'--check-skin'])])
 shutil.copy2(res/'blender/rigged.glb',res/'topology/model.glb')
 a=run(k+'-rig-archive',['authoring','resource','archive','model-tripo-'+k,'--kind','model','--prefab','dragon_rpg_ui_v2','--workspace-id','workspace_jcb1a5xe'])
 print(k,a,flush=True)
 attach=run(k+'-rig-attach',['authoring','prefab','attach','dragon_rpg_ui_v2','--kind','model','--uri',a['uri'],'--workspace-id','workspace_jcb1a5xe']);print(k,attach,flush=True)
