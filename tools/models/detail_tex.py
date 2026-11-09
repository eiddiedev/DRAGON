#!/usr/bin/env python3
"""地形细节贴图：无缝、黑底，靠发光通道叠加到地形上。
detail_grass：草叶条纹 + 草丛明暗；detail_rock：岩石碎裂 + 雪面颗粒。
用法：detail_tex.py <输出目录>
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

OUT = sys.argv[1]
R = 1024


def spec(beta, fmin, fmax, seed, aniso=None):
    r = np.random.default_rng(seed)
    fy = np.fft.fftfreq(R)[:, None] * R
    fx = np.fft.fftfreq(R)[None, :] * R
    if aniso:
        a, k = aniso
        u, v = fx * np.cos(a) + fy * np.sin(a), -fx * np.sin(a) + fy * np.cos(a)
        f = np.hypot(u * k, v)
    else:
        f = np.hypot(fx, fy)
    f[0, 0] = 1
    amp = f ** (-beta / 2)
    amp[(f < fmin) | (f > fmax)] = 0
    o = np.real(np.fft.ifft2(np.fft.fft2(r.normal(size=(R, R))) * amp))
    lo, hi = np.percentile(o, .5), np.percentile(o, 99.5)
    return np.clip((o - lo) / (hi - lo), 0, 1)


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# ---------- 草：多方向的细长草叶，亮叶尖；大团明暗
blades = np.zeros((R, R))
for i, ang in enumerate((.25, .9, 1.5, 2.2, 2.8)):
    b = spec(.8, 30, 500, 100 + i, (ang, 7))
    blades = np.maximum(blades, ss(.62, .86, b) * (.7 + .3 * (i % 2)))
clump = spec(2.0, 2, 24, 120)
speck = ss(.8, .96, spec(.4, 200, 512, 121))
g = blades * (.3 + .7 * ss(.25, .75, clump)) + speck * .25
rgb = np.dstack([g * .72, g * 1.0, g * .42])
Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 'detail_grass.png'))
# ---------- 岩石：裂缝网 + 颗粒（中性偏冷）
n1 = spec(2.0, 3, 120, 130)
n2 = spec(1.6, 20, 400, 131)
ridge = 1 - np.abs(n1 * 2 - 1)
cracks = ss(.86, .97, ridge)
strata = spec(1.6, 8, 240, 132, (1.5, 6))
r = (1 - cracks) * (.28 + .5 * ss(.3, .8, strata) * ss(.3, .7, n2)) + ss(.75, .95, n2) * .2
rgb = np.dstack([r * .92, r * .95, r * 1.0])
Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, 'detail_rock.png'))
print('done', round(float(g.mean()), 3), round(float(r.mean()), 3))
