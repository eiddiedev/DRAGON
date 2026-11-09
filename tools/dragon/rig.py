#!/usr/bin/env python3
"""给 AI 生成的黑龙绑骨骼：关节位置手工给初值，再吸附到附近网格的中心；蒙皮权重按网格上的测地距离算。
输出 assets/dragon/ai/rig.npz"""
import sys, os, json
import numpy as np
from scipy import sparse
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
sys.path.insert(0, os.path.dirname(__file__))
from load import load_glb
OUT = 'assets/dragon/ai'
pos, nrm, uv, idx, img = load_glb(f'{OUT}/hero_raw.glb')
img.save(f'{OUT}/hero_base.png')
# 切掉 AI 误生成的三脚架（前爪下方），前爪改踩真的岩石
tv = (pos[:, 1] < .205) & (pos[:, 2] > .118)
keep_tri = ~tv[idx].all(1)
idx = idx[keep_tri]
used = np.unique(idx)
remap = -np.ones(len(pos), int)
remap[used] = np.arange(len(used))
pos, nrm, uv = pos[used], nrm[used], uv[used]
idx = remap[idx]
print('after tripod cut', len(pos), len(idx))
# 关节：名字, 父, 初值(x,y,z), 吸附半径
J = [
    ('hip', None, (0, .33, -.12), .06),
    ('sp1', 'hip', (0, .35, -.02), .06),
    ('sp2', 'sp1', (0, .37, .07), .06),
    ('chest', 'sp2', (0, .38, .14), .06),
    ('nk1', 'chest', (0, .39, .2), .045),
    ('nk2', 'nk1', (0, .38, .26), .035),
    ('nk3', 'nk2', (0, .36, .31), .03),
    ('head', 'nk3', (0, .31, .345), .03),
    ('snout', 'head', (0, .27, .365), .02),
    ('t1', 'hip', (-.01, .32, -.21), .05),
    ('t2', 't1', (-.05, .29, -.3), .04),
    ('t3', 't2', (-.12, .25, -.35), .035),
    ('t4', 't3', (-.22, .21, -.36), .03),
    ('t5', 't4', (-.32, .17, -.3), .03),
    ('t6', 't5', (-.42, .12, -.2), .025),
    ('t7', 't6', (-.48, .08, -.09), .025),
    ('t8', 't7', (-.48, .05, 0), .02),
    ('t9', 't8', (-.43, .03, .07), .015),
    ('fl', 'chest', (.06, .31, .17), .04),
    ('fl2', 'fl', (.05, .23, .21), .03),
    ('fr', 'chest', (-.06, .31, .17), .04),
    ('fr2', 'fr', (-.05, .23, .21), .03),
    ('hl', 'hip', (.1, .26, -.09), .05),
    ('hl2', 'hl', (.11, .07, -.09), .035),
    ('hr', 'hip', (-.11, .26, -.09), .05),
    ('hr2', 'hr', (-.11, .07, -.09), .035),
    ('as', 'chest', (-.06, .46, .1), .04),
    ('ae', 'as', (-.12, .6, .13), .03),
    ('aw', 'ae', (-.12, .76, .17), .025),
    ('af0', 'aw', (-.35, .63, .2), .02),
    ('af1', 'aw', (-.46, .38, .15), .018),
    ('af2', 'aw', (-.42, .32, .08), .018),
    ('af3', 'aw', (-.34, .31, .03), .018),
    ('bs', 'chest', (.06, .46, .1), .04),
    ('be', 'bs', (.14, .54, .1), .03),
    ('bw', 'be', (.2, .68, .1), .025),
    ('bf0', 'bw', (.4, .56, .17), .02),
    ('bf1', 'bw', (.48, .37, .2), .018),
    ('bf2', 'bw', (.44, .36, .14), .018),
    ('bf3', 'bw', (.33, .31, .04), .018),
]
names = [j[0] for j in J]
tree = cKDTree(pos)
P = []
for n, par, g, r in J:
    g = np.array(g, float)
    c = g
    if not tree.query_ball_point(c, r):
        c = pos[tree.query(c)[1]]
    for _ in range(3):
        ids = tree.query_ball_point(c, r)
        if ids:
            c = pos[ids].mean(0)
    P.append(c)
    print(n, np.round(g, 2), '->', np.round(c, 3), len(ids))
P = np.array(P)
parents = [names.index(j[1]) if j[1] else -1 for j in J]
# 网格图
e = np.vstack([idx[:, [0, 1]], idx[:, [1, 2]], idx[:, [2, 0]]])
w = np.linalg.norm(pos[e[:, 0]] - pos[e[:, 1]], axis=1)
n = len(pos)
G = sparse.coo_matrix((np.r_[w, w], (np.r_[e[:, 0], e[:, 1]], np.r_[e[:, 1], e[:, 0]])), shape=(n, n)).tocsr()
ncomp, labels = sparse.csgraph.connected_components(G, directed=False)
print('components', ncomp, np.bincount(labels)[:8])
# 把重合的顶点也连起来（UV 接缝处顶点是分开的）
pairs = tree.query_pairs(1e-5, output_type='ndarray')
print('coincident pairs', len(pairs))
if len(pairs):
    G = G + sparse.coo_matrix((np.full(len(pairs) * 2, 1e-5), (np.r_[pairs[:, 0], pairs[:, 1]], np.r_[pairs[:, 1], pairs[:, 0]])), shape=(n, n)).tocsr()
ncomp, labels = sparse.csgraph.connected_components(G, directed=False)
print('components after weld', ncomp)
# 再把相近的小孤岛连上最近的主体
sizes = np.bincount(labels)
main = sizes.argmax()
if ncomp > 1:
    mt = cKDTree(pos[labels == main])
    mid = np.where(labels == main)[0]
    extra = []
    for c in range(ncomp):
        if c == main:
            continue
        ids = np.where(labels == c)[0]
        d, j = mt.query(pos[ids])
        k = d.argmin()
        extra.append((ids[k], mid[j[k]], d[k]))
    ex = np.array(extra)
    G = G + sparse.coo_matrix((np.r_[ex[:, 2] + 1e-5, ex[:, 2] + 1e-5], (np.r_[ex[:, 0], ex[:, 1]].astype(int), np.r_[ex[:, 1], ex[:, 0]].astype(int))), shape=(n, n)).tocsr()


def seg_dist(p, a, b):
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab + 1e-12), 0, 1)
    return np.linalg.norm(p - (a + ab * t[:, None]), axis=1)


# 每根骨骼一段：关节 → 它的第一个子节点（没有子节点就是一个点）
kids = {i: [k for k, p in enumerate(parents) if p == i] for i in range(len(J))}
D = np.zeros((len(J), n))
for i in range(len(J)):
    a = P[i]
    ends = [P[k] for k in kids[i]] or [a]
    # 手指骨是腕到指尖：权重挂在指尖关节上
    pa = parents[i]
    if names[i][1:2] == 'f' and names[i][0] in 'ab':
        seg = (P[pa], a)
    else:
        seg = (a, ends[0])
    d0 = seg_dist(pos, seg[0], seg[1])
    seeds = np.where(d0 < d0.min() + .008)[0]
    if len(seeds) == 0:
        seeds = np.array([d0.argmin()])
    # 手指骨沿线的种子
    if names[i][1:2] == 'f' and names[i][0] in 'ab':
        seeds = np.where(d0 < .012)[0]
        if len(seeds) == 0:
            seeds = np.array([d0.argmin()])
    d = dijkstra(G, indices=seeds, min_only=True)
    d[~np.isfinite(d)] = 9
    D[i] = d
W = 1 / (D + .008) ** 4
order = np.argsort(-W, axis=0)
top2 = order[:2]
j0, j1 = top2[0], top2[1]
w0 = W[j0, np.arange(n)]
w1 = W[j1, np.arange(n)]
wt = w1 / (w0 + w1)
print('main bone usage', {names[i]: int((j0 == i).sum()) for i in range(len(J))})
# 分三个部件：翅膀 / 身体尾巴 / 头颈和腿
part = np.ones(n, int)
for i, nm in enumerate(names):
    if nm[0] in 'ab' and nm[1] in 'sewf':
        part[j0 == i] = 0
    if nm in ('nk1', 'nk2', 'nk3', 'head', 'snout', 'fl', 'fl2', 'fr', 'fr2', 'hl', 'hl2', 'hr', 'hr2'):
        part[j0 == i] = 2
np.savez(f'{OUT}/rig.npz', P=P, parents=np.array(parents), names=np.array(names), j0=j0, j1=j1, wt=wt, part=part, pos=pos, nrm=nrm, uv=uv, idx=idx)
print('parts', np.bincount(part), 'tris', [int((part[idx].max(1) == p).sum()) for p in range(3)])
# 可视化：按主骨上色
from PIL import Image, ImageDraw
np.random.seed(3)
cols = (np.random.rand(len(J), 3) * 200 + 40).astype(int)
for a, b, nm in ((2, 1, 'rig_zy.png'), (0, 1, 'rig_xy.png')):
    S = 900
    im = Image.new('RGB', (S, S), (245, 245, 245)); d = ImageDraw.Draw(im)
    lo, hi = -.6, .95
    m = lambda x, y: ((x - lo) / (hi - lo) * S, S - (y - lo) / (hi - lo) * S)
    for t in idx:
        d.polygon([m(pos[v, a], pos[v, b]) for v in t], fill=tuple(cols[j0[t[0]]]))
    for i, q in enumerate(P):
        x, y = m(q[a], q[b]); d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(0, 0, 0)); d.text((x + 4, y - 4), names[i], fill=(0, 0, 0))
        if parents[i] >= 0:
            d.line([m(P[parents[i]][a], P[parents[i]][b]), (x, y)], fill=(255, 255, 255), width=1)
    im.save('/tmp/' + nm)
