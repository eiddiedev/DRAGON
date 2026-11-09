#!/usr/bin/env python3
"""为一块地形生成高精度高度和手绘风贴图。用法：terrain_tile_data.py <scene.data> <x0> <z0> <size> <输出目录>"""
import os
import sys
import zipfile

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from scipy.spatial import cKDTree

src, X0, Z0, SIZE, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
os.makedirs(out, exist_ok=True)
Z = zipfile.ZipFile(src)
H = np.frombuffer(Z.read('HeightMap_3193404.data'), '<f4').reshape(257, 257).astype(float) * 256
TEX = 2048
rng = np.random.default_rng(int(X0 * 1000 + Z0))
SEA = 27.0


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def fbm(n, base, oct=4):
    o, amp, tot = np.zeros((n, n)), 1., 0.
    for i in range(oct):
        g = base * 2 ** i
        o += amp * nd.zoom(rng.random((g + 3, g + 3)), n / (g + 3), order=3)[:n, :n]
        tot += amp
        amp *= .5
    o /= tot
    return (o - o.min()) / (o.max() - o.min())


# 世界坐标网格：贴图第 0 行是北边
ys, xs = np.mgrid[0:TEX, 0:TEX]
wx = X0 + (xs + .5) / TEX * SIZE
wz = Z0 + SIZE - (ys + .5) / TEX * SIZE
base = nd.map_coordinates(H, [wz, wx], order=3, mode='nearest')
gz, gx = np.gradient(nd.gaussian_filter(base, 3), SIZE / TEX)
slope0 = np.degrees(np.arctan(np.hypot(gx, gz)))
rock = smoothstep(26, 42, slope0 + (fbm(TEX, 8) - .5) * 22)
# 块面岩石：Voronoi 分块，每块有自己的抬升和朝向，得到编辑器模型那种切面石头
N = int(SIZE * SIZE / 7)
pts = rng.random((N, 2)) * TEX
d, cell = cKDTree(pts).query(np.dstack([ys.ravel(), xs.ravel()])[0], k=1)
cell = cell.reshape(TEX, TEX)
d = d.reshape(TEX, TEX)
lift = rng.uniform(-.8, .8, N)[cell]
tiltx, tiltz = rng.uniform(-.34, .34, N)[cell], rng.uniform(-.34, .34, N)[cell]
facet = lift + (xs - pts[cell, 1]) * SIZE / TEX * tiltx + (ys - pts[cell, 0]) * SIZE / TEX * tiltz
crack = np.exp(-(d / (TEX / SIZE * .12 + 1e-3)) ** 2)
_, second = cKDTree(pts).query(np.dstack([ys.ravel(), xs.ravel()])[0], k=2)
ds = np.array(_)
edge = (ds[:, 1] - ds[:, 0]).reshape(TEX, TEX) * SIZE / TEX
crack = 1 - smoothstep(.02, .3, edge)
# 岩层：沿高度走的水平纹理
strata = np.sin((base + (fbm(TEX, 6) - .5) * 5) * 2.6) * .22
wave = (fbm(TEX, 22, 3) - .5) * .35
h = base + rock * (facet * .95 + strata) + (1 - rock) * wave
land = smoothstep(SEA - .3, SEA + 1.2, base)
h = base + (h - base) * land

gz, gx = np.gradient(nd.gaussian_filter(h, 1.2), SIZE / TEX)
nx, nz, ny = -gx, -gz, np.ones_like(gx)
ln = np.sqrt(nx * nx + nz * nz + ny * ny)
L = np.array([-.5, .62, .6])
L /= np.linalg.norm(L)
ndl = np.clip((nx * L[0] + ny * L[1] + nz * L[2]) / ln, 0, 1)


def col(c):
    return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], float)


def mix(a, b, t):
    return a * (1 - t[..., None]) + b * t[..., None]


# 草地：两层大色块 + 小草丛笔触
blot = fbm(TEX, 5)
g = mix(np.broadcast_to(col('#7DB843'), (TEX, TEX, 3)), np.broadcast_to(col('#A6CE4F'), (TEX, TEX, 3)), smoothstep(.35, .68, blot))
patch = smoothstep(.56, .64, fbm(TEX, 16))
g = mix(g, np.broadcast_to(col('#C2DB5E'), (TEX, TEX, 3)), patch * .55)
dark = smoothstep(.58, .66, fbm(TEX, 12))
g = mix(g, np.broadcast_to(col('#5E9E3C'), (TEX, TEX, 3)), dark * .5)
ang = fbm(TEX, 6) * 6.28
tuft = (np.sin(xs * .55 * np.cos(ang) + ys * .55 * np.sin(ang) + fbm(TEX, 30, 2) * 18) > .72).astype(float)
tuft = nd.gaussian_filter(tuft, .7) * smoothstep(.45, .7, fbm(TEX, 40, 2))
g = g * (1 + tuft[..., None] * .10)
# 花点
fl = (rng.random((TEX, TEX)) > .99965).astype(float)
fl = nd.gaussian_filter(fl, 1.6) * 16
g = mix(g, np.broadcast_to(col('#FBEFD2'), (TEX, TEX, 3)), np.clip(fl, 0, 1) * (1 - rock))
# 岩石：按格子变色，切面感
tint = rng.uniform(0, 1, N)[cell]
r = mix(np.broadcast_to(col('#B4AEAA'), (TEX, TEX, 3)), np.broadcast_to(col('#D8CFC2'), (TEX, TEX, 3)), tint)
warm = smoothstep(.45, .7, fbm(TEX, 7))
r = mix(r, np.broadcast_to(col('#C9A98A'), (TEX, TEX, 3)), warm * .55)
r = r * (1 - crack[..., None] * .22)
# 崖顶苔藓：岩石朝上的面和岩缝长草
moss = smoothstep(.72, .95, ny / ln) * smoothstep(.35, .6, fbm(TEX, 18))
r = mix(r, np.broadcast_to(col('#A3C84A'), (TEX, TEX, 3)), moss * .8)
c = mix(g, r, rock)
# 草地与岩石交界加一条深草边
bd = np.clip(1 - np.abs(rock - .5) * 2, 0, 1)
c = mix(c, np.broadcast_to(col('#4F8A36'), (TEX, TEX, 3)), bd * .4)
# 沙滩、水下
sand = (1 - smoothstep(SEA + .4, SEA + 2.2, base + (fbm(TEX, 20) - .5) * 1.2))
c = mix(c, np.broadcast_to(col('#EBD9A2'), (TEX, TEX, 3)), sand)
under = 1 - smoothstep(SEA - 1.5, SEA - .1, base)
c = mix(c, np.broadcast_to(col('#3F8E96'), (TEX, TEX, 3)), under)
# 烘进卡通光影：亮面暖、暗面紫，色阶略微收拢
light = np.clip(ndl * 1.25, 0, 1)
light = light * .72 + np.round(light * 4) / 4 * .28
shadow = np.array([.60, .52, .72])
sun = np.array([1.10, 1.06, .95])
c = c * (shadow + (sun - shadow) * light[..., None])
Image.fromarray(np.clip(c, 0, 255).astype(np.uint8)).save(os.path.join(out, 'albedo.png'))

# 网格顶点高度（120 段，单块 2.88 万面，低于导入上限 3 万面）
SEG = 120
yy = (np.arange(SEG + 1) / SEG * (TEX - 1)).astype(int)
hm = h[np.ix_(yy, yy)]
np.save(os.path.join(out, 'heights.npy'), hm)
print('tile', X0, Z0, SIZE, 'height', hm.min().round(1), hm.max().round(1), 'grid m', SIZE / SEG)
