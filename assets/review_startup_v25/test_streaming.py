from pathlib import Path
from lupa import LuaRuntime
s=Path('assets/review_startup_v25/dragon_world_bridge.lua').read_text()
l=LuaRuntime(unpack_returned_tuples=True)
# Execute the actual boot branch with all world-model checks deliberately failing.
branch=s[s.index('function UI.update(actor)'):s.index('    elseif UI.state == "title" then',s.index('function UI.update(actor)'))]+'\nend\nend'
l.execute('''Time={unscaledDeltaTime=.1};UI={t=0,wait=0,state='boot',cover={},P_title={},loading={},K={step=function()return true end}};UI.requiredModelsReady=function()error('must not block on streamed models')end;UI.findTextures=function()return true end;UI.buildAll=function()end;UI.buildSounds=function()end;UI.camStart=function()end;UI.lockPlayer=function()end;UI.show=function()end;UI.log=function()end''')
l.execute(branch);l.execute('UI.update({})');assert l.eval('UI.state')=='title'
# Execute actual recurring ground fix; assets absent initially, and a material arriving late.
a=s.index('UI.groundCover={');b=s.index('\nUI.v23GroundUpdate',a)
l.execute('''Time.realtimeSinceStartup=0;typeof=function(x)return x end;local tex={width=1024,height=1024};TextureSource_MobileGroundColorSource={};UnityEngine={Material={},Resources={}};local data={Length=0};UnityEngine.Resources.FindObjectsOfTypeAll=function()return data end;UI.textureFromAsset=function(go)if go then return tex end end;function addLateMaterial() data[0]={shader={name='ParaSpace/World/ENV/EnvGrass03'},HasProperty=function()return true end,GetTexture=function(self)return self.texture end,SetTexture=function(self,_,v)self.texture=v end};data.Length=1 end;function isBound()return data[0].texture==tex end''')
l.execute(s[a:b]);l.execute('UI.bindMobileFlowerGround(); Time.realtimeSinceStartup=6;UI.bindMobileFlowerGround(); addLateMaterial();Time.realtimeSinceStartup=12;UI.bindMobileFlowerGround()');assert l.eval('isBound()')
assert l.eval('UI.groundCover.scans')==3
print('PASS: title proceeds without distant models; vegetation arriving after initial scans receives saved ground texture')
