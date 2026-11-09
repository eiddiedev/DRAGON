#!/usr/bin/env python3
"""把出生点南边的小山铺平成草地，让玩家从低处仰视台地上的城堡。
用法：flatten_spawn_hill.py <输入 scene.data> <提供干净草地贴图的旧存档> <输出 scene.data>
"""
import io
import sys
import zipfile

import numpy as np
from PIL import Image
from scipy import ndimage as nd

src, clean, out = sys.argv[1:4]
z = zipfile.ZipFile(src)
HN, TN = 'HeightMap_3193404.data', 'MatCoverTex_3193404.png'
h = np.frombuffer(z.read(HN), '<f4').reshape(257, 257).astype(float) * 256
zz, xx = np.mgrid[0:257, 0:257].astype(float)
rng = np.random.default_rng(9)
CX, CZ, OUTER = 130.0, 56.0, 60.0


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


r = np.hypot(xx - CX, zz - CZ)
# 从区域外缘向内做调和插值：地面平滑接上四周，不会鼓包也不会凹成盆地
inside = r < OUTER - 3
ground = np.where(inside, 42.0, h)
KERNEL = np.array([[0, .25, 0], [.25, 0, .25], [0, .25, 0]])
for _ in range(4000):
    avg = nd.convolve(ground, KERNEL, mode='nearest')
    ground = np.where(inside, avg, ground)
roll = nd.gaussian_filter(rng.standard_normal((257, 257)), 9) * 9 * .35
new = ground + roll
blend = 1 - ss(OUTER - 14, OUTER - 1, r)
h2 = h * (1 - blend) + new * blend
gz, gx = np.gradient(h2)
slope = np.degrees(np.arctan(np.hypot(gx, gz)))
print('height in region', h2[r < 40].min().round(1), h2[r < 40].max().round(1), 'max slope r<46', slope[r < 46].max().round(1))
print('x130 z10..106', [round(float(h2[k, 130]), 1) for k in range(10, 107, 12)])

# 贴图：用旧存档里干净的平原草地重铺，去掉旧山坡的明暗
tex = np.array(Image.open(io.BytesIO(z.read(TN))).convert('RGBA')).astype(float)
ctex = np.array(Image.open(io.BytesIO(zipfile.ZipFile(clean).read(TN))).convert('RGB')).astype(float)
T = tex.shape[0]
S = T / 256
patch = ctex[int((256 - 96) * S):int((256 - 72) * S), int(112 * S):int(172 * S)]
tile = np.concatenate([patch, patch[::-1]], axis=0)
tile = np.concatenate([tile, tile[:, ::-1]], axis=1)
ty, tx = np.mgrid[0:T, 0:T]
grass = tile[ty % tile.shape[0], tx % tile.shape[1]]
var = nd.gaussian_filter(nd.zoom(rng.random((33, 33)), T / 33, order=3)[:T, :T], 20)
var = (var - var.mean()) / (var.std() + 1e-6)
grass = grass * (1 + .05 * var[..., None])
wz, wx = 256 - (ty + .5) / S, (tx + .5) / S
pm = 1 - ss(OUTER - 18, OUTER - 4, np.hypot(wx - CX, wz - CZ))
tex[..., :3] = tex[..., :3] * (1 - pm[..., None]) + grass * pm[..., None]
b = io.BytesIO()
Image.fromarray(np.clip(tex, 0, 255).round().astype(np.uint8)).save(b, 'PNG', compress_level=6)

with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as w:
    for i in z.infolist():
        data = z.read(i.filename)
        if i.filename == HN:
            data = (h2 / 256).astype('<f4').tobytes()
        elif i.filename == TN:
            data = b.getvalue()
        ni = zipfile.ZipInfo(i.filename, i.date_time)
        ni.compress_type = zipfile.ZIP_DEFLATED
        ni.external_attr = i.external_attr
        w.writestr(ni, data)
