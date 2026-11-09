#!/usr/bin/env python3
"""第二步：按身体部位分区，用连续权重蒙皮（翅膀按离肩距离分环，不会撕裂）。输出 rig2.npz"""
import numpy as np, sys, json
Z = np.load('assets/dragon/ai/rig.npz')
pos, nrm, uv, idx = Z['pos'], Z['nrm'], Z['uv'], Z['idx']
n = len(pos)
x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
# 关节（原始坐标）
BODY = np.array([(0, .36, -.14), (0, .36, -.03), (0, .36, .07), (0, .36, .16)])
NECK = np.array([(0, .385, .2), (0, .375, .27), (0, .35, .32), (0, .3, .35)])
names = list(Z['names'])
P0 = Z['P']
TAIL = np.array([P0[names.index(f't{i}')] for i in range(1, 10)])
TAIL = np.vstack([BODY[0], TAIL])
SH = {'a': np.array([-.05, .46]), 'b': np.array([.05, .46])}
RING = np.array([0, .1, .22, .36, .55])
joints = []
def add(nm, p):
    joints.append((nm, np.array(p, float)))
    return len(joints) - 1
JB = [add(f'b{i}', p) for i, p in enumerate(BODY)]
JN = [add(f'n{i}', p) for i, p in enumerate(NECK)]
JT = [add(f't{i}', p) for i, p in enumerate(TAIL[1:])]
JL = add('leg', (0, .2, 0))
JW = {}
for s, c in SH.items():
    JW[s] = [add(f'{s}{k}', (c[0], c[1], .1)) for k in range(len(RING))]
j0 = np.zeros(n, int); j1 = np.zeros(n, int); wt = np.zeros(n)


def poly_param(p, line):
    """点到折线最近处：返回(段号, 段内比例, 距离)"""
    best = np.full(len(p), 1e9); seg = np.zeros(len(p), int); tt = np.zeros(len(p))
    for i in range(len(line) - 1):
        a, b = line[i], line[i + 1]
        ab = b - a
        t = np.clip(((p - a) * ab).sum(1) / (ab @ ab), 0, 1)
        d = np.linalg.norm(p - (a + ab * t[:, None]), axis=1)
        m = d < best
        best[m], seg[m], tt[m] = d[m], i, t[m]
    return seg, tt, best


seg_t, tt_t, d_t = poly_param(pos, TAIL)
wing_a = (x < -.055) & (y > .3) & (z > -.07) & (z < .26)
wing_b = (x > .055) & (y > .3) & (z > -.07) & (z < .26)
wing_a |= (x < -.04) & (y > .42) & (z > -.02) & (z < .24)
wing_b |= (x > .04) & (y > .42) & (z > -.02) & (z < .24)
wing = wing_a | wing_b
tail = ~wing & ((z < -.17) | (x < -.14)) & (d_t < .12)
neck = ~wing & ~tail & (z > .19) & (y > .25) & (np.abs(x) < .11)
legs = ~wing & ~tail & ~neck & (y < .3)
body = ~wing & ~tail & ~neck & ~legs
region = np.full(n, 1)
region[wing] = 0
region[neck] = 2
region[legs] = 2
print('regions wing/tail/body/neck/legs', wing.sum(), tail.sum(), body.sum(), neck.sum(), legs.sum())
# 身体：按 z 插值
for mask in (body,):
    f = np.interp(z[mask], BODY[:, 2], np.arange(len(BODY)))
    i0 = np.minimum(f.astype(int), len(BODY) - 2)
    j0[mask] = np.array(JB)[i0]; j1[mask] = np.array(JB)[i0 + 1]; wt[mask] = f - i0
# 尾巴
s_, t_ = seg_t[tail], tt_t[tail]
chain = [JB[0]] + JT
j0[tail] = np.array(chain)[s_]; j1[tail] = np.array(chain)[np.minimum(s_ + 1, len(chain) - 1)]; wt[tail] = t_
# 脖子和头
seg_n, tt_n, _ = poly_param(pos, NECK)
s_, t_ = seg_n[neck], tt_n[neck]
j0[neck] = np.array(JN)[s_]; j1[neck] = np.array(JN)[s_ + 1]; wt[neck] = t_
# 头部整块跟头骨
head = neck & (z > .325)
j0[head] = JN[3]; j1[head] = JN[3]; wt[head] = 0
# 腿：不动，大腿根和身体过渡
j0[legs] = JL; j1[legs] = JB[1]; wt[legs] = np.clip((y[legs] - .24) / .08, 0, 1)
# 翅膀：按离肩距离分环
for s, m in (('a', wing_a), ('b', wing_b)):
    c = SH[s]
    r = np.hypot(x[m] - c[0], y[m] - c[1])
    f = np.interp(r, RING, np.arange(len(RING)))
    i0 = np.minimum(f.astype(int), len(RING) - 2)
    arr = np.array(JW[s])
    j0[m] = arr[i0]; j1[m] = arr[i0 + 1]; wt[m] = f - i0
np.savez('assets/dragon/ai/rig2.npz', pos=pos, nrm=nrm, uv=uv, idx=idx, j0=j0, j1=j1, wt=wt, region=region, names=np.array([j[0] for j in joints]), jp=np.array([j[1] for j in joints]), JB=JB, JN=JN, JT=JT, JL=JL, JWa=JW['a'], JWb=JW['b'])
tr = region[idx].max(1)
print('joints', len(joints), 'tris per region', [(tr == k).sum() for k in range(3)])
from PIL import Image, ImageDraw
SP = '/tmp/'
cols = np.array([[230, 90, 90], [90, 200, 110], [90, 120, 240], [230, 200, 80], [160, 90, 220]])
lab = np.zeros(n, int); lab[tail] = 1; lab[body] = 2; lab[neck] = 3; lab[legs] = 4
for a, b, nm in ((0, 1, 'r2_xy.png'), (2, 1, 'r2_zy.png')):
    S = 800; im = Image.new('RGB', (S, S), (245, 245, 245)); d = ImageDraw.Draw(im)
    lo, hi = -.6, .95
    m_ = lambda u, v: ((u - lo) / (hi - lo) * S, S - (v - lo) / (hi - lo) * S)
    for t in idx:
        d.polygon([m_(pos[v, a], pos[v, b]) for v in t], fill=tuple(cols[lab[t[0]]]))
    im.save(SP + nm)
