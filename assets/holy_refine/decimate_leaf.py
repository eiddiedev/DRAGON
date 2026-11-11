import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='/Users/bytedance/Documents/ChatGPT/DRAGON/assets/tripo/approved_batch/tree_single_leaf_source.glb')
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  bpy.context.view_layer.objects.active=o;o.select_set(True);m=o.modifiers.new('Leaf_budget','DECIMATE');m.ratio=64/458;bpy.ops.object.modifier_apply(modifier=m.name)
bpy.ops.export_scene.gltf(filepath='/Users/bytedance/Documents/ChatGPT/DRAGON/assets/holy_refine/single_leaf_64.glb',export_format='GLB')
