"""Blender background: rig_v8.py -- <source.glb> <output-dir>.

Dragon-specific armature, bounded four-weight skinning, and distinct motion
clips. All landmarks are in the original normalized glTF coordinate system.
The .blend is retained for visual weight/animation refinement.
"""
import bpy
import math
import json
import sys
from pathlib import Path
import numpy as np
from mathutils import Vector, Quaternion

src, output = sys.argv[sys.argv.index('--')+1:]
out=Path(output);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
mesh.name='dragon_v8'
bpy.context.view_layer.objects.active=mesh;mesh.select_set(True)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
# Weld duplicate position vertices while keeping UVs on face corners.
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=.000002)
bpy.ops.object.mode_set(mode='OBJECT')
for p in mesh.data.polygons:p.use_smooth=True

def cv(p): return Vector((p[0],-p[2],p[1]))
defs={}
def bone(name,a,b,parent=None): defs[name]=(np.array(a,float),np.array(b,float),parent)
bone('root',(0,.12,.16),(0,.17,.16))
bone('pelvis',(0,.17,.13),(0,.19,.21),'root')
bone('spine',(0,.19,.21),(0,.23,.30),'pelvis')
bone('chest',(0,.23,.30),(0,.28,.35),'spine')
bone('neck_base',(0,.28,.35),(0,.335,.365),'chest')
bone('neck_mid',(0,.335,.365),(0,.385,.39),'neck_base')
bone('head',(0,.385,.39),(0,.395,.465),'neck_mid')
bone('jaw',(0,.375,.405),(0,.365,.466),'head')
bone('rider_socket',(0,.275,.235),(0,.295,.235),'spine')
tail=[(0,.17,.13),(0,.145,.055),(0,.12,-.04),(0,.105,-.13),(0,.087,-.23),(0,.075,-.32),(0,.075,-.41),(0,.09,-.48)]
for i in range(len(tail)-1):bone(f'tail_{i}',tail[i],tail[i+1],'pelvis' if i==0 else f'tail_{i-1}')
for side,s in [('L',1),('R',-1)]:
    def p(x,y,z):return(s*x,y,z)
    bone(f'front_upper.{side}',p(.065,.235,.35),p(.085,.13,.36),'chest')
    bone(f'front_lower.{side}',p(.085,.13,.36),p(.08,.035,.40),f'front_upper.{side}')
    bone(f'front_foot.{side}',p(.08,.035,.40),p(.08,.015,.455),f'front_lower.{side}')
    bone(f'hind_upper.{side}',p(.06,.17,.13),p(.085,.10,.18),'pelvis')
    bone(f'hind_lower.{side}',p(.085,.10,.18),p(.065,.045,.10),f'hind_upper.{side}')
    bone(f'hind_foot.{side}',p(.065,.045,.10),p(.075,.015,.16),f'hind_lower.{side}')
    bone(f'wing_upper.{side}',p(.055,.27,.33),p(.14,.30,.32),'chest')
    bone(f'wing_fore.{side}',p(.14,.30,.32),p(.25,.425,.35),f'wing_upper.{side}')
    for i,end in enumerate([p(.492,.29,.22),p(.37,.22,.225),p(.25,.205,.25),p(.145,.235,.28)]):
        wrist=np.array(p(.25,.425,.35));end=np.array(end)
        mid=wrist+(end-wrist)*.55
        bone(f'wing_finger{i}.{side}',wrist,mid,f'wing_fore.{side}')
        bone(f'wing_tip{i}.{side}',mid,end,f'wing_finger{i}.{side}')

# Independent ankle targets keep all four feet planted while the torso breathes
# or absorbs an impact. IK is baked into deform-bone transforms on export.
for side in ('L','R'):
    for part in ('front','hind'):
        a,b,_=defs[f'{part}_foot.{side}']
        bone(f'contact_{part}.{side}',a,b)

bpy.ops.object.select_all(action='DESELECT')
arm_data=bpy.data.armatures.new('dragon_skeleton')
arm=bpy.data.objects.new('dragon_rig',arm_data);bpy.context.collection.objects.link(arm)
arm.select_set(True);bpy.context.view_layer.objects.active=arm
bpy.ops.object.mode_set(mode='EDIT')
for name,(a,b,parent) in defs.items():
    eb=arm_data.edit_bones.new(name);eb.head=cv(a);eb.tail=cv(b)
    if parent:eb.parent=arm_data.edit_bones[parent]
    eb.use_deform=name not in ('root','rider_socket') and not name.startswith('contact_')
bpy.ops.object.mode_set(mode='OBJECT');arm.show_in_front=True
contacts=[]
for side in ('L','R'):
    for part in ('front','hind'):
        target=f'contact_{part}.{side}'
        ik=arm.pose.bones[f'{part}_lower.{side}'].constraints.new('IK')
        ik.target=arm;ik.subtarget=target;ik.chain_count=2;ik.use_stretch=False
        rot=arm.pose.bones[f'{part}_foot.{side}'].constraints.new('COPY_ROTATION')
        rot.target=arm;rot.subtarget=target;rot.owner_space='POSE';rot.target_space='POSE'
        contacts.extend((ik,rot))
mesh.parent=arm
mod=mesh.modifiers.new('DragonSkin','ARMATURE');mod.object=arm

names=[n for n in defs if n not in ('root','rider_socket') and not n.startswith('contact_')]
v=np.array([(p.co.x,p.co.z,-p.co.y) for p in mesh.data.vertices])
dist=np.zeros((len(v),len(names)))
for j,name in enumerate(names):
    a,b,_=defs[name];ab=b-a;t=np.clip(((v-a)*ab).sum(1)/(ab@ab),0,1)
    dist[:,j]=np.linalg.norm(v-(a+t[:,None]*ab),axis=1)
allowed=np.zeros_like(dist,dtype=bool)
for i,(x,y,z) in enumerate(v):
    side='L' if x>=0 else 'R'
    if abs(x)>.115 and y>.18:
        candidates=[n for n in names if n.startswith('wing_') and n.endswith(side)]
        if abs(x)<.15:candidates+=['chest']
    elif z<.065:
        candidates=[n for n in names if n.startswith('tail_')]+['pelvis']
    elif y>.30:
        candidates=['neck_base','neck_mid','head']
        if z>.435 and y<.382:candidates+=['jaw']
    elif abs(x)>.035 and y<.215 and z>.285:
        candidates=[f'front_{n}.{side}' for n in ('upper','lower','foot')]+['chest']
    elif abs(x)>.035 and y<.19 and z<.245:
        candidates=[f'hind_{n}.{side}' for n in ('upper','lower','foot')]+['pelvis','spine']
    else:
        candidates=['pelvis','spine','chest','neck_base','neck_mid']
        if y>.24 and abs(x)>.06:candidates += [f'wing_upper.{side}']
        if z<.13:candidates+=['tail_0','tail_1']
    for n in candidates:allowed[i,names.index(n)]=True
dist[~allowed]=100
weights=np.exp(-np.square(dist/.032))
weights+=allowed*1e-12
weights/=weights.sum(1)[:,None]
# Smooth weights across welded topology, but do not diffuse across semantic
# regions (wing membrane must never inherit a nearby front-leg bone).
edges=np.array([e.vertices[:] for e in mesh.data.edges],dtype=int)
degree=np.bincount(edges.reshape(-1),minlength=len(v)).clip(1)
for _ in range(3):
    neighbors=np.zeros_like(weights)
    np.add.at(neighbors,edges[:,0],weights[edges[:,1]])
    np.add.at(neighbors,edges[:,1],weights[edges[:,0]])
    weights=(weights*.75+neighbors/degree[:,None]*.25)*allowed
    weights/=weights.sum(1)[:,None]
top=np.argsort(weights,axis=1)[:,-4:]
mask=np.zeros_like(weights);np.put_along_axis(mask,top,1,axis=1)
weights*=mask;weights/=weights.sum(1)[:,None]
for j,n in enumerate(names):
    vg=mesh.vertex_groups.new(name=n)
    for i in np.flatnonzero(weights[:,j]>1e-5):vg.add([int(i)],float(weights[i,j]),'REPLACE')

# A small saddle follows the spine/socket, keeping a clear seat above the ridges.
def saddle_part(name,loc,scale,color):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=cv(loc))
    ob=bpy.context.object;ob.name=name;ob.scale=(scale[0],scale[2],scale[1])
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mat=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color=(*color,1);mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.7
    ob.data.materials.append(mat)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    ob.parent=arm;mo=ob.modifiers.new('SaddleSkin','ARMATURE');mo.object=arm
    vg=ob.vertex_groups.new(name='spine');vg.add(list(range(len(ob.data.vertices))),1,'REPLACE')
    for p in ob.data.polygons:p.use_smooth=True
    return ob
saddle_part('saddle_leather',(0,.267,.235),(.025,.008,.032),(.10,.045,.025))
saddle_part('saddle_back',(0,.275,.21),(.025,.014,.006),(.14,.07,.03))
saddle_part('saddle_front',(0,.274,.263),(.026,.010,.005),(.24,.15,.045))

def turn(pb,axis,angle):
    local=pb.bone.matrix_local.to_3x3().inverted()@Vector(axis)
    pb.rotation_quaternion=pb.rotation_quaternion@Quaternion(local,math.radians(angle))

fps=30;bpy.context.scene.render.fps=fps
clips={'idle':6.0,'takeoff':1.8,'fly':1.4,'land':2.8,'perch':6.0,'perch_takeoff':1.8,'perch_land':2.8}
def smooth(x):
    x=min(1,max(0,x));return x*x*(3-2*x)
for clip_name,duration in clips.items():
    perched=clip_name.startswith('perch')
    clip={'perch':'idle','perch_takeoff':'takeoff','perch_land':'land'}.get(clip_name,clip_name)
    action=bpy.data.actions.new(clip_name);arm.animation_data_create();arm.animation_data.action=action
    frames=round(duration*fps)
    for frame in range(frames+1):
        t=frame/fps;u=t/duration
        for pb in arm.pose.bones:
            pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion();pb.location=(0,0,0);pb.scale=(1,1,1)
        if clip=='idle':flight=0;flap=.28*math.sin(u*math.tau);breath=math.sin(u*math.tau)
        elif clip=='fly':flight=1;flap=math.sin(u*math.tau);breath=0
        elif clip=='takeoff':flight=smooth((u-.25)/.6);flap=math.sin(u*math.tau)*flight;breath=0
        else:flight=1-smooth(u/.65);flap=math.sin(u*math.tau)*flight;breath=0
        # Crouched alert perch with continuously beating open wings. Mountain
        # perch has raised foreclaws; ordinary landings remain on level ground.
        crouch=1 if clip=='idle' else 0 if clip=='fly' else 1-smooth(u/.55) if clip=='takeoff' else smooth((u-.65)/.35)
        proud=(1-flight) if perched else 0
        crouch_depth=.025 if perched else .055
        for side in ('L','R'):
            target=arm.pose.bones[f'contact_front.{side}']
            # Convert armature-space vertical to the independent target's axes.
            target.location=target.bone.matrix_local.to_3x3().inverted()@Vector((0,0,.12*proud))
        for constraint in contacts:
            constraint.influence=1-flight
            constraint.keyframe_insert(data_path='influence',frame=frame)
        arm.pose.bones['root'].location.y=-crouch_depth*crouch+.0015*breath
        if clip=='takeoff':arm.pose.bones['root'].location.y=-crouch_depth*crouch+(-.012*math.sin(min(u/.35,1)*math.pi) if u<.35 else 0)
        if clip=='land':arm.pose.bones['root'].location.y=-crouch_depth*crouch-.012*math.sin(math.pi*max(0,(u-.65)/.35))**2
        turn(arm.pose.bones['spine'],(1,0,0),crouch*6-30*proud+breath*.7)
        turn(arm.pose.bones['neck_base'],(1,0,0),crouch*8-20*proud-flight*12+breath*1.2)
        turn(arm.pose.bones['neck_mid'],(0,0,1),2*math.sin(u*math.tau)*(1-flight))
        turn(arm.pose.bones['head'],(1,0,0),crouch*2-10*proud+flight*6+breath*.8)
        for i in range(7):
            turn(arm.pose.bones[f'tail_{i}'],(0,0,1),crouch*(16 if i<5 else 12)+math.sin(u*math.tau-i*.45)*(1.5+flight*1.5))
            turn(arm.pose.bones[f'tail_{i}'],(1,0,0),flight*1.4)
        for side,s in [('L',1),('R',-1)]:
            turn(arm.pose.bones[f'wing_upper.{side}'],(0,1,0),s*(flap*32+(1-flight)*-8))
            turn(arm.pose.bones[f'wing_upper.{side}'],(0,0,1),s*(1-flight)*10)
            turn(arm.pose.bones[f'wing_fore.{side}'],(0,1,0),s*(math.sin(u*math.tau-.55)*12*flight))
            turn(arm.pose.bones[f'wing_fore.{side}'],(0,0,1),s*(1-flight)*8)
            for i in range(4):
                turn(arm.pose.bones[f'wing_finger{i}.{side}'],(0,1,0),s*(math.sin(u*math.tau-.9)*6*flight+(1-flight)*4))
                turn(arm.pose.bones[f'wing_tip{i}.{side}'],(0,1,0),s*math.sin(u*math.tau-1.2)*4*flight)
            for part in ('front','hind'):
                # Flight limbs fold in two stages after push-off; delayed hind
                # legs make takeoff read as a whole-body action, not a rigid lift.
                tuck=flight
                if clip=='takeoff':tuck=smooth((u-(.28 if part=='front' else .38))/.52)
                swing=math.sin(u*math.tau)*(3 if part=='front' else 4)*flight
                turn(arm.pose.bones[f'{part}_upper.{side}'],(1,0,0),tuck*(58 if part=='front' else -42)+swing)
                turn(arm.pose.bones[f'{part}_lower.{side}'],(1,0,0),tuck*(-88 if part=='front' else 82)-swing*.65)
                turn(arm.pose.bones[f'{part}_foot.{side}'],(1,0,0),tuck*26)
        for pb in arm.pose.bones:
            pb.keyframe_insert(data_path='rotation_quaternion',frame=frame,group=pb.name)
            if pb.name=='root' or pb.name.startswith('contact_'):pb.keyframe_insert(data_path='location',frame=frame,group=pb.name)
    action.use_fake_user=True
    track=arm.animation_data.nla_tracks.new();track.name=clip_name
    strip=track.strips.new(clip_name,0,action);strip.name=clip_name;track.mute=True
arm.animation_data.action=None
for pb in arm.pose.bones:pb.rotation_quaternion=Quaternion();pb.location=(0,0,0)
# Export in real world meters: 54 m wingspan, about 28 m high.
arm.scale=(54,54,54)
bpy.context.scene.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str((out/'dragon_rig.blend').resolve()))
bpy.ops.export_scene.gltf(filepath=str((out/'dragon_v8.glb').resolve()),export_format='GLB',export_animations=True,export_animation_mode='NLA_TRACKS',export_nla_strips=True,export_anim_single_armature=True,export_force_sampling=True,export_skins=True,export_yup=True)
report=dict(vertices=len(v),bones=len(defs),clips=clips,max_influences=int((weights>1e-5).sum(1).max()),max_weight_error=float(abs(weights.sum(1)-1).max()),socket=[0,.275*54,.235*54],wingspan=54)
(out/'rig-report.json').write_text(json.dumps(report,indent=2))
print('RIG_REPORT',report)
