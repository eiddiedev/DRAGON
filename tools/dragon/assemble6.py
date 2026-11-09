#!/usr/bin/env python3
"""把烘好的贴图、蒙皮和动画拼成最终模型。输出 assets/dragon/final/{shd_w,shd_b,shd_h}.glb"""
import sys, json, math, os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as nd
sys.path.insert(0, 'tools/models')
from glbw import Geo, write_glb, Rigid, q_rot, q_axis, q_mul
ROOT = 'assets/dragon/ai'
OUT = 'assets/dragon/final'
os.makedirs(OUT, exist_ok=True)
Z = np.load(f'{ROOT}/rig2.npz')
S = 63.0
pos, nrm = Z['pos'], Z['nrm']
j0, j1, wt = Z['j0'], Z['j1'], Z['wt']


def D(v):
    """原始坐标 → 设计坐标（东 x，北 -z，上 y），并放大到真实尺寸"""
    v = np.asarray(v, float)
    return np.stack([v[..., 0], -v[..., 2], v[..., 1]], -1)


names = [str(n) for n in Z['names']]
for k, j in enumerate(Z['JWb']):
    names[int(j)] = f'c{k}'
jp = D(Z['jp']) * S
joints = list(zip(names, jp))
JB, JN, JT, JL = list(Z['JB']), list(Z['JN']), list(Z['JT']), int(Z['JL'])
JWa, JWb = list(Z['JWa']), list(Z['JWb'])
# ---------- 动画：16 秒
FPS, DUR = 8, 16.0
Nf = int(DUR * FPS) + 1
times = np.linspace(0, DUR, Nf)
POS = np.zeros((Nf, len(joints), 3)); ROT = np.zeros((Nf, len(joints), 4))
UP = np.array([0, 0, 1.0]); AX = np.array([0, 1.0, 0]); EAST = np.array([1.0, 0, 0])
for f, t in enumerate(times):
    ph = t / DUR * math.tau
    roar = max(0.0, math.sin((t - 9) / 5 * math.pi)) ** 1.3 if 9 < t < 14 else 0.0
    # 身体：呼吸
    M = Rigid()
    breathe = math.sin(ph * 4)
    Mb = []
    for k, j in enumerate(JB):
        m = Rigid(t=UP * breathe * .1 * k / 3 + UP * roar * .35 * k / 3)
        Mb.append(m)
        POS[f, j] = m.apply(jp[j]); ROT[f, j] = m.q
    # 脖子：摆动，吼的时候抬起
    M = Mb[-1]
    for k, j in enumerate(JN):
        pan = (.05 * math.sin(ph) + .02 * math.sin(ph * 3 + 1)) * (.6 + k * .35)
        nod = (.018 * math.sin(ph * 2 + .6) + .1 * roar) * (.6 + k * .35)
        M = Rigid.about(jp[j], UP, pan).then(Rigid.about(jp[j], EAST, nod)).then(M)
        POS[f, j] = M.apply(jp[j]); ROT[f, j] = M.q
    # 尾巴：行波，越到尾尖越大
    M = Mb[0]
    for k, j in enumerate(JT):
        a = (.012 + .012 * k) * math.sin(ph * 2 - k * .7)
        M = Rigid.about(jp[j], UP, a).then(M)
        POS[f, j] = M.apply(jp[j]); ROT[f, j] = M.q
    # 腿：不动
    POS[f, JL] = jp[JL]; ROT[f, JL] = (1, 0, 0, 0)
    # 翅膀：慢拍，环与环之间有滞后，翼尖最大
    for arr, sgn in ((JWa, -1), (JWb, 1)):
        M = Mb[-1]
        for k, j in enumerate(arr):
            local = (.05 + .012 * k) * math.sin(ph * 2 - k * .42) + .012 * math.sin(ph) + .035 * roar
            M = Rigid.about(jp[j], AX, local * -sgn).then(M)
            POS[f, j] = M.apply(jp[j]); ROT[f, j] = M.q
POS[-1] = POS[0]; ROT[-1] = ROT[0]
CLIP = dict(idle=dict(times=times, pos=POS, rot=ROT))
# ---------- 贴图合成
PARTS = [('shd_wa', 0), ('shd_wb', 1), ('shd_body', 2), ('shd_tail', 3), ('shd_head', 4), ('shd_legs', 5)]
for nm, part in PARTS:
    col = np.asarray(Image.open(f'{ROOT}/bake6/p{part}_color.png').convert('RGB')).astype(float) / 255
    mask = np.asarray(Image.open(f'{ROOT}/bake6/p{part}_mask.png').convert('RGB')).astype(float) / 255
    edge, cell, ao = mask[..., 0], mask[..., 1], mask[..., 2]
    # 紫色区域保留、提亮；其余压成黑紫色
    purple = np.clip((col[..., 2] - col[..., 1] * 1.25) * 6, 0, 1)
    purple = nd.gaussian_filter(purple, 1.2)[..., None]
    lum = col.mean(2, keepdims=True)
    tint = np.array([.92, .88, 1.18])
    aoi = (.4 + .6 * ao[..., None])
    if part < 2:   # 翼膜：暗皮革，骨边略亮，少量皱纹
        wr = np.clip(edge * 6, 0, 1)[..., None]
        out = (lum * .34 + .012) * tint * (.8 + .3 * wr) * (1 + (cell[..., None] - .5) * .18) * aoi
    else:           # 鳞片：缝隙近黑，片心带冷色高光，每片明暗不同
        dome = np.clip(edge * 9, 0, 1)[..., None] ** .7
        cv = 1 + (cell[..., None] - .5) * .9
        out = (.018 + lum * .05 + .105 * dome * dome) * tint * cv * aoi
        out = out * (.25 + .75 * np.clip(edge * 22, 0, 1)[..., None])
    glow = np.array([.62, .22, 1.0]) * (.55 + .7 * lum)
    if part > 1:
        glow = glow * (.45 + .75 * np.clip(edge * 10, 0, 1)[..., None])
    out = out * (1 - purple) + glow * purple
    img = Image.fromarray((out.clip(0, 1) * 255).astype(np.uint8)).resize((1024, 1024), Image.LANCZOS)
    img.save(f'{OUT}/{nm}.png')
    # 组装几何
    B = np.load(f'{ROOT}/bake6/p{part}_uv.npz')
    used, tv, corner = B['used'], B['tv'], B['corner']
    g = Geo([[(0, '#ffffff'), (1, '#ffffff')]])
    vid = used[tv]  # 三角形数×3 的原始顶点号
    P = D(pos[vid]) * S
    Nn = D(nrm[vid])
    T = corner.copy()
    T[..., 1] = 1 - T[..., 1]
    g.P = P.reshape(-1, 3)
    g.N = Nn.reshape(-1, 3)
    g.T = T.reshape(-1, 2)
    jj0, jj1, ww = j0[vid].reshape(-1), j1[vid].reshape(-1), wt[vid].reshape(-1)
    g.J = np.stack([jj0, jj1, np.zeros_like(jj0), np.zeros_like(jj0)], 1)
    w1 = np.round(ww * 255).astype(int)
    g.W = np.stack([255 - w1, w1, np.zeros_like(w1), np.zeros_like(w1)], 1)
    tr = write_glb(f'{OUT}/{nm}.glb', g, joints, CLIP, name=nm, rough=.55, metal=.05, image=img, emissive=(.3, .3, .3) if part > 1 else (.16, .16, .16))
    print(nm, tr, 'tris', round(os.path.getsize(f'{OUT}/{nm}.glb') / 1e6, 2), 'MB')
allp = D(pos) * S
print('bounds', allp.min(0).round(1), allp.max(0).round(1))
json.dump(dict(S=S, bounds=[allp.min(0).tolist(), allp.max(0).tolist()]), open(f'{OUT}/dragon.json', 'w'))
