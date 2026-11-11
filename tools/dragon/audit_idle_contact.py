"""Measure exported idle contacts against the editor's unanimated bind pose."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
folder=Path(sys.argv[sys.argv.index('--')+1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(folder/'dragon_v8.glb'))
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
for track in arm.animation_data.nla_tracks:track.mute=True
feet=[f'{p}_foot.{s}' for p in ('front','hind') for s in ('L','R')]
bind={n:arm.matrix_world@arm.data.bones[n].head_local for n in feet}
report={}
for clip in ('idle','perch'):
    action=next(a for a in bpy.data.actions if a.name==clip)
    arm.animation_data.action=action
    if len(action.slots):arm.animation_data.action_slot=action.slots[0]
    samples=[];wing=[]
    for frame in range(int(action.frame_range[0]),int(action.frame_range[1])+1):
        bpy.context.scene.frame_set(frame)
        samples.append({n:arm.matrix_world@arm.pose.bones[n].head for n in feet})
        wing.append((arm.matrix_world@arm.pose.bones['wing_tip0.L'].tail).copy())
    report[clip]={
        'max_ankle_distance_from_bind_m':{n:max((p[n]-bind[n]).length for p in samples) for n in feet},
        'max_ankle_motion_m':max((p[n]-samples[0][n]).length for p in samples for n in feet),
        'wing_tip_span_m':max((a-b).length for a in wing for b in wing)}
assert max(report['idle']['max_ankle_distance_from_bind_m'].values())<.02,report
assert report['idle']['wing_tip_span_m']>1,report
(folder/'idle-contact-audit.json').write_text(json.dumps(report,indent=2))
print('IDLE_CONTACT_AUDIT',json.dumps(report))
