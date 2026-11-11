from cli import D,P
p=D/'vfx/build_effects.py';s=p.read_text().replace('width=.70*','width=.46*').replace('[(2.4-width,0),(2.4,1)]','[(1.5-width,0),(1.5,1)]')
s=s.replace("mat['properties']['disturbance1']['vStrength']=.02", "mat['properties']['disturbance1']['vStrength']=0;mat['properties']['disturbance1']['uStrength']=0;mat['properties']['base']['texture']['texture']=None")
s=s.replace("('arrow','疾风箭迹',None,[.06,1,.38,1])]", "('arrow','疾风箭迹',None,[.06,1,.38,1]),('frost','霜星冲击',[2,3,4,5,9,10],[.04,.75,1,1]),('meteor','陨星冲击',[2,3,4,5,9,10],[1,.16,.025,1])]")
s=s.replace("if stem=='burst':", "if stem in ['burst','frost','meteor']:")
s=s.replace("col(p['main']['startColor'],[.15,.8,1,1]);", "col(p['main']['startColor'],[.15,.8,1,1]if stem!='meteor'else[1,.6,.025,1]);")
p.write_text(s)
p=D/'vfx/archive_effects.py';s=p.read_text().replace("'bolt','arrow']", "'bolt','arrow','frost','meteor']");p.write_text(s)
p=D/'vfx/bind_effects.py';s=p.read_text().replace("'arena':'ArenaEffect'", "'arena':'ArenaEffect','frost':'FrostEffect','meteor':'MeteorEffect'");p.write_text(s)
p=D/'vfx/dragon_fx.body.lua';s=p.read_text().replace('local U=CS.UnityEngine','''---@var FrostEffect:UnityEngine.GameObject=nil
---@name 霜星冲击
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
---@var MeteorEffect:UnityEngine.GameObject=nil
---@name 陨星冲击
---@refFrom asset
---@assetCategory Effect
---@dataType Prefab
local U=CS.UnityEngine''',1)
s=s.replace("sound('v2-time-hit');one(BlastEffect,p,nil,1.1)", "sound('v2-time-hit');one(FrostEffect,p,nil,1.1)")
s=s.replace("one(BlastEffect,p,nil,action=='skill3'and 2 or 1.4)", "one(action=='skill3'and MeteorEffect or BlastEffect,p,nil,action=='skill3'and 1.8 or 1.4)")
p.write_text(s)
p=D/'dragon_rpg.body.lua';s=p.read_text().replace(' shapes.book=', ' shapes.judgement={{12,51,23,40},{17,35,29,47},{24,39,45,18},{45,18,40,31},{40,31,29,43},{45,18,31,23},{45,5,45,11},{53,14,59,14},{53,6,57,2}}\n shapes.book=');p.write_text(s)
p=D/'dragon_rules.body.lua';s=p.read_text().replace('name="巨剑裁决",icon="sword"','name="巨剑裁决",icon="judgement"');p.write_text(s)
p=P/'scripts/dragon_outfits.lua';s=p.read_text().replace('local original=r.sharedMaterial;local color=original.color',"local original=r.sharedMaterial;local color=U.Color.white;if original:HasProperty('_BaseColor')then color=original:GetColor('_BaseColor')elseif original:HasProperty('_Color')then color=original:GetColor('_Color')end");p.write_text(s);(D.parent/p.name).write_text(s)
p=P/'scripts/dragon_timeline.lua';s=p.read_text();idx=s.index('\nlocal function clamp01');s=s[:idx]+'''
-- Held sword stays compact; a deliberate overhead strike drives the judgement effect.
TIMELINES.melee.skill3={duration=1.05,keys={
 {t=0,hand={.25,-.2,.35},aim={0,0,1},spine=0,weight=0,target=0,lean=0},
 {t=.2,hand={.35,.55,.1},aim={0,1,0},spine=15,weight=1,target=0,lean=-12},
 {t=.55,hand={.2,.85,-.18},aim={0,.8,-.4},spine=20,weight=1,target=0,lean=-18},
 {t=.68,hand={.05,-.05,.95},aim={0,-.65,1},spine=-22,weight=1,target=1,lean=18},
 {t=.82,hand={-.1,-.25,.65},aim={0,-.7,.7},spine=-16,weight=.8,target=0,lean=8},
 {t=1.05,hand={.25,-.2,.35},aim={0,0,1},spine=0,weight=0,target=0,lean=0}}}
''' +s[idx:];p.write_text(s);(D.parent/p.name).write_text(s)
print('refined arc, frost/meteor palettes, judgement animation')
