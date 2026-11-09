import struct, json, io
import numpy as np
from PIL import Image
def load_glb(path):
    f=open(path,'rb'); f.read(12); n,_=struct.unpack('<II',f.read(8)); g=json.loads(f.read(n)); bl,_=struct.unpack('<II',f.read(8)); b=f.read(bl)
    def acc(i):
        a=g['accessors'][i]; v=g['bufferViews'][a['bufferView']]
        off=v.get('byteOffset',0)+a.get('byteOffset',0)
        ct={5126:np.float32,5125:np.uint32,5123:np.uint16}[a['componentType']]
        k={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
        return np.frombuffer(b,ct,a['count']*k,off).reshape(-1,k) if k>1 else np.frombuffer(b,ct,a['count'],off)
    p=g['meshes'][0]['primitives'][0]
    pos,nrm,uv=acc(p['attributes']['POSITION']),acc(p['attributes']['NORMAL']),acc(p['attributes']['TEXCOORD_0'])
    idx=acc(p['indices']).astype(np.int64)
    im=g['images'][0]; v=g['bufferViews'][im['bufferView']]
    img=Image.open(io.BytesIO(b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])).convert('RGB')
    return pos.copy(),nrm.copy(),uv.copy(),idx.reshape(-1,3).copy(),img
