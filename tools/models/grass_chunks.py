#!/usr/bin/env python3
"""贴地的草：每根草都按真实地形网格的高度种下，按 18 米一块合并。
块原点在中心的拟合平面上，脚本沿平面法线做剪切，让草随风晃而根不离地。
用法：grass_chunks.py <输出目录>"""
import json, math, os, random, sys
import numpy as np
from scipy import ndimage as nd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbw import Geo, write_glb
import terrain_mesh as TM
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
ROOT = '/Users/a1234/Documents/awesomeWRLD/assets'
SITES = json.load(open(f'{ROOT}/terrain/v3/sites.json'))
PATH = json.load(open(f'{ROOT}/terrain/v3/path.json'))
ROAD = [(130, 52), (135, 66), (149, 79), (159, 90), (162, 96), (162, 127), (167, 134), (171, 141)]
N = 512  # 0.5 米一格
xs = (np.arange(N) + .5) / 2
X, Z = np.meshgrid(xs, xs)
Y = TM.height(X, Z)
gy, gx = np.gradient(Y, .5)
slope = np.degrees(np.arctan(np.hypot(gx, gy)))


def line_mask(pts, r):
    m = np.zeros((N, N), bool)
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        L = max(1, int(math.hypot(bx - ax, bz - az) * 3))
        for t in np.linspace(0, 1, L):
            ix, iz = int((ax + (bx - ax) * t) * 2), int((az + (bz - az) * t) * 2)
            if 0 <= ix < N and 0 <= iz < N:
                m[iz, ix] = True
    return nd.distance_transform_edt(~m) * .5 < r if r > 0 else m


pp = [(a, b) for a, b, _ in PATH[::3]]
roads = line_mask(pp, 2.4) | line_mask(ROAD, 2.2)
trails = np.zeros((N, N), bool)
for tr in SITES['trails']:
    trails |= line_mask(tr, 1.6)
near_way = line_mask(pp, 11) | line_mask(ROAD, 13)
for tr in SITES['trails']:
    near_way |= line_mask(tr, 9)
flowers = np.hypot((X - 140) / 1.15, Z - 62) < 37
pasture = (X > 78) & (X < 122) & (Z > 36) & (Z < 92)
spawn = np.hypot(X - 130, Z - 48) < 26
hill = (np.hypot(X - 127, Z - 176) < 44) & (np.hypot(X - 127, Z - 176) > 19)
sites_m = np.zeros((N, N), bool)
sites_core = np.zeros((N, N), bool)
for s in SITES['sites'].values():
    d = np.hypot(X - s['x'], Z - s['z'])
    sites_m |= d < s['r'] + 7
    sites_core |= d < s['r'] * .6
rng = np.random.default_rng(4)
blob = nd.gaussian_filter(rng.normal(size=(N, N)), 10)
blob = (blob - blob.mean()) / blob.std()
want = (flowers | pasture | spawn | hill | sites_m | near_way) & (Y > 29.5) & (Y < 76) & (slope < 42)
want &= ~roads & ~trails & ~sites_core
HOUSES = [(176, 60), (188, 66), (182, 79), (170, 88), (196, 82), (186, 95), (176, 124), (190, 128), (200, 140), (184, 146), (196, 158), (178, 160), (171, 146), (125, 135)]
for hx, hz in HOUSES:
    want &= np.hypot(X - hx, Z - hz) > 5
want &= np.hypot(X - 160.5, Z - 74) > 2.4
want &= np.hypot(X - 121, Z - 57) > 2.5
# 羽化成 0~1 的密度
dens = nd.gaussian_filter(want.astype(float), 3)
dens = np.clip(dens * want * 1.3, 0, 1) * np.clip(.82 + blob * .22, .35, 1)
# 出生镜头压得很低，镜头脚下的草不种，否则会糊在屏幕上
dens *= np.clip((np.hypot(X - 129, Z - 43) - 3.5) / 2.0, 0, 1)
ROWS = [
    [(0, '#123019'), (.4, '#2a6128'), (.75, '#55963c'), (1, '#96c65a')],
    [(0, '#143423'), (.4, '#26633f'), (.75, '#4a955e'), (1, '#8bc884')],
    [(0, '#27371a'), (.4, '#566e27'), (.75, '#8ba042'), (1, '#c4c868')],
    [(0, '#3d2a7a'), (.4, '#6f47c9'), (.75, '#a97ce8'), (1, '#e6d4fb')],
    [(0, '#7a2f8a'), (.5, '#c75cc8'), (1, '#f6c3ec')],
    [(0, '#c79a2a'), (1, '#ffe690')],
    [(0, '#bdbbaa'), (1, '#ffffff')],
]
CH = 18.0
rnd = random.Random(8)
UP = np.array([0, 0, 1.0])
info = []
cells = int(256 // CH)
DENS = 58  # 每平方米草数上限
for cz in range(cells + 1):
    for cx in range(cells + 1):
        x0, z0 = cx * CH, cz * CH
        ix0, iz0 = int(x0 * 2), int(z0 * 2)
        sub = dens[iz0:iz0 + int(CH * 2), ix0:ix0 + int(CH * 2)]
        if sub.size == 0 or sub.mean() < .06:
            continue
        ox, oz = x0 + CH / 2, z0 + CH / 2
        # 拟合平面：y = a x + b z + c
        ss = want[iz0:iz0 + int(CH * 2), ix0:ix0 + int(CH * 2)]
        xx, zz = X[iz0:iz0 + int(CH * 2), ix0:ix0 + int(CH * 2)][ss] - ox, Z[iz0:iz0 + int(CH * 2), ix0:ix0 + int(CH * 2)][ss] - oz
        yy = Y[iz0:iz0 + int(CH * 2), ix0:ix0 + int(CH * 2)][ss]
        A = np.column_stack([xx, zz, np.ones_like(xx)])
        a, b, c = np.linalg.lstsq(A, yy, rcond=None)[0]
        g = Geo(ROWS)
        tris = 0
        tries = int(CH * CH * DENS)
        for _ in range(tries):
            if tris > 29300:
                break
            px, pz = x0 + rnd.random() * CH, z0 + rnd.random() * CH
            i, j = min(int(px * 2), N - 1), min(int(pz * 2), N - 1)
            if rnd.random() > dens[j, i]:
                continue
            py = float(TM.height(np.array(px), np.array(pz))) - .04
            lx, lz, ly = px - ox, pz - oz, py - c
            ang = rnd.uniform(0, math.tau)
            d = np.array([math.cos(ang), math.sin(ang), 0.0])
            base = np.array([lx, lz, ly])
            fl = flowers[j, i]
            if fl and rnd.random() < .05:
                # 花：茎 + 五瓣 + 花心
                h = rnd.uniform(.22, .4)
                top = base + UP * h + d * rnd.uniform(-.05, .05)
                s_ = np.array([-d[1], d[0], 0]) * .012
                g.tri(base - s_, base + s_, top, (.12, .12, .5), 0, normals=[UP] * 3)
                r = rnd.uniform(.05, .085)
                tilt = np.array([rnd.uniform(-.4, .4), rnd.uniform(-.4, .4), 1.0])
                tilt /= np.linalg.norm(tilt)
                u = np.cross(tilt, (1, 0, 0))
                u /= np.linalg.norm(u)
                v = np.cross(tilt, u)
                row = rnd.choice((3, 3, 3, 4))
                for k in range(5):
                    t = ang + k / 5 * math.tau
                    o = u * math.cos(t) + v * math.sin(t)
                    q = v * math.cos(t) - u * math.sin(t)
                    tip = top + o * r + tilt * r * .3
                    g.tri(top + o * r * .15, tip + q * r * .36, tip - q * r * .36, (.42, .86, .86), row, normals=[tilt] * 3)
                g.tri(top + u * r * .2, top + v * r * .2, top - u * r * .2 - v * r * .2, .6, 5, normals=[tilt] * 3)
                tris += 7
            else:
                h = rnd.uniform(.12, .32) * (1.1 if fl else 1.0)
                w = rnd.uniform(.03, .055)
                sd = np.array([-d[1], d[0], 0.0]) * w / 2
                t = base + UP * h + d * h * rnd.uniform(.1, .55)
                n = UP + d * .3
                n = n / np.linalg.norm(n)
                row = rnd.choice((0, 0, 0, 1, 2)) if not fl else rnd.choice((0, 1))
                g.tri(base - sd, base + sd, t, (.08, .08, rnd.uniform(.7, .98)), row, normals=[n] * 3)
                tris += 1
        if tris < 150:
            continue
        nm = f'gc_{len(info)}'
        t_ = write_glb(os.path.join(OUT, nm + '.glb'), g, name=nm, rough=.9)
        nr = np.array([-a, -b, 1.0])
        nr /= np.linalg.norm(nr)
        info.append(dict(name=nm, x=ox, z=oz, y=float(c), nx=float(nr[0]), ny=float(nr[2]), nz=float(nr[1]), tris=t_))
print('chunks', len(info), 'tris', sum(i['tris'] for i in info), 'max', max(i['tris'] for i in info))
json.dump(info, open(os.path.join(OUT, 'chunks.json'), 'w'))
