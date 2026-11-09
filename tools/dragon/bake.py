# 用法：Blender --background --python bake.py
# 把三个部件各烘两张图：原贴图转到新 UV；鳞片/AO 遮罩。输出到 assets/dragon/ai/bake/
import os, bpy, bmesh, numpy as np, math
ROOT = '/Users/a1234/Documents/awesomeWRLD/assets/dragon/ai'
Z = np.load(f'{ROOT}/rig2.npz')
pos, uv, idx, region = Z['pos'], Z['uv'], Z['idx'], Z['region']
S = 63.0
os.makedirs(f'{ROOT}/bake', exist_ok=True)
base = None
for part in range(3):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 12
    tris = idx[region[idx].max(1) == part] if part < 2 else idx[region[idx].max(1) == 2]
    used, inv = np.unique(tris, return_inverse=True)
    inv = inv.reshape(-1, 3)
    me = bpy.data.meshes.new('p')
    me.from_pydata([tuple(p * S) for p in pos[used]], [], [tuple(int(v) for v in t) for t in inv])
    me.update()
    uv0 = me.uv_layers.new(name='orig')
    for pl in me.polygons:
        for li in pl.loop_indices:
            vi = me.loops[li].vertex_index
            uv0.data[li].uv = (float(uv[used[vi], 0]), 1 - float(uv[used[vi], 1]))
    me.uv_layers.new(name='bake')
    me.uv_layers.active = me.uv_layers['bake']
    ob = bpy.data.objects.new('p', me); scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(68), island_margin=.0025)
    bpy.ops.object.mode_set(mode='OBJECT')
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons)); me.update()
    m = bpy.data.materials.new('b'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission')
    nt.links.new(em.outputs[0], out.inputs[0])
    uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'orig'
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(f'{ROOT}/hero_base.png')
    nt.links.new(uvn.outputs[0], tx.inputs[0])
    target = bpy.data.images.new('t', 2048, 2048)
    tg = nt.nodes.new('ShaderNodeTexImage'); tg.image = target; nt.nodes.active = tg
    me.materials.append(m)
    # 第一张：原贴图
    nt.links.new(tx.outputs[0], em.inputs[0])
    scene.cycles.bake_type = 'EMIT'
    bpy.ops.object.bake(type='EMIT', margin=8, use_clear=True)
    target.filepath_raw = f'{ROOT}/bake/p{part}_color.png'; target.file_format = 'PNG'; target.save()
    # 第二张：R 鳞缝 G 鳞片随机 B AO
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.feature = 'DISTANCE_TO_EDGE'
    vo.inputs['Scale'].default_value = 1.9 if part != 0 else .4     # 鳞片约半米
    vr = nt.nodes.new('ShaderNodeTexVoronoi'); vr.feature = 'F1'
    vr.inputs['Scale'].default_value = 1.9 if part != 0 else .4
    nt.links.new(geo.outputs['Position'], vo.inputs['Vector'])
    nt.links.new(geo.outputs['Position'], vr.inputs['Vector'])
    ao = nt.nodes.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = 3.0; ao.samples = 16
    cmb = nt.nodes.new('ShaderNodeCombineColor')
    nt.links.new(vo.outputs['Distance'], cmb.inputs[0])
    nt.links.new(vr.outputs['Color'], cmb.inputs[1])
    nt.links.new(ao.outputs['AO'], cmb.inputs[2])
    nt.links.new(cmb.outputs[0], em.inputs[0])
    target2 = bpy.data.images.new('m', 2048, 2048, float_buffer=False)
    tg.image = target2; target2.colorspace_settings.name = 'Non-Color'
    bpy.ops.object.bake(type='EMIT', margin=8, use_clear=True)
    target2.filepath_raw = f'{ROOT}/bake/p{part}_mask.png'; target2.file_format = 'PNG'; target2.save()
    # 新 UV
    uvb = np.zeros((len(used), 2)); seen = np.zeros(len(used), bool)
    # 每个三角形的三个角分别存，避免接缝错位
    corner = np.zeros((len(inv), 3, 2), np.float32)
    for pi, pl in enumerate(me.polygons):
        for ci, li in enumerate(pl.loop_indices):
            corner[pi, ci] = me.uv_layers['bake'].data[li].uv
    tv = np.array([[me.loops[li].vertex_index for li in pl.loop_indices] for pl in me.polygons])
    np.savez(f'{ROOT}/bake/p{part}_uv.npz', used=used, tv=tv, corner=corner)
    print('BAKED', part, len(inv), flush=True)
print('DONE')
