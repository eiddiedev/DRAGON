"""Split the exact reviewed windmill without moving any vertex, UV, or material.
Candidate files only; never imports or writes a scene.
"""
from pathlib import Path
import copy,json,struct,zipfile,hashlib,collections
D=Path(__file__).parent
z=zipfile.ZipFile('/Users/bytedance/Downloads/world_dev_unity_143175468-dsst-PROD.zip')
blob=z.read('5f34a7048bfdcbee6c8d91ba3fd64794843c98d9010a83976546f02a6fa1ee96.glb')
json_size=struct.unpack_from('<I',blob,12)[0];doc=json.loads(blob[20:20+json_size]);off=20+json_size
bin_len=struct.unpack_from('<I',blob,off)[0];binary=bytearray(blob[off+8:off+8+bin_len]);original_binary=bytes(binary)

def accessor(idx):
 a=doc['accessors'][idx];v=doc['bufferViews'][a['bufferView']]
 fmt={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
 stride=v.get('byteStride',struct.calcsize('<'+fmt)*n);start=v.get('byteOffset',0)+a.get('byteOffset',0)
 vals=[struct.unpack_from('<'+fmt*n,binary,start+i*stride)for i in range(a['count'])]
 return [x[0]for x in vals]if n==1 else vals

main=next(i for i,n in enumerate(doc['nodes'])if n['name']=='main');mi=doc['nodes'][main]['mesh'];prim=doc['meshes'][mi]['primitives'][0]
verts=accessor(prim['attributes']['POSITION']);indices=accessor(prim['indices']);lo=[min(v[k]for v in verts)for k in range(3)];hi=[max(v[k]for v in verts)for k in range(3)]
factor=(hi[1]-lo[1])/22.301563262939453;oy=lo[1]+2*factor;oz=(lo[2]+hi[2])/2
parent=list(range(len(verts)));keys={}
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for i,v in enumerate(verts):
 key=','.join(format(x,'.5f')for x in (v[0]/factor,(v[1]-oy)/factor,(v[2]-oz)/factor));parent[i]=keys.get(key,i);keys[key]=parent[i]
for a,b,c in zip(indices[0::3],indices[1::3],indices[2::3]):
 a,b,c=find(a),find(b),find(c);parent[b]=a;parent[c]=a
bounds={}
for i,v in enumerate(verts):
 root=find(i);z=(v[2]-oz)/factor;y=(v[1]-oy)/factor;b=bounds.setdefault(root,[float('inf'),float('-inf'),float('inf')]);b[0]=min(b[0],z);b[1]=max(b[1],z);b[2]=min(b[2],y)
fixed=[];moving=[]
for a,b,c in zip(indices[0::3],indices[1::3],indices[2::3]):
 low,high,y=bounds[find(a)];target=moving if ((low>3.79 and high<4.11)or(low>-4.11 and high<-3.79))and y>2.4 else fixed;target.extend((a,b,c))
assert len(moving)>100 and len(fixed)>100
assert collections.Counter(zip(indices[0::3],indices[1::3],indices[2::3]))==collections.Counter(zip(fixed[0::3],fixed[1::3],fixed[2::3]))+collections.Counter(zip(moving[0::3],moving[1::3],moving[2::3]))
pivot=[(lo[0]+hi[0])/2,oy+11.4*factor,sum(verts[i][2]for i in moving)/len(moving)]
def add_indices(vals):
 while len(binary)%4:binary.append(0)
 start=len(binary);data=struct.pack('<'+'H'*len(vals),*vals);binary.extend(data)
 bv=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(data),'target':34963})
 ai=len(doc['accessors']);doc['accessors'].append({'bufferView':bv,'componentType':5123,'count':len(vals),'type':'SCALAR','min':[min(vals)],'max':[max(vals)]});return ai
oldprim=copy.deepcopy(prim);prim['indices']=add_indices(fixed);rp=copy.deepcopy(oldprim);rp['indices']=add_indices(moving)
rmi=len(doc['meshes']);doc['meshes'].append({'name':'windmill_rotor_mesh','primitives':[rp]})
pidx=len(doc['nodes']);doc['nodes'].extend([{'name':'windmill_rotor_pivot','translation':pivot,'children':[pidx+1]},{'name':'windmill_rotor','translation':[-v for v in pivot],'mesh':rmi}]);doc['nodes'][main].setdefault('children',[]).append(pidx)
doc['buffers'][0]['byteLength']=len(binary)
js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\x00'*((-len(binary))%4)
out=struct.pack('<4sII',b'glTF',2,12+8+len(js)+8+len(binary))+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(binary),b'BIN\x00')+binary
assert bytes(binary[:len(original_binary)])==original_binary
(D/'windmill_split.glb').write_bytes(out)
report={'sourceZip':'/Users/bytedance/Downloads/world_dev_unity_143175468-dsst-PROD.zip','sourceEntry':'5f34a7048bfdcbee6c8d91ba3fd64794843c98d9010a83976546f02a6fa1ee96.glb','sourceSHA256':hashlib.sha256(blob).hexdigest(),'output':'windmill_split.glb','outputSHA256':hashlib.sha256(out).hexdigest(),'bytesBefore':len(blob),'bytesAfter':len(out),'originalTriangles':len(indices)//3,'fixedTriangles':len(fixed)//3,'movingTriangles':len(moving)//3,'rotorPivotLocal':pivot,'preserved':['all original binary buffer bytes','positions and normals','UVs and textures','materials','original glow node','original main node transform','exact original triangle multiset at rest'],'sceneNodeId':932317899,'sceneTransformMustRemainUnchanged':True,'notVerified':['actual imported pivot discovery','mobile rendering/rotation']}
(D/'windmill-split-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
