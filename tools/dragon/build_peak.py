#!/usr/bin/env python3
"""龙站的山岩：山脊上隆起的岩台，一层层岩板，顶上有雪。用法：build_peak.py <输出目录>"""
import json, math, os, random, sys
import numpy as np
sys.path.insert(0, 'tools/models')
from glbw import Geo, write_glb
import terrain_mesh as TM
OUT = sys.argv[1]
OX, OZ = 165.0, 234.0
TOP, RB = 112.0, 40.0
rnd = random.Random(4)


def G(x, z):
    return float(TM.height(np.array(x + OX), np.array(z + OZ)))


def crag(th, r):
    return 1.0 * math.sin(th * 5 + r * .23) + .8 * math.sin(th * 11 - r * .41 + 1.3) + .45 * math.sin(th * 23 + r * .9)


def spire(x, z):
    r = math.hypot(x, z)
    th = math.atan2(z, x)
    rb = RB * (1 + .1 * math.sin(3 * th + 1) + .05 * math.sin(7 * th))
    plateau = rb * .62
    if r < plateau:
        return TOP - .9 * (r / plateau) ** 2 + .35 * crag(th, r) * (r / plateau)
    t = (r - plateau) / (rb - plateau)
    # 岩层：台阶状
    h = TOP - .9 - 62 * t ** 1.05
    step = 5.2
    h = h * .55 + .45 * (round(h / step) * step)
    return h + crag(th, r) * 1.3


pk = Geo([[(0, '#1a1d24'), (.33, '#3e424c'), (.5, '#6e7480'), (.62, '#aeb8c6'), (.74, '#e2eaf2'), (1, '#fcfeff')]])
NR, NT = 62, 130
grid = np.zeros((NR + 1, NT + 1, 3))
for i in range(NR + 1):
    r = RB * 1.6 * (i / NR) ** 1.15 + .01
    for j in range(NT + 1):
        th = j / NT * math.tau
        x, z = math.cos(th) * r, math.sin(th) * r
        grid[i, j] = (x, z, spire(x, z) + .3 * rnd.uniform(-1, 1) * min(1, r / 3))
    grid[i, NT] = grid[i, 0]
dx_, dy_ = np.gradient(grid, axis=0), np.gradient(grid, axis=1)
gn = np.cross(dy_, dx_)
gn /= np.linalg.norm(gn, axis=2, keepdims=True) + 1e-9
gn[gn[..., 2] < 0] *= -1


def vtone(p, n):
    th = math.atan2(p[1], p[0])
    streak = math.sin(th * 17 + p[2] * .12) * .5 + math.sin(th * 41 - p[2] * .2) * .3 + math.sin(th * 83 + p[2] * .5) * .2
    patch = math.sin(p[0] * 1.1 + p[1] * .7) * math.sin(p[1] * 1.3 - p[2] * .8)
    strata = math.sin(p[2] * 1.9) * .08
    k = n[2] * .85 + streak * .2 + patch * .08 + strata
    return min(.96, max(.04, .26 + k * .62))


for i in range(NR):
    for j in range(NT):
        v = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
        P4 = [grid[a] for a in v]
        if max(p[2] - G(p[0], p[1]) for p in P4) < -1.2:
            continue
        N4 = [gn[a] for a in v]
        T4 = [vtone(p, n) for p, n in zip(P4, N4)]
        pk.tri(P4[0], P4[1], P4[2], (T4[0], T4[1], T4[2]), 0, normals=[N4[0], N4[1], N4[2]])
        pk.tri(P4[0], P4[2], P4[3], (T4[0], T4[2], T4[3]), 0, normals=[N4[0], N4[2], N4[3]])
# 前爪踩的岩板：叠起来的大石板，由 place 时的龙朝向决定位置
slabs = json.load(open(os.path.join(OUT, 'slabs.json'))) if os.path.exists(os.path.join(OUT, 'slabs.json')) else []


def ledge(c, rot, sx, sy, sz, tilt, tone):
    """不规则的岩板：顶面微斜带裂缝，侧面一层层往外放"""
    c = np.array(c, float)
    ca, sa = math.cos(rot), math.sin(rot)
    tx, ty = tilt
    NO = 18
    seed = [rnd.uniform(.82, 1.14) for _ in range(NO)]
    # 大的棱角：隔几个点削一刀
    for k in range(0, NO, rnd.randint(3, 5)):
        seed[k] *= rnd.uniform(.8, .95)

    def ring(scale, dz, jit):
        pts = []
        for k in range(NO):
            t = k / NO * math.tau
            r = seed[k] * scale + rnd.uniform(-jit, jit)
            lx, ly = math.cos(t) * sx * r, math.sin(t) * sy * r
            wx, wy = lx * ca - ly * sa, lx * sa + ly * ca
            pts.append(c + np.array([wx, wy, tx * lx + ty * ly + dz + rnd.uniform(-jit, jit) * sz]))
        return pts

    rings = [ring(.5, .05 * sz, .03), ring(.86, 0, .02), ring(1.0, -.12 * sz, .015), ring(1.05, -.95 * sz, .03), ring(1.2, -2.0 * sz, .05)]
    tones = [tone + .17, tone + .14, tone + .03, tone - .05, tone - .09]
    mid = c + np.array([0, 0, .1 * sz])
    for k in range(NO):
        j = (k + 1) % NO
        crack = rnd.uniform(-.05, .05)
        pk.tri(mid, rings[0][k], rings[0][j], tone + .19 + crack, 0, ref=c - np.array([0, 0, sz * 3]))
    for lv in range(len(rings) - 1):
        for k in range(NO):
            j = (k + 1) % NO
            v = rnd.uniform(-.045, .045)
            q = (rings[lv][k], rings[lv][j], rings[lv + 1][j], rings[lv + 1][k])
            ref = c - np.array([0, 0, sz * 3]) if lv < 2 else c
            pk.tri(q[0], q[1], q[2], tones[lv] + v, 0, ref=ref)
            pk.tri(q[0], q[2], q[3], tones[lv] + v, 0, ref=ref)


for s_ in slabs:
    ledge(s_['c'], s_['rot'], s_['sx'], s_['sy'], s_['sz'], s_.get('tilt', (0.0, 0.0)), s_.get('tone', .36))
for _ in range(70):
    th, r = rnd.uniform(0, math.tau), rnd.uniform(RB * .6, RB * 1.05)
    x, z = math.cos(th) * r, math.sin(th) * r
    h = max(G(x, z), spire(x, z))
    s_ = rnd.uniform(.6, 2.2)
    out = np.array([math.cos(th), math.sin(th), .35])
    c_ = np.array([x, z, h])
    pk.cone(c_ - out * s_ * .5, c_ + out * s_ * .4 + np.array([0, 0, s_ * rnd.uniform(.3, .8)]), s_ * .8, up=(0, 0, 1), seg=5, tone=.26, row=0, tip_tone=.5)
pp = os.path.join(OUT, 'dragon_peak.glb')
t = write_glb(pp, pk, name='dragon_peak', rough=.85)
P = np.array(pk.P)
size = float((P.max(0) - P.min(0)).max())
json.dump(dict(ox=OX, oz=OZ, top=TOP, size=size), open(os.path.join(OUT, 'peak.json'), 'w'))
print('peak', t, 'tris', round(os.path.getsize(pp) / 1e6, 2), 'MB size', round(size, 1))
