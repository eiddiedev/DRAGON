from pathlib import Path
import ast,math
import numpy as np,cv2
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent
source=Path('tools/ui/make_ui.py').read_text();tree=ast.parse(source)
namespace={'np':np,'cv2':cv2}
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in ('noise','parchment'):exec(compile(ast.Module(body=[node],type_ignores=[]),'parchment','exec'),namespace)
im=Image.new('RGBA',(256,256));paper=Image.fromarray(namespace['parchment'](145,180,907,True));im.alpha_composite(paper,(48,40));d=ImageDraw.Draw(im);ink=(65,44,25,240)
d.arc((47,27,194,64),180,355,fill=ink,width=3)
for y,w in [(76,80),(97,64),(118,76)]:d.line([(72,y),(72+w,y)],fill=(85,61,35,170),width=3)
d.line([(74,147),(100,141),(89,155),(115,145),(137,150)],fill=ink,width=3)
d.polygon([(135,170),(153,176),(156,227),(143,215),(129,226)],fill=(135,32,24,255))
d.ellipse((121,154,166,195),fill=(158,43,29,255),outline=(96,26,18,255),width=3)
d.ellipse((130,162,158,187),outline=(201,104,67,255),width=2)
# Distinct long quill silhouette, crossing the upright signed parchment.
d.polygon([(103,186),(132,115),(164,58),(211,22),(223,18),(221,51),(196,97),(153,139)],fill=(223,209,172,255),outline=ink,width=3)
d.line([(102,192),(147,119),(215,27)],fill=ink,width=4)
for k in range(7):
 x=149+k*8;y=119-k*12;d.line([(x,y),(x+21,y-2)],fill=(111,86,51,210),width=2);d.line([(x,y),(x-5,y-24)],fill=(111,86,51,210),width=2)
im=im.resize((128,128),Image.Resampling.LANCZOS);im.save(D/'source/quest_entry_v11.png')
q=im.quantize(colors=48,method=Image.Quantize.FASTOCTREE);rgba=q.convert('RGBA');pixels=list(rgba.getdata());palette=list(dict.fromkeys(pixels));idx={v:i+1 for i,v in enumerate(palette)};runs=[]
for p in pixels:
 n=idx[p]
 if runs and runs[-1][0]==n:runs[-1][1]+=1
 else:runs.append([n,1])
colors=','.join('{'+','.join(str(c)for c in x)+'}'for x in palette)
runtext=','.join('{%d,%d}'%tuple(r) for r in runs)
code='''function GetQuestEntrySprite()
 if UI.questSprite then return UI.questSprite end
 local texture=UnityEngine.Texture2D(128,128,UnityEngine.TextureFormat.RGBA32,false)
 local palette={COLORS}
 local runs={RUNS}
 local pixel=0
 for _,run in ipairs(runs)do local c=palette[run[1]];local color=UnityEngine.Color(c[1]/255,c[2]/255,c[3]/255,c[4]/255)
  for i=1,run[2]do texture:SetPixel(pixel%128,127-math.floor(pixel/128),color);pixel=pixel+1 end
 end
 texture:Apply();texture.filterMode=UnityEngine.FilterMode.Bilinear
 UI.questSprite=UnityEngine.Sprite.Create(texture,UnityEngine.Rect(0,0,128,128),UI.V2(.5,.5),100)
 return UI.questSprite
end
'''.replace('COLORS',colors).replace('RUNS',runtext)
(D/'quest_sprite_v11.lua').write_text(code)
print('quest icon',len(palette),'colors',len(runs),'runs')
