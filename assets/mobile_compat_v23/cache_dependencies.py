from pathlib import Path
import re
A=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9/ai-sessions/workspace_m293a9tg/wprefabs/dragon_fx_mobile_v22')
base=Path('assets/mobile_perf_v21/prepare.py').read_text();cache=base.split("cache='''",1)[1].split("'''",1)[0].replace('mobile-v21','mobile-v23')
for file,pattern,target in [('dragon_exploration.lua',r"local scope=require\('official.core.runtime_scope'\).from\(self\)",'scope'),('dragon_combat.lua',r"local scope=require\('official.core.runtime_scope'\).from\(self\)",'scope'),('dragon_daycycle.lua',r"local scope=require\('official.core.runtime_scope'\).from\(self\)",'scope'),('dragon_progress.lua',r"local scope=require\('official.core.runtime_scope'\).from\(self\)",'scope'),('dragon_rpg.lua',r'local scope=Scope.from\(self\)','scope'),('dragon_outfits.lua',r'local runtimeScope, scopeReason = RuntimeScope.from\(self\)','runtimeScope'),('dragon_weapons.lua',r'local runtimeScope, runtimeScopeReason = RuntimeScope.from\(self\)','runtimeScope')]:
 p=A/'scripts'/file;s=p.read_text();assert 'resolve each dependency'not in s
 s,n=re.subn(pattern,lambda m:m[0]+cache.replace('SCOPE',target).replace('RELEASE','ReleaseMobileDependencies'),s,count=1);assert n,file
 s+='\ndo local previous=OnDestroy;function OnDestroy()if previous then previous()end;ReleaseMobileDependencies()end end\n';p.write_text(s)
# Reuse bounded source readiness logic without touching the baseline author directory.
source=Path('assets/mobile_perf_v21/patch_shadow.py').read_text();source=source[source.index("marker="):].replace("p.write_text(s)","p.write_text(s.replace('mobile-v21','mobile-v23'))")
p=A/'scripts/dragon_combat.lua';s=p.read_text();exec(source)
print('cached 7 local dependency scopes; bounded shadow spawn retries')
