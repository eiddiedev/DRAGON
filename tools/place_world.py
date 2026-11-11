#!/usr/bin/env python3
"""把导入的模型摆到世界里，并把引擎地形压到新地形下面。可重复运行。
用法：place_world.py <输入 scene.data> <输出 scene.data>
要点（实测）：
- 导入时几何缩到最大边 1 米、原点不变，所以节点 scale 不动，pos 填模型原点的世界坐标即可。
- 导入后模型转了 180 度，所以每个模型绕 Y 轴再转 180 度转回来。
- 子节点存的是世界坐标（和父节点原点相同）。
"""
import copy
import json
import math
import os
import random
import sys
import zipfile

import numpy as np

src, out = sys.argv[1:3]
ROOT = '/Users/bytedance/Documents/ChatGPT/DRAGON/assets'
z = zipfile.ZipFile(src)
d = json.loads(z.read('SerializePcgData.json'))
N = d['nodeTransformDatas']
base_path = f'{ROOT}/terrain/world/base_heights.npy'
H = np.load(base_path)  # 未压低的高度，和新地形一致
SEA = 27.0
SINK = 3.0  # 引擎地形往下压的距离


def G(x, y):
    x = min(max(x, 0), 255.99)
    y = min(max(y, 0), 255.99)
    x0, y0 = int(x), int(y)
    fx, fy = x - x0, y - y0
    return float(H[y0, x0] * (1 - fx) * (1 - fy) + H[y0, x0 + 1] * fx * (1 - fy) + H[y0 + 1, x0] * (1 - fx) * fy + H[y0 + 1, x0 + 1] * fx * fy)


def Gmin(x, y, r):
    return min(G(x + a * r, y + b * r) for a in (-1, 0, 1) for b in (-1, 0, 1))


def yaw_q(deg):
    """deg 是 Blender 里朝向的旋转（从上往下看逆时针为正），已包含导入的 180 度修正。"""
    a = math.radians(180 - deg)
    return {'x': 0.0, 'y': round(math.sin(a / 2), 6), 'z': 0.0, 'w': round(math.cos(a / 2), 6)}


# ---------- 清理：白模（古龙先留作占位）、旧的重复模型
KEEP_WB = {'白模_古龙龙巢'}
children = {}
for n in N:
    children.setdefault(n['parentId'], []).append(n)


def subtree(n):
    out_ = [n['id']]
    for c in children.get(n['id'], []):
        out_ += subtree(c)
    return out_


remove = set()
last = {}
for n in N:
    if n['parentId'] != 0:
        continue
    name = n['nodeName']
    if (name.startswith('白模_') and name not in KEEP_WB) or name == 'terrain_tile':
        remove |= set(subtree(n))
    elif name in last:  # 同名的留最后拖进来的那个（新版本）
        remove |= set(subtree(last[name]))
        last[name] = n
    elif name not in ('地图', '出生点', '低模刺柏', '方块'):
        last[name] = n
print('removed', len(remove))
N = [n for n in N if n['id'] not in remove]
roots = {n['nodeName']: n for n in N if n['parentId'] == 0}
children = {}
for n in N:
    children.setdefault(n['parentId'], []).append(n)
used = {n['id'] for n in N}
rnd = random.Random(2026)


def new_id():
    while True:
        v = rnd.randint(1, 2 ** 31 - 1)
        if v not in used:
            used.add(v)
            return v


def set_pos(n, x, y, z_, deg=0.0):
    p = {'x': round(float(x), 4), 'y': round(float(y), 4), 'z': round(float(z_), 4)}
    n['pos'] = p
    n['rot'] = yaw_q(deg)
    for c in children.get(n['id'], []):  # 子节点存的是世界变换，位置和旋转都要跟着改
        c['pos'] = dict(p)
        c['rot'] = dict(n['rot'])


def clone(n):
    c = copy.deepcopy(n)
    c['id'] = new_id()
    kids = []
    for k in children.get(n['id'], []):
        kk = copy.deepcopy(k)
        kk['id'] = new_id()
        kk['parentId'] = c['id']
        kids.append(kk)
    N.append(c)
    N.extend(kids)
    children[c['id']] = kids
    return c


# ---------- 地形块
tiles = json.load(open(f'{ROOT}/terrain/world/manifest.json'))
missing = [t['name'] for t in tiles if t['name'] not in roots]
assert not missing, missing
for t in tiles:
    set_pos(roots[t['name']], t['x0'] + 32, 0, t['z0'] + 32)

# ---------- 城堡（四个部件共用一个原点）
for n in ('castle_walls', 'castle_keep', 'castle_library', 'castle_towers'):
    set_pos(roots[n], 127, 0, 173)

# ---------- 按世界坐标建的道具
for p in json.load(open(f'{ROOT}/props/placements.json')):
    if p['name'] in roots:
        set_pos(roots[p['name']], p['x'], p['y'], p['z'])

# ---------- 药水铺：城堡东坡脚下，上城堡的路边
set_pos(roots['witch_shop_v2'], 171, G(171, 146) - .1, 146, 0)

# ---------- 民居
RIVER = [(77, 253), (77, 236), (80, 219), (74, 192), (79, 173), (88, 152), (98, 136), (108, 124), (125, 116), (141, 118), (154, 110), (168, 110), (187, 103)]


def river_dist(x, y):
    best = 1e9
    for (ax, ay), (bx, by) in zip(RIVER, RIVER[1:]):
        dx, dy = bx - ax, by - ay
        t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - ax - t * dx, y - ay - t * dy))
    return best


spots = []


def scatter(xr, yr, want):
    tries = placed = 0
    while placed < want and tries < 1500:
        tries += 1
        x, y = rnd.uniform(*xr), rnd.uniform(*yr)
        if river_dist(x, y) < 11 or abs(x - 162) < 7:
            continue
        if abs(y - 165) < 8:  # 让开高架坡道
            continue
        if math.hypot(x - 171, y - 146) < 13:  # 让开药水铺
            continue
        lo, hi = Gmin(x, y, 5), max(G(x + a * 5, y + b * 5) for a in (-1, 0, 1) for b in (-1, 0, 1))
        if lo < SEA + 2 or hi - lo > 3.5:
            continue
        if any(math.hypot(x - a, y - b) < 13.5 for a, b, _ in spots):
            continue
        spots.append((x, y, rnd.choice('aabbc')))
        placed += 1


scatter((146, 192), (56, 102), 11)  # 河南岸
scatter((162, 204), (118, 160), 7)  # 河北岸，城堡脚下
used_first = set()
for x, y, kind in spots:
    name = 'house_' + kind
    node = roots[name] if name not in used_first else clone(roots[name])
    used_first.add(name)
    # 门大致朝南，正对出生点方向
    set_pos(node, x, Gmin(x, y, 4) - .05, y, rnd.choice((-25, -12, 0, 12, 25)))
print('houses', len(spots))

# ---------- 帆船与羊
ships = [(238, 64, 200), (232, 112, 150), (222, 40, 170)]
for i, (x, y, deg) in enumerate(ships):
    node = roots['sailboat'] if i == 0 else clone(roots['sailboat'])
    set_pos(node, x, SEA - .1, y, deg)
for i in range(9):
    x, y = rnd.uniform(88, 118), rnd.uniform(40, 96)
    node = roots['sheep'] if i == 0 else clone(roots['sheep'])
    s = rnd.uniform(1.2, 1.5)
    node['scale'] = {k: round(v * s, 4) for k, v in node['scale'].items()}
    set_pos(node, x, G(x, y) + .05, y, rnd.uniform(0, 360))

# ---------- 出生点 + 样本物体
for n in N:
    if n['tag'] == 'BornPoint':
        n['pos'] = {'x': 130.0, 'y': round(G(130, 48) + 1.0, 3), 'z': 48.0}
for n in N:
    if n['nodeName'] == '低模刺柏' and n['parentId'] == 0:
        n['pos'] = {'x': 117.0, 'y': round(G(117, 44), 3), 'z': 44.0}
    if n['nodeName'] == '方块' and n['parentId'] == 0:
        n['isActive'] = False  # 只是试验用的方块，隐藏

d['nodeTransformDatas'] = N
# 引擎地形压到新地形下面，只作为兜底
sunk = np.clip(H - SINK, 0, None) / 256
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as w:
    for i in z.infolist():
        data = z.read(i.filename)
        if i.filename == 'SerializePcgData.json':
            data = json.dumps(d, ensure_ascii=False, separators=(',', ':')).encode()
        elif i.filename == 'HeightMap_3193404.data':
            data = sunk.astype('<f4').tobytes()
        ni = zipfile.ZipInfo(i.filename, i.date_time)
        ni.compress_type = zipfile.ZIP_DEFLATED
        ni.external_attr = i.external_attr
        w.writestr(ni, data)
print('nodes', len(N), 'roots', sum(1 for n in N if n['parentId'] == 0))
