"""Read-only preservation check scoped to the entrance addition."""
import json,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'assets/castle_entry_v2';P=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data')
a=zipfile.ZipFile(O/'scene-before.data');b=zipfile.ZipFile(P)
old=json.loads(a.read('SerializePcgData.json'));new=json.loads(b.read('SerializePcgData.json'))
om={str(n['id']):n for n in old['nodeTransformDatas']};nm={str(n['id']):n for n in new['nodeTransformDatas']}
def eq(x,y):
 if isinstance(x,(int,float)) and isinstance(y,(int,float)):return abs(x-y)<1e-4
 if isinstance(x,dict) and isinstance(y,dict):return x.keys()==y.keys() and all(eq(v,y[k]) for k,v in x.items())
 return x==y
roots={i:n for i,n in om.items() if n.get('editor',{}).get('assetData') and i!='-1084074086'}
changes=[{'id':i,'name':n['basic']['nodeName']} for i,n in roots.items() if i not in nm or not eq(n['basic'],nm[i]['basic'])]
terrain=[n for n in a.namelist() if n!='SerializePcgData.json' and (n not in b.namelist() or a.read(n)!=b.read(n))]
scripts=[k for k,v in old['runtimeScripts'].items() if new['runtimeScripts'].get(k,{}).get('content')!=v.get('content')]
clocks=[{'id':i,'position':n['basic']['pos']} for i,n in nm.items() if n['basic']['nodeName']=='time_dial']
result={'preserved_original_asset_roots':len(roots),'changed_original_asset_roots':changes,'terrain_changes':terrain,'script_content_changes':scripts,'castle_sundial_removed':'-1084074086' not in nm,'remaining_sundials':clocks,'existing_castle_root_preserved':om['1743285643']['basic']==nm['1743285643']['basic'],'new_entry_root':json.loads((O/'scene-import.json').read_text())['data']['rootIDs']}
(O/'invariants.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(result)
assert not changes and not terrain and not scripts
assert result['castle_sundial_removed'] and result['existing_castle_root_preserved'] and len(clocks)==1 and clocks[0]['id']=='194003353'
