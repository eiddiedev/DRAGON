"""Stage six interaction changes from latest saved scene; never overwrite live scene."""
from pathlib import Path
import json,zipfile,uuid,struct,re,sys
from lupa import LuaRuntime
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data'
if len(sys.argv)>1:SOURCE=Path(sys.argv[1])
OUT=ROOT/'assets/interactions_v1';OUT.mkdir(exist_ok=True)
with zipfile.ZipFile(SOURCE) as z: entries={n:z.read(n) for n in z.namelist()}
d=json.loads(entries['SerializePcgData.json']); original={n['id']:n['basic'].copy() for n in d['nodeTransformDatas']}
lua=LuaRuntime();check=lua.eval('function(s) local f,e=load(s);return f~=nil,e end')
def register(name,content,module=False):
 ok,err=check(content);assert ok,(name,err)
 sid='modules/'+name+'.lua' if module else str(uuid.uuid5(uuid.NAMESPACE_URL,'dragon-interactions-v1/'+name))
 if not module:content='---@id '+sid+'\n---@referenceName '+name+'.lua\n'+content
 d['runtimeScripts'][sid]={'content':content,'contentPath':None,'referenceName':None if module else name+'.lua','referencePath':'modules/'+name+'.lua','isModuleScript':module}
 return sid
register('scene_interaction_bus',(ROOT/'scripts/scene_interaction_bus.lua').read_text(),True)
h=struct.unpack('<'+str(257*257)+'f',entries['HeightMap_3193404.data'])
grid='{'+','.join('{'+','.join(str(round(h[z*257+x]*256,4)) for x in range(0,257,4))+'}' for z in range(0,257,4))+'}'
ids={}
for kind in ['horse','boat','carpet']:
 s=(ROOT/'scripts/scene_vehicle.lua').read_text().replace('__KIND__',repr(kind)).replace('__HEIGHT_GRID__',grid)
 ids[kind]=register('scene_vehicle_'+kind,s)
for kind in ['dial','mushroom','sheep_sound']:ids[kind]=register('scene_'+kind,(ROOT/('scripts/scene_'+kind+'.lua')).read_text())
changed=[]
for n in d['nodeTransformDatas']:
 name=n['basic']['nodeName'];kind=None
 if n['id']==-1372397970:kind='horse';size=(5,4,5)
 elif re.fullmatch('sailboat_[0-2]',name):kind='boat';size=(10,6,17)
 elif n['id']==-2081863013:kind='carpet';size=(6,4,6)
 elif name=='time_dial':kind='dial';size=(8,5,8)
 elif re.fullmatch('mush(?:_[1-5])?',name):kind='mushroom';size=(3,4,3)
 elif re.fullmatch('sheep_[0-8]',name):kind='sheep_sound';size=(10,5,10)
 if not kind:continue
 scale=n['basic']['scale'];localSize={k:v/abs(scale[k]) for k,v in zip('xyz',size)}
 n['physics']['triggerData']=[{'shape':'box','enabled':True,'center':{'x':0,'y':localSize['y']*.25,'z':0},'size':localSize,'radius':.5,'height':2,'direction':1}]
 if kind=='mushroom':n['physics']['physicsColliderData']['enableCollision']=True
 bindings=n.setdefault('runtimeScriptBindings',[])
 if not any(b['scriptId']==ids[kind] for b in bindings):bindings.append({'enabled':True,'scriptId':ids[kind],'scriptType':1,'paramsJson':'{}'})
 changed.append({'id':n['id'],'name':name,'kind':kind})
sid='a87ebe50-812d-4151-a056-727a118aecbd';s=d['runtimeScripts'][sid]['content']
a=s.index('    local entered = false',s.index('local function updateDayNight'));b=s.index('    local target =',a)
s=s[:a]+'''    local bus=require('modules.scene_interaction_bus')
    if bus.dialRequests>0 and dialCooldown<=0 then
        bus.dialRequests=0;setDay(not isDay);dialCooldown=1
    end
'''+s[b:]
# Retain mushroom glow, remove old proximity/Teleport bounce.
a=s.index('    if bounceT == nil then',s.index('local function updateMush'));b=s.index('\n---- 唤龙祭坛',a)
s=s[:a]+'end\n'+s[b:]
s=s.replace('    updateMount(actor, p)','    -- Native per-object seat script owns carpet movement.')
s=s.replace('    updateBoats(actor, p)','    -- Native per-object seat scripts own boat movement.')
# Preserve leaf silhouettes in the emissive pass; two small canopy lights cast
# the glow onto the trunk and nearby ground instead of whitening whole cards.
s=s.replace('m:SetTexture("_EmissionTex", UnityEngine.Texture2D.whiteTexture)', 'm:SetTexture("_EmissionTex", m:GetTexture("_BaseMap") or m:GetTexture("_MainTex") or UnityEngine.Texture2D.whiteTexture)')
s=s.replace('holyTried.found[name] = true', '''holyTried.found[name] = true
                    holyTried.lights=holyTried.lights or {}
                    local center=rs[0].bounds.center
                    holyTried.lights[#holyTried.lights+1]=addLight(center,Color(1,.12,.24,1),16,0)''')
s=s.replace('local glow = night * night * (.68 + .045 * math.sin(Time.time * .65))','''local glow = night * night * (1.15 + .06 * math.sin(Time.time * .65))
    for _,light in ipairs(holyTried.lights or {}) do
        light.intensity=night*night*1.8;light.enabled=night>.01
    end''')
a=s.index('\nfunction OnDestroy()',s.index('function UI.clip'))
s=s[:a]+'\n'+(ROOT/'scripts/scene_interaction_audio.lua').read_text()+'\n'+s[a:]
s=s.replace('function Update()\n','function Update()\n    UI.prepareInteractionAudio()\n',1)
ok,err=check(s);assert ok,err;d['runtimeScripts'][sid]['content']=s
assert all(n['basic']==original[n['id']] for n in d['nodeTransformDatas'])
entries['SerializePcgData.json']=json.dumps(d,ensure_ascii=False).encode()
with zipfile.ZipFile(OUT/'scene-STAGED-UNTESTED.data','w',zipfile.ZIP_DEFLATED) as z:
 for name,data in entries.items():z.writestr(name,data)
(OUT/'staging-report.json').write_text(json.dumps({'source':str(SOURCE),'status':'staged-not-installed-not-runtime-tested','nodes':changed,'preservedAllBasicTransforms':True,'treeGlow':'masked emission and two canopy lights; needs visual verification'},ensure_ascii=False,indent=2))
print(json.dumps({'stagedNodes':len(changed),'syntax':'pass','transforms':'unchanged','installed':False}))
