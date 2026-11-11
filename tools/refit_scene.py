#!/usr/bin/env python3
"""Prepare terrain-aware placement changes without overwriting the live editor.

Reads the current scene heightmap; writes a reviewable plan and replacement
meshes. Applying a plan is separate and requires the editor project to be closed.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import sys
import zipfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/models'))
from glbw import Geo, write_glb


def sample(h, x, z):
    x, z = np.clip(x, 0, 255.99999), np.clip(z, 0, 255.99999)
    a, b = np.asarray(x, dtype=int), np.asarray(z, dtype=int)
    u, v = x - a, z - b
    return (h[b, a] * (1-u) + h[b, a+1] * u) * (1-v) + (h[b+1, a] * (1-u) + h[b+1, a+1] * u) * v


def warp_glb(src, dst, old_h, new_h):
    """Rebase baked scenery vertically, preserving all texture and index data.

    These legacy models use (E,U,-N) around world origin (128,0,128).
    Terrain offsets are smooth, so iron rails remain joined at their endpoints.
    """
    raw = src.read_bytes()
    size, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4e4f534a
    doc = json.loads(raw[20:20+size])
    bstart = 20 + size + 8
    binary = bytearray(raw[bstart:])
    modified = set()
    modified_normals = set()
    changes = []
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            ai = prim['attributes']['POSITION']
            if ai in modified:
                continue
            modified.add(ai)
            acc = doc['accessors'][ai]
            view = doc['bufferViews'][acc['bufferView']]
            assert acc['componentType'] == 5126 and acc['type'] == 'VEC3'
            off = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
            verts = np.ndarray((acc['count'], 3), '<f4', binary, off, strides=(view.get('byteStride', 12), 4))
            x, z = 128 + verts[:, 0], 128 - verts[:, 2]
            dy = sample(new_h, x, z) - sample(old_h, x, z)
            verts[:, 1] += dy
            acc['min'], acc['max'] = verts.min(0).tolist(), verts.max(0).tolist()
            ni = prim['attributes'].get('NORMAL')
            if ni is not None and ni not in modified_normals:
                modified_normals.add(ni)
                na = doc['accessors'][ni]
                nv = doc['bufferViews'][na['bufferView']]
                assert na['componentType'] == 5126 and na['count'] == acc['count']
                no = nv.get('byteOffset', 0) + na.get('byteOffset', 0)
                normals = np.ndarray((na['count'], 3), '<f4', binary, no, strides=(nv.get('byteStride', 12), 4))
                delta_h = new_h - old_h
                dx = (sample(delta_h,x+.05,z)-sample(delta_h,x-.05,z))/.1
                dn = (sample(delta_h,x,z+.05)-sample(delta_h,x,z-.05))/.1
                # Inverse-transpose Jacobian for y'=y+f(x,-z): keeps lighting
                # consistent with the warped geometry instead of old slopes.
                normals[:,0] -= dx*normals[:,1]
                normals[:,2] += dn*normals[:,1]
                normals[:] /= np.linalg.norm(normals,axis=1)[:,None].clip(1e-12)
            changes.extend([float(dy.min()), float(dy.max())])
    js = json.dumps(doc, separators=(',', ':')).encode()
    js += b' ' * (-len(js) % 4)
    dst.write_bytes(struct.pack('<III', 0x46546c67, 2, 28+len(js)+len(binary)) + struct.pack('<II', len(js), 0x4e4f534a) + js + struct.pack('<II', len(binary), 0x004e4942) + binary)
    return dict(file=str(dst.relative_to(ROOT)), min_shift=min(changes), max_shift=max(changes))


def prepare(scene, out):
    out.mkdir(parents=True, exist_ok=True)
    raw = scene.read_bytes()
    with zipfile.ZipFile(scene) as z:
        doc = json.loads(z.read('SerializePcgData.json'))
        hn = next(n for n in z.namelist() if n.startswith('HeightMap_'))
        hraw = z.read(hn)
    h = np.frombuffer(hraw, '<f4').reshape(257, 257) * 256
    nodes = doc['nodeTransformDatas']
    roots = [n for n in nodes if n['parentId'] == 0]
    plan = dict(source=str(scene), scene_sha256=hashlib.sha256(raw).hexdigest(),
                height_sha256=hashlib.sha256(hraw).hexdigest(), moves=[], disable=[], meshes=[])
    # Rebuild lamps at their original roadside anchors, so each post stays rigid
    # and vertical while the connecting strings follow the new elevations.
    subprocess.run([sys.executable, str(ROOT/'tools/models/props3d.py'), str(out), 'lamps', '--terrain-scene', str(scene)], check=True)
    for name in ('lamp_posts', 'lamp_glow'):
        (out/f'{name}.glb').replace(out/f'{name}_v8.glb')
        plan['meshes'].append(dict(file=str((out/f'{name}_v8.glb').relative_to(ROOT)),method='rebuilt from current terrain',count=18))
    old = np.load(ROOT / 'assets/terrain/world/base_heights.npy')
    plan['meshes'].append(warp_glb(ROOT/'assets/night/graveyard.glb',out/'graveyard_v8.glb',old,h))

    houses = [n for n in roots if n['nodeName'].startswith(('house_', 'hs_house_'))]
    occupied = [(n['pos']['x'], n['pos']['z'], n['id']) for n in houses]
    # Sample actual floor footprints, excluding roof overhangs and chimney.
    dims = {'a': (-2.8, 2.8, -4.9, 3.2), 'b': (-4.5, 4.5, -5.0, 3.2), 'c': (-3.1, 4.9, -4.9, 3.2)}
    road = [(130,52),(135,66),(149,79),(159,90),(162,96),(162,127),(167,134),(171,141)]
    def road_distance(x,z):
        best=1e9
        for (a,b),(c,d) in zip(road,road[1:]):
            t=np.clip(((x-a)*(c-a)+(z-b)*(d-b))/((c-a)**2+(d-b)**2),0,1)
            best=min(best,math.hypot(x-a-t*(c-a),z-b-t*(d-b)))
        return best
    bases = Geo([[(0, '#242731'), (.5, '#4b5058'), (1, '#73767b')]])
    for n in houses:
        kind = n['nodeName'].split('house_')[1][0]
        xmin,xmax,zmin,zmax = dims[kind]
        p = n['pos']; ox, oz = p['x'], p['z']
        # Unity imports glTF with an X reflection; legacy roots include a
        # 180-degree rotation, so authored EN yaw is pi minus the root yaw.
        yaw = math.pi - 2 * math.atan2(n['rot']['y'], n['rot']['w'])
        co, si = math.cos(yaw), math.sin(yaw)
        local = np.array([(x, z) for x in np.linspace(xmin, xmax, 7) for z in np.linspace(zmin, zmax, 7)])
        offsets = local @ np.array([[co, si], [-si, co]])
        best = None
        for dx in range(-32, 33, 2):
            for dz in range(-32, 33, 2):
                x, z = ox+dx, oz+dz
                if any(math.hypot(x-a, z-b) < 10.5 for a,b,i in occupied if i != n['id']):
                    continue
                if math.hypot(x-160.5,z-74) < 19 or math.hypot(x-171,z-146) < 11:
                    continue
                if road_distance(x,z) < 7.0 or not (148 < x < 207 and 39 < z < 170):
                    continue
                elev = sample(h, x+offsets[:,0], z+offsets[:,1])
                lo, hi = float(elev.min()), float(elev.max())
                if lo < 29.0 or hi-lo > 2.4:
                    continue
                score = (hi-lo)*3 + math.hypot(dx,dz)*.3
                if best is None or score < best[0]: best=(score,x,z,lo,hi)
        if best is None:
            plan.setdefault('unresolved', []).append(n['nodeName'])
            continue
        _, x,z,lo,hi=best
        y=hi+.08
        occupied=[(x,z,i) if i==n['id'] else (a,b,i) for a,b,i in occupied]
        plan['moves'].append(dict(id=n['id'],name=n['nodeName'],before=p,before_rot=n['rot'],before_scale=n['scale'],after=dict(x=x,y=y,z=z),ground_range=[lo,hi]))
        # Stone footing fills the downslope gap; no house floats after lifting.
        corners=[]
        for lx,lz in [(xmin-.15,zmin-.15),(xmax+.15,zmin-.15),(xmax+.15,zmax+.15),(xmin-.15,zmax+.15)]:
            corners.append(np.array([x+lx*co-lz*si-128,z+lx*si+lz*co-128,y-.045]))
        for j,a in enumerate(corners):
            b=corners[(j+1)%4];aa=a.copy();bb=b.copy();aa[2]=lo-.4;bb[2]=lo-.4
            bases.quad(a,aa,bb,b,.5,0)
        bases.quad(*corners,.68,0)
        # A short stair leads from each door apron down to the existing ground.
        # Stop once the next riser is buried; never alter the user's terrain.
        for step in range(1, 14):
            zz=zmin-.15-step*.38
            sx,sz=x-zz*si,z+zz*co
            top=y-.045-step*.18
            bottom=float(sample(h,sx,sz))-.2
            if top <= bottom+.05: break
            bases.box((sx-128,sz-128,(top+bottom)/2),
                      (co*1.2,si*1.2,0),(-si*.22,co*.22,0),(0,0,(top-bottom)/2),tone=.55+(step%2)*.07)
    write_glb(out/'village_bases.glb',bases,name='village_bases',rough=.95)
    plan['meshes'].append(dict(file=str((out/'village_bases.glb').relative_to(ROOT)),method='stone footings and entrance stairs',count=len(houses)))

    for n in roots:
        if not n['isActive'] or not n['nodeName'].startswith('pl_'): continue
        p=n['pos'];x,z=p['x'],p['z'];kind=n['nodeName'].split('_')[1]
        r=max(n['scale']['x'],n['scale']['z'])*(.2 if kind=='tree' else .5)
        points=[(x+r*math.cos(t),z+r*math.sin(t)) for t in np.linspace(0,math.tau,9)]
        edge=any(a<1 or b<1 or a>255 or b>255 or sample(h,a,b)<27.5 for a,b in points)
        house=any(abs(x-m['after']['x'])<5 and abs(z-m['after']['z'])<5 for m in plan['moves'])
        if edge or house:
            plan['disable'].append(dict(id=n['id'],name=n['nodeName'],reason='shore/edge' if edge else 'house footprint'))
        else:
            ground=float(sample(h,x,z))-.04
            if abs(ground-p['y'])>.18:
                plan['moves'].append(dict(id=n['id'],name=n['nodeName'],before=p,after=dict(x=x,y=ground,z=z)))
    (out/'placement-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2))
    print(json.dumps(dict(moves=len(plan['moves']),disabled=len(plan['disable']),unresolved=plan.get('unresolved',[]),meshes=plan['meshes']),indent=2))


if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--scene',type=Path,default=Path.home()/'Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data')
    ap.add_argument('--out',type=Path,default=ROOT/'assets/refit_v8')
    args=ap.parse_args();prepare(args.scene.resolve(),args.out.resolve())
