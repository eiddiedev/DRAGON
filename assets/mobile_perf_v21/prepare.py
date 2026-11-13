import json,re,wave,struct,zipfile
from pathlib import Path
from lupa import LuaRuntime
O=Path('assets/mobile_perf_v21'); A=Path(json.loads((O/'baseline.json').read_text())['source']); B=O/'baseline-scripts'
scene=json.loads(zipfile.ZipFile(O/'baseline.scene.data').read('SerializePcgData.json'))
names={n['basic']['nodeName'] for n in scene['nodeTransformDatas']}
# Cache only this script's scope instance, never the official library. Bounded failures.
cache='''
-- mobile-v21: resolve each dependency at most once a second, at most 30 attempts.
do
 local target=SCOPE
 local original=target.GetScript
 local memo,attempts,nextAt={},{},{}
 local failures={}
 target.GetScript=function(_,name)
  if memo[name] then return memo[name] end
  local now=CS.UnityEngine.Time.realtimeSinceStartup
  if (attempts[name] or 0)>=30 or now<(nextAt[name] or 0) then return nil end
  attempts[name]=(attempts[name] or 0)+1;nextAt[name]=now+1
  local ok,value=pcall(original,target,name)
  if ok and value then memo[name]=value;return value end
  if attempts[name]==30 then failures[name]=tostring(value or 'not loaded');print('[mobile-v21] dependency failed: '..name..' '..failures[name]) end
  return nil
 end
 function GetDependencyDiagnostics() return {build='mobile-v21',attempts=attempts,failures=failures} end
 local destroy=OnDestroy
 -- Installed after lifecycle definitions below; clears references on scene exit.
 RELEASE=function()memo={};attempts={};nextAt={};failures={} end
end
'''
# Add cache immediately after scope creation, cleanup after all lifecycle definitions.
for file,pattern,target in [('dragon_exploration.lua',r"local scope=require\('official.core.runtime_scope'\).from\(self\)",'scope'),('dragon_combat.lua',r"local scope=require\('official.core.runtime_scope'\).from\(self\)",'scope'),('dragon_daycycle.lua',r"local scope=require\('official.core.runtime_scope'\).from\(self\)",'scope'),('dragon_progress.lua',r"local scope=require\('official.core.runtime_scope'\).from\(self\)",'scope'),('dragon_rpg.lua',r'local scope=Scope.from\(self\)','scope'),('dragon_outfits.lua',r'local runtimeScope, scopeReason = RuntimeScope.from\(self\)','runtimeScope'),('dragon_weapons.lua',r'local runtimeScope, runtimeScopeReason = RuntimeScope.from\(self\)','runtimeScope')]:
 s=(B/file).read_text();s,n=re.subn(pattern,lambda m:m[0]+cache.replace('SCOPE',target).replace('RELEASE','ReleaseMobileDependencies'),s,count=1);assert n,file
 s+='\ndo local previous=OnDestroy;function OnDestroy()if previous then previous()end;ReleaseMobileDependencies()end end\n'
 (A/'scripts'/file).write_text(s)
# Bake exact existing deterministic sound synthesis offline.
s=(B/'dragon_fx.lua').read_text();lua=LuaRuntime(unpack_returned_tuples=True)
core=s[s.index('local SAMPLE_RATE'):s.index('local function buildClip')]
lib=lua.execute(core+'\nreturn {names=SOUND_NAMES,rate=SAMPLE_RATE,build=buildSamples}')
labels=['挥剑','剑击','巨力觉醒','重击','弓弦','箭击','叶刃蓄力','叶刃破空','叶刃命中','箭雨落下','箭雨命中','奥术发射','奥术命中','奥术爆发','陨星下落','陨星撞击','冲击发射','冲击爆炸','时空命中','破壁','奖励','闪避']
manifest=[];decl=[];entries=[]
for i,name in lib.names.items():
 var='Bank'+''.join(w.title() for w in name.replace('v2-','').split('-'));rid='audio-'+name
 folder=A/'assets/audio'/rid;folder.mkdir(parents=True,exist_ok=True)
 duration,samples=lib.build(name);rate=int(lib.rate);count=int(rate*duration)
 pcm=b''.join(struct.pack('<h',round(max(-1,min(1,samples[j]))*32767))for j in range(1,count+1))
 with wave.open(str(folder/'audio.wav'),'wb')as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate);w.writeframes(pcm)
 (folder/'meta.json').write_text(json.dumps({'schemaVersion':4,'resourceId':rid,'displayName':'龙眠'+labels[i-1]+'音效','summary':'离线烘焙现有战斗音效，避免手机运行时合成。'},ensure_ascii=False))
 decl.append(f'---@var {var}:UnityEngine.AudioClip=nil\n---@name {labels[i-1]}音效\n---@refFrom asset\n---@assetCategory Music\n---@dataType Audio\n---@var {var}Volume:number=0.48\n---@name {labels[i-1]}音量\n---@var {var}MaxDistance:number=25\n---@name {labels[i-1]}作用范围\n')
 entries.append(f" ['{name}']={{{var},{var}Volume,{var}MaxDistance}}")
 manifest.append({'name':name,'var':var,'resource':rid,'bytes':len(pcm)+44,'seconds':duration})
s=s.replace('local U=CS.UnityEngine',''.join(decl)+'local U=CS.UnityEngine',1)
a=s.index('local SAMPLE_RATE');b=s.index('local audioClips={}')
s=s[:a]+"local function audioConfig()return {\n"+',\n'.join(entries)+"\n}end\n"+s[b:]
a=s.index('local function sound(');b=s.index('local originalSources={}',a)
s=s[:a]+'''local function sound(name,gain)
 local now=U.Time.time;if audioLastTime[name]and now-audioLastTime[name]<.07 then return end
 local c=audioConfig()[name];local clip=c and c[1]
 if not clip then audioFailed=audioFailed+1;logger:warnOnce('missing-'..name,'audio asset unavailable',name);return end
 if c[2]<=0 or c[3]<=0 then return end
 local actor=CS.DouyinActorService.GetLocalActor()
 if not actor then return end
 if not audioRoot then audioRoot=U.GameObject('DragonCombatAudio')end
 local source=nil
 for _,v in ipairs(audioPool)do if not v.isPlaying then source=v;break end end
 local limit=U.Application.isMobilePlatform and 4 or 8
 if not source and #audioPool<limit then local go=U.GameObject('CombatVoice'..#audioPool);go.transform:SetParent(audioRoot.transform,false);source=go:AddComponent(typeof(U.AudioSource));source.playOnAwake=false;source.spatialBlend=1;source.rolloffMode=U.AudioRolloffMode.Linear;source.loop=false;audioPool[#audioPool+1]=source end
 if not source then return end
 source.transform.position=actor.position;source.minDistance=math.min(2,c[3]*.1);source.maxDistance=c[3]
 source.volume=math.max(0,math.min(1,c[2]));source.mute=false;source.pitch=1;source:PlayOneShot(clip,gain or 1)
 audioLastTime[name]=now;audioPlayed=audioPlayed+1;audioLast=name
end
'''+s[b:]
s=re.sub(r' if warmIndex<=#SOUND_NAMES then[^\n]+\n','',s)
s=s.replace('for _,clip in pairs(audioClips)do U.Object.Destroy(clip)end;','')
s=s.replace("local scope15=require('official.core.runtime_scope').from(self)","local scope15=require('official.core.runtime_scope').from(self)"+cache.replace('SCOPE','scope15').replace('RELEASE','ReleaseMobileDependencies'))
s=s.replace('for i=1,count do local a=', 'if U.Application.isMobilePlatform then count=math.max(2,math.ceil(count*.4))end\n for i=1,count do local a=')
s=s.replace('#flying>=26','#flying>=(U.Application.isMobilePlatform and 10 or 26)')
s+='\ndo local previous=OnDestroy;function OnDestroy()previous();ReleaseMobileDependencies()end end\n'
(A/'scripts/dragon_fx.lua').write_text(s);(O/'audio-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
# Source only; authoring CLI validates and registers resources.
print('baked',len(manifest),'audio bytes',sum(v['bytes']for v in manifest))
