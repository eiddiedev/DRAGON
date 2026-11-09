#!/usr/bin/env python3
"""花丛贴图（带透明）：上面一条是侧面看的花带，贴在竖直面片上；下面是俯视的花毯，贴在地面片上。
用法：flower_tex.py <输出目录>
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
S = 2  # 超采样
W, H = 2048 * S, 2048 * S
BAND = int(H * .36)  # 花带占上面 36%


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


PETALS = [(124, 79, 201), (154, 95, 214), (181, 123, 228), (213, 155, 232), (239, 226, 250), (232, 120, 200)]
CORE = (245, 211, 107)
GREEN = [(42, 84, 42), (58, 104, 48), (34, 70, 38), (74, 120, 56)]


def flower(draw, x, y, r, col, k=1.0, tilt=.62, rnd=random):
    """一朵花：5~6 片椭圆花瓣围一圈，tilt<1 表示从侧面看被压扁。"""
    n = rnd.choice((5, 5, 6))
    a0 = rnd.uniform(0, math.tau)
    for i in range(n):
        a = a0 + i / n * math.tau
        px, py = x + math.cos(a) * r * .62, y + math.sin(a) * r * .62 * tilt
        rx, ry = r * .56, r * .4 * (tilt + .3)
        c = shade(col, k * rnd.uniform(.88, 1.1))
        draw.ellipse((px - rx, py - ry, px + rx, py + ry), fill=c + (255,))
        # 花瓣里的亮线
        draw.line((x, y, px + math.cos(a) * r * .3, py + math.sin(a) * r * .3 * tilt), fill=shade(col, k * 1.25) + (255,), width=max(1, int(r * .07)))
    cr = r * .24
    draw.ellipse((x - cr, y - cr * tilt, x + cr, y + cr * tilt), fill=shade(CORE, k) + (255,))


def leaf(draw, x, y, L, ang, col):
    pts = []
    for t in range(9):
        u = t / 8
        w = math.sin(u * math.pi) * L * .2
        cx, cy = x + math.cos(ang) * L * u, y + math.sin(ang) * L * u
        pts.append((cx - math.sin(ang) * w, cy + math.cos(ang) * w))
    for t in range(8, -1, -1):
        u = t / 8
        w = math.sin(u * math.pi) * L * .2
        cx, cy = x + math.cos(ang) * L * u, y + math.sin(ang) * L * u
        pts.append((cx + math.sin(ang) * w, cy - math.cos(ang) * w))
    draw.polygon(pts, fill=col + (255,))


img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
rnd = random.Random(11)
# ---------- 花带：底部是地面，从后往前画三层
items = []
for layer, (count, r0, r1, k) in enumerate(((95, 34, 52, .62), (80, 52, 78, .82), (60, 78, 112, 1.0))):
    for _ in range(count):
        items.append((layer, rnd.uniform(0, W), r0 * S, r1 * S, k))
for layer, x, r0, r1, k in items:
    r = rnd.uniform(r0, r1)
    h = (BAND * rnd.uniform(.4, .72)) * (1 - layer * .16)
    top = BAND - h
    lean = rnd.uniform(-.2, .2) * h
    g = shade(rnd.choice(GREEN), .8 + layer * .12)
    d.line([(x, BAND), (x + lean * .5, BAND - h * .55), (x + lean, top)], fill=g + (255,), width=int(r * .14))
    for _ in range(rnd.randint(2, 4)):
        t = rnd.uniform(.05, .6)
        lx, ly = x + lean * t, BAND - h * t
        leaf(d, lx, ly, r * rnd.uniform(1.3, 2.2), rnd.choice((-1, 1)) * rnd.uniform(.2, .9) - (math.pi / 2) + rnd.choice((-1.1, 1.1)), g)
    flower(d, x + lean, top, r, rnd.choice(PETALS), k, .62, rnd)
# 花带底部的草
for _ in range(600):
    x = rnd.uniform(0, W)
    h = rnd.uniform(.12, .32) * BAND
    g = rnd.choice(GREEN)
    d.polygon([(x - 12 * S, BAND), (x + 12 * S, BAND), (x + rnd.uniform(-30, 30) * S, BAND - h)], fill=g + (255,))
# ---------- 花毯：俯视，圆形羽化
cy0 = BAND + (H - BAND) // 2
cx0 = W // 2
R = (H - BAND) // 2 - 6
for _ in range(1500):
    a, q = rnd.uniform(0, math.tau), R * math.sqrt(rnd.random())
    x, y = cx0 + math.cos(a) * q, cy0 + math.sin(a) * q
    c = rnd.choice(GREEN)
    leaf(d, x, y, rnd.uniform(40, 90) * S, rnd.uniform(0, math.tau), c)
for _ in range(1050):
    a, q = rnd.uniform(0, math.tau), (R * .97) * math.sqrt(rnd.random())
    x, y = cx0 + math.cos(a) * q, cy0 + math.sin(a) * q
    flower(d, x, y, rnd.uniform(26, 50) * S, rnd.choice(PETALS), rnd.uniform(.8, 1.05), .95, rnd)
img = img.resize((W // S, H // S), Image.LANCZOS)
# 透明边缘的颜色往外扩一点，免得缩小时出现黑边
rgb = img.convert('RGB').filter(ImageFilter.MaxFilter(5))
base = Image.merge('RGBA', (*rgb.split(), img.getchannel('A')))
base.paste(img, (0, 0), img)
base.save(os.path.join(OUT, 'flower_atlas.png'), optimize=True)
print('atlas', round(os.path.getsize(os.path.join(OUT, 'flower_atlas.png')) / 1e6, 2), 'MB', 'band', BAND / S)
