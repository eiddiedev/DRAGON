#!/usr/bin/env python3
"""粗略预览白模：地形用高度场光线步进，方块用深度缓冲光栅化。不是编辑器渲染。
用法：preview_whitebox.py <scene.data> <boxes.json> <输出目录>
"""
import io
import json
import math
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw

src, dump, outdir = sys.argv[1:4]
z = zipfile.ZipFile(src)
H = np.frombuffer(z.read('HeightMap_3193404.data'), '<f4').reshape(257, 257) * 256
tex = np.array(Image.open(io.BytesIO(z.read('MatCoverTex_3193404.png'))).convert('RGB'))
T = tex.shape[0]
boxes = json.load(open(dump))
SEA = 27.0
CORNERS = np.array([[x, y, zz] for x in (-.5, .5) for y in (-.5, .5) for zz in (-.5, .5)])
FACES = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
NORMALS = np.array([[-1, 0, 0], [1, 0, 0], [0, -1, 0], [0, 1, 0], [0, 0, -1], [0, 0, 1]], float)
LIGHT = np.array([-.45, .75, -.5])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def rotmat(q):
    x, y, zz, w = q
    return np.array([[1 - 2 * (y * y + zz * zz), 2 * (x * y - zz * w), 2 * (x * zz + y * w)],
                     [2 * (x * y + zz * w), 1 - 2 * (x * x + zz * zz), 2 * (y * zz - x * w)],
                     [2 * (x * zz - y * w), 2 * (y * zz + x * w), 1 - 2 * (x * x + y * y)]])


def render(ex, ey, ez, yaw, pitch, fn, W=1280, Hh=720, fov=62):
    f = (W / 2) / math.tan(math.radians(fov) / 2)
    img = np.zeros((Hh, W, 3), float)
    depth = np.full((Hh, W), 1e9)
    for y in range(Hh):
        t = y / Hh
        img[y] = np.array([112, 170, 225]) * (1 - t) + np.array([222, 236, 246]) * t
    hor = Hh / 2 + math.tan(math.radians(pitch)) * f
    for col in range(W):
        off = math.atan((col - W / 2) / f)
        a = math.radians(yaw) + off
        dx, dz, cosc = math.sin(a), math.cos(a), math.cos(off)
        ybuf = Hh
        d = 1.0
        while d < 650 and ybuf > 0:
            px, pz = ex + dx * d, ez + dz * d
            if 0 <= px < 256 and 0 <= pz < 256:
                x0, z0 = int(px), int(pz)
                fx, fz = px - x0, pz - z0
                g = (H[z0, x0] * (1 - fx) * (1 - fz) + H[z0, x0 + 1] * fx * (1 - fz)
                     + H[z0 + 1, x0] * (1 - fx) * fz + H[z0 + 1, x0 + 1] * fx * fz)
                c = tex[min(T - 1, int((256 - pz) / 256 * T)), min(T - 1, int(px / 256 * T))].astype(float)
            else:
                g, c = SEA, np.array([40, 110, 145.])
            if g < SEA:
                g, c = SEA, np.array([45, 125, 155.])
            dz_view = d * cosc
            sy = int(hor + (ey - g) / dz_view * f)
            if sy < ybuf:
                fog = min(1, d / 1000)
                s = max(sy, 0)
                img[s:ybuf, col] = c * (1 - fog) + np.array([205, 225, 242]) * fog
                depth[s:ybuf, col] = dz_view
                ybuf = s
            d += .25 + d * .005
    # view basis
    cy, sy_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    right = np.array([cy, 0, -sy_])
    forward0 = np.array([sy_, 0, cy])
    up = np.array([0, 1, 0.])
    eye = np.array([ex, ey, ez])

    def project(P):
        v = P - eye
        vz = v @ forward0
        return np.array([W / 2 + (v @ right) / vz * f, hor - (v @ up) / vz * f, vz])

    for b in boxes:
        R = rotmat(b['rot'])
        s = np.array(b['scale'])
        c = np.array(b['pos'])
        pts = (CORNERS * s) @ R.T + c
        for fi, face in enumerate(FACES):
            n = R @ NORMALS[fi]
            if n @ (c + n * 1e-3 - eye) > 0 and (pts[face[0]] - eye) @ n > 0:
                continue
            shade = .62 + .5 * max(0, n @ LIGHT)
            col = np.array(b['color']) * 255 * shade
            P = [pts[i] for i in face]
            if any((p - eye) @ forward0 < 1 for p in P):
                continue
            q = np.array([project(p) for p in P])
            x0, x1 = int(max(0, q[:, 0].min())), int(min(W - 1, q[:, 0].max() + 1))
            y0, y1 = int(max(0, q[:, 1].min())), int(min(Hh - 1, q[:, 1].max() + 1))
            if x0 > x1 or y0 > y1:
                continue
            gy, gx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
            for tri in ((0, 1, 2), (0, 2, 3)):
                A, B, C = q[list(tri)]
                den = (B[1] - C[1]) * (A[0] - C[0]) + (C[0] - B[0]) * (A[1] - C[1])
                if abs(den) < 1e-6:
                    continue
                l1 = ((B[1] - C[1]) * (gx - C[0]) + (C[0] - B[0]) * (gy - C[1])) / den
                l2 = ((C[1] - A[1]) * (gx - C[0]) + (A[0] - C[0]) * (gy - C[1])) / den
                l3 = 1 - l1 - l2
                m = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
                if not m.any():
                    continue
                dd = 1 / (l1 / A[2] + l2 / B[2] + l3 / C[2])
                yy, xx = gy[m], gx[m]
                vis = dd[m] < depth[yy, xx]
                depth[yy[vis], xx[vis]] = dd[m][vis]
                img[yy[vis], xx[vis]] = col
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(fn)


def topdown(fn):
    S = 1280 / 256
    im = Image.fromarray(tex).resize((1280, 1280)).convert('RGB')
    dr = ImageDraw.Draw(im)
    for b in sorted(boxes, key=lambda k: k['pos'][1] + k['scale'][1] / 2):
        R = rotmat(b['rot'])
        pts = (CORNERS * np.array(b['scale'])) @ R.T + np.array(b['pos'])
        p2 = [(p[0] * S, (256 - p[2]) * S) for p in pts]
        cx, cy = np.mean(p2, axis=0)
        p2.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx))
        c = tuple(int(v * 255) for v in b['color'])
        dr.polygon(p2, fill=c, outline=(30, 30, 30))
    for g in range(0, 257, 32):
        y = (256 - g) * S
        dr.line([(g * S, 0), (g * S, 1280)], fill=(255, 255, 255, 80))
        dr.line([(0, y), (1280, y)], fill=(255, 255, 255, 80))
        dr.text((g * S + 3, 3), str(g), fill=(255, 255, 0))
        dr.text((3, y + 2), str(g), fill=(255, 255, 0))
    im.save(fn)


topdown(f'{outdir}/whitebox-top.png')
render(130, 62.5, 55, 0, 3, f'{outdir}/whitebox-spawn.png')
render(40, 150, 40, 42, -22, f'{outdir}/whitebox-air.png')
