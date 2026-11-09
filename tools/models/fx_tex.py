#!/usr/bin/env python3
"""火焰和光柱贴图。用法：fx_tex.py <输出目录>"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(4)
W, H = 512, 768
y, x = np.mgrid[0:H, 0:W].astype(float)
v = 1 - y / H        # 0 底 1 顶
u = (x - W / 2) / (W / 2)
tot = np.zeros((H, W, 4))
for i, (cx, ww, hh) in enumerate(((0, .62, .98), (-.32, .34, .62), (.3, .36, .68))):
    n = nd.gaussian_filter(rng.normal(size=(H, W)), (46, 16))
    n = n / n.std()
    n2 = nd.gaussian_filter(rng.normal(size=(H, W)), (18, 7))
    n2 = n2 / n2.std()
    uu = u - cx + (n * .10 + n2 * .05) * (v / hh) * 1.6
    prof = ww * (1 - np.clip(v / hh, 0, 1)) ** .62 * np.clip(v * 8 + .5, 0, 1)
    d = np.abs(uu) / (prof + 1e-3)
    a = np.clip(1 - d, 0, 1)
    a = np.clip(a * 2.2, 0, 1) ** .9 * (v < hh)
    t = np.clip(a * 1.25 - (v / hh) * .35, 0, 1)
    r = np.clip(.95 + t * .1, 0, 1)
    g = np.clip(.18 + t * 1.0, 0, 1)
    b = np.clip(-.15 + t * .9, 0, 1)
    tot[..., 0] = np.maximum(tot[..., 0], r * (a > 0))
    tot[..., 1] = np.maximum(tot[..., 1], g * (a > 0))
    tot[..., 2] = np.maximum(tot[..., 2], b * (a > 0))
    tot[..., 3] = np.maximum(tot[..., 3], a)
tot[..., 3] = nd.gaussian_filter(tot[..., 3], 2)
Image.fromarray((np.clip(tot, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 'flame.png'))
# 光柱：竖向渐隐，横向中间亮
H2, W2 = 512, 256
y, x = np.mgrid[0:H2, 0:W2].astype(float)
v = 1 - y / H2
n = nd.gaussian_filter(rng.normal(size=(H2, W2)), (60, 3), mode='wrap')
n = n / n.std()
a = (.55 + .18 * n) * (1 - v) ** .7 * np.clip(v * 14, 0, 1)
col = np.dstack([.68 + .32 * v, .90 + .1 * v, np.ones_like(v)])
beam = np.dstack([col, np.clip(a, 0, 1)])
Image.fromarray((np.clip(beam, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 'beam.png'))
# 火星
S = 64
y, x = np.mgrid[0:S, 0:S].astype(float)
r = np.hypot(x - S / 2 + .5, y - S / 2 + .5) / (S / 2)
a = np.clip(1 - r, 0, 1) ** 2.2
Image.fromarray((np.dstack([np.ones_like(a), np.ones_like(a) * .75, np.ones_like(a) * .35, a]) * 255).astype(np.uint8)).save(os.path.join(OUT, 'spark.png'))
