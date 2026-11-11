"""Read-only saved-scene preservation audit for the castle refit."""
import json,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'assets/castle_refit_v1'
live=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data')
zb=zipfile.ZipFile(O/'scene-before.data');zf=zipfile.ZipFile(live)
b=json.loads(zb.read('SerializePcgData.json'));f=json.loads(zf.read('SerializePcgData.json'))
old={str(n['id']):n for n in b['nodeTransformDatas']};new={str(n['id']):n for n in f['nodeTransformDatas']}
replaced={'gothic_main','gothic_towers','gothic_wall','castle_rooms','lamp_posts','lamp_glow','tripo_castle_statue_0','tripo_castle_statue_1','tripo_castle_cornice_0','tripo_castle_cornice_1'}
allowed={i for i,n in old.items() if n['basic']['nodeName'] in replaced}
changed=True
while changed:
 before=len(allowed);allowed.update(i for i,n in old.items() if str(n['basic'].get('parentId')) in allowed);changed=len(allowed)!=before
authored={i for i,n in old.items() if n.get('editor',{}).get('assetData') or n['basic'].get('tag') in ['Map','Terrain','TerrainTile']}
missing=[i for i in authored if i not in new and i not in allowed]
def equal(a,b):
 if isinstance(a,(int,float)) and isinstance(b,(int,float)):return abs(a-b)<1e-4
 if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all(equal(v,b[k]) for k,v in a.items())
 return a==b
basic=[{'id':i,'name':n['basic']['nodeName']} for i,n in old.items() if i in authored and i not in allowed and i in new and not equal(n['basic'],new[i]['basic'])]
terrain=[n for n in zb.namelist() if n!='SerializePcgData.json' and (n not in zf.namelist() or zb.read(n)!=zf.read(n))]
main=next(v['content'] for v in f['runtimeScripts'].values() if v.get('content') and 'local CASTLE_NAMES' in v['content'])
result={'scope':'Authored asset roots and terrain; generated runtime child IDs excluded; float tolerance1e-4','authored_checked':len(authored-allowed),'unrelated_missing':missing,'unrelated_basic_changes':basic,'terrain_changes':terrain,'nodes':len(new),'castle_roots':[i for i,n in new.items() if n['basic']['nodeName']=='龙眠城堡精修'],'main_has_fixed_stone':'Castle materials retain their authored dark stone' in main,'main_has_split_names':'gothic_main-east' in main}
(O/'invariants-final.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(result)
assert not missing and not basic and not terrain and result['main_has_fixed_stone'] and result['main_has_split_names']
