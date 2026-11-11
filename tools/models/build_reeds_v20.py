"""Layered grass study: static short colour layer + detailed flexible long blades."""
import bpy,math,random,json,numpy as np
from pathlib import Path
from mathutils import Vector
O=Path('/Users/bytedance/Documents/ChatGPT/DRAGON/assets/reeds_v20');O.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);r=random.Random(1701)
verts=[];faces=[];flex=[];material_ids=[]
# Nine independent root clusters. Every blade has a folded cross section,
# an arching centre line and a pointed tip; no alpha cards or texture silhouettes.
def blade(x,y,angle,h,reach,width,mobile,tone):
    side=Vector((-math.sin(angle),math.cos(angle),0))
    forward=Vector((math.cos(angle),math.sin(angle),0))
    segments=7 if mobile else 4
    start=len(verts)
    twist=r.uniform(-.6,.6)
    for i in range(segments):
        t=i/segments
        profile=(.22+.78*math.sin(math.pi*t))*(1-t)**.65
        centre=Vector((x,y,0))+forward*(reach*t**1.65)+Vector((0,0,h*math.sin(t*1.95)))
        direction=side*math.cos(twist*t)+forward*math.sin(twist*t)
        for j in (-1,0,1):
            v=centre+direction*(width*profile*j)
            if j==0:v.z+=width*profile*.38
            verts.append(tuple(v));flex.append(mobile)
    tip=Vector((x,y,0))+forward*reach+Vector((0,0,h*math.sin(1.95)))
    verts.append(tuple(tip));flex.append(mobile)
    for i in range(segments-1):
        for j in range(2):
            q=start+i*3+j;faces.append((q,q+1,q+4,q+3));material_ids.append(tone)
    tipidx=len(verts)-1;q=start+(segments-1)*3
    faces.extend([(q,q+1,tipidx),(q+1,q+2,tipidx)]);material_ids.extend([tone,tone])
for k in range(9):
    theta=k*2.399963;rad=.66*math.sqrt((k+.25)/9)
    x,y=rad*math.cos(theta),rad*math.sin(theta)
    for j in range(7):
        a=j*math.tau/7+theta+r.uniform(-.3,.3)
        h=r.uniform(.65,1.35)*(1 if k%3 else .85)
        blade(x+r.uniform(-.025,.025),y+r.uniform(-.025,.025),a,h,r.uniform(.35,.78),r.uniform(.022,.037),True,r.randrange(2,7))
    for j in range(6):
        a=j*math.tau/6+theta+.4
        blade(x,y,a,r.uniform(.15,.40),r.uniform(.40,.69),r.uniform(.028,.050),False,r.randrange(5))
me=bpy.data.meshes.new('individual_folded_blades');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('grass_geometry_clumps',me);bpy.context.collection.objects.link(ob)
colours=[(.25,.23,.10,1),(.34,.30,.14,1),(.43,.36,.19,1),(.52,.42,.22,1),(.61,.50,.28,1),(.70,.58,.35,1),(.78,.66,.42,1)]
m=bpy.data.materials.new('straw_vertex_colours');m.use_nodes=True;m.use_backface_culling=False
bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.83
colour=me.color_attributes.new(name='Colour',type='FLOAT_COLOR',domain='CORNER')
for poly,tone in zip(me.polygons,material_ids):
    poly.use_smooth=True
    for li in poly.loop_indices:colour.data[li].color=colours[tone]
attr=m.node_tree.nodes.new('ShaderNodeVertexColor');attr.layer_name='Colour';bs.inputs['Base Color'].default_value=(.62,.49,.27,1);me.materials.append(m)
armdata=bpy.data.armatures.new('grass_bones');arm=bpy.data.objects.new('grass_rig',armdata);bpy.context.collection.objects.link(arm);arm.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for name,z0,z1,parent in [('root',0,.1,None),('reed_lower',.1,.55,'root'),('reed_upper',.55,1.4,'reed_lower')]:
 b=armdata.edit_bones.new(name);b.head=(0,0,z0);b.tail=(0,0,z1)
 if parent:b.parent=armdata.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT');ob.parent=arm;mod=ob.modifiers.new('GrassSkin','ARMATURE');mod.object=arm
vg={n:ob.vertex_groups.new(name=n) for n in ['root','reed_lower','reed_upper']}
for i,v in enumerate(me.vertices):
 z=v.co.z;lo=max(0,min(1,z/.5)) if flex[i] else 0;hi=max(0,min(1,(z-.45)/.8))
 for n,w in {'root':1-lo,'reed_lower':lo*(1-hi),'reed_upper':lo*hi}.items():
  if w>0:vg[n].add([i],w,'REPLACE')
for fr,angle in [(1,0),(31,.04),(61,0),(91,-.04),(121,0)]:
 for name,factor in [('reed_lower',1),('reed_upper',1.3)]:
  b=arm.pose.bones[name];b.rotation_mode='XYZ';b.rotation_euler=(angle*factor,angle*.4,0);b.keyframe_insert('rotation_euler',frame=fr)
arm.animation_data.action.name='wind';bpy.context.scene.frame_set(1);bpy.context.scene.frame_end=121
bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(O/'reed_v20.glb'),export_format='GLB',export_animations=True,export_skins=True)
me.calc_loop_triangles();report={'triangles':len(me.loop_triangles),'high_blades':63,'short_blades':54,'bones':3,'texture':0,'independent_tufts':9,'bytes':(O/'reed_v20.glb').stat().st_size};(O/'model-report.json').write_text(json.dumps(report,indent=2));print(report)
bpy.ops.wm.save_as_mainfile(filepath=str(O/'reed_v20.blend'))
