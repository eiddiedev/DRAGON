#!/usr/bin/env python3
"""Stage imported scenery and terrain placements into a new archive.

Never writes the live project. Import these five named assets and save first:
tree_v8, lamps_v12, glow_v12, grave_v12, bases_v12.
Regenerate placement-plan.json from that saved scene before staging.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import zipfile

from apply_refit_plan import transform_document


def stage(scene, plan_path, output):
    raw = scene.read_bytes()
    plan = json.loads(plan_path.read_text())
    if hashlib.sha256(raw).hexdigest() != plan['scene_sha256']:
        raise ValueError('Scene changed: regenerate the placement plan first')
    with zipfile.ZipFile(scene) as z:
        entries = [(i, z.read(i.filename)) for i in z.infolist()]
    doc = json.loads(next(r for i, r in entries if i.filename == 'SerializePcgData.json'))
    result, audit = transform_document(doc, plan)
    nodes = result['nodeTransformDatas']

    def root(name):
        found = [n for n in nodes if n['parentId'] == 0 and n['nodeName'] == name]
        if len(found) != 1:
            raise ValueError(f'Expected one imported root {name}, found {len(found)}')
        n = found[0]
        if any(c['parentId'] == n['id'] for c in nodes):
            raise ValueError(f'Unexpected serialized children: {name}')
        return n

    audit['replaced_assets'] = []
    for old, new in [('holy_tree3', 'tree_v8'), ('lamp_posts', 'lamps_v12'),
                     ('lamp_glow', 'glow_v12'), ('graveyard', 'grave_v12')]:
        target, imported = root(old), root(new)
        # Keep the original transform and collision policy. Imported static
        # assets are normalized, so the new importer scale must accompany them.
        for key in ('assetData', 'aigcModelData', 'glbSliceData', 'scale'):
            target[key] = copy.deepcopy(imported[key])
        audit['replaced_assets'].append({'root': old, 'asset': target['assetData']})
        nodes.remove(imported)
    foundation = root('bases_v12')
    foundation['nodeName'] = 'village_bases_v12'
    foundation['pos'] = dict(x=128.0, y=0.0, z=128.0)
    foundation['rot'] = dict(x=0.0, y=1.0, z=0.0, w=0.0)
    foundation['physicsColliderData']['enableCollision'] = True
    audit['replacement_meshes_pending'] = []
    audit['foundation_id'] = foundation['id']
    audit['source_sha256'] = hashlib.sha256(raw).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as z:
        for info, content in entries:
            if info.filename == 'SerializePcgData.json':
                content = json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode()
            z.writestr(info, content)
    output.with_suffix('.audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2))
    return audit


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene', required=True, type=Path)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(stage(args.scene, args.plan, args.output), ensure_ascii=False, indent=2))
