#!/usr/bin/env python3
"""Verify and restore the exact review ZIP from ordinary Git byte parts."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'assets/handoff_20261113/review-package/manifest.json'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=DEFAULT)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--check', action='store_true', help='Verify parts without writing a ZIP')
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    target = args.out or args.manifest.parent / manifest['filename']
    combined = hashlib.sha256()
    total = 0
    paths = []
    for part in manifest['parts']:
        path = args.manifest.parent / part['name']
        if path.stat().st_size != part['bytes'] or digest(path) != part['sha256']:
            raise SystemExit(f'Part integrity check failed: {path.name}')
        paths.append(path)
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                combined.update(block)
                total += len(block)
    if total != manifest['bytes'] or combined.hexdigest() != manifest['sha256']:
        raise SystemExit('Combined ZIP integrity check failed')
    if args.check:
        print(f'OK: {len(paths)} parts, {total} bytes, SHA256 {combined.hexdigest()}')
        return
    if target.exists():
        if target.stat().st_size == total and digest(target) == manifest['sha256']:
            print(f'Already verified: {target}')
            return
        raise SystemExit(f'Refusing to overwrite a different file: {target}')
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=target.name + '.', suffix='.tmp', dir=target.parent)
    try:
        with os.fdopen(fd, 'wb') as output:
            for path in paths:
                with path.open('rb') as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b''):
                        output.write(block)
        if digest(Path(tmp)) != manifest['sha256']:
            raise SystemExit('Restored ZIP integrity check failed')
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    print(f'Restored and SHA256 verified: {target}')

if __name__ == '__main__':
    main()
