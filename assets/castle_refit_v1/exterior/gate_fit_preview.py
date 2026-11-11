import bpy,sys,zipfile,numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path('tools/models').resolve()));import kit
kit.reset();bpy.ops.import_scene.gltf(filepath=str(Path('assets/castle_refit_v1/exterior/gothic_wall-GI.glb').resolve()))
z=zipfile.ZipFile('assets/castle_refit_v1/scene-before.data');h=np.frombuffer(z.read(next(n for n in z.namelist() if n.startswith('HeightMap_'))),'<f4').reshape(257,257)*256
vs=[];fs=[];nx,ny=41,41
for j in range(ny):
 for i in range(nx):
  x=-10+i*.5;y=-30+j*.5;wx,wz=127+x,176+y;a,b=int(wx),int(wz);u,v=wx-a,wz-b;hh=(h[b,a]*(1-u)+h[b,a+1]*u)*(1-v)+(h[b+1,a]*(1-u)+h[b+1,a+1]*u)*v;vs.append((x,y,float(hh)))
for j in range(ny-1):
 for i in range(nx-1):
  a=j*nx+i;fs.extend([(a,a+1,a+nx+1),(a,a+nx+1,a+nx)])
m=bpy.data.meshes.new('actual_heightmap_patch');m.from_pydata(vs,[],fs);m.update();o=bpy.data.objects.new('actual_heightmap_patch',m);bpy.context.scene.collection.objects.link(o)
for name,color in [('grass','#577348'),('rock','#727176')]:
 mat=bpy.data.materials.new(name);mat.diffuse_color=kit.srgb(color);mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=kit.srgb(color);mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.9;m.materials.append(mat)
for f in m.polygons:f.material_index=int(f.normal.z<.65)
cam=kit.preview_setup();bpy.context.scene.cycles.samples=20
kit.shot(cam,'assets/castle_refit_v1/exterior/gate-terrain-final.png',(2,-28,74),(0,-18.5,73.5),34,(1200,1000))
kit.shot(cam,'assets/castle_refit_v1/exterior/gate-left-foot-final.png',(-8,-23,71.5),(-4.1,-18.5,70.6),35,(1100,900))
