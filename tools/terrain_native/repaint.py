#!/usr/bin/env python3
"""回到原生地形：按现在的山形重画 16 层材质权重（splat），高度图不再下沉。
用法：repaint.py <输出目录>，写出 SplatMap_0..15.png 和 heights.f32
splat 图的行和高度图的行上下颠倒（实测：flipud 后海面层的平均高度最低）。"""
import json, math, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
ROOT = '/Users/bytedance/Documents/ChatGPT/DRAGON/assets'
H = np.load(f'{ROOT}/terrain/native/tile_heights.npy').astype(np.float64)   # [z, x]，原贴图地形的实际地面
Z0, X0 = np.mgrid[0:257, 0:257].astype(float)
# 城堡平台整体压低 1.2 米，避免地面从庭院和房间地板里冒出来
castle = (np.hypot(X0 - 127, Z0 - 176) < 30) & (H > 70.5)
H = np.where(castle, H - 1.2, H)
# 桥头：桥面南端 42.28、北端 40.78（模型实测），把两端地面垫到桥面下 0.12 米，往外 2.5 米平台、再 5 米顺坡
for z_end, deck, out in ((95.8, 42.28, -1), (125.2, 40.78, 1)):
    for zi in range(257):
        d = (zi - z_end) * out          # 往桥外为正
        if d < -2.0 or d > 7.5:
            continue
        w_side = np.clip((4.6 - np.abs(X0[zi] - 162)) / 1.2, 0, 1)
        w_len = 1.0 if d < 2.5 else max(0.0, 1 - (d - 2.5) / 5.0)
        tgt = deck - .12
        H[zi] = np.where(H[zi] < tgt, H[zi] + (tgt - H[zi]) * w_side * w_len, H[zi])
SEA = 27.0
gz, gx = np.gradient(nd.gaussian_filter(H, .8))
slope = np.degrees(np.arctan(np.hypot(gx, gz)))
Z, X = np.mgrid[0:257, 0:257].astype(float)
rnd = np.random.default_rng(3)
noise = nd.gaussian_filter(rnd.standard_normal(H.shape), 4)
noise /= noise.std() + 1e-9


def ss(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# 小路：沿 path.json 的折线，宽 2.6 米
road = np.zeros_like(H)
try:
    P = json.load(open(f'{ROOT}/terrain/v3/path.json'))
    pts = P['points'] if isinstance(P, dict) and 'points' in P else P
    pts = [(p[0], p[1]) if not isinstance(p, dict) else (p['x'], p['z']) for p in pts]
    for (x0, z0), (x1, z1) in zip(pts[:-1], pts[1:]):
        n = int(max(2, math.hypot(x1 - x0, z1 - z0) * 2))
        for t in np.linspace(0, 1, n):
            x, z = x0 + (x1 - x0) * t, z0 + (z1 - z0) * t
            road = np.maximum(road, 1 - ss(1.0, 2.2, np.hypot(X - x, Z - z)))
except Exception as e:
    print('path skipped', e)
L = {k: i for i, k in enumerate(['Beach_H', 'Beach_V', 'Farm_H', 'Farm_V', 'Rocky_H', 'Rocky_V', 'Sea_H', 'Sea_V', 'River_H', 'River_V', 'Valley_H', 'Valley_V', 'Mount_H', 'Mount_V', 'Hill_H', 'Hill_V'])}
W = np.zeros((16,) + H.shape)
under = 1 - ss(SEA - .6, SEA + .4, H)
beach = (1 - under) * (1 - ss(SEA + 1.2, SEA + 3.0, H + noise * .6)) * (1 - ss(18, 30, slope))
high = ss(70, 90, H + noise * 4)
vert = ss(30, 42, slope + noise * 3)     # 陡坡用竖直投影的同类材质
rock = ss(52, 62, slope + noise * 3)     # 更陡才露岩石
land = np.clip(1 - under - beach, 0, 1)
W[L['Sea_H']] = under
W[L['Beach_H']] = beach
W[L['Mount_H']] = land * high * (1 - vert)
W[L['Mount_V']] = land * high * vert
low = land * (1 - high)
W[L['Rocky_V']] = low * rock
g = low * (1 - rock)
mix = ss(-.4, .9, noise + (H - 45) / 25)
W[L['Valley_H']] = g * (1 - mix) * (1 - vert)
W[L['Valley_V']] = g * (1 - mix) * vert
W[L['Hill_H']] = g * mix * (1 - vert)
W[L['Hill_V']] = g * mix * vert
# 路
r = road * land * (1 - high)
W = W * (1 - r)
W[L['Rocky_H']] += r
W = np.clip(W, 0, None)
W /= W.sum(0, keepdims=True) + 1e-9
# 量化成 0~255 且每像素和为 255
q = np.floor(W * 255).astype(int)
rest = 255 - q.sum(0)
top = W.argmax(0)
for k in range(16):
    q[k] += np.where(top == k, rest, 0)
for k in range(16):
    Image.fromarray(q[k][::-1].astype(np.uint8)).save(f'{OUT}/SplatMap_{k}.png')
(H / 256).astype('<f4').tofile(f'{OUT}/heights.f32')
names = list(L)
print({names[k]: round(float(W[k].mean()), 3) for k in range(16) if W[k].mean() > .001})
