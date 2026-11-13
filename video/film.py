#!/usr/bin/env python3
"""逐帧拍运镜：在预览里另架一台相机（film_cam），世界冻结，每帧设相机位姿再截图。
用法：python3 video/film.py <镜头名>      输出 video/frames/<镜头名>/0001.jpg…
相机路径在 SHOTS 里：每个镜头给出若干关键帧 (位置, 看向的点, 视野)，按帧数平滑插值。"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCR = os.environ.get('SCRATCH', '/tmp')
RID = open(f'{SCR}/runtime_id').read().strip()

# 镜头名: (帧数, [(pos, look, fov), ...])
SHOTS = {
    'test': (1, [((128, 150, -60), (128, 60, 150), 45)]),
}
if os.path.exists(f'{REPO}/video/shots.json'):
    for k, v in json.load(open(f'{REPO}/video/shots.json')).items():
        SHOTS[k] = (v[0], [tuple(map(tuple, kf[:2])) + (kf[2],) for kf in v[1]])


def smooth(t):
    return t * t * (3 - 2 * t)


def pose(keys, u):
    if len(keys) == 1:
        return keys[0]
    f = smooth(u) * (len(keys) - 1)
    i = min(int(f), len(keys) - 2)
    t = f - i
    a, b = keys[i], keys[i + 1]
    lerp = lambda x, y: tuple(np.array(x) * (1 - t) + np.array(y) * t)
    return lerp(a[0], b[0]), lerp(a[1], b[1]), a[2] * (1 - t) + b[2] * t


def cli(*args):
    return subprocess.run(['douyin-world', 'runtime', *args, '--runtime-id', RID, '-q'], capture_output=True, text=True, cwd=REPO)


name = sys.argv[1]
n, keys = SHOTS[name]
out = f'{REPO}/video/frames/{name}'
os.makedirs(out, exist_ok=True)
for k in range(n):
    dst = f'{out}/{k + 1:04d}.jpg'
    if os.path.exists(dst):
        continue
    p, l, fov = pose(keys, k / max(1, n - 1))
    code = ("local U=CS.UnityEngine;local go=U.GameObject.Find('film_cam');local t=go.transform;"
            f"t.position=U.Vector3({p[0]:.3f},{p[1]:.3f},{p[2]:.3f});"
            f"t.rotation=U.Quaternion.LookRotation(U.Vector3({l[0] - p[0]:.3f},{l[1] - p[1]:.3f},{l[2] - p[2]:.3f}));"
            f"go:GetComponent(typeof(U.Camera)).fieldOfView={fov:.2f};return 1")
    r = cli('lua', 'eval', code, '--global')
    png = f'{SCR}/film/_f.png'
    cli('screenshot', '--out', png)
    im = Image.open(png).convert('RGB')
    w, h = im.size
    top = int(h * .075)                       # 裁掉预览顶部的按键提示条，取 16:9
    ch = h - top
    cw = int(ch * 16 / 9)
    x0 = (w - cw) // 2
    im.crop((x0, top, x0 + cw, h)).resize((1920, 1080), Image.LANCZOS).save(dst, quality=92)
    print(name, k + 1, n, flush=True)
