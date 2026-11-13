from pathlib import Path
import json,zipfile,struct,base64,hashlib,io,shutil
from PIL import Image
from lupa import LuaRuntime
O=Path('assets/mobile_visual_riding_v26');A=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project-1facc28c-97a0-4f56-bec3-bf9acaf89fb9/ai-sessions/workspace_m293a9tg/wprefabs')
p=A/'dragon_fx_mobile_v22/scripts/dragon_world_bridge.lua';s=p.read_text();assert 'v26-bundled-ui' not in s
shutil.copy2(p,O/'bridge-before.lua')
z=zipfile.ZipFile('/Users/bytedance/Downloads/world_dev_unity_143126706-t0z0-PROD.zip');d=json.loads(z.read('SerializePcgData.json'));refs={r['id']:r['pathOrUrl'] for r in d['resourceRefs']};wanted={k.replace('TextureSource_',''):v['uri'] for k,v in json.load(open('assets/review_startup_v25/texture-dependencies.json')).items()}
imgs={};manifest={}
for n in d['nodeTransformDatas']:
 name=n['basic']['nodeName']
 if name not in wanted:continue
 g=n['resource']['glbSliceData'];assert g['sourceUri']==wanted[name];raw=z.read(refs[g['sourceMeshRefId']]);sz=struct.unpack('<I',raw[12:16])[0];j=json.loads(raw[20:20+sz]);binary=raw[28+sz:];v=j['bufferViews'][j['images'][0]['bufferView']];img=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
 source='review GLB embedded PNG (same URI)'
 if name=='InkCarrier_map':img=Path('assets/ui_v2/source/map_original_v10.png').read_bytes();source='original map source PNG'
 if name=='MobileGroundColorSource':img=Path('assets/mobile_compat_v23/MatCoverTex_3193404.png').read_bytes();source='original saved ground color PNG'
 im=Image.open(io.BytesIO(img));assert max(im.size)<=2048,(name,im.size)
 imgs[name]=base64.b64encode(img).decode();manifest[name]={'uri':wanted[name],'source':source,'bytes':len(img),'size':im.size,'sha256':hashlib.sha256(img).hexdigest()}
assert len(imgs)==13
(O/'fallback-images.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
block='''-- v26: review clients may not expose textures on GLB asset parameters.
-- Lossless original image bytes; at most one decode/frame, no network or scene scan.
UI.bundled={at=1,tex={},owned={},errors={},status={},frame=-1}
UI.bundled.order={'''+','.join("'%s'"%k for k in imgs)+'''}
UI.bundled.bytes={'''+','.join("['%s']='%s'"%(k,v) for k,v in imgs.items())+'''}
function UI.textureNamed(name)
 local cached=UI.bundled.tex[name];if cached then return cached end
 local ok,t=pcall(UI.textureFromAsset,UI.textureSource(name))
 if ok and t then return t end
 return nil
end
function UI.bundledStep()
 local b=UI.bundled;if b.at>#b.order then return true end
 if b.frame==Time.frameCount then return false end;b.frame=Time.frameCount
 local name=b.order[b.at];local t=UI.textureNamed(name)
 if t then b.tex[name]=t;b.status[name]='asset'
 else
  local made=nil
  local ok,err=pcall(function()
   made=UnityEngine.Texture2D(2,2,UnityEngine.TextureFormat.RGBA32,false)
   local bytes=CS.System.Convert.FromBase64String(b.bytes[name])
   if not made:LoadImage(bytes,true)then error('LoadImage returned false')end
   made.name='BundledUI_'..name;made.wrapMode=UnityEngine.TextureWrapMode.Clamp
   made.filterMode=UnityEngine.FilterMode.Bilinear
   b.tex[name]=made;b.owned[name]=made;b.status[name]='bundled'
  end)
  if not ok then
   if made then UnityEngine.Object.Destroy(made)end
   b.errors[name]=tostring(err);b.status[name]='failed'
   UI.log('bundled image failed '..name..': '..tostring(err))
  end
 end
 b.bytes[name]=nil;b.at=b.at+1
 if b.at>#b.order then b.bytes=nil;return true end
 return false
end
'''
a=s.index('function UI.findTextures()');s=s[:a]+block+s[a:]
s=s.replace('local t=UI.textureFromAsset(UI.textureSource(n))','local t=UI.textureNamed(n)')
s=s.replace("local t=UI.textureFromAsset(UI.textureSource('InkCarrier_'..key))","local t=UI.textureNamed('InkCarrier_'..key)")
s=s.replace('s.texture=UI.textureFromAsset(TextureSource_MobileGroundColorSource)',"s.texture=UI.textureNamed('MobileGroundColorSource')")
s=s.replace('local kitReady = UI.K.step()','local kitReady = UI.K.step()\n        if kitReady then kitReady=UI.bundledStep() end',1)
s=s.replace("build='v25-streaming-ui'","build='v26-bundled-ui',bundled=UI.bundled.status,bundleErrors=UI.bundled.errors")
s+='''\nUI.v26Destroy=OnDestroy
function OnDestroy()
 UI.v26Destroy()
 for _,t in pairs(UI.bundled.owned)do pcall(function()UnityEngine.Object.Destroy(t)end)end
 UI.bundled.tex={};UI.bundled.owned={};UI.bundled.bytes=nil
end
'''
l=LuaRuntime();ok,e=l.eval('function(s)local f,e=load(s);return f~=nil,e end')(s);assert ok,e
p.write_text(s);shutil.copy2(p,O/'dragon_world_bridge.lua')
# Keep seat ownership; synchronize the local actor through the public actor API.
p=A/'mobile_actors_v23/scripts/horse_seat_v1.lua';s=p.read_text();shutil.copy2(p,O/'horse-before.lua')
s=s.replace('local lastClip=nil','local lastClip=nil\nlocal ridingStats={build="v26-actor-follow",aligns=0,maxError=0,lastError=nil}')
s=s.replace('tr:SetParent(seat.transform,true);tr.localScale=s.scale;', 'if tr.parent~=seat.transform then tr:SetParent(seat.transform,true)end;tr.localScale=s.scale;')
s=s.replace('local an=actor.gameObject:GetComponentInChildren(typeof(U.Animator),true)\n if an then','local an=s.animator\n if not an then an=actor.gameObject:GetComponentInChildren(typeof(U.Animator),true);if an and an.isHuman then s.animator=an end end\n if an and an.isHuman then')
needle='\n end\nend\nlocal function setSeat()'
replacement='''
 end
 -- Transform parenting alone can be overwritten by the network actor controller.
 -- Write the local actor's authoritative pose after the hips offset is resolved.
 if actor.isLocal then
  local desired=tr.position;local rot=tr.rotation
  actor.position=desired;actor.rotation=rot
  ridingStats.aligns=ridingStats.aligns+1
  ridingStats.maxError=math.max(ridingStats.maxError,(actor.position-desired).magnitude)
 end
end
local function setSeat()'''
assert needle in s;s=s.replace(needle,replacement,1)
s=s.replace('function LateUpdate() for actor,_ in pairs(seated) do align(actor) end end','''function LateUpdate()
 if seat then setSeat()end
 for actor,_ in pairs(seated)do
  local ok,err=pcall(align,actor)
  if not ok and ridingStats.lastError~=tostring(err)then ridingStats.lastError=tostring(err);U.Debug.LogWarning('[horse-follow] '..tostring(err))end
 end
end
function GetRidingDiagnostics()return {build=ridingStats.build,aligns=ridingStats.aligns,maxError=ridingStats.maxError,lastError=ridingStats.lastError,mounted=passenger~=nil,horse=tostring(self.transform.position),rider=passenger and tostring(passenger.position)or nil}end''')
ok,e=l.eval('function(s)local f,e=load(s);return f~=nil,e end')(s);assert ok,e
p.write_text(s);shutil.copy2(p,O/'horse_seat_v1.lua')
print('Lua syntax OK; original image bytes',sum(v['bytes']for v in manifest.values()),'GPU RGBA bytes',sum(v['size'][0]*v['size'][1]*4 for v in manifest.values()))
