#!/usr/bin/env python3
"""真烟花：升空的亮点，炸开成几十颗带尾巴的火星，减速、下坠、闪烁、熄灭。每颗火星是一根骨骼。"""
import math, os, random, sys
import numpy as np
sys.path.insert(0, 'tools/models')
from glbw import Geo, write_glb
OUT = 'assets/fireworks'
os.makedirs(OUT, exist_ok=True)
FPS = 15


def fib(n, rnd):
    res = []
    for i in range(n):
        y = 1 - 2 * (i + .5) / n
        r = math.sqrt(max(0, 1 - y * y))
        a = i * 2.39996 + rnd.uniform(-.12, .12)
        v = np.array([math.cos(a) * r, math.sin(a) * r, y]) + np.array([rnd.uniform(-.08, .08) for _ in range(3)])
        res.append(v / np.linalg.norm(v))
    return res


def build(name, rows, cycle, shells, seed):
    """shells: [dict(t0, c, n, R, row, g, life, tail, w)]，t0 炸开时刻，c 炸开位置"""
    rnd = random.Random(seed)
    geo = Geo(rows)
    sparks = []
    for sh in shells:
        # 升空的亮点
        if sh.get('rise', True):
            j = len(sparks)
            sparks.append(dict(kind='rise', sh=sh))
            geo.skin = (j, j, 0)
            d = np.array([0, 0, 1.0])
            geo.cone(np.array([0, 0, -9.0]), np.array([0, 0, 1.4]), 1.0, up=(1, 0, 0), seg=3, tone=.2, row=sh['row'], tip_tone=.97)
        for d in fib(sh['n'], rnd):
            j = len(sparks)
            k = rnd.uniform(.86, 1.08)
            sparks.append(dict(kind='spark', sh=sh, d=d, k=k, tw=rnd.uniform(0, 6.28)))
            geo.skin = (j, j, 0)
            tail = sh['tail'] * rnd.uniform(.8, 1.15)
            geo.cone(-d * tail, d * 1.1, sh['w'], up=(0.3, .5, .8), seg=3, tone=.14, row=sh['row'], tip_tone=.97)
    joints = [(f's{i}', np.zeros(3)) for i in range(len(sparks))]
    Nf = int(cycle * FPS) + 1
    times = np.linspace(0, cycle, Nf)
    POS = np.zeros((Nf, len(sparks), 3)); ROT = np.zeros((Nf, len(sparks), 4)); ROT[..., 0] = 1
    SCL = np.zeros((Nf, len(sparks)))
    for f, t in enumerate(times):
        for j, s in enumerate(sparks):
            sh = s['sh']
            c = np.array(sh['c'], float)
            if s['kind'] == 'rise':
                t1 = sh['t0'] - 1.1
                if t1 <= t < sh['t0']:
                    e = (t - t1) / 1.1
                    e = 1 - (1 - e) ** 2
                    POS[f, j] = c + np.array([math.sin(e * 5) * 1.2, 0, -72 * (1 - e)])
                    SCL[f, j] = 1
                else:
                    POS[f, j] = c
            else:
                u = t - sh['t0']
                POS[f, j] = c
                if u < 0 or u > sh['life']:
                    continue
                r = sh['R'] * s['k'] * (1 - math.exp(-2.7 * u))
                POS[f, j] = c + s['d'] * r + np.array([0, 0, -.5 * sh['g'] * u * u])
                fade = 1.0 if u < sh['life'] * .55 else max(0.0, 1 - (u - sh['life'] * .55) / (sh['life'] * .45))
                tw = 1.0 if u < sh['life'] * .4 else .55 + .45 * math.sin(u * 19 + s['tw'])
                SCL[f, j] = min(1.0, u * 9 + .25) * fade * tw
    tr = write_glb(f'{OUT}/{name}.glb', geo, joints, dict(idle=dict(times=times, pos=POS, rot=ROT, scale=SCL)), name=name, rough=1.0, metal=0, emissive=(1, 1, 1))
    print(name, tr, 'tris', len(sparks), 'bones', round(os.path.getsize(f'{OUT}/{name}.glb') / 1e6, 2), 'MB')


GOLD = [(0, '#ff5a10'), (.5, '#ffb030'), (1, '#fffbe0')]
RED = [(0, '#c0103a'), (.5, '#ff4060'), (1, '#fff0f0')]
VIOLET = [(0, '#5020d0'), (.5, '#a060ff'), (1, '#fbf0ff')]
CYAN = [(0, '#1060d0'), (.5, '#40c0ff'), (1, '#f0ffff')]
GREEN = [(0, '#109050'), (.5, '#50ff90'), (1, '#f4fff4')]
build('fwx_a', [GOLD, RED], 8.5, [
    dict(t0=1.2, c=(0, 0, 0), n=46, R=46, row=0, g=7, life=2.7, tail=9, w=.75),
    dict(t0=1.35, c=(0, 0, 0), n=20, R=22, row=1, g=7, life=2.0, tail=5, w=.7, rise=False)], 11)
build('fwx_b', [VIOLET, CYAN], 10.5, [
    dict(t0=1.2, c=(0, 0, 0), n=40, R=42, row=0, g=6, life=2.6, tail=8, w=.75),
    dict(t0=3.0, c=(34, 0, 22), n=26, R=28, row=1, g=6, life=2.2, tail=6, w=.7)], 12)
build('fwx_c', [GOLD, GREEN], 12.5, [   # 柳枝：拖得长，慢慢垂下来
    dict(t0=1.2, c=(0, 0, 0), n=44, R=38, row=0, g=15, life=4.0, tail=13, w=.65),
    dict(t0=4.6, c=(-30, 0, 16), n=24, R=25, row=1, g=6, life=2.2, tail=6, w=.7)], 13)
