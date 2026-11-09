#!/usr/bin/env python3
"""树冠贴图：一大团金白色小叶，边缘散开，带透明。用法：leaf_tex.py <输出目录>"""
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter

S = 2048
rnd = random.Random(3)
img = Image.new('RGBA', (S, S), (255, 240, 170, 0))
d = ImageDraw.Draw(img)
COLS = [(255, 214, 110), (255, 232, 150), (255, 244, 196), (255, 251, 232), (248, 196, 92)]
for i in range(2600):
    a = rnd.uniform(0, math.tau)
    q = abs(rnd.gauss(0, .46)) * S / 2
    if q > S * .47:
        continue
    x, y = S / 2 + math.cos(a) * q, S / 2 + math.sin(a) * q
    # 外圈的叶子小而暗，中间亮
    k = 1 - q / (S * .5)
    L = rnd.uniform(26, 60) * (.65 + k * .7)
    ang = rnd.uniform(0, math.tau)
    pts = []
    for t in (0, .35, 1, .65):
        pass
    ca, sa = math.cos(ang), math.sin(ang)
    w = L * rnd.uniform(.3, .46)
    pts = [(x - ca * L, y - sa * L), (x - sa * w, y + ca * w), (x + ca * L, y + sa * L), (x + sa * w, y - ca * w)]
    c = COLS[min(len(COLS) - 1, int(rnd.uniform(0, 3) + k * 2.2))]
    d.polygon(pts, fill=c + (255,))
glow = img.filter(ImageFilter.GaussianBlur(24))
a = glow.getchannel('A').point(lambda v: int(v * .62))
glow.putalpha(a)
glow.alpha_composite(img)
glow.save(os.path.join(sys.argv[1], 'leaf_atlas.png'), optimize=True)
print('leaf atlas', round(os.path.getsize(os.path.join(sys.argv[1], 'leaf_atlas.png')) / 1e6, 2), 'MB')
