# 用法：Blender --background --python props.py -- <输出目录>
# 灯塔、码头、帆船、石桥、上城堡的高架坡道、风车、竞技场、出生点道具、羊。
# 除帆船、羊外都按世界坐标减去各自原点建模。原点写在 ORIGINS，摆放脚本从 placements.json 读取。
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
from kit import C, Euler, Mesh, Vector, finish, preview_setup, rnd, shot, srgb

outdir = sys.argv[sys.argv.index('--') + 1]
ROOT = os.path.abspath(os.path.join(outdir, '..'))
H = np.load(os.path.join(ROOT, 'terrain', 'world', 'base_heights.npy'))
SEA = 27.0
C.update({k: srgb(v) for k, v in dict(cs='#E8E0CF', cs2='#CFC6B4', cs3='#F4EEE0', slate='#6A86B8', white='#F6F1E6', red='#E05A44', red2='#C64632',
                                      sail='#FBF3DF', hull='#9A5C33', hull2='#7B4527', wool='#FAF5E8', dragon='#3AA39A', dragon2='#2B8A84', dragon3='#79CDBE').items()})
placements = []


def smooth(pts, sub):
    """Catmull-Rom 插值，把折线变圆滑。"""
    P_ = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = map(np.array, (P_[i - 1], P_[i], P_[i + 1], P_[i + 2]))
        for k in range(sub):
            t = k / sub
            out.append(tuple(.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (3 * p1 - p0 - 3 * p2 + p3) * t ** 3)))
    out.append(tuple(pts[-1]))
    return out


def G(x, y):
    x = min(max(x, 0), 255.99)
    y = min(max(y, 0), 255.99)
    x0, y0 = int(x), int(y)
    fx, fy = x - x0, y - y0
    return float(H[y0, x0] * (1 - fx) * (1 - fy) + H[y0, x0 + 1] * fx * (1 - fy) + H[y0 + 1, x0] * (1 - fx) * fy + H[y0 + 1, x0 + 1] * fx * fy)


def done(name, P, G_, origin, size=1024, cam=None, tgt=None):
    main = P.to_object('main')
    finish([main], G_, name, outdir, tex_size=size)
    placements.append(dict(name=name, x=origin[0], y=origin[2], z=origin[1]))
    c = preview_setup()
    d = cam or (20, -30, 14)
    shot(c, os.path.join(outdir, name + '.png'), d, tgt or (0, 0, 5), 38, (760, 560))


def lighthouse():
    kit.reset()
    P, Gl = Mesh(), Mesh()
    sub = H[120:146, 198:226]
    lz, lx = np.unravel_index(sub.argmax(), sub.shape)
    lx, ly = int(lx) + 198, int(lz) + 120
    gy = float(H[ly, lx])
    for k in range(26):
        a = rnd.uniform(0, math.tau)
        r = rnd.uniform(3.4, 5.0)
        s = rnd.uniform(1, 2.0)
        P.rbox((s, s, s * .8), (math.cos(a) * r, math.sin(a) * r, rnd.uniform(-1, 1)), C[rnd.choice(('stone', 'stone2', 'stone3'))], (0, 0, a), jitter=.03)
    P.lathe([(4.6, -2), (4.4, 1.6), (3.3, 2.1)], C['stone3'], 24)
    prof = [(3.3, 2.0), (2.9, 8), (2.45, 14), (2.25, 19)]
    # 红白相间的塔身
    bands = [(2, 7, 'white'), (7, 11, 'red'), (11, 15, 'white'), (15, 19, 'red')]
    rz = lambda z: float(np.interp(z, [p[1] for p in prof], [p[0] for p in prof]))
    for a_, b_, c_ in bands:
        P.lathe([(rz(a_) + .02, a_), (rz((a_ + b_) / 2) + .04, (a_ + b_) / 2), (rz(b_) + .02, b_)], C[c_], 24)
    P.lathe([(2.3, 19), (3.4, 19.5), (3.5, 20), (.02, 20)], C['iron'], 24)
    for i in range(14):
        a = i / 14 * math.tau
        P.rbox((.14, .14, 1.0), (math.cos(a) * 3.25, math.sin(a) * 3.25, 20.5), C['iron'])
    P.lathe([(3.2, 21), (3.3, 21.08), (3.2, 21.16)], C['iron'], 24)
    Gl.cyl(1.7, 1.7, 3.2, (0, 0, 21.6), 'glass', 16)
    for i in range(6):
        a = i / 6 * math.tau
        P.rbox((.2, .2, 3.3), (math.cos(a) * 1.72, math.sin(a) * 1.72, 21.6), C['red2'])
    P.lathe([(2.4, 23.1), (1.1, 24.6), (.05, 25.8)], C['red'], 20)
    P.sphere(.34, (0, 0, 26), C['gold'], 10)
    for i, z in enumerate((6, 12, 17)):
        a = -math.pi / 2 + (.5 if i % 2 else -.5)
        r = rz(z) + .02
        Gl.rbox((.75, .1, 1.3), (math.cos(a) * r, math.sin(a) * r, z), 'glass', (0, 0, a + math.pi / 2), cuts=0)
    P.rbox((1.5, .2, 2.5), (0, -3.15, 3.35), C['hull2'])
    done('lighthouse', P, Gl, (lx, ly, gy), cam=(16, -30, 14), tgt=(0, 0, 12))


def piers():
    kit.reset()
    P, Gl = Mesh(), Mesh()
    # 第一条码头的世界位置由海岸线决定，两条都从岸上伸进海里
    ox, oy = 0.0, 0.0
    coast = {}
    for pz in (90, 76):
        coast[pz] = next(x for x in range(140, 256) if H[pz, x] < SEA - .2)
    origin = (coast[90], 83.0, SEA)
    for pz in (90, 76):
        cx = coast[pz] - origin[0]
        y = pz - origin[1]
        x0, x1 = cx - 7, cx + 22
        for i in range(int((x1 - x0) / .85)):
            x = x0 + i * .85
            P.rbox((.8, 4.6 + rnd.uniform(-.1, .1), .22), (x, y + rnd.uniform(-.03, .03), 1.75), C[rnd.choice(('wood2', 'wood', 'floor'))], cuts=0)
        for sy in (-1, 1):
            P.rbox((x1 - x0, .3, .3), ((x0 + x1) / 2, y + sy * 2.1, 1.55), C['wood3'])
            for x in np.arange(cx + 2, x1, 5.5):
                P.cyl(.22, .26, 6.5, (float(x), y + sy * 2.2, -.9), C['wood3'], 8)
                P.lathe([(.25, 1.55), (.3, 1.75), (.25, 1.95)], C['iron'], 8, center=(float(x), y + sy * 2.2))
        # 箱子、木桶、吊灯
        P.rbox((1.1, 1.1, 1.1), (x1 - 3, y - 1.2, 2.45), C['wood2'])
        P.rbox((.9, .9, .8), (x1 - 3, y - 1.2, 3.4), C['wood'])
        for dx in (0, 1.1):
            P.lathe([(.42, 1.86), (.52, 2.4), (.42, 2.95), (.02, 2.95)], C['hull'], 10, center=(x1 - 6 + dx, y + 1.3))
        P.rbox((.2, .2, 3.6), (x1 - .8, y + 1.9, 3.5), C['wood3'])
        P.rbox((.9, .14, .14), (x1 - 1.2, y + 1.9, 5.2), C['wood3'])
        Gl.sphere(.3, (x1 - 1.6, y + 1.9, 4.75), 'glass', 8)
    done('piers', P, Gl, origin, cam=(26, -26, 12), tgt=(8, 0, 2))


def sailboat():
    kit.reset()
    P, Gl = Mesh(), Mesh()
    # 船头朝 +Y。船身：一层层收窄的木板
    L, W_ = 16.0, 5.4
    rows = 5
    for k in range(rows):
        z = -.6 + k * .62
        w = W_ * (.62 + .1 * k)
        l = L * (.8 + .05 * k)
        for i in range(10):
            t0 = (i + .5) / 10 * 2 - 1
            y = t0 * l / 2
            ww = w * math.sqrt(max(.04, 1 - max(0, t0) ** 2.2 * .95)) * (1 - max(0, -t0) * .12)
            P.rbox((ww, l / 10 * 1.04, .6), (0, y, z), C['hull' if k % 2 else 'hull2'], cuts=1)
    P.rbox((W_ * .86, L * .84, .24), (0, -.3, 2.0), C['floor'], cuts=0)
    P.rbox((W_ * .92, 3.4, 1.7), (0, -L * .36, 2.9), C['hull'])
    P.rbox((W_ * .98, 3.7, .3), (0, -L * .36, 3.85), C['gold'])
    Gl.rbox((1.0, .1, .7), (0, -L * .36 - 1.75, 2.95), 'glass', cuts=0)
    for y, h, sw in ((2.2, 14.0, 7.6), (-2.6, 11.5, 6.0)):
        P.cyl(.24, .14, h, (0, y, 2 + h / 2), C['wood3'], 8)
        for i, frac in enumerate((.42, .72)):
            z = 2 + h * frac
            s = sw * (1 - i * .22)
            P.rbox((s, .2, .2), (0, y, z + h * .13), C['wood3'], cuts=1)
            for k in range(6):
                t = (k + .5) / 6 * 2 - 1
                bulge = (1 - t * t) * .7
                P.rbox((s / 6 * 1.04, .16, h * .25), (t * s / 2, y + bulge, z), C['sail' if k % 2 else 'cloth2'], cuts=0)
        P.rbox((1.5, .06, .7), (.8, y, 2 + h + .3), C['banner' if 'banner' in C else 'cloth'], cuts=0)
    P.rbox((.5, 4.4, .3), (0, L * .47, 1.9), C['wood3'], (math.radians(22), 0, 0))
    done('sailboat', P, Gl, (0, 0, 0), cam=(26, -22, 12), tgt=(0, 0, 6))
    placements.pop()


def bridge():
    kit.reset()
    P, Gl = Mesh(), Mesh()
    bx, a, b = 162.0, 96.0, 125.0
    ya, yb = G(bx, a), G(bx, b)
    ox, oy, oz = bx, (a + b) / 2, 0.0
    mid = max(ya, yb) + 2.6
    n = 22
    deck = []
    for i in range(n + 1):
        t = i / n
        y = a + (b - a) * t
        lin = ya + (yb - ya) * t
        arch = (mid - (ya + yb) / 2) * (1 - (2 * t - 1) ** 2)
        deck.append((y - oy, lin + arch))
    for (y0, z0), (y1, z1) in zip(deck, deck[1:]):
        l = math.hypot(y1 - y0, z1 - z0)
        pitch = math.atan2(z1 - z0, y1 - y0)
        P.rbox((6.4, l + .1, .7), (0, (y0 + y1) / 2, (z0 + z1) / 2 - .32), C['stone3'], (pitch, 0, 0), cuts=0)
        for sx in (-1, 1):
            P.rbox((.62, l * .88, .95), (sx * 3.05, (y0 + y1) / 2, (z0 + z1) / 2 + .45), C[rnd.choice(('stone', 'stone3'))], (pitch, 0, 0))
    # 两个石拱墩
    for py in (104.0, 117.0):
        h0 = G(bx, py) - 3
        z = np.interp(py - oy, [d[0] for d in deck], [d[1] for d in deck])
        P.rbox((6.8, 3.4, z - h0), (0, py - oy, (z + h0) / 2 - .4), C['stone'], cuts=0)
        P.lathe([(3.4, h0 + 2), (3.6, z - 1.2)], C['stone2'], 4, center=(0, py - oy)) if False else None
    done('bridge', P, Gl, (ox, oy, oz), cam=(42, -18, 50), tgt=(0, 0, 40))


def causeway():
    kit.reset()
    P, Gl = Mesh(), Mesh()
    xa, xb, y = 200.0, 153.2, 165.0
    za, zb = G(xa, y) - .1, 58.3
    ox, oy = (xa + xb) / 2, y
    L = xa - xb
    n = 28
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        x0, x1 = xa + (xb - xa) * t0, xa + (xb - xa) * t1
        z0, z1 = za + (zb - za) * t0, za + (zb - za) * t1
        pitch = math.atan2(z1 - z0, x0 - x1)
        P.rbox((abs(x1 - x0) + .08, 8.0, .8), ((x0 + x1) / 2 - ox, 0, (z0 + z1) / 2 - .4), C['cs2'], (0, pitch, 0), cuts=0)
        for sy in (-1, 1):
            P.rbox((abs(x1 - x0) * .9, .6, .9), ((x0 + x1) / 2 - ox, sy * 3.9, (z0 + z1) / 2 + .42), C[rnd.choice(('cs', 'cs3'))], (0, pitch, 0))
        P.rbox((abs(x1 - x0) * .8, 7.0, .05), ((x0 + x1) / 2 - ox, 0, (z0 + z1) / 2 + .03), C['trim' if False else 'cs3'], (0, pitch, 0), cuts=0)
    # 拱形桥墩
    for t in (.28, .48, .68, .86):
        x = xa + (xb - xa) * t
        z = za + (zb - za) * t
        g = G(x, y) - 2
        if z - g < 2:
            continue
        P.rbox((2.4, 8.4, z - g), (x - ox, 0, (z + g) / 2 - .5), C['cs'], cuts=0)
        P.rbox((3.2, 8.8, .8), (x - ox, 0, z - 1.2), C['cs3'])
    for t in (.1, .55, .98):
        x = xa + (xb - xa) * t
        z = za + (zb - za) * t
        for sy in (-1, 1):
            P.rbox((.5, .5, 3.4), (x - ox, sy * 3.95, z + 1.9), C['iron'])
            Gl.sphere(.34, (x - ox, sy * 3.95, z + 3.8), 'glass', 8)
    done('causeway', P, Gl, (ox, oy, 0.0), size=1024, cam=(10, -48, 60), tgt=(0, 0, 44))


def windmill():
    kit.reset()
    P, Gl = Mesh(), Mesh()
    wx, wy = 84.0, 66.0
    gy = G(wx, wy)
    P.lathe([(4.4, -2), (4.0, 1.4), (3.2, 7), (2.8, 11)], C['plaster'], 22)
    for _ in range(26):
        a = rnd.uniform(0, math.tau)
        z = rnd.uniform(.2, 3)
        r = np.interp(z, [-2, 1.4, 7], [4.4, 4.0, 3.2])
        s = rnd.uniform(.7, 1.3)
        P.rbox((s, .3, s * .55), (math.cos(a) * r, math.sin(a) * r, z), C[rnd.choice(('stone', 'stone2', 'stone3'))], (0, 0, a + math.pi / 2))
    P.lathe([(3.2, 11), (3.4, 11.3), (3.1, 11.5)], C['beam'], 22)
    P.lathe([(3.3, 11.4), (2.3, 13.4), (.05, 15)], C['roof_red'], 18)
    P.rbox((1.3, .25, 2.2), (0, -3.95, 1.3), C['wood2'])
    Gl.rbox((.8, .1, 1.0), (0, -3.06, 6.5), 'glass', cuts=0)
    hub = (0, -3.4, 11.4)
    P.cyl(.45, .45, 1.8, (0, -3.1, 11.4), C['wood3'], 10, (math.pi / 2, 0, 0))
    for i in range(4):
        a = i * math.pi / 2 + .35
        c, s = math.cos(a), math.sin(a)
        P.rbox((9.5, .2, .34), (c * 4.7, -3.95, 11.4 + s * 4.7), C['wood3'], (0, -a, 0))
        for k in range(6):
            r = 2.2 + k * 1.2
            nx, nz = -s, c
            P.rbox((1.1, .09, 1.5), (c * r + nx * .95, -3.92, 11.4 + s * r + nz * .95), C['cloth2' if k % 2 else 'sail'], (0, -a, 0), cuts=0)
    done('windmill', P, Gl, (wx, wy, gy), cam=(14, -30, 12), tgt=(0, 0, 8))


def arena():
    kit.reset()
    P, Gl = Mesh(), Mesh()
    AY = 32.0
    S = 26.0
    P.rbox((S + 1, S + 1, 1), (0, 0, -.5), C['stone2'], cuts=0)
    P.rbox((S + 1, S + 1, .6), (0, 0, 10.2), C['iron'], cuts=0)
    for name, x, y, sx, sy in (('s', 0, -S / 2, S + 1, 1), ('n', 0, S / 2, S + 1, 1), ('w', -S / 2, 0, 1, S + 1), ('e', S / 2, 0, 1, S + 1)):
        P.rbox((sx, sy, 10), (x, y, 5), C['stone'], cuts=0)
    # 擂台（出界线就是它的边）
    P.lathe([(9, 0), (9.1, .25), (9, .5), (.02, .5)], C['stone3'], 40)
    P.lathe([(8.4, .51), (8.5, .54), (8.4, .57), (8.0, .57), (8.0, .52)], C['gold'], 40)
    P.lathe([(2.2, .51), (2.3, .55), (2.0, .57), (.02, .57)], C['gold'], 24)
    # 龙肋骨：一圈白色弯骨架向内弯
    for i in range(12):
        a = i / 12 * math.tau
        px, py = math.cos(a), math.sin(a)
        for k in range(6):
            t = k / 5
            r = 12.0 - t * t * 5.0
            z = t * 8.5
            P.rbox((.8 - t * .4, .8 - t * .4, 2.1), (px * r, py * r, z + .9), C['wool'], (0, 0, a))
        Gl.sphere(.3, (px * 12.4, py * 12.4, 6), 'glass', 6) if i % 3 == 0 else None
    for sx in (-1, 1):
        P.rbox((.9, 5.0, 2.4), (sx * 11.5, 0, 1.2), C['wood'])
        P.rbox((1.1, 5.2, .22), (sx * 11.5, 0, 2.45), C['wood2'])
    # 胜场榜
    P.rbox((10, .3, 4), (0, S / 2 - .6, 6.5), C['wood2'])
    P.rbox((8.8, .32, 3.2), (0, S / 2 - .64, 6.5), C['cloth2'], cuts=0)
    done('arena', P, Gl, (127.0, 172.0, AY), size=1024, cam=(17, -21, 23), tgt=(0, 0, 3))


def arena_gate():
    kit.reset()
    P, Gl = Mesh(), Mesh()
    gx, gy = 125.0, 135.0
    g = G(gx, gy)
    n = 13
    for i in range(n):
        t = i / (n - 1) * math.pi
        rr = 3.6
        P.rbox((1.25, 1.5, .9), (-math.cos(t) * rr, 0, 3.0 + math.sin(t) * rr), C['stone3' if i % 2 else 'stone'], (0, -t + math.pi / 2, 0))
    for sx in (-1, 1):
        for i in range(4):
            P.rbox((1.4, 1.6, .85), (sx * 3.6, 0, .3 + i * .85), C['stone2' if i % 2 else 'stone'])
        P.rbox((.4, .4, 2.0), (sx * 4.8, -.9, 3), C['iron'])
        Gl.sphere(.36, (sx * 4.8, -.9, 4.3), 'glass', 8)
    # 龙骨门饰
    for sx in (-1, 1):
        P.rbox((.6, .6, 3.4), (sx * 1.5, -.3, 7.6), C['wool'], (0, sx * .5, 0))
    P.rbox((6.4, .35, 5.8), (0, .55, 3.0), C['iron'], cuts=0)
    Gl.lathe([(2.6, .08), (2.7, .14), (2.6, .2), (.02, .2)], 'p_blue', 28, center=(0, -3))
    done('arena_gate', P, Gl, (gx, gy, g), size=1024, cam=(9, -18, 7), tgt=(0, 0, 4))


def spawn_props():
    kit.reset()
    P, Gl = Mesh(), Mesh()
    fx, fy = 121.0, 50.0
    gy = G(fx, fy)
    # 魔法画框（站到前面拍照）
    P.rbox((5.0, .9, .5), (0, 0, .25), C['wood'])
    n = 15
    for i in range(n):
        t = i / (n - 1) * math.pi
        P.rbox((1.1, .4, .42), (-math.cos(t) * 2.1, 0, 2.7 + math.sin(t) * 2.1), C['gold'], (0, -t + math.pi / 2, 0))
    for sx in (-1, 1):
        P.rbox((.42, .4, 2.5), (sx * 2.1, 0, 1.6), C['gold'])
    Gl.sphere(.34, (0, 0, 5.1), 'star', 10)
    done('magic_frame', P, Gl, (fx, fy, gy), size=512, cam=(5, -10, 4), tgt=(0, 0, 3))

    kit.reset()
    P, Gl = Mesh(), Mesh()
    fx, fy = 137.0, 45.0
    gy = G(fx, fy)
    for i in range(9):
        a = i / 9 * math.tau
        P.rbox((.55, .5, .36), (math.cos(a) * .95, math.sin(a) * .95, .15), C[rnd.choice(('stone', 'stone2'))], (0, 0, a))
    for i in range(4):
        a = i / 4 * math.pi + .3
        P.rbox((1.5, .2, .2), (0, 0, .3), C['wood3'], (0, .3, a))
    Gl.sphere(.42, (0, 0, .7), 'p_red', 8, (1, 1, 1.5))
    Gl.sphere(.28, (.08, 0, 1.15), 'star', 8, (1, 1, 1.6))
    for dx in (-1.9, 2.0):
        P.rbox((1.5, .4, .4), (dx, -.7, .2), C['wood2'], (0, 0, .4 * dx))
    done('campfire', P, Gl, (fx, fy, gy), size=256, cam=(3, -5, 2.5), tgt=(0, 0, .6))


def sheep():
    kit.reset()
    P, Gl = Mesh(), Mesh()
    for dx, dy, dz, r in ((0, 0, .72, .46), (.3, .25, .78, .3), (-.3, .25, .78, .3), (.32, -.22, .8, .3), (-.3, -.22, .76, .3), (0, .46, .78, .3), (0, -.42, .84, .3), (0, 0, 1.02, .3)):
        P.sphere(r, (dx, dy, dz), C['wool'], 8)
    P.sphere(.22, (0, .72, .92), C['iron'], 8, (.82, 1.15, 1))
    P.sphere(.15, (0, .84, 1.12), C['wool'], 6)
    for sx in (-1, 1):
        P.sphere(.09, (sx * .21, .68, 1.01), C['iron'], 6, (1.6, .6, .6))
        for sy in (-1, 1):
            P.cyl(.07, .06, .42, (sx * .2, sy * .28, .21), C['iron'], 6)
    Gl = None
    main = P.to_object('main')
    finish([main], None, 'sheep', outdir, tex_size=256)
    c = preview_setup()
    shot(c, os.path.join(outdir, 'sheep.png'), (2, -3, 1.4), (0, 0, .6), 40, (500, 400))


def dragon_pose(P, pts, radii, head_dir, wing_span=1.0, teal=('dragon', 'dragon2', 'dragon3'), spikes=True):
    """pts 从尾巴到脖子根。头朝 head_dir。"""
    belly = C[teal[2]]
    P.tube(pts, radii, C[teal[0]], 12, .86, c_fn=lambda i, s: belly if s in (8, 9, 10) else C[teal[0] if (i + s) % 3 else teal[1]])
    if spikes:
        for i in range(2, len(pts) - 1, 1):
            p, q = Vector(pts[i]), Vector(pts[i + 1])
            t = (q - p).normalized()
            P.rbox((radii[i] * .12, radii[i] * .55, radii[i] * .8), tuple(p + Vector((0, 0, radii[i] * 1.06))), C[teal[1]], Euler((0, 0, -math.atan2(t.x, t.y))).to_matrix(), cuts=1, taper=.25)
    return Vector(pts[-1]), Vector(head_dir).normalized()


def head(P, Gl, n, d, s=1.0, teal=('dragon', 'dragon2', 'dragon3')):
    """n 是头根部位置，d 是朝向，s 是缩放。"""
    side = d.cross(Vector((0, 0, 1))).normalized()
    up = side.cross(d).normalized()
    at = lambda a, b, c: tuple(n + d * a * s + side * b * s + up * c * s)
    yaw = -math.atan2(d.x, d.y)
    R = Euler((0, 0, yaw)).to_matrix()
    P.rbox((5.4 * s, 6.5 * s, 3.6 * s), at(3.2, 0, .3), C[teal[0]], R, cuts=2)
    P.rbox((3.6 * s, 5.2 * s, 2.0 * s), at(7.6, 0, .25), C[teal[0]], R, cuts=2)
    P.rbox((3.4 * s, 4.4 * s, .9 * s), at(6.6, 0, -1.25), C[teal[2]], R, cuts=2)  # 下颌
    for sx in (-1, 1):
        P.rbox((.5 * s, .7 * s, 1.5 * s), at(9.6, sx * 1.35, 1.1), C[teal[1]], R, cuts=1, taper=.3)  # 鼻角
        P.sphere(.82 * s, at(3.9, sx * 2.75, 1.5), C['cloth2'], 10)
        Gl.sphere(.5 * s, at(4.45, sx * 3.1, 1.55), 'star', 8)
        P.sphere(.24 * s, at(4.75, sx * 3.45, 1.6), C['iron'], 6)
        # 龙角
        pts = [at(1.5 - k * 1.6, sx * (1.9 + k * .55), 2.0 + k * 1.15) for k in range(5)]
        P.tube(pts, [.72 * s, .56 * s, .42 * s, .28 * s, .08 * s], C['cloth2'], 7)
        # 腮鳍
        P.rbox((.3 * s, 2.0 * s, 2.5 * s), at(.7, sx * 3.0, .6), C[teal[1]], R, cuts=1, taper=.4)
    for x in (6.2, 7.3, 8.4):  # 牙
        for sx in (-1, 1):
            P.rbox((.26 * s, .3 * s, .55 * s), at(x, sx * 1.55, -.6), C['wool'], R, cuts=0, taper=.2)


def wing(P, root, tip_dir, span, chord, teal=('dragon', 'dragon2', 'dragon3')):
    """一片翅膀：翼骨 + 三片翼膜（一面一层的扇形薄片）。"""
    root = Vector(root)
    tip_dir = Vector(tip_dir).normalized()
    el = root + tip_dir * span * .45 + Vector((0, 0, span * .2))
    P.tube([root, el], [chord * .1, chord * .07], C[teal[1]], 8)
    tips = [el + (tip_dir * span * .62 + Vector((0, a, b)) * span) for a, b in ((.15, .35), (-.12, .1), (-.42, -.18), (-.62, -.42))]
    back = root + Vector((0, -chord * .9, -chord * .12))
    for t in tips[:-1]:
        P.tube([el, t], [chord * .055, chord * .02], C[teal[1]], 6)
    P.tube([el, tips[-1]], [chord * .05, chord * .02], C[teal[1]], 6)
    # 翼膜：扇形多边形
    fan = [tips[0], tips[1], tips[2], tips[3], back]
    bm = P.bm
    c0 = bm.verts.new(el)
    fv = [bm.verts.new(v) for v in fan]
    for a, b in zip(fv, fv[1:]):
        f = bm.faces.new((c0, a, b))
        for l in f.loops:
            l[P.col] = C[teal[2]]
    r0 = bm.verts.new(root)
    f = bm.faces.new((c0, fv[-1], r0))
    for l in f.loops:
        l[P.col] = C[teal[2]]


def dragon_big():
    """盘在主峰南面的古龙。"""
    kit.reset()
    P, Gl = Mesh(), Mesh()
    ox, oy = 135.0, 232.0
    gh = lambda x, y: G(x, y)
    B = [(178, 248), (170, 246), (160, 243), (150, 244), (138, 246), (126, 245), (114, 241), (106, 236), (106, 230), (114, 227), (126, 226), (138, 226), (148, 225), (152, 220), (147, 215)]
    pts = []
    for i, (x, y) in enumerate(B):
        z = max(gh(x, y) + 4.5, 100 + i * .6)
        pts.append((x - ox, y - oy, z))
    pts2 = smooth(pts, 4)
    N = len(pts2)
    radii = [1.1 + 6.6 * math.sin(min(1, (i + 1) / N * 1.15) * math.pi * .62) ** .8 for i in range(N)]
    base, _ = dragon_pose(P, pts2, radii, (-.5, -1, 0))
    d = Vector((-.48, -1, -.1)).normalized()
    # 脖子：从身体末端探出来
    n0 = Vector(pts2[-1])
    n1 = n0 + Vector((-3, -7, 2.0))
    n2 = n1 + Vector((-3, -6, 2.2))
    P.tube([tuple(n0), tuple(n1), tuple(n2)], [radii[-1], 3.9, 3.2], C['dragon'], 12, .9)
    head(P, Gl, n2 - d * 1.0, d, 1.25)
    # 翅膀：收在背上微微张开
    rootL = Vector((110 - ox, 240 - oy, 112))
    rootR = Vector((150 - ox, 240 - oy, 112))
    wing(P, rootL, (-1, -.15, .55), 44, 22)
    wing(P, rootR, (1, -.15, .55), 44, 22)
    # 前爪
    for x, y in ((118, 222), (140, 220)):
        z = max(gh(x, y), 92)
        P.tube([(x - ox, y + 4 - oy, z + 10), (x - ox, y - oy, z + 4), (x - ox, y - 3 - oy, z + .5)], [3, 2.1, 1.7], C['dragon2'], 8)
        for k in (-1, 0, 1):
            P.rbox((.8, 2, .9), (x - ox + k * 1.2, y - 5 - oy, z), C['cloth2'], cuts=1, taper=.4)
    main = P.to_object('main')
    finish([main], Gl, 'dragon_big', outdir, tex_size=2048)
    placements.append(dict(name='dragon_big', x=ox, y=0.0, z=oy))
    c = preview_setup()
    shot(c, os.path.join(outdir, 'dragon_big.png'), (10, -95, 118), (0, 0, 112), 40, (1000, 700))


def dragon_mount():
    """骑乘用小龙：趴在底座上，背上有鞍。"""
    kit.reset()
    P, Gl = Mesh(), Mesh()
    P.lathe([(4.3, 0), (4.5, .35), (4.0, .9), (.02, .9)], C['stone3'], 18)
    tail = [(0, -7.5 + i * 1.3, 1.1 + i * .45) for i in range(4)]
    body = tail + [(0, -2.0, 2.9), (0, -.4, 3.2), (0, 1.3, 3.0), (0, 2.8, 3.5), (0, 3.8, 4.7)]
    radii = [.14, .3, .45, .7, 1.25, 1.55, 1.45, 1.0, .7]
    dragon_pose(P, body, radii, (0, 1, .15))
    d = Vector((0, 1, .05)).normalized()
    head(P, Gl, Vector(body[-1]) + Vector((0, -.2, .1)), d, .34)
    for sx in (-1, 1):
        wing(P, (sx * 1.0, -.2, 3.9), (sx, -.1, .6), 9, 4.5)
        for y in (-1.5, 1.4):
            P.tube([(sx * .9, y, 2.4), (sx * 1.3, y + .1, 1.3), (sx * 1.35, y + .4, .95)], [.5, .34, .3], C['dragon2'], 7)
    P.rbox((1.9, 1.9, .34), (0, -.3, 4.72), C['red'])
    P.rbox((2.3, .3, .85), (0, -1.3, 4.95), C['gold'])
    main = P.to_object('main')
    gy = G(145, 46)
    finish([main], Gl, 'dragon_mount', outdir, tex_size=1024)
    placements.append(dict(name='dragon_mount', x=145.0, y=gy, z=46.0))
    c = preview_setup()
    shot(c, os.path.join(outdir, 'dragon_mount.png'), (10, -16, 8), (0, 0, 3.4), 38, (900, 650))


import sys as _s
only = _s.argv[_s.argv.index('--') + 2:]
ALL = dict(lighthouse=lighthouse, piers=piers, sailboat=sailboat, bridge=bridge, causeway=causeway, windmill=windmill, arena=arena, arena_gate=arena_gate, spawn_props=spawn_props, sheep=sheep, dragon_big=dragon_big, dragon_mount=dragon_mount)
for k_, fn in ALL.items():
    if not only or k_ in only:
        fn()
pp = os.path.join(outdir, 'placements.json')
old = json.load(open(pp)) if os.path.exists(pp) else []
names = {q['name'] for q in placements}
json.dump([q for q in old if q['name'] not in names] + placements, open(pp, 'w'), indent=1)
