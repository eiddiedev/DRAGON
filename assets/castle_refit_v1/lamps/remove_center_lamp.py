from pathlib import Path
import struct,json,hashlib
import numpy as np
R=Path(__file__).resolve().parents[3];O=Path(__file__).parent;P=R/'assets/refit_v13';places=json.loads((P/'lamp-placement.json').read_text());target=places[13];center=np.array([target['x']-128,target['z']-128,target['ground_max']-.1]);beads=[]
for ia,ib in [(12,13),(13,14)]:
 a,b=places[ia],places[ib];a=np.array([a['x']-128,a['z']-128,a['ground_max']+2.9]);b=np.array([b['x']-128,b['z']-128,b['ground_max']+2.9]);L=np.linalg.norm((a-b)[:2])
 if L>16:continue
 k=int(L/1.25)
 for i in range(1,k):
  t=i/k;q=a*(1-t)+b*t;q[2]-=np.sin(t*np.pi)*L*.07;beads.append(q)
report={'source_lamp_index':13,'world_center':target,'string_beads_removed':len(beads),'origin':[128,128],'outputs':{}}
for name in ['lamp_posts','lamp_glow']:
 src=P/(name+'.glb');raw=src.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+jl]);offset=20+jl;bl=struct.unpack_from('<I',raw,offset)[0];binary=bytearray(raw[offset+8:offset+8+bl]);prim=d['meshes'][0]['primitives'][0]
 def acc(idx):
  a=d['accessors'][idx];v=d['bufferViews'][a['bufferView']];dims={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];return np.frombuffer(binary,dtype=dt,count=a['count']*dims,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).copy().reshape(a['count'],dims)
 pos=acc(prim['attributes']['POSITION']);faces=acc(prim['indices']).reshape(-1,3);ct=pos[faces].mean(1);ct=ct[:,[0,2,1]]*np.array([1,-1,1]);drop=(np.linalg.norm(ct[:,:2]-center[:2],axis=1)<1.4)&(ct[:,2]>center[2]-.8)&(ct[:,2]<center[2]+4.2)
 if name=='lamp_glow':
  for q in beads:drop|=np.linalg.norm(ct-q,axis=1)<.1
 kept=faces[~drop];a=d['accessors'][prim['indices']];a['count']=int(kept.size)
 while len(binary)%4:binary+=b'\0'
 a['bufferView']=len(d['bufferViews']);a['byteOffset']=0;a['componentType']=5125;d['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':kept.size*4,'target':34963});binary+=kept.astype('<u4').tobytes();d['buffers'][0]['byteLength']=len(binary)
 # Preserve every source vertex, texture, normal, UV and retained triangle verbatim.
 oldretained=pos[faces[~drop]].tobytes();newretained=pos[kept].tobytes();assert oldretained==newretained
 js=json.dumps(d,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4)
 out=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary;(O/(name+'.glb')).write_bytes(out)
 used=pos[np.unique(kept)];removed_vertices=np.setdiff1d(np.unique(faces[drop]),np.unique(kept));report['outputs'][name]={'original_triangles':len(faces),'removed_triangles':int(drop.sum()),'retained_triangles':len(kept),'newly_unreferenced_vertices':len(removed_vertices),'geometry_retained_sha256':hashlib.sha256(oldretained).hexdigest(),'bounds_gltf':[used.min(0).tolist(),used.max(0).tolist()],'max_dimension':float(max(used.max(0)-used.min(0))),'vertex_buffers_unchanged':True}
(O/'removal-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
