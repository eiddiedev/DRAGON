"""真实渲染的地形网格高度（各块 heights.npy 拼成），用来让东西真正贴地。"""
import json
import os

import numpy as np

V3 = '/Users/bytedance/Documents/ChatGPT/DRAGON/assets/terrain/v3'
_G = None
SEG = 120
TILE = 64.0
STEP = TILE / SEG


def load():
    global _G
    if _G is not None:
        return _G
    n = 4 * SEG + 1
    G = np.zeros((n, n), np.float32)
    for t in json.load(open(os.path.join(V3, 'manifest.json'))):
        h = np.load(os.path.join(V3, t['name'], 'heights.npy'))
        c0, r0 = int(t['x0'] / TILE) * SEG, int(t['z0'] / TILE) * SEG
        G[r0:r0 + SEG + 1, c0:c0 + SEG + 1] = h[::-1]  # r=0 是北边
    _G = G
    return G


def height(x, z):
    G = load()
    fx, fz = np.clip(np.asarray(x) / STEP, 0, G.shape[1] - 1.001), np.clip(np.asarray(z) / STEP, 0, G.shape[0] - 1.001)
    ix, iz = fx.astype(int), fz.astype(int)
    tx, tz = fx - ix, fz - iz
    return G[iz, ix] * (1 - tx) * (1 - tz) + G[iz, ix + 1] * tx * (1 - tz) + G[iz + 1, ix] * (1 - tx) * tz + G[iz + 1, ix + 1] * tx * tz
