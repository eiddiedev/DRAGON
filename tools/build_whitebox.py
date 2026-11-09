#!/usr/bin/env python3
"""龙眠之境白模生成器：读 scene.data，把基础方块搭成的体量写入一个新存档。

重复运行是安全的：所有白模都挂在名字以「白模_」开头的分组下，运行时会先清掉旧的。
用法：build_whitebox.py <输入 scene.data> <输出 scene.data> <boxes.json>
"""
import copy
import json
import math
import random
import sys
import zipfile
import zlib

import numpy as np

src, out, dump = sys.argv[1:4]
z = zipfile.ZipFile(src)
scene = json.loads(z.read('SerializePcgData.json'))
H = np.frombuffer(z.read('HeightMap_3193404.data'), '<f4').reshape(257, 257).astype(float) * 256
SEA = 27.0
nodes = scene['nodeTransformDatas']

cube_tpl = next(n for n in nodes if n['nodeName'] == '方块' and not n['nodeName'].startswith('白模'))
group_tpl = next(n for n in nodes if n['nodeName'] == '水体')

STONE = (.85, .83, .77)
STONE_D = (.70, .69, .66)
SLATE = (.40, .48, .60)
ROOF = (.77, .32, .22)
CREAM = (.93, .88, .76)
WOOD = (.45, .32, .22)
DRAGON = (.16, .42, .40)
GOLD = (.89, .66, .23)
LIGHT = (1.0, .85, .45)
VIOLET = (.46, .34, .70)
WHITE = (.96, .96, .94)
DARK = (.16, .17, .20)
FIRE = (1.0, .48, .15)


def G(x, z_):
    x = min(max(x, 0), 255.999)
    z_ = min(max(z_, 0), 255.999)
    x0, z0 = int(x), int(z_)
    fx, fz = x - x0, z_ - z0
    return float(H[z0, x0] * (1 - fx) * (1 - fz) + H[z0, x0 + 1] * fx * (1 - fz)
                 + H[z0 + 1, x0] * (1 - fx) * fz + H[z0 + 1, x0 + 1] * fx * fz)


def Gmin(x, z_, sx, sz):
    return min(G(x + a * sx / 2, z_ + b * sz / 2) for a in (-1, 0, 1) for b in (-1, 0, 1))


def Gmax(x, z_, sx, sz):
    return max(G(x + a * sx / 2, z_ + b * sz / 2) for a in (-1, 0, 1) for b in (-1, 0, 1))


def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def qaxis(axis, deg):
    s, c = math.sin(math.radians(deg) / 2), math.cos(math.radians(deg) / 2)
    return tuple(s * v for v in axis) + (c,)


def rot(yaw=0.0, pitch=0.0, roll=0.0):
    # Unity order: yaw(Y) * pitch(X) * roll(Z); yaw 0 faces +z (north)
    return qmul(qmul(qaxis((0, 1, 0), yaw), qaxis((1, 0, 0), pitch)), qaxis((0, 0, 1), roll))


boxes = []
group = ['']


def box(name, cx, y0, cz, sx, sy, sz, color, q=(0, 0, 0, 1)):
    boxes.append(dict(group=group[0], name=name, pos=(cx, y0 + sy / 2, cz), scale=(sx, sy, sz), rot=q, color=color))


def centered(name, cx, cy, cz, sx, sy, sz, color, q=(0, 0, 0, 1)):
    boxes.append(dict(group=group[0], name=name, pos=(cx, cy, cz), scale=(sx, sy, sz), rot=q, color=color))


def column(name, cx, cz, sx, sz, top, color):
    """方块从地下一直立到 top，保证不会悬空。"""
    y0 = Gmin(cx, cz, sx, sz) - 2
    box(name, cx, y0, cz, sx, top - y0, sz, color)


def steps(name, cx, cz, w, y, height, color, n=3):
    """用层层收窄的方块代替锥形屋顶。"""
    for i in range(n):
        s = w * (1 - i / n)
        box(f'{name}_{i + 1}', cx, y + height * i / n, cz, s, height / n, s, color)


def beam(name, a, b, width, thick, color):
    """连接两个世界坐标点的斜面（坡道、桥面）。"""
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    run = math.hypot(dx, dz)
    q = rot(math.degrees(math.atan2(dx, dz)), -math.degrees(math.atan2(dy, run)))
    centered(name, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - thick / 2, (a[2] + b[2]) / 2,
             width, thick, math.hypot(run, dy), color, q)


# ---------------------------------------------------------------- 星塔城堡
group[0] = '白模_星塔城堡'
X0, X1, Z0, Z1 = 102, 152, 152, 194
T1, T2 = 61, 67  # 下层、上层平台顶面高度
WT = 63  # 城墙顶高度（台地东缘地面约 58 米）
for name, cx, cz, sx, sz in [('南墙', 127, Z0, 50, 2), ('北墙', 127, Z1, 50, 2), ('西墙', X0, 173, 2, 42),
                             ('东墙南段', X1, 156, 2, 8), ('东墙北段', X1, 182, 2, 24)]:
    column(name, cx, cz, sx, sz, WT, STONE)
box('城门门楣', X1, WT - 1, 165, 2.4, 2, 10, STONE_D)
for name, cx, cz in [('东南角塔', X1, Z0), ('东北角塔', X1, Z1), ('西南角塔', X0, Z0)]:
    column(name, cx, cz, 7, 7, 71, STONE)
    steps(name + '尖顶', cx, cz, 8.5, 71, 9, SLATE)
for name, cz in [('城门塔南', 160), ('城门塔北', 170)]:
    column(name, X1, cz, 5, 5, 68, STONE)
    steps(name + '尖顶', X1, cz, 6, 68, 6, SLATE)

# 下层平台 + 上层平台 + 主楼，从南往北一层层抬高
column('下层平台', 124, 174, 28, 32, T1, STONE_D)
beam('下层坡道', (151, G(151, 165) + .2, 165), (138, T1, 165), 7, 1, STONE_D)
column('上层平台', 128, 178, 16, 16, T2, STONE)
beam('上层坡道', (128, T1, 158.5), (128, T2, 170), 6, 1, STONE_D)
box('主楼', 128, T2, 178, 12, 13, 12, STONE)
steps('主楼尖顶', 128, 178, 15, T2 + 13, 15, SLATE, 4)
box('主楼前塔', 128, T2, 171.5, 5, 18, 5, STONE)
steps('前塔尖顶', 128, 171.5, 6.5, T2 + 18, 8, SLATE)

# 浮空图书馆（下层平台西侧的长厅）
box('图书馆', 114.5, T1, 174, 8, 8, 26, CREAM)
centered('图书馆屋顶', 114.5, T1 + 8, 174, 7, 7, 27, SLATE, rot(0, 0, 45))
for i, dz in enumerate((-8, 0, 8)):
    box(f'图书馆浮空书{i + 1}', 121, T1 + 3.5, 174 + dz, 1.4, .3, 1.8, LIGHT)

# 天文塔 · 扫帚起飞台（全图最细最高）
column('天文塔', 103, 193, 6, 6, 96, STONE)
box('起飞台', 103, 96, 193, 13, 1, 13, STONE_D)
box('天文穹顶', 103, 97, 193, 5.5, 3, 5.5, SLATE)
for i, dx in enumerate((-4.5, -3, -1.5)):
    box(f'扫帚{i + 1}', 103 + dx, 97, 188, .3, 3, .3, WOOD)

# 月之钟楼
column('钟楼', 146, 185, 7, 7, 76, STONE)
box('钟楼钟室', 146, 76, 185, 8, 5, 8, STONE_D)
box('月之钟', 146, 77, 180.8, 3, 3, .8, GOLD)
steps('钟楼尖顶', 146, 185, 9, 81, 10, SLATE)

# 女巫药水铺（城门内南侧，紫色尖帽很好认）
column('药水铺', 144, 156, 6, 5, 66, CREAM)
steps('药水铺尖帽', 144, 156, 8.5, 66, 10, VIOLET, 4)
box('药水摊', 137.5, G(137.5, 156), 156, 6, 1.1, 2.5, WOOD)
for i, dx in enumerate((-2, -.7, .7, 2)):
    box(f'药水{i + 1}', 137.5 + dx, G(137.5, 156) + 1.1, 156, .5, .8, .5, [VIOLET, LIGHT, WHITE, FIRE][i])
box('坩埚', 133, G(133, 156), 156, 2, 1.1, 2, DARK)

# 上城堡的大坡道：从东边草地到城门
eg = G(200, 165)
beam('东侧大坡道', (200, eg - .2, 165), (153.2, G(153.2, 165) + .2, 165), 8, 1, STONE_D)

# 地下龙骨竞技场：做在台地下面，之后用传送阵进出
group[0] = '白模_龙骨竞技场'
AY, AX, AZ, AS = 32, 127, 172, 26
box('地面', AX, AY - 1, AZ, AS, 1, AS, STONE_D)
box('天花板', AX, AY + 9, AZ, AS, 1, AS, DARK)
for n, dx, dz, sx, sz in [('南', 0, -AS / 2, AS, 1), ('北', 0, AS / 2, AS, 1), ('西', -AS / 2, 0, 1, AS), ('东', AS / 2, 0, 1, AS)]:
    box(f'墙{n}', AX + dx, AY, AZ + dz, sx, 9, sz, STONE)
for i in range(6):
    a = i / 6 * math.tau
    box(f'龙肋骨{i + 1}', AX + math.cos(a) * 11, AY, AZ + math.sin(a) * 11, .9, 8, .9, WHITE)
box('擂台', AX, AY, AZ, 16, .4, 16, GOLD)
for n, dx in (('A', -9.5), ('B', 9.5)):
    box(f'武器架{n}', AX + dx, AY, AZ, .8, 2, 4, WOOD)
ey = G(125, 135)
box('入口左柱', 121.5, ey - 1, 135, 1.5, 7, 1.5, STONE)
box('入口右柱', 128.5, ey - 1, 135, 1.5, 7, 1.5, STONE)
box('入口门楣', 125, ey + 6, 135, 8.5, 1.5, 1.5, STONE_D)
box('入口传送阵', 125, ey + .1, 137, 5, .2, 5, GOLD)

# ---------------------------------------------------------------- 桥
group[0] = '白模_桥'
BX = 162
ba, bb = (BX, G(BX, 96) + .1, 96), (BX, G(BX, 125) + .1, 125)
mid_y = max(ba[1], bb[1]) + 2
mid = (BX, mid_y, 110.5)
beam('桥面南段', ba, mid, 6, .8, STONE_D)
beam('桥面北段', mid, bb, 6, .8, STONE_D)
for name, dz in (('桥墩南', 104), ('桥墩北', 117)):
    y0 = G(BX, dz) - 2
    box(name, BX, y0, dz, 7, mid_y - .8 - y0, 2.5, STONE)

# ---------------------------------------------------------------- 红顶小镇
group[0] = '白模_红顶小镇'
RIVER = [(77, 253), (77, 236), (80, 219), (74, 192), (79, 173), (88, 152), (98, 136), (108, 124), (125, 116), (141, 118),
         (154, 110), (168, 110), (187, 103)]


def river_dist(x, z_):
    best = 1e9
    for (ax, az), (bx, bz) in zip(RIVER, RIVER[1:]):
        dx, dz = bx - ax, bz - az
        t = max(0, min(1, ((x - ax) * dx + (z_ - az) * dz) / (dx * dx + dz * dz)))
        best = min(best, math.hypot(x - ax - t * dx, z_ - az - t * dz))
    return best


rnd = random.Random(42)
houses = []


def try_place(xr, zr, want):
    tries = placed = 0
    while placed < want and tries < 800:
        tries += 1
        x, z_ = rnd.uniform(*xr), rnd.uniform(*zr)
        if river_dist(x, z_) < 11 or abs(x - BX) < 8 or abs(z_ - 165) < 10:
            continue
        if Gmin(x, z_, 10, 10) < SEA + 2 or Gmax(x, z_, 10, 10) - Gmin(x, z_, 10, 10) > 5:
            continue
        if any(math.hypot(x - a, z_ - b) < 12.5 for a, b, _ in houses):
            continue
        houses.append((x, z_, rnd.choice('AABBC')))
        placed += 1


try_place((158, 192), (58, 104), 11)
try_place((164, 200), (118, 158), 7)
for i, (x, z_, kind) in enumerate(houses):
    yaw = rnd.choice((0, 15, 30, -15, -30, 90, 75, 105))
    y0 = Gmin(x, z_, 9, 9) - 1
    gy = Gmax(x, z_, 9, 9)
    n = f'民居{i + 1:02d}{kind}'
    w, d, wall = {'A': (5, 6, 6), 'B': (8, 6, 4), 'C': (6, 6, 7)}[kind]
    box(n + '墙', x, y0, z_, w, gy + wall - y0, d, CREAM, rot(yaw))
    # 屋顶是绕长轴转 45° 的方块，露出来的部分就是人字顶
    r = w * .74
    if kind == 'B':
        centered(n + '顶', x, gy + wall, z_, d * .74, d * .74, w + 1, ROOF, rot(yaw + 90, 0, 45))
    else:
        centered(n + '顶', x, gy + wall, z_, r, r, d + 1, ROOF, rot(yaw, 0, 45))
    if kind == 'C':
        a = math.radians(yaw)
        tx, tz = x + math.cos(a) * (w / 2 + .8), z_ - math.sin(a) * (w / 2 + .8)
        box(n + '塔', tx, y0, tz, 2.6, gy + wall + 3 - y0, 2.6, CREAM, rot(yaw))
        steps(n + '塔顶', tx, tz, 3.2, gy + wall + 3, 3, ROOF, 2)

# ---------------------------------------------------------------- 港口 · 灯塔 · 帆船
group[0] = '白模_港口'


def coast_x(z_):
    return next(x for x in range(140, 256) if H[int(z_), x] < SEA - .2)


for i, pz in enumerate((90, 76)):
    cx = coast_x(pz)
    x0, x1 = cx - 6, cx + 20
    box(f'码头{i + 1}', (x0 + x1) / 2, SEA + 1.4, pz, x1 - x0, .6, 4, WOOD)
    for dx in (6, 13, 19):
        box(f'码头{i + 1}桩{dx}', cx + dx, SEA - 3, pz + 1.6, .6, 4.4, .6, WOOD)
        box(f'码头{i + 1}桩{dx}b', cx + dx, SEA - 3, pz - 1.6, .6, 4.4, .6, WOOD)
for i, (x, pz, yaw, s) in enumerate([(cx + 12, 98, 20, 1.0), (236, 64, -35, 1.2), (232, 112, 60, 1.4)]):
    h = 12 * s
    box(f'帆船{i + 1}船身', x, SEA - .6, pz, 4 * s, 2.4 * s, h, WOOD, rot(yaw))
    box(f'帆船{i + 1}桅杆', x, SEA + 1, pz, .4, 10 * s, .4, WOOD)
    a = math.radians(yaw)
    centered(f'帆船{i + 1}帆', x, SEA + 1 + 6 * s, pz, 6 * s, 6 * s, .3, WHITE, rot(yaw))

sub = H[120:146, 198:226]
lz, lx = np.unravel_index(sub.argmax(), sub.shape)
lz, lx = int(lz) + 120, int(lx) + 198
ly = float(H[lz, lx])
column('灯塔座', lx, lz, 8, 8, ly + 2, STONE_D)
box('灯塔身下', lx, ly + 2, lz, 5.5, 9, 5.5, WHITE)
box('灯塔红环', lx, ly + 11, lz, 5, 3, 5, ROOF)
box('灯塔身上', lx, ly + 14, lz, 4.2, 6, 4.2, WHITE)
box('灯塔回廊', lx, ly + 20, lz, 6.5, .6, 6.5, DARK)
box('灯塔灯室', lx, ly + 20.6, lz, 3.2, 3.2, 3.2, LIGHT)
steps('灯塔顶', lx, lz, 4.4, ly + 23.8, 3, ROOF, 2)

# ---------------------------------------------------------------- 古龙 · 龙巢
group[0] = '白模_古龙龙巢'
north = H[205:, :]
pz, px = np.unravel_index(north.argmax(), north.shape)
pz, px = int(pz) + 205, int(px)
py = float(H[pz, px])
BODY = [(172, 247), (154, 244), (134, 247), (114, 244), (103, 238), (112, 232), (130, 232), (146, 232), (150, 228), (140, 224)]
pts = [(x, max(G(x, zz) + 4, 102), zz) for x, zz in BODY]
for i, (p, q) in enumerate(zip(pts, pts[1:])):
    t = 7.5 - abs(i - 4) * .7
    beam(f'龙身{i + 1}', p, q, t, t, DRAGON)
hx, hz = 128, 215
head = (hx, max(G(hx, hz) + 7, 106), hz)
beam('龙颈', pts[-1], head, 4.5, 4.5, DRAGON)
centered('龙头', head[0] - .5, head[1], head[2] - 3, 6.5, 4.2, 9, DRAGON, rot(-20))
centered('龙吻', head[0] - 2.5, head[1] - .8, head[2] - 8.5, 4, 2.4, 4.5, DRAGON, rot(-20))
for i, dx in enumerate((-2.2, 2.2)):
    beam(f'龙角{i + 1}', (head[0] + dx, head[1] + 2, head[2]), (head[0] + dx * 1.7, head[1] + 8, head[2] + 7), 1, 1, STONE)
    centered(f'龙眼{i + 1}', head[0] + dx * 1.45 - 1.6, head[1] + .8, head[2] - 7, .8, 1, 1.4, GOLD)
wy = 99
centered('左翼', 98, wy + 14, 232, 54, 1.2, 24, DRAGON, rot(-8, 0, -22))
centered('右翼', 172, wy + 14, 232, 54, 1.2, 24, DRAGON, rot(8, 0, 22))
for i, (ex, ez) in enumerate(((170, 222), (175, 224), (172, 228))):
    box(f'龙蛋{i + 1}', ex, G(ex, ez) - .2, ez, 1.8, 2.8, 1.8, GOLD)
print('dragon ground', [round(G(x, zz), 1) for x, zz in BODY], 'head', round(head[1], 1), 'wing y', round(wy + 14, 1))

# ---------------------------------------------------------------- 出生观景崖
group[0] = '白模_出生点'
SX, SZ = 130.0, 48.0
for n in nodes:
    if n['tag'] == 'BornPoint':
        n['pos'] = {'x': SX, 'y': round(G(SX, SZ) + .5, 3), 'z': SZ}
fy = G(121, 50)
box('魔法画框底', 121, fy, 50, 4, .4, 1, WOOD)
box('魔法画框左', 119.5, fy, 50, .5, 4, .5, GOLD)
box('魔法画框右', 122.5, fy, 50, .5, 4, .5, GOLD)
box('魔法画框顶', 121, fy + 4, 50, 3.5, .5, .5, GOLD)
box('篝火', 137, G(137, 45), 45, 1.2, .9, 1.2, FIRE)
PX_, PZ_ = 145.0, 46.0
PY = G(PX_, PZ_)
box('骑龙底座', PX_, PY - .3, PZ_, 7, 1.1, 7, STONE_D)
beam('骑乘龙身', (PX_, PY + 3, PZ_ - 4), (PX_, PY + 3.6, PZ_ + 3), 3.2, 3.2, DRAGON)
beam('骑乘龙颈', (PX_, PY + 3.6, PZ_ + 3), (PX_, PY + 7, PZ_ + 6), 1.6, 1.6, DRAGON)
centered('骑乘龙头', PX_, PY + 7.4, PZ_ + 7, 2, 1.8, 3.2, DRAGON)
centered('骑乘龙左翼', PX_ - 5.5, PY + 6, PZ_ - 1, 9, .4, 5, DRAGON, rot(0, 0, -28))
centered('骑乘龙右翼', PX_ + 5.5, PY + 6, PZ_ - 1, 9, .4, 5, DRAGON, rot(0, 0, 28))
box('骑乘鞍', PX_, PY + 5, PZ_ - 1, 2.4, .5, 2.6, ROOF)

# ---------------------------------------------------------------- 牧羊坡
group[0] = '白模_牧羊坡'
wx, wz = 84, 66
wy = G(wx, wz)
column('风车塔', wx, wz, 5, 5, wy + 11, CREAM)
steps('风车顶', wx, wz, 6, wy + 11, 3, ROOF, 2)
for deg in (20, 110):
    centered(f'风车叶片{deg}', wx, wy + 11, wz - 3, 18, 1.4, .3, WOOD, rot(0, 0, deg))
rnd2 = random.Random(7)
for i in range(9):
    x, zz = rnd2.uniform(88, 118), rnd2.uniform(70, 96)
    y = G(x, zz)
    yaw = rnd2.uniform(-180, 180)
    box(f'羊{i + 1}', x, y + .35, zz, .9, .7, 1.5, WHITE, rot(yaw))

# ================================================================= 写入场景
kept, removed_ids = [], set()
for n in nodes:
    if n['nodeName'].startswith('白模_') or n['parentId'] in removed_ids:
        removed_ids.add(n['id'])
    else:
        kept.append(n)
print('removed old whitebox nodes', len(nodes) - len(kept))
used = {n['id'] for n in kept}


def new_id(key):
    v = zlib.crc32(key.encode()) & 0x7fffffff
    v = v or 1
    while v in used:
        v += 1
    used.add(v)
    return v


def vec(v):
    return {'x': round(v[0], 4), 'y': round(v[1], 4), 'z': round(v[2], 4)}


gid = {}
added = []
for b in boxes:
    if b['group'] not in gid:
        g = copy.deepcopy(group_tpl)
        g.update(nodeName=b['group'], parentId=0, id=new_id(b['group']), isActive=True)
        g['pos'] = vec((0, 0, 0))
        g['rot'] = {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}
        g['scale'] = vec((1, 1, 1))
        gid[b['group']] = g['id']
        added.append(g)
    n = copy.deepcopy(cube_tpl)
    n.update(nodeName=b['name'], parentId=gid[b['group']], id=new_id(b['group'] + '/' + b['name']), isActive=True)
    n['pos'] = vec([float(v) for v in b['pos']])
    n['scale'] = vec([float(v) for v in b['scale']])
    n['rot'] = dict(zip('xyzw', (round(float(v), 6) for v in b['rot'])))
    n['appearanceData']['color'] = {'r': b['color'][0], 'g': b['color'][1], 'b': b['color'][2], 'a': 1.0}
    n['appearanceData']['isModified'] = True
    added.append(n)
scene['nodeTransformDatas'] = kept + added
counts = {}
for b in boxes:
    counts[b['group']] = counts.get(b['group'], 0) + 1
print('cubes', len(boxes), counts)
print('houses', len(houses), 'lighthouse', lx, lz, round(ly, 1), 'peak', px, pz, round(py, 1))
print('causeway foot ground', round(eg, 1), 'bridge ends', round(ba[1], 1), round(bb[1], 1), 'deck', round(mid_y, 1),
      'arena door ground', round(ey, 1))
for c, name in [((X0, Z0), 'SW'), ((X1, Z0), 'SE'), ((X0, Z1), 'NW'), ((X1, Z1), 'NE'), ((127, Z0), 'S'), ((127, Z1), 'N'), ((X0, 173), 'W'), ((X1, 165), 'E gate')]:
    print('  castle', name, c, 'ground', round(G(*c), 1))

json.dump(boxes, open(dump, 'w'), ensure_ascii=False, default=float)
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as w:
    for i in z.infolist():
        data = z.read(i.filename)
        if i.filename == 'SerializePcgData.json':
            data = json.dumps(scene, ensure_ascii=False, separators=(',', ':')).encode()
        ni = zipfile.ZipInfo(i.filename, i.date_time)
        ni.compress_type = zipfile.ZIP_DEFLATED
        ni.external_attr = i.external_attr
        w.writestr(ni, data)
