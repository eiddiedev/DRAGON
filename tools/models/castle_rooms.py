#!/usr/bin/env python3
"""城堡内部：每个房间都有明确用途，留出空地给你以后摆东西。
大厅（王座）/ 西翼书库 / 东翼宴会厅 / 西南塔军械库 / 东南塔厨房 / 后殿下层龙巢圣所 / 后殿上层寝殿 / 北廊和大楼梯。
坐标和 gothic.py 相同：原点山顶中心（世界 127,176），+X 东 +Y 北，Z 绝对海拔。
用法：castle_rooms.py <输出目录>"""
import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbw import Geo, write_glb

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
T = 72.0
rnd = random.Random(44)
ROWS = [
    [(0, '#2a2c35'), (1, '#6b6e7c')],  # 0 深色石
    [(0, '#8e8878'), (1, '#efe7d6')],  # 1 浅色石
    [(0, '#1e120b'), (1, '#4c2f1c')],  # 2 深木
    [(0, '#4a2c16'), (1, '#a06a35')],  # 3 暖木
    [(0, '#4a0e16'), (1, '#b12a30')],  # 4 深红布
    [(0, '#8a6420'), (.6, '#d9a83e'), (1, '#ffe48f')],  # 5 金
    [(0, '#16161c'), (1, '#55565f')],  # 6 铁
    [(0, '#6e2a26'), (.2, '#2a4a70'), (.4, '#2f5d3a'), (.6, '#7a5a26'), (.8, '#54306e'), (1, '#8a7a5e')],  # 7 书脊
    [(0, '#b9a97f'), (1, '#f4ecd2')],  # 8 羊皮纸
    [(0, '#121a3e'), (1, '#2c3f8f')],  # 9 靛蓝布
    [(0, '#5e6a78'), (1, '#c8d6e4')],  # 10 钢
    [(0, '#3d2616'), (1, '#c98a4a')],  # 11 食物
]
GL_ROWS = [
    [(0, '#ff8a2a'), (.6, '#ffc35a'), (1, '#fff2c0')],  # 0 火
    [(0, '#8fdcff'), (1, '#f0fbff')],  # 1 冰蓝（龙蛋）
    [(0, '#7a4fd6'), (.3, '#3c6ee0'), (.55, '#e0507a'), (.8, '#f2c14e'), (1, '#6fd6e8')],  # 2 彩窗
]
g = Geo(ROWS)
gl = Geo(GL_ROWS)


def B(cx, cy, cz, sx, sy, sz, row, tone=.5, rot=0.0, geo=None, taper=1.0):
    """轴对齐（可绕 Z 转）的盒子，cx,cy,cz 是中心，s 是半尺寸。"""
    c, s = math.cos(rot), math.sin(rot)
    (geo or g).box((cx, cy, cz), (sx * c, sx * s, 0), (-sy * s, sy * c, 0), (0, 0, sz), tone, row, taper=taper)


def C(cx, cy, z0, z1, r0, r1, row, tone=.5, seg=8, geo=None, cap=True):
    """竖直圆柱/圆锥。"""
    rings = [[np.array([cx + math.cos(i / seg * math.tau) * r, cy + math.sin(i / seg * math.tau) * r, z]) for i in range(seg)] for r, z in ((r0, z0), (r1, z1))]
    (geo or g).loft(rings, tone, row, [np.array([cx, cy, z0]), np.array([cx, cy, z1])], cap=cap, tone_fn=lambda i, k: tone + .12 * math.sin(k / seg * math.tau * 2 + .7))


def bar(a, b, r, row, tone=.5, seg=5, geo=None):
    """任意方向的杆。"""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    s = np.cross(d, (.3, .2, 1))
    s /= np.linalg.norm(s)
    u = np.cross(d, s)
    u /= np.linalg.norm(u)
    rings = [[p + (s * math.cos(q) + u * math.sin(q)) * r for q in np.linspace(0, math.tau, seg, endpoint=False)] for p in (a, b)]
    (geo or g).loft(rings, tone, row, [a, b])


def flame(x, y, z, h=.34, r=.1):
    gl.cone((x, y, z), (x, y, z + h), r, seg=5, tone=.3, row=0, tip_tone=.98)


def candle(x, y, z, h=.22):
    C(x, y, z, z + h, .035, .03, 8, .9, 5)
    flame(x, y, z + h, .13, .03)


def torch(x, y, z, nx, ny):
    """墙上的火把：铁托 + 木柄 + 火焰。nx,ny 是离墙方向。"""
    bar((x, y, z), (x + nx * .28, y + ny * .28, z + .12), .025, 6, .5)
    bar((x + nx * .28, y + ny * .28, z - .3), (x + nx * .28, y + ny * .28, z + .28), .045, 3, .3)
    C(x + nx * .28, y + ny * .28, z + .22, z + .34, .05, .09, 6, .5, 6, cap=True)
    flame(x + nx * .28, y + ny * .28, z + .3, .3, .06)
    flame(x + nx * .28 + .03, y + ny * .28 - .02, z + .3, .2, .045)
    flame(x + nx * .28 - .03, y + ny * .28 + .02, z + .3, .22, .045)


def stained(x, y, z, w, h, nx, ny):
    """室内看到的彩窗：铁框加一格格彩色玻璃。nx,ny 指向室内。"""
    ux, uy = -ny, nx
    cols, rows_ = max(2, int(w / .32)), max(3, int(h / .42))
    for r in range(rows_):
        for c in range(cols):
            u0, u1 = (c / cols - .5) * w, ((c + 1) / cols - .5) * w
            v0, v1 = r / rows_ * h, (r + 1) / rows_ * h
            # 尖拱：顶部收窄
            def wid(v):
                k = (v - h * .68) / (h * .32)
                return 1.0 if k <= 0 else max(0.0, 1 - k * k * k * .98 - k * .02)
            a = np.array([x + ux * u0 * wid(v0), y + uy * u0 * wid(v0), z + v0])
            b = np.array([x + ux * u1 * wid(v0), y + uy * u1 * wid(v0), z + v0])
            c_ = np.array([x + ux * u1 * wid(v1), y + uy * u1 * wid(v1), z + v1])
            d = np.array([x + ux * u0 * wid(v1), y + uy * u0 * wid(v1), z + v1])
            n = np.array([nx, ny, 0.0])
            gl.tri(a, b, c_, rnd.random(), 2, normals=[n] * 3)
            gl.tri(a, c_, d, rnd.random(), 2, normals=[n] * 3)
    # 窗框和竖棂
    for s in (-1, 1):
        B(x + ux * s * w * .52, y + uy * s * w * .52, z + h * .36, max(.05, abs(ux) * .05 + abs(nx) * .06), max(.05, abs(uy) * .05 + abs(ny) * .06), h * .36, 1, .6)
    B(x, y, z - .05, abs(ux) * w * .58 + abs(nx) * .1, abs(uy) * w * .58 + abs(ny) * .1, .07, 1, .7)


def banner(x, y, z, w, h, nx, ny, row=9, emblem=True):
    """垂挂的旗帜，金边，中央是展翼西方龙纹（原创几何）。"""
    ux, uy = -ny, nx
    n = np.array([nx, ny, 0.0])
    ox, oy = x + nx * .06, y + ny * .06

    def P(u, v, d=0.0):
        return np.array([ox + ux * u + nx * d, oy + uy * u + ny * d, z - v])

    segs = 6
    for i in range(segs):
        v0, v1 = i / segs * h, (i + 1) / segs * h
        w0, w1 = w * (1 if i < segs - 1 else 1), w * (1 if i < segs - 1 else .1)
        b0, b1 = .04 * math.sin(i * 1.3), .04 * math.sin((i + 1) * 1.3)
        g.tri(P(-w0, v0, b0), P(w0, v0, b0), P(w1, v1, b1), .55 + .1 * (i % 2), row, normals=[n] * 3)
        g.tri(P(-w0, v0, b0), P(w1, v1, b1), P(-w1, v1, b1), .55 + .1 * (i % 2), row, normals=[n] * 3)
        g.tri(P(-w0 - .03, v0, b0 + .01), P(-w0 + .05, v0, b0 + .01), P(-w1 + .05, v1, b1 + .01), .75, 5, normals=[n] * 3)
        g.tri(P(w0 + .03, v0, b0 + .01), P(w1 + .03, v1, b1 + .01), P(w1 - .05, v1, b1 + .01), .75, 5, normals=[n] * 3)
    bar((ox + ux * -w * 1.15, oy + uy * -w * 1.15, z + .02), (ox + ux * w * 1.15, oy + uy * w * 1.15, z + .02), .035, 5, .7)
    if emblem:
        v0 = h * .42
        for s in (-1, 1):  # 一对展开的翼 + 身体
            g.tri(P(0, v0, .03), P(s * w * .78, v0 - h * .18, .03), P(s * w * .45, v0 + h * .1, .03), .85, 5, normals=[n] * 3)
            g.tri(P(s * w * .45, v0 + h * .1, .03), P(s * w * .78, v0 - h * .18, .03), P(s * w * .62, v0 + h * .08, .03), .7, 5, normals=[n] * 3)
        g.tri(P(-w * .09, v0 - h * .1, .035), P(w * .09, v0 - h * .1, .035), P(0, v0 + h * .24, .035), .9, 5, normals=[n] * 3)
        g.tri(P(-w * .06, v0 - h * .1, .035), P(w * .06, v0 - h * .1, .035), P(w * .04, v0 - h * .22, .035), .9, 5, normals=[n] * 3)


def planks(x0, x1, y0, y1, z, along='y', w=.42):
    """木地板。"""
    if along == 'y':
        n = int((x1 - x0) / w)
        for i in range(n):
            xa = x0 + i * (x1 - x0) / n
            xb = xa + (x1 - x0) / n * .97
            t = rnd.uniform(.35, .85)
            g.quad((xa, y0, z), (xb, y0, z), (xb, y1, z), (xa, y1, z), t, 3, (0, 0, z - 5))
    else:
        n = int((y1 - y0) / w)
        for i in range(n):
            ya = y0 + i * (y1 - y0) / n
            yb = ya + (y1 - y0) / n * .97
            t = rnd.uniform(.35, .85)
            g.quad((x0, ya, z), (x1, ya, z), (x1, yb, z), (x0, yb, z), t, 3, (0, 0, z - 5))


def tiles(x0, x1, y0, y1, z, s=1.2):
    for i in range(int((x1 - x0) / s)):
        for j in range(int((y1 - y0) / s)):
            xa, ya = x0 + i * s, y0 + j * s
            dark = (i + j) % 2
            t = rnd.uniform(.3, .55) if dark else rnd.uniform(.6, .85)
            g.quad((xa + .012, ya + .012, z), (xa + s - .012, ya + .012, z), (xa + s - .012, ya + s - .012, z), (xa + .012, ya + s - .012, z), t, 0 if dark else 1, (0, 0, z - 5))


def beams(x0, x1, y0, y1, z, along='x', n=5):
    for i in range(n):
        if along == 'x':
            B((x0 + x1) / 2, y0 + (i + .5) * (y1 - y0) / n, z, (x1 - x0) / 2, .14, .17, 2, .6)
        else:
            B(x0 + (i + .5) * (x1 - x0) / n, (y0 + y1) / 2, z, .14, (y1 - y0) / 2, .17, 2, .6)


def bookshelf(x, y, z, width, height, nx, ny, shelves=6):
    """书架：背板、隔板、一本本立着的书（真实几何）。nx,ny 指向室内。"""
    ux, uy = -ny, nx
    depth = .3
    bx, by = x + nx * depth / 2, y + ny * depth / 2
    sxx = abs(ux) * width / 2 + abs(nx) * depth / 2
    syy = abs(uy) * width / 2 + abs(ny) * depth / 2
    # 背板
    B(x + nx * .02, y + ny * .02, z + height / 2, abs(ux) * width / 2 + abs(nx) * .02, abs(uy) * width / 2 + abs(ny) * .02, height / 2, 2, .35)
    for i in range(shelves + 1):
        zz = z + i * height / shelves
        B(bx, by, zz, sxx, syy, .03, 2, .6)
    for s in (-1, 1):
        B(bx + ux * s * width / 2, by + uy * s * width / 2, z + height / 2, abs(ux) * .04 + abs(nx) * depth / 2, abs(uy) * .04 + abs(ny) * depth / 2, height / 2, 2, .6)
    for i in range(shelves):
        zz = z + i * height / shelves + .03
        sh = height / shelves - .1
        u = -width / 2 + .06
        while u < width / 2 - .1:
            w_ = rnd.uniform(.035, .075)
            if rnd.random() < .06:
                u += rnd.uniform(.08, .2)
                continue
            h_ = sh * rnd.uniform(.62, .96)
            tone = rnd.random()
            d_ = depth * rnd.uniform(.72, .94)
            B(x + ux * (u + w_) + nx * (d_ / 2 + .04), y + uy * (u + w_) + ny * (d_ / 2 + .04), zz + h_ / 2, abs(ux) * w_ + abs(nx) * d_ / 2, abs(uy) * w_ + abs(ny) * d_ / 2, h_ / 2, 7, tone)
            u += w_ * 2 + .006


def chair(x, y, z, rot, row=3, high=False):
    c, s = math.cos(rot), math.sin(rot)

    def P(a, b):
        return x + c * a - s * b, y + s * a + c * b
    B(x, y, z + .45, .23, .23, .03, row, .7, rot)
    for a, b in ((-.2, -.2), (.2, -.2), (-.2, .2), (.2, .2)):
        px, py = P(a, b)
        C(px, py, z, z + .44, .025, .022, row, .45, 5)
    # 靠背
    bh = 1.3 if high else .95
    for a in (-.2, .2):
        px, py = P(a, -.21)
        C(px, py, z + .45, z + bh, .025, .02, row, .5, 5)
    px, py = P(0, -.21)
    B(px, py, z + (.5 + bh) / 2 + .2, .19, .02, (bh - .5) / 2 - .05, 4, .6, rot)


def table(x, y, z, sx, sy, h=.78):
    B(x, y, z + h, sx, sy, .045, 3, .7)
    for a in (-1, 1):
        for b in (-1, 1):
            C(x + a * (sx - .12), y + b * (sy - .12), z, z + h, .05, .04, 3, .4, 6)
    B(x, y, z + .2, .04, sy - .2, .03, 3, .4) if sy > sx else B(x, y, z + .2, sx - .2, .04, .03, 3, .4)


def barrel(x, y, z, r=.3, h=.8):
    rings = []
    for t, k in ((0, .84), (.25, .97), (.5, 1.0), (.75, .97), (1, .84)):
        rings.append([np.array([x + math.cos(i / 10 * math.tau) * r * k, y + math.sin(i / 10 * math.tau) * r * k, z + h * t]) for i in range(10)])
    g.loft(rings, .55, 3, [np.array([x, y, z + h * t]) for t in (0, .25, .5, .75, 1)], tone_fn=lambda i, k: .42 + .3 * (k % 2))
    for t in (.14, .86):
        C(x, y, z + h * t - .025, z + h * t + .025, r * .98 * (.9 if t < .5 or t > .5 else 1), r * .98 * .9, 6, .5, 10)


def fireplace(x, y, z, width, nx, ny, height=1.9):
    """壁炉。nx,ny 指向室内。"""
    ux, uy = -ny, nx
    d = .62
    cx, cy = x + nx * d / 2, y + ny * d / 2
    for s in (-1, 1):
        B(cx + ux * s * width / 2, cy + uy * s * width / 2, z + height * .4, abs(ux) * .17 + abs(nx) * d / 2, abs(uy) * .17 + abs(ny) * d / 2, height * .4, 1, .55)
    B(cx, cy, z + height * .86, abs(ux) * (width / 2 + .32) + abs(nx) * (d / 2 + .08), abs(uy) * (width / 2 + .32) + abs(ny) * (d / 2 + .08), .1, 1, .8)
    # 烟罩
    B(x + nx * d * .3, y + ny * d * .3, z + height + .75, abs(ux) * width * .42 + abs(nx) * d * .3, abs(uy) * width * .42 + abs(ny) * d * .3, .75, 1, .45, taper=.72)
    B(x + nx * .03, y + ny * .03, z + height * .4, abs(ux) * width / 2 + abs(nx) * .03, abs(uy) * width / 2 + abs(ny) * .03, height * .4, 0, .15)
    # 柴和火
    for k in range(4):
        a = cx + ux * (k - 1.5) * width * .16
        b = cy + uy * (k - 1.5) * width * .16
        bar((a - nx * .15, b - ny * .15, z + .1), (a + nx * .15, b + ny * .15, z + .1 + (k % 2) * .08), .05, 2, .4)
    for k in range(5):
        a = cx + ux * (k - 2) * width * .13
        b = cy + uy * (k - 2) * width * .13
        flame(a, b, z + .14, rnd.uniform(.4, .75), rnd.uniform(.07, .12))


def chandelier(x, y, z, r=1.6, n=10, chain_to=None):
    """铁环吊灯：铁链 + 环 + 蜡烛。"""
    rings = []
    for q in (0, 1):
        rings.append([np.array([x + math.cos(i / 16 * math.tau) * (r - .04 + .08 * q), y + math.sin(i / 16 * math.tau) * (r - .04 + .08 * q), z]) for i in range(16)])
    for i in range(16):
        a, b = rings[0][i], rings[0][(i + 1) % 16]
        c_, d = rings[1][i], rings[1][(i + 1) % 16]
        g.quad(a + (0, 0, .05), b + (0, 0, .05), d + (0, 0, .05), c_ + (0, 0, .05), .5, 6, (x, y, z - 3))
        g.quad(c_ + (0, 0, .05), d + (0, 0, .05), d - (0, 0, .05), c_ - (0, 0, .05), .4, 6, (x, y, z))
    for i in range(4):
        a = i / 4 * math.tau + .4
        bar((x + math.cos(a) * r, y + math.sin(a) * r, z), (x, y, z + r * .9), .018, 6, .5, 4)
    bar((x, y, z + r * .9), (x, y, chain_to or z + 6), .022, 6, .4, 4)
    for i in range(n):
        a = i / n * math.tau
        px, py = x + math.cos(a) * r, y + math.sin(a) * r
        C(px, py, z + .04, z + .08, .06, .03, 6, .6, 5, cap=True)
        candle(px, py, z + .08)


# ==================== 大厅
tiles(-6.1, 6.1, -7.1, 13.9, T + .22)
# 红毯：从大门到王座
for y0_ in np.arange(-7.5, 8.8, .9):
    g.quad((-1.25, y0_, T + .24), (1.25, y0_, T + .24), (1.25, y0_ + .9, T + .24), (-1.25, y0_ + .9, T + .24), .6 + .06 * math.sin(y0_), 4, (0, 0, T - 5))
    for s in (-1, 1):
        g.quad((s * 1.25, y0_, T + .245), (s * 1.12, y0_, T + .245), (s * 1.12, y0_ + .9, T + .245), (s * 1.25, y0_ + .9, T + .245), .7, 5, (0, 0, T - 5))
# 大门：两扇敞开的厚木门
for s in (-1, 1):
    a = math.radians(78)
    px, py = s * 1.9, -7.2
    c, sn = math.cos(a), math.sin(a)
    for i in range(5):
        k = (i + .5) / 5 * 1.9
        B(px - s * k * c, py + k * sn, T + 2.65, .19, .05, 2.4, 2, .4 + .2 * (i % 2), rot=s * -a)
    for z_ in (1.0, 2.6, 4.2):
        B(px - s * .95 * c, py + .95 * sn, T + z_, .95, .06, .05, 6, .4, rot=s * -a)
# 王座高台：三级
for i, (w, d, h) in enumerate(((4.2, 3.6, .22), (3.4, 2.9, .44), (2.6, 2.2, .66))):
    B(0, 10.0, T + .22 + h / 2, w, d / 2 + (2 - i) * .05, h / 2, 0, .35 + i * .08)
    g.quad((-w, 10.0 - d / 2 - .1, T + .22 + h + .004), (w, 10.0 - d / 2 - .1, T + .22 + h + .004), (w, 10.0 - d / 2 - .02, T + .22 + h + .004), (-w, 10.0 - d / 2 - .02, T + .22 + h + .004), .7, 5, (0, 10, T - 5))
TZ = T + .88
# 王座：高背石椅，两侧张开的翼形
B(0, 10.25, TZ + .3, .55, .5, .3, 1, .45)  # 座基
B(0, 10.15, TZ + .66, .5, .46, .06, 4, .7)  # 坐垫
B(0, 10.7, TZ + 1.55, .52, .1, .95, 1, .5, taper=.7)
B(0, 10.72, TZ + 1.5, .34, .07, .7, 4, .65)
for s in (-1, 1):
    B(s * .6, 10.15, TZ + .78, .08, .45, .08, 5, .75)
    C(s * .6, 9.72, TZ + .3, TZ + .78, .07, .06, 1, .55, 6)
    # 翼形靠背
    P = [np.array([s * .5, 10.7, TZ + 2.0]), np.array([s * 2.1, 10.82, TZ + 3.5]), np.array([s * 1.65, 10.82, TZ + 1.9]), np.array([s * 1.25, 10.82, TZ + 1.1]), np.array([s * .55, 10.76, TZ + .85])]
    for a, b in zip(P[1:], P[2:]):
        g.tri(P[0], a, b, .62, 1, ref=(0, 12, TZ + 1))
        g.tri(P[0], b, a, .4, 1, ref=(0, 8, TZ + 1))
    bar(P[0], P[1], .07, 5, .75)
    bar(P[1], P[2], .045, 5, .7)
    bar(P[1], P[3], .045, 5, .7)
    bar(P[1], P[4], .045, 5, .7)
    # 高台两侧的火盆
    C(s * 2.9, 8.2, T + .22, T + 1.05, .1, .08, 6, .5, 8)
    C(s * 2.9, 8.2, T + 1.05, T + 1.32, .12, .36, 6, .5, 10)
    for k in range(4):
        flame(s * 2.9 + (k - 1.5) * .12, 8.2 + (k % 2 - .5) * .12, T + 1.25, rnd.uniform(.38, .62), .08)
# 两排柱间的旗帜和墙上的火把（窗在高处）
for s in (-1, 1):
    for y_, row, zz in ((-5.2, 9, 5.4), (-1.4, 4, 5.4), (.6, 9, 5.4), (9.6, 4, 6.8)):
        banner(s * 6.14, y_, T + zz, .55, 3.4, -s, 0, row)
    for y_ in (-5.6, -2.6, -.3, 6.4):
        torch(s * 6.18, y_, T + 2.7, -s, 0)
for y_, zz in ((-3.0, T + 8.6), (5.0, T + 8.6)):
    chandelier(0, y_, zz, 1.9, 12, T + 16.8)
# 大楼梯：东西两翼沿墙向北上到北廊（T+4.2）
STAIR_Y0, STAIR_Y1, GZ = 4.9, 12.2, T + 4.2
N_ST = 17
for s in (-1, 1):
    for i in range(N_ST):
        k0, k1 = i / N_ST, (i + 1) / N_ST
        y0_, y1_ = STAIR_Y0 + (STAIR_Y1 - STAIR_Y0) * k0, STAIR_Y0 + (STAIR_Y1 - STAIR_Y0) * k1
        top = T + .22 + (GZ - T - .22) * k1
        B(s * 5.47, (y0_ + y1_) / 2, (T + .22 + top) / 2, .73, (y1_ - y0_) / 2 + .01, (top - T - .22) / 2, 1, .5 + .06 * (i % 2))
        g.quad((s * 4.74, y0_, top + .005), (s * 6.2, y0_, top + .005), (s * 6.2, y1_, top + .005), (s * 4.74, y1_, top + .005), .6, 4, (s * 5.5, y0_, top - 3))
    # 栏杆
    for i in range(0, N_ST + 1, 2):
        k = i / N_ST
        y_ = STAIR_Y0 + (STAIR_Y1 - STAIR_Y0) * k
        zz = T + .22 + (GZ - T - .22) * k
        C(s * 4.76, y_, zz, zz + 1.0, .035, .03, 6, .45, 6)
    bar((s * 4.76, STAIR_Y0, T + 1.22), (s * 4.76, STAIR_Y1, GZ + 1.0), .04, 5, .75)
    # 楼梯起点的龙头柱
    C(s * 4.76, STAIR_Y0, T + .22, T + 1.5, .11, .09, 1, .6, 8)
    C(s * 4.76, STAIR_Y0, T + 1.5, T + 1.75, .13, .02, 5, .7, 8)
# 北廊：连接两段楼梯，通往寝殿
B(0, 13.05, GZ - .11, 6.2, .9, .11, 2, .5)
planks(-6.2, 6.2, 12.2, 13.9, GZ + .01, 'x', .36)
for x_ in np.arange(-3.6, 3.61, .6):
    C(x_, 12.22, GZ, GZ + 1.0, .03, .026, 6, .45, 5)
bar((-4.7, 12.22, GZ + 1.0), (4.7, 12.22, GZ + 1.0), .04, 5, .75)
for x_ in (-4.0, 4.0):
    C(x_, 12.3, T + .22, GZ - .2, .16, .14, 1, .6, 8)
# ==================== 西翼书库（X -13..-7, Y -1..7）
FZ = T + .22
planks(-13.0, -6.95, -.6, 6.6, FZ, 'y')
beams(-13.0, -7.0, -.6, 6.6, T + 8.75, 'x', 5)
g.quad((-13.1, -.7, T + 8.9), (-6.9, -.7, T + 8.9), (-6.9, 6.7, T + 8.9), (-13.1, 6.7, T + 8.9), .25, 2, (-10, 3, T + 12))
bookshelf(-12.95, -.45 + 3.55, FZ, 7.0, 5.2, 1, 0, 8) if False else None
# 南北墙和西墙的书架
bookshelf(-12.9, 1.0, FZ, 2.6, 5.4, 1, 0, 9)   # 西墙南段
bookshelf(-12.9, 5.2, FZ, 2.6, 5.4, 1, 0, 9)   # 西墙北段
for x_ in (-11.5, -9.0):
    bookshelf(x_, -.55, FZ, 2.4, 5.4, 0, 1, 9)
    bookshelf(x_, 6.55, FZ, 2.4, 5.4, 0, -1, 9)
stained(-13.0, 3.1, FZ + 1.4, 1.2, 4.2, 1, 0)
# 二层走道的木栏（装饰）和爬梯
B(-11.9, 3.1, FZ + .3, .6, .9, .02, 4, .6)
bar((-12.5, -.1, FZ), (-12.3, .3, FZ + 3.2), .03, 3, .5)
bar((-12.0, -.1, FZ), (-11.8, .3, FZ + 3.2), .03, 3, .5)
for k in range(9):
    t = k / 9
    bar((-12.5 + .2 * t, -.1 + .4 * t, FZ + 3.2 * t), (-12.0 + .2 * t, -.1 + .4 * t, FZ + 3.2 * t), .018, 3, .55, 4)
# 中央阅览桌：摊开的书、蜡烛、墨水瓶、卷轴
table(-10, 3.1, FZ, .55, 1.3)
for s in (-1, 1):
    g.tri((-10 + s * .02, 2.75, FZ + .84), (-10 + s * .24, 2.72, FZ + .85), (-10 + s * .24, 3.0, FZ + .85), .9, 8, ref=(-10, 2.8, FZ))
    g.tri((-10 + s * .02, 2.75, FZ + .84), (-10 + s * .24, 3.0, FZ + .85), (-10 + s * .02, 3.03, FZ + .84), .85, 8, ref=(-10, 2.8, FZ))
candle(-10.3, 3.6, FZ + .83)
candle(-9.72, 2.35, FZ + .83)
C(-9.78, 3.55, FZ + .83, FZ + .93, .04, .035, 6, .35, 6)
for k in range(3):
    bar((-10.35 + k * .1, 3.92, FZ + .86), (-10.1 + k * .12, 4.1, FZ + .86), .03, 8, .75)
for s in (-1, 1):
    chair(-10 + s * .92, 3.1, FZ, -s * math.pi / 2 + math.pi, 3)
# 地球仪
C(-8.0, 5.3, FZ, FZ + .9, .1, .05, 3, .5, 6)
g.loft([[np.array([-8.0 + math.cos(i / 10 * math.tau) * .36 * math.sin(a), 5.3 + math.sin(i / 10 * math.tau) * .36 * math.sin(a), FZ + 1.25 + .36 * math.cos(a)]) for i in range(10)] for a in np.linspace(.08, 3.06, 7)], .6, 3, [np.array([-8.0, 5.3, FZ + 1.25 + .36 * math.cos(a)]) for a in np.linspace(.08, 3.06, 7)], tone_fn=lambda i, k: rnd.uniform(.3, .9), cap=False)
torch(-12.92, 3.1 - 1.4, FZ + 2.4, 1, 0)
torch(-12.92, 3.1 + 1.4, FZ + 2.4, 1, 0)
banner(-7.06, 5.3, FZ + 4.9, .4, 2.6, -1, 0, 4, True) if False else None
# ==================== 东翼宴会厅（X 7..13, Y -1..7）
planks(6.95, 13.0, -.6, 6.6, FZ, 'x')
beams(7, 13, -.6, 6.6, T + 8.75, 'y', 5)
g.quad((6.9, -.7, T + 8.9), (13.1, -.7, T + 8.9), (13.1, 6.7, T + 8.9), (6.9, 6.7, T + 8.9), .25, 2, (10, 3, T + 12))
table(9.6, 3.0, FZ, .62, 2.6)
# 桌旗和餐具：一人一份
g.quad((9.25, .55, FZ + .83), (9.95, .55, FZ + .83), (9.95, 5.45, FZ + .83), (9.25, 5.45, FZ + .83), .55, 4, (9.6, 3, FZ))
for y_ in (1.0, 2.0, 3.0, 4.0, 5.0):
    for s in (-1, 1):
        chair(9.6 + s * 1.0, y_, FZ, -s * math.pi / 2 + math.pi, 3)
        C(9.6 + s * .4, y_, FZ + .825, FZ + .85, .1, .13, 10, .85, 10)   # 盘子
        C(9.6 + s * .28, y_ + .22, FZ + .825, FZ + .84, .03, .02, 5, .7, 6)    # 高脚杯
        C(9.6 + s * .28, y_ + .22, FZ + .84, FZ + .95, .012, .012, 5, .7, 5, cap=False)
        C(9.6 + s * .28, y_ + .22, FZ + .95, FZ + 1.02, .02, .036, 5, .75, 6)
chair(9.6, .0 - .05, FZ, 0, 3, True)
chair(9.6, 6.05, FZ, math.pi, 3, True)
# 大烤肉盘、面包篮、水果
C(9.6, 3.0, FZ + .825, FZ + .86, .22, .3, 5, .7, 10)
g.loft([[np.array([9.6 + math.cos(i / 8 * math.tau) * .2 * math.sin(a) * (1 + .4 * abs(math.cos(i / 8 * math.tau))), 3.0 + math.sin(i / 8 * math.tau) * .17 * math.sin(a), FZ + .95 + .14 * math.cos(a)]) for i in range(8)] for a in np.linspace(.2, 2.9, 5)], .6, 11, [np.array([9.6, 3.0, FZ + .95 + .14 * math.cos(a)]) for a in np.linspace(.2, 2.9, 5)], cap=True)
for y_ in (1.5, 4.5):
    C(9.6, y_, FZ + .825, FZ + .92, .1, .16, 3, .7, 8)
    for k in range(5):
        a = k / 5 * math.tau
        C(9.6 + math.cos(a) * .08, y_ + math.sin(a) * .08, FZ + .88, FZ + .96, .05, .03, 11, .75, 6)
for y_ in (2.0, 4.0):
    C(9.6, y_, FZ + .825, FZ + 1.15, .05, .02, 5, .7, 6)
    for s in (-1, 0, 1):
        candle(9.6 + s * .13, y_, FZ + 1.14 - abs(s) * .08)
fireplace(12.92, 3.0, FZ, 1.9, -1, 0)
for y_ in (.0, 6.0):
    banner(12.96, y_, FZ + 4.8, .48, 3.0, -1, 0, 4)
    torch(12.96, y_ + (1 if y_ < 1 else -1) * .0, FZ + 2.3, -1, 0)
for x_, y_ in ((7.6, -.2), (8.3, -.25)):
    barrel(x_, y_, FZ)
barrel(7.9, -.2, FZ + .82, .26, .6)
stained(13.0, 1.0, FZ + 3.0, .9, 3.2, -1, 0)
stained(13.0, 5.0, FZ + 3.0, .9, 3.2, -1, 0)
# ==================== 西南塔：军械库（X -12..-7, Y -10.5..-5.5）
AX, AY = -9.5, -8.0
planks(-11.5, -7.05, -10.0, -6.0, FZ, 'y', .34)
g.quad((-11.6, -10.1, T + 4.3), (-7.0, -10.1, T + 4.3), (-7.0, -5.9, T + 4.3), (-11.6, -5.9, T + 4.3), .3, 2, (AX, AY, T + 8))
beams(-11.5, -7.05, -10.0, -6.0, T + 4.1, 'x', 3)
# 北墙：武器架，一排长剑
B(AX, -6.08, FZ + 2.2, 2.0, .04, .05, 2, .6)
B(AX, -6.08, FZ + .9, 2.0, .04, .05, 2, .6)
for k in range(7):
    x_ = AX - 1.6 + k * .53
    bar((x_, -6.14, FZ + .6), (x_, -6.14, FZ + 2.05), .022, 10, .8, 4)     # 剑身
    B(x_, -6.14, FZ + 2.08, .12, .025, .025, 5, .7)      # 护手
    C(x_, -6.14, FZ + 2.1, FZ + 2.32, .016, .016, 2, .6, 5)
    C(x_, -6.14, FZ + 2.32, FZ + 2.37, .03, .012, 5, .75, 5)
# 南墙：圆盾和十字交叉之外的斧头（避开十字图案，用翼形纹）
for k, x_ in enumerate((-11.0, -9.5, -8.0)):
    rows_ = [[np.array([x_ + math.cos(i / 12 * math.tau) * r, -9.96 + d, FZ + 2.2 + math.sin(i / 12 * math.tau) * r]) for i in range(12)] for r, d in ((.48, 0), (.42, .05), (.12, .08))]
    g.loft(rows_, .55, 9 if k != 1 else 4, [np.array([x_, -9.96 + d, FZ + 2.2]) for d in (0, .05, .08)], cap=True)
    C(x_, -9.86, FZ + 2.16, FZ + 2.24, .1, .06, 5, .8, 8)
    for s in (-1, 1):
        g.tri((x_, -9.87, FZ + 2.2), (x_ + s * .32, -9.87, FZ + 2.42), (x_ + s * .3, -9.87, FZ + 2.12), .8, 5, ref=(x_, -11, FZ + 2))
# 西墙：长矛架
B(-11.42, AY, FZ + 1.6, .05, 1.6, .04, 2, .6)
B(-11.3, AY, FZ + .3, .05, 1.6, .04, 2, .6)
for k in range(7):
    y_ = AY - 1.4 + k * .46
    bar((-11.32, y_, FZ + .1), (-11.46, y_, FZ + 2.9), .02, 3, .6, 4)
    bar((-11.46, y_, FZ + 2.9), (-11.47, y_, FZ + 3.3), .03, 10, .8, 4)
# 盔甲架两副
for x_, y_ in ((-8.1, -7.0), (-8.1, -9.0)):
    C(x_, y_, FZ, FZ + .05, .28, .28, 2, .5, 8)
    C(x_, y_, FZ + .05, FZ + 1.0, .03, .03, 2, .5, 5, cap=False)
    rings = [[np.array([x_ + math.cos(i / 10 * math.tau) * r * 1.1, y_ + math.sin(i / 10 * math.tau) * r * .72, z_]) for i in range(10)] for r, z_ in ((.2, FZ + .95), (.25, FZ + 1.2), (.31, FZ + 1.5), (.26, FZ + 1.65), (.1, FZ + 1.72))]
    g.loft(rings, .68, 10, [np.array([x_, y_, z_]) for z_ in (FZ + .95, FZ + 1.2, FZ + 1.5, FZ + 1.65, FZ + 1.72)])
    for s in (-1, 1):
        g.loft([[np.array([x_ + s * .36 + math.cos(i / 8 * math.tau) * .13, y_ + math.sin(i / 8 * math.tau) * .13, FZ + 1.6 + math.sin(a) * .13]) for i in range(8)] for a in (-1.2, 0, 1.2)], .74, 10, [np.array([x_ + s * .36, y_, FZ + 1.6 + math.sin(a) * .13]) for a in (-1.2, 0, 1.2)])
    rings = [[np.array([x_ + math.cos(i / 10 * math.tau) * r, y_ + math.sin(i / 10 * math.tau) * r, z_]) for i in range(10)] for r, z_ in ((.13, FZ + 1.74), (.15, FZ + 1.9), (.14, FZ + 2.02), (.05, FZ + 2.14))]
    g.loft(rings, .7, 10, [np.array([x_, y_, z_]) for z_ in (FZ + 1.74, FZ + 1.9, FZ + 2.02, FZ + 2.14)])
    C(x_, y_, FZ + 2.14, FZ + 2.3, .025, .01, 4, .7, 5)
# 铁砧、木箱
B(-10.3, -9.3, FZ + .25, .22, .14, .25, 6, .4)
B(-10.3, -9.3, FZ + .58, .34, .16, .08, 6, .55)
B(-10.9, -6.75, FZ + .28, .32, .26, .28, 3, .5)
torch(-7.08, -9.4, FZ + 2.5, -1, 0)
# ==================== 东南塔：厨房（X 7..11.6, Y -10.3..-5.7）
planks(7.05, 11.15, -9.9, -6.1, FZ, 'x', .32)
g.quad((7.0, -10.0, T + 4.3), (11.2, -10.0, T + 4.3), (11.2, -6.0, T + 4.3), (7.0, -6.0, T + 4.3), .3, 2, (9.3, -8, T + 8))
beams(7.05, 11.15, -9.9, -6.1, T + 4.1, 'y', 3)
# 灶台（南墙）+ 铁锅
fireplace(9.3, -9.95, FZ, 2.3, 0, 1)
bar((8.6, -9.5, FZ + 1.5), (10.0, -9.5, FZ + 1.5), .03, 6, .5)
rings = [[np.array([9.3 + math.cos(i / 12 * math.tau) * r, -9.5 + math.sin(i / 12 * math.tau) * r, z_]) for i in range(12)] for r, z_ in ((.2, FZ + .55), (.38, FZ + .72), (.42, FZ + .95), (.36, FZ + 1.08))]
g.loft(rings, .3, 6, [np.array([9.3, -9.5, z_]) for z_ in (FZ + .55, FZ + .72, FZ + .95, FZ + 1.08)])
bar((9.3, -9.5, FZ + 1.5), (9.3, -9.5, FZ + 1.08), .012, 6, .5, 4)
# 中央操作台：砧板、面包、蔬菜、菜刀
table(9.3, -7.6, FZ, 1.05, .45, .85)
B(8.9, -7.6, FZ + .91, .3, .2, .02, 3, .8)
for k in range(4):
    x_ = 9.4 + k * .17
    rg = [[np.array([x_ + math.cos(i / 8 * math.tau) * .13 * math.sin(a), -7.55 + (k % 2) * .08 + math.sin(i / 8 * math.tau) * .07 * math.sin(a), FZ + .95 + .06 * math.cos(a)]) for i in range(8)] for a in np.linspace(.2, 2.9, 4)]
    g.loft(rg, .7, 11, [np.array([x_, -7.55, FZ + .95 + .06 * math.cos(a)]) for a in np.linspace(.2, 2.9, 4)])
B(8.85, -7.55, FZ + .935, .14, .025, .006, 10, .85)
B(8.68, -7.55, FZ + .935, .05, .02, .012, 2, .5)
# 挂着的锅和香肠
B(9.3, -7.6, T + 3.3, 1.2, .03, .03, 6, .4)
for k in range(5):
    x_ = 8.5 + k * .4
    bar((x_, -7.6, T + 3.3), (x_, -7.6, T + 3.0), .01, 6, .4, 4)
    rg = [[np.array([x_ + math.cos(i / 10 * math.tau) * r, -7.6 + math.sin(i / 10 * math.tau) * r, T + 3.0 - d]) for i in range(10)] for r, d in ((.16, 0), (.15, .1), (.08, .14))]
    g.loft(rg, .4, 6, [np.array([x_, -7.6, T + 3.0 - d]) for d in (0, .1, .14)])
# 储物：桶、麻袋、架子上的陶罐
barrel(10.9, -6.5, FZ)
barrel(10.3, -6.4, FZ, .27, .7)
barrel(7.6, -6.45, FZ, .3, .8)
for k, (x_, y_) in enumerate(((10.9, -9.4), (10.5, -9.55), (10.85, -8.95))):
    rg = [[np.array([x_ + math.cos(i / 8 * math.tau) * r, y_ + math.sin(i / 8 * math.tau) * r, FZ + z_]) for i in range(8)] for r, z_ in ((.2, 0), (.26, .2), (.2, .48), (.05, .58))]
    g.loft(rg, .6, 8, [np.array([x_, y_, FZ + z_]) for z_ in (0, .2, .48, .58)])
B(7.15, -8.3, FZ + 1.6, .12, 1.0, .025, 2, .6)
B(7.15, -8.3, FZ + 2.2, .12, 1.0, .025, 2, .6)
for z_ in (1.62, 2.22):
    for k in range(5):
        y_ = -9 + k * .35
        rg = [[np.array([7.15 + math.cos(i / 8 * math.tau) * r, y_ + math.sin(i / 8 * math.tau) * r, FZ + z_ + d]) for i in range(8)] for r, d in ((.07, 0), (.1, .1), (.05, .22))]
        g.loft(rg, rnd.uniform(.3, .8), 3, [np.array([7.15, y_, FZ + z_ + d]) for d in (0, .1, .22)])
torch(7.08, -9.5, FZ + 2.5, 1, 0)
# ==================== 后殿下层：龙巢圣所（圆心 0,14，半径 6）
def apse_floor(z, row, rad=6.2, n=14):
    for i in range(n):
        a0, a1 = i / n * math.pi, (i + 1) / n * math.pi
        for r0, r1, t in ((0, rad * .34, .75), (rad * .34, rad * .4, .95), (rad * .4, rad * .72, .45), (rad * .72, rad, .6)):
            g.quad((math.cos(a0) * r0, 14 + math.sin(a0) * r0, z), (math.cos(a0) * r1, 14 + math.sin(a0) * r1, z), (math.cos(a1) * r1, 14 + math.sin(a1) * r1, z), (math.cos(a1) * r0, 14 + math.sin(a1) * r0, z), t + .05 * (i % 2), row, (0, 14, z - 5))


apse_floor(FZ, 1)
SZ = FZ
# 中央基座：三层，放一枚发光的巨大龙蛋
for r_, h_ in ((1.8, .25), (1.25, .5), (.8, 1.0)):
    C(0, 17.2, SZ, SZ + h_, r_, r_ * .96, 0, .5, 12)
rings = []
for t, r_ in ((0, .1), (.15, .4), (.4, .56), (.65, .5), (.85, .34), (1, .06)):
    rings.append([np.array([math.cos(i / 16 * math.tau) * r_, 17.2 + math.sin(i / 16 * math.tau) * r_, SZ + 1.0 + t * 1.5]) for i in range(16)])
gl.loft(rings, .5, 1, [np.array([0, 17.2, SZ + 1.0 + t * 1.5]) for t in (0, .15, .4, .65, .85, 1)], tone_fn=lambda i, k: .25 + rnd.random() * .7)
# 四角火盆 + 环形烛台
for a in (.5, 1.2, 1.94, 2.64):
    x_, y_ = math.cos(a) * 4.9, 14 + math.sin(a) * 4.9
    C(x_, y_, SZ, SZ + .95, .09, .07, 6, .5, 8)
    C(x_, y_, SZ + .95, SZ + 1.2, .1, .3, 6, .5, 10)
    for k in range(3):
        flame(x_ + (k - 1) * .1, y_, SZ + 1.15, rnd.uniform(.32, .5), .07)
for a in np.linspace(.15, math.pi - .15, 5):
    stained(math.cos(a) * 6.05, 14 + math.sin(a) * 6.05, SZ + 1.0, .9, 3.0, -math.cos(a), -math.sin(a))
# 圣所顶（寝殿地板）
for i in range(14):
    a0, a1 = i / 14 * math.pi, (i + 1) / 14 * math.pi
    for z_, row_, t_, ref_ in ((GZ - .15, 2, .4, GZ + 3), (GZ + .01, 3, .6, GZ - 3)):
        g.quad((0, 14, z_), (math.cos(a0) * 6.3, 14 + math.sin(a0) * 6.3, z_), (math.cos(a1) * 6.3, 14 + math.sin(a1) * 6.3, z_), (0, 14, z_), t_ + .06 * (i % 2), row_, (0, 14, ref_))
# ==================== 后殿上层：寝殿
BZ = GZ + .01
# 圆毯
for i in range(16):
    a0, a1 = i / 16 * math.tau, (i + 1) / 16 * math.tau
    for r0, r1, row_, t in ((0, 1.9, 4, .6), (1.9, 2.15, 5, .7)):
        g.quad((math.cos(a0) * r0, 16.6 + math.sin(a0) * r0, BZ + .012), (math.cos(a0) * r1, 16.6 + math.sin(a0) * r1, BZ + .012), (math.cos(a1) * r1, 16.6 + math.sin(a1) * r1, BZ + .012), (math.cos(a1) * r0, 16.6 + math.sin(a1) * r0, BZ + .012), t, row_, (0, 16.6, BZ - 3))
# 四柱床：床头靠后殿弧墙
BX, BY = 0.0, 18.2
B(BX, BY, BZ + .3, 1.15, 1.25, .3, 2, .55)
B(BX, BY, BZ + .68, 1.1, 1.2, .1, 8, .85)
B(BX, BY - .25, BZ + .76, 1.14, .98, .05, 4, .62)
for s in (-.55, .55):
    B(BX + s, BY + .9, BZ + .86, .42, .2, .1, 8, .95)
for sx in (-1, 1):
    for sy in (-1, 1):
        C(BX + sx * 1.15, BY + sy * 1.25, BZ, BZ + 3.1, .07, .06, 2, .55, 8)
        C(BX + sx * 1.15, BY + sy * 1.25, BZ + 3.1, BZ + 3.3, .08, .02, 5, .7, 6)
B(BX, BY, BZ + 3.1, 1.2, 1.3, .05, 9, .6)
for sx in (-1, 1):
    B(BX + sx * 1.2, BY + .3, BZ + 2.0, .025, .95, 1.05, 4, .55)
B(BX, BY + 1.27, BZ + 1.5, 1.1, .05, .9, 2, .55)
# 衣柜、梳妆台、箱子、壁炉
B(-4.2, 17.0, BZ + 1.15, .7, .35, 1.15, 2, .55, rot=-.7)
B(-4.17, 16.68, BZ + 1.15, .03, .03, .95, 5, .7, rot=-.7)
table(4.1, 16.8, BZ, .7, .3, .78)
B(4.1, 16.9, BZ + 1.4, .4, .02, .55, 10, .95)
chair(4.0, 16.2, BZ, 0, 3)
candle(3.65, 16.75, BZ + .82)
candle(4.55, 16.75, BZ + .82)
B(2.6, 19.1, BZ + .3, .55, .3, .3, 3, .55, rot=-.35)
B(2.6, 19.1, BZ + .63, .57, .32, .05, 5, .65, rot=-.35)
fireplace(-3.0, 19.3, BZ, 1.6, .5, -.86) if False else None
for a in np.linspace(.3, math.pi - .3, 4):
    stained(math.cos(a) * 6.05, 14 + math.sin(a) * 6.05, BZ + 1.6, 1.0, 5.0, -math.cos(a), -math.sin(a))
for a in (.75, 2.39):
    torch(math.cos(a) * 6.05, 14 + math.sin(a) * 6.05, BZ + 2.4, -math.cos(a), -math.sin(a))
# ==================== 大厅高窗的内侧（让室内看得到窗）
for s in (-1, 1):
    for y_ in (-7.0, -3.5, 7.5, 11.5):
        stained(s * 6.17, y_, T + 7.6, 1.4, 6.2, -s, 0)
stained(0, 13.93, GZ + 1.4, 0.1, 0.1, 0, -1) if False else None
g_t = write_glb(os.path.join(OUT, 'castle_rooms.glb'), g, name='castle_rooms', rough=.8)
gl_t = write_glb(os.path.join(OUT, 'castle_rooms_glow.glb'), gl, name='castle_rooms_glow', rough=.5, emissive=(1, 1, 1))
print('rooms tris', g_t, 'glow', gl_t, round(os.path.getsize(os.path.join(OUT, 'castle_rooms.glb')) / 1e6, 2), 'MB')
