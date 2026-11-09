#!/usr/bin/env python3
"""把城堡高台改成一座孤立的小山，并在南坡开出一条蜿蜒的盘山路。
用法：sculpt_hill.py <旧高度 .npy> <输出目录>
输出：base_heights.npy（新高度）、path.json（山路中心线，世界坐标 x,z,y）、hill-heights.png（检查用）
桥、河道、竞技场入口的高度保持不变。
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

src, OUT = sys.argv[1:3]
H0 = np.load(src).astype(float)
n = H0.shape[0]
zz, xx = np.mgrid[0:n, 0:n].astype(float)

CX, CZ = 127.0, 176.0  # 山顶中心，城堡就在这里
TOP = 72.0  # 山顶海拔
R_TOP = 20.0  # 山顶平地半径
R_FOOT = 43.0  # 山脚半径
FOOT_MAX = 47.0  # 山脚和周围地面的最高海拔，让山孤立出来
R_CLEAR = 66.0  # 这个半径内把原来的高台压下去

rng = np.random.default_rng(77)


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def noise(sigma):
    g = nd.gaussian_filter(rng.normal(size=(n, n)), sigma, mode='nearest')
    return g / g.std()


# 河道
scene_river = [(77, 253), (77, 236), (80, 219), (74, 192), (79, 173), (88, 152), (98, 136), (108, 124), (125, 116), (141, 118), (154, 110), (168, 110), (187, 103)]
mask = np.zeros((n, n), bool)
for (ax, az), (bx, bz) in zip(scene_river, scene_river[1:]):
    for t in np.linspace(0, 1, 80):
        mask[int(az + (bz - az) * t), int(ax + (bx - ax) * t)] = True
river_d = nd.distance_transform_edt(~mask)

r = np.hypot(xx - CX, zz - CZ) + noise(9) * 1.8
# 先把周围压低，北面是雪山，所以越往北放得越开
clear = (1 - ss(R_FOOT, R_CLEAR, r)) * (1 - ss(196, 212, zz))
ground = H0 * (1 - clear) + np.minimum(H0, FOOT_MAX + noise(7) * .9) * clear
# 山的轮廓：山顶平，往下先陡后缓
t = np.clip((r - R_TOP) / (R_FOOT - R_TOP), 0, 1)
# 上陡下缓的山形，像一座孤立的小山，不是圆台
profile = TOP - (TOP - FOOT_MAX + 3) * (1 - (1 - t) ** 1.7)
profile += noise(4) * 1.1 * ss(R_TOP, R_TOP + 5, r)  # 山坡起伏
hill = np.where(r < R_FOOT, np.maximum(profile, ground), ground)
hill = np.where(r < R_TOP, TOP, hill)

# 河道和桥头不动
keep = ss(5, 13, river_d)
H = H0 * (1 - keep) + hill * keep
# 竞技场入口留一个凹口
gate_d = np.hypot(xx - 125, zz - 135)
w = 1 - ss(5, 11, gate_d)
H = H * (1 - w) + H0 * w
# 桥北头
bridge_d = np.hypot(xx - 162, zz - 127)
w = 1 - ss(4, 9, bridge_d)
H = H * (1 - w) + H0 * w
H = nd.gaussian_filter(H, .8, mode='nearest')


def catmull(pts, per=24):
    p = np.array(pts, float)
    p = np.vstack([p[0], p, p[-1]])
    out = []
    for i in range(1, len(p) - 2):
        for s in np.linspace(0, 1, per, endpoint=False):
            a, b, c, d = p[i - 1], p[i], p[i + 1], p[i + 2]
            out.append(.5 * (2 * b + (c - a) * s + (2 * a - 5 * b + 4 * c - d) * s * s + (3 * b - a - 3 * c + d) * s ** 3))
    out.append(p[-2])
    return np.array(out)


# 山路：从桥北头出发，向西横穿南坡，折返向东，再折回到山顶南门
ROUTE = [(162, 127), (158, 134), (146, 139), (128, 142), (110, 145), (98, 152), (100, 158), (114, 153), (134, 149), (150, 151), (155, 158), (146, 158.5), (134, 156), (127, 156.5)]
C = catmull(ROUTE)
seg = np.hypot(*np.diff(C, axis=0).T)
s = np.concatenate([[0], np.cumsum(seg)])
y0 = float(nd.map_coordinates(H0, [[127.0], [162.0]], order=1)[0])
Y = y0 + (TOP - y0) * ss(0, 1, s / s[-1]) ** .95
print('path length', round(s[-1], 1), 'grade deg', round(float(np.degrees(np.arctan((TOP - y0) / s[-1]))), 1))
# 每个格子取最近的路点
from scipy.spatial import cKDTree  # noqa: E402

tree = cKDTree(C)
d, idx = tree.query(np.dstack([xx.ravel(), zz.ravel()])[0])
d, idx = d.reshape(n, n), idx.reshape(n, n)
w = 1 - ss(2.4, 6.2, d)
H = H * (1 - w) + Y[idx] * w
H = nd.gaussian_filter(H, .55, mode='nearest')
# 路面再压平一次
w = 1 - ss(1.8, 3.0, d)
H = H * (1 - w) + Y[idx] * w

os.makedirs(OUT, exist_ok=True)
np.save(os.path.join(OUT, 'base_heights.npy'), H)
json.dump([[round(float(a), 2), round(float(b), 2), round(float(c), 2)] for (a, b), c in zip(C, Y)], open(os.path.join(OUT, 'path.json'), 'w'))
gz, gx = np.gradient(H)
slope = np.degrees(np.arctan(np.hypot(gx, gz)))
on = d < 1.6
print('slope on path mean/max', round(float(slope[on].mean()), 1), round(float(slope[on].max()), 1))
print('top', round(float(H[176, 127]), 1), 'spawn', round(float(H[48, 130]), 1), 'bridge N', round(float(H[127, 162]), 1), 'bridge S', round(float(H[96, 162]), 1), 'gate', round(float(H[135, 125]), 1))
vis = np.clip((H - 20) / 100, 0, 1)
shade = np.clip(.55 + (gx * .6 + gz * .5) * .25, 0, 1)
img = np.dstack([vis * 255, shade * 255, (1 - w) * vis * 255]).astype(np.uint8)[::-1]
Image.fromarray(img).resize((768, 768), Image.BICUBIC).save(os.path.join(OUT, 'hill-heights.png'))
