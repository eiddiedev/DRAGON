#!/usr/bin/env python3
"""Apply reviewed root placements to a NEW scene archive, never the live file.

Import replacement models and close the project through the editor before
installing the resulting archive. This handles existing-node placements only;
it does not pretend that replacement mesh imports have been completed.
"""
import argparse
from collections import defaultdict
import copy
import hashlib
import json
import math
from pathlib import Path
import zipfile


def transform_document(document, plan):
    result = copy.deepcopy(document)
    nodes = result['nodeTransformDatas']
    by_id = {n['id']: n for n in nodes}
    if len(by_id) != len(nodes):
        raise ValueError('Duplicate scene node IDs')
    children = defaultdict(list)
    for n in nodes:
        children[n['parentId']].append(n['id'])
    actions = plan['moves'] + plan['disable']
    action_ids = [a['id'] for a in actions]
    if len(set(action_ids)) != len(action_ids):
        raise ValueError('Plan targets the same root more than once')
    # Validate the whole plan before changing anything. Imports may add nodes,
    # but a user edit to any targeted root must force a fresh review.
    for action in actions:
        n = by_id.get(action['id'])
        if n is None or n['nodeName'] != action['name'] or n['parentId'] != 0:
            raise ValueError(f'Root identity changed: {action["name"]}')
        if 'before' in action:
            for key in ('rot','scale'):
                if 'before_'+key in action and n[key] != action['before_'+key]:
                    raise ValueError(f'Root {key} changed since planning: {action["name"]}')
            for axis in 'xyz':
                if abs(n['pos'][axis] - action['before'][axis]) > 1e-5:
                    raise ValueError(f'Root was moved since planning: {action["name"]}')
                if not math.isfinite(action['after'][axis]):
                    raise ValueError('Non-finite destination')

    def subtree(root):
        pending, seen = [root], set()
        while pending:
            nid = pending.pop()
            if nid in seen:
                raise ValueError('Cycle in scene hierarchy')
            seen.add(nid)
            yield by_id[nid]
            pending.extend(children[nid])

    translated, disabled = [], []
    for action in plan['moves']:
        delta = {a: action['after'][a] - action['before'][a] for a in 'xyz'}
        for n in subtree(action['id']):
            # This editor serializes CHILD positions in world coordinates.
            n['pos'] = {a: n['pos'][a] + delta[a] for a in 'xyz'}
            translated.append(n['id'])
    for action in plan['disable']:
        for n in subtree(action['id']):
            n['isActive'] = False
            disabled.append(n['id'])
    return result, dict(moved_roots=len(plan['moves']), disabled_roots=len(plan['disable']),
                        translated_nodes=len(translated), disabled_nodes=len(disabled),
                        replacement_meshes_pending=plan['meshes'])


def stage(scene, plan_path, output):
    if scene.resolve() == output.resolve():
        raise ValueError('Output must be a new archive; live in-place writes are forbidden')
    plan = json.loads(plan_path.read_text())
    with zipfile.ZipFile(scene) as archive:
        entries = [(info, archive.read(info.filename)) for info in archive.infolist()]
    heights = [raw for info, raw in entries if info.filename.startswith('HeightMap_')]
    if len(heights) != 1 or hashlib.sha256(heights[0]).hexdigest() != plan['height_sha256']:
        raise ValueError('Terrain has changed since planning')
    document = json.loads(next(raw for info, raw in entries if info.filename == 'SerializePcgData.json'))
    result, report = transform_document(document, plan)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation makes accidental overwrite of any existing artifact fail.
    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as archive:
        for info, raw in entries:
            if info.filename == 'SerializePcgData.json':
                raw = json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode()
            archive.writestr(info, raw)
    report.update(source=str(scene), output=str(output),
                  source_sha256=hashlib.sha256(scene.read_bytes()).hexdigest())
    output.with_suffix('.audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene', required=True, type=Path)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(stage(args.scene, args.plan, args.output), ensure_ascii=False, indent=2))
