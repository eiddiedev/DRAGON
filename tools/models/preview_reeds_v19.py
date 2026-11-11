import bpy,math,random
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/Users/bytedance/Documents/ChatGPT/DRAGON/assets/reeds_v19/reed_v19.glb')
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');r=random.Random(3)
# Static preview reuses the rest mesh, preserving the actual modeled curvature.
mesh.modifiers.clear();mesh.parent=None;bpy.data.objects.remove(rig,do_unlink=True)
for j in range(5):
 for i in range(5):
  ob=mesh.copy();ob.data=mesh.data;bpy.context.collection.objects.link(ob);ob.location=((i-2)*1.0+r.uniform(-.15,.15),(j-2)*1.0+r.uniform(-.15,.15),0);ob.rotation_euler[2]=r.uniform(-math.pi,math.pi);ob.scale=(1.15,1.15,r.uniform(.85,1.2))
bpy.data.objects.remove(mesh,do_unlink=True)
bpy.ops.mesh.primitive_plane_add(size=200);ground=bpy.context.object;m=bpy.data.materials.new('earth');m.diffuse_color=(.17,.12,.065,1);m.use_nodes=True;m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.17,.12,.065,1);ground.data.materials.append(m)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.transparent_max_bounces=64;s.world=bpy.data.worlds.new('world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.72,.75,.8,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.7
bpy.ops.object.light_add(type='SUN');bpy.context.object.data.energy=2;bpy.context.object.rotation_euler=(.8,-.4,-.6)
bpy.ops.object.camera_add(location=(3,-6,2));cam=bpy.context.object;cam.rotation_euler=(Vector((0,1,.6))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=35;s.camera=cam;s.render.resolution_x=1000;s.render.resolution_y=700;s.render.resolution_percentage=100;s.render.filepath='/Users/bytedance/Documents/ChatGPT/DRAGON/assets/reeds_v19/golden_field.png';bpy.ops.render.render(write_still=True)
cam.location=(0,0,10);cam.rotation_euler=(0,0,0);cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=s.render.filepath.replace('golden_field.png','top_view.png');bpy.ops.render.render(write_still=True)
