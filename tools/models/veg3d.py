#!/usr/bin/env python3
"""真实几何体的植被：松树（树叶、树干都是模型，没有透明贴图）、草叶、花朵、圣树。
用法：veg3d.py <输出目录> [trees] [grass] [holy]"""
import json
import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbw import Geo, write_glb

OUT = sys.argv[1]
what = set(sys.argv[2:]) or {'trees', 'grass', 'holy'}
os.makedirs(OUT, exist_ok=True)
ROOT = '/Users/bytedance/Documents/ChatGPT/DRAGON/assets'
H = np.load(f'{ROOT}/terrain/v3/base_heights.npy')
SITES = json.load(open(f'{ROOT}/terrain/v3/sites.json'))
PATH = json.load(open(f'{ROOT}/terrain/v3/path.json'))


def Gh(x, z):
    x = min(max(x, 0), 255.99)
    z = min(max(z, 0), 255.99)
    x0, z0 = int(x), int(z)
    fx, fz = x - x0, z - z0
    return float(H[z0, x0] * (1 - fx) * (1 - fz) + H[z0, x0 + 1] * fx * (1 - fz) + H[z0 + 1, x0] * (1 - fx) * fz + H[z0 + 1, x0 + 1] * fx * fz)


PINE_ROWS = [
    [(0, '#0a1f13'), (.35, '#13351f'), (.7, '#214d2b'), (1, '#3a6c3d')],  # 深绿
    [(0, '#0b2219'), (.35, '#143b2d'), (.7, '#235544'), (1, '#3f7560')],  # 蓝绿
    [(0, '#102412'), (.35, '#1f3f1d'), (.7, '#355a26'), (1, '#587c36')],  # 黄绿
    [(0, '#16301f'), (.4, '#2b5a3c'), (.72, '#93b7a4'), (1, '#f2f8fa')],  # 积雪
    [(0, '#1e1510'), (.5, '#40301f'), (1, '#6d543a')],  # 树皮
]


def unit(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) + 1e-9)


def skirt(g, cx, cz, top, R, drop, teeth, tone, row, rnd):
    """一层松枝：带锯齿的下垂裙边，顶面亮、边缘更亮，下面有暗面。"""
    a0 = rnd.uniform(0, math.tau)
    inner_r = R * .2
    inner_z = top - drop * .12
    outer, notch, inner = [], [], []
    for i in range(teeth):
        a = a0 + i / teeth * math.tau + rnd.uniform(-.1, .1)
        k = rnd.uniform(.7, 1.22)
        outer.append(np.array([cx + math.cos(a) * R * k, cz + math.sin(a) * R * k, top - drop * k * rnd.uniform(.85, 1.15)]))
        a2 = a + math.pi / teeth
        notch.append(np.array([cx + math.cos(a2) * R * .66, cz + math.sin(a2) * R * .66, top - drop * .56]))
        inner.append(np.array([cx + math.cos(a) * inner_r, cz + math.sin(a) * inner_r, inner_z]))
    for i in range(teeth):
        j = (i + 1) % teeth
        a = a0 + i / teeth * math.tau
        n = unit((math.cos(a), math.sin(a), 1.25))
        t_o = tone + rnd.uniform(.06, .26)
        t_i = tone - .24
        t_n = tone - .02
        g.tri(inner[i], outer[i], notch[i], (t_i, t_o, t_n), row, normals=[n] * 3)
        g.tri(inner[i], notch[i], inner[j], (t_i, t_n, t_i), row, normals=[n] * 3)
        g.tri(notch[i], outer[j], inner[j], (t_n, t_o, t_i), row, normals=[n] * 3)
    # 下面的暗面
    nd = np.array([0, 0, -1.0])
    c = np.array([cx, cz, inner_z - drop * .1])
    for i in range(0, teeth, 2):
        j = (i + 2) % teeth
        g.tri(c, notch[j], notch[i], tone - .26, row, normals=[nd] * 3)


def pine_near(g, x, z, y, ht, wd, rnd, row, row_top=None):
    """单棵松树：十来层下垂的枝叶裙，上小下大，每层参差不齐。"""
    levels = int(8 + ht * .34)
    base = max(3.1, ht * .27)
    tt = rnd.uniform(.42, .56)
    for lv in range(levels):
        t = lv / (levels - 1)
        topz = y + base + (ht - base) * (1 - (1 - t) ** 1.0) * .94 + ht * .06
        R = wd * (1 - t) ** .82 * rnd.uniform(.92, 1.08) + .22
        drop = ht / levels * (1.9 - .5 * t)
        teeth = 26 if t < .5 else 18 if t < .8 else 10
        cur = row_top if (row_top is not None and t > .25) else row
        ox, oz = rnd.uniform(-.05, .05) * wd, rnd.uniform(-.05, .05) * wd
        skirt(g, x + ox, z + oz, topz, R, drop, teeth, tt + t * .14, cur, rnd)


def frond(g, a, b, w, sag, t0, t1, row, nout):
    """一片细长针叶簇：菱形，中间略宽，末端下垂。"""
    m = (a + b) / 2 + np.array([0, 0, -sag])
    d = b - a
    s = np.cross(d, (0, 0, 1))
    ln = np.linalg.norm(s)
    if ln < 1e-6:
        return
    s = s / ln * w
    g.tri(a, m + s, b, (t0, (t0 + t1) / 2, t1), row, normals=[nout] * 3)
    g.tri(a, b, m - s, (t0, t1, (t0 + t1) / 2), row, normals=[nout] * 3)


def pine_fine(g, x, z, y, ht, wd, rnd, row, row_top=None):
    """精细松树：里面一层层暗色枝叶撑起体积，外面是一根根下垂的枝条和细长针叶簇。"""
    base = max(3.0, ht * .24)
    tt = rnd.uniform(.42, .56)
    a0 = rnd.uniform(0, math.tau)
    up = np.array([0, 0, 1.0])
    # 内层：暗色裙，低面数，只负责体积和遮挡
    inner = 6 + int(ht * .12)
    for lv in range(inner):
        t = lv / (inner - 1)
        topz = y + base + (ht - base) * (1 - (1 - t)) * .96 + ht * .05
        R = wd * .8 * (1 - t) ** .85 + .14
        cur = row_top if (row_top is not None and t > .3) else row
        skirt(g, x, z, topz, R, ht / inner * 1.8, 10 if t < .6 else 7, tt - .14 + t * .1, cur, rnd)
    # 外层：下垂的枝条
    levels = int(6 + ht * .28)
    for lv in range(levels):
        t = lv / (levels - 1)
        h0 = base + (ht - base) * t ** .95
        R = wd * 1.12 * (1 - t) ** .85 + .2
        cnt = 7 if t < .4 else 5 if t < .75 else 3
        cur = row_top if (row_top is not None and t > .22) else row
        for k in range(cnt):
            ang = a0 + (k + rnd.uniform(-.3, .3) + (lv % 2) * .5) / cnt * math.tau
            L = R * rnd.uniform(.85, 1.15)
            d = np.array([math.cos(ang), math.sin(ang), 0.0])
            sd = np.array([-d[1], d[0], 0.0])
            droop = (.46 - .3 * t) * rnd.uniform(.8, 1.2)
            root = np.array([x, z, y + h0 + rnd.uniform(-.1, .1)])

            def P(u):
                return root + d * L * u + up * (-droop * L * u * u + .1 * L * u * (1 - u))

            nout = unit(d * .55 + up * .85)
            tone = tt + t * .12 + rnd.uniform(-.06, .06)
            for u in (.3, .48, .64, .8):
                for sgn in (-1, 1):
                    a = P(u)
                    fl = L * (.5 - .24 * u) * rnd.uniform(.85, 1.15)
                    dirv = unit(d * .7 + sd * sgn * .8)
                    b = a + dirv * fl + up * (-.25 * fl)
                    frond(g, a, b, fl * .2, fl * .08, tone - .12 + u * .08, tone + .16 + u * .1, cur, nout)
            frond(g, P(.8), P(1.0) + d * L * .1, L * .08, L * .03, tone, tone + .26, cur, nout)
    g.tri(np.array([x - .08, z, y + ht - .4]), np.array([x + .08, z, y + ht - .4]), np.array([x, z, y + ht + .5]), (tt, tt, tt + .3), row_top if row_top is not None else row, normals=[up] * 3)


def pine_far(g, x, z, y, ht, wd, rnd, row, row_top=None):
    """远处的松树：三层带锯齿的枝叶裙。"""
    base = max(2.6, ht * .24)
    tt = rnd.uniform(.4, .5)
    for lv in range(3):
        t = lv / 2
        topz = y + base + (ht - base) * (.34 + t * .66)
        R = wd * (1 - t * .68)
        cur = row_top if (row_top is not None and t > .3) else row
        skirt(g, x, z, topz, R, (ht - base) * .5, 7, tt + t * .1, cur, rnd)


def trunk(g, x, z, y, ht, wd, rnd):
    rows, ctrs = [], []
    r0 = .13 + ht * .022
    for t, k in ((-.04, 1.25), (.05, 1.0), (.4, .72), (.8, .3)):
        c = np.array([x, z, y + ht * t])
        rows.append([c + np.array([math.cos(i / 6 * math.tau) * r0 * k, math.sin(i / 6 * math.tau) * r0 * k, 0]) for i in range(6)])
        ctrs.append(c)
    g.loft(rows, .5, 4, ctrs, cap=False, tone_fn=lambda i, k_: .45 + .3 * math.sin(k_ * 1.05 + x) ** 2)


# ---------- 松林
if 'trees' in what:
    all_trees = json.load(open(f'{ROOT}/forest2/trees.json'))
    rnd = random.Random(21)
    rnd.shuffle(all_trees)
    keep, occ = [], {}
    SP = 2.25  # 最小间距
    for x, z, y in all_trees:
        key = (int(x / SP), int(z / SP))
        if any((key[0] + a, key[1] + b) in occ for a in (-1, 0, 1) for b in (-1, 0, 1)):
            continue
        occ[key] = 1
        keep.append((x, z, y))
    # 保留林缘多样高度
    if len(keep) > 620:
        keep = keep[:620]
    print('trees kept', len(keep))
    specs = []
    for x, z, y in keep:
        ht = rnd.uniform(8.5, 16.5)
        wd = ht * rnd.uniform(.2, .27)
        row = rnd.choice((0, 0, 1, 2))
        top = 3 if y > 60 else None
        specs.append((x, z, y - .25, ht, wd, row, top, rnd.randrange(1 << 30)))
    # 引擎单个模型上限 3 万面：按棵数递归切块，每块不超过 34 棵
    def split(items):
        if len(items) <= 34:
            return [items]
        xs = [i[0] for i in items]
        zs = [i[1] for i in items]
        k = 0 if max(xs) - min(xs) > max(zs) - min(zs) else 1
        items = sorted(items, key=lambda i: i[k])
        m = len(items) // 2
        return split(items[:m]) + split(items[m:])

    base = {}
    for s_ in specs:
        base.setdefault((int(s_[0] // 64), int(s_[1] // 64)), []).append(s_)
    info = []
    for ss in [c for v in sorted(base.values(), key=lambda v: v[0][:2]) for c in split(v)]:
        g = Geo(PINE_ROWS)
        ox, oz = round(sum(i[0] for i in ss) / len(ss), 1), round(sum(i[1] for i in ss) / len(ss), 1)
        for x, z, y, ht, wd, row, top, seed in ss:
            pine_near(g, x - ox, z - oz, y, ht, wd, random.Random(seed), row, top)
        nm = f'pine_{len(info)}'
        t = write_glb(os.path.join(OUT, nm + '.glb'), g, name=nm, rough=.9)
        info.append(dict(name=nm, x=ox, z=oz, n=len(ss), tris=t))
        print(nm, len(ss), 'trees', t, 'tris', flush=True)
    # 近景精细版：每块不超过 19 棵（3 万面上限）
    def split2(items, cap):
        if len(items) <= cap:
            return [items]
        xs = [i[0] for i in items]
        zs = [i[1] for i in items]
        k = 0 if max(xs) - min(xs) > max(zs) - min(zs) else 1
        items = sorted(items, key=lambda i: i[k])
        m = len(items) // 2
        return split2(items[:m], cap) + split2(items[m:], cap)

    fine = []
    for ss in split2(specs, 19):
        g = Geo(PINE_ROWS)
        ox, oz = round(sum(i[0] for i in ss) / len(ss), 1), round(sum(i[1] for i in ss) / len(ss), 1)
        for x, z, y, ht, wd, row, top, seed in ss:
            pine_fine(g, x - ox, z - oz, y, ht, wd, random.Random(seed + 1), row, top)
        nm = f'pn_{len(fine)}'
        t = write_glb(os.path.join(OUT, nm + '.glb'), g, name=nm, rough=.9)
        fine.append(dict(name=nm, x=ox, z=oz, n=len(ss), tris=t))
    print('fine chunks', len(fine), 'max tris', max(f['tris'] for f in fine), 'total', sum(f['tris'] for f in fine))
    json.dump(fine, open(os.path.join(OUT, 'pines_fine.json'), 'w'))
    gf = Geo(PINE_ROWS)
    gt = Geo(PINE_ROWS)
    for x, z, y, ht, wd, row, top, seed in specs:
        r = random.Random(seed)
        trunk(gt, x - 128, z - 128, y, ht, wd, r)
    print('trunks', write_glb(os.path.join(OUT, 'pine_trunks.glb'), gt, name='pine_trunks', rough=.9))
    # 远景分块（3 万面上限）
    far = []
    for ss in split2(specs, 280):
        gf = Geo(PINE_ROWS)
        for x, z, y, ht, wd, row, top, seed in ss:
            pine_far(gf, x - 128, z - 128, y, ht, wd, random.Random(seed + 2), row, top)
        nm = f'pf_{len(far)}'
        far.append(nm)
        print(nm, write_glb(os.path.join(OUT, nm + '.glb'), gf, name=nm, rough=.9))
    json.dump(far, open(os.path.join(OUT, 'pines_far.json'), 'w'))
    json.dump(info, open(os.path.join(OUT, 'pines.json'), 'w'))

# ---------- 草和花
GR_ROWS = [
    [(0, '#16361a'), (.4, '#2e6a2a'), (.75, '#5a9c3e'), (1, '#9cc95c')],  # 草
    [(0, '#1a3a24'), (.4, '#2a6a44'), (.75, '#4f9a62'), (1, '#8fcb88')],  # 冷草
    [(0, '#2a3a18'), (.4, '#5a7328'), (.75, '#90a544'), (1, '#c8cc6a')],  # 枯黄草
    [(0, '#3d2a7a'), (.4, '#6f47c9'), (.75, '#a97ce8'), (1, '#e6d4fb')],  # 紫瓣
    [(0, '#7a2f8a'), (.5, '#c75cc8'), (1, '#f6c3ec')],  # 粉瓣
    [(0, '#c79a2a'), (1, '#ffe690')],  # 花心
    [(0, '#bdbbaa'), (1, '#ffffff')],  # 白瓣
]
UPN = np.array([0, 0, 1.0])


def blade(g, x, z, y, h, w, ang, lean, row, tone_top):
    """一根草叶：细长三角形。"""
    d = np.array([math.cos(ang), math.sin(ang), 0.0])
    s = np.array([-d[1], d[0], 0.0]) * w / 2
    b = np.array([x, z, y])
    t = b + UPN * h + d * lean
    n = unit(UPN + d * .35)
    g.tri(b - s, b + s, t, (.1, .1, tone_top), row, normals=[n] * 3)


def flower(g, x, z, y, h, r, row, rnd):
    """茎 + 五片花瓣 + 花心，全部是三角面。"""
    ang = rnd.uniform(0, math.tau)
    lean = rnd.uniform(-.06, .06)
    c = np.array([x + lean, z, y + h])
    s = np.array([math.cos(ang), math.sin(ang), 0]) * .018
    g.tri(np.array([x, z, y]) - s, np.array([x, z, y]) + s, c, (.15, .15, .55), 0, normals=[unit(UPN)] * 3)
    tilt = unit((rnd.uniform(-.4, .4), rnd.uniform(-.4, .4), 1))
    u = unit(np.cross(tilt, (1, 0, 0)))
    v = np.cross(tilt, u)
    for k in range(5):
        a = ang + k / 5 * math.tau
        o = u * math.cos(a) + v * math.sin(a)
        p = v * math.cos(a) - u * math.sin(a)
        tip = c + o * r + tilt * r * .3
        base = c + o * r * .2
        g.tri(base + p * r * .12, tip + p * r * .36, tip - p * r * .36, (.42, .86, .86), row, normals=[tilt] * 3)
    g.tri(c + u * r * .22, c + v * r * .22, c - u * r * .22 - v * r * .22, .6, 5, normals=[tilt] * 3)


if 'grass' in what:
    rnd = random.Random(5)
    R = 3.9
    VARS = dict(gr3_a=(3000, 0, None), gr3_b=(2500, 70, 6), gr3_c=(1500, 210, 3))
    for nm, (blades, flowers, frow) in VARS.items():
        g = Geo(GR_ROWS)
        for _ in range(blades):
            a, q = rnd.uniform(0, math.tau), R * math.sqrt(rnd.random())
            edge = 1 - .55 * (q / R) ** 4
            h = rnd.uniform(.16, .4) * edge
            blade(g, math.cos(a) * q, math.sin(a) * q, -.05, h, rnd.uniform(.05, .085), rnd.uniform(0, math.tau), h * rnd.uniform(.12, .55), rnd.choice((0, 0, 0, 1, 2)), rnd.uniform(.72, .98))
        for _ in range(flowers):
            a, q = rnd.uniform(0, math.tau), R * math.sqrt(rnd.random())
            row = frow if frow != 3 else rnd.choice((3, 3, 3, 4))
            flower(g, math.cos(a) * q, math.sin(a) * q, -.05, rnd.uniform(.26, .46) * (1 - .5 * (q / R) ** 4), rnd.uniform(.06, .1), row, rnd)
        t = write_glb(os.path.join(OUT, nm + '.glb'), g, name=nm, rough=.85)
        print(nm, t, 'tris', round(os.path.getsize(os.path.join(OUT, nm + '.glb')) / 1e6, 2), 'MB', flush=True)

# ---------- 圣树（真实树枝和叶子）
if 'holy' in what:
    rnd = random.Random(508)
    ROWS = [[(0, '#1a1214'), (.5, '#3a2a28'), (1, '#6a5046')], [(0, '#173222'), (.5, '#467449'), (1, '#8fac65')], [(0, '#23432a'), (.6, '#64834c'), (1, '#b0bb77')]]
    tr = Geo(ROWS)
    gl = Geo(ROWS)
    ends = []

    def tube(pts, radii, seg, tone=.5):
        pts = [np.asarray(p, float) for p in pts]
        rings = []
        for i, p in enumerate(pts):
            t = unit(pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)])
            s = unit(np.cross(t, (.3, .2, 1)))
            u = np.cross(t, s)
            rings.append([p + (s * math.cos(a) + u * math.sin(a)) * radii[i] for a in np.linspace(0, math.tau, seg, endpoint=False)])
        # 平滑法线
        for i in range(len(pts) - 1):
            for k in range(seg):
                k2 = (k + 1) % seg
                a, b, c, d = rings[i][k], rings[i + 1][k], rings[i + 1][k2], rings[i][k2]
                na, nb, nc, nd = unit(a - pts[i]), unit(b - pts[i + 1]), unit(c - pts[i + 1]), unit(d - pts[i])
                bark = tone + .28 * math.sin(k * 2.4 + i * 1.3) * .5
                tr.tri(a, b, c, bark, 0, ref=pts[i], normals=[na, nb, nc])
                tr.tri(a, c, d, bark, 0, ref=pts[i], normals=[na, nc, nd])

    def limb(start, direction, length, radius, depth):
        pts, radii = [np.asarray(start, float)], [radius]
        d = unit(direction)
        n = 7 if depth <= 1 else 4
        for i in range(n):
            d = unit(d + np.array([rnd.uniform(-.22, .22), rnd.uniform(-.22, .22), rnd.uniform(-.1, .1)]))
            pts.append(pts[-1] + d * length / n)
            radii.append(radius * (1 - (i + 1) / n * .66))
        tube(pts, radii, 12 if depth <= 1 else 7 if depth == 2 else 5)
        if depth < 4:
            for k in range(3 if depth < 3 else 2):
                o = rnd.randint(n // 2, n)
                a = rnd.uniform(0, math.tau)
                nd = unit(d * .55 + np.array([math.cos(a), math.sin(a), rnd.uniform(.03, .4)]))
                limb(pts[o], nd, length * rnd.uniform(.5, .68), radii[o] * .74, depth + 1)
        else:
            ends.append(pts[-1])

    tp, tr_ = [], []
    for i in range(14):
        t = i / 13
        ang = t * 1.2
        tp.append((math.cos(ang) * t * 1.3, math.sin(ang) * t * 1.3, t * 13.5 - .8))
        tr_.append(2.8 * (1 - t) ** 1.8 + 1.15)
    tube(tp, tr_, 20)
    for i in range(11):
        a = i / 11 * math.tau + rnd.uniform(-.2, .2)
        L = rnd.uniform(4.5, 8)
        rp = [(math.cos(a) * 1.6, math.sin(a) * 1.6, 2.5), (math.cos(a) * L * .32, math.sin(a) * L * .32, 1.0), (math.cos(a + .12) * L * .68, math.sin(a + .12) * L * .68, .15), (math.cos(a + .25) * L, math.sin(a + .25) * L, -.55)]
        tube(rp, [1.05, .72, .42, .14], 8)
    top = np.asarray(tp[-1])
    for i in range(7):
        a = i / 7 * math.tau + rnd.uniform(-.25, .25)
        limb(top, (math.cos(a), math.sin(a), rnd.uniform(.5, .95)), rnd.uniform(9, 11.5), 1.0, 1)
    print('holy ends', len(ends), 'bark tris', tr.tris_count())

    def leaf(c, s, row, tone):
        # 一片真实的叶子：两个三角形组成的菱形，叶面微折
        u = unit((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-.6, .2))) * s
        v = unit(np.cross(u, (rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)))) * s * .55
        n1 = unit(np.cross(u, v))
        if n1[2] < 0:
            n1 = -n1
        nmid = unit(n1 + (c - np.array([0, 0, 18])) * .04)
        gl.tri(c - u, c + v, c + u, tone, row, normals=[nmid] * 3)
        gl.tri(c - u, c + u, c - v, tone - .08, row, normals=[nmid] * 3)

    gl_b = Geo(ROWS)
    glow_trunk = gl
    for idx, e in enumerate(ends):
        target = gl if idx % 2 == 0 else gl_b
        gl_save = gl
        for _ in range(190 if idx % 2 else 165):
            off = np.array([rnd.gauss(0, 1.65), rnd.gauss(0, 1.65), rnd.gauss(0, .85)])
            d_ = float(np.linalg.norm(off / np.array([1.65, 1.65, .85])))
            tone = min(.98, .42 + .24 * d_ + rnd.uniform(-.08, .1))   # 内部暗、外缘亮，有层次
            u = unit((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-.6, .2)))
            sz = rnd.uniform(.2, .38)
            row_ = 2 if rnd.random() < .1 else 1
            if row_ == 2:
                sz *= .8
                tone = rnd.uniform(.55, .9)
            v = unit(np.cross(u, (rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)))) * sz * .55
            u = u * sz
            c = e + off
            n1 = unit(np.cross(u, v))
            if n1[2] < 0:
                n1 = -n1
            target.tri(c - u, c + v, c + u, tone, row_, normals=[n1] * 3)
            target.tri(c - u, c + u, c - v, tone - .08, row_, normals=[n1] * 3)
    for e in rnd.sample(ends, min(len(ends), 46)):
        L = rnd.uniform(3, 7.5)
        ox, oy = rnd.uniform(-2, 2), rnd.uniform(-2, 2)
        for i in range(int(L / .3)):
            t = i / (L / .3)
            c = e + np.array([ox + math.sin(t * 2.4) * .3, oy, -t * L])
            leaf(c, .24 * (1 - t * .4), 1, .85)
    print('holy tris', tr.tris_count(), gl.tris_count())
    write_glb(os.path.join(OUT, 'holy_tree3.glb'), tr, name='holy_tree3', rough=.85)
    print('canopy', gl.tris_count(), gl_b.tris_count())
    write_glb(os.path.join(OUT, 'holy_canopy3.glb'), gl, name='holy_canopy3', rough=.82)
    write_glb(os.path.join(OUT, 'holy_canopy4.glb'), gl_b, name='holy_canopy4', rough=.82)
