#!/usr/bin/env python3
"""冰晶巨龙（西方龙）：站在山尖，前身高抬，脖子成 S 形向前低探，双翼高举，尾巴垂在身后。
真骨骼蒙皮，带循环动画。原点在山顶 (165, 242)，高度用绝对海拔。
用法：ice_dragon.py <输出目录>"""
import json
import math
import os
import random
import sys

import numpy as np
from scipy import ndimage as nd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glbw import Geo, Rigid, q_between, q_rot, write_glb

OUT = sys.argv[1]
H = np.load('/Users/a1234/Documents/awesomeWRLD/assets/terrain/v3/base_heights.npy')
OX, OZ = 165.0, 242.0
rnd = random.Random(9)


SCALE = .72   # 整体缩放，绕山尖 (3, -2, 118)；出生点才看得到整条龙
PX, PZ, PY = 3.0, -2.0, 118.0


def G(x, z):
    wx, wz = PX + (x - PX) * SCALE, PZ + (z - PZ) * SCALE
    h = float(nd.map_coordinates(H, [[min(wz + OZ, 255.9)], [min(max(wx + OX, 0), 255.9)]], order=1)[0])
    return PY + (h - PY) / SCALE


ROWS = [
    [(0, '#3a6ea3'), (.35, '#74abd6'), (.65, '#b2def4'), (.85, '#e2f6fd'), (1, '#ffffff')],  # 0 甲片
    [(0, '#5d7f9c'), (.5, '#b8d4e5'), (1, '#f4fbff')],  # 1 腹甲
    [(0, '#4a86b6'), (.4, '#86c0e2'), (.7, '#c2e8f7'), (1, '#f4fcff')],  # 2 翼膜
    [(0, '#22354c'), (.45, '#6d8dab'), (.8, '#c4e3f3'), (1, '#ffffff')],  # 3 角、爪、翼骨
    [(0, '#7ff4ff'), (1, '#e6ffff')],  # 4 眼睛
    [(0, '#1f1b2c'), (1, '#54405e')],  # 5 口腔
    [(0, '#b4cad6'), (1, '#ffffff')],  # 6 牙
]
geo = Geo(ROWS)


def catmull(pts, per=14):
    p = np.array(pts, float)
    p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        for s in np.linspace(0, 1, per, endpoint=False):
            a, b, c, d = p[i - 1], p[i], p[i + 1], p[i + 2]
            out.append(.5 * (2 * b + (c - a) * s + (2 * a - 5 * b + 4 * c - d) * s * s + (3 * b - a - 3 * c + d) * s ** 3))
    out.append(p[-2])
    return np.array(out)


def resample(C, step):
    seg = np.linalg.norm(np.diff(C, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.arange(0, s[-1], step)
    return np.stack([np.interp(t, s, C[:, k]) for k in range(C.shape[1])], 1), s[-1]


# ---------- 龙盘踞的尖峰（高度场）
SC_X, SC_Z = 3.0, -2.0
TOP, BASE, RB = 118.0, 58.0, 40.0


def crag(th, r):
    return 1.2 * math.sin(th * 5 + r * .23) + .9 * math.sin(th * 11 - r * .41 + 1.3) + .5 * math.sin(th * 23 + r * .9)


def spire_h(x, z):
    dx, dz = x - SC_X, z - SC_Z
    r = math.hypot(dx, dz)
    th = math.atan2(dz, dx)
    rb = RB * (1 + .12 * math.sin(3 * th + 1) + .06 * math.sin(7 * th))
    if r > rb * 1.5:
        return -1e9
    return TOP - (TOP - BASE) * (r / rb) ** 1.25 + crag(th, r) * min(1, r / 8)


def G2(x, z):
    return max(G(x, z), spire_h(x, z))


# ---------- 姿势：身体朝西南（从出生点看是 3/4 侧面），前腿抓山尖，胸口高、臀部低
F2 = np.array([-.9, -.44, 0.0])
F2 = F2 / np.linalg.norm(F2)
UP = np.array([0, 0, 1.0])
SIDE = np.cross(F2, UP)
CHEST = np.array([-1.0, -5.0, 128.0])
HIPS = CHEST - F2 * 20 + UP * -15
# 尾巴：从臀部往后，绕到东面，再横过南坡，尾尖卷在西南。高度跟着山体走
TAIL_XZ = [(31, 8), (39, 10), (45, 5), (47, -4), (42, -12), (34, -13)]
tail_xz = catmull([tuple(HIPS[:2])] + TAIL_XZ, 8)
tail_xz, _ = resample(tail_xz, .8)
tail_y = np.array([G2(x, z) for x, z in tail_xz])
tl = len(tail_xz)
# 尾根离开臀部的高度平滑过渡到贴地
w = np.clip(np.arange(tl) / (tl * .22), 0, 1)
w = w * w * (3 - 2 * w)
rad_t = 4.0 * (1 - np.arange(tl) / (tl - 1)) ** 1.0 + .1
tail_y = (HIPS[2]) * (1 - w) + (tail_y + rad_t * .75) * w
tail_y = nd.gaussian_filter1d(tail_y, 4, mode='nearest')
tail = np.column_stack([tail_xz, tail_y])[::-1]  # 尾尖在前
torso = catmull([HIPS, HIPS + F2 * 5 + UP * 3.2, CHEST - F2 * 7 - UP * 3.8, CHEST], 8)
neck_c = [CHEST, CHEST + F2 * 3 + UP * 7, CHEST + F2 * 4.5 + UP * 15, CHEST + F2 * 8 + UP * 20, CHEST + F2 * 14 + UP * 20, CHEST + F2 * 20 + UP * 15, CHEST + F2 * 25 + UP * 9]
neck_p = catmull(neck_c, 8)
all_pts = np.vstack([tail, torso[1:], neck_p[1:]])
spine, total = resample(all_pts, .7)
n = len(spine)
seg = np.linalg.norm(np.diff(all_pts, axis=0), axis=1)
L_tail = np.linalg.norm(np.diff(tail, axis=0), axis=1).sum()
L_torso = np.linalg.norm(np.diff(torso, axis=0), axis=1).sum()
L_neck = total - L_tail - L_torso
sv = np.arange(n) * .7
print('tail', round(L_tail, 1), 'torso', round(L_torso, 1), 'neck', round(L_neck, 1))
# 半径（水平, 竖直），按弧长插值：尾尖细、臀部粗、腰略收、胸最粗、脖子收细
S_KEYS = [0, L_tail * .5, L_tail, L_tail + L_torso * .22, L_tail + L_torso * .55, L_tail + L_torso * .9, L_tail + L_torso + L_neck * .25, L_tail + L_torso + L_neck * .7, total]
RW = np.interp(sv, S_KEYS, [.1, 2.6, 6.2, 7.0, 6.0, 7.8, 5.0, 2.8, 1.5])
RH = np.interp(sv, S_KEYS, [.1, 2.6, 6.4, 7.6, 6.6, 9.0, 5.8, 3.2, 1.7])
RW = nd.gaussian_filter1d(RW, 4, mode='nearest')
RH = nd.gaussian_filter1d(RH, 4, mode='nearest')
# 平行输运标架，脖子竖起来时也不翻转
tan = np.gradient(spine, axis=0)
tan /= np.linalg.norm(tan, axis=1, keepdims=True)
side = np.zeros((n, 3))
nrm = np.zeros((n, 3))
s0 = np.cross(tan[0], UP)
s0 /= np.linalg.norm(s0)
side[0] = s0
nrm[0] = np.cross(s0, tan[0])
for i in range(1, n):
    v = side[i - 1] - tan[i] * np.dot(side[i - 1], tan[i])
    v /= np.linalg.norm(v)
    side[i] = v
    nrm[i] = np.cross(v, tan[i])
# 把背部方向转到朝上：统一转一个固定角，让躯干中点的 nrm 朝上
mid = int((L_tail + L_torso * .5) / .7)
ang = math.atan2(np.dot(UP, side[mid]), np.dot(UP, nrm[mid]))
c_, s_ = math.cos(ang), math.sin(ang)
side, nrm = side * c_ - nrm * s_, side * s_ + nrm * c_
# ---------- 骨骼
joints = []
J_SP = []
sp_idx = []
s = 0.0
while True:
    if s < L_tail:
        step = 6.0
    elif s < L_tail + L_torso:
        step = 5.0
    else:
        step = 3.6
    sp_idx.append(min(int(s / .7), n - 1))
    if sp_idx[-1] >= n - 1:
        break
    s += step
for k, i in enumerate(sp_idx):
    J_SP.append(len(joints))
    joints.append((f's{k}', spine[i].copy()))


def sp_skin(i):
    f = np.searchsorted(sp_idx, i, side='right') - 1
    f = min(f, len(sp_idx) - 2)
    a, b = sp_idx[f], sp_idx[f + 1]
    return (J_SP[f], J_SP[f + 1], (i - a) / (b - a))


# 底管：颜色和甲片接近，甲片之间不会露出黑缝
RING = 14
rings, skins, ctrs = [], [], []
for i in range(0, n, 2):
    rings.append([spine[i] + side[i] * math.cos(k / RING * math.tau) * RW[i] * .97 + nrm[i] * math.sin(k / RING * math.tau) * RH[i] * .97 for k in range(RING)])
    skins.append(sp_skin(i))
    ctrs.append(spine[i])
geo.loft(rings, .55, 0, ctrs, skins, tone_fn=lambda i, k: .58 + .12 * math.sin(k / RING * math.tau))


def plate(c, along, sd, nr, L, W, h, tone, row=0, skin=None):
    """一片平滑的冰晶甲：五边形瓦片，中央微微隆起，朝 along 方向搭接。"""
    tip = c + along * L * .62
    back = c - along * L * .5
    bl, br = back + sd * W * .46, back - sd * W * .46
    ml, mr = c + along * L * .08 + sd * W * .5, c + along * L * .08 - sd * W * .5
    top = c + nr * h + along * L * .02
    ref = c - nr
    for a, b, d in ((bl, br, .05), (br, mr, -.01), (mr, tip, -.05), (tip, ml, -.02), (ml, bl, .02)):
        geo.tri(a, b, top, tone + d, row, ref, skin)


# ---------- 甲片
i_f = 0.0
row_i = 0
while i_f < n - 1:
    i = int(i_f)
    rw, rh = RW[i], RH[i]
    L = .38 + .22 * (rw + rh) / 2
    perim = math.tau * math.sqrt((rw * rw + rh * rh) / 2)
    count = max(6, int(perim / (L * .86)))
    for k in range(count):
        a = (k + (row_i % 2) * .5) / count * math.tau
        ca, sa = math.cos(a), math.sin(a)
        c = spine[i] + side[i] * ca * rw + nrm[i] * sa * rh
        out = side[i] * ca / rw + nrm[i] * sa / rh
        out /= np.linalg.norm(out)
        sd = np.cross(out, tan[i])
        sd /= np.linalg.norm(sd)
        if sa < -.62:
            plate(c, tan[i], sd, out, L * 1.25, L * 1.5, L * .05, .62 + rnd.uniform(-.02, .02), 1, sp_skin(i))
        else:
            plate(c, -tan[i], sd, out, L * 1.55, L * 1.18, L * .2, .6 + .16 * sa + rnd.uniform(-.09, .09), 0, sp_skin(i))
    i_f += L * .62 / .7
    row_i += 1
# 背脊：一排渐变的冰晶刃，肩部最高，尾部小
i = 6
while i < n - 6:
    rr = RH[i]
    h = (rr * .62 + .35) * (1.5 if sv[i] > L_tail else 1.0) * rnd.uniform(.85, 1.15)
    b = spine[i] + nrm[i] * rr * .9
    tip = b + nrm[i] * h - tan[i] * h * .7
    pa, pb = b + tan[i] * (h * .42 + .12), b - tan[i] * (h * .42 + .12)
    th = side[i] * (.1 + rr * .05)
    sk = sp_skin(i)
    geo.tri(pa + th, tip, pb + th, .84, 3, spine[i], sk)
    geo.tri(pa - th, pb - th, tip, .72, 3, spine[i], sk)
    geo.tri(pa + th, pa - th, tip, .9, 3, spine[i], sk)
    geo.tri(pb + th, tip, pb - th, .66, 3, spine[i], sk)
    i += max(2, int((.8 + rr * .4) / .7))
# ---------- 头：局部坐标 F 向前，U 向上，S 向右
geo_spine = geo
geo = Geo(ROWS)   # 引擎单模型上限 3 万面：身体、头和腿、翅膀分三个模型，共用骨骼和动画
HEAD_POS = spine[-1]
J_NECK_IDS = [J_SP[k] for k, i in enumerate(sp_idx) if sv[i] > L_tail + L_torso]
Fh = tan[-1] * .5 + F2 * .62 + UP * -.12
Fh = Fh / np.linalg.norm(Fh)
Sh = np.cross(Fh, UP)
Sh = Sh / np.linalg.norm(Sh)
Uh = np.cross(Sh, Fh)
J_HEAD = len(joints)
joints.append(('head', HEAD_POS.copy()))
HS = 1.0


def hp(f, s, u):
    return HEAD_POS + (Fh * f * 1.12 + Sh * s * .82 + Uh * u * .92) * HS


ST = [(-1.4, 1.45, 1.5, -1.25), (.3, 1.75, 1.85, -.9), (1.8, 1.8, 2.05, -.6), (3.2, 1.55, 1.8, -.42), (4.4, 1.2, 1.15, -.34), (5.8, 1.0, .85, -.3), (7.3, .95, .74, -.3), (8.5, 1.0, .8, -.28), (9.5, .78, .62, -.22), (10.3, .3, .28, -.12)]
PROF = [(1, 0), (.9, .5), (.55, .92), (0, 1.05), (-.55, .92), (-.9, .5), (-1, 0), (-.5, -1), (.5, -1)]
rings, ctrs = [], []
for f, w_, t, b in ST:
    rings.append([hp(f, sx * w_, t * sy if sy > 0 else b * -sy) for sx, sy in PROF])
    ctrs.append(hp(f, 0, (t + b) / 2))
geo.skin = (J_HEAD, J_HEAD, 0.0)
geo.loft(rings, .7, 0, ctrs, tone_fn=lambda i, k: .68 + .16 * math.sin(k / 9 * math.tau) + rnd.uniform(-.03, .03))
# 头部小甲片：平贴，不起尖
for _ in range(220):
    f = rnd.uniform(-1, 9.4)
    k = min(max(np.searchsorted([q[0] for q in ST], f), 1), len(ST) - 1)
    a, b_ = ST[k - 1], ST[k]
    u_ = (f - a[0]) / (b_[0] - a[0])
    w_ = a[1] + (b_[1] - a[1]) * u_
    t = a[2] + (b_[2] - a[2]) * u_
    ang_ = rnd.uniform(-.1, math.pi + .1)
    c = hp(f, math.cos(ang_) * w_, math.sin(ang_) * t)
    out = Sh * math.cos(ang_) + Uh * math.sin(ang_)
    sd = np.cross(out, Fh)
    L = rnd.uniform(.5, .85) * HS
    plate(c, -Fh, sd, out, L * 1.4, L * 1.1, L * .08, .72 + .14 * math.sin(ang_) + rnd.uniform(-.04, .04), 0)
for sgn in (-1, 1):
    # 眉骨：一条连续的棱，压住眼睛
    pts = [hp(-.6, sgn * 1.55, 2.0), hp(1, sgn * 1.8, 2.4), hp(2.8, sgn * 1.48, 2.15), hp(4.3, sgn * .98, 1.3)]
    for a, b_ in zip(pts, pts[1:]):
        geo.cone(a, b_, .4 * HS, up=Fh, seg=5, tone=.76, row=3, tip_tone=.84)
    e = hp(2.75, sgn * 1.62, 1.28)
    ec = hp(2.6, sgn * 1.2, 1.2)
    a, b_, c_, d_ = hp(2.3, sgn * 1.68, 1.25), hp(3.3, sgn * 1.45, 1.12), hp(2.85, sgn * 1.64, 1.5), hp(2.85, sgn * 1.7, .98)
    for t1, t2 in ((a, c_), (c_, b_), (b_, d_), (d_, a)):
        geo.tri(t1, t2, e + Sh * sgn * .16, .6, 4, ec)
    # 主角：一对大角向后上方弯；后面两支副角
    geo.cone(hp(-.4, sgn * 1.2, 1.55), hp(-11, sgn * 3.8, 8.5), .95 * HS, up=Sh, seg=7, tone=.56, row=3, curve=(Uh * 2.2 + Sh * sgn * .4) * HS, n=6, tip_tone=.99)
    geo.cone(hp(.5, sgn * 1.65, 1.1), hp(-5.8, sgn * 5, 3), .5 * HS, up=Sh, seg=6, tone=.58, row=3, curve=Uh * 1.1 * HS, n=5, tip_tone=.99)
    # 腮后三片冰刃
    for f0, s0, u0, f1, s1, u1, w_ in ((.4, 1.75, -.2, -4.2, 3.7, -.9, .3), (-.3, 1.6, -.6, -3.8, 3.1, -2.3, .28), (1.2, 1.8, .3, -2.8, 4.0, .9, .24)):
        geo.cone(hp(f0, sgn * s0, u0), hp(f1, sgn * s1, u1), w_ * HS, up=Sh, seg=4, tone=.62, row=3, tip_tone=.99)
    # 冠：一圈向后张开的冰刃（参考图的头冠）
    for k_, (f0, s0, u0, f1, s1, u1, w_) in enumerate(((1.2, .7, 2.1, -3.8, 1.2, 7.4, .34), (2.0, 1.05, 2.0, -2.0, 2.3, 6.2, .3), (2.7, 1.2, 1.9, -.2, 2.8, 4.6, .24), (-.2, .6, 1.8, -6.6, 1.0, 5.0, .34), (-.8, 1.1, 1.3, -7.4, 2.8, 3.2, .36), (-1.0, 1.4, .4, -6.8, 4.4, 1.2, .34), (-.6, 1.3, -.5, -5.4, 4.6, -1.6, .3), (.8, 1.4, -.9, -2.8, 3.4, -3.4, .26), (3.4, 1.05, -.45, 1.0, 2.2, -2.6, .18))):
        geo.cone(hp(f0, sgn * s0, u0), hp(f1, sgn * s1, u1), w_ * HS, up=Sh, seg=4, tone=.66, row=3, tip_tone=.99)
    # 鼻尖小角
    geo.cone(hp(8.8, sgn * .68, .62), hp(9.6, sgn * .78, 1.25), .17 * HS, up=Fh, seg=4, tone=.66, row=3)
    # 上牙
    for k_ in range(9):
        f = 3.4 + k_ * .72
        w_ = np.interp(f, [q[0] for q in ST], [q[1] for q in ST]) * .92
        L = .7 if k_ in (5, 6) else rnd.uniform(.32, .46)
        geo.cone(hp(f, sgn * w_, -.2), hp(f, sgn * w_, -.25 - L), .12 * HS, up=Fh, seg=3, tone=.8, row=6, tip_tone=.98)
geo.quad(hp(1.6, -1.3, -.42), hp(1.6, 1.3, -.42), hp(9.2, .55, -.2), hp(9.2, -.55, -.2), .3, 5, hp(5, 0, 2))
# 下颌
JAW_PIVOT = hp(.8, 0, -.7)
J_JAW = len(joints)
joints.append(('jaw', JAW_PIVOT.copy()))
geo.skin = (J_JAW, J_JAW, 0.0)
JST = [(.2, 1.35, -.45, -1.3), (2, 1.3, -.45, -1.05), (4, 1.05, -.42, -.82), (6, .85, -.42, -.7), (8, .78, -.38, -.62), (9.2, .5, -.32, -.48), (9.8, .18, -.28, -.34)]
rings, ctrs = [], []
for f, w_, t, b in JST:
    rings.append([hp(f, sx * w_, b + (t - b) * (sy + 1) / 2) for sx, sy in ((1, 1), (.9, 0), (.45, -1), (-.45, -1), (-.9, 0), (-1, 1), (-.4, .7), (.4, .7))])
    ctrs.append(hp(f, 0, (t + b) / 2))
geo.loft(rings, .6, 0, ctrs, tone_fn=lambda i, k: {0: .72, 1: .62, 2: .55, 3: .55, 4: .62, 5: .72, 6: .22, 7: .22}[k])
for sgn in (-1, 1):
    for k_ in range(8):
        f = 3.4 + k_ * .74
        w_ = np.interp(f, [q[0] for q in JST], [q[1] for q in JST]) * .88
        L = .55 if k_ in (5, 6) else rnd.uniform(.26, .38)
        geo.cone(hp(f, sgn * w_, -.5), hp(f, sgn * w_, -.5 + L), .1 * HS, up=Fh, seg=3, tone=.8, row=6, tip_tone=.98)
# ---------- 腿：大块肌肉，三段
J_LEGS = {}


def leg(name, hip, knee, ankle, foot, r0, claw_dir, fs=1.0):
    hip, knee, ankle, foot = [np.asarray(x, float) for x in (hip, knee, ankle, foot)]
    J = len(joints)
    joints.append((name, hip.copy()))
    J_LEGS[name] = J
    geo.skin = (J, J, 0.0)
    path = catmull([hip, knee, ankle, foot], 7)
    tn = np.gradient(path, axis=0)
    tn /= np.linalg.norm(tn, axis=1, keepdims=True)
    rad = np.interp(np.linspace(0, 1, len(path)), [0, .16, .34, .5, .68, 1], [r0, r0 * 1.02, r0 * .68, r0 * .52, r0 * .46, r0 * .4])
    rings, ctrs = [], []
    sref = np.cross(tn[0], F2 + UP * .3)
    sref /= np.linalg.norm(sref)
    frames_ = []
    for i, (p, t) in enumerate(zip(path, tn)):
        sv_ = sref - t * np.dot(sref, t)
        sv_ /= np.linalg.norm(sv_)
        sref = sv_
        u = np.cross(t, sv_)
        frames_.append((sv_, u))
        rings.append([p + (sv_ * math.cos(a) + u * math.sin(a)) * rad[i] for a in np.linspace(0, math.tau, 10, endpoint=False)])
        ctrs.append(p)
    geo.loft(rings, .55, 0, ctrs, tone_fn=lambda i, k: .56 + .1 * math.sin(k / 10 * math.tau))
    plen = float(np.linalg.norm(np.diff(path, axis=0), axis=1).sum())
    # 甲片
    acc = 0.0
    row_k = 0
    pseg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    ps = np.concatenate([[0], np.cumsum(pseg)])
    while acc < plen:
        i = min(int(np.searchsorted(ps, acc)), len(path) - 1)
        p, t = path[i], tn[i]
        sv_, u = frames_[i]
        L = .34 + .22 * rad[i]
        cnt = max(6, int(math.tau * rad[i] / (L * .86)))
        for k in range(cnt):
            a = (k + rnd.random() * .6 + (row_k % 2) * .5) / cnt * math.tau
            o = sv_ * math.cos(a) + u * math.sin(a)
            plate(p + o * rad[i] * 1.01, -t, np.cross(o, t), o, L * 1.55, L * 1.18, L * .2, .6 + .14 * o[2] + rnd.uniform(-.09, .09), 0)
        acc += L * .62
        row_k += 1
    # 趾和爪，贴着地形抓下去
    cd = np.asarray(claw_dir, float)
    cd = cd / np.linalg.norm(cd)
    cs = np.cross(cd, UP)
    for ang_ in (-.7, -.24, .24, .7):
        d = cd * math.cos(ang_) + cs * math.sin(ang_)
        k1 = foot + d * 1.9 * fs + UP * .35 * fs
        tip_xy = foot + d * 4.1 * fs
        tip = np.array([tip_xy[0], tip_xy[1], G2(tip_xy[0], tip_xy[1]) - .3])
        geo.cone(foot, k1, rad[-1] * .62, up=cs, seg=6, tone=.68, row=0, tip_tone=.74)
        geo.cone(k1, tip, .42 * fs, up=cs, seg=6, tone=.42, row=3, curve=UP * .55 * fs, n=4, tip_tone=.98)


chest_i = int((L_tail + L_torso) / .7)
hip_i = int(L_tail / .7)
for sgn, nm in ((1, 'fl'), (-1, 'fr')):
    hip = CHEST + SIDE * sgn * 5.8 - UP * 2.0 - F2 * 1.0
    fxy = CHEST + SIDE * sgn * 8.5 + F2 * 7.5
    foot = np.array([fxy[0], fxy[1], G2(fxy[0], fxy[1]) + 1.0])
    knee = hip + (foot - hip) * .5 + SIDE * sgn * 1.8 - F2 * 1.8 + UP * .8
    ankle = foot + (knee - foot) * .34 + F2 * .9 + UP * .3
    leg(nm, hip, knee, ankle, foot, 3.6, F2, 1.5)
for sgn, nm in ((1, 'hl'), (-1, 'hr')):
    hip = HIPS + SIDE * sgn * 5.2 + F2 * .5 + UP * .3
    fxy = HIPS + SIDE * sgn * 9.0 + F2 * 5.0
    foot = np.array([fxy[0], fxy[1], G2(fxy[0], fxy[1]) + 1.0])
    knee = hip + (foot - hip) * .42 + SIDE * sgn * 1.4 + F2 * 4.2 + UP * 1.4
    ankle = foot + (knee - foot) * .36 - F2 * 3.2 + UP * .8
    leg(nm, hip, knee, ankle, foot, 4.6, F2, 1.7)
# ---------- 关节处的冰晶簇：撑起雄壮的轮廓


def cluster(c, out, n_, size, skin):
    c = np.asarray(c, float)
    out = np.asarray(out, float)
    out = out / np.linalg.norm(out)
    a = np.cross(out, (.2, .3, 1))
    a = a / np.linalg.norm(a)
    b = np.cross(out, a)
    for k in range(n_):
        an = rnd.uniform(0, math.tau)
        sp = rnd.uniform(.1, .75)
        d = out + (a * math.cos(an) + b * math.sin(an)) * sp
        L = size * rnd.uniform(.55, 1.1)
        geo.cone(c + (a * math.cos(an) + b * math.sin(an)) * size * .12, c + d * L, size * rnd.uniform(.1, .17), up=out, seg=5, tone=.62, row=3, skin=skin, tip_tone=.99)


chest_sk = sp_skin(chest_i)
hip_sk = sp_skin(hip_i)
for sgn in (-1, 1):
    cluster(CHEST + SIDE * sgn * 7.0 + UP * 3.2 - F2 * 1.0, SIDE * sgn * .7 + UP * .9 - F2 * .4, 9, 6.4, chest_sk)
    cluster(HIPS + SIDE * sgn * 6.6 + UP * 3.2, SIDE * sgn * .7 + UP * .8 - F2 * .7, 8, 5.6, hip_sk)
# 尾尖：一片冰刃尾鳍
tip_p = spine[0]
geo.cone(spine[6], tip_p - tan[0] * 4, .9, up=UP, seg=4, tone=.66, row=3, skin=sp_skin(4), tip_tone=.99)
# ---------- 翅膀：翼面朝玩家方向，高高举起，翼尖下垂
WF = np.array([-.3, -.95, 0.0])
WF = WF / np.linalg.norm(WF)
J_WING = {}


def wing(sgn, tag):
    SD = np.cross(WF, UP) * sgn

    def wp(a, b, c=0.0):
        return shoulder + SD * a + UP * b + WF * c

    shoulder = CHEST + SIDE * sgn * 5.2 + UP * 5.5 - F2 * 3.2
    k_ = 1.26 if sgn > 0 else 1.1
    elbow = wp(9 * k_, 15 * k_, -1)
    wrist = wp(13 * k_, 34 * k_, -3)
    tips = [wp(36 * k_, 38 * k_, 3), wp(50 * k_, 17 * k_, 8), wp(49 * k_, -8 * k_, 10), wp(34 * k_, -24 * k_, 8)]
    root = HIPS + SIDE * sgn * 3.5 + UP * 4.5
    names = ['sh', 'el', 'wr', 'f1', 'f2', 'f3', 'f4']
    J = {}
    for nm, p in zip(names, [shoulder, elbow, wrist, wrist, wrist, wrist, wrist]):
        J[nm] = len(joints)
        joints.append((f'{tag}_{nm}', p.copy()))
    J_WING[tag] = dict(J=J, shoulder=shoulder, elbow=elbow, wrist=wrist, sgn=sgn)

    def bone(a, b, r0, r1, skin, seg=7, tone=.6):
        path = [np.asarray(a) + (np.asarray(b) - np.asarray(a)) * t for t in np.linspace(0, 1, 5)]
        dv = np.asarray(b) - np.asarray(a)
        s = np.cross(dv, WF)
        s /= np.linalg.norm(s)
        u = np.cross(dv, s)
        u /= np.linalg.norm(u)
        rings = [[p + (s * math.cos(q) + u * math.sin(q)) * (r0 + (r1 - r0) * i / 4) for q in np.linspace(0, math.tau, seg, endpoint=False)] for i, p in enumerate(path)]
        geo.loft(rings, tone, 3, path, skin, tone_fn=lambda i, k: tone + .12 * math.cos(k / seg * math.tau))

    bone(shoulder, elbow, 1.9, 1.15, [(J['sh'], J['sh'], 0.)] * 4 + [(J['sh'], J['el'], .5)])
    bone(elbow, wrist, 1.15, .7, [(J['sh'], J['el'], .5)] + [(J['el'], J['el'], 0.)] * 3 + [(J['el'], J['wr'], .5)])
    # 翼爪
    for hk in ((-3.2, 6.2, -1.4), (.4, 8.4, -1.2), (2.8, 6.6, -1.0)):
        geo.cone(wrist, wrist + SD * hk[0] + UP * hk[1], .8 if abs(hk[0]) < 1 else .62, up=WF, seg=6, tone=.5, row=3, skin=(J['wr'], J['wr'], 0.), curve=SD * hk[2], n=5, tip_tone=.99)

    def finger_pt(k, u):
        tip = tips[k]
        p = wrist + (tip - wrist) * u
        bow = np.asarray(SD) * .08 + UP * .12
        return p + bow * math.sin(u * math.pi) * np.linalg.norm(tip - wrist) * .55

    fingers = ['f1', 'f2', 'f3', 'f4']
    for k in range(4):
        pts = [finger_pt(k, u) for u in np.linspace(0, 1, 12)]
        for i in range(11):
            r0, r1 = .62 * (1 - i / 11) + .06, .62 * (1 - (i + 1) / 11) + .06
            dv = pts[i + 1] - pts[i]
            s = np.cross(dv, WF)
            s /= np.linalg.norm(s)
            u = np.cross(dv, s)
            u /= np.linalg.norm(u)
            ring0 = [pts[i] + (s * math.cos(q) + u * math.sin(q)) * r0 for q in np.linspace(0, math.tau, 5, endpoint=False)]
            ring1 = [pts[i + 1] + (s * math.cos(q) + u * math.sin(q)) * r1 for q in np.linspace(0, math.tau, 5, endpoint=False)]
            geo.loft([ring0, ring1], .62, 3, [pts[i], pts[i + 1]], [(J[fingers[k]], J[fingers[k]], 0.)] * 2, tone_fn=lambda i_, k_: .62 + .1 * math.cos(k_ * 1.25), cap=False)

    def membrane(pa, pb, sa, sb, nu, nv, scallop, jitter, tear=0.0):
        grid = {}
        for iu in range(nu + 1):
            for iv in range(nv + 1):
                u_, v_ = iu / nu, iv / nv
                ue = u_ * (1 - scallop * math.sin(v_ * math.pi) ** .8)
                p = pa(ue) * (1 - v_) + pb(ue) * v_
                bulge = math.sin(v_ * math.pi) * math.sin(u_ * math.pi * .9 + .1)
                p = p + WF * bulge * 2.0
                if 0 < iu < nu and 0 < iv < nv:
                    p = p + np.array([rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)]) * jitter
                grid[iu, iv] = (p, v_)
        for iu in range(nu):
            for iv in range(nv):
                a, va = grid[iu, iv]
                b, vb = grid[iu + 1, iv]
                c, vc = grid[iu + 1, iv + 1]
                d, vd = grid[iu, iv + 1]
                tone = .52 + rnd.uniform(-.13, .16) + .16 * (iu / nu)
                for tri_ in ((a, b, c, va, vb, vc), (a, c, d, va, vc, vd)):
                    if iu >= nu - 4 and rnd.random() < tear * (1 + 2.5 * (iu - nu + 4) / 4):   # 只有外缘有少量破口
                        continue
                    p0, p1, p2, v0, v1, v2 = tri_
                    sk = [(sa, sb, v0), (sa, sb, v1), (sa, sb, v2)]
                    ctr = (p0 + p1 + p2) / 3
                    t_ = tone + rnd.uniform(-.015, .015)
                    geo.tri(p0, p1, p2, t_, 2, ctr + WF, sk)
                    geo.tri(p0, p1, p2, t_ - .12, 2, ctr - WF, sk)

    for k0 in range(3):
        membrane(lambda u, k0=k0: finger_pt(k0, u), lambda u, k0=k0: finger_pt(k0 + 1, u), J[fingers[k0]], J[fingers[k0 + 1]], 30, 16, .22, .22, .1)
    membrane(lambda u: finger_pt(3, u), lambda u: wrist + (root - wrist) * u, J[fingers[3]], J['el'], 26, 14, .26, .2, .06)
    membrane(lambda u: elbow + (wrist - elbow) * (1 - u), lambda u: elbow + (shoulder - elbow) * u, J['el'], J['sh'], 6, 4, .08, .1)


geo_body = geo
geo = Geo(ROWS)   # 引擎单个模型上限 3 万面：翅膀单独一个模型，共用同一套骨骼和动画
geo_wing = geo
wing(1, 'wl')
wing(-1, 'wr')
print('tris spine', geo_spine.tris_count(), 'head+legs', geo_body.tris_count(), 'wings', geo_wing.tris_count(), 'joints', len(joints))
# ---------- 动画：16 秒循环
FPS = 6
DUR = 16.0
frames_n = int(DUR * FPS) + 1
times = np.linspace(0, DUR, frames_n)
NJ = len(joints)
POS = np.zeros((frames_n, NJ, 3))
ROT = np.zeros((frames_n, NJ, 4))
rest = np.array([j[1] for j in joints])
sp_i = np.array(sp_idx)
b_rest, b_tan, b_side, b_nrm, b_sv = spine[sp_i], tan[sp_i], side[sp_i], nrm[sp_i], sv[sp_i]
neck_start = next(k for k, i in enumerate(sp_idx) if sv[i] > L_tail + L_torso)
for fi, t in enumerate(times):
    ph = t / DUR * math.tau
    roar = max(0.0, math.sin((t - 9.0) / 5.0 * math.pi)) if 9.0 < t < 14.0 else 0.0
    roar = roar ** 1.3
    # 尾巴：一条行波从尾根传到尾尖，越往尾尖幅度越大
    u_tail = np.clip(1 - b_sv / L_tail, 0, 1)
    amp = 1.7 * u_tail ** 1.5
    wave = np.sin(ph * 2 + b_sv * .14) * amp
    lift = np.sin(ph * 2 + b_sv * .14 + 1.1) * amp * .35
    new = b_rest + b_side * wave[:, None] + b_nrm * lift[:, None]
    # 呼吸：胸口起伏
    tb = np.clip((b_sv - L_tail) / L_torso, 0, 1) * (b_sv < L_tail + L_torso + 1)
    new = new + UP * (np.sin(ph * 4) * .16 * tb)[:, None]
    nt = np.gradient(new, axis=0)
    nt /= np.linalg.norm(nt, axis=1, keepdims=True)
    MS = []
    for j in range(neck_start):
        q = q_between(b_tan[j], nt[j])
        ROT[fi, J_SP[j]] = q
        POS[fi, J_SP[j]] = new[j]
        MS.append(Rigid(q, new[j] - q_rot(q, b_rest[j])))
    # 脖子：缓慢左右看，吼的时候抬起
    M = MS[-1]
    cnt = len(sp_idx) - neck_start
    for k in range(cnt):
        jid = J_SP[neck_start + k]
        p0 = rest[jid]
        pan = (.055 * math.sin(ph) + .025 * math.sin(ph * 3 + 1)) * (.5 + k / cnt)
        nod = (.022 * math.sin(ph * 2 + .6) + .05 * roar) * (.5 + k / cnt)
        M = Rigid.about(p0, UP, pan).then(Rigid.about(p0, SIDE, nod)).then(M)
        POS[fi, jid] = M.apply(p0)
        ROT[fi, jid] = M.q
    p0 = rest[J_HEAD]
    Mh = Rigid.about(p0, UP, .09 * math.sin(ph + .8)).then(Rigid.about(p0, Sh, .05 * math.sin(ph * 2 + 2) + .15 * roar)).then(M)
    POS[fi, J_HEAD] = Mh.apply(p0)
    ROT[fi, J_HEAD] = Mh.q
    p0 = rest[J_JAW]
    Mj = Rigid.about(p0, Sh, -(.04 + .02 * math.sin(ph * 2)) - .55 * roar).then(Mh)
    POS[fi, J_JAW] = Mj.apply(p0)
    ROT[fi, J_JAW] = Mj.q
    # 腿稳稳站住，只有微小的重心变化
    for nm, jid in J_LEGS.items():
        POS[fi, jid] = rest[jid] + UP * math.sin(ph * 4) * .03
        ROT[fi, jid] = np.array([1., 0, 0, 0])
    # 翅膀：慢拍，翼尖滞后
    chest_m = MS[-1]
    for tag, W in J_WING.items():
        J, sgn = W['J'], W['sgn']
        axis = WF * sgn
        base = .11 * math.sin(ph * 2) + .04 * math.sin(ph) + .07 * roar
        Ms = Rigid.about(W['shoulder'], axis, base).then(chest_m)
        Me = Rigid.about(W['elbow'], axis, .1 * math.sin(ph * 2 - .7) - .04 * roar).then(Ms)
        Mw = Rigid.about(W['wrist'], axis, .12 * math.sin(ph * 2 - 1.4)).then(Me)
        for nm, m_, p_ in (('sh', Ms, W['shoulder']), ('el', Me, W['elbow']), ('wr', Mw, W['wrist'])):
            POS[fi, J[nm]] = m_.apply(p_)
            ROT[fi, J[nm]] = m_.q
        for k, fn in enumerate(('f1', 'f2', 'f3', 'f4')):
            mf = Rigid.about(W['wrist'], axis, (.04 + .03 * k) * math.sin(ph * 2 - 2.0 - k * .3)).then(Mw)
            POS[fi, J[fn]] = mf.apply(W['wrist'])
            ROT[fi, J[fn]] = mf.q
POS[-1] = POS[0]
ROT[-1] = ROT[0]
os.makedirs(OUT, exist_ok=True)
CLIP = dict(idle=dict(times=times, pos=POS, rot=ROT))
for g_, nm_ in ((geo_spine, 'ice_dragon'), (geo_body, 'ice_dragon_h'), (geo_wing, 'ice_dragon_w')):
    path = os.path.join(OUT, nm_ + '.glb')
    tris = write_glb(path, g_, joints, CLIP, name=nm_, rough=.34, metal=.12)
    print('BUILT', nm_, tris, 'tris', round(os.path.getsize(path) / 1e6, 2), 'MB')
P = np.vstack([np.array(geo_spine.P), np.array(geo_body.P), np.array(geo_wing.P)])
print('bounds', P.min(0).round(1), P.max(0).round(1))
json.dump(dict(scale=SCALE, pos=[OX + PX * (1 - SCALE), PY * (1 - SCALE), OZ + PZ * (1 - SCALE)], chest=[float(x) for x in CHEST], head=[float(x) for x in HEAD_POS], OX=OX, OZ=OZ, bounds=[P.min(0).tolist(), P.max(0).tolist()]), open(os.path.join(OUT, 'ice_dragon.json'), 'w'))
# ---------- 尖峰模型（静态，和龙同原点）
pk = Geo([
    [(0, '#20262f'), (.33, '#4a5260'), (.5, '#7f8896'), (.62, '#b9c6d3'), (.74, '#e4edf4'), (1, '#fdfeff')],
])
NR, NT = 58, 130
grid = np.zeros((NR + 1, NT + 1, 3))
for i in range(NR + 1):
    r = RB * 1.45 * (i / NR) ** 1.25 + .01
    for j in range(NT + 1):
        th = j / NT * math.tau
        x, z = SC_X + math.cos(th) * r, SC_Z + math.sin(th) * r
        h = spire_h(x, z)
        if h < -1e8:
            h = 0.0
        grid[i, j] = (x, z, h + .42 * rnd.uniform(-1, 1) * min(1, r / 3))
    grid[i, NT] = grid[i, 0]
dx_ = np.gradient(grid, axis=0)
dy_ = np.gradient(grid, axis=1)
gn = np.cross(dy_, dx_)
gn = gn / (np.linalg.norm(gn, axis=2, keepdims=True) + 1e-9)
gn[gn[..., 2] < 0] *= -1


def vtone(p, n):
    # 岩脊露出、其余积雪：高频条纹沿山坡方向
    th = math.atan2(p[1] - SC_Z, p[0] - SC_X)
    streak = math.sin(th * 17 + p[2] * .12) * .5 + math.sin(th * 41 - p[2] * .2) * .3 + math.sin(th * 83 + p[2] * .5) * .2
    patch = math.sin(p[0] * 1.1 + p[1] * .7) * math.sin(p[1] * 1.3 - p[2] * .8)
    k = n[2] * .9 + streak * .22 + patch * .1 + (p[2] - 90) * .006
    return min(.98, max(.04, .34 + k * .75))


for i in range(NR):
    for j in range(NT):
        v = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
        P4 = [grid[a] for a in v]
        if max(p[2] - G(p[0], p[1]) for p in P4) < -1.5:
            continue
        N4 = [gn[a] for a in v]
        T4 = [vtone(p, n) for p, n in zip(P4, N4)]
        pk.tri(P4[0], P4[1], P4[2], (T4[0], T4[1], T4[2]), 0, normals=[N4[0], N4[1], N4[2]])
        pk.tri(P4[0], P4[2], P4[3], (T4[0], T4[2], T4[3]), 0, normals=[N4[0], N4[2], N4[3]])
for _ in range(120):
    th = rnd.uniform(0, math.tau)
    r = rnd.uniform(5, RB * 1.05)
    x, z = SC_X + math.cos(th) * r, SC_Z + math.sin(th) * r
    h = G2(x, z)
    s_ = rnd.uniform(.5, 1.7) * (.6 + r / RB)
    out = np.array([math.cos(th), math.sin(th), .35])
    c_ = np.array([x, z, h])
    pk.cone(c_ - out * s_ * .5, c_ + out * s_ * .4 + np.array([0, 0, s_ * rnd.uniform(.3, .9)]), s_ * .8, up=(0, 0, 1), seg=5, tone=.3, row=0, tip_tone=.62)
pp = os.path.join(OUT, 'dragon_peak.glb')
write_glb(pp, pk, name='dragon_peak', rough=.85)
Pk = np.array(pk.P)
JD = json.load(open(os.path.join(OUT, 'ice_dragon.json')))
JD['peak_size'] = float((Pk.max(0) - Pk.min(0)).max())
json.dump(JD, open(os.path.join(OUT, 'ice_dragon.json'), 'w'))
print('PEAK', pk.tris_count(), round(os.path.getsize(pp) / 1e6, 2), 'MB', JD['peak_size'])
