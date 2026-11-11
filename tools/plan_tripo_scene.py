"""Prepare placements from preserved scene anchors; never writes the live scene."""
from pathlib import Path
import json,zipfile,math,numpy as np
R=Path(__file__).resolve().parents[1];O=R/'assets/tripo/scene_install';B=json.loads((O/'model-bounds.json').read_text())
with zipfile.ZipFile(O/'scene-before.data') as z:
 D=json.loads(z.read('SerializePcgData.json'));hn=next(n for n in z.namelist() if n.startswith('HeightMap_'));H=np.frombuffer(z.read(hn),'<f4').reshape(257,257)*256
old={n['basic']['nodeName']:n for n in D['nodeTransformDatas'] if n['basic']['parentId']==0};plan=[];replace=[]
def ground(x,z):
 i,j=int(x),int(z);a,b=x-i,z-j;return float((H[j,i]*(1-a)+H[j,i+1]*a)*(1-b)+(H[j+1,i]*(1-a)+H[j+1,i+1]*a)*b)
def add(key,name,x,z,height,y=None,yaw=0,active=True,replace_name=None,collision=False):
 bb=B[key];scale=height/(bb['unity_max'][1]-bb['unity_min'][1]);y=ground(x,z) if y is None else y
 p={'asset':key,'name':name,'pos':{'x':x,'y':y-bb['unity_min'][1]*scale,'z':z},'rot':{'x':0,'y':math.sin(math.radians(yaw)/2),'z':0,'w':math.cos(math.radians(yaw)/2)},'scale':dict.fromkeys('xyz',scale),'active':active,'collision':collision}
 if replace_name:
  n=old[replace_name];replace.append({'id':n['id'],'name':replace_name,'before':n['basic']});p['replaces']=n['id']
 plan.append(p);return p
# Exact old anchor positions. Preserve gameplay node names so existing controllers keep working.
for i in range(9):
 n=old[f'sheep_{i}']['basic'];add('sheep_clumped_v4',f'sheep_{i}',n['pos']['x'],n['pos']['z'],1.15,y=n['pos']['y'],yaw=180,replace_name=f'sheep_{i}')
for i in range(3):
 n=old[f'sailboat_{i}']['basic'];add('sailboat_full',f'sailboat_{i}',n['pos']['x'],n['pos']['z'],10.0,y=25.6,yaw=90,replace_name=f'sailboat_{i}',collision=True)
n=old['altar3']['basic'];add('altarWestern','altar3',n['pos']['x'],n['pos']['z'],3.7,y=n['pos']['y'],yaw=180,replace_name='altar3',collision=True)
for i in range(3):
 name=f'rune_{i}';n=old[name]['basic'];add('rune_stone',name,n['pos']['x'],n['pos']['z'],3.2,y=n['pos']['y'],yaw=i*120,replace_name=name,collision=True)
for i,name in enumerate(['mush']+[f'mush_{j}' for j in range(1,6)]):
 n=old[name]['basic'];add('glowing_mushrooms',name,n['pos']['x'],n['pos']['z'],1.2+.15*(i%3),y=n['pos']['y'],yaw=i*57,replace_name=name)
# Existing trunk anchor, retain the user's current glowing canopies.
n=old['holy_tree3']['basic'];add('tree_trunk','holy_tree3',n['pos']['x'],n['pos']['z'],16.8,y=n['pos']['y'],yaw=180,replace_name='holy_tree3',collision=True)
add('horse_unridden_v4','tripo_horse',135,55,2.35,yaw=0)
add('stable','tripo_stable',140,59,4.2,yaw=-90,collision=True)
add('witch_world_v3','tripo_witch',168,140.5,2.05,yaw=-90)
add('witch_staff','tripo_witch_staff',167.25,140.5,1.85,yaw=-90)
add('potion','tripo_potion',169,141,.38,y=ground(169,141)+1.1)
add('camp_stele','tripo_camp_stele',64.7,65,1.9,yaw=-90,collision=True)
add('mushroom_skewer','tripo_mushroom_skewer',61,62.6,.22,y=ground(61,62.6)+.85)
for i,(x,z) in enumerate([(148,60),(151,64),(146,64),(153,60),(149,66)]):add('moonflowers',f'tripo_moonflower_{i}',x,z,.8,yaw=i*71)
# Pool templates and hatch stages are stored inactive, not as visible duplicate props.
add('shadow_spirit','tripo_shadow_template',129,132,1.8,y=ground(129,132)+.5,active=False)
add('watch_lamp','tripo_watch_lamp',65.5,61,1.75,yaw=-90,collision=True)
for i,key in enumerate(['dragon_egg','dragon_egg_2','dragon_egg_3','dragon_egg_4']):add(key,f'tripo_egg_stage_{i}',127,193.2,2.25,y=73.5,active=i==0)
add('tree_single_leaf','tripo_leaf_template',160.5,74,1,y=45,active=False)
for key,x in [('sword',113),('staff',114.5),('bow',116)]:add(key,'tripo_'+key,x,170,1.5,y=72.3,yaw=-90)
for key,x in [('trial_platform_red',123.5),('trial_platform_blue',130.5)]:add(key,'tripo_'+key,x,172,.35,y=32.2)
# Castle decorations last; no shell/wall/room transform is replaced.
for i,x in enumerate([123.2,130.8]):add('castle_armor',f'tripo_castle_armor_{i}',x,174,2.2,y=72.25,yaw=-90,collision=True)
for i,x in enumerate([123,131]):add('castle_statue',f'tripo_castle_statue_{i}',x,166,3.3,y=72.25,yaw=-90,collision=True)
add('castle_throne','tripo_castle_throne',127,185.3,3.8,y=72.88,yaw=-90,collision=True)
for i,z in enumerate([177,181]):add('castle_bookshelf',f'tripo_castle_bookshelf_{i}',114.7,z,3.5,y=72.3,yaw=180,collision=True)
for i,x in enumerate([121,133]):add('castle_window',f'tripo_castle_window_{i}',x,183,4,y=76.3,yaw=0 if i==0 else 180)
add('castle_door','tripo_castle_side_door',140.1,178,4,y=72.3,yaw=180)
for i,x in enumerate([122,132]):add('castle_cornice',f'tripo_castle_cornice_{i}',x,166.8,1,y=72.5,yaw=90,collision=True)
for i,x in enumerate([121,133]):add('castle_gargoyle',f'tripo_castle_gargoyle_{i}',x,168,2,y=80.2,yaw=-90)
# Apply visually verified final world positions after initial bounds fitting.
for fix in json.loads((O/'fit-fixes.json').read_text()):
 for item in plan:
  if item['name']==fix['name']: item['pos']=fix['pos']
(O/'placement-plan.json').write_text(json.dumps({'placements':plan,'replacements':replace,'preserved':['dragon_v8_live','arena_gate','gothic_main','gothic_towers','castle_rooms','holy_canopy3','holy_canopy4'],'note':'Leaf/template and egg stages 1–3 are inactive. No new gameplay completion claimed.'},ensure_ascii=False,indent=2));print(len(plan),'placements',len(replace),'old roots to replace')
