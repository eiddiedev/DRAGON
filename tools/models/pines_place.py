#!/usr/bin/env python3
# 用法：pines_place.py <地形目录> <贴图> <输出目录>
# 大片松林：每棵树 4 张交叉面片，法线朝外做成蓬松感；按区域分成几个模型，便于视锥剔除。
import json
import math
import os
import random
import sys

import numpy as np
from scipy import ndimage as nd

TD, TEX, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
H = np.load(os.path.join(TD, 'base_heights.npy'))
sites = json.load(open(os.path.join(TD, 'sites.json')))
path = np.array(json.load(open(os.path.join(TD, 'path.json'))))[:, :2]
SEA = 27.0
rnd = random.Random(12)
rng = np.random.default_rng(12)
Hf = nd.gaussian_filter(H, 1)
gz, gx = np.gradient(Hf)
slope = np.degrees(np.arctan(np.hypot(gx, gz)))
dens = nd.gaussian_filter(rng.normal(size=H.shape), 7)
dens = (dens - dens.min()) / (dens.max() - dens.min())
roads = [list(map(tuple, path[::4]))] + [[(130, 52), (135, 66), (149, 79), (159, 90), (162, 96), (162, 127), (167, 134), (171, 141)]] + sites['trails']


def road_dist(x, z):
    best = 1e9
    for r in roads:
        for (ax, az), (bx, bz) in zip(r, r[1:]):
            dx, dz = bx - ax, bz - az
            t = max(0, min(1, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz + 1e-6)))
            best = min(best, math.hypot(x - ax - t * dx, z - az - t * dz))
    return best


HOUSES = [(176, 60), (188, 66), (182, 79), (170, 88), (196, 82), (186, 95), (176, 124), (190, 128), (200, 140), (184, 146), (196, 158), (178, 160), (171, 146), (125, 135), (60, 56), (100, 80)]
trees = []
cellsz = 1.35
occ = {}
for _ in range(400000):
    x, z = rnd.uniform(2, 254), rnd.uniform(2, 254)
    h = float(H[int(z), int(x)])
    if h < SEA + 2.2 or slope[int(z), int(x)] > 44:
        continue
    line = 80 - 24 * min(max((z - 196) / 26, 0), 1)
    if h > line - 8:
        continue
    if math.hypot(x - 127, z - 176) < 46:
        continue
    if math.hypot((x - 140) / 1.15, z - 62) < 40:  # 花海和出生点
        continue
    if x > 118 and z < 130 and x < 170:  # 从出生点望向城堡的视线
        continue
    east = x > 165 and z < 175
    want = (.28 if not east else .55)
    if dens[int(z), int(x)] < want:
        continue
    if any(math.hypot(x - s['x'], z - s['z']) < s['r'] + 7 for s in sites['sites'].values()):
        continue
    if any(math.hypot(x - a, z - b) < 8 for a, b in HOUSES):
        continue
    if road_dist(x, z) < 6.5:
        continue
    key = (int(x / cellsz), int(z / cellsz))
    if any((key[0] + a, key[1] + b) in occ for a in (-1, 0, 1) for b in (-1, 0, 1)):
        continue
    occ[key] = 1
    trees.append((x, z, h))
print('trees', len(trees), flush=True)
json.dump(trees, open(os.path.join(OUT, 'trees.json'), 'w'))
