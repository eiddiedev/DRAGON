"""Verify the additive sample leaves the saved original scene intact."""
import json,zipfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'assets/castle_expand_v5'
live=Path('/Users/bytedance/Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data')
a=zipfile.ZipFile(O/'scene-before.data');b=zipfile.ZipFile(live)
old=json.loads(a.read('SerializePcgData.json'));new=json.loads(b.read('SerializePcgData.json'))
om={str(n['id']):n for n in old['nodeTransformDatas']};nm={str(n['id']):n for n in new['nodeTransformDatas']}
def eq(x,y):
 if isinstance(x,(int,float)) and isinstance(y,(int,float)):return abs(x-y)<1e-4
 if isinstance(x,dict) and isinstance(y,dict):return x.keys()==y.keys() and all(eq(v,y[k]) for k,v in x.items())
 if isinstance(x,list) and isinstance(y,list):return len(x)==len(y) and all(eq(a,b) for a,b in zip(x,y))
 return x==y
authored={i:n for i,n in om.items() if n.get('editor',{}).get('assetData')}
changes=[{'id':i,'name':n['basic']['nodeName']} for i,n in authored.items() if i not in nm or any(not eq(n.get(k),nm[i].get(k)) for k in ('basic','physics','resource','editor'))]
def descendants(nodes,roots):
 ids=set(roots)
 while True:
  more={i for i,n in nodes.items() if str(n['basic'].get('parentId')) in ids}
  if more<=ids:return ids
  ids|=more
protected=descendants(om,{'1743285643','-1788843370','-1910942728'})
empty_editor={'assetData':None,'editorOnlyData':{'isLock':False,'isGroupRoot':False,'editorData':''}}
normalized_editor_defaults=[]
def protected_equal(i):
 if i not in nm:return False
 before,after=dict(om[i]),dict(nm[i])
 # The host adds an empty editor record to GLB child receivers on resave.
 # Accept only this exact empty default; transforms/resources/physics remain strict.
 if 'editor' not in before and after.get('editor')==empty_editor:
  after.pop('editor');normalized_editor_defaults.append(i)
 return eq(before,after)
castle_changes=[i for i in protected if not protected_equal(i)]
terrain=[n for n in a.namelist() if n!='SerializePcgData.json' and (n not in b.namelist() or a.read(n)!=b.read(n))]
scripts=[k for k,v in old['runtimeScripts'].items() if new['runtimeScripts'].get(k,{}).get('content')!=v.get('content')]
settings=[k for k in old if k not in ('nodeTransformDatas','runtimeScripts','resourceRefs','spawnPointData') and not eq(old[k],new[k])]
# The host regenerates spawn/water/model-child identifiers on loading. Compare
# the actual spawn configuration rather than the regenerated integer reference.
spawn_equal=eq([om[str(n['id'])]['basic'] for n in old['spawnPointData']],[nm[str(n['id'])]['basic'] for n in new['spawnPointData']])
sample_roots=json.loads((O/'scene-import.json').read_text())['data']['rootIDs']
added=[nm[i] for i in descendants(nm,set(sample_roots))]
blocking=[n['basic']['nodeName'] for n in added if (n.get('physics',{}).get('physicsColliderData') or {}).get('enableCollision')]
result={'original_node_count':len(om),'preserved_authored_roots':len(authored),'changed_authored_roots':changes,'protected_castle_nodes':len(protected),'changed_castle_nodes':castle_changes,'terrain_changes':terrain,'original_script_changes':scripts,'settings_changes':settings,'spawn_configuration_preserved':spawn_equal,'sample_nodes':len(added),'added_collision_nodes':blocking,'host_generated_ids_or_animated_child_poses_not_used_as_layout_evidence':True}
result['host_added_empty_editor_records']=normalized_editor_defaults
(O/'invariants.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(result)
assert not changes and not castle_changes and not terrain and not scripts and not settings and not blocking and spawn_equal
