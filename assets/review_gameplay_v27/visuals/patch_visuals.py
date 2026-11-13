"""Apply only the v27 visual replacements to a merged bridge candidate.

The source can already contain the other agents' non-overlapping bridge fixes.
No file outside the provided destination is changed.
"""
from pathlib import Path
import argparse

HERE = Path(__file__).resolve().parent


def patch(source: str) -> str:
    for stem in ("holy", "quality"):
        before = (HERE / f"{stem}-before.lua").read_text()
        after = (HERE / f"{stem}-after.lua").read_text()
        if source.count(before) != 1:
            raise ValueError(f"{stem}: expected exactly one unchanged v26 block")
        source = source.replace(before, after, 1)
    return source


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("destination", type=Path)
    args = ap.parse_args()
    args.destination.write_text(patch(args.source.read_text()))
    print(f"Wrote visual candidate: {args.destination}")
