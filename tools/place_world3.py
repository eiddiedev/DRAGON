#!/usr/bin/env python3
"""第三版世界摆放：写实地形、松林、会晃的草、森林互动点、龙。可重复运行。
用法：place_world3.py <输入 scene.data> <输出 scene.data>
同名根节点保留最后拖进来的那个。子节点存世界变换，位置和旋转都要跟着父节点。
"""
import json
import math
import os
import sys
import zipfile

import numpy as np

src, out = sys.argv[1:3]
ROOT = '/Users/bytedance/Documents/ChatGPT/DRAGON/assets'
z = zipfile.ZipFile(src)
d = json.loads(z.read('SerializePcgData.json'))
N = d['nodeTransformDatas']
H = np.load(f'{ROOT}/terrain/v3/base_heights.npy')
SITES = json.load(open(f'{ROOT}/terrain/v3/sites.json'))
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


# ---------- 编辑器 AI 生成的模型按描述开头认名字
AI_NAMES = {'一头原创奇幻巨龙': 'dragon_big', '一头原创奇幻坐骑': 'dragon_mount', '一座原创的古老唤龙': 'altar', '一处原创的冒险者': 'camp', '一组原创的发光': 'mush', '一顶原创': 'tent', '一块原创的古老龙纹': 'rune', '一块原创的古老符文': 'rune_old'}
for n in N:
    if n['parentId'] == 0:
        for k, v in AI_NAMES.items():
            if n['nodeName'].startswith(k):
                n['nodeName'] = v
        # 上一轮改过名的模板改回来，方便重复运行
        if n['nodeName'] == 'rune_0':
            n['nodeName'] = 'rune'
        if n['nodeName'] == 'beam_3':
            n['nodeName'] = 'beam_fx'
# ---------- 清理：同名只留最后一个；旧城堡、高架坡道、旧天空去掉；可重复的道具（民居、羊、帆船）不算重复
REPEAT = {'sheep', 'sailboat', '__DouyinWaterArea2Triggers'}
POOLED = ('fw_', 'bat_', 'fc_', 'hs_', 'gr_', 'mush_', 'rune_', 'tent_', 'beam_')  # 脚本克隆出来的节点，重新生成
REMOVE = {'dragon_fly', 'forest', 'flower_clump_a', 'flower_clump_b', 'flower_clump_c', 'castle_walls', 'castle_keep', 'castle_library', 'castle_towers', 'causeway', 'sky_dome', 'sky_swirl', 'sky_moon', 'terrain_tile', 'magic_frame', 'campfire'}
remove = set()
last = {}
for n in N:
    if n['parentId'] != 0:
        continue
    name = n['nodeName']
    if name in ('fw_gold_0', 'fw_pink_0', 'fw_blue_0', 'bat_0'):
        continue  # 第一份是模板，保留
    if name != 'beam_fx' and (name in REMOVE or name.startswith(POOLED) or name in ('flowers_a', 'flowers_b')):
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
tiles = json.load(open(f'{ROOT}/terrain/v3/manifest.json'))
for t in tiles:
    n = one(t['name'])
    set_pos(n, t['x0'] + 32, 0, t['z0'] + 32)
    if n.get('appearanceData'):
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
path = json.load(open(f'{ROOT}/terrain/v3/path.json'))
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
# ---------- 松林
if os.path.exists(f'{ROOT}/forest2/pines.json'):
    for p in json.load(open(f'{ROOT}/forest2/pines.json')):
        if p['name'] in roots:
            n = one(p['name'])
            set_pos(n, p['x'], 0, p['z'])
            no_collision(n)
            n['appearanceData']['castShadows'] = False
# ---------- 会晃的草：贴合地面坡度
TRAILS = SITES['trails']


def trail_dist(x, y):
    best = 1e9
    for tr in TRAILS:
        for (ax, ay), (bx, by) in zip(tr, tr[1:]):
            dx, dy = bx - ax, by - ay
            k = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
            best = min(best, math.hypot(x - ax - k * dx, y - ay - k * dy))
    return best


def qmul(a, b):
    return {'w': a['w'] * b['w'] - a['x'] * b['x'] - a['y'] * b['y'] - a['z'] * b['z'],
            'x': a['w'] * b['x'] + a['x'] * b['w'] + a['y'] * b['z'] - a['z'] * b['y'],
            'y': a['w'] * b['y'] - a['x'] * b['z'] + a['y'] * b['w'] + a['z'] * b['x'],
            'z': a['w'] * b['z'] + a['x'] * b['y'] - a['y'] * b['x'] + a['z'] * b['w']}


def set_tilted(n, x, y, z_, deg):
    """放到地面上，按坡度倾斜。"""
    e = 1.6
    nx = G(x - e, z_) - G(x + e, z_)
    nz = G(x, z_ - e) - G(x, z_ + e)
    ny = 2 * e
    ln = math.sqrt(nx * nx + ny * ny + nz * nz)
    nx, ny, nz = nx / ln, ny / ln, nz / ln
    # 把 +Y 转到地面法线
    ax, az = nz, -nx
    s = math.sqrt(ax * ax + az * az)
    ang = math.atan2(s, ny)
    if s > 1e-5:
        tilt = {'w': math.cos(ang / 2), 'x': ax / s * math.sin(ang / 2), 'y': 0.0, 'z': az / s * math.sin(ang / 2)}
    else:
        tilt = {'w': 1.0, 'x': 0.0, 'y': 0.0, 'z': 0.0}
    q = qmul(tilt, yaw_q(deg))
    q = {k: round(v, 6) for k, v in q.items()}
    p = {'x': round(float(x), 4), 'y': round(float(y), 4), 'z': round(float(z_), 4)}
    n['pos'], n['rot'] = p, q
    for c in children.get(n['id'], []):
        c['pos'], c['rot'] = dict(p), dict(q)


if 'grass_c' in roots:
    tpl_c = one('grass_c')
    tpl_a = one('grass_a') if 'grass_a' in roots else tpl_c
    tpl_b = one('grass_b') if 'grass_b' in roots else tpl_c
    occ, spots = {}, []

    def ok_spot(x, y, r):
        key = (int(x / r), int(y / r))
        if any((key[0] + a, key[1] + b) in occ for a in (-1, 0, 1) for b in (-1, 0, 1)):
            return False
        occ[key] = 1
        return True

    # 花海
    for _ in range(40000):
        a_, d_ = rnd.uniform(0, math.tau), 37 * math.sqrt(rnd.random())
        x, y = 140 + math.cos(a_) * d_ * 1.15, 62 + math.sin(a_) * d_
        if near_road(x, y, 3.0) or math.hypot(x - 153, y - 71) < 2.8 or math.hypot(x - 121, y - 57) < 4 or math.hypot(x - 130, y - 45) < 7.5:
            continue
        if G(x, y) < 31 or abs(G(x + 3, y) - G(x - 3, y)) > 3.2 or abs(G(x, y + 3) - G(x, y - 3)) > 3.2:
            continue
        if ok_spot(x, y, 2.5):
            spots.append((x, y, 'c'))
    nc = len(spots)
    # 路边和森林空地的草，疏密不一
    for _ in range(60000):
        x, y = rnd.uniform(4, 240), rnd.uniform(4, 215)
        g = G(x, y)
        steep_ok = 6.0 if math.hypot(x - 127, y - 176) < 46 else 3.2   # 小山陡坡上也铺草，盖住拉伸的贴图
        if g < 31 or g > 72 or abs(G(x + 3, y) - G(x - 3, y)) > steep_ok or abs(G(x, y + 3) - G(x, y - 3)) > steep_ok:
            continue
        if math.hypot((x - 140) / 1.15, y - 62) < 38 or math.hypot(x - 127, y - 176) < 20:
            continue
        d_r = 99 if not near_road(x, y, 9) else (0 if near_road(x, y, 2.8) else 5)
        d_t = trail_dist(x, y)
        if d_t < 1.8 or any(math.hypot(x - s['x'], y - s['z']) < s['r'] * .55 for s in SITES['sites'].values()):
            continue
        near = d_r < 9 or d_t < 9 or any(math.hypot(x - s['x'], y - s['z']) < s['r'] + 9 for s in SITES['sites'].values()) or math.hypot(x - 127, y - 176) < 46
        if not near and rnd.random() > .18:
            continue
        if ok_spot(x, y, 3.2):
            spots.append((x, y, 'a' if rnd.random() < .78 else 'b'))
        if len(spots) > nc + 300:
            break
    print('grass', nc, len(spots) - nc)
    gr_base = dict(a=tpl_a['scale']['x'], b=tpl_b['scale']['x'], c=tpl_c['scale']['x'])
    tpls = dict(a=tpl_a, b=tpl_b, c=tpl_c)
    grass_list = []
    for i, (x, y, kind) in enumerate(spots):
        n = clone(tpls[kind], f'gr_{i}')
        n['isActive'] = True
        set_tilted(n, x, G(x, y) - .04, y, rnd.uniform(0, 360))
        k = rnd.uniform(.9, 1.15) * gr_base[kind]
        n['scale'] = {'x': round(k, 3), 'y': round(k, 3), 'z': round(k, 3)}
        no_collision(n)
        n['appearanceData']['castShadows'] = False
        for c in children.get(n['id'], []):
            c['scale'] = dict(n['scale'])
    for tp in tpls.values():
        tp['isActive'] = False
    json.dump(len(spots), open(f'{ROOT}/grass/count.json', 'w'))
# ---------- 细节贴图载体：藏在地下，运行时脚本取走贴图
for name in ('detail_grass', 'detail_rock'):
    if name in roots:
        n = one(name)
        set_pos(n, 128, -18, 128)
        no_collision(n)
        n['appearanceData']['castShadows'] = False
# ---------- 森林互动点和龙（缩放等于最大边长）
S_ = SITES['sites']


def put(name, x, z_, size, deg=0.0, y=None, solid=True):
    if name not in roots:
        print('skip', name)
        return None
    n = one(name)
    yy = G(x, z_) - .05 if y is None else y
    set_pos(n, x, yy, z_, deg)
    n['scale'] = {'x': size, 'y': size, 'z': size}
    for c in children.get(n['id'], []):
        c['scale'] = dict(n['scale'])
    if not solid:
        no_collision(n)
    return n


put("camp", S_["camp"]["x"], S_["camp"]["z"], 4.4, 30)
if 'tent' in roots:
    put('tent', S_['camp']['x'] + 6, S_['camp']['z'] + 5, 4.6, -130)
    t2 = clone(one('tent'), 'tent_1')
    set_pos(t2, S_['camp']['x'] - 6.5, G(S_['camp']['x'] - 6.5, S_['camp']['z'] + 4) - .05, S_['camp']['z'] + 4, 140)
if 'mush' in roots:
    tpl = one('mush')
    cx, cz = S_['mush']['x'], S_['mush']['z']
    for i in range(6):
        a_ = i / 6 * math.tau + .4
        r_ = 9.5 + (i % 2) * 1.6
        x, z2 = cx + math.cos(a_) * r_, cz + math.sin(a_) * r_
        n = tpl if i == 0 else clone(tpl, f'mush_{i}')
        set_pos(n, x, G(x, z2) - .05, z2, i * 67)
        k = 3.2 + (i * 37 % 5) * .6
        n['scale'] = {'x': k, 'y': k, 'z': k}
        for c in children.get(n['id'], []):
            c['scale'] = dict(n['scale'])
put('altar', S_['altar']['x'], S_['altar']['z'], 13, 180)
if 'rune' in roots:
    tpl = one('rune')
    cx, cz = S_['altar']['x'], S_['altar']['z']
    for i in range(3):
        a_ = math.radians(-90 + i * 120)
        x, z2 = cx + math.cos(a_) * 12, cz + math.sin(a_) * 12
        n = tpl if i == 0 else clone(tpl, f'rune_{i}')
        n['nodeName'] = f'rune_{i}'
        set_pos(n, x, G(x, z2) - .1, z2, -math.degrees(a_) + 90)
        n['scale'] = {'x': 5.2, 'y': 5.2, 'z': 5.2}
        for c in children.get(n['id'], []):
            c['scale'] = dict(n['scale'])
put('dragon_mount', S_['perch']['x'], S_['perch']['z'], 6, 200, y=G(S_['perch']['x'], S_['perch']['z']) + .3, solid=False)
# 篝火、光柱、火星
def fx(name, x, y, z2, size, newname=None):
    n = one(name) if newname is None else clone(one(name), newname)
    set_pos(n, x, y, z2)
    n['scale'] = {'x': size, 'y': size, 'z': size}
    for c in children.get(n['id'], []):
        c['scale'] = dict(n['scale'])
    no_collision(n)
    n['appearanceData']['castShadows'] = False
    return n


if 'fire_fx' in roots:
    cx, cz = S_['camp']['x'], S_['camp']['z']
    fx('fire_fx', cx, G(cx, cz) + .2, cz, 1.9)
if 'spark_fx' in roots:
    cx, cz = S_['camp']['x'], S_['camp']['z']
    fx('spark_fx', cx, G(cx, cz) + 1, cz, 3.5)
if 'beam_fx' in roots:
    cx, cz = S_['altar']['x'], S_['altar']['z']
    for i in range(3):
        a_ = math.radians(-90 + i * 120)
        x, z2 = cx + math.cos(a_) * 12, cz + math.sin(a_) * 12
        fx('beam_fx', x, G(x, z2) + .2, z2, 24, f'beam_{i}')
    mx, mz = S_['mush']['x'], S_['mush']['z']
    fx('beam_fx', mx, G(mx, mz) + .05, mz, 2.6, 'beam_4')   # 蘑菇林中央的弹跳光圈
    b3 = one('beam_fx')
    b3['nodeName'] = 'beam_3'
    set_pos(b3, cx, G(cx, cz) + 3, cz)
    b3['scale'] = {'x': 120, 'y': 120, 'z': 120}
    for c in children.get(b3['id'], []):
        c['scale'] = dict(b3['scale'])
    no_collision(b3)
    b3['appearanceData']['castShadows'] = False
# 巨龙：蹲在北面主峰上俯瞰全图；白天另有一条绕城堡盘旋
if 'dragon_big' in roots:
    px, pz = 182, 226
    put('dragon_big', px, pz, 40, 200, y=G(px, pz) + 1, solid=False)
    fly = clone(one('dragon_big'), 'dragon_fly')
    set_pos(fly, 127, 120, 176)
    no_collision(fly)
    fly['scale'] = {'x': 38, 'y': 38, 'z': 38}
    for c in children.get(fly['id'], []):
        c['scale'] = dict(fly['scale'])
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
