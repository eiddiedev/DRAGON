#!/usr/bin/env python3
"""白天的云：一朵朵蓬松的积云（带透明的贴片，飘在远处）和铺满云的天空穹顶。
用法：cloud_tex.py <输出目录>"""
import json, math, os, random, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbw import Geo, write_glb
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)


def fbm(h, w, rng, base=4, oct_=5, gain=.55):
    out = np.zeros((h, w))
    amp = 1.0
    for o in range(oct_):
        n = nd.gaussian_filter(rng.normal(size=(h, w)), max(h, w) / (base * 2 ** o) / 2.5, mode='wrap')
        out += n / (n.std() + 1e-9) * amp
        amp *= gain
    return out / np.abs(out).max()


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def cumulus(seed, W=1024, H=512):
    rng = np.random.default_rng(seed)
    r_ = random.Random(seed)
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    # 用噪声扭曲坐标，边缘才蓬松
    wx, wy = fbm(H, W, rng, 7, 6, .6) * 62, fbm(H, W, rng, 7, 6, .6) * 62
    X, Y = xx + wx, yy + wy
    hf = np.zeros((H, W))
    base_y = H * .68
    n = r_.randint(14, 20)
    for i in range(n):
        u = (i + .5) / n
        cx = W * (.12 + .76 * u) + r_.uniform(-30, 30)
        envelope = math.sin(u * math.pi) ** .7
        r = r_.uniform(50, 88) * (.55 + envelope * .9)
        cy = base_y - r * r_.uniform(.2, 1.15) * (.5 + envelope)
        d2 = (X - cx) ** 2 + ((Y - cy) * 1.05) ** 2
        z = np.sqrt(np.clip(r * r - d2, 0, None))
        hf = np.maximum(hf, z)
    for _ in range(30):  # 顶上小鼓包
        cx, cy, r = r_.uniform(W * .15, W * .85), r_.uniform(H * .15, H * .6), r_.uniform(16, 40)
        d2 = (X - cx) ** 2 + (Y - cy) ** 2
        z = np.sqrt(np.clip(r * r - d2, 0, None)) * .8
        hf = np.where((hf > 2) | (z > 0), np.maximum(hf, z * (hf > 2)), hf)
    # 底部压平
    flat = smooth(base_y + 16, base_y - 34, Y)
    hf = hf * flat
    detail = fbm(H, W, rng, 24, 4)
    hf2 = nd.gaussian_filter(hf, 5.0) + detail * 5 * (hf > 1)
    gy, gx = np.gradient(nd.gaussian_filter(hf2, 3.0))
    nz = 1 / np.sqrt(gx * gx + gy * gy + 1)
    nx, ny = -gx * nz, -gy * nz
    L = np.array([-.55, -.62, .56])
    L /= np.linalg.norm(L)
    light = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    v = yy / H
    light = light * .42 + .62 - smooth(.5, .72, v) * .36
    light = np.clip(light + detail * .05, 0, 1)
    shadow, mid, high = np.array([118, 140, 172.]), np.array([206, 218, 233.]), np.array([255, 255, 255.])
    t = light[..., None]
    col = np.where(t < .55, shadow + (mid - shadow) * (t / .55), mid + (high - mid) * ((t - .55) / .45))
    alpha = smooth(.5, 22, hf2 + detail * 8) * smooth(base_y + 22, base_y - 16, Y)
    alpha = nd.gaussian_filter(alpha, 2.2)
    edge = np.clip(1 - np.maximum(np.abs(xx / W - .5) * 2, np.abs(yy / H - .5) * 2), 0, 1)
    alpha = alpha * smooth(0, .05, edge)
    img = np.dstack([col, alpha * 255]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(img, 'RGBA')


clouds = [cumulus(10 + i) for i in range(5)]
for i, c in enumerate(clouds):
    c.save(os.path.join(OUT, f'cloud_{i}.png'), optimize=True)
    g = Geo([[(0, '#ffffff'), (1, '#ffffff')]])
    a, b, c_, d = np.array([-.5, 0, -.25]), np.array([.5, 0, -.25]), np.array([.5, 0, .25]), np.array([-.5, 0, .25])
    n = np.array([0, -1.0, 0])
    # 直接写贴片 UV
    for p, t in ((a, (0, 1)), (b, (1, 1)), (c_, (1, 0)), (a, (0, 1)), (c_, (1, 0)), (d, (0, 0))):
        g.P.append(p); g.N.append(n); g.T.append(t); g.J.append((0, 0, 0, 0)); g.W.append((255, 0, 0, 0))
    nm = f'cloud_{i}'
    write_glb(os.path.join(OUT, nm + '.glb'), g, name=nm, rough=1.0, image=c, emissive=(.95, .95, .95), alpha=True)
    print(nm, round(os.path.getsize(os.path.join(OUT, nm + '.glb')) / 1e6, 2), 'MB')
# ---------- 白天穹顶：蓝天 + 高空卷云 + 大量远云；下半边是海平线的雾色，和海接上
W, H = 2048, 1024
rng = np.random.default_rng(2)
vv = (np.arange(H) / (H - 1))[:, None]   # 0 顶部（天顶）1 底部
sky = np.zeros((H, W, 3))
top, mid, hor = np.array([46, 110, 196.]), np.array([96, 162, 226.]), np.array([206, 230, 244.])
el = np.clip((.5 - vv) / .5, 0, 1)   # 0 地平线 1 天顶
for c in range(3):
    sky[..., c] = np.where(el < .22, hor[c] + (mid[c] - hor[c]) * (el / .22) ** .6, mid[c] + (top[c] - mid[c]) * ((el - .22) / .78))
cir = fbm(H, W, rng, 5, 6, .6)
cir2 = fbm(H, W, rng, 12, 4)
cirrus = smooth(.08, .55, cir + cir2 * .2) * smooth(.02, .3, el) * .62
sky = sky + (np.array([255, 255, 255.]) - sky) * cirrus[..., None]
pil = Image.fromarray(sky.clip(0, 255).astype(np.uint8)).convert('RGBA')
r_ = random.Random(5)
for i in range(70):
    c = clouds[r_.randrange(5)]
    # 越靠近地平线越小越密
    e = r_.random() ** 1.7
    w_ = int(90 + 330 * e)
    y_ = int(H * .5 - 8 - e * H * .3 - w_ * .26)
    x_ = r_.randrange(W)
    sp = c.resize((w_, w_ // 2), Image.LANCZOS)
    for dx in (0, -W):
        pil.alpha_composite(sp, (max(0, x_ + dx), max(0, y_))) if x_ + dx >= 0 else None
arr = np.asarray(pil.convert('RGB')).astype(float)
sea = np.array([150, 196, 224.])
bl = smooth(.5, .52, vv)
arr = arr * (1 - bl[..., None]) + sea * bl[..., None]
Image.fromarray(arr.astype(np.uint8)).save(os.path.join(OUT, 'sky_day.jpg'), quality=92)
print('dome done')
