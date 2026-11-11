import bpy,sys
from pathlib import Path
sys.path.insert(0,str(Path('tools/models').resolve()));import kit
OUT=Path('assets/castle_expand_v5/wall')
bpy.ops.wm.open_mainfile(filepath=str((OUT/'wall-baked.blend').resolve()))
scene=bpy.context.scene;world=scene.world
for name in ['ring_wall_skin','wall_turrets_skin','gatehouse_skin']:
 ob=bpy.data.objects[name];mat=ob.data.materials[0].copy();nt=mat.node_tree;tex=next(n for n in nt.nodes if n.type=='TEX_IMAGE');em=nt.nodes.new('ShaderNodeEmission');nt.links.new(tex.outputs['Color'],em.inputs['Color']);nt.links.new(em.outputs[0],nt.nodes['Material Output'].inputs['Surface']);ob.data.materials[0]=mat
cam=kit.preview_setup();scene.world=world;scene.cycles.samples=24
kit.shot(cam,str(OUT/'ring-wall-back.png'),(-43,44,97),(-5,10,79),48,(1600,1250))
