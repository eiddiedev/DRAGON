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
TILES = sys.argv[4].split(',') if len(sys.argv) > 4 else None  # 只生成指定地块
EROSION = nd.zoom(np.load(os.path.join(OUT, 'erosion.npy')), 1, order=0)
WEAR = np.load(os.path.join(OUT, 'wear.npy'))


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


def pnoise(res, beta, fmin, fmax, seed, aniso=None):
    '''无缝循环的噪声：频谱滤波，结果 0..1。aniso=(角度, 拉长倍数)'''
    r = np.random.default_rng(seed)
    fy = np.fft.fftfreq(res)[:, None] * res
    fx = np.fft.fftfreq(res)[None, :] * res
    if aniso:
        a, k = aniso
        u, v = fx * math.cos(a) + fy * math.sin(a), -fx * math.sin(a) + fy * math.cos(a)
        f = np.hypot(u * k, v)
    else:
        f = np.hypot(fx, fy)
    f[0, 0] = 1
    amp = f ** (-beta / 2)
    amp[(f < fmin) | (f > fmax)] = 0
    o = np.real(np.fft.ifft2(np.fft.fft2(r.normal(size=(res, res))) * amp))
    lo, hi = np.percentile(o, .5), np.percentile(o, 99.5)
    return np.clip((o - lo) / (hi - lo), 0, 1).astype(np.float32)


class PN:
    def __init__(self, a, period):
        self.a, self.k = a, a.shape[0] / period

    def __call__(self, x, z_):
        return nd.map_coordinates(self.a, [z_ * self.k, x * self.k], order=1, mode='grid-wrap')


P_clump = PN(pnoise(1024, 1.8, 4, 256, 31), 32.0)      # 草丛：1~8 米一团
P_tuft_a = PN(pnoise(1024, 1.2, 12, 500, 32, (.6, 5)), 12.0)   # 草叶：细长条纹
P_tuft_b = PN(pnoise(1024, 1.2, 12, 500, 33, (2.3, 5)), 13.0)
P_rock = PN(pnoise(1024, 2.0, 4, 400, 34), 40.0)       # 岩面碎裂
P_rock2 = PN(pnoise(1024, 1.7, 16, 500, 35), 11.0)     # 岩石微观
P_snow = PN(pnoise(1024, 2.2, 3, 200, 36, (.3, 3)), 37.0)   # 雪面风纹
P_soil = PN(pnoise(1024, 1.6, 10, 500, 37), 9.0)       # 土路碎石
P_big = PN(pnoise(1024, 2.6, 2, 60, 38), 64.0)         # 大块岩面，不带颗粒

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
ero, wear = Grid2048(EROSION), Grid2048(WEAR)
# 全图统一算一次大尺度曲率，地块边界才不会断
_Hf = nd.zoom(H, EROSION.shape[0] / H.shape[0], order=3)[:EROSION.shape[0], :EROSION.shape[0]] + EROSION
_cell = 256 / (EROSION.shape[0] - 1)
cav2_g = Grid2048((_Hf - nd.gaussian_filter(_Hf, 7 / _cell)).astype(np.float32))
_gz, _gx = np.gradient(nd.gaussian_filter(_Hf, 1.2 / _cell), _cell)
steep_g = Grid2048(np.degrees(np.arctan(np.hypot(_gx, _gz))).astype(np.float32))


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
SITES = json.load(open(os.path.join(OUT, 'sites.json')))
TRAILS = [catmull(tr) for tr in SITES['trails']]
ROAD += TRAILS
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
    grassy = (1 - ss(40, 50, hr)) * np.maximum(.82, ss(-.25, .55, ((127 - x) * .45 + (176 - z_) * .9) / (hr + 1)))
    outcrop = ss(.60, .68, n_rockmix(x, z_) * .55 + n_blot(x, z_) * .45) * ss(24, 30, hr)  # 草坡上露出的岩块
    rock = np.maximum(rock * (1 - grassy * .85), outcrop * (1 - ss(40, 48, hr)) * .95)
    # 山势冲沟：只在高处，不碰小山顶和道路
    high = ss(62, 78, b) * (1 - (1 - ss(24, 34, hr)))
    gully = (lic_c(x, z_) - .5) * 3.4 + (lic_f(x, z_) - .5) * .9
    # 小山的坡面起伏，岩块鼓出来
    hill_relief = (1 - ss(40, 47, hr)) * ss(21, 27, hr) * ((lic_c(x, z_) - .5) * .5 + outcrop * 1.1 + (n_patch(x, z_) - .5) * 2.4 + (n_blot(x, z_) - .5) * 1.6)   # 不要顺坡的竖条
    h = b + (rock * (facet + strata) * (1 - high) + (1 - rock) * wave * (1 - high)) * keep + hill_relief * keep + ero(x, z_)
    return h, b, rock, cell, edge


def col(c):
    return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], float)


def mix(a, b, t):
    if b.ndim == 1:
        b = np.broadcast_to(b, a.shape)
    return a * (1 - t[..., None]) + b * t[..., None]


def paint(x0, z0, res):
    """返回 (基础色, 法线)。全部按世界坐标取样，相邻地块无缝。"""
    m_per_px = TILE / res
    pad = int(8 / m_per_px)
    ys, xs = np.mgrid[-pad:res + pad, -pad:res + pad]
    wx = x0 + (xs + .5) / res * TILE
    wz = z0 + TILE - (ys + .5) / res * TILE  # 第 0 行是北边
    wx = np.clip(wx, 0, 255.99).astype(np.float32)
    wz = np.clip(wz, 0, 255.99).astype(np.float32)
    full = res + 2 * pad
    h, b, rock, cell, edge = fields(wx, wz)
    lc = lic_c(wx, wz)
    fine = n_fine(wx, wz)
    clump, ta, tb = P_clump(wx, wz), P_tuft_a(wx, wz), P_tuft_b(wx, wz)
    tuft = np.maximum(ta, tb * .9)
    prock, prock2 = P_rock(wx, wz), P_rock2(wx, wz)
    psnow, psoil = P_snow(wx, wz), P_soil(wx, wz)
    pbig = P_big(wx, wz)
    wr = np.clip(np.log1p(np.maximum(wear(wx, wz), 0)) / 5, 0, 1)
    # 高度细节：岩石碎裂、草丛起伏，只进法线，不改碰撞
    ridged = 1 - np.abs(prock * 2 - 1)
    hd = b * 0
    road = road_d(wx, wz) + (n_patch(wx, wz) - .5) * 1.3
    rmask = 1 - ss(1.5, 2.6, road)
    line = 80 - 24 * ss(196, 222, wz)
    # ---------- 先算坡度，用来决定雪和岩石
    sm0 = nd.gaussian_filter(h, .5 / m_per_px)
    gz0, gx0 = np.gradient(sm0, m_per_px)
    nyv0 = 1 / np.sqrt(1 + gx0 * gx0 + gz0 * gz0)
    steep = steep_g(wx, wz)
    cav1 = sm0 - nd.gaussian_filter(sm0, 2.0 / m_per_px)     # 小沟小脊
    cav2 = cav2_g(wx, wz)                                    # 大沟大脊
    # 雪线：高处积雪，沟里多、脊上少，陡壁挂不住
    snow = ss(line - 4, line + 6, h + (n_snow(wx, wz) - .5) * 12 - np.clip(cav2, -3, 3) * 1.2 + (pbig - .5) * 8)
    bare = ss(72, 84, steep + (pbig - .5) * 22 + np.clip(cav1, -1, 1) * 6)               # 只有真正的陡壁才露岩
    bare = np.maximum(bare, ss(1.6, 3.4, cav2 + (pbig - .5) * 2.8) * ss(46, 66, steep))   # 尖山脊露岩
    hrr = np.hypot(wx - 127, wz - 176)
    rock = np.maximum(rock, ss(line - 8, line, h) * ss(44, 50, hrr))                     # 雪线附近没有草，小山除外
    snow = snow * (1 - bare) * ss(46, 54, np.hypot(wx - 127, wz - 176))
    snow_edge = np.clip(snow * (1 - snow) * 4, 0, 1)
    # ---------- 法线用的细节高度
    hd = h.copy()
    rk = np.maximum(rock, ss(line - 12, line - 2, h))
    hd = hd + (ridged - .5) * .4 * rk * (1 - snow * .9) + (prock2 - .5) * .08 * rk * (1 - snow) + (pbig - .5) * 1.2 * rk * (1 - snow * .8)
    hd = hd + (psnow - .5) * .10 * snow
    hd = hd + (clump - .5) * .10 * (1 - rk) * (1 - rmask) + (tuft - .4) * .05 * (1 - rk) * (1 - rmask)
    hd = hd + (psoil - .5) * .05 * rmask
    gz, gx = np.gradient(nd.gaussian_filter(hd, .7), m_per_px)
    nyv = 1 / np.sqrt(1 + gx * gx + gz * gz)
    # 切线空间：x 东、y 北，第 0 行在北，gz 沿行向南
    ntx, nty = -gx * nyv, gz * nyv * -1
    nrm = np.dstack([ntx * .5 + .5, nty * .5 + .5, nyv * .5 + .5])
    # ---------- 草：墨绿打底，大片色块 + 草丛 + 草叶
    c = mix(np.broadcast_to(col('#3B5A2A'), (full, full, 3)).copy(), col('#4D6A30'), ss(.36, .66, n_blot(wx, wz)))
    c = mix(c, col('#2A4524'), ss(.52, .68, n_dark(wx, wz)) * .85)
    c = mix(c, col('#66753A'), ss(.60, .72, n_patch(wx, wz)) * .55)   # 枯黄片
    c = mix(c, col('#75703F'), ss(.66, .78, n_moss(wx, wz)) * .35)
    grass_tone = (.62 + .62 * ss(.28, .72, clump))                     # 草丛暗缝和亮顶
    blade = (.72 + .62 * ss(.3, .8, tuft))                             # 草叶
    c = c * (grass_tone * blade)[..., None]
    c = c + (np.array([18., 22., 6.]) * (ss(.72, .95, tuft) * ss(.45, .8, clump))[..., None])  # 草尖反光
    # 零星野花
    petals = ss(.965, .985, fine * .5 + ta * .5) * ss(.5, .62, n_patch(wx, wz))
    c = mix(c, col('#D9C34E'), petals * .8)
    # ---------- 岩石：分层 + 碎裂 + 冷暖
    strata_v = (h + (n_strata(wx, wz) - .5) * 40 + (pbig - .5) * 18) * 1.6
    band = .5 + .3 * np.sin(strata_v) + .2 * np.sin(strata_v * 2.3 + 1.3)
    r = mix(np.broadcast_to(col('#3F4047'), (full, full, 3)).copy(), col('#62626A'), ss(.25, .8, pbig))
    r = r * (.9 + .16 * band)[..., None]
    r = mix(r, col('#2C2D34'), ss(.5, .75, 1 - pbig) * .5)
    r = mix(r, col('#7D6B5A'), ss(.52, .72, n_warm(wx, wz)) * .25)
    r = r * ((.86 + .26 * ss(.25, .8, prock2)) * (.88 + .2 * ss(.3, .85, ridged)))[..., None]
    r = r * (1 - ss(.72, .95, wr)[..., None] * .35)                   # 冲沟里更暗
    r = mix(r, col('#46592F'), ss(.70, .96, nyv0) * ss(.42, .62, n_moss(wx, wz)) * .7)  # 平处长苔
    c = mix(c, r, rock)
    c = mix(c, col('#33502A'), np.clip(1 - np.abs(rock - .5) * 2, 0, 1) * .3)
    # ---------- 雪：大块亮面、蓝影、风纹，边缘带碎雪
    sc = mix(np.broadcast_to(col('#AEBFDC'), (full, full, 3)).copy(), col('#F6F8FC'), ss(-.5, .9, np.clip(cav1, -1, 1) + (psnow - .5) * 1.4 + .35))
    sc = sc * (.96 + .08 * ss(.3, .7, prock2))[..., None]
    sc = mix(sc, col('#8496BD'), ss(.55, .95, wr) * .35)
    # 雪线附近岩雪交错
    snow2 = ss(.15, .75, snow + (prock - .5) * .35 * np.clip(snow * (1 - snow) * 4, 0, 1))
    c = mix(c, sc, snow2)
    # 雪线下碎石带
    scree = ss(line - 16, line - 4, h) * (1 - np.clip(snow, 0, 1)) * (1 - rock) * .55
    c = mix(c, col('#5B5B5E') * (.8 + .5 * psoil[..., None]), scree)
    # ---------- 道路：夯土碎石，草吃路边
    rc = mix(np.broadcast_to(col('#7D6C50'), (full, full, 3)).copy(), col('#62553F'), ss(.38, .62, psoil))
    rc = mix(rc, col('#9A8A6C'), ss(.62, .78, psoil) * .75)
    rc = mix(rc, col('#4B4034'), ss(.72, .9, 1 - clump) * .35)   # 车辙
    edge_noise = (tuft - .4) * .9
    rmask2 = 1 - ss(1.5, 2.6, road + edge_noise)
    c = mix(c, rc, rmask2)
    # ---------- 林间空地和花地打底
    for s in SITES['sites'].values():
        dd = np.hypot(wx - s['x'], wz - s['z']) + (pbig - .5) * 5
        c = mix(c, mix(rc, c, ss(.3, .7, clump) * .8), (1 - ss(s['r'] * .45, s['r'] * .8, dd)) * .85)
    fd = np.maximum(np.hypot(wx - 140, wz - 60) + (pbig - .5) * 20, 40 - (np.hypot(wx - 130, wz - 46) - 9) * 3)  # 出生点一圈保持草地
    fl = (1 - ss(26, 42, fd)) * (1 - rmask2) * ss(.42, .62, ta * .6 + fine * .4)
    c = mix(c, col('#4A3A78') * (.7 + .6 * tb[..., None]), (1 - ss(26, 42, fd)) * (1 - rmask2) * .72)
    c = mix(c, col('#7D5FC0') * (.8 + .5 * tb[..., None]), fl * .55)
    # ---------- 沙滩、水下
    c = mix(c, col('#B5A277') * (.85 + .3 * psoil[..., None]), 1 - ss(SEA + .4, SEA + 2.2, b + (n_sand(wx, wz) - .5) * 1.2))
    c = mix(c, col('#2F6C74'), 1 - ss(SEA - 1.5, SEA - .1, b))
    c = mix(c, col('#0D2C3C'), 1 - ss(SEA - 6, SEA - 1.5, b))
    # 只烘很弱的沟壑阴影，明暗交给引擎和法线
    ao = np.clip(1 + np.clip(cav1, -1.2, 1.2) * .18 + np.clip(cav2, -3, 3) * .05, .68, 1.12)
    c = c * ao[..., None]
    c = c[pad:pad + res, pad:pad + res]
    nrm = nrm[pad:pad + res, pad:pad + res]
    nimg = Image.fromarray(np.clip(nrm * 255, 0, 255).astype(np.uint8)).resize((res // 2, res // 2), Image.BILINEAR)
    return Image.fromarray(np.clip(c, 0, 255).astype(np.uint8)), nimg


def grid(x0, z0, seg):
    idx = np.arange(seg + 1)
    wx = np.clip(x0 + idx / seg * TILE, 0, 255.99)
    wz = np.clip(z0 + TILE - idx / seg * TILE, 0, 255.99)  # 第 0 行是北边
    X, Zz = np.meshgrid(wx, wz)
    h, *_ = fields(X, Zz)
    return h


if PREVIEW:
    sheet = Image.new('RGB', (1536, 1536))
    for x0 in range(0, 256, 64):
        for z0 in range(0, 256, 64):
            print('preview', x0, z0, flush=True)
            sheet.paste(paint(x0, z0, 384)[0], (x0 * 6, (192 - z0) * 6))
    sheet.save(os.path.join(OUT, 'albedo-preview.jpg'), quality=88)
    sys.exit(0)
manifest = []
for x0 in range(0, 256, 64):
    for z0 in range(0, 256, 64):
        name = f't{x0:03d}_{z0:03d}'
        if TILES and name not in TILES:
            continue
        seg = 120
        sub = H[z0:min(z0 + 65, 257), x0:min(x0 + 65, 257)]
        if sub.max() < SEA - 1:  # 整块都在海面下，不用建
            print('skip sea', name)
            continue
        d = os.path.join(OUT, name)
        os.makedirs(d, exist_ok=True)
        hm = grid(x0, z0, seg)
        np.save(os.path.join(d, 'heights.npy'), hm)
        res = 2048
        alb, nrm = paint(x0, z0, res)
        alb.save(os.path.join(d, 'albedo.png'))
        nrm.save(os.path.join(d, 'normal.png'))
        ext = TILE
        rng_y = float(hm.max())  # 导入时按最大边归一化，y 从 0 算起
        manifest.append(dict(name=name, x0=x0, z0=z0, seg=seg, res=res, ymin=float(hm.min()), ymax=rng_y))
        print('tile', name, 'seg', seg, 'h', round(float(hm.min()), 1), round(rng_y, 1), flush=True)
if not TILES:
    json.dump(manifest, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
else:
    json.dump(manifest, open(os.path.join(OUT, 'manifest_part.json'), 'w'), indent=1)
