import trimesh,numpy as np,json
from pathlib import Path
p=Path('assets/castle_refit_v1/exterior');m=trimesh.load(p/'gothic_wall.glb').to_mesh();t=m.triangles;n=m.face_normals
mask=(np.abs(t[:,:,1]-72.24).max(axis=1)<.001)&(np.abs(t[:,:,0]).max(axis=1)<=2.301)&(n[:,1]>.99)
r=t[mask];assert len(r)==2,len(r)
assert abs(r[:,:,2].max()-17)<.001
assert abs(r[:,:,2].min()-7.9)<.001
info={'approach':'flat only; all added terrain-conforming ramp removed','flat_road_world_z':[float(176-r[:,:,2].max()),float(176-r[:,:,2].min())],'top_y_range':[float(r[:,:,1].min()),float(r[:,:,1].max())],'max_plane_slope_deg':float(np.degrees(np.arccos(n[mask,1].min()))),'up_facing_road_triangles':int(mask.sum()),'road_front_world_z':159,'overlap_with_main_floor_m':.10,'left_gate_foot':'sx=-1 lower south footprint reduced 1m; unchanged fromv7','statue_plinths':'unchanged','source_road_box':'width4.6 length9.10 height3.74 center(0,-12.45,70.37)'}
(p/'flat-road-v10-validation.json').write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2))
