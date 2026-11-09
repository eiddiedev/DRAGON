#!/usr/bin/env python3
"""全图无缝地形：所有噪声都按世界坐标取样，相邻地形块的边界完全一致。
用法：world_terrain_data.py <scene.data> <输出目录> [preview]
preview：只出一张全图贴图检查，不写地形块。
高度来自 base_heights.npy（由 sculpt_hill.py 生成）。贴图只烘很弱的明暗，昼夜靠引擎光照区分。
"""
import json
import math
import os
import sys
import zipfile

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from scipy.spatial import cKDTree

src, OUT = sys.argv[1:3]
PREVIEW = 'preview' in sys.argv[3:]
os.makedirs(OUT, exist_ok=True)
Z = zipfile.ZipFile(src)
base_path = os.path.join(OUT, 'base_heights.npy')
if os.path.exists(base_path):  # 引擎地形之后会被压低，高度只从第一次的存档取
    H = np.load(base_path)
else:
    H = np.frombuffer(Z.read('HeightMap_3193404.data'), '<f4').reshape(257, 257).astype(float) * 256
    np.save(base_path, H)
scene = json.loads(Z.read('SerializePcgData.json'))
SEA = 27.0
rng = np.random.default_rng(1234)
TILE = 64.0
# 精度：出生点到城堡这条视线上的 8 块用高精度，其余低精度
HI = {(64, 0), (128, 0), (64, 64), (128, 64), (64, 128), (128, 128), (64, 192), (128, 192)}


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def make_noise(cells, res=2048, oct=4):
    o, amp, tot = np.zeros((res, res)), 1., 0.
    for i in range(oct):
        g = cells * 2 ** i
        if g > res // 3:
            break
        o += amp * nd.zoom(rng.random((g + 3, g + 3)), res / (g + 3), order=3)[:res, :res]
        tot += amp
        amp *= .5
    o /= tot
    return (o - o.min()) / (o.max() - o.min())


class Noise:
    def __init__(self, cells, res=2048, oct=4):
        self.a = make_noise(cells, res, oct)
        self.k = (res - 1) / 256.0

    def __call__(self, x, z_):
        return nd.map_coordinates(self.a, [z_ * self.k, x * self.k], order=1, mode='nearest')


n_rockmix = Noise(32)
n_strata = Noise(24)
n_wave = Noise(90)
n_blot = Noise(20)
n_patch = Noise(64)
n_dark = Noise(48)
n_ang = Noise(24)
n_warm = Noise(28)
n_moss = Noise(72)
n_sand = Noise(80)
n_snow = Noise(40)
n_fine = Noise(400, 4096, 2)

# 河道：水边不做岩石位移，免得戳穿河面
river = next(n for n in scene['nodeTransformDatas'] if n.get('riverDisplayData'))
rp = [(river['pos']['x'] + k['x'], river['pos']['z'] + k['z']) for k in river['riverDisplayData']['keyPoints']]
rm = np.zeros((257, 257), bool)
for (ax, az), (bx, bz) in zip(rp, rp[1:]):
    for t in np.linspace(0, 1, 60):
        rm[int(az + (bz - az) * t), int(ax + (bx - ax) * t)] = True
river_d = nd.distance_transform_edt(~rm)


def line_integral(noise_sigma, steps, seed):
    """沿地形下坡方向把噪声抹开，得到顺着山势走的冲沟纹理。结果缓存。"""
    path = os.path.join(OUT, f'lic_{seed}.npy')
    if os.path.exists(path):
        return np.load(path)
    R = 2048
    k = (R - 1) / 256.0
    r = np.random.default_rng(seed)
    src_n = nd.gaussian_filter(r.normal(size=(R, R)), noise_sigma, mode='wrap')
    Hs = nd.gaussian_filter(nd.zoom(H, R / 257, order=1), 6)
    gz, gx = np.gradient(Hs)
    mag = np.hypot(gx, gz) + 1e-4
    tx, tz = gx / mag, gz / mag
    yy, xx = np.mgrid[0:R, 0:R].astype(np.float32)
    total = src_n.copy()
    for sgn in (1, -1):
        px, pz = xx.copy(), yy.copy()
        for i in range(steps):
            cz = [pz, px]
            dx = nd.map_coordinates(tx, cz, order=1, mode='nearest')
            dz = nd.map_coordinates(tz, cz, order=1, mode='nearest')
            px += dx * 2 * sgn
            pz += dz * 2 * sgn
            total += nd.map_coordinates(src_n, [pz, px], order=1, mode='wrap')
    lo, hi = np.percentile(total, 1), np.percentile(total, 99)
    out_ = np.clip((total - lo) / (hi - lo), 0, 1).astype(np.float32)
    np.save(path, out_)
    print('lic', seed, flush=True)
    return out_


LIC_C = line_integral(14, 44, 11)
LIC_F = line_integral(4, 24, 12)


class Grid2048:
    def __init__(self, a):
        self.a = a
        self.k = (a.shape[0] - 1) / 256.0

    def __call__(self, x, z_):
        return nd.map_coordinates(self.a, [z_ * self.k, x * self.k], order=1, mode='nearest')


lic_c, lic_f = Grid2048(LIC_C), Grid2048(LIC_F)


def catmull(pts, per=24):
    p = np.array(pts, float)
    p = np.vstack([p[0], p, p[-1]])
    out_ = []
    for i in range(1, len(p) - 2):
        for t in np.linspace(0, 1, per, endpoint=False):
            a, b, c, d = p[i - 1], p[i], p[i + 1], p[i + 2]
            out_.append(.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (3 * b - a - 3 * c + d) * t ** 3))
    out_.append(p[-2])
    return np.array(out_)


# 道路：盘山路 + 出生点到桥 + 桥头到药水铺
ROAD = [np.array(json.load(open(os.path.join(OUT, 'path.json'))))[:, :2],
        catmull([(130, 52), (135, 66), (149, 79), (159, 90), (162, 96)]),
        catmull([(162, 127), (167, 134), (171, 141)])]
rm2 = np.zeros((2048, 2048), bool)
_k = 2047 / 256.0
for pts in ROAD:
    pp = catmull([tuple(q) for q in pts[::6]], 8) if len(pts) > 200 else pts
    for (ax, az), (bx, bz) in zip(pp, pp[1:]):
        for t in np.linspace(0, 1, 16):
            rm2[int((az + (bz - az) * t) * _k), int((ax + (bx - ax) * t) * _k)] = True
road_d = Grid2048((nd.distance_transform_edt(~rm2) / _k).astype(np.float32))

# 全图岩石块
NPTS = int(256 * 256 / 12)
PTS = rng.random((NPTS, 2)) * 256
TREE = cKDTree(PTS)
LIFT = rng.uniform(-.75, .75, NPTS)
TX, TZ = rng.uniform(-.3, .3, NPTS), rng.uniform(-.3, .3, NPTS)
TINT = rng.random(NPTS)


def base(x, z_):
    return nd.map_coordinates(H, [z_, x], order=3, mode='nearest')


def fields(x, z_):
    """给世界坐标返回：高度、岩石度、最近岩块编号、岩块缝。全图同一个函数，所以无缝。"""
    b = base(x, z_)
    e = .9
    dx = base(x + e, z_) - base(x - e, z_)
    dz = base(x, z_ + e) - base(x, z_ - e)
    slope = np.degrees(np.arctan(np.hypot(dx, dz) / (2 * e)))
    rock = ss(27, 43, slope + (n_rockmix(x, z_) - .5) * 20)
    q = np.dstack([x.ravel(), z_.ravel()])[0]
    ds, ids = TREE.query(q, k=2)
    cell = ids[:, 0].reshape(x.shape)
    edge = (ds[:, 1] - ds[:, 0]).reshape(x.shape)
    facet = (LIFT[cell] + (x - PTS[cell, 0]) * TX[cell] + (z_ - PTS[cell, 1]) * TZ[cell]) * .55
    strata = np.sin((b + (n_strata(x, z_) - .5) * 26) * .55) * .12
    wave = (n_wave(x, z_) - .5) * .32
    riv = nd.map_coordinates(river_d, [z_, x], order=1, mode='nearest')
    road = road_d(x, z_)
    keep = ss(5, 11, riv) * ss(SEA - .3, SEA + 1.2, b) * ss(2.6, 6.5, road)
    # 小山：南面和西面偏草坡，东北面露岩
    hr = np.hypot(x - 127, z_ - 176)
    grassy = (1 - ss(40, 50, hr)) * ss(-.25, .55, ((127 - x) * .45 + (176 - z_) * .9) / (hr + 1))
    outcrop = ss(.60, .68, n_rockmix(x, z_) * .55 + n_blot(x, z_) * .45) * ss(24, 30, hr)  # 草坡上露出的岩块
    rock = np.maximum(rock * (1 - grassy * .85), outcrop * (1 - ss(40, 48, hr)) * .95)
    # 山势冲沟：只在高处，不碰小山顶和道路
    high = ss(62, 78, b) * (1 - (1 - ss(24, 34, hr)))
    gully = (lic_c(x, z_) - .5) * 3.4 + (lic_f(x, z_) - .5) * .9
    # 小山的坡面起伏，岩块鼓出来
    hill_relief = (1 - ss(40, 47, hr)) * ss(21, 27, hr) * ((lic_c(x, z_) - .5) * 3.2 + outcrop * 1.5 + (n_patch(x, z_) - .5) * 1.8)
    h = b + (rock * (facet + strata) + (1 - rock) * wave) * keep + gully * high * keep + hill_relief * keep
    return h, b, rock, cell, edge


def col(c):
    return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], float)


def mix(a, b, t):
    if b.ndim == 1:
        b = np.broadcast_to(b, a.shape)
    return a * (1 - t[..., None]) + b * t[..., None]


def paint(x0, z0, res):
    m_per_px = TILE / res
    pad = int(4 / m_per_px)  # 多算一圈再裁掉，模糊和梯度在地块边界才不会断
    ys, xs = np.mgrid[-pad:res + pad, -pad:res + pad]
    wx = x0 + (xs + .5) / res * TILE
    wz = z0 + TILE - (ys + .5) / res * TILE  # 第 0 行是北边
    wx = np.clip(wx, 0, 255.99)
    wz = np.clip(wz, 0, 255.99)
    full = res + 2 * pad
    h, b, rock, cell, edge = fields(wx, wz)
    lc, lf = lic_c(wx, wz), lic_f(wx, wz)
    fine = n_fine(wx, wz)
    # 看不见的高频细节也算进法线，贴图才有山脊和沟的层次
    detail = h + (lc - .5) * 1.5 * rock + (lf - .5) * 1.1 * rock + (fine - .5) * .22
    sm = nd.gaussian_filter(detail, .35 / m_per_px)
    gz, gx = np.gradient(sm, m_per_px)
    nyv = 1 / np.sqrt(1 + gx * gx + gz * gz)
    nx, nz = -gx * nyv, gz * nyv  # 第 0 行在北，gz 沿行向南
    Lv = np.array([-.663, .643, -.383])  # 指向月亮/太阳：西南偏高，和引擎主光一致
    ndl = np.clip(nx * Lv[0] + nyv * Lv[1] + nz * Lv[2], 0, 1)
    cav = sm - nd.gaussian_filter(sm, 1.4 / m_per_px)  # 沟里暗、脊上亮
    steep = np.degrees(np.arccos(np.clip(nyv, 0, 1)))
    # 草：深绿为底，几种草色大块交错
    c = mix(np.broadcast_to(col('#3F6E31'), (full, full, 3)).copy(), col('#577F38'), ss(.36, .66, n_blot(wx, wz)))
    c = mix(c, col('#2F5A2C'), ss(.54, .68, n_dark(wx, wz)) * .75)
    c = mix(c, col('#6F8F42'), ss(.60, .70, n_patch(wx, wz)) * .45)
    c = mix(c, col('#7A7440'), ss(.66, .76, n_moss(wx, wz)) * .3)
    c = c * (1 + (fine[..., None] - .5) * .34)
    # 岩石：顺山势的条纹，脊亮沟暗
    r = mix(np.broadcast_to(col('#7D756D'), (full, full, 3)).copy(), col('#A1978A'), ss(.35, .7, lc))
    r = mix(r, col('#5D5854'), ss(.45, .72, 1 - lf) * .7)
    r = mix(r, col('#8E7A62'), ss(.45, .7, n_warm(wx, wz)) * .45)
    strata = .5 + .5 * np.sin((b + (n_strata(wx, wz) - .5) * 26) * .55)
    r = r * (.97 + .05 * strata[..., None])
    crack = 1 - ss(.02, .4, edge)
    r = r * (1 - crack[..., None] * .02)
    r = mix(r, col('#566F36'), ss(.74, .96, nyv) * ss(.4, .62, n_moss(wx, wz)) * .75)
    c = mix(c, r, rock)
    c = mix(c, col('#3C5E30'), np.clip(1 - np.abs(rock - .5) * 2, 0, 1) * .3)
    # 雪：高处积雪，冲沟里堆得多，山脊和陡壁露岩
    line = 78 - 30 * ss(196, 222, wz)
    snow = ss(line - 6, line + 6, h + (n_snow(wx, wz) - .5) * 16 + (.5 - lc) * 12)
    ridge = ss(.56, .78, lc)
    bare = np.clip(ss(50, 74, steep + (n_moss(wx, wz) - .5) * 16) * .85 + ridge * ss(32, 54, steep) * .55, 0, 1)
    snow = snow * (1 - bare) * ss(46, 54, np.hypot(wx - 127, wz - 176))
    s_lit = ss(.25, .85, ndl + np.clip(cav, -1, 1) * .35)
    sc = mix(np.broadcast_to(col('#7F92BC'), (full, full, 3)).copy(), col('#F4F7FB'), s_lit)
    c = mix(c, sc, snow)
    # 道路：夯土 + 零散石块，边缘被草吃掉一点
    rd = road_d(wx, wz) + (n_patch(wx, wz) - .5) * 1.3
    road = 1 - ss(1.5, 2.6, rd)
    soft = nd.gaussian_filter(fine, .25 / m_per_px)
    rc = mix(np.broadcast_to(col('#94805F'), (full, full, 3)).copy(), col('#7F6F55'), ss(.42, .6, soft))
    rc = mix(rc, col('#A89A80'), ss(.55, .7, n_blot(wx, wz)) * .4)
    c = mix(c, rc, road)
    c = mix(c, col('#6F6A58'), np.exp(-((rd - 2.7) / .55) ** 2) * .4 * (1 - road))  # 路肩
    # 出生点一带的紫色花地（真正的花是模型，这里是打底）
    fd = np.hypot(wx - 140, wz - 60)
    fl = (1 - ss(20, 42, fd + (n_blot(wx, wz) - .5) * 22)) * (1 - road)
    tone = ss(.38, .62, n_patch(wx, wz))
    fc = mix(np.broadcast_to(col('#3E3468'), (full, full, 3)).copy(), col('#5F4A86'), tone)
    c = mix(c, fc * (.85 + .3 * fine[..., None]), fl * ss(.45, .6, n_dark(wx, wz) * .5 + fine * .5 + .15) * .28)
    # 沙滩与水下：水越深越暗，地图边缘不露出明显的矩形
    c = mix(c, col('#C2AE80'), 1 - ss(SEA + .4, SEA + 2.2, b + (n_sand(wx, wz) - .5) * 1.2))
    c = mix(c, col('#2F6C74'), 1 - ss(SEA - 1.5, SEA - .1, b))
    c = mix(c, col('#0D2C3C'), 1 - ss(SEA - 6, SEA - 1.5, b))
    # 烘一点明暗和沟壑阴影
    lit = np.clip(ndl * 1.25, 0, 1)
    shade = .80 + .26 * lit
    ao = np.clip(1 + cav * .55, .62, 1.14)
    c = c * (shade * ao)[..., None]
    c = c[pad:pad + res, pad:pad + res]
    return Image.fromarray(np.clip(c, 0, 255).astype(np.uint8))


def grid(x0, z0, seg):
    idx = np.arange(seg + 1)
    wx = np.clip(x0 + idx / seg * TILE, 0, 255.99)
    wz = np.clip(z0 + TILE - idx / seg * TILE, 0, 255.99)  # 第 0 行是北边
    X, Zz = np.meshgrid(wx, wz)
    h, *_ = fields(X, Zz)
    if seg == 120:  # 高精度块的边界退回低精度网格，和相邻低精度块严丝合缝
        for arr in (h[0], h[-1], h[:, 0], h[:, -1]):
            arr[1:-1:2] = (arr[0:-2:2] + arr[2::2]) / 2
    return h


if PREVIEW:
    sheet = Image.new('RGB', (1536, 1536))
    for x0 in range(0, 256, 64):
        for z0 in range(0, 256, 64):
            print('preview', x0, z0, flush=True)
            sheet.paste(paint(x0, z0, 384), (x0 * 6, (192 - z0) * 6))
    sheet.save(os.path.join(OUT, 'albedo-preview.jpg'), quality=88)
    sys.exit(0)
manifest = []
for x0 in range(0, 256, 64):
    for z0 in range(0, 256, 64):
        name = f't{x0:03d}_{z0:03d}'
        seg = 120 if (x0, z0) in HI else 60
        sub = H[z0:min(z0 + 65, 257), x0:min(x0 + 65, 257)]
        if sub.max() < SEA - 1:  # 整块都在海面下，不用建
            print('skip sea', name)
            continue
        d = os.path.join(OUT, name)
        os.makedirs(d, exist_ok=True)
        hm = grid(x0, z0, seg)
        np.save(os.path.join(d, 'heights.npy'), hm)
        res = 2048 if seg == 120 else 1024
        paint(x0, z0, res).save(os.path.join(d, 'albedo.png'))
        ext = TILE
        rng_y = float(hm.max())  # 导入时按最大边归一化，y 从 0 算起
        manifest.append(dict(name=name, x0=x0, z0=z0, seg=seg, res=res, ymin=float(hm.min()), ymax=rng_y))
        print('tile', name, 'seg', seg, 'h', round(float(hm.min()), 1), round(rng_y, 1), flush=True)
json.dump(manifest, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
