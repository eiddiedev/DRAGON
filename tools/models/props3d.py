#!/usr/bin/env python3
"""路灯、绵羊、蝙蝠、飞毯、祭坛、龙纹立石。都是真实几何体，生物带骨骼动画。
用法：props3d.py <输出目录> [lamps sheep bat carpet altar]"""
import json
import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbw import Geo, Rigid, write_glb

OUT = sys.argv[1]
what = set(sys.argv[2:]) or {'lamps', 'sheep', 'bat', 'carpet', 'altar'}
os.makedirs(OUT, exist_ok=True)
ROOT = '/Users/a1234/Documents/awesomeWRLD/assets'
H = np.load(f'{ROOT}/terrain/v3/base_heights.npy')
PATH = json.load(open(f'{ROOT}/terrain/v3/path.json'))
rnd = random.Random(8)
UP = np.array([0, 0, 1.0])


def Gh(x, z):
    x = min(max(x, 0), 255.99)
    z = min(max(z, 0), 255.99)
    x0, z0 = int(x), int(z)
    fx, fz = x - x0, z - z0
    return float(H[z0, x0] * (1 - fx) * (1 - fz) + H[z0, x0 + 1] * fx * (1 - fz) + H[z0 + 1, x0] * (1 - fx) * fz + H[z0 + 1, x0 + 1] * fx * fz)


def unit(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) + 1e-9)


def ring(c, r, seg, z=0.0, a0=0.0, sy=1.0):
    return [np.array([c[0] + math.cos(a0 + i / seg * math.tau) * r, c[1] + math.sin(a0 + i / seg * math.tau) * r * sy, c[2] + z]) for i in range(seg)]


def lathe(g, c, prof, row, seg=8, tone=.5, a0=0.0, skin=None):
    rings = [ring(c, r, seg, z, a0) for r, z in prof]
    ctrs = [np.array([c[0], c[1], c[2] + z]) for _, z in prof]
    g.loft(rings, tone, row, ctrs, [skin] * len(prof) if skin else None, tone_fn=lambda i, k: tone + .1 * math.sin(k * 1.9 + i))


_PHI = (1 + 5 ** .5) / 2
_IV = [unit(p) for p in ((-1, _PHI, 0), (1, _PHI, 0), (-1, -_PHI, 0), (1, -_PHI, 0), (0, -1, _PHI), (0, 1, _PHI), (0, -1, -_PHI), (0, 1, -_PHI), (_PHI, 0, -1), (_PHI, 0, 1), (-_PHI, 0, -1), (-_PHI, 0, 1))]
_IF = ((0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1))


def smooth_sphere(g, c, r, row, tone, skin=None, sq=(1, 1, 1)):
    """二十面体：顶点法线放射状，看起来是圆润的一团。"""
    c = np.asarray(c, float)
    k = np.array(sq) * r
    for a, b, d in _IF:
        g.tri(c + _IV[a] * k, c + _IV[b] * k, c + _IV[d] * k, tone, row, c, skin, normals=[_IV[a], _IV[b], _IV[d]])


# ==================== 路灯
if 'lamps' in what:
    ROWS = [[(0, '#14141a'), (.5, '#30313a'), (1, '#6d6f7c')], [(0, '#4a4a50'), (1, '#9a988f')], [(0, '#6a4a1c'), (1, '#c9a24b')]]
    GROWS = [[(0, '#ffb04a'), (.6, '#ffd98a'), (1, '#fff7dc')]]
    P, Gl = Geo(ROWS), Geo(GROWS)
    roads = [[(p[0], p[1]) for p in PATH[::3]], [(130, 52), (135, 66), (149, 79), (159, 90), (162, 96)], [(162, 127), (167, 134), (171, 141)]]
    lamps = []

    def add_line(pts, every, flip=True):
        acc, s = 0.0, 1
        for i in range(1, len(pts)):
            ax, ay = pts[i - 1]
            bx, by = pts[i]
            L = math.hypot(bx - ax, by - ay)
            acc += L
            if acc >= every:
                acc = 0
                nx, ny = -(by - ay) / (L + 1e-6), (bx - ax) / (L + 1e-6)
                lamps.append((bx + nx * 2.7 * s, by + ny * 2.7 * s, math.atan2(-ny * s, -nx * s)))
                if flip:
                    s = -s

    add_line(roads[0], 11.0)
    add_line(roads[1], 12.0)
    add_line(roads[2], 9.0, False)
    print('lamps', len(lamps))
    OX, OY = 128.0, 128.0
    tops = []
    for x, y, face in lamps:
        g_ = Gh(x, y)
        c = np.array([x - OX, y - OY, g_ - .1])
        # 石基 + 铸铁灯柱：底座、收腰、竖棱、圈饰
        lathe(P, c, [(.34, 0), (.34, .18), (.26, .26), (.2, .55)], 1, 8, .55, math.pi / 8)
        lathe(P, c, [(.17, .55), (.12, .72), (.075, .95), (.06, 1.9), (.055, 3.0)], 0, 8, .55)
        for z in (1.0, 2.05, 3.0):
            lathe(P, c, [(.06, z - .05), (.105, z), (.06, z + .05)], 0, 8, .7)
        # 弯臂：向路面伸出，末端卷起，吊着灯笼
        d = np.array([math.cos(face), math.sin(face), 0])
        pts = [c + UP * 3.0, c + UP * 3.3 + d * .22, c + UP * 3.42 + d * .55, c + UP * 3.34 + d * .86]
        for a, b in zip(pts, pts[1:]):
            P.cone(a, b, .035, up=(0, 0, 1), seg=4, tone=.5, row=0, tip_tone=.5)
        # 铁艺卷饰：撑臂
        P.cone(c + UP * 2.62, c + UP * 3.18 + d * .42, .02, up=(0, 0, 1), seg=4, tone=.5, row=0, tip_tone=.5)
        # 灯顶尖饰
        lathe(P, c, [(.06, 3.0), (.09, 3.06), (.02, 3.42), (.05, 3.5), (.005, 3.72)], 0, 6, .6)
        # 灯笼：六边形铁笼
        L_ = c + UP * 3.34 + d * .86
        Lz = L_ - UP * .08
        lathe(P, Lz, [(.015, 0), (.03, -.05), (.25, -.17), (.22, -.21), (.16, -.21)], 0, 6, .5)
        lathe(P, Lz, [(.26, -.62), (.2, -.72), (.09, -.76), (.09, -.8), (.03, -.84)], 0, 6, .55)
        # 铁栅
        for i in range(6):
            a = i / 6 * math.tau
            top = Lz + np.array([math.cos(a) * .21, math.sin(a) * .21, -.2])
            bot = Lz + np.array([math.cos(a) * .25, math.sin(a) * .25, -.63])
            P.cone(top, bot, .014, up=(0, 0, 1), seg=3, tone=.45, row=0, tip_tone=.45)
        # 发光的灯罩和灯芯
        rings = [ring(Lz, .2, 6, -.21), ring(Lz, .235, 6, -.62)]
        Gl.loft(rings, .55, 0, [Lz - UP * .21, Lz - UP * .62], cap=True)
        tops.append((c[0], c[1], g_ + 2.9))
    # 灯柱之间的串灯
    for (ax, ay, az), (bx, by, bz) in zip(tops, tops[1:]):
        L = math.hypot(ax - bx, ay - by)
        if L > 16:
            continue
        k = int(L / 1.25)
        for i in range(1, k):
            t = i / k
            sag = math.sin(t * math.pi) * L * .07
            q = np.array([ax + (bx - ax) * t, ay + (by - ay) * t, az + (bz - az) * t - sag])
            smooth_sphere(Gl, q, .06, 0, .7)
    t1 = write_glb(os.path.join(OUT, 'lamp_posts.glb'), P, name='lamp_posts', rough=.55, metal=.3)
    t2 = write_glb(os.path.join(OUT, 'lamp_glow.glb'), Gl, name='lamp_glow', rough=.4, emissive=(1, 1, 1))
    print('lamp tris', t1, t2)

# ==================== 绵羊
if 'sheep' in what:
    ROWS = [[(0, '#8c8574'), (.5, '#d5ccb8'), (1, '#fbf6ea')], [(0, '#1f1a18'), (1, '#55453c')], [(0, '#0e0c0c'), (1, '#2b2522')], [(0, '#6b5a50'), (1, '#b09a8c')]]
    g = Geo(ROWS)
    J = {}
    joints = []

    def j(nm, p):
        J[nm] = len(joints)
        joints.append((nm, np.array(p, float)))

    j('body', (0, 0, .78))
    j('neck', (0, .52, .9))
    j('head', (0, .78, 1.02))
    j('earL', (.13, .8, 1.14))
    j('earR', (-.13, .8, 1.14))
    j('tail', (0, -.66, .86))
    LEGS = [('LF', .22, .42), ('RF', -.22, .42), ('LH', .22, -.42), ('RH', -.22, -.42)]
    for nm, x, y in LEGS:
        j(nm + 'u', (x, y, .56))
        j(nm + 'l', (x, y + .01, .3))
    r_ = random.Random(3)
    # 羊毛：一整团蓬松的身体，表面只有细小的起伏，不是一颗颗毛球
    def wool(c, radii, subdiv, skin, amp=.055):
        verts = [np.array(v) for v in _IV]
        faces = list(_IF)
        for _ in range(subdiv):
            cache, nf = {}, []

            def mid(i, j):
                k = (min(i, j), max(i, j))
                if k not in cache:
                    verts.append(unit(verts[i] + verts[j]))
                    cache[k] = len(verts) - 1
                return cache[k]

            for i, j, k in faces:
                a_, b_, c_ = mid(i, j), mid(j, k), mid(k, i)
                nf += [(i, a_, c_), (j, b_, a_), (k, c_, b_), (a_, b_, c_)]
            faces = nf
        V = np.array(verts)

        def bump(p):
            return (np.sin(p[0] * 11 + 1.3) * np.sin(p[1] * 13) * np.sin(p[2] * 12 + .7) + .5 * np.sin(p[0] * 23) * np.sin(p[1] * 27 + 2) * np.sin(p[2] * 25))

        D = np.array([v * (1 + amp * bump(v)) * np.array(radii) for v in V])
        N_ = np.zeros_like(D)
        for i, j, k in faces:
            n_ = np.cross(D[j] - D[i], D[k] - D[i])
            N_[i] += n_
            N_[j] += n_
            N_[k] += n_
        N_ /= np.linalg.norm(N_, axis=1, keepdims=True) + 1e-9
        ctr = np.asarray(c, float)
        for i, j, k in faces:
            tones = tuple(float(.68 + .14 * V[q][2] + .1 * np.sin(V[q][0] * 31) * np.sin(V[q][1] * 29)) for q in (i, j, k))
            g.tri(D[i] + ctr, D[j] + ctr, D[k] + ctr, tones, 0, ctr, skin, normals=[N_[i], N_[j], N_[k]])

    wool((0, -.02, .8), (.47, .72, .44), 3, (J['body'], J['body'], 0.))
    wool((0, .5, .94), (.24, .28, .25), 2, (J['neck'], J['neck'], 0.))
    # 头：长脸，深色
    g.skin = (J['head'], J['head'], 0.0)
    prof = [(.74, .09, .11), (.8, .105, .125), (.88, .092, .108), (.96, .068, .078), (1.0, .05, .052)]
    rings, ctrs = [], []
    for y, rx, rz in prof:
        zc = 1.03 - (y - .76) * .38
        rings.append([np.array([math.cos(i / 8 * math.tau) * rx, y, zc + math.sin(i / 8 * math.tau) * rz]) for i in range(8)])
        ctrs.append(np.array([0, y, zc]))
    for a, b, ca, cb in zip(rings, rings[1:], ctrs, ctrs[1:]):
        for k in range(8):
            k2 = (k + 1) % 8
            na, nb, nc, nd = unit(a[k] - ca), unit(b[k] - cb), unit(b[k2] - cb), unit(a[k2] - ca)
            g.tri(a[k], b[k], b[k2], .55, 1, ca, normals=[na, nb, nc])
            g.tri(a[k], b[k2], a[k2], .55, 1, ca, normals=[na, nc, nd])
    smooth_sphere(g, (0, 1.0, .925), .042, 2, .6, sq=(1, .6, .7))
    wool((0, .78, 1.14), (.11, .13, .075), 1, (J['head'], J['head'], 0.), .03)
    # 眼
    for s in (-1, 1):
        smooth_sphere(g, (s * .092, .84, 1.035), .02, 2, .4)
    # 耳
    for nm, s in (('earL', 1), ('earR', -1)):
        g.skin = (J[nm], J[nm], 0.0)
        base = joints[J[nm]][1]
        g.cone(base, base + np.array([s * .2, -.02, -.05]), .05, up=(0, 1, 0), seg=4, tone=.5, row=3, tip_tone=.4, n=1)
    # 尾巴
    g.skin = (J['tail'], J['tail'], 0.0)
    wool((0, -.7, .8), (.07, .08, .12), 1, (J['tail'], J['tail'], 0.), .03)
    # 腿：上段带毛，下段细，蹄子
    for nm, x, y in LEGS:
        g.skin = (J[nm + 'u'], J[nm + 'u'], 0.0)
        lathe(g, (x, y, .3), [(.052, 0), (.068, .14), (.085, .3)], 1, 6, .5, skin=(J[nm + 'u'], J[nm + 'u'], 0.0))
        sk = (J[nm + 'l'], J[nm + 'l'], 0.0)
        g.skin = sk
        lathe(g, (x, y + .01, 0), [(.052, 0), (.05, .05), (.036, .08), (.04, .3)], 1, 6, .45, skin=sk)
        lathe(g, (x, y + .01, 0), [(.056, 0), (.05, .055)], 2, 6, .4, skin=sk)
    n_j = len(joints)
    rest = np.array([p for _, p in joints])
    XA = np.array([1.0, 0, 0])

    def bake(fn, dur, fps=12):
        n = int(dur * fps) + 1
        times = np.linspace(0, dur, n)
        pos = np.zeros((n, n_j, 3))
        rot = np.zeros((n, n_j, 4))
        for f, t in enumerate(times):
            M = fn(t / dur * math.tau, t)
            for nm, i in J.items():
                m = M.get(nm, Rigid())
                pos[f, i] = m.apply(rest[i])
                rot[f, i] = m.q
        pos[-1], rot[-1] = pos[0], rot[0]
        return dict(times=times, pos=pos, rot=rot)

    def pose(body_z=0.0, body_pitch=0.0, neck=0.0, head=0.0, head_yaw=0.0, ear=0.0, tail=0.0, legs=None):
        Mb = Rigid(t=(0, 0, body_z)).then(Rigid()) if False else Rigid.about(rest[J['body']], XA, body_pitch).then(Rigid(t=(0, 0, body_z)))
        Mn = Rigid.about(rest[J['neck']], XA, neck).then(Mb)
        Mh = Rigid.about(rest[J['head']], UP, head_yaw).then(Rigid.about(rest[J['head']], XA, head)).then(Mn)
        out = dict(body=Mb, neck=Mn, head=Mh)
        out['earL'] = Rigid.about(rest[J['earL']], (0, 1, 0), ear).then(Mh)
        out['earR'] = Rigid.about(rest[J['earR']], (0, 1, 0), -ear).then(Mh)
        out['tail'] = Rigid.about(rest[J['tail']], (0, 1, 0), tail).then(Mb)
        for nm, _, _ in LEGS:
            u, l = (legs or {}).get(nm, (0.0, 0.0))
            Mu = Rigid.about(rest[J[nm + 'u']], XA, u).then(Mb)
            out[nm + 'u'] = Mu
            out[nm + 'l'] = Rigid.about(rest[J[nm + 'l']], XA, l).then(Mu)
        return out

    def walk(ph, t):
        s = math.sin(ph)
        c_ = math.cos(ph)
        legs = {}
        for nm, phase in (('LF', 0), ('RH', 0), ('RF', math.pi), ('LH', math.pi)):
            a = math.sin(ph + phase)
            b = max(0.0, math.cos(ph + phase))
            legs[nm] = (.42 * a, -.55 * b)
        return pose(body_z=.018 * math.sin(ph * 2), body_pitch=.018 * s, neck=.05 * math.sin(ph * 2 + .6), head=-.03 * math.sin(ph * 2), ear=.1 * c_, tail=.2 * math.sin(ph * 2), legs=legs)

    def graze(ph, t):
        # 低头吃草：1 秒低下去，中间咀嚼，最后抬起
        dur = 8.0
        k = min(1.0, t / 1.1, (dur - t) / 1.1) if 0 < t < dur else 0.0
        k = k * k * (3 - 2 * k)
        chew = math.sin(t * 7) * .04 * k
        lift = .08 * math.sin(t * 1.3) * k
        return pose(body_pitch=-.05 * k, neck=-.95 * k, head=-.35 * k + chew, head_yaw=.08 * math.sin(t * 1.1) * k, ear=.18 * math.sin(t * 2.3) * (t > 4), tail=.25 * math.sin(t * 4.2) * (t > 5.5))

    def idle(ph, t):
        return pose(body_z=.006 * math.sin(ph * 3), neck=.05 * math.sin(ph), head=.04 * math.sin(ph * 2), head_yaw=.5 * math.sin(ph), ear=.14 * (math.sin(t * 5) if 2 < t < 2.8 else 0), tail=.12 * math.sin(t * 6) * (t > 4))

    clips = dict(walk=bake(walk, 1.0, 16), graze=bake(graze, 8.0, 10), idle=bake(idle, 6.0, 8))
    t = write_glb(os.path.join(OUT, 'sheep3.glb'), g, joints, clips, name='sheep3', rough=.92)
    print('sheep', t, 'tris', round(os.path.getsize(os.path.join(OUT, 'sheep3.glb')) / 1e6, 2), 'MB')

# ==================== 蝙蝠
if 'bat' in what:
    ROWS = [[(0, '#0e0a10'), (1, '#3a2f3e')], [(0, '#1a1018'), (1, '#54405a')]]
    g = Geo(ROWS)
    joints = [('body', np.array([0, 0, 0.0])), ('wL1', np.array([.07, .05, .02])), ('wR1', np.array([-.07, .05, .02])), ('wL2', np.array([.34, .08, .05])), ('wR2', np.array([-.34, .08, .05]))]
    g.skin = (0, 0, 0.0)
    smooth_sphere(g, (0, 0, 0), .1, 0, .5, sq=(.85, 1.5, .85))
    smooth_sphere(g, (0, .15, .03), .07, 0, .55)
    for s in (-1, 1):
        g.cone((s * .035, .16, .07), (s * .06, .15, .17), .025, seg=3, tone=.5, row=0)
    for s, a, b in ((1, 1, 3), (-1, 2, 4)):
        # 翼膜 + 指骨，内外两段
        pts = dict(sh=np.array([s * .07, .05, .02]), el=np.array([s * .34, .08, .05]), t1=np.array([s * .68, .04, .02]), t2=np.array([s * .62, -.14, 0]), t3=np.array([s * .42, -.2, 0]), r1=np.array([s * .2, -.22, 0]), r0=np.array([s * .05, -.14, 0]))
        A, B_ = (a, a, 0.0), (b, b, 0.0)
        for p0, p1, p2, sk in ((pts['sh'], pts['el'], pts['r1'], [A, A, A]), (pts['sh'], pts['r1'], pts['r0'], [A, A, A]), (pts['el'], pts['t3'], pts['r1'], [A, B_, A]), (pts['el'], pts['t2'], pts['t3'], [A, B_, B_]), (pts['el'], pts['t1'], pts['t2'], [A, B_, B_])):
            g.tri(p0, p1, p2, .6, 1, ref=(0, 0, -1), skin=sk)
            g.tri(p0, p1, p2, .35, 1, ref=(0, 0, 1), skin=sk)
    rest = np.array([p for _, p in joints])

    def flap(ph, t):
        a = .75 * math.sin(ph)
        b = .55 * math.sin(ph - .9)
        ML1 = Rigid.about(rest[1], (0, 1, 0), -a)
        MR1 = Rigid.about(rest[2], (0, 1, 0), a)
        ML2 = Rigid.about(rest[3], (0, 1, 0), -b).then(ML1)
        MR2 = Rigid.about(rest[4], (0, 1, 0), b).then(MR1)
        return [Rigid(t=(0, 0, -.03 * math.sin(ph))), ML1, MR1, ML2, MR2]

    n = 9
    pos = np.zeros((n, 5, 3))
    rot = np.zeros((n, 5, 4))
    times = np.linspace(0, .36, n)
    for f, t_ in enumerate(times):
        ms = flap(t_ / .36 * math.tau, t_)
        for i, m in enumerate(ms):
            pos[f, i] = m.apply(rest[i])
            rot[f, i] = m.q
    pos[-1], rot[-1] = pos[0], rot[0]
    print('bat', write_glb(os.path.join(OUT, 'bat3.glb'), g, joints, dict(flap=dict(times=times, pos=pos, rot=rot)), name='bat3', rough=.8))

# ==================== 飞毯
if 'carpet' in what:
    ROWS = [[(0, '#3e0a14'), (1, '#9c1f2c')], [(0, '#0e1740'), (1, '#27408f')], [(0, '#8a6420'), (.6, '#dcae44'), (1, '#ffe89a')], [(0, '#8d7b56'), (1, '#efe2bf')]]
    g = Geo(ROWS)
    LEN, WID = 4.4, 2.5
    NL, NW = 52, 30
    NB = 8
    joints = [(f'c{i}', np.array([0, -LEN / 2 + i / (NB - 1) * LEN, .05])) for i in range(NB)]

    def skin_at(y):
        f = (y + LEN / 2) / LEN * (NB - 1)
        i = min(int(f), NB - 2)
        return (i, i + 1, f - i)

    def cell_color(i, j):
        """图案：外框、回纹边、斜格底，中央一轮圆形花心。不用十字。"""
        y = ((i + .5) / NL - .5) * LEN
        x = ((j + .5) / NW - .5) * WID
        ex, ey = 1 - abs(x) / (WID / 2), 1 - abs(y) / (LEN / 2)
        e = min(ex * WID / 2, ey * LEN / 2)
        if e < .1:
            return 2, .62
        if e < .2:
            return 1, .55
        if e < .25:
            return 2, .8
        r = math.hypot(x * 1.0, y * .82)
        th = math.atan2(y, x)
        petal = .62 + .05 * math.cos(th * 8)
        if r < .16:
            return 2, .85
        if r < .28:
            return 3, .8
        if r < .34:
            return 2, .7
        if r < petal - .08:
            return 1, .55
        if r < petal:
            return 2, .75
        d = (x * .9 + y * .9) % .46
        d2 = (x * .9 - y * .9) % .46
        if min(d, d2) < .045:
            return 2, .55
        return 0, .55 + .07 * math.sin(x * 9) * math.sin(y * 9)

    for i in range(NL):
        y0, y1 = -LEN / 2 + i / NL * LEN, -LEN / 2 + (i + 1) / NL * LEN
        for j in range(NW):
            x0, x1 = -WID / 2 + j / NW * WID, -WID / 2 + (j + 1) / NW * WID
            row, tone = cell_color(i, j)
            sk = [skin_at(y0), skin_at(y0), skin_at(y1), skin_at(y1)]
            a, b, c, d = np.array([x0, y0, .05]), np.array([x1, y0, .05]), np.array([x1, y1, .05]), np.array([x0, y1, .05])
            n = np.array([0, 0, 1.0])
            g.tri(a, b, c, tone, row, skin=[sk[0], sk[1], sk[2]], normals=[n] * 3)
            g.tri(a, c, d, tone, row, skin=[sk[0], sk[2], sk[3]], normals=[n] * 3)
            # 背面
            g.tri(a - (0, 0, .03), c - (0, 0, .03), b - (0, 0, .03), .35, 1, skin=[sk[0], sk[2], sk[1]], normals=[-n] * 3)
            g.tri(a - (0, 0, .03), d - (0, 0, .03), c - (0, 0, .03), .35, 1, skin=[sk[0], sk[3], sk[2]], normals=[-n] * 3)
    # 流苏
    for e, y in ((0, -LEN / 2), (NB - 1, LEN / 2)):
        s_ = 1 if y > 0 else -1
        for k in range(26):
            x = -WID / 2 + (k + .5) / 26 * WID
            sk = (e, e, 0.0)
            g.tri((x - .025, y, .05), (x + .025, y, .05), (x, y + s_ * .22, .02), .8, 3, ref=(x, y, -1), skin=sk)
            g.tri((x - .025, y, .05), (x + .025, y, .05), (x, y + s_ * .22, .02), .6, 3, ref=(x, y, 1), skin=sk)
    # 边缘加粗，有厚度感
    rest = np.array([p for _, p in joints])
    n = 25
    times = np.linspace(0, 2.0, n)
    pos = np.zeros((n, NB, 3))
    rot = np.zeros((n, NB, 4))
    for f, t in enumerate(times):
        ph = t / 2.0 * math.tau
        zs = [.075 * math.sin(ph - i * .8) for i in range(NB)]
        for i in range(NB):
            pos[f, i] = rest[i] + UP * zs[i]
            dz = zs[min(i + 1, NB - 1)] - zs[max(i - 1, 0)]
            ang = math.atan2(dz, LEN / (NB - 1) * 2)
            rot[f, i] = Rigid.about(rest[i], (1, 0, 0), ang).q
    pos[-1], rot[-1] = pos[0], rot[0]
    print('carpet', write_glb(os.path.join(OUT, 'flying_carpet.glb'), g, joints, dict(ripple=dict(times=times, pos=pos, rot=rot)), name='flying_carpet', rough=.85))

# ==================== 祭坛和龙纹立石
if 'altar' in what:
    ROWS = [[(0, '#23252e'), (.5, '#555864'), (1, '#9a9ca6')], [(0, '#3b3d48'), (1, '#b1b2bb')], [(0, '#5a4a20'), (1, '#c9a24b')]]
    GROWS = [[(0, '#3fb4ff'), (.6, '#8fe0ff'), (1, '#eaffff')]]
    P, Gl = Geo(ROWS), Geo(GROWS)
    # 八角形三层石台，南面有台阶
    tiers = [(7.4, 0, .7), (5.7, .7, 1.4), (4.1, 1.4, 2.1)]
    for R, z0, z1 in tiers:
        rings = [ring((0, 0, 0), R * 1.02, 8, z0 - .6, math.pi / 8), ring((0, 0, 0), R, 8, z1 - .08, math.pi / 8), ring((0, 0, 0), R * .97, 8, z1, math.pi / 8)]
        P.loft(rings, .5, 0, [np.array([0, 0, z0 - .6]), np.array([0, 0, z1 - .08]), np.array([0, 0, z1])], tone_fn=lambda i, k: .46 + .12 * (k % 2))
        # 石缝：竖向的一圈凸条
        for k in range(8):
            a = math.pi / 8 + k / 8 * math.tau
            P.box((math.cos(a) * R * 1.0, math.sin(a) * R * 1.0, (z0 + z1) / 2), (.16, 0, 0), (0, .16, 0), (0, 0, (z1 - z0) / 2), .62, 1)
    for i in range(6):
        P.box((0, -7.8 + i * .42 + .2, .2 + i * .35), (1.5 - .05 * i, 0, 0), (0, .28, 0), (0, 0, .2 + i * .35), .55 + .03 * (i % 2), 1)
    # 地上的发光符环（几何小块，不是贴图）
    for R, cnt, w in ((3.3, 24, .13), (2.6, 16, .1)):
        for k in range(cnt):
            a0 = k / cnt * math.tau
            a1 = (k + .6) / cnt * math.tau
            za = 2.13
            n = UP
            pts = [np.array([math.cos(a) * r, math.sin(a) * r, za]) for a, r in ((a0, R - w), (a1, R - w), (a1, R + w), (a0, R + w))]
            Gl.tri(pts[0], pts[1], pts[2], .7, 0, normals=[n] * 3)
            Gl.tri(pts[0], pts[2], pts[3], .7, 0, normals=[n] * 3)
    # 中央基座
    lathe(P, (0, 0, 2.1), [(1.7, 0), (1.5, .35), (1.05, .55), (.95, 1.5), (1.25, 1.75), (1.35, 1.95)], 0, 8, .55, math.pi / 8)
    # 基座上：一尊张翼俯视的西方龙石像（石像只要大形，雄浑）
    Z0 = 4.05
    body = [((0, -.3, 0), .5, .6), ((0, -.05, .55), .78, .9), ((0, .1, 1.35), .88, 1.0), ((0, -.1, 2.2), .72, .86), ((0, -.35, 2.85), .46, .55), ((0, -.55, 3.5), .34, .4), ((0, -.72, 4.05), .28, .32), ((0, -1.15, 4.42), .25, .28)]
    rings, ctrs = [], []
    for (x, y, z), rw, rd in body:
        rings.append([np.array([x + math.cos(i / 10 * math.tau) * rw, y + math.sin(i / 10 * math.tau) * rd, Z0 + z]) for i in range(10)])
        ctrs.append(np.array([x, y, Z0 + z]))
    P.loft(rings, .55, 0, ctrs, tone_fn=lambda i, k: .46 + .22 * math.sin(k / 10 * math.tau + 1.2) + rnd.uniform(-.06, .06))
    # 胸前腹甲条
    for i in range(7):
        z = .5 + i * .42
        rw = np.interp(z, [b[0][2] for b in body], [b[1] for b in body])
        rd = np.interp(z, [b[0][2] for b in body], [b[2] for b in body])
        yc = np.interp(z, [b[0][2] for b in body], [b[0][1] for b in body])
        P.box((0, yc - rd * .92, Z0 + z), (rw * .55, 0, 0), (0, .12, 0), (0, 0, .15), .62, 1)
    # 头：窄长、低垂、角向后
    hc = np.array([0, -1.2, Z0 + 4.42])
    hrings, hctrs = [], []
    for f, w_, t, b in ((-.05, .3, .32, -.26), (.35, .36, .36, -.24), (.8, .28, .25, -.18), (1.35, .22, .17, -.16), (1.72, .13, .08, -.1)):
        c = hc + np.array([0, -f, -f * .32])
        hrings.append([c + np.array([sx * w_, 0, (t if sz > 0 else b) * abs(sz)]) for sx, sz in ((1, 0), (.7, .85), (0, 1), (-.7, .85), (-1, 0), (-.5, -1), (.5, -1))])
        hctrs.append(c)
    P.loft(hrings, .58, 0, hctrs)
    for s_ in (-1, 1):
        P.cone(hc + np.array([s_ * .24, .05, .24]), hc + np.array([s_ * .7, 1.5, 1.05]), .14, up=(1, 0, 0), seg=6, tone=.5, row=0, curve=np.array([0, 0, .32]), n=4, tip_tone=.75)
        P.cone(hc + np.array([s_ * .34, .02, .05]), hc + np.array([s_ * 1.0, .9, .22]), .08, up=(1, 0, 0), seg=4, tone=.5, row=0, tip_tone=.7)
        # 发光的眼
        e = hc + np.array([s_ * .31, -.42, .14])
        smooth_sphere(Gl, e, .065, 0, .95)
        # 前腿：撑在基座边缘
        S_ = np.array([s_, 0, 0])
        hip = np.array([s_ * .8, -.15, Z0 + 1.2])
        knee = np.array([s_ * 1.08, -.72, Z0 + .6])
        foot = np.array([s_ * .78, -1.05, Z0 + .03])
        for a, b, r0, r1 in ((hip, knee, .38, .25), (knee, foot, .25, .18)):
            d = b - a
            u = unit(np.cross(d, (0, 1, .1)))
            v = unit(np.cross(d, u))
            P.loft([[p + (u * math.cos(q) + v * math.sin(q)) * r for q in np.linspace(0, math.tau, 7, endpoint=False)] for p, r in ((a, r0), (b, r1))], .52, 0, [a, b])
        for k in (-.5, 0, .5):
            P.cone(foot, foot + np.array([k * .34, -.42, -.02]), .07, up=(0, 0, 1), seg=4, tone=.32, row=0, tip_tone=.7)
        # 翅膀：半张，向后上方
        sh = np.array([s_ * .55, .2, Z0 + 2.15])
        el = sh + np.array([s_ * 1.5, .75, 1.25])
        wr = el + np.array([s_ * .9, .35, 1.65])
        tips = [wr + np.array([s_ * 2.5, .4, .5]), wr + np.array([s_ * 3.1, .6, -1.35]), wr + np.array([s_ * 2.6, .6, -3.2]), wr + np.array([s_ * 1.3, .4, -4.3])]
        for a, b, r in ((sh, el, .2), (el, wr, .13)):
            P.cone(a, b, r, up=(0, 1, 0), seg=6, tone=.55, row=0, tip_tone=.6, n=2)
        for tp in tips:
            P.cone(wr, tp, .09, up=(0, 1, 0), seg=4, tone=.55, row=0, tip_tone=.6, n=2)
        edges = [wr] + tips + [np.array([s_ * .9, .6, Z0 + .9])]
        back = np.array([0, 1, .1])
        for a, b in zip(tips, tips[1:] + [edges[-1]]):
            mid = (a + b) / 2 + (wr - (a + b) / 2) * .16
            for p0, p1 in ((wr, mid),):
                P.tri(wr, a, mid, .44 + rnd.uniform(-.03, .03), 0, ref=wr + back)
                P.tri(wr, mid, b, .44 + rnd.uniform(-.03, .03), 0, ref=wr + back)
                P.tri(wr, a, mid, .34, 0, ref=wr - back)
                P.tri(wr, mid, b, .34, 0, ref=wr - back)
        P.tri(sh, el, wr, .42, 0, ref=sh + back)
        P.tri(sh, wr, edges[-1], .42, 0, ref=sh + back)
        P.tri(sh, el, wr, .34, 0, ref=sh - back)
        P.tri(sh, wr, edges[-1], .34, 0, ref=sh - back)
    # 尾巴盘在基座后面
    tl = [np.array([0, .3, Z0 + .2]), np.array([.5, .95, Z0 + .13]), np.array([1.1, .55, Z0 + .11]), np.array([1.2, -.2, Z0 + .1]), np.array([1.5, -.7, Z0 + .08])]
    for a, b, r0, r1 in zip(tl, tl[1:], (.42, .32, .22, .13), (.32, .22, .13, .03)):
        d = b - a
        u = unit(np.cross(d, (0, 0, 1)))
        v = unit(np.cross(d, u))
        P.loft([[p + (u * math.cos(q) + v * math.sin(q)) * r for q in np.linspace(0, math.tau, 7, endpoint=False)] for p, r in ((a, r0), (b, r1))], .5, 0, [a, b], cap=False)
    # 四角火盆座
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        c = (math.cos(a) * 5.0, math.sin(a) * 5.0, 1.4)
        lathe(P, c, [(.42, 0), (.28, .2), (.2, 1.2), (.46, 1.45), (.5, 1.6)], 0, 8, .5)
        for q in range(3):
            Gl.cone(np.array(c) + np.array([(q - 1) * .15, 0, 1.55]), np.array(c) + np.array([(q - 1) * .13, 0, 2.2 + q % 2 * .25]), .14, seg=5, tone=.5, row=0, tip_tone=.98)
    print('altar', write_glb(os.path.join(OUT, 'altar3.glb'), P, name='altar3', rough=.85), write_glb(os.path.join(OUT, 'altar3_glow.glb'), Gl, name='altar3_glow', rough=.4, emissive=(1, 1, 1)))
    # 龙纹立石：粗粝的巨石，正面浮雕一只张翼西方龙（发光件单独）
    R_, Rg = Geo(ROWS), Geo(GROWS)
    prof = [(0, 1.05, .55), (.35, 1.0, .5), (2.0, .85, .42), (3.7, .68, .34), (4.5, .34, .2)]
    rings = []
    ctrs = []
    for z, w_, d in prof:
        c = np.array([0, 0, z])
        pts = [(1, 0), (.92, .85), (.35, 1), (-.35, 1), (-.92, .85), (-1, 0), (-.92, -.85), (-.35, -1), (.35, -1), (.92, -.85)]
        rings.append([c + np.array([x * w_ + rnd.uniform(-.04, .04), y * d + rnd.uniform(-.03, .03), rnd.uniform(-.05, .05) if z > 0 else 0]) for x, y in pts])
        ctrs.append(c)
    R_.loft(rings, .55, 0, ctrs, tone_fn=lambda i, k: .46 + .18 * rnd.random())
    # 浮雕（朝 -Y）
    f = -.47
    n = np.array([0, -1.0, 0])

    def e2(x, z, d=.0):
        return np.array([x, f - d, z])

    def tri_g(a, b, c, t=.7):
        Rg.tri(a, b, c, t, 0, normals=[n] * 3)

    cz = 2.25
    for s_ in (-1, 1):
        # 翼
        w0 = e2(s_ * .08, cz + .35)
        for tip, nxt in ((e2(s_ * .62, cz + 1.05), e2(s_ * .66, cz + .5)), (e2(s_ * .66, cz + .5), e2(s_ * .56, cz + .05)), (e2(s_ * .56, cz + .05), e2(s_ * .3, cz - .25))):
            mid = (tip + nxt) / 2 + (w0 - (tip + nxt) / 2) * .22
            tri_g(w0, tip, mid, .55)
            tri_g(w0, mid, nxt, .55)
            tri_g(w0, tip, tip + (w0 - tip) * .02 + np.array([0, -.002, .04]), .9)
    # 身体、脖子、头、尾
    tri_g(e2(-.13, cz + .35), e2(.13, cz + .35), e2(0, cz - .35), .85)
    tri_g(e2(-.12, cz + .33), e2(.12, cz + .33), e2(.05, cz + .78), .85)
    tri_g(e2(-.12, cz + .33), e2(.05, cz + .78), e2(-.05, cz + .78), .85)
    tri_g(e2(-.09, cz + .74), e2(.09, cz + .74), e2(0, cz + 1.05), .95)
    tri_g(e2(-.07, cz + .78), e2(-.2, cz + .98), e2(-.03, cz + .85), .9)
    tri_g(e2(.07, cz + .78), e2(.03, cz + .85), e2(.2, cz + .98), .9)
    tri_g(e2(-.05, cz - .3), e2(.05, cz - .3), e2(.22, cz - .78), .85)
    print('rune', write_glb(os.path.join(OUT, 'rune3.glb'), R_, name='rune3', rough=.9), write_glb(os.path.join(OUT, 'rune3_glow.glb'), Rg, name='rune3_glow', rough=.4, emissive=(1, 1, 1)))
