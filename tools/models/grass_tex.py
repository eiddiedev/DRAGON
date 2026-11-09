#!/usr/bin/env python3
"""草和花的贴图（带透明）。一张图分三条：上面是草，中间是草里夹白花小黄花，下面是紫花。
用法：grass_tex.py <输出目录>
"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
S = 2
W, H = 2048 * S, 1536 * S
BANDS = 3
BH = H // BANDS
GREEN = [(58, 88, 40), (70, 100, 44), (46, 74, 34), (86, 112, 50), (98, 118, 58), (120, 124, 64), (40, 62, 30)]
rnd = random.Random(7)


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def blade(d, x, base, h, w, lean, col, bend=None):
    """一片草叶：根部宽，尖部细，向一侧弯。"""
    n = 8
    bend = bend if bend is not None else rnd.uniform(.15, .55)
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        cx = x + lean * t ** (1.6 + bend)
        cy = base - h * (t - .12 * bend * t * t)
        ww = w * (1 - t) ** .75
        left.append((cx - ww, cy))
        right.append((cx + ww, cy))
    d.polygon(left + right[::-1], fill=col + (255,))
    # 叶脉亮线
    d.line([(x + lean * (i / n) ** (1.6 + bend), base - h * (i / n - .12 * bend * (i / n) ** 2)) for i in range(n)], fill=shade(col, 1.25) + (255,), width=max(1, int(w * .18)))


def grass_band(d, top, count, hscale=1.0):
    base = top + BH - 4 * S
    items = []
    for i in range(count):
        depth = rnd.random()  # 0 后 1 前
        items.append((depth, rnd.uniform(0, W)))
    items.sort()
    for depth, x in items:
        h = rnd.uniform(.5, 1.0) * BH * .92 * hscale * (1 - depth * .25)
        w = rnd.uniform(7, 15) * S
        lean = rnd.uniform(-.34, .34) * h
        k = .50 + depth * .62  # 后排暗，前排亮
        blade(d, x, base, h, w, lean, shade(rnd.choice(GREEN), k))


def flower(d, x, y, r, col, core=(235, 200, 90), n=None):
    n = n or rnd.choice((5, 5, 6))
    a0 = rnd.uniform(0, math.tau)
    tilt = rnd.uniform(.55, .85)
    for i in range(n):
        a = a0 + i / n * math.tau
        px, py = x + math.cos(a) * r * .6, y + math.sin(a) * r * .6 * tilt
        rx, ry = r * .52, r * .4 * (tilt + .25)
        d.ellipse((px - rx, py - ry, px + rx, py + ry), fill=shade(col, rnd.uniform(.88, 1.08)) + (255,))
    cr = r * .24
    d.ellipse((x - cr, y - cr * tilt, x + cr, y + cr * tilt), fill=core + (255,))


def stems_and_flowers(d, top, count, palette, rmin, rmax, hmin=.45, hmax=.95):
    base = top + BH - 4 * S
    fl = []
    for i in range(count):
        depth = rnd.random()
        fl.append((depth, rnd.uniform(0, W)))
    fl.sort()
    for depth, x in fl:
        h = rnd.uniform(hmin, hmax) * BH * .9
        lean = rnd.uniform(-.18, .18) * h
        k = .6 + depth * .5
        g = shade(rnd.choice(GREEN), k)
        d.line([(x, base), (x + lean * .4, base - h * .55), (x + lean, base - h)], fill=g + (255,), width=int(5 * S))
        for _ in range(rnd.randint(1, 2)):
            t = rnd.uniform(.2, .6)
            blade(d, x + lean * t, base - h * t, h * .28, 7 * S, rnd.choice((-1, 1)) * h * .25, g, .4)
        flower(d, x + lean, base - h, rnd.uniform(rmin, rmax) * S, shade(rnd.choice(palette), k))


img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
# 第一条：纯草
grass_band(d, 0, 900)
# 第二条：草里夹小白花小黄花
grass_band(d, BH, 620, .92)
stems_and_flowers(d, BH, 90, [(240, 240, 232), (250, 250, 245), (236, 210, 96), (228, 196, 70)], 13, 21, .55, .98)
# 第三条：紫花海（紫、淡紫、白、一点粉）
grass_band(d, BH * 2, 360, .75)
stems_and_flowers(d, BH * 2, 240, [(124, 79, 201), (154, 95, 214), (181, 123, 228), (205, 160, 236), (232, 222, 250), (214, 120, 196)], 17, 30, .42, .98)
img = img.resize((W // S, H // S), Image.LANCZOS)
# 透明边缘的颜色往外扩，缩小时才不会有黑边
rgb = img.convert('RGB').filter(ImageFilter.MaxFilter(5))
base = Image.merge('RGBA', (*rgb.split(), img.getchannel('A')))
base.paste(img, (0, 0), img)
base.save(os.path.join(OUT, 'grass_atlas.png'), optimize=True)
base.convert('RGB').resize((1024, 768)).save(os.path.join(OUT, 'grass_atlas_preview.jpg'), quality=85)
print('atlas MB', round(os.path.getsize(os.path.join(OUT, 'grass_atlas.png')) / 1e6, 2))
