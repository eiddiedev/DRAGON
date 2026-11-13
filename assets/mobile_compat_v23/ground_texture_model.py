import json,struct
from pathlib import Path
D=Path('assets/mobile_compat_v23');img=(D/'MatCoverTex_3193404.png').read_bytes();chunks=[];views=[]
def add(b,target=None):
 off=sum(len(v) for v in chunks);chunks.append(b+b'\0'*((-len(b))%4));v={'buffer':0,'byteOffset':off,'byteLength':len(b)}
 if target:v['target']=target
 views.append(v);return len(views)-1
p=add(struct.pack('<9f',0,0,0,.001,0,0,0,.001,0),34962);uv=add(struct.pack('<6f',0,0,1,0,0,1),34962);idx=add(struct.pack('<3H',0,1,2),34963);im=add(img)
g={'asset':{'version':'2.0','generator':'Dragon explicit saved ground-color dependency'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'name':'GroundColorDependency','mesh':0}],'meshes':[{'primitives':[{'attributes':{'POSITION':0,'TEXCOORD_0':1},'indices':2,'material':0}]}],'materials':[{'name':'SavedGroundCover','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':1}}],'textures':[{'source':0}],'images':[{'name':'SavedGroundCover_v23','bufferView':im,'mimeType':'image/png'}],'accessors':[{'bufferView':p,'componentType':5126,'count':3,'type':'VEC3','min':[0,0,0],'max':[.001,.001,0]},{'bufferView':uv,'componentType':5126,'count':3,'type':'VEC2'},{'bufferView':idx,'componentType':5123,'count':3,'type':'SCALAR'}],'bufferViews':views,'buffers':[{'byteLength':sum(map(len,chunks))}]};j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b=b''.join(chunks);out=struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b;(D/'ground-color-dependency.glb').write_bytes(out)
print('texture unchanged',len(img),'bytes')
