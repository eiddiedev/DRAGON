#!/usr/bin/env python3
"""原生地形的顶视底色图（MatCoverTex，2048²）：原来那张是旧岛的样子（河、瀑布、旧海岸），
按现在的山形重画；草色比原图深一档。图的上方是北（z 大），和高度图上下颠倒。"""
import numpy as np
from PIL import Image
from scipy import ndimage as nd
ROOT = '/Users/a1234/Documents/awesomeWRLD/assets'
H = np.load(f'{ROOT}/terrain/native/tile_heights.npy')
Z0, X0 = np.mgrid[0:257, 0:257].astype(float)
H = np.where((np.hypot(X0 - 127, Z0 - 176) < 30) & (H > 70.5), H - 1.2, H)
S = 2048
Hs = nd.zoom(H, S / 257, order=1)[:S, :S]
gz, gx = np.gradient(Hs, 256 / S)
slope = np.degrees(np.arctan(np.hypot(gx, gz)))
rng = np.random.default_rng(5)


def noise(scale, amp):
    n = nd.gaussian_filter(rng.standard_normal((S, S)), scale)
    return n / (n.std() + 1e-9) * amp


nz = noise(40, 1) * .6 + noise(10, 1) * .3 + noise(3, 1) * .1


def ss(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def col(c):
    return np.array(c, float)[None, None, :] / 255


grass = col((70, 92, 52)) * (1 + .12 * nz[..., None]) + (col((88, 100, 56)) - col((70, 92, 52))) * ss(-.5, 1.2, nz + (Hs - 48) / 20)[..., None]
img = grass
steep = ss(34, 48, slope)[..., None]
img = img * (1 - steep) + col((58, 72, 46)) * steep
rock = ss(52, 64, slope)[..., None]
img = img * (1 - rock) + col((104, 102, 98)) * (1 + .1 * nz[..., None]) * rock
high = ss(72, 90, Hs + nz * 4)[..., None]
img = img * (1 - high) + col((112, 112, 112)) * high
snow = ss(86, 100, Hs + nz * 5)[..., None] * (1 - ss(50, 65, slope))[..., None]
img = img * (1 - snow) + col((226, 230, 238)) * snow
beach = (ss(25.8, 26.6, Hs) * (1 - ss(27.8, 29.5, Hs)))[..., None]
img = img * (1 - beach) + col((178, 164, 128)) * beach
sea = (1 - ss(25.6, 26.6, Hs))[..., None]
deep = ss(0, 18, 26 - Hs)[..., None]
img = img * (1 - sea) + (col((40, 104, 120)) * (1 - deep) + col((14, 52, 78)) * deep) * sea
out = (np.clip(img, 0, 1) * 255).astype(np.uint8)[::-1]
rgba = np.dstack([out, np.full((S, S), 255, np.uint8)])
Image.fromarray(rgba).save(f'{ROOT}/terrain/native/MatCoverTex.png')
Image.fromarray(out[::8, ::8]).save('/tmp/cover_new.png')
print('ok', np.median(out.reshape(-1, 3), 0))
