"""Patch only enemy visual lifetime/setup; preserve engine, network, attacks, loot."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def patch(source: str) -> str:
    if 'review-v27: each successfully spawned model' in source:
        raise ValueError('enemy visual patch already applied')
    begin=source.index('local function clearVisuals()')
    end=source.index(' fx.SetArena(V(state.x,state.y+.08,state.z),state.radius,false)',begin)
    old=source[begin:end]
    if 'PrimitiveType.Cube' not in old or 'visuals[e.id]=v' not in old:
        raise ValueError('unexpected enemy visual implementation')
    return source[:begin]+(ROOT/'enemy-visuals.lua').read_text()+'\n'+source[end:]
