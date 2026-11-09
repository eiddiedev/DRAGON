# 用法：Blender --background --python castle.py -- <输出目录>
# 星塔城堡分 5 个模型导入（单个不超过 3 万面）。所有坐标都是世界坐标减去原点 ORIGIN，
# 所以这 5 个模型只要摆在同一个位置就能对齐。+X 东，+Y 北（游戏里的 +Z），Z 是海拔。
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
from kit import C, Mesh, arch_cutter, cut, finish, preview_setup, rnd, shot, srgb

outdir = sys.argv[sys.argv.index('--') + 1]
C.update({k: srgb(v) for k, v in dict(cs='#F2EAD9', cs2='#DACFBC', cs3='#FBF5E9', slate='#6A86B8', slate2='#546FA3', slate3='#83A0CE',
                                      trim='#B9AE9B', banner='#3F5FA8').items()})
OX, OY = 127.0, 173.0
T0, WT, T1, T2 = 53.0, 63.0, 61.0, 67.0  # 台地面、城墙顶、下层平台、上层平台（海拔）


def W(x, y):
    """世界坐标 → 模型坐标。"""
    return x - OX, y - OY


def stones_on_cyl(P, cx, cy, r, z0, z1, n):
    for _ in range(n):
        a = rnd.uniform(0, math.tau)
        z = rnd.uniform(z0, z1)
        s = rnd.uniform(.7, 1.3)
        P.rbox((s, .22, s * .5), (cx + math.cos(a) * (r + .02), cy + math.sin(a) * (r + .02), z), C[rnd.choice(('cs2', 'cs3', 'trim'))], (0, 0, a + math.pi / 2))


def cone_roof(P, cx, cy, r, z, h, seg=20, bands=3, tip=True):
    """微微外卷的尖顶，几圈瓦带，顶上一个金尖。"""
    prof = [(r * (1 - t) ** 1.25 + .03, z + t * h) for t in [i / 8 for i in range(9)]]
    prof = [(r + .55, z - .25)] + prof
    P.lathe(prof, C['slate'], seg, center=(cx, cy))
    for i in range(bands):
        t = (i + .6) / (bands + 1)
        rr = r * (1 - t) ** 1.25
        zz = z + t * h
        P.lathe([(rr + .02, zz - .22), (rr + .14, zz), (rr + .02, zz + .22)], C['slate2' if i % 2 else 'slate3'], seg, center=(cx, cy))
    if tip:
        P.cyl(.16, .03, 1.3, (cx, cy, z + h + .5), C['gold'], 6)
        P.sphere(.24, (cx, cy, z + h + .05), C['gold'], 8)


def crenel_ring(P, cx, cy, r, z, n=14):
    P.lathe([(r + .32, z - .7), (r + .5, z - .1), (r + .5, z + .25), (r - .2, z + .25)], C['cs2'], 28, center=(cx, cy))
    for i in range(n):
        a = i / n * math.tau
        P.rbox((math.tau * r / n * .55, .5, .95), (cx + math.cos(a) * (r + .2), cy + math.sin(a) * (r + .2), z + .7), C['cs3' if i % 2 else 'cs'], (0, 0, a + math.pi / 2))


def round_tower(P, G, cx, cy, r, z0, top, roof_h, windows=2):
    P.lathe([(r + .45, z0), (r + .25, z0 + 3), (r, z0 + 7), (r, top)], C['cs'], 26, center=(cx, cy))
    stones_on_cyl(P, cx, cy, r, z0 + 2, top - .8, int((top - z0) * 1.1))
    crenel_ring(P, cx, cy, r, top)
    cone_roof(P, cx, cy, r * .96, top + 1.0, roof_h)
    P.lathe([(r - .05, top + .98), (.02, top + .98)], C['trim'], 16, center=(cx, cy))
    for i in range(windows):
        a = -math.pi / 2 + rnd.uniform(-.5, .5)
        z = top - 2.6 - i * 4.2
        x, y = cx + math.cos(a) * (r + .02), cy + math.sin(a) * (r + .02)
        G.rbox((.8, .1, 1.5), (x, y, z), 'glass', (0, 0, a + math.pi / 2), cuts=0)
        G.cyl(.4, .4, .1, (x, y, z + .75), 'glass', 10, (math.pi / 2, 0, a + math.pi / 2))
        P.rbox((1.1, .16, .16), (x, y, z - .8), C['trim'], (0, 0, a + math.pi / 2))


def wall_run(P, a, b, z0, top, thick=2.0, gap=None):
    """一段城墙 + 墙头垛口 + 墙面零星石块。a、b 为模型坐标。"""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    rz = math.atan2(dy, dx)
    c, s = math.cos(rz), math.sin(rz)
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    P.rbox((L, thick, top - z0), (mx, my, (z0 + top) / 2), C['cs'], (0, 0, rz), cuts=0)
    # 走道外沿
    for sgn in (-1, 1):
        ox, oy = -s * sgn * (thick / 2 + .05), c * sgn * (thick / 2 + .05)
        P.rbox((L, .22, .34), (mx + ox, my + oy, top - .25), C['cs2'], (0, 0, rz), cuts=1)
    n = int(L / 1.6)
    for i in range(n):
        t = (i + .5) / n * L
        x, y = a[0] + c * t, a[1] + s * t
        for sgn in (1,):
            ox, oy = -s * sgn * (thick / 2 - .1), c * sgn * (thick / 2 - .1)
            P.rbox((.92, .36, .95), (x + ox, y + oy, top + .45), C['cs3' if i % 2 else 'cs2'], (0, 0, rz))
    for _ in range(int(L * .75)):
        t = rnd.uniform(0, L)
        z = rnd.uniform(z0 + 2, top - 1)
        sgn = rnd.choice((-1, 1))
        w = rnd.uniform(.8, 1.5)
        ox, oy = -s * sgn * (thick / 2 + .02), c * sgn * (thick / 2 + .02)
        P.rbox((w, .18, w * .45), (a[0] + c * t + ox, a[1] + s * t + oy, z), C[rnd.choice(('cs2', 'cs3', 'trim'))], (0, 0, rz))


def gable_roof(P, cx, cy, w, d, z, rise, over=.6):
    """人字瓦顶，脊沿 Y 轴。"""
    half = w / 2 + over
    length = d + over * 2
    slope = math.atan2(rise, w / 2)
    run = half / math.cos(slope)
    for sx in (-1, 1):
        P.rbox((run + .1, length, .24), (cx + sx * half / 2, cy, z + rise - math.sin(slope) * run / 2), C['slate2'], (0, sx * slope, 0))
        rows = max(4, int(run / 1.0))
        cols = max(5, int(length / 1.15))
        for r in range(rows):
            dist = run * ((r + .5) / rows - .5)
            xx = cx + sx * (half / 2 - math.cos(slope) * dist)
            zz = z + rise - math.sin(slope) * run / 2 + math.sin(slope) * dist + .32
            for k in range(cols):
                y = cy - length / 2 + (k + .5 + (r % 2) * .5) * length / cols
                if abs(y - cy) > length / 2 - .1:
                    continue
                P.rbox((run / rows * 1.28, length / cols * 1.02, .14), (xx, y, zz), C[rnd.choice(('slate', 'slate', 'slate2', 'slate3'))], (0, sx * slope, 0))
    P.rbox((.55, length + .25, .34), (cx, cy, z + rise + .18), C['slate2'])


def export(name, P, G, extra=None, size=2048):
    main = P.to_object('main')
    objs = finish([main] + (extra or []), G, name, outdir, tex_size=size)
    cam = preview_setup()
    return cam


def part_walls():
    kit.reset()
    P, G = Mesh(), Mesh()
    z0 = 44.0
    (x0, y0), (x1, y1) = W(102, 152), W(152, 194)
    gate_lo, gate_hi = W(0, 160)[1] + OY - OY, W(0, 170)[1]
    wall_run(P, (x0, y0), (x1, y0), z0, WT)
    wall_run(P, (x0, y1), (x1, y1), z0, WT)
    wall_run(P, (x0, y0), (x0, y1), z0, WT)
    wall_run(P, (x1, y0), (x1, gate_lo), z0, WT)
    wall_run(P, (x1, gate_hi), (x1, y1), z0, WT)
    # 城门拱
    gy = (gate_lo + gate_hi) / 2
    n = 9
    for i in range(n):
        t = i / (n - 1) * math.pi
        y = gy - math.cos(t) * 4.2
        z = 58.2 + 2.0 + math.sin(t) * 2.6
        P.rbox((2.6, .9, .7), (x1, y, z), C['cs3' if i % 2 else 'cs2'], (t - math.pi / 2, 0, 0))
    P.rbox((2.4, 9.6, 1.3), (x1, gy, WT - .2), C['cs'], cuts=1)
    for i in range(6):
        P.rbox((.92, .36, .95) if False else (.36, .92, .95), (x1 + .9, gy - 4 + i * 1.6, WT + .95), C['cs3' if i % 2 else 'cs2'])
    # 门前旗帜
    for sy in (-1, 1):
        P.rbox((.08, 2.0, 4.5), (x1 + 1.25, gy + sy * 3.5, 58.8), C['banner'], cuts=0)
        P.rbox((.14, 2.2, .18), (x1 + 1.27, gy + sy * 3.5, 61.1), C['gold'])
    for (wx, wy) in ((152, 152), (152, 194), (102, 152)):
        x, y = W(wx, wy)
        round_tower(P, G, x, y, 4.0, z0, 71, 11)
    for wy in (159.5, 170.5):
        x, y = W(152, wy)
        round_tower(P, G, x, y, 2.9, z0, 68, 7.5, windows=1)
    cam = export('castle_walls', P, G)
    shot(cam, os.path.join(outdir, 'castle_walls.png'), (20, -75, 60), (0, 0, 62), 40)


def part_keep():
    kit.reset()
    P, G = Mesh(), Mesh()
    # 下层平台
    x, y = W(124, 174)
    P.rbox((28, 32, T1 - 44), (x, y, (T1 + 44) / 2), C['cs2'], cuts=0)
    P.rbox((28.6, 32.6, .5), (x, y, T1 - .05), C['trim'], cuts=1)
    # 上层平台
    x, y = W(128, 178)
    P.rbox((16, 16, T2 - T1 + 1), (x, y, (T2 + T1 - 1) / 2), C['cs'], cuts=0)
    P.rbox((16.5, 16.5, .4), (x, y, T2 - .05), C['trim'], cuts=1)
    # 坡道：表面一条条木阶
    def ramp(a, b, width, name=None):
        dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        run = math.hypot(dx, dy)
        L = math.hypot(run, dz)
        yaw = math.atan2(dx, dy)
        pitch = math.atan2(dz, run)
        q = (pitch, 0, -yaw)
        from mathutils import Euler
        R = Euler((0, 0, -yaw)).to_matrix() @ Euler((pitch, 0, 0)).to_matrix()
        mx, my, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2
        P.rbox((width, L, .5), (mx, my, mz - .3), C['cs2'], R, cuts=0)
        n = int(L / .9)
        for i in range(n):
            t = (i + .5) / n
            P.rbox((width - .6, .5, .08), (a[0] + dx * t, a[1] + dy * t, a[2] + dz * t), C['trim'], R, cuts=0)
        c, s = math.cos(yaw), math.sin(yaw)
        for sgn in (-1, 1):
            P.rbox((.5, L, .8), (mx + c * sgn * width / 2, my - s * sgn * width / 2, mz + .15), C['cs3'], R, cuts=1)
    gx, gy = W(151, 165)
    tx, ty = W(138, 165)
    ramp((gx, gy, 58.3), (tx, ty, T1), 7)
    ax, ay = W(128, 158.6)
    bx, by = W(128, 170)
    ramp((ax, ay, T1), (bx, by, T2), 6)

    # 主楼：空心大厅，南门朝坡道
    kx, ky = W(128, 178)
    KW, KD, KH = 12.0, 12.0, 13.0
    m = Mesh()
    m.rbox((KW, KD, KH), (kx, ky, T2 + KH / 2), C['cs'], cuts=0)
    shell = m.to_object('keep_wall')
    inner = Mesh()
    inner.rbox((KW - 1.2, KD - 1.2, KH - .6), (kx, ky, T2 + (KH - .6) / 2 + .02), C['iron'], cuts=0)
    cutters = [inner.to_object('keep_in')] + arch_cutter(kx, ky - KD / 2, 3.4, 5.0, T2 + .03, 0, 3.0, 'kd')
    wins = [(kx - KW / 2, ky, math.pi / 2), (kx + KW / 2, ky, math.pi / 2), (kx - 3, ky + KD / 2, 0), (kx + 3, ky + KD / 2, 0), (kx - 4, ky - KD / 2, 0), (kx + 4, ky - KD / 2, 0)]
    for i, (wx, wy, rz) in enumerate(wins):
        cutters += arch_cutter(wx, wy, 1.5, 3.4, T2 + 6.6, rz, 3.0, f'kw{i}')
    cut(shell, cutters)
    for wx, wy, rz in wins:
        G.rbox((1.5, .1, 3.4), (wx, wy, T2 + 8.2), 'glass', (0, 0, rz), cuts=0)
    P.rbox((KW - 1.1, KD - 1.1, .15), (kx, ky, T2 + .08), C['floor'], cuts=0)
    P.rbox((KW + .2, KD + .2, .3), (kx, ky, T2 + KH - .15), C['wood3'], cuts=0)
    n = 9
    for i in range(n):
        t = i / (n - 1) * math.pi
        P.rbox((1.0, 1.15, .7), (kx - math.cos(t) * 2.15, ky - KD / 2, T2 + 3.3 + math.sin(t) * 2.15), C['cs3' if i % 2 else 'cs2'], (0, -t + math.pi / 2, 0))
    for sx in (-1, 1):
        for i in range(4):
            P.rbox((1.05, 1.15, .78), (kx + sx * 2.15, ky - KD / 2, T2 + .4 + i * .8), C['cs3' if i % 2 else 'cs2'])
    for _ in range(40):
        side = rnd.choice('NSEW')
        w = rnd.uniform(.9, 1.7)
        z = rnd.uniform(T2 + 5.5, T2 + KH - 1)
        t = rnd.uniform(-KW / 2 + .8, KW / 2 - .8)
        if side in 'NS':
            P.rbox((w, .2, w * .45), (kx + t, ky + (KD / 2 + .02) * (1 if side == 'N' else -1), z), C[rnd.choice(('cs2', 'cs3', 'trim'))])
        else:
            P.rbox((.2, w, w * .45), (kx + (KW / 2 + .02) * (1 if side == 'E' else -1), ky + t, z), C[rnd.choice(('cs2', 'cs3', 'trim'))])
    # 主楼屋顶：大尖顶 + 四角小塔
    P.rbox((KW + 1.1, KD + 1.1, .8), (kx, ky, T2 + KH + .1), C['cs2'])
    for i in range(4):
        s = KW + 1 - i * 2.0
        P.rbox((s, s, 2.1), (kx, ky, T2 + KH + 1.4 + i * 2.05), C['slate' if i % 2 else 'slate2'])
    cone_roof(P, kx, ky, 4.8, T2 + KH + 8.6, 14, 24)
    for sx in (-1, 1):
        for sy in (-1, 1):
            round_tower(P, G, kx + sx * (KW / 2 + .4), ky + sy * (KD / 2 + .4), 1.5, T2, T2 + KH + 2.5, 6, windows=1)
    # 坡道两侧的小炮楼
    for sx in (-1, 1):
        x_, y_ = kx + sx * 6.8, ky - KD / 2 - .6
        round_tower(P, G, x_, y_, 1.3, T1 - .5, T2 + 5, 4.5, windows=0)
    cam = export('castle_keep', P, G, [shell])
    shot(cam, os.path.join(outdir, 'castle_keep.png'), (15, -60, 70), (0, 5, 72), 40)


def part_library():
    kit.reset()
    P, G = Mesh(), Mesh()
    cx, cy = W(114.5, 174)
    LW, LD, LH = 9.0, 27.0, 9.0
    m = Mesh()
    m.rbox((LW, LD, LH), (cx, cy, T1 + LH / 2), C['plaster'], cuts=0)
    shell = m.to_object('lib_wall')
    inner = Mesh()
    inner.rbox((LW - 1.0, LD - 1.0, LH - .5), (cx, cy, T1 + (LH - .5) / 2 + .02), C['iron'], cuts=0)
    cutters = [inner.to_object('lib_in')] + arch_cutter(cx + LW / 2, cy, 2.8, 4.2, T1 + .03, math.pi / 2, 3.0, 'ld')
    wy = [-10, -5, 5, 10]
    for i, dy in enumerate(wy):
        cutters += arch_cutter(cx + LW / 2, cy + dy, 2.0, 4.8, T1 + 2.8, math.pi / 2, 3.0, f'le{i}')
        cutters += arch_cutter(cx - LW / 2, cy + dy, 2.0, 4.8, T1 + 2.8, math.pi / 2, 3.0, f'lw{i}')
    cut(shell, cutters)
    for dy in wy:
        for sx in (-1, 1):
            G.rbox((.1, 2.0, 4.8), (cx + sx * LW / 2, cy + dy, T1 + 5.0), 'glass', (0, 0, 0), cuts=0)
            P.rbox((.3, .12, 4.9), (cx + sx * LW / 2, cy + dy, T1 + 5.2), C['wood3'], cuts=0)
            P.rbox((.3, 2.1, .12), (cx + sx * LW / 2, cy + dy, T1 + 5.2), C['wood3'], cuts=0)
            P.rbox((.5, 2.6, .28), (cx + sx * LW / 2, cy + dy, T1 + 2.8), C['trim'])
    # 木框架
    for dy in (-LD / 2, -7.5, 7.5, LD / 2):
        for sx in (-1, 1):
            P.rbox((.5, .6, LH + .1), (cx + sx * LW / 2, cy + dy, T1 + LH / 2), C['beam'])
    for sx in (-1, 1):
        P.rbox((.42, LD + .4, .42), (cx + sx * LW / 2, cy, T1 + LH), C['beam'])
        for sy in (-1, 1):  # 门洞处断开
            P.rbox((.3, LD / 2 - 1.5, .3), (cx + sx * LW / 2, cy + sy * (LD / 4 + .75), T1 + 2.3), C['beam'])
    # 拱门石框
    n = 9
    gy = cy
    gx = cx + LW / 2
    for i in range(n):
        t = i / (n - 1) * math.pi
        P.rbox((1.0, .9, .6), (gx, gy - math.cos(t) * 1.8, T1 + 2.8 + math.sin(t) * 1.8), C['cs3' if i % 2 else 'cs2'], (t - math.pi / 2, 0, 0))
    # 室内
    P.rbox((LW - .9, LD - .9, .14), (cx, cy, T1 + .1), C['floor'], cuts=0)
    P.rbox((LW + .1, LD + .1, .3), (cx, cy, T1 + LH), C['wood3'], cuts=0)
    book_cols = ['cloth', 'roof', 'gold', 'banner', 'green', 'cloth2']
    for sy in (-1, 1):  # 两端书墙
        for z in (1.2, 2.6, 4.0, 5.4):
            P.rbox((LW - 1.6, .7, .16), (cx, cy + sy * (LD / 2 - 1.0), T1 + z), C['wood2'])
            x = cx - LW / 2 + 1.1
            while x < cx + LW / 2 - 1.1:
                w = rnd.uniform(.18, .34)
                h = rnd.uniform(.7, 1.05)
                P.rbox((w, .5, h), (x, cy + sy * (LD / 2 - 1.0), T1 + z + .08 + h / 2), C[rnd.choice(book_cols)], cuts=0)
                x += w + .03
    # 中央书台（领魔杖的交互点在 cy 处）
    P.rbox((1.8, 1.8, .4), (cx, cy, T1 + .35), C['cs2'])
    P.rbox((.8, .8, 1.3), (cx, cy, T1 + 1.0), C['wood'])
    P.rbox((1.5, 1.1, .16), (cx, cy, T1 + 1.7), C['wood2'], (math.radians(-18), 0, 0))
    P.rbox((1.1, .75, .1), (cx, cy, T1 + 1.82), C['cloth2'], (math.radians(-18), 0, 0))
    # 静态的飘浮书（之后可换成会动的）
    for i in range(10):
        a = i / 10 * math.tau
        x_, y_ = cx + math.cos(a) * 2.8, cy + math.sin(a) * 8.5
        P.rbox((.75, .55, .14), (x_, y_, T1 + rnd.uniform(3.3, 5.6)), C[rnd.choice(book_cols)], (rnd.uniform(-.4, .4), rnd.uniform(-.4, .4), a), cuts=0)
    for dy in (-6, 6):
        G.sphere(.4, (cx, cy + dy, T1 + LH - 1.4), 'glass', 10)
        P.cyl(.04, .04, 1.1, (cx, cy + dy, T1 + LH - .6), C['iron'], 5)
    gable_roof(P, cx, cy, LW, LD, T1 + LH, 4.4)
    for sy in (-1, 1):
        y = cy + sy * (LD / 2 - .05)
        P.prism(LW, y - .15, y + .15, T1 + LH, 4.4, C['plaster2'], cx)
        G.sphere(.55, (cx, y + sy * .2, T1 + LH + 1.7), 'star', 10)
    cam = export('castle_library', P, G, [shell])
    shot(cam, os.path.join(outdir, 'castle_library.png'), (cx + 26, cy - 22, T1 + 9), (cx, cy, T1 + 6), 38)


def part_towers():
    kit.reset()
    P, G = Mesh(), Mesh()
    # 天文塔
    x, y = W(103, 193)
    z0, top = 44.0, 96.0
    P.lathe([(4.2, z0), (3.6, 56), (3.1, 66), (3.0, top - 1), (3.6, top)], C['cs'], 24, center=(x, y))
    stones_on_cyl(P, x, y, 3.05, 55, top - 1.5, 45)
    for z in (68, 78, 88):
        P.lathe([(3.05, z - .25), (3.28, z), (3.05, z + .25)], C['trim'], 24, center=(x, y))
    for i, z in enumerate((64, 72, 80, 88)):
        a = -math.pi / 2 + (i % 2) * .7
        wx, wy = x + math.cos(a) * 3.05, y + math.sin(a) * 3.05
        G.rbox((.8, .1, 1.6), (wx, wy, z), 'glass', (0, 0, a + math.pi / 2), cuts=0)
    P.lathe([(3.6, top), (6.6, top + .4), (6.8, top + .8), (6.6, top + 1.1), (.02, top + 1.1)], C['cs2'], 30, center=(x, y))
    for i in range(18):  # 栏杆
        a = i / 18 * math.tau
        P.rbox((.22, .22, 1.1), (x + math.cos(a) * 6.4, y + math.sin(a) * 6.4, top + 1.6), C['iron'])
    P.lathe([(6.4, top + 2.1), (6.5, top + 2.2), (6.4, top + 2.3)], C['iron'], 30, center=(x, y))
    P.sphere(2.9, (x, y + 1.6, top + 1.1), C['slate'], 18, (1, 1, .95))
    P.rbox((.5, 4.6, .5), (x + .5, y - .6, top + 4.6), C['gold'], (math.radians(38), 0, 0))
    P.cyl(.4, .4, .3, (x + .5, y - 2.5, top + 6.05), C['iron'], 12, (math.radians(38 + 90), 0, 0))
    for i, dx in enumerate((-4.2, -3.2, -2.2)):  # 扫帚架
        P.rbox((.12, .12, 3.0), (x + dx, y - 3.6, top + 2.6), C['wood2'], (0, math.radians(8), 0), cuts=0)
        P.cyl(.3, .12, .9, (x + dx - .2, y - 3.6, top + 1.75), C['gold'], 7)
    # 钟楼：四面开拱，能看到金钟
    bx, by = W(146, 185)
    P.lathe([(4.6, 44), (4.0, T0 + 2), (3.6, T0 + 8), (3.5, 76)], C['cs'], 24, center=(bx, by))
    stones_on_cyl(P, bx, by, 3.55, T0 + 3, 75, 34)
    P.lathe([(3.5, 76), (4.3, 76.3), (4.3, 76.7), (.02, 76.7)], C['trim'], 24, center=(bx, by))
    for i in range(4):
        a = i / 4 * math.tau + math.pi / 4
        P.rbox((1.4, 1.4, 5.0), (bx + math.cos(a) * 3.1, by + math.sin(a) * 3.1, 79.2), C['cs3'])
    P.lathe([(4.3, 81.7), (4.5, 82), (4.3, 82.3), (.02, 82.3)], C['trim'], 24, center=(bx, by))
    P.lathe([(.25, 81.7), (1.5, 80.8), (1.75, 79.0), (2.25, 77.8), (2.3, 77.7), (.02, 77.7)], C['gold'], 18, center=(bx, by))
    P.sphere(.42, (bx, by, 77.4), C['wood3'], 8)
    cone_roof(P, bx, by, 4.1, 82.3, 10, 22)
    P.rbox((.3, .3, .9), (bx, by, 92.9), C['gold'])
    P.sphere(.5, (bx, by, 93.8), C['gold'], 10, (.45, 1, 1))
    # 敲钟处的门
    ang = -math.pi / 2
    gx, gy = bx + math.cos(ang) * 3.65, by + math.sin(ang) * 3.65
    P.rbox((1.8, .3, 3.1), (gx, gy, 57.3), C['wood2'])
    for i in range(7):
        t = i / 6 * math.pi
        P.rbox((.72, .6, .5), (gx - math.cos(t) * 1.25, gy, 58.6 + math.sin(t) * 1.25), C['cs3' if i % 2 else 'cs2'], (0, -t + math.pi / 2, 0))
    cam = export('castle_towers', P, G)
    shot(cam, os.path.join(outdir, 'castle_towers.png'), (20, -70, 70), (0, 10, 78), 40)


part_walls()
part_keep()
part_library()
part_towers()
