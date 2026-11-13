from pathlib import Path
import json,shutil
A=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9/ai-sessions/workspace_m293a9tg/wprefabs/dragon_fx_mobile_v22')
O=Path('assets/mobile_failure_v22'); (O/'fx-source').mkdir(exist_ok=True)
# Isolate this change: all unrelated scripts revert to the known pre-v21 baseline.
for p in Path('assets/mobile_perf_v21/baseline-scripts').glob('*.lua'):
 if p.name!='dragon_fx.lua': shutil.copy2(p,A/'scripts'/p.name)
s=Path('assets/mobile_perf_v21/candidate-scripts/dragon_fx.lua').read_text()
s=s[:s.index('local hurtFeel=nil')]
s=s.replace("v.go.transform.position=position;", "if v.source.isPlaying then return end\n v.go.transform.position=position;")
tail=(O/'fx-tail.lua').read_text();s+=tail
(A/'scripts/dragon_fx.lua').write_text(s);(O/'fx-source/dragon_fx.lua').write_text(s)
# Preserve each effect's silhouette/colors while removing duplicated glow layers.
keep={'slash':{'Ring01','Sparks'},'shield':{'Ring01','Sparks'},'hit':{'Core','Sparks'},'bolt':{'Trail','CometCore'},'arrow':{'Trail','CometCore'},'burst':{'Ring01','Sparks'},'frost':{'Ring01','Sparks'},'meteor':{'Ring01','Sparks'}}
stats=[]
def const(curve,value):
 curve.update(mode='constant',min=value,max=value,multiplier=value)
for kind,names in keep.items():
 p=A/'assets/effects'/('effect-combat-'+kind)/'effect.json';d=json.loads(p.read_text());before=[];after=[]
 for n in d['nodeTransformDatas']:
  ps=n.get('effects',{}).get('particleSystemData')
  if not ps:continue
  name=n['basic']['nodeName'];before.append(ps['main']['maxParticles']);enabled=name in names
  n['basic']['isActive']=enabled
  if not enabled:continue
  cap=10 if name in {'Sparks','Trail'} else 2
  ps['main']['maxParticles']=cap;ps['main']['prewarm']=False
  life=.25 if name=='Trail' else .4
  const(ps['main']['startLifetime'],life)
  if not ps['main']['loop']: ps['main']['duration']=.5
  for b in ps['emission'].get('bursts',[]):const(b['count'],min(cap,max(1,round(b['count'].get('max',1)*.25))));b['cycleCount']=1
  for key in ('rateOverTime','rateOverDistance'):
   c=ps['emission'].get(key)
   if c:const(c,min(12,max(0,c.get('max',0)*.25)))
  for key in ('collision','trigger','lights','noise','trails','subEmitters'):
   if key in ps:ps[key]['enabled']=False
  ps['renderer']['shadowCastingMode']='off';ps['renderer']['receiveShadows']=False
  after.append(cap)
 for n in d['nodeTransformDatas']:
  for m in n.get('effects',{}).get('effectData',{}).get('materials',[]):
   m['properties']['depthFade']=0
 p.write_text(json.dumps(d,ensure_ascii=False));shutil.copy2(p,O/'fx-source'/(kind+'.json'))
 stats.append({'effect':kind,'systemsBefore':len(before),'systemsAfter':len(after),'maxParticlesBefore':sum(before),'maxParticlesAfter':sum(after)})
(O/'fx-budget.json').write_text(json.dumps(stats,indent=2));print(json.dumps(stats,indent=2))
