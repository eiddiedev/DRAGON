#!/usr/bin/env python3
"""生成夜空贴图：穹顶（等距柱状）、三层云雾漩涡（带透明）、月亮（带环形山和光晕）。
用法：sky_tex.py <输出目录> [dome] [swirl] [moon]，不写就全部生成。
穹顶贴图的 u=0.5 对着北（+Y），v=1 是天顶。
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

OUT = sys.argv[1]
PARTS = set(sys.argv[2:]) or {'dome', 'day', 'swirl', 'moon'}
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(1208)


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def col(c):
    return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], float)


def mix(a, b, t):
    return a * (1 - t[..., None]) + b * t[..., None]


def periodic_noise(h, w, power=1.9):
    """1/f 噪声，上下左右都能无缝接上。"""
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.fftfreq(w)[None, :] * w
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1
    spec = (rng.normal(size=(h, w)) + 1j * rng.normal(size=(h, w))) / f ** power
    spec[0, 0] = 0
    n = np.fft.ifft2(spec).real
    return (n - n.min()) / (n.max() - n.min())


def sample(n, u, v):
    """在无缝噪声上按 0..1 的坐标取样，超出范围自动绕回。"""
    h, w = n.shape
    return nd.map_coordinates(n, [v * h, u * w], order=1, mode='grid-wrap')


def dome():
    H, W = 4096, 8192
    vv, uu = np.mgrid[0:H, 0:W]
    el = (.5 - (vv + .5) / H) * np.pi  # 仰角
    az = ((uu + .5) / W - .5) * 2 * np.pi  # 0 是北，向东为正
    dx, dy, dz = np.cos(el) * np.sin(az), np.cos(el) * np.cos(az), np.sin(el)
    # 漩涡中心的方向（北偏上）
    cx, cy, cz = 0, np.cos(np.radians(30)), np.sin(np.radians(30))
    near = np.clip(dx * cx + dy * cy + dz * cz, -1, 1)
    ang = np.degrees(np.arccos(near))
    cloud = periodic_noise(H, W, 2.0)
    cloud2 = periodic_noise(H, W, 1.6)
    up = ss(-.05, .9, np.sin(el))
    c = mix(np.broadcast_to(col('#3A1C6E'), (H, W, 3)).copy(), col('#0D1038'), up)  # 地平线紫 → 天顶深蓝
    c = mix(c, col('#7A2C8E'), (1 - ss(0, .28, np.abs(np.sin(el)))) * ss(.42, .72, cloud) * .75)  # 地平线附近的品红云
    c = mix(c, col('#4A3CC8'), (1 - ss(18, 88, ang + (cloud - .5) * 34)) * .92)  # 漩涡背后的紫蓝
    c = mix(c, col('#7464EE'), (1 - ss(2, 30, ang + (cloud2 - .5) * 16)) * .7)
    c = mix(c, col('#060716'), ss(.5, .78, cloud2) * .42 * ss(30, 90, ang))  # 其他方向的暗云
    c = mix(c, col('#090A20'), ss(-.02, -.2, np.sin(el)))  # 地平线以下
    # 星星：在球面上均匀撒点，小而密，亮星很少
    stars = np.zeros((H, W))
    for size, count, amp in ((.8, 9000, .45), (1.1, 2200, .8), (1.7, 260, 1.0)):
        z_ = rng.uniform(-.05, 1, count)
        th = rng.uniform(-np.pi, np.pi, count)
        v = ((.5 - np.arcsin(z_) / np.pi) * H).astype(int).clip(0, H - 1)
        u = (((th / (2 * np.pi)) + .5) * W).astype(int).clip(0, W - 1)
        layer = np.zeros((H, W))
        layer[v, u] = rng.uniform(.4, 1, count)
        g = nd.gaussian_filter(layer, size, mode='wrap')
        stars = np.maximum(stars, g / g.max() * amp)
    c = c + (col('#F2F0FF') - c) * np.clip(stars * 1.25, 0, 1)[..., None]
    Image.fromarray(np.clip(c, 0, 255).astype(np.uint8)).save(os.path.join(OUT, 'sky_dome.jpg'), quality=88)


def day_dome():
    """白天：通透的蓝天、大朵积云、西南方的太阳光晕。"""
    H, W = 2048, 4096
    vv, uu = np.mgrid[0:H, 0:W]
    el = (.5 - (vv + .5) / H) * np.pi
    az = ((uu + .5) / W - .5) * 2 * np.pi
    dx, dy, dz = np.cos(el) * np.sin(az), np.cos(el) * np.cos(az), np.sin(el)
    up = np.clip(np.sin(el), -1, 1)
    c = mix(np.broadcast_to(col('#BFE4F7'), (H, W, 3)).copy(), col('#4FA5EA'), ss(.0, .34, up))
    c = mix(c, col('#2F7FD9'), ss(.32, .95, up))
    L = np.array([-.663, -.383, .643])  # 太阳方向：x 东，y 北，z 上
    sun = np.clip(dx * L[0] + dy * L[1] + dz * L[2], -1, 1)
    c = mix(c, col('#FFF4D6'), ss(.86, 1.0, sun) * .85)
    c = mix(c, col('#FFFFFF'), ss(.996, .9995, sun))
    # 云：两层噪声，地平线附近压扁、高处舒展
    n1 = periodic_noise(H, W, 2.05)
    n2 = periodic_noise(H, W, 1.55)
    band = ss(-.02, .08, up) * (1 - ss(.72, .98, up))
    den = (n1 + (n2 - .5) * .42 - .50) * 7.5
    cloud = np.clip(ss(.12, .86, den), 0, 1) * band
    shadow = np.clip(ss(.45, 1.5, den), 0, 1) * band  # 云底偏灰蓝
    cc = mix(np.broadcast_to(col('#FFFFFF'), (H, W, 3)).copy(), col('#A9BEDD'), shadow * .8)
    cc = mix(cc, col('#FFF3D8'), ss(.55, .95, sun) * .6)
    c = mix(c, cc, cloud)
    c = mix(c, col('#3B6D8F'), ss(-.02, -.18, up))  # 地平线以下
    Image.fromarray(np.clip(c, 0, 255).astype(np.uint8)).save(os.path.join(OUT, 'sky_day.jpg'), quality=90)


def swirl_layer(name, S, arms, twist, lo, hi, streak_amp, puff_amp, inner, outer, dark, lit, seed_shift=0.0, alpha_max=1.0):
    """一层云。沿旋臂方向拉长的噪声做丝状云絮，再用团块噪声把边缘吃碎。"""
    ys, xs = np.mgrid[0:S, 0:S]
    x, y = (xs + .5) / S * 2 - 1, (ys + .5) / S * 2 - 1
    r = np.hypot(x, y)
    th = np.arctan2(y, x)
    lr = np.log(r + .03)
    puff = periodic_noise(S, S, 1.75)
    puff2 = periodic_noise(S, S, 1.25)
    streak = periodic_noise(1024, 1024, 1.55)
    streak2 = periodic_noise(1024, 1024, 1.2)
    warp = puff - .5
    # p：绕一圈增加 arms 的旋臂相位；q：顺着旋臂走的坐标
    p = th / (2 * np.pi) * arms + lr * twist + warp * .85 + seed_shift
    q = lr * .22
    band = .5 + .5 * np.cos(2 * np.pi * p)
    fil = nd.gaussian_filter(sample(streak, p * 3, q + warp * .10), S / 900)  # 垂直旋臂方向细，顺着旋臂方向长
    fil2 = nd.gaussian_filter(sample(streak2, p * 8, q * 2.2 + warp * .06), S / 1400)
    dens = band ** 1.35 + (fil - .5) * streak_amp + (fil2 - .5) * streak_amp * .32 + (puff2 - .5) * puff_amp
    a = ss(lo, hi, dens)
    a = a * (.72 + .28 * ss(.25, .7, puff2))  # 云内部有疏有密，不是一整块
    fade = (1 - ss(outer * .62, outer, r + warp * .30)) * ss(inner * .4, inner * 1.5, r + warp * .06)
    a = nd.gaussian_filter(a * fade, S / 1100)  # 去掉等高线一样的细线，边缘更像雾
    # 受光：稀薄处透出紫光，浓密处接近黑；朝漩涡中心的一侧更亮
    gy, gx = np.gradient(nd.gaussian_filter(a, S / 340))
    toward_center = -(gx * x + gy * y) / (r + .02)
    light = np.clip(toward_center * S / 46, -1, 1)
    c = mix(np.broadcast_to(col(dark), (S, S, 3)).copy(), col(lit), np.clip((1 - a) ** 1.5 * .95 + light * .34, 0, 1))
    c = c * (.9 + .2 * puff2[..., None])
    rgba = np.dstack([np.clip(c, 0, 255), np.clip(a * alpha_max, 0, 1) * 255]).astype(np.uint8)
    Image.fromarray(rgba).save(os.path.join(OUT, name + '.png'), optimize=True)
    print(name, 'alpha mean', round(float(a.mean()), 3))


def swirl():
    # 最后面：大而淡的雾，把漩涡和天空融在一起
    swirl_layer('sky_swirl_a', 1536, 3, 1.05, .30, 1.0, .85, .6, .10, 1.0, '#120E36', '#6A58E0', .15, .72)
    # 中间：主体烟云
    swirl_layer('sky_swirl_b', 2048, 4, 1.55, .42, .90, .95, .5, .07, .98, '#05050F', '#4636B8', .0, .98)
    # 最前面：靠近中心转得快的丝状薄云
    swirl_layer('sky_swirl_c', 1536, 5, 1.9, .58, 1.05, 1.1, .45, .05, .80, '#0A0920', '#7E6CF2', .4, .85)


def moon():
    M = 1536
    ys, xs = np.mgrid[0:M, 0:M]
    x, y = (xs + .5) / M * 2 - 1, (ys + .5) / M * 2 - 1
    r = np.hypot(x, y)
    R = .5  # 月面半径，外面是光晕
    nx, ny = x / R, y / R
    rr = np.clip(nx * nx + ny * ny, 0, 1)
    nz = np.sqrt(1 - rr)
    # 球面取样，靠近边缘的纹理被压扁，看起来才像球
    sx, sy = np.where(rr < 1, nx / (1 + nz), 0), np.where(rr < 1, ny / (1 + nz), 0)
    low = periodic_noise(1024, 1024, 2.3)
    mid = periodic_noise(1024, 1024, 1.7)
    hi = periodic_noise(2048, 2048, 1.05)
    lo_s = sample(low, sx * 1.35 + .2, sy * 1.35 + .6)
    mid_s = sample(mid, sx * .8, sy * .8)
    hi_s = sample(hi, sx * 1.3, sy * 1.3)
    # 月海：边界有大小起伏的暗区
    blot = nd.gaussian_filter(lo_s + (mid_s - .5) * .34, 5)
    cut = np.percentile(blot[rr < 1], 64)
    mare = ss(cut - .03, cut + .075, blot)
    L = .90 - mare * .36 + (mid_s - .5) * .22 + (hi_s - .5) * .30
    # 环形山：亮边、暗底，大的少小的多；少数有放射纹
    crater = np.zeros((M, M))
    rays = np.zeros((M, M))
    for i in range(420):
        s = .006 * (1 / rng.uniform(.03, 1)) ** .62
        s = min(s, .055)
        a, d = rng.uniform(0, 2 * np.pi), np.sqrt(rng.uniform(0, 1)) * .97
        cx, cy = np.cos(a) * d, np.sin(a) * d
        foreshort = np.sqrt(max(1 - d * d, .03))
        ex, ey = np.cos(a), np.sin(a)
        px0, py0 = int((cx * R + 1) / 2 * M), int((cy * R + 1) / 2 * M)
        w = int(s * R * M * 2.2) + 3
        x0, x1, y0, y1 = max(px0 - w, 0), min(px0 + w, M), max(py0 - w, 0), min(py0 + w, M)
        if x1 <= x0 or y1 <= y0:
            continue
        dxx, dyy = nx[y0:y1, x0:x1] - cx, ny[y0:y1, x0:x1] - cy
        along = (dxx * ex + dyy * ey) / foreshort
        across = -dxx * ey + dyy * ex
        q = np.hypot(along, across) / s
        depth = rng.uniform(.5, 1)
        crater[y0:y1, x0:x1] += depth * (-.05 * (1 - ss(.55, .95, q)) + .07 * np.exp(-((q - 1.0) / .28) ** 2))
        # 向阳面亮、背阴面暗，给一点立体感
        shade = np.clip((dxx * .6 - dyy * .8) / (s + 1e-4), -1, 1)
        crater[y0:y1, x0:x1] += depth * .035 * shade * np.exp(-((q - .85) / .3) ** 2)
    for i in range(5):
        a, d = rng.uniform(0, 2 * np.pi), rng.uniform(.1, .85)
        cx, cy = np.cos(a) * d, np.sin(a) * d
        dxx, dyy = nx - cx, ny - cy
        q = np.hypot(dxx, dyy)
        ang = np.arctan2(dyy, dxx)
        ray = sample(low, ang / (2 * np.pi) * 4, np.full_like(ang, rng.uniform(0, 1)))
        rays = np.maximum(rays, ss(.42, .72, ray) * np.exp(-q / rng.uniform(.08, .2)) * ss(.0, .04, q))
    L = L + crater + rays * .07
    L = nd.gaussian_filter(L, .7)
    # 边缘略暗，但不要太多，满月的亮度比较平
    L = L * (.9 + .1 * nz ** .5) + ss(R * .97, R, r) * .12
    L = np.clip(L, 0, 1.15)[..., None]
    c = col('#5C6340') * (1 - L) + col('#FBF8CE') * L
    # 光晕：内圈亮、向外很快变淡
    halo = np.exp(-np.clip(r - R, 0, None) / .085) * .36 + np.exp(-np.clip(r - R, 0, None) / .26) * .16
    halo = halo * (1 - ss(.82, 1.0, r))
    edge = ss(R + .0035, R - .0035, r)
    c = np.where((r < R + .006)[..., None], c, np.broadcast_to(col('#C9D685'), c.shape))
    a = np.maximum(edge, halo)
    rgba = np.dstack([np.clip(c, 0, 255), np.clip(a, 0, 1) * 255]).astype(np.uint8)
    Image.fromarray(rgba).save(os.path.join(OUT, 'sky_moon.png'), optimize=True)


if 'dome' in PARTS:
    dome()
if 'day' in PARTS:
    day_dome()
if 'swirl' in PARTS:
    swirl()
if 'moon' in PARTS:
    moon()
for n in sorted(os.listdir(OUT)):
    print(n, round(os.path.getsize(os.path.join(OUT, n)) / 1e6, 2), 'MB')
