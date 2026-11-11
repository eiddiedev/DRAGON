import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path('/Users/bytedance/Documents/ChatGPT/DRAGON');O=R/'assets/castle_refit_v1/interior'
bpy.ops.wm.read_factory_settings(use_empty=True)
for name in ['castle_rooms.glb','castle_rooms_glow.glb']:bpy.ops.import_scene.gltf(filepath=str(O/name))
# Original shell used only as contextual occlusion, not part of delivered interior.
bpy.ops.import_scene.gltf(filepath=str(R/'assets/castle3/gothic_main.glb'))
context=list(bpy.context.selected_objects)
for ob in context:
 if ob.type=='MESH':
  for mat in ob.data.materials:
   if mat and mat.use_nodes:
    bs=mat.node_tree.nodes.get('Principled BSDF')
    if bs:
     for link in list(bs.inputs['Base Color'].links):mat.node_tree.links.remove(link)
     bs.inputs['Base Color'].default_value=(.16,.14,.21,1)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
world=bpy.data.worlds.new('Ambient');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.36,.5,1);world.node_tree.nodes['Background'].inputs[1].default_value=.25;scene.world=world
for l in json.loads((O/'lighting-plan.json').read_text())['lights']:
 data=bpy.data.lights.new(l['name'],'POINT');data.energy=l['energy_watts'];data.color=l['color'];data.shadow_soft_size=l['radius'];ob=bpy.data.objects.new(l['name'],data);scene.collection.objects.link(ob);ob.location=l['position_blender']
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.clip_end=300
scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=1
for name,loc,at,lens in [('hall-clean',(0,-7,74.2),(0,9,75.8),20),('library-clean',(-7.2,3.1,74.4),(-12.7,3.1,74.3),22),('dining',(7.2,-.1,74.1),(11,4,73.9),22)]:
 cam.location=loc;cam.rotation_euler=(Vector(at)-Vector(loc)).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;scene.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True)
