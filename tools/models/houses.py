# 用法：Blender --background --python houses.py -- <输出目录>
# 红顶民居三款：都可以走进去。门朝 -Y（南），单位米，原点在屋子中心的地面。
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
from kit import C, Mesh, Vector, arch_cutter, cut, finish, preview_setup, rnd, shot

outdir = sys.argv[sys.argv.index('--') + 1]
os.makedirs(outdir, exist_ok=True)
C.update({k: kit.srgb(v) for k, v in dict(shut='#3F6C80', flower1='#B57BE4', flower2='#F2A6D0', flower3='#FFF0B8', ivy1='#3C6B2C', ivy2='#2C5524').items()})


def shell(w, d, h, t=.35):
    """空心墙壳：外盒减内盒。"""
    m = Mesh()
    m.rbox((w, d, h), (0, 0, h / 2), C['plaster'], cuts=0)
    ob = m.to_object('wall')
    inner = Mesh()
    inner.rbox((w - 2 * t, d - 2 * t, h + 2), (0, 0, h / 2 + .15), C['iron'], cuts=0)
    return ob, inner.to_object('inner')


def gable(P, w, d, y0, rise, over=.55, stack=True):
    """人字屋顶，脊沿 Y 轴（宽 w 是山墙方向）。一片片圆瓦。"""
    half = w / 2 + over
    length = d + over * 2
    slope = math.atan2(rise, w / 2)
    run = half / math.cos(slope)
    # 底壳
    for sx in (-1, 1):
        P.rbox((run + .1, length, .22), (sx * half / 2, 0, y0 + rise * (half / (w / 2)) / 2 - .05 + rise * (1 - half / (w / 2)) * 0), C['roof_red2'], (0, sx * slope, 0), cuts=1)
    rows = max(4, int(run / .78))
    cols = max(5, int(length / .9))
    for sx in (-1, 1):
        for r in range(rows):
            t = (r + .5) / rows
            dist = run * (t - .5)
            cx = sx * (half / 2) + sx * math.cos(slope) * dist * -1
            cz = y0 + rise * (half / (w / 2)) / 2 + math.sin(slope) * dist + .28
            for c in range(cols):
                y = -length / 2 + (c + .5 + (r % 2) * .5) * length / cols
                if abs(y) > length / 2 - .05:
                    continue
                col = C[rnd.choice(('roof_red', 'roof_red', 'roof_red2', 'roof_red3'))]
                P.rbox((run / rows * 1.32, length / cols * 1.02, .13), (cx, y, cz + rnd.uniform(-.015, .015)), col, (0, sx * slope, 0), cuts=1)
    # 屋脊
    P.rbox((.5, length + .2, .3), (0, 0, y0 + rise + .16), C['roof_red2'], cuts=1)


def timber(P, w, d, h):
    """木框架：转角柱、腰线、山墙斜撑。"""
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.rbox((.36, .36, h + .1), (sx * w / 2, sy * d / 2, h / 2), C['beam'])
    for sy in (-1, 1):
        P.rbox((w + .3, .26, .26), (0, sy * (d / 2 + .02), h), C['beam'])
        P.rbox((w + .3, .22, .22), (0, sy * (d / 2 + .02), h * .52), C['beam'])
    for sx in (-1, 1):
        P.rbox((.26, d + .3, .26), (sx * (w / 2 + .02), 0, h), C['beam'])
        P.rbox((.22, d + .3, .22), (sx * (w / 2 + .02), 0, h * .52), C['beam'])


def stone_base(P, w, d, door_w=2.4):
    """墙脚石带：平整地贴着墙，不再有鼓起来的石块。"""
    H_ = .62
    for sy in (-1, 1):
        y = sy * (d / 2 + .03)
        if sy < 0:
            seg = (w - door_w - .4) / 2
            for sx in (-1, 1):
                P.rbox((seg, .12, H_), (sx * (door_w / 2 + .2 + seg / 2), y, H_ / 2), C['stone2'], cuts=0)
        else:
            P.rbox((w + .1, .12, H_), (0, y, H_ / 2), C['stone2'], cuts=0)
    for sx in (-1, 1):
        P.rbox((.12, d + .1, H_), (sx * (w / 2 + .03), 0, H_ / 2), C['stone2'], cuts=0)
    # 一道压顶
    for sy in (-1, 1):
        P.rbox((w + .2, .16, .08), (0, sy * (d / 2 + .05), H_ + .02), C['stone3'], cuts=0) if sy > 0 else None
    for sx in (-1, 1):
        P.rbox((.16, d + .2, .08), (sx * (w / 2 + .05), 0, H_ + .02), C['stone3'], cuts=0)


def door(P, w, d, door_w=1.9, door_h=2.9, open_deg=70):
    oy = -d / 2
    n = 7
    for i in range(n):
        t = i / (n - 1) * math.pi
        rr = door_w / 2 + .18
        x, z = -math.cos(t) * rr, door_h - door_w / 2 + math.sin(t) * rr
        P.rbox((.42, .5, .3), (x, oy, z), C['stone3' if i % 2 else 'stone'], (0, -t + math.pi / 2, 0), cuts=0)
    for sx in (-1, 1):
        for i, z in enumerate((.3, .9, 1.5, 2.1)):
            P.rbox((.42, .5, .56), (sx * (door_w / 2 + .2), oy, z), C['stone2' if i % 2 else 'stone'], cuts=0)
    a = math.radians(open_deg)
    hx, hy = door_w / 2, oy - .08
    m = 4
    for i in range(m):
        w_ = door_w / m
        dd = (i + .5) * w_
        h = (door_h - door_w / 2) + math.sqrt(max(0, (door_w / 2) ** 2 - (-door_w / 2 + dd) ** 2)) - .08
        P.rbox((w_ * .96, .12, h), (hx + dd * math.cos(a), hy - dd * math.sin(a), h / 2 + .02), C['wood2' if i % 2 else 'wood'], (0, 0, -a))


def window(P, G, x, y, z, rz, w=.95, h=1.25):
    P.rbox((w + .34, .22, .18), (x, y, z - h / 2), C['wood2'], (0, 0, rz))
    P.rbox((w + .2, .2, .16), (x, y, z + h / 2 - .1), C['wood'], (0, 0, rz))
    c, s = math.cos(rz), math.sin(rz)
    for sx in (-1, 1):
        P.rbox((.14, .2, h), (x + c * sx * (w / 2 + .05), y + s * sx * (w / 2 + .05), z), C['wood'], (0, 0, rz))
    P.rbox((.08, .1, h), (x, y, z), C['wood3'], (0, 0, rz))
    P.rbox((w, .1, .08), (x, y, z), C['wood3'], (0, 0, rz))
    G.rbox((w + .1, .06, h), (x, y, z), 'glass', (0, 0, rz), cuts=0)


def interior(P, w, d):
    P.rbox((w - .3, d - .3, .12), (0, 0, .1), C['floor'], cuts=0)
    for i in range(int(w / .9)):
        P.rbox((.86, d - .35, .06), (-w / 2 + .6 + i * .9, 0, .18), C[rnd.choice(('floor', 'wood2'))], cuts=0)


def details(P, G, w, d, h, rise, windows):
    """中世纪细节：斜撑、竖棂、百叶、花箱、门灯、台阶、木桶、木箱、藤蔓、老虎窗、檐下托架。"""
    z_mid = h * .52
    # 上半层的竖向木筋和斜撑（四面）
    for sy in (-1, 1):
        y = sy * (d / 2 + .04)
        for x in (-w * .33, w * .33):
            P.rbox((.13, .08, h - z_mid), (x, y, (h + z_mid) / 2), C['beam'], cuts=0)
        for sx in (-1, 1):
            L = math.hypot(w * .17, h - z_mid)
            a = math.atan2(h - z_mid, w * .17)
            P.rbox((L, .08, .13), (sx * w * .415, y, (h + z_mid) / 2), C['beam'], (0, sx * a, 0), cuts=0)
            # 下半层转角斜撑
            Ld = math.hypot(w * .13, z_mid - .7)
            ad = math.atan2(z_mid - .7, w * .13)
            P.rbox((Ld, .08, .13), (sx * w * .435, y, (z_mid + .7) / 2), C['beam'], (0, -sx * ad, 0), cuts=0)
    for sx in (-1, 1):
        x = sx * (w / 2 + .04)
        for y in (-d * .33, d * .33):
            P.rbox((.08, .13, h - z_mid), (x, y, (h + z_mid) / 2), C['beam'], cuts=0)
        for sy in (-1, 1):
            L = math.hypot(d * .17, h - z_mid)
            a = math.atan2(h - z_mid, d * .17)
            P.rbox((.08, L, .13), (x, sy * d * .415, (h + z_mid) / 2), C['beam'], (-sy * a, 0, 0), cuts=0)
    # 檐下托架
    for sx in (-1, 1):
        for i in range(5):
            y = -d / 2 + (i + .5) * d / 5
            P.rbox((.5, .14, .14), (sx * (w / 2 + .2), y, h - .22), C['wood3'], (0, sx * .6, 0), cuts=0)
    # 窗：百叶和花箱
    for x, y, z, rz in windows:
        c, s = math.cos(rz), math.sin(rz)
        out = 1 if (rz != 0 and x > 0) or (rz == 0 and y > 0) else -1
        nx, ny = -s * out * -1 if rz != 0 else 0, c * out if rz == 0 else 0
        if rz != 0:
            nx, ny = out, 0
        for sd in (-1, 1):
            P.rbox((.34, .07, 1.3), (x + c * sd * .78 + nx * .1, y + s * sd * .78 + ny * .1, z), C['shut'], (0, 0, rz), cuts=0)
            P.rbox((.3, .08, .05), (x + c * sd * .78 + nx * .13, y + s * sd * .78 + ny * .13, z + .3), C['wood3'], (0, 0, rz), cuts=0)
        bx, by = x + nx * .22, y + ny * .22
        P.rbox((1.25, .3, .24), (bx, by, z - .78), C['wood2'], (0, 0, rz), cuts=0)
        for i in range(7):
            u = -.5 + i / 6
            P.sphere(.11, (bx + c * u, by + s * u, z - .58 + rnd.uniform(0, .08)), C[rnd.choice(('flower1', 'flower2', 'flower3', 'green'))], 5)
    # 台阶和门灯
    P.rbox((2.9, 1.0, .18), (0, -d / 2 - .55, .08), C['stone3'], cuts=0)
    P.rbox((2.3, .55, .18), (0, -d / 2 - .95, .22) if False else (0, -d / 2 - .4, .24), C['stone'], cuts=0)
    for sx in (-1, 1):
        lx = sx * 1.6
        P.rbox((.08, .42, .08), (lx, -d / 2 - .22, 3.05), C['iron'], cuts=0)
        P.rbox((.3, .3, .05), (lx, -d / 2 - .42, 2.98), C['iron'], cuts=0)
        G.rbox((.22, .22, .32), (lx, -d / 2 - .42, 2.78), 'glass', cuts=0)
    # 木桶和木箱
    bx = w / 2 - .5
    for k, (ox, oy, z0) in enumerate(((0, 0, 0), (.7, .25, 0), (.3, .1, .95))):
        cx, cy = bx + ox, -d / 2 - 1.0 + oy
        P.cyl(.34, .38, .9, (cx, cy, z0 + .45), C['wood2'], 10)
        for zz in (.2, .7):
            P.cyl(.4, .4, .06, (cx, cy, z0 + zz), C['iron'], 10)
    for k, (ox, oy, z0, sz) in enumerate(((-.2, 0, 0, .8), (.6, .1, 0, .65), (.15, .05, .8, .55))):
        P.rbox((sz, sz, sz), (-w / 2 + .6 + ox, -d / 2 - .9 + oy, z0 + sz / 2), C['wood' if k % 2 else 'wood3'], (0, 0, k * .4), cuts=0)
    # 老虎窗（东坡面）
    dy = d * .05
    dx = w * .23
    dz = h + rise * (1 - dx / (w / 2))
    P.rbox((1.0, 1.25, 1.15), (dx, dy, dz + .25), C['plaster2'], cuts=0)
    G.rbox((.08, .72, .72), (dx + .52, dy, dz + .3), 'glass', cuts=0)
    P.rbox((.1, .9, .08), (dx + .54, dy, dz + .68), C['wood3'], cuts=0)
    P.rbox((.1, .08, .78), (dx + .55, dy, dz + .3), C['wood3'], cuts=0)
    for sg in (-1, 1):
        P.rbox((1.5, .92, .12), (dx, dy + sg * .4, dz + 1.02), C['roof_red2'], (sg * .72, 0, 0), cuts=0)


def build(name, w, d, h, rise, extras):
    kit.reset()
    wall, inner = shell(w, d, h)
    cutters = [inner] + arch_cutter(0, -d / 2, 1.9, 2.9, .05, 0, name='door')
    windows = extras['windows']
    for i, (x, y, z, rz) in enumerate(windows):
        cutters += arch_cutter(x, y, 1.0, 1.35, z - .65, rz, 2.0, f'w{i}')
    cut(wall, cutters)
    P, G = Mesh(), Mesh()
    timber(P, w, d, h)
    stone_base(P, w, d)
    door(P, w, d)
    interior(P, w, d)
    for x, y, z, rz in windows:
        window(P, G, x, y, z, rz)
    # 天花板，挡住从屋顶往下看到地面
    P.rbox((w, d, .14), (0, 0, h + .02), C['wood3'], cuts=0)
    # 山墙：两个三角面
    for sy in (-1, 1):
        y = sy * (d / 2 - .04)
        P.prism(w, y - .15, y + .15, h, rise, C['plaster2'])
    gable(P, w, d, h, rise)
    extras['fn'](P, G, w, d, h, rise)
    details(P, G, w, d, h, rise, windows)
    main = P.to_object('main')
    objs = finish([main, wall], G, name, outdir)
    cam = preview_setup()
    shot(cam, os.path.join(outdir, name + '.png'), (w * 1.5, -d * 2.3 - 4, h + 2.5), (0, 0, (h + rise) * .52), 40)


def fn_a(P, G, w, d, h, rise):  # 窄高屋：一根烟囱，一盏门灯
    cx, cy = w * .22, d * .22
    top = h + rise * (1 - cx / (w / 2)) + 1.5
    n = int((top - h) / .75) + 1
    for i in range(n):
        P.rbox((1.05, 1.05, .82), (cx + rnd.uniform(-.03, .03), cy, h + (i + .5) * .75), C['stone' if i % 2 else 'stone2'])
    P.rbox((1.35, 1.35, .22), (cx, cy, h + n * .75 + .05), C['iron'])
    G.sphere(.24, (-1.5, -d / 2 - .35, 2.6), 'glass', 10)
    P.rbox((.08, .55, .08), (-1.5, -d / 2 - .2, 2.92), C['iron'])


def fn_b(P, G, w, d, h, rise):  # 宽屋：花箱 + 木棚
    for x in (-w * .3, w * .3):
        P.rbox((1.3, .34, .32), (x, -d / 2 - .2, 1.1), C['wood2'])
        for i in range(5):
            P.sphere(.15, (x - .5 + i * .25, -d / 2 - .22, 1.33), C[rnd.choice(('cloth', 'gold', 'cloth2'))], 6)
    for sx in (-1, 1):
        P.rbox((.18, .18, 2.3), (sx * 1.6, -d / 2 - 1.6, 1.15), C['wood'])
    P.rbox((3.9, 1.9, .14), (0, -d / 2 - .8, 2.45), C['roof_red2'], (math.radians(-12), 0, 0))
    for i in range(5):
        P.rbox((.95, .95, .78), (-w * .25, d * .1, h + (i + .5) * .72), C['stone2' if i % 2 else 'stone'])
    P.rbox((1.25, 1.25, .2), (-w * .25, d * .1, h + 3.7), C['iron'])


def fn_c(P, G, w, d, h, rise):  # 塔屋：右侧一座小尖塔
    r = 1.35
    tx, ty = w / 2 + .3, -d / 2 + .9
    P.lathe([(r + .12, 0), (r, .6), (r * .96, h + 1.6)], C['plaster'], 18, center=(tx, ty))
    prof = [(r + .55, h + 1.55), (r * .78, h + 2.3), (r * .42, h + 3.4), (.05, h + 4.7)]
    P.lathe(prof, C['roof_red'], 18, center=(tx, ty))
    P.lathe([(r + .12, h + 1.3), (r + .22, h + 1.5), (r + .12, h + 1.7)], C['beam'], 18, center=(tx, ty))
    G.rbox((.7, .1, 1.0), (tx + r * .42, ty - r * .92, h - .4), 'glass', (0, 0, .43), cuts=0)
    P.rbox((.95, .16, .14), (tx + r * .43, ty - r * .94, h - .95), C['wood2'], (0, 0, .43))
    P.rbox((.95, .16, .14), (tx + r * .43, ty - r * .94, h + .15), C['wood2'], (0, 0, .43))
    P.rbox((.2, .2, .4), (tx, ty, h + 4.8), C['gold'])


WIN_Z = 2.1
build('house_a', 5.6, 6.4, 5.2, 3.6, dict(fn=fn_a, windows=[(5.6 / 2, 0, WIN_Z, math.pi / 2), (-5.6 / 2, 0, WIN_Z, math.pi / 2), (1.4 + .4, -3.2, 3.9, 0)]))
build('house_b', 9.0, 6.4, 3.8, 2.9, dict(fn=fn_b, windows=[(2.8, -3.2, WIN_Z, 0), (-2.8, -3.2, WIN_Z, 0), (4.5, 0, WIN_Z, math.pi / 2)]))
build('house_c', 6.2, 6.4, 6.0, 3.4, dict(fn=fn_c, windows=[(-3.1, 0, WIN_Z, math.pi / 2), (-1.6, -3.2, 4.2, 0), (1.6, -3.2, 4.2, 0)]))
