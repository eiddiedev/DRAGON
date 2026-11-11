#!/usr/bin/env python3
"""算出草片的摆放点，并生成远处的低面数草地块。用法：grass_spots.py <输出目录>"""
import json, math, os, random, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbw import Geo, write_glb
OUT = sys.argv[1]
ROOT = '/Users/bytedance/Documents/ChatGPT/DRAGON/assets'
H = np.load(f'{ROOT}/terrain/v3/base_heights.npy')
SITES = json.load(open(f'{ROOT}/terrain/v3/sites.json'))
path = json.load(open(f'{ROOT}/terrain/v3/path.json'))
road = [(130, 52), (135, 66), (149, 79), (159, 90), (162, 96), (162, 127), (167, 134), (171, 141)]
rnd = random.Random(55)
def G(x, y):
    x = min(max(x, 0), 255.99); y = min(max(y, 0), 255.99)
    x0, y0 = int(x), int(y); fx, fy = x - x0, y - y0
    return float(H[y0, x0] * (1 - fx) * (1 - fy) + H[y0, x0 + 1] * fx * (1 - fy) + H[y0 + 1, x0] * (1 - fx) * fy + H[y0 + 1, x0 + 1] * fx * fy)
def near_road(x, y, r):
    pts = [(a, b) for a, b, _ in path[::3]]
    best = min(math.hypot(x - a, y - b) for a, b in pts + road)
    for (ax, ay), (bx, by) in zip(road, road[1:]):
        dx, dy = bx - ax, by - ay
        t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - ax - t * dx, y - ay - t * dy))
    return best < r
def trail_dist(x, y):
    best = 1e9
    for tr in SITES['trails']:
        for (ax, ay), (bx, by) in zip(tr, tr[1:]):
            dx, dy = bx - ax, by - ay
            k = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
            best = min(best, math.hypot(x - ax - k * dx, y - ay - k * dy))
    return best
occ, spots = {}, []
def ok_spot(x, y, r):
    key = (int(x / r), int(y / r))
    if any((key[0] + a, key[1] + b) in occ for a in (-1, 0, 1) for b in (-1, 0, 1)):
        return False
    occ[key] = 1
    return True
for _ in range(40000):
    a_, d_ = rnd.uniform(0, math.tau), 37 * math.sqrt(rnd.random())
    x, y = 140 + math.cos(a_) * d_ * 1.15, 62 + math.sin(a_) * d_
    if near_road(x, y, 3.0) or math.hypot(x - 160.5, y - 74) < 3.2 or math.hypot(x - 121, y - 57) < 4 or math.hypot(x - 130, y - 45) < 7.5:
        continue
    if G(x, y) < 31 or abs(G(x + 3, y) - G(x - 3, y)) > 3.2 or abs(G(x, y + 3) - G(x, y - 3)) > 3.2:
        continue
    if ok_spot(x, y, 3.3):
        spots.append((x, y, 'c'))
nc = len(spots)
for _ in range(60000):
    x, y = rnd.uniform(4, 240), rnd.uniform(4, 215)
    g = G(x, y)
    steep_ok = 6.0 if math.hypot(x - 127, y - 176) < 46 else 3.2
    if g < 31 or g > 72 or abs(G(x + 3, y) - G(x - 3, y)) > steep_ok or abs(G(x, y + 3) - G(x, y - 3)) > steep_ok:
        continue
    if math.hypot((x - 140) / 1.15, y - 62) < 38 or math.hypot(x - 127, y - 176) < 20:
        continue
    d_r = 99 if not near_road(x, y, 9) else (0 if near_road(x, y, 2.8) else 5)
    d_t = trail_dist(x, y)
    if d_t < 1.8 or any(math.hypot(x - s['x'], y - s['z']) < s['r'] * .55 for s in SITES['sites'].values()):
        continue
    near = d_r < 9 or d_t < 9 or any(math.hypot(x - s['x'], y - s['z']) < s['r'] + 9 for s in SITES['sites'].values()) or math.hypot(x - 127, y - 176) < 46
    if not near and rnd.random() > .12:
        continue
    if ok_spot(x, y, 3.5):
        spots.append((x, y, 'a' if rnd.random() < .78 else 'b'))
    if len(spots) >= nc + 170:
        break
# 羊群草地：铺满
for _ in range(9000):
    x, y = rnd.uniform(78, 122), rnd.uniform(36, 92)
    g = G(x, y)
    if g < 31 or trail_dist(x, y) < 1.6 or near_road(x, y, 2.6) or math.hypot((x - 140) / 1.15, y - 62) < 38:
        continue
    if abs(G(x + 3, y) - G(x - 3, y)) > 3.5 or abs(G(x, y + 3) - G(x, y - 3)) > 3.5:
        continue
    if ok_spot(x, y, 3.0):
        spots.append((x, y, 'a' if rnd.random() < .8 else 'b'))
print('spots', nc, len(spots) - nc)
os.makedirs(OUT, exist_ok=True)
json.dump(spots, open(os.path.join(OUT, 'spots.json'), 'w'))
