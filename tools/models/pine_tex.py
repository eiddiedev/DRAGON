#!/usr/bin/env python3
"""松树贴图：四棵不同的树排一行，带透明。用法：pine_tex.py <输出 png>"""
import math
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

S = 2
TW, TH = 384 * S, 768 * S
W, H = TW * 4, TH
img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
rnd = random.Random(9)


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def needles(x, y, ang, length, col, width):
    """一根下垂的枝：主枝加一排针叶。"""
    steps = 7
    px, py = x, y
    for i in range(steps):
        t = (i + 1) / steps
        nx = x + math.cos(ang) * length * t
        ny = y + math.sin(ang) * length * t + length * .28 * t * t
        d.line((px, py, nx, ny), fill=shade(col, .55) + (255,), width=max(2, int(width * (1 - t * .6))))
        for s in (-1, 1):
            for _ in range(5):
                a2 = ang + s * rnd.uniform(.5, 1.1) + .35
                l2 = length * rnd.uniform(.12, .24) * (1.1 - t * .6)
                c = shade(col, rnd.uniform(.72, 1.22) * (.8 + t * .35))
                d.line((nx, ny, nx + math.cos(a2) * l2, ny + math.sin(a2) * l2), fill=c + (255,), width=max(1, int(width * .55)))
        px, py = nx, ny


PAL = [(30, 56, 40), (26, 50, 44), (36, 62, 38), (34, 52, 46)]
for k in range(4):
    cx0 = TW * k + TW / 2
    base = TH - 6
    top = TH * .02
    col = PAL[k]
    # 树干
    tw = TW * .018
    d.polygon([(cx0 - tw, base), (cx0 + tw, base), (cx0 + 2, top + 40), (cx0 - 2, top + 40)], fill=(44, 34, 28, 255))
    h = base - top
    tiers = 34
    # 从下往上画，靠外的枝先画暗的
    for i in range(tiers):
        t = i / (tiers - 1)
        y = base - h * (.1 + .9 * t)
        spread = TW * .48 * (1 - t) ** .86 + TW * .02
        spread *= rnd.uniform(.82, 1.08)
        # 内层暗色枝叶，让树冠不透
        for _ in range(int(14 + spread / 30)):
            ox = rnd.uniform(-spread * .72, spread * .72)
            ry = rnd.uniform(4, 11) * S
            rx = rnd.uniform(8, 20) * S
            yy = y + rnd.uniform(-10, 16) * S + abs(ox) * .22
            d.ellipse((cx0 + ox - rx, yy - ry, cx0 + ox + rx, yy + ry), fill=shade(col, rnd.uniform(.42, .62)) + (255,))
        for side in (-1, 1):
            for _ in range(5):
                length = spread * rnd.uniform(.62, 1.0)
                ang = math.radians(rnd.uniform(0, 26)) if side > 0 else math.pi - math.radians(rnd.uniform(0, 26))
                needles(cx0 + rnd.uniform(-2, 2), y + rnd.uniform(-8, 8) * S, ang, length, shade(col, .78 + t * .4), 3.2 * S)
        # 正面的短枝填中间
        for _ in range(4):
            length = spread * rnd.uniform(.2, .55)
            ang = rnd.choice((0, math.pi)) + rnd.uniform(-.2, .2)
            needles(cx0 + rnd.uniform(-spread * .3, spread * .3), y + rnd.uniform(-4, 14) * S, ang, length, shade(col, .95 + t * .35), 2.6 * S)
img = img.resize((W // S, H // S), Image.LANCZOS)
rgb = img.convert('RGB').filter(ImageFilter.MaxFilter(5))
b = Image.merge('RGBA', (*rgb.split(), img.getchannel('A')))
b.paste(img, (0, 0), img)
b.save(sys.argv[1], optimize=True)
b2 = Image.new('RGB', b.size, (120, 150, 190))
b2.paste(b, (0, 0), b.getchannel('A'))
b2.resize((1024, 512)).save(sys.argv[1].replace('.png', '_preview.jpg'), quality=85)
print('size', b.size)
