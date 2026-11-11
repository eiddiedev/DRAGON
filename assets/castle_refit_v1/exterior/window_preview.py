import bpy,sys
from pathlib import Path
sys.path.insert(0,str(Path('tools/models').resolve()));import kit
kit.reset();bpy.ops.import_scene.gltf(filepath=str(Path('assets/castle_refit_v1/exterior/gothic_main-GI.glb').resolve()));cam=kit.preview_setup();bpy.context.scene.cycles.samples=16
kit.shot(cam,'assets/castle_refit_v1/exterior/rear-window-final.png',(0,3,81.0),(0,13.1,82.5),32,(1000,800))
