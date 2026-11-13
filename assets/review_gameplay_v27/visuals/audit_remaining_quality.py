"""Read only saved official/candidate scene resources and registered script bodies."""
import base64
import hashlib
import io
import json
import re
from pathlib import Path
from zipfile import ZipFile
from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECTS = Path('/Users/bytedance/Library/Application Support/AI World Creator/projects')
OFFICIAL = PROJECTS / 'project-55a43370-8734-4825-92a8-b0de824a45e2/scene.data'
CANDIDATE = PROJECTS / 'project-8f93f84d-13f4-4ca1-95b2-42eafc8c27a5/scene.data'
PATTERN = re.compile(r'masterTexture|globalTexture|[Mm]ipmap|mipMap|filterMode\s*=|anisoLevel\s*=|[.:]Compress\(|[.:]Resize\(|[.:]Reinitialize\(|QualitySettings|renderScale|Shader\.Find|SetTexture\(|Texture2D\(')

def digest(x):
    return hashlib.sha256(x).hexdigest()

archives = [ZipFile(OFFICIAL), ZipFile(CANDIDATE)]
scenes = [json.loads(z.read('SerializePcgData.json')) for z in archives]
reports = []
for label, scene in zip(['official_v26', 'isolated_v27'], scenes):
    entries = []
    for ident, record in scene['runtimeScripts'].items():
        code = record.get('content') or ''
        entries.append({'id': ident, 'name': record.get('referenceName') or ident, 'sha256': digest(code.encode()),
                        'matching_lines': [{'line': i, 'source': text[:450]} for i, text in enumerate(code.splitlines(), 1) if PATTERN.search(text)]})
    reports.append({'version': label, 'registered_script_count': len(entries), 'scripts': entries})

payloads = []
for name in archives[0].namelist():
    if name == 'SerializePcgData.json':
        continue
    data = archives[0].read(name)
    payloads.append({'name': name, 'bytes': len(data), 'sha256': digest(data),
                     'candidate_identical': name in archives[1].namelist() and data == archives[1].read(name)})
bridge = next(x['content'] for x in scenes[1]['runtimeScripts'].values() if x.get('referenceName') == 'dragon_world_bridge.lua')
image_match = re.search(r"\['MobileGroundColorSource'\]='([^']+)'", bridge)
ground = archives[1].read('MatCoverTex_3193404.png')
bundled = base64.b64decode(image_match[1])
ground_audit = {'saved_dimensions': Image.open(io.BytesIO(ground)).size,
                'bundled_dimensions': Image.open(io.BytesIO(bundled)).size,
                'saved_sha256': digest(ground), 'bundled_sha256': digest(bundled), 'identical_bytes': ground == bundled}
result = {'inputs': [str(OFFICIAL), str(CANDIDATE)], 'scripts': reports, 'scene_payloads': payloads,
          'resource_refs_identical': scenes[0]['resourceRefs'] == scenes[1]['resourceRefs'],
          'environment_identical': all(scenes[0].get(k) == scenes[1].get(k) for k in ['envType', 'envSettingPath', 'envParamJson']),
          'ground_source': ground_audit,
          'limitations': ['Registered source and saved assets were audited; no phone-native renderer or resource-loader internals were inspected.']}
(HERE / 'remaining-quality-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'registered_script_counts': [r['registered_script_count'] for r in reports],
                  'unchanged_payloads': sum(x['candidate_identical'] for x in payloads),
                  'resource_refs_identical': result['resource_refs_identical'],
                  'environment_identical': result['environment_identical'], 'ground_source': ground_audit}, ensure_ascii=False, indent=2))
