"""Check the exported GLB, including baked IK and looping clip boundaries."""
import bpy, json, sys
from pathlib import Path
from mathutils import Vector
folder=Path(sys.argv[sys.argv.index('--')+1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(folder/'dragon_v8.glb'))
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
scene=bpy.context.scene
for track in arm.animation_data.nla_tracks: track.mute=True
report={'clips':{},'bone_count':len(arm.data.bones)}
endpoints={}
for clip in ['idle','takeoff','fly','land','perch','perch_takeoff','perch_land']:
    action=next(a for a in bpy.data.actions if a.name==clip or a.name.startswith(clip+'_'))
    arm.animation_data.action=action
    if len(action.slots): arm.animation_data.action_slot=action.slots[0]
    start,end=map(int,action.frame_range)
    samples=[];feet=[];socket=[]
    for frame in range(start,end+1):
        scene.frame_set(frame)
        samples.append({b.name:b.matrix.copy() for b in arm.pose.bones})
        feet.append([(arm.matrix_world@arm.pose.bones[f'{p}_foot.{s}'].head)[:] for p in ['front','hind'] for s in ['L','R']])
        socket.append((arm.matrix_world@arm.pose.bones['rider_socket'].head)[:])
    loop=max(max(abs(samples[0][n][r][c]-samples[-1][n][r][c]) for r in range(4) for c in range(4)) for n in samples[0])
    endpoints[clip]=(samples[0],samples[-1])
    drift=max((Vector(p)-Vector(feet[0][j])).length for points in feet for j,p in enumerate(points))
    report['clips'][clip]={'frames':[start,end],'endpoint_matrix_delta':loop,'max_ankle_drift_m':drift,'seat_bounds':[[min(p[i] for p in socket),max(p[i] for p in socket)] for i in range(3)]}
    if clip in ['idle','perch']: assert drift<.02,('Idle foot sliding',drift)
    if clip in ['land','perch_land']:
        planted=feet[round((end-start)*.65)+1:]
        contact_drift=max((Vector(p)-Vector(planted[0][j])).length for points in planted for j,p in enumerate(points))
        report['clips'][clip]['contact_ankle_drift_m']=contact_drift
        assert contact_drift<.02,('Landing foot sliding',contact_drift)
        assert max(p[2] for p in socket)-min(p[2] for p in socket)>.5, 'Missing vertical impact cushioning'
    if clip in ['idle','fly','perch']: assert loop<.0001,('Loop discontinuity',clip,loop)
    assert all(all(abs(x)<100 for x in point) for point in socket)
report['transitions']={}
for a,ai,b,bi in [('idle',0,'takeoff',0),('takeoff',1,'fly',0),('fly',0,'land',0),('land',1,'idle',0),('perch',0,'perch_takeoff',0),('perch_takeoff',1,'fly',0),('fly',0,'perch_land',0),('perch_land',1,'perch',0)]:
    delta=max(max(abs(endpoints[a][ai][n][r][c]-endpoints[b][bi][n][r][c]) for r in range(4) for c in range(4)) for n in endpoints[a][ai])
    report['transitions'][a+'->'+b]=delta
    assert delta<.001,('Clip transition jump',a,b,delta)
# Four nonzero normalized influences are required by the editor importer.
for ob in bpy.context.scene.objects:
    if ob.type!='MESH' or not any(m.type=='ARMATURE' for m in ob.modifiers):continue
    for v in ob.data.vertices:
        values=[g.weight for g in v.groups if g.weight>1e-5]
        assert 0<len(values)<=4,(ob.name,v.index,len(values),ob.parent_type)
        assert abs(sum(values)-1)<.0001
(folder/'export-check.json').write_text(json.dumps(report,indent=2))
print('EXPORT_CHECK',json.dumps(report))
