#!/usr/bin/env python3
"""第六版世界摆放：回到原生地形（不下沉、重画材质），植被换成公共库的树和草。
第五版世界摆放：真实几何的植被、城堡房间、一条站在山尖的冰龙、飞毯。可重复运行。
用法：place_world3.py <输入 scene.data> <输出 scene.data>
同名根节点保留最后拖进来的那个。子节点存世界变换，位置和旋转都要跟着父节点。
"""
import json
import re
import math
import os
import sys
import zipfile

import numpy as np

src, out = sys.argv[1:3]
ROOT = '/Users/a1234/Documents/awesomeWRLD/assets'
z = zipfile.ZipFile(src)
d = json.loads(z.read('SerializePcgData.json'))
N = d['nodeTransformDatas']
H = np.load(f'{ROOT}/terrain/v3/base_heights.npy')
H = np.fromfile(f'{ROOT}/terrain/native/heights.f32', '<f4').reshape(257, 257).astype(np.float64) * 256  # 实际地面（原生地形）
SITES = json.load(open(f'{ROOT}/terrain/v3/sites.json'))
SINK = 0.0  # 原生地形就是地面，不再下沉
WATER_SCALE = 8.0
MUSIC_URI = 'hamlet-ugc/aigc_editor/dev/unity/MS4wLjABAAAAiXeSmRTg5HzBJoZQNA48Huyphyi10N36i8B2izzYJ3Y/ymph7136yvyafmdh.wav'


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
        if n['nodeName'].startswith('sailboat_'):
            n['nodeName'] = 'sailboat'
        if n['nodeName'] == 'rune_0':
            n['nodeName'] = 'rune'
        if n['nodeName'] == 'beam_3':
            n['nodeName'] = 'beam_fx'
# ---------- 清理：同名只留最后一个；旧城堡、高架坡道、旧天空去掉；可重复的道具（民居、羊、帆船）不算重复
REPEAT = {'sailboat', '__DouyinWaterArea2Triggers'}
SAILS = ('sailboat_0', 'sailboat_1', 'sailboat_2')
POOLED = ('pl_', 'cl_', 'fw_', 'bat_', 'fc_', 'hs_', 'gr_', 'mush_', 'rune_', 'runeg_', 'tent_', 'beam_', 'test_', 'sheep_')  # 脚本克隆出来的节点，重新生成
REMOVE = {'shd_w', 'shd_b', 'shd_h', 'ice_dragon', 'ice_dragon_h', 'ice_dragon_w', 'gr3_a', 'gr3_b', 'gr3_c', 'pine_far', *{f'pine_{i}' for i in range(40)}, 'field_all', 'dragon_fly', 'dragon_big', 'dragon_mount', 'altar', 'rune', 'rune_old', 'sheep', 'bat', 'grass_a', 'grass_b', 'grass_c', 'holy_tree', 'holy_canopy', 'path_lamps', 'pines_0_0', 'pines_0_1', 'pines_1_0', 'pines_1_1', 'test_skin', 'test_parts', 'test_vcol', 'forest', 'flower_clump_a', 'flower_clump_b', 'flower_clump_c', 'castle_walls', 'castle_keep', 'castle_library', 'castle_towers', 'causeway', 'firework_gold', 'firework_pink', 'firework_blue', 'fw_gold_0', 'fw_pink_0', 'fw_blue_0', 'sky_dome', 'sky_swirl', 'sky_moon', 'terrain_tile', 'magic_frame', 'campfire'}
remove = set()
last = {}
for n in N:
    if n['parentId'] != 0:
        continue
    name = n['nodeName']
    if re.match(r'^t\d{3}_\d{3}$', name) or name.startswith(('gc_', 'pn_', 'pf_')) or name in ('pine_trunks', 'detail_grass', 'detail_rock'):
        remove |= set(subtree(n))
    elif name != 'beam_fx' and (name in REMOVE or name.startswith(POOLED) or name in ('flowers_a', 'flowers_b')):
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

    def rec(q):
        for c in children.get(q['id'], []):
            c['pos'] = dict(p)
            c['rot'] = dict(n['rot'])
            rec(c)

    rec(n)


def no_collision(n):
    if n.get('physicsColliderData'):
        n['physicsColliderData']['enableCollision'] = False
    for c in children.get(n['id'], []):
        no_collision(c)


def one(name):
    return roots[name][-1]


# ---------- 地形块：贴图重画了，不再压暗
tiles = json.load(open(f'{ROOT}/terrain/v3/manifest.json'))
for t in tiles:
    if t['name'] not in roots:
        continue
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
HT = (160.5, 74.0)
set_pos(one('holy_tree3'), HT[0], G(*HT) - .1, HT[1])
set_pos(one('holy_canopy3'), HT[0], G(*HT) - .1, HT[1])
no_collision(one('holy_canopy3'))
one('holy_canopy3')['appearanceData']['castShadows'] = False
set_pos(one('holy_canopy4'), HT[0], G(*HT) - .1, HT[1])
no_collision(one('holy_canopy4'))
one('holy_canopy4')['appearanceData']['castShadows'] = False
# 路灯
set_pos(one('lamp_posts'), 128, 0, 128)
set_pos(one('lamp_glow'), 128, 0, 128)
no_collision(one('lamp_glow'))
one('lamp_glow')['appearanceData']['castShadows'] = False
# 城堡房间
set_pos(one('castle_rooms'), 127, 0, 176)
set_pos(one('rooms_glow'), 127, 0, 176)
no_collision(one('rooms_glow'))
one('rooms_glow')['appearanceData']['castShadows'] = False
# 暗影龙和山岩：龙头朝东南偏向玩家，左边高翼，脚踩岩台
PJ = json.load(open(f'{ROOT}/dragon/final/peak.json'))
DRAGON_DEG = 35
for nm in ('shd_wa', 'shd_wb', 'shd_body', 'shd_tail', 'shd_head', 'shd_legs'):
    if nm not in roots:
        continue
    set_pos(one(nm), PJ['ox'], PJ['top'] - .3, PJ['oz'], DRAGON_DEG)
    no_collision(one(nm))
    for c_ in [one(nm)] + children.get(one(nm)['id'], []):
        if c_.get('appearanceData'):
            c_['appearanceData']['castShadows'] = False
set_pos(one('dragon_peak'), PJ['ox'], 0, PJ['oz'])
one('dragon_peak')['scale'] = {'x': PJ['size'], 'y': PJ['size'], 'z': PJ['size']}
for c_ in children.get(one('dragon_peak')['id'], []):
    c_['scale'] = dict(one('dragon_peak')['scale'])
no_collision(one('dragon_peak'))
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
    N.append(c)
    children[c['id']] = []

    def rec(old, new_parent):
        for k in children.get(old['id'], []):
            kk = copy.deepcopy(k)
            kk['id'] = new_id()
            kk['parentId'] = new_parent['id']
            N.append(kk)
            children.setdefault(new_parent['id'], []).append(kk)
            children[kk['id']] = []
            rec(k, kk)

    rec(src_node, c)
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
# ---------- 松林：精细枝叶（近）、三层枝叶裙（远）、树干（带碰撞）
for p in json.load(open(f'{ROOT}/veg3d/pines_fine.json')):
    if p['name'] in roots:
        n = one(p['name'])
        set_pos(n, p['x'], 0, p['z'])
        no_collision(n)
        n['appearanceData']['castShadows'] = False
for nm in json.load(open(f'{ROOT}/veg3d/pines_far.json')):
    if nm in roots:
        n = one(nm)
        set_pos(n, 128, 0, 128)
        no_collision(n)
        n['appearanceData']['castShadows'] = False
if 'pine_trunks' in roots:
    n = one('pine_trunks')
    set_pos(n, 128, 0, 128)
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


for c_ in json.load(open(f'{ROOT}/grass4/chunks.json')):
    if c_['name'] in roots:
        n = one(c_['name'])
        set_pos(n, c_['x'], c_['y'], c_['z'])
        no_collision(n)
        n['appearanceData']['castShadows'] = False
# ---------- 白天的云：一圈远云
rc = random.Random(9)
for i in range(16):
    k = i % 5
    nm = f'cloud_{k}'
    if nm not in roots:
        continue
    n = clone(one(nm), f'cl_{i}')
    n['isActive'] = True
    a_ = i / 16 * 360 + rc.uniform(-8, 8)
    r_ = rc.uniform(430, 560)
    x, z2 = 128 + math.cos(math.radians(a_)) * r_, 128 + math.sin(math.radians(a_)) * r_
    set_pos(n, x, rc.uniform(110, 260), z2, a_ - 90)
    sc = rc.uniform(230, 460)
    n['scale'] = {'x': sc, 'y': sc, 'z': sc}
    no_collision(n)
    n['appearanceData']['castShadows'] = False
for k in range(5):
    if f'cloud_{k}' in roots:
        one(f'cloud_{k}')['isActive'] = False
# ---------- 船：靠在码头边，能开
MOOR = [(206, 98, 90), (218, 70, 90), (234, 110, 200)]  # 都在开阔海面上
for i, n in enumerate(roots.get('sailboat', [])):
    n['nodeName'] = f'sailboat_{i}'
    set_pos(n, MOOR[i][0], 26.9, MOOR[i][1], MOOR[i][2])
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
def keep(name, x, z_, deg=0.0, y=None, solid=True):
    """真实尺寸的模型：不改缩放。"""
    n = one(name)
    yy = G(x, z_) - .05 if y is None else y
    set_pos(n, x, yy, z_, deg)
    if not solid:
        no_collision(n)
    return n


ax_, az_ = S_['altar']['x'], S_['altar']['z']
keep('altar3', ax_, az_)
g3 = keep('altar3_glow', ax_, az_, solid=False)
g3['appearanceData']['castShadows'] = False
tpl_r, tpl_g = one('rune3'), one('rune3_glow')
for i in range(3):
    a_ = -90 + i * 120
    x, z2 = ax_ + math.cos(math.radians(a_)) * 12, az_ + math.sin(math.radians(a_)) * 12
    r_ = clone(tpl_r)
    g_ = clone(tpl_g)
    r_['isActive'] = g_['isActive'] = True
    r_['nodeName'] = f'rune_{i}'
    g_['nodeName'] = f'runeg_{i}'
    set_pos(r_, x, G(x, z2) - .15, z2, a_ - 90)
    set_pos(g_, x, G(x, z2) - .15, z2, a_ - 90)
    no_collision(g_)
    g_['appearanceData']['castShadows'] = False
tpl_r['isActive'] = tpl_g['isActive'] = False
c3 = keep('flying_carpet', S_['perch']['x'], S_['perch']['z'], 200, y=G(S_['perch']['x'], S_['perch']['z']) + .75, solid=False)
c3['appearanceData'] and c3['appearanceData'].update(castShadows=False)
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
# ---------- 烟花、蝙蝠：脚本控制，先放在城堡上空
FW_SPOTS = []  # 用户要求：背后不要烟花
for i, (nm, x_, y_, z2_) in enumerate(FW_SPOTS):
    if nm not in roots:
        continue
    n = clone(one(nm), f'fw_{i}')
    n['isActive'] = True
    set_pos(n, x_, y_, z2_)
    no_collision(n)
    n['appearanceData'] and n['appearanceData'].update(castShadows=False)
for nm in ('fwx_a', 'fwx_b', 'fwx_c'):
    if nm in roots:
        one(nm)['isActive'] = False
tpl = one('bat3')
tpl['isActive'] = True
for i in range(10):
    n = clone(tpl)
    n['nodeName'] = f'bat_{i}'
    set_pos(n, 127, 100 + i, 176)
    no_collision(n)
    n['appearanceData'] and n['appearanceData'].update(castShadows=False)
tpl['isActive'] = False
# ---------- 绵羊：9 只，脚本让它们走动吃草
tpl = one('sheep3')
tpl['isActive'] = True
for i in range(9):
    n = clone(tpl)
    n['nodeName'] = f'sheep_{i}'
    x, y = 84 + (i * 13) % 34, 42 + (i * 23) % 44
    set_pos(n, x, G(x, y) + .05, y, i * 40)
    no_collision(n)
tpl['isActive'] = False
# ---------- 公共库植被：松树、灌木（模型），青草和野花（官方贴片植物）
PLANT_TPL = {'tree': '松树01', 'bush': '翠绿灌木02', 'grass': '青草01', 'forget': '勿忘草01', 'lav': '薰衣草01', 'tail': '狼尾草02'}
prnd = random.Random(808)
road_pts = [(p[0], p[1]) for p in path]
house_pts = [(n['pos']['x'], n['pos']['z']) for n in N if n['parentId'] == 0 and n['nodeName'].startswith(('hs_', 'house_', 'witch_shop', 'windmill', 'lighthouse', 'arena_gate', 'camp', 'tent'))]
SITE_PTS = [(v['x'], v['z'], v['r']) for v in S_.values()] + [(130, 48, 7), (121, 57, 4), (160.5, 74, 7), (127, 176, 30), (165, 234, 30), (48, 150, 18)]


def slope_at(px, pz):
    e = 1.0
    return math.degrees(math.atan(math.hypot(G(px + e, pz) - G(px - e, pz), G(px, pz + e) - G(px, pz - e)) / (2 * e)))


def near_any(px, pz, pts, r):
    return any((px - a) ** 2 + (pz - b) ** 2 < r * r for a, b in pts)


def free_spot(px, pz, road_r=2.6, house_r=6.0):
    if not (4 < px < 252 and 4 < pz < 252):
        return False
    h = G(px, pz)
    if h < 28.6 or h > 78:
        return False
    if near_any(px, pz, road_pts, road_r) or near_any(px, pz, house_pts, house_r):
        return False
    if any((px - a) ** 2 + (pz - b) ** 2 < r * r for a, b, r in SITE_PTS):
        return False
    return True


def plant(kind, i, px, pz, deg, k, solid=False, shadow=False):
    tpl = one(PLANT_TPL[kind])
    n = clone(tpl, f'pl_{kind}_{i}')
    n['isActive'] = True
    y0 = G(px, pz) - (.15 if kind in ('tree', 'bush') else .02)
    set_pos(n, px, y0, pz, deg)
    base = tpl['scale']
    n['scale'] = {'x': base['x'] * k, 'y': base['y'] * k, 'z': base['z'] * k}
    # 公共库模型的子节点存的是相对缩放（1），位置是世界坐标：按模板里的偏移旋转、缩放后放回去
    tq = tpl['rot']
    t_yaw = 2 * math.atan2(tq['y'], tq['w'])
    nq = n['rot']
    n_yaw = 2 * math.atan2(nq['y'], nq['w'])
    dy = n_yaw - t_yaw
    for c, tc in zip(children.get(n['id'], []), children.get(tpl['id'], [])):
        ox, oy, oz = tc['pos']['x'] - tpl['pos']['x'], tc['pos']['y'] - tpl['pos']['y'], tc['pos']['z'] - tpl['pos']['z']
        rx = ox * math.cos(dy) + oz * math.sin(dy)
        rz = -ox * math.sin(dy) + oz * math.cos(dy)
        c['pos'] = {'x': px + rx * k, 'y': y0 + oy * k, 'z': pz + rz * k}
        c['scale'] = dict(tc['scale'])
    if not solid:
        no_collision(n)
    for c in [n] + children.get(n['id'], []):
        if c.get('appearanceData'):
            c['appearanceData']['castShadows'] = shadow
    if kind in ('grass', 'tail') and n.get('appearanceData'):
        n['appearanceData']['color'] = {'r': .74, 'g': .84, 'b': .66, 'a': 1.0}
    return n


if all(v in roots for v in PLANT_TPL.values()):
    # 松林：沿用原来的森林分布，最小间距 4 米
    trees = json.load(open(f'{ROOT}/forest2/trees.json'))
    prnd.shuffle(trees)
    occ, nt = set(), 0
    for px, pz, _y in trees:
        key = (int(px / 4), int(pz / 4))
        if key in occ or not free_spot(px, pz, 3.0, 7.0) or slope_at(px, pz) > 40:
            continue
        # 出生镜头朝北偏东看城堡和龙，这个扇形里 150 米内不种树
        ang = math.degrees(math.atan2(px - 130, pz - 48))
        if math.hypot(px - 130, pz - 48) < 150 and -28 < ang < 52:
            continue
        occ |= {(key[0] + a, key[1] + b) for a in (-1, 0, 1) for b in (-1, 0, 1)}
        ht = prnd.uniform(1.4, 2.3)          # 模型默认 4.7 米高，放大到 6.5~11 米
        plant('tree', nt, px, pz, prnd.uniform(0, 360), ht, solid=True, shadow=True)
        nt += 1
        if nt >= 300:
            break
    # 林缘灌木
    nb = 0
    for px, pz, _y in trees[::5]:
        px += prnd.uniform(-4, 4); pz += prnd.uniform(-4, 4)
        if free_spot(px, pz) and slope_at(px, pz) < 35:
            plant('bush', nb, px, pz, prnd.uniform(0, 360), prnd.uniform(.8, 1.4))
            nb += 1
            if nb >= 90:
                break
    # 青草：5 米网格抖动，平缓处才种，越靠近出生点和小路越密
    ng = nf = nl = nw = 0
    for gz in range(5, 251, 3):
        for gx in range(5, 251, 3):
            px, pz = gx + prnd.uniform(-1.4, 1.4), gz + prnd.uniform(-1.4, 1.4)
            if not free_spot(px, pz) or slope_at(px, pz) > 30:
                continue
            d_spawn = math.hypot(px - 130, pz - 60)
            keep_p = .95 if d_spawn < 80 else .7
            if prnd.random() > keep_p:
                continue
            if math.hypot(px - 150, pz - 62) < 22 and prnd.random() < .8:
                plant('lav', nl, px, pz, prnd.uniform(0, 360), prnd.uniform(1.0, 1.5)); nl += 1
                continue
            r_ = prnd.random()
            if r_ < .08:
                plant('forget', nf, px, pz, prnd.uniform(0, 360), prnd.uniform(.9, 1.4)); nf += 1
            elif r_ < .14 and G(px, pz) < 34:
                plant('tail', nw, px, pz, prnd.uniform(0, 360), prnd.uniform(.9, 1.3)); nw += 1
            else:
                plant('grass', ng, px, pz, prnd.uniform(0, 360), prnd.uniform(.8, 1.25)); ng += 1
    for v in PLANT_TPL.values():
        one(v)['isActive'] = False
    print('plants trees', nt, 'bushes', nb, 'grass', ng, 'forget', nf, 'lav', nl, 'tail', nw)

# ---------- 出生点、样本
for n in N:
    if n['tag'] == 'BornPoint':
        n['pos'] = {'x': 130.0, 'y': round(G(130, 48) + 1.0, 3), 'z': 48.0}
    if n['nodeName'] == '低模刺柏' and n['parentId'] == 0:
        n['pos'] = {'x': 112.0, 'y': round(G(112, 44) - 30, 3), 'z': 44.0}  # 脚本挂在它身上，藏到地下
    if n['nodeName'] == '方块' and n['parentId'] == 0:
        n['isActive'] = False
    if n['nodeName'] == '白模_古龙龙巢' and n['parentId'] == 0:
        n['isActive'] = False
for n in N:
    if n['nodeName'] == '海洋':
        n['scale'] = {'x': WATER_SCALE, 'y': 1.0, 'z': WATER_SCALE}
d['nodeTransformDatas'] = N
# 背景音乐只认官方曲库，保留编辑器里选的曲目
sunk = np.fromfile(f'{ROOT}/terrain/native/heights.f32', '<f4').reshape(257, 257)  # 原生地形用重建的地面
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as w:
    for i in z.infolist():
        data = z.read(i.filename)
        if i.filename == 'SerializePcgData.json':
            data = json.dumps(d, ensure_ascii=False, separators=(',', ':')).encode()
        elif i.filename == 'MatCoverTex_3193404.png':
            data = open(f'{ROOT}/terrain/native/MatCoverTex.png', 'rb').read()
        elif i.filename.startswith('SplatMap_3193404_'):
            k = int(i.filename.split('_')[-1].split('.')[0])
            data = open(f'{ROOT}/terrain/native/SplatMap_{k}.png', 'rb').read()
        elif i.filename == 'HeightMap_3193404.data':
            data = sunk.astype('<f4').tobytes()
        ni = zipfile.ZipInfo(i.filename, i.date_time)
        ni.compress_type = zipfile.ZIP_DEFLATED
        ni.external_attr = i.external_attr
        w.writestr(ni, data)
print('nodes', len(N), 'roots', sum(1 for n in N if n['parentId'] == 0))
print(sorted(k for k in roots))
