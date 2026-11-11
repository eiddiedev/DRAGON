#!/usr/bin/env python3
"""Build a terrain-following stone support without moving the lighthouse."""
import hashlib
import json
import math
from pathlib import Path
import sys
import zipfile

import numpy as np

from refit_scene import sample
sys.path.insert(0, str(Path(__file__).parent / 'models'))
from glbw import Geo, write_glb


def build(scene, output):
    raw = scene.read_bytes()
    with zipfile.ZipFile(scene) as archive:
        document = json.loads(archive.read('SerializePcgData.json'))
        heights = np.frombuffer(archive.read(next(n for n in archive.namelist()
                                    if n.startswith('HeightMap_'))), '<f4').reshape(257, 257) * 256
    node = next(n for n in document['nodeTransformDatas']
                if n['nodeName'] == 'lighthouse' and n['parentId'] == 0)
    p = node['pos']
    geo = Geo([[(0, '#343944'), (.5, '#646b78'), (1, '#949ca6')]])
    # Original lighthouse base starts at local y=-2, radius 4.6m.
    # Overlap it vertically; widen towards the terrain for a buttressed skirt.
    segments = 48
    gap = []
    for i in range(segments):
        a, b = i * math.tau / segments, (i + 1) * math.tau / segments
        points = []
        for angle, radius, top in [(a, 4.58, True), (a, 5.1, False),
                                   (b, 5.1, False), (b, 4.58, True)]:
            x, z = p['x'] + math.cos(angle)*radius, p['z'] + math.sin(angle)*radius
            y = p['y'] - 1.72 if top else float(sample(heights, x, z)) - .35
            points.append(np.array([x-128, z-128, y]))
        # Hide upper parts where the mountain already intersects the base.
        geo.quad(*points, tone=.43 + .055*(i % 4))
        gap.append(p['y']-2-float(sample(heights,p['x']+4.6*math.cos(a),p['z']+4.6*math.sin(a))))
    output.mkdir(parents=True, exist_ok=True)
    triangles = write_glb(output/'lighthouse_footing.glb', geo, name='lighthouse_footing', rough=.95)
    report = dict(source_sha256=hashlib.sha256(raw).hexdigest(), lighthouse_transform={
        k:node[k] for k in ('id','pos','rot','scale')}, triangles=triangles,
        maximum_original_gap=max(gap), install_position=dict(x=128,y=0,z=128),
        install_rotation=dict(x=0,y=1,z=0,w=0), installed=False)
    (output/'lighthouse-footing-report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))


if __name__ == '__main__':
    build(Path(sys.argv[1]), Path(sys.argv[2]))
