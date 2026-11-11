#!/usr/bin/env python3
"""第二版世界摆放：小山、哥特城堡、发光树、花海、路灯、森林。可重复运行。
用法：place_world2.py <输入 scene.data> <输出 scene.data>
同名根节点保留最后拖进来的那个。子节点存世界变换，位置和旋转都要跟着父节点。
"""
import json
import math
import sys
import zipfile

import numpy as np

src, out = sys.argv[1:3]
ROOT = '/Users/bytedance/Documents/ChatGPT/DRAGON/assets'
z = zipfile.ZipFile(src)
d = json.loads(z.read('SerializePcgData.json'))
N = d['nodeTransformDatas']
H = np.load(f'{ROOT}/terrain/world/base_heights.npy')
SINK = 3.0


def G(x, y):
    x = min(max(x, 0), 255.99)
    y = min(max(y, 0), 255.99)
    x0, y0 = int(x), int(y)
    fx, fy = x - x0, y - y0
    return float(H[y0, x0] * (1 - fx) * (1 - fy) + H[y0, x0 + 1] * fx * (1 - fy) + H[y0 + 1, x0] * (1 - fx) * fy + H[y0 + 1, x0 + 1] * fx * fy)


def yaw_q(deg):
    a = math.radians(180 - deg)
    return {'x': 0.0, 'y': round(math.sin(a / 2), 6), 'z': 0.0, 'w': round(math.cos(a / 2), 6)}


children = {}
for n in N:
    children.setdefault(n['parentId'], []).append(n)


def subtree(n):
    res = [n['id']]
    for c in children.get(n['id'], []):
        res += subtree(c)
    return res


# ---------- 清理：同名只留最后一个；旧城堡、高架坡道、旧天空去掉；可重复的道具（民居、羊、帆船）不算重复
REPEAT = {'sheep', 'sailboat', '__DouyinWaterArea2Triggers'}
POOLED = ('fw_', 'bat_', 'fc_', 'hs_')  # 脚本克隆出来的节点，重新生成
REMOVE = {'castle_walls', 'castle_keep', 'castle_library', 'castle_towers', 'causeway', 'sky_dome', 'sky_swirl', 'sky_moon', 'terrain_tile', 'magic_frame', 'campfire'}
remove = set()
last = {}
for n in N:
    if n['parentId'] != 0:
        continue
    name = n['nodeName']
    if name in ('fw_gold_0', 'fw_pink_0', 'fw_blue_0', 'bat_0'):
        continue  # 第一份是模板，保留
    if name in REMOVE or name.startswith(POOLED) or name in ('flowers_a', 'flowers_b'):
        remove |= set(subtree(n))
    elif name in REPEAT or name in ('地图', '出生点', '低模刺柏', '方块', '城门地板', 'time_dial'):
        continue
    elif name in last:
        remove |= set(subtree(last[name]))
        last[name] = n
    else:
        last[name] = n
print('removed', len(remove))
N = [n for n in N if n['id'] not in remove and not (n['nodeName'] == '城门地板')]
roots = {}
for n in N:
    if n['parentId'] == 0:
        roots.setdefault(n['nodeName'], []).append(n)
children = {}
for n in N:
    children.setdefault(n['parentId'], []).append(n)


def set_pos(n, x, y, z_, deg=0.0):
    p = {'x': round(float(x), 4), 'y': round(float(y), 4), 'z': round(float(z_), 4)}
    n['pos'] = p
    n['rot'] = yaw_q(deg)
    for c in children.get(n['id'], []):
        c['pos'] = dict(p)
        c['rot'] = dict(n['rot'])


def no_collision(n):
    n['physicsColliderData']['enableCollision'] = False
    for c in children.get(n['id'], []):
        if c.get('physicsColliderData'):
            c['physicsColliderData']['enableCollision'] = False


def one(name):
    return roots[name][-1]


# ---------- 地形块：贴图重画了，不再压暗
tiles = json.load(open(f'{ROOT}/terrain/world/manifest.json'))
for t in tiles:
    n = one(t['name'])
    set_pos(n, t['x0'] + 32, 0, t['z0'] + 32)
    n['appearanceData']['color'] = {'r': 1.0, 'g': 1.0, 'b': 1.0, 'a': 1.0}
# ---------- 哥特城堡
for name in ('gothic_main', 'gothic_towers', 'gothic_wall'):
    set_pos(one(name), 127, 0, 176)
# ---------- 氛围道具
for p in json.load(open(f'{ROOT}/night/placements.json')):
    if p['name'] in roots:
        set_pos(roots[p['name']][-1], p['x'], p['y'], p['z'])
if 'holy_canopy' in roots:
    no_collision(one('holy_canopy'))
    one('holy_canopy')['appearanceData']['castShadows'] = False
for c in children.get(one('holy_tree')['id'], []):
    if c['nodeName'] == 'glow' and c.get('physicsColliderData'):
        c['physicsColliderData']['enableCollision'] = False
        c['appearanceData']['castShadows'] = False
for c in children.get(one('path_lamps')['id'], []):
    if c['nodeName'] == 'glow' and c.get('physicsColliderData'):
        c['physicsColliderData']['enableCollision'] = False

# ---------- 第二个时之晷：城堡庭院钟楼下
import copy
import random
rnd = random.Random(55)
used = {n['id'] for n in N}


def new_id():
    while True:
        v = rnd.randint(1, 2 ** 31 - 1)
        if v not in used:
            used.add(v)
            return v


def clone(src_node, name=None):
    c = copy.deepcopy(src_node)
    c['id'] = new_id()
    if name:
        c['nodeName'] = name
    kids = []
    for k in children.get(src_node['id'], []):
        kk = copy.deepcopy(k)
        kk['id'] = new_id()
        kk['parentId'] = c['id']
        kids.append(kk)
    N.append(c)
    N.extend(kids)
    children[c['id']] = kids
    return c


if len(roots['time_dial']) < 2:
    src_node = roots['time_dial'][-1]
    c = copy.deepcopy(src_node)
    c['id'] = new_id()
    kids = []
    for k in children.get(src_node['id'], []):
        kk = copy.deepcopy(k)
        kk['id'] = new_id()
        kk['parentId'] = c['id']
        kids.append(kk)
    N.append(c)
    N.extend(kids)
    children[c['id']] = kids
    roots['time_dial'].insert(0, c)
set_pos(roots['time_dial'][0], 117.5, 72.05, 162.5)
# ---------- 天空：缩放等于直径；关碰撞和投影，否则穹顶会把光全挡住
SKY = {
    'sky_dome2': ((128.0, 30.0, 128.0), 1240.0),
    'sky_day': ((128.0, 30.0, 128.0), 1260.0),  # 比夜空略大，编辑器里默认看到夜空
    'sky_moon2': ((30.0, 225.0, 480.0), 150.0),
    'sky_swirl_a': ((128.0, 235.0, 455.0), 560.0),
    'sky_swirl_b': ((128.0, 235.0, 440.0), 470.0),
    'sky_swirl_c': ((128.0, 235.0, 425.0), 330.0),
}
for name, ((x, y, z_), size) in SKY.items():
    n = one(name)
    set_pos(n, x, y, z_)
    n['scale'] = {'x': size, 'y': size, 'z': size}
    no_collision(n)
    n['appearanceData']['castShadows'] = False
# ---------- 其他道具的高度跟着新地形走
for name in ('witch_shop_v2', 'windmill', 'lighthouse', 'arena_gate'):
    if name in roots:
        n = one(name)
        set_pos(n, n['pos']['x'], G(n['pos']['x'], n['pos']['z']) - .1, n['pos']['z'])
set_pos(one('arena'), 127, 32, 172)
# ---------- 民居：避开大树、出生点、盘山路、小山
path = json.load(open(f'{ROOT}/terrain/world/path.json'))
road = [(130, 52), (135, 66), (149, 79), (159, 90), (162, 96), (162, 127), (167, 134), (171, 141)]


def near_road(x, y, r):
    pts = [(a, b) for a, b, _ in path[::3]]
    best = min(math.hypot(x - a, y - b) for a, b in pts + road)
    for (ax, ay), (bx, by) in zip(road, road[1:]):
        dx, dy = bx - ax, by - ay
        t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - ax - t * dx, y - ay - t * dy))
    return best < r


SLOTS = [(176, 60), (188, 66), (182, 79), (170, 88), (196, 82), (186, 95), (176, 124), (190, 128), (200, 140), (184, 146), (196, 158), (178, 160)]
houses = []
for k, count in (('house_a', 3), ('house_b', 4), ('house_c', 3)):
    tpl = roots[k][-1]
    houses.append(tpl)
    for i in range(count - 1):
        houses.append(clone(tpl, f'hs_{k}_{i}'))
rnd.shuffle(houses)
slots = [s for s in SLOTS if not near_road(s[0], s[1], 7) and math.hypot(s[0] - 171, s[1] - 146) > 13]
for n, (x, y) in zip(houses, slots):
    lo = min(G(x + a * 4, y + b * 4) for a in (-1, 0, 1) for b in (-1, 0, 1))
    set_pos(n, x, lo - .05, y, (x * 7 % 50) - 25)
print('houses', len(houses), 'slots', len(slots))
# ---------- 花海：花丛铺开
fc_tpls = [one('flower_clump_a'), one('flower_clump_b'), one('flower_clump_c')]
fc_base = [t['scale']['x'] for t in fc_tpls]
spots = []
tries = 0
while len(spots) < 96 and tries < 6000:
    tries += 1
    a_, d_ = rnd.uniform(0, math.tau), 36 * math.sqrt(rnd.random())
    x, y = 140 + math.cos(a_) * d_ * 1.15, 62 + math.sin(a_) * d_
    if near_road(x, y, 3.6) or math.hypot(x - 153, y - 71) < 5 or math.hypot(x - 121, y - 57) < 4.5 or math.hypot(x - 130, y - 44) < 13:  # 出生点和镜头前后留空，花片不挡视线
        continue
    if G(x, y) < 31 or abs(G(x + 3, y) - G(x - 3, y)) > 2.2 or abs(G(x, y + 3) - G(x, y - 3)) > 2.2:
        continue
    if any(math.hypot(x - a, y - b) < 4.6 for a, b in spots):
        continue
    spots.append((x, y))
for i, (x, y) in enumerate(spots):
    tpl = fc_tpls[i % 3]
    n = tpl if i < 3 else clone(tpl, f'fc_{i}')
    set_pos(n, x, G(x, y) - .03, y, rnd.uniform(0, 360))
    k = rnd.uniform(.9, 1.2)
    base = fc_base[i % 3]
    n['scale'] = {'x': round(base * k, 3), 'y': round(base * k, 3), 'z': round(base * k, 3)}
    no_collision(n)
    n['appearanceData']['castShadows'] = False
print('clumps', len(spots))
# ---------- 烟花、蝙蝠：脚本控制，先放在城堡上空
for kind in ('gold', 'pink', 'blue'):
    tpl = one('firework_' + kind) if 'firework_' + kind in roots else one(f'fw_{kind}_0')
    for i in range(2):
        n = tpl if i == 0 else clone(tpl)
        n['nodeName'] = f'fw_{kind}_{i}'
        set_pos(n, 127, 130, 240)
        no_collision(n)
        n['appearanceData']['castShadows'] = False
tpl = one('bat') if 'bat' in roots else one('bat_0')
for i in range(10):
    n = tpl if i == 0 else clone(tpl)
    n['nodeName'] = f'bat_{i}'
    set_pos(n, 127, 100 + i, 176)
    no_collision(n)
    n['appearanceData']['castShadows'] = False
# ---------- 羊挪到花海以外的西边草地
for i, n in enumerate(roots.get('sheep', [])):
    x, y = 84 + (i * 13) % 34, 42 + (i * 23) % 44
    set_pos(n, x, G(x, y) + .05, y, i * 40)
# ---------- 出生点、样本
for n in N:
    if n['tag'] == 'BornPoint':
        n['pos'] = {'x': 130.0, 'y': round(G(130, 48) + 1.0, 3), 'z': 48.0}
    if n['nodeName'] == '低模刺柏' and n['parentId'] == 0:
        n['pos'] = {'x': 112.0, 'y': round(G(112, 44), 3), 'z': 44.0}
    if n['nodeName'] == '方块' and n['parentId'] == 0:
        n['isActive'] = False
    if n['nodeName'] == '白模_古龙龙巢' and n['parentId'] == 0:
        n['isActive'] = False
d['nodeTransformDatas'] = N
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
print(sorted(k for k in roots))
