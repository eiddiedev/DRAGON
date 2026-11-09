#!/usr/bin/env python3
"""给雪山做水滴侵蚀，得到树枝状的山脊和冲沟。只动高处，小山、道路、河道都不碰。
用法：erode.py <地形目录>，读 base_heights.npy，写 erosion.npy（高度差）、wear.npy（冲刷量）和 erosion-check.png。
"""
import os
import sys

import numpy as np
from numba import njit
from PIL import Image
from scipy import ndimage as nd

OUT = sys.argv[1]
H = np.load(os.path.join(OUT, 'base_heights.npy'))
R = 513
CELL = 256 / (R - 1)
yy, xx = np.mgrid[0:R, 0:R].astype(np.float32)
wx, wz = xx * CELL, yy * CELL
h0 = nd.zoom(H, R / H.shape[0], order=3)[:R, :R].astype(np.float64)


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def fract(beta, fmin, fmax, seed):
    r = np.random.default_rng(seed)
    fy, fx = np.fft.fftfreq(R)[:, None] * R, np.fft.fftfreq(R)[None, :] * R
    f = np.hypot(fx, fy)
    f[0, 0] = 1
    amp = f ** (-beta / 2)
    amp[(f < fmin) | (f > fmax)] = 0
    o = np.real(np.fft.ifft2(np.fft.fft2(r.normal(size=(R, R))) * amp))
    return (o - o.mean()) / o.std()


hr = np.hypot(wx - 127, wz - 176)
M = ss(48, 62, h0) * ss(46, 56, hr)
print('mountain cells', int((M > .01).sum()), flush=True)
# 山形：大尺度山脊分形，越高越强；只改轮廓，细节留给水滴
big = 1 - np.abs(fract(2.6, 3, 16, 21))
mid = 1 - np.abs(fract(2.4, 12, 40, 22))
rel = np.clip(h0 - 48, 0, 70)
h = h0 + M * ((big - .55) * (2.5 + rel * .16) + (mid - .55) * (1 + rel * .05) + fract(2.2, 30, 120, 23) * .25)


@njit(cache=True)
def droplets(h, M, n, seed, cell):
    np.random.seed(seed)
    R = h.shape[0]
    wear = np.zeros_like(h)
    inertia, cap, mins, er, dp, evap, g = .12, 1.6, .02, .1, .3, .02, 4.0
    # 笔刷
    rad = 3
    for k in range(n):
        while True:
            x = np.random.random() * (R - 3) + 1
            y = np.random.random() * (R - 3) + 1
            if M[int(y), int(x)] > .08:
                break
        dx = dy = 0.0
        sp, w, s = 1.0, 1.0, 0.0
        for life in range(70):
            ix, iy = int(x), int(y)
            if ix < 1 or iy < 1 or ix >= R - 2 or iy >= R - 2:
                break
            u, v = x - ix, y - iy
            a, b, c, d = h[iy, ix], h[iy, ix + 1], h[iy + 1, ix], h[iy + 1, ix + 1]
            gx = (b - a) * (1 - v) + (d - c) * v
            gy = (c - a) * (1 - u) + (d - b) * u
            here = a * (1 - u) * (1 - v) + b * u * (1 - v) + c * (1 - u) * v + d * u * v
            dx = dx * inertia - gx * (1 - inertia)
            dy = dy * inertia - gy * (1 - inertia)
            ln = (dx * dx + dy * dy) ** .5
            if ln < 1e-6:
                break
            dx, dy = dx / ln, dy / ln
            nx, ny = x + dx, y + dy
            jx, jy = int(nx), int(ny)
            if jx < 1 or jy < 1 or jx >= R - 2 or jy >= R - 2:
                break
            u2, v2 = nx - jx, ny - jy
            there = h[jy, jx] * (1 - u2) * (1 - v2) + h[jy, jx + 1] * u2 * (1 - v2) + h[jy + 1, jx] * (1 - u2) * v2 + h[jy + 1, jx + 1] * u2 * v2
            dh = there - here
            cc = max(-dh / 1.0, mins) * sp * w * cap
            if s > cc or dh > 0:
                amt = min(dh, s) if dh > 0 else (s - cc) * dp
                amt = max(amt, 0.0)
                s -= amt
                m = M[iy, ix]
                h[iy, ix] += amt * (1 - u) * (1 - v) * m
                h[iy, ix + 1] += amt * u * (1 - v) * m
                h[iy + 1, ix] += amt * (1 - u) * v * m
                h[iy + 1, ix + 1] += amt * u * v * m
            else:
                amt = min((cc - s) * er, -dh)
                tot = 0.0
                for oy in range(-rad, rad + 1):
                    for ox in range(-rad, rad + 1):
                        qx, qy = ix + ox, iy + oy
                        if qx < 0 or qy < 0 or qx >= R or qy >= R:
                            continue
                        wt = max(0.0, rad + .5 - (ox * ox + oy * oy) ** .5)
                        tot += wt
                for oy in range(-rad, rad + 1):
                    for ox in range(-rad, rad + 1):
                        qx, qy = ix + ox, iy + oy
                        if qx < 0 or qy < 0 or qx >= R or qy >= R:
                            continue
                        wt = max(0.0, rad + .5 - (ox * ox + oy * oy) ** .5) / tot
                        q = amt * wt * M[qy, qx]
                        h[qy, qx] -= q
                        wear[qy, qx] += q
                s += amt
            sp = (max(sp * sp + dh * g * -1, 0.0)) ** .5
            w *= 1 - evap
            x, y = nx, ny
    return wear


wear = droplets(h, M, 90000, 7, CELL)
# 太尖的毛刺抹一下
hs = nd.gaussian_filter(h, 1.2)
gz, gx = np.gradient(h, CELL)
sl = np.hypot(gx, gz)
h = h + (hs - h) * ss(1.2, 2.2, sl) * M
delta = h - h0
# 冲沟深度软限制，保留走向，不把山切碎
L = 11.0
delta = np.where(delta < 0, -L * (1 - np.exp(delta / L)), 5 * (1 - np.exp(-delta / 5)))
delta = nd.gaussian_filter(delta, .6).astype(np.float32)
h = h0 + delta
np.save(os.path.join(OUT, 'erosion.npy'), delta)
np.save(os.path.join(OUT, 'wear.npy'), wear.astype(np.float32))
gz, gx = np.gradient(h, CELL)
nyv = 1 / np.sqrt(1 + gx * gx + gz * gz)
shade = np.clip((gx * .663 + .643 + gz * .383) * nyv, 0, 1) ** 1.2
Image.fromarray((shade[::-1] * 255).astype(np.uint8)).crop((0, 0, 513, 210)).resize((1026, 420)).save(os.path.join(OUT, 'erosion-check.png'))
slope = np.degrees(np.arctan(np.hypot(gx, gz)))
print('delta', round(float(delta.min()), 1), round(float(delta.max()), 1), 'slope p50/p90/p99', [round(float(np.percentile(slope[M > .5], p)), 1) for p in (50, 90, 99)], 'wear p99', float(np.percentile(wear[M > .5], 99)))
