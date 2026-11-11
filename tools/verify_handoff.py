#!/usr/bin/env python3
"""Verify portable editor project files without accessing the live editor."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'editor_project/project_lapv8fm0'
MANIFEST=ROOT/'docs/project-manifest.json'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def included(p):
 rel=p.relative_to(BASE)
 return not any(x=='.awc' or x.endswith('_log') or x=='__pycache__' for x in rel.parts) and p.name!='.DS_Store' and not p.name.endswith('.bak') and not p.name.startswith('scene.before-')
if '--write' in sys.argv:
 files={str(p.relative_to(BASE)):{'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(BASE.rglob('*')) if p.is_file() and included(p)}
 MANIFEST.write_text(json.dumps({'project':'project_lapv8fm0','files':files},ensure_ascii=False,indent=2)+'\n')
 print(f'Wrote manifest: {len(files)} files')
else:
 files=json.loads(MANIFEST.read_text())['files'];bad=[]
 for name,v in files.items():
  p=BASE/name
  if not p.is_file() or p.stat().st_size!=v['bytes'] or digest(p)!=v['sha256']:bad.append(name)
 if bad:
  print('Missing or changed files:\n'+'\n'.join(bad));sys.exit(1)
 print(f'OK: {len(files)} project files match SHA-256 manifest')
