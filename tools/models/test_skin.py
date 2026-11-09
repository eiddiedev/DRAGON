# 用法：Blender --background --python test_skin.py -- <输出目录>
# 探针：蒙皮+动画、顶点色、多物体层级，导入后看引擎保留了什么。
import math, os, sys
import bpy, bmesh
from mathutils import Vector
OUT = sys.argv[sys.argv.index('--') + 1]

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def export(name):
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, name + '.glb'), export_format='GLB', use_selection=True, export_yup=True, export_animations=True, export_skins=True, export_vertex_color='ACTIVE', export_all_vertex_colors=True)

# ---- 蒙皮
reset()
bm = bmesh.new()
rings = []
N = 40
for i in range(N + 1):
    z = i / N * 8
    rings.append([bm.verts.new((math.cos(a / 12 * math.tau) * .5, math.sin(a / 12 * math.tau) * .5, z)) for a in range(12)])
for a, b in zip(rings, rings[1:]):
    for s in range(12):
        bm.faces.new((a[s], a[(s + 1) % 12], b[(s + 1) % 12], b[s]))
me = bpy.data.meshes.new('skin_mesh')
bm.to_mesh(me)
ob = bpy.data.objects.new('skin_mesh', me)
bpy.context.scene.collection.objects.link(ob)
mat = bpy.data.materials.new('m')
mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.2, .6, 1, 1)
me.materials.append(mat)
arm = bpy.data.armatures.new('rig')
ao = bpy.data.objects.new('rig', arm)
bpy.context.scene.collection.objects.link(ao)
bpy.context.view_layer.objects.active = ao
bpy.ops.object.mode_set(mode='EDIT')
B = 8
prev = None
for i in range(B):
    e = arm.edit_bones.new(f'b{i}')
    e.head = (0, 0, i)
    e.tail = (0, 0, i + 1)
    if prev:
        e.parent = prev
        e.use_connect = True
    prev = e
bpy.ops.object.mode_set(mode='OBJECT')
for i in range(B):
    ob.vertex_groups.new(name=f'b{i}')
for v in me.vertices:
    t = v.co.z - .5
    i0 = max(0, min(B - 1, int(math.floor(t))))
    i1 = min(B - 1, i0 + 1)
    f = max(0, min(1, t - i0))
    ob.vertex_groups[f'b{i0}'].add([v.index], 1 - f, 'REPLACE')
    if i1 != i0:
        ob.vertex_groups[f'b{i1}'].add([v.index], f, 'REPLACE')
mod = ob.modifiers.new('a', 'ARMATURE')
mod.object = ao
ob.parent = ao
ao.animation_data_create()
act = bpy.data.actions.new('sway')
ao.animation_data.action = act
bpy.context.view_layer.objects.active = ao
bpy.ops.object.mode_set(mode='POSE')
for f in range(0, 61, 5):
    for i in range(B):
        pb = ao.pose.bones[f'b{i}']
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)
        pb.rotation_euler.x = .3 * math.sin(f / 60 * math.tau + i * .7)
        pb.keyframe_insert('rotation_euler', frame=f)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.scene.frame_start, bpy.context.scene.frame_end = 0, 60
export('test_skin')

# ---- 顶点色（无贴图）
reset()
bm = bmesh.new()
col = bm.loops.layers.color.new('Col')
for i in range(5):
    vs = [bm.verts.new((i * 1.2 + x, 0, z)) for x, z in ((-.5, 0), (.5, 0), (.5, 4), (-.5, 4))]
    f = bm.faces.new(vs)
    cs = {0: (1, 0, 0, 1), 1: (0, 1, 0, 1), 2: (0, 0, 1, 1), 3: (1, 1, 0, 1), 4: (1, 1, 1, 1)}[i]
    for l in f.loops:
        l[col] = cs if l.vert.co.z > .1 else (0, 0, 0, 1)
me = bpy.data.meshes.new('vcol')
bm.to_mesh(me)
ob = bpy.data.objects.new('vcol', me)
bpy.context.scene.collection.objects.link(ob)
mat = bpy.data.materials.new('vc')
mat.use_nodes = True
nt = mat.node_tree
a = nt.nodes.new('ShaderNodeVertexColor')
a.layer_name = 'Col'
nt.links.new(a.outputs['Color'], nt.nodes['Principled BSDF'].inputs['Base Color'])
me.materials.append(mat)
export('test_vcol')

# ---- 多物体层级
reset()
def box(name, loc, size, parent=None, c=(1, .4, .2, 1)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    if parent:
        o.parent = parent
        o.matrix_parent_inverse = parent.matrix_world.inverted()
    return o
b = box('body', (0, 0, 2), (3, 1, 1))
h = box('head', (2, 0, 3), (1, 1, 1), b)
j = box('jaw', (2.8, 0, 2.6), (.8, .5, .3), h)
bpy.context.view_layer.update()
export('test_parts')
print('OK')
