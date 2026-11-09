# 用法：Blender --background --python gothic.py -- <输出目录> [部件名...]
# 小山顶上的哥特城堡：白石墙、深蓝尖顶、金饰。分三个模型（各不超过 3 万面），摆在同一个原点就能对齐。
# 原点是山顶中心（世界 x=127, z=176），高度用绝对海拔。+X 东，+Y 北，Z 海拔。大门朝南，正对上山的路。
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit
from kit import C, Mesh, finish, preview_setup, rnd, shot, srgb
from mathutils import Euler, Vector

args = sys.argv[sys.argv.index('--') + 1:]
outdir = args[0]
only = set(args[1:])
T = 72.0  # 山顶海拔
C.update({k: srgb(v) for k, v in dict(
    w1='#EFE8DA', w2='#DDD3C2', w3='#F8F3E8', w4='#C7BCA9', band='#B8AC97',
    sl1='#2E4A8F', sl2='#233B76', sl3='#3C5FAE', gold1='#F2C14E',
).items()})
PI = math.pi


def rot(yaw, local=(0, 0, 0)):
    return Euler((0, 0, yaw)).to_matrix() @ Euler(local).to_matrix()


def at(cx, cy, yaw, u, n):
    """墙面局部坐标（u 沿墙，n 向外）转世界。yaw=0 的墙面朝南。"""
    return (cx + math.cos(yaw) * u + math.sin(yaw) * n, cy + math.sin(yaw) * u - math.cos(yaw) * n)


def lancet(P, G, cx, cy, yaw, u, z, w, h, n=0.0, glow='glass'):
    """尖拱窗：发光的窗面、石框、竖棂。z 是窗底。"""
    x, y = at(cx, cy, yaw, u, n + .06)
    G.rbox((w, .10, h - w * .6), (x, y, z + (h - w * .6) / 2), glow, rot(yaw), cuts=0)
    G.rbox((w * .72, .10, w * .72), (x, y, z + h - w * .6), glow, rot(yaw, (0, PI / 4, 0)), cuts=0)
    x2, y2 = at(cx, cy, yaw, u, n + .12)
    P.rbox((.12, .14, h - w * .25), (x2, y2, z + (h - w * .25) / 2), C['w4'], rot(yaw), cuts=0)  # 竖棂
    P.rbox((w * .95, .14, .1), (x2, y2, z + (h - w * .6) * .62), C['w4'], rot(yaw), cuts=0)
    for s in (-1, 1):
        fx, fy = at(cx, cy, yaw, u + s * (w / 2 + .1), n + .1)
        P.rbox((.22, .22, h - w * .6), (fx, fy, z + (h - w * .6) / 2), C['w3'], rot(yaw), cuts=0)
        tx, ty = at(cx, cy, yaw, u + s * w * .27, n + .1)
        P.rbox((w * .86, .22, .22), (tx, ty, z + h - w * .32), C['w3'], rot(yaw, (0, -s * PI / 3.4, 0)), cuts=0)


def rose(P, G, cx, cy, yaw, u, z, r, n=0.0):
    """玫瑰窗：彩色发光花瓣加石框。"""
    x, y = at(cx, cy, yaw, u, n + .06)
    R = rot(yaw, (PI / 2, 0, 0))
    G.cyl(r, r, .1, (x, y, z), 'p_blue', 16, (0, 0, 0) if False else _euler(yaw))
    x2, y2 = at(cx, cy, yaw, u, n + .1)
    for i in range(8):
        a = i / 8 * math.tau
        px, py = at(cx, cy, yaw, u + math.cos(a) * r * .58, n + .14)
        G.rbox((r * .3, .08, r * .3), (px, py, z + math.sin(a) * r * .58), 'p_pink' if i % 2 else 'star', rot(yaw), cuts=0)
        bx, by = at(cx, cy, yaw, u + math.cos(a) * r * .5, n + .18)
        P.rbox((r * 1.0, .1, .1), (bx, by, z + math.sin(a) * r * .5), C['w3'], rot(yaw, (0, -a, 0)), cuts=0)
    for i in range(16):  # 外框
        a = (i + .5) / 16 * math.tau
        px, py = at(cx, cy, yaw, u + math.cos(a) * r, n + .14)
        P.rbox((r * .42, .3, .28), (px, py, z + math.sin(a) * r), C['w3'], rot(yaw, (0, -a + PI / 2, 0)), cuts=0)
    G.rbox((r * .4, .08, r * .4), (x2, y2, z), 'star', rot(yaw, (0, PI / 4, 0)), cuts=0)


def _euler(yaw):
    # 圆柱轴线转到墙面法线方向
    return (PI / 2, 0, yaw)


def pinnacle(P, x, y, z, r, h, c='w1', tip=True):
    """小尖塔。"""
    P.rbox((r * 2, r * 2, h * .3), (x, y, z + h * .15), C[c], cuts=0)
    P.cyl(r * 1.25, .02, h * .72, (x, y, z + h * .3 + h * .36), C['w3'], 4, (0, 0, PI / 4))
    if tip:
        P.sphere(r * .28, (x, y, z + h * 1.0), C['gold1'], 6)


def spire(P, cx, cy, z, r, h, seg=8, ribs=True):
    """深蓝尖顶：瓦色分段，棱线是细金线，底部有小老虎窗，顶上金球和尖针。"""
    n = max(5, int(h / 2.2))
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        r0, r1 = r * (1 - t0) ** 1.08 + .025, r * (1 - t1) ** 1.08 + .025
        P.cyl(r0, r1, h / n, (cx, cy, z + h * (t0 + t1) / 2), C[('sl1', 'sl2', 'sl1', 'sl3')[i % 4]], seg, (0, 0, PI / seg))
    P.cyl(r * 1.1, r * 1.0, .36, (cx, cy, z + .18), C['gold1'], seg, (0, 0, PI / seg))
    if ribs:
        for i in range(seg):
            a = (i + .5) / seg * math.tau + PI / seg
            pts = []
            for t in (0.0, .5, 1.0):
                rr = (r * (1 - t) ** 1.08 + .025) * 1.01
                pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr, z + h * t))
            P.tube(pts, [.07, .055, .03], C['gold1'], seg=3)
        for i in range(4):  # 老虎窗
            a = i / 4 * math.tau + PI / 4
            rr = r * .74
            x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
            P.rbox((r * .3, r * .3, r * .46), (x, y, z + h * .17), C['w3'], (0, 0, a), cuts=0)
            P.cyl(r * .24, .02, r * .62, (x, y, z + h * .17 + r * .54), C['sl3'], 4, (0, 0, a + PI / 4))
    P.sphere(max(r * .1, .2), (cx, cy, z + h + .05), C['gold1'], 8)
    P.cyl(.1, .01, 2.6, (cx, cy, z + h + 1.3), C['gold1'], 6)


def needle(P, G, x, y, z, r, h, sp_h):
    """贴在主塔边上的细高圆塔，做出尖塔成簇的感觉。"""
    P.cyl(r, r * .92, h, (x, y, z + h / 2), C['w3'], 8)
    for k in range(1, 4):
        P.cyl(r * 1.16, r * 1.16, .18, (x, y, z + h * k / 3), C['band'], 8)
    G.rbox((r * .7, r * 2.06, h * .16), (x, y, z + h * .82), 'glass', cuts=0)
    spire(P, x, y, z + h, r * 1.18, sp_h, seg=6, ribs=False)


def arcade(P, cx, cy, yaw, width, z, h, n, count):
    """盲券廊：一排浅浮雕尖拱，让大墙面不空。"""
    w = width / count
    for i in range(count):
        u = -width / 2 + (i + .5) * w
        x, y = at(cx, cy, yaw, u, n + .05)
        P.rbox((w * .66, .08, h - w * .35), (x, y, z + (h - w * .35) / 2), C['w4'], rot(yaw), cuts=0)
        P.rbox((w * .47, .08, w * .47), (x, y, z + h - w * .35), C['w4'], rot(yaw, (0, PI / 4, 0)), cuts=0)
        x2, y2 = at(cx, cy, yaw, u + w / 2, n + .09)
        P.rbox((w * .16, .16, h), (x2, y2, z + h / 2), C['w3'], rot(yaw), cuts=0)
    x3, y3 = at(cx, cy, yaw, 0, n + .1)
    P.rbox((width, .2, .2), (x3, y3, z + h + .1), C['band'], rot(yaw), cuts=0)


def stones(P, cx, cy, yaw, width, z0, z1, n=0.0, count=40):
    """墙面上零散的石块，让大面不单调。"""
    for _ in range(count):
        u = rnd.uniform(-width / 2 + .4, width / 2 - .4)
        z = rnd.uniform(z0 + .3, z1 - .3)
        x, y = at(cx, cy, yaw, u, n + .03)
        P.rbox((rnd.uniform(.7, 1.4), .1, rnd.uniform(.32, .46)), (x, y, z), C[rnd.choice(('w2', 'w3', 'w4'))], rot(yaw), cuts=0)


def gable_roof(P, cx, cy, yaw, z, w, length, rise, over=.5):
    """陡峭的双坡屋顶，屋脊沿局部 Y。yaw=0 时屋脊南北走向。"""
    half = w / 2 + over
    slope = math.atan2(rise, half)
    run = half / math.cos(slope)
    rows = max(5, int(run / 1.35))
    for sx in (-1, 1):
        for r in range(rows):
            d = run * ((r + .5) / rows - .5)
            ux = sx * (half / 2 - math.cos(slope) * d)
            zz = z + rise / 2 + math.sin(slope) * d
            px = cx + math.cos(yaw) * ux
            py = cy + math.sin(yaw) * ux
            P.rbox((run / rows * 1.14, length + over * 2, .32), (px, py, zz), C[('sl1', 'sl2', 'sl1', 'sl3', 'sl2')[r % 5]], rot(yaw, (0, sx * slope, 0)), cuts=0)
    P.rbox((.5, length + over * 2 + .3, .36), (cx, cy, z + rise + .1), C['gold1'], rot(yaw), cuts=0)
    # 屋脊上的小尖饰
    k = max(2, int(length / 3.2))
    for i in range(k):
        v = -length / 2 + (i + .5) * length / k
        px = cx - math.sin(yaw) * v
        py = cy + math.cos(yaw) * v
        P.cyl(.14, .01, 1.3, (px, py, z + rise + .9), C['gold1'], 4)


def gable_wall(P, cx, cy, yaw, n, z, w, rise, c='w1', t=.7):
    """山墙（三角形墙面）。"""
    pts = [(-w / 2, z), (w / 2, z), (0, z + rise)]
    vs = []
    for off in (n, n - t):
        for u, zz in pts:
            x, y = at(cx, cy, yaw, u, off)
            vs.append(P.bm.verts.new((x, y, zz)))
    a, b = vs[:3], vs[3:]
    P.bm.faces.new(a)
    P.bm.faces.new(b[::-1])
    for i in range(3):
        j = (i + 1) % 3
        P.bm.faces.new((a[i], b[i], b[j], a[j]))
    P.paint(vs, C[c])


def square_tower(P, G, cx, cy, z0, h, w, sp_h, window_levels=3, spire_r=None):
    """方塔：逐层收分的角柱、束带、尖拱窗、女儿墙、四角小尖塔、高尖顶。"""
    P.rbox((w, w, h), (cx, cy, z0 + h / 2), C['w1'], cuts=0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            levels = 3
            for k in range(levels):
                s = (w * .19) * (1 - k * .18)
                zb = z0 + h * k / levels
                P.rbox((s, s, h / levels + .1), (cx + sx * (w / 2 + s * .22), cy + sy * (w / 2 + s * .22), zb + h / levels / 2), C['w2' if k % 2 else 'w3'], cuts=0)
    nb = max(3, int(h / 6.5))
    for i in range(1, nb + 1):
        P.rbox((w + .45, w + .45, .34), (cx, cy, z0 + h * i / nb), C['band'], cuts=0)
    win_h = min(h / window_levels * .62, 6.0)
    for yaw in (0, PI / 2, PI, -PI / 2):
        for lv in range(window_levels):
            zb = z0 + h * (lv + .22) / window_levels
            count = 2 if w >= 6 and lv == window_levels - 1 else 1
            for j in range(count):
                u = 0 if count == 1 else (j - .5) * w * .42
                lancet(P, G, cx, cy, yaw, u, zb, w * .2, win_h, w / 2)
        stones(P, cx, cy, yaw, w, z0, z0 + h, w / 2, 10)
        arcade(P, cx, cy, yaw, w * .8, z0 + .4, h * .13, w / 2, 4)
    top = z0 + h
    P.rbox((w + .9, w + .9, .5), (cx, cy, top + .25), C['w3'], cuts=0)
    k = max(3, int(w / 1.1))
    for yaw in (0, PI / 2, PI, -PI / 2):
        for i in range(k):
            u = (i + .5) / k * w - w / 2
            x, y = at(cx, cy, yaw, u, w / 2 + .2)
            P.rbox((w / k * .55, .34, 1.1), (x, y, top + .95), C['w1'], rot(yaw), cuts=0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            pinnacle(P, cx + sx * w * .5, cy + sy * w * .5, top + .4, w * .09, w * 1.25)
            needle(P, G, cx + sx * (w / 2 + .55), cy + sy * (w / 2 + .55), z0 + h * .5, w * .12, h * .36, w * .95)
    spire(P, cx, cy, top + .4, spire_r or w * .43, sp_h)


def buttress(P, G, x_wall, y, side, z0, top, reach=4.2):
    """飞扶壁：外侧墩柱 + 两道斜撑 + 墩顶小尖塔。"""
    px = x_wall + side * reach
    H = top - z0 - 3.2
    P.rbox((1.3, 1.3, H), (px, y, z0 + H / 2), C['w2'], cuts=0)
    P.rbox((1.6, 1.6, .5), (px, y, z0 + H * .55), C['band'], cuts=0)
    pinnacle(P, px, y, z0 + H, .6, 3.6)
    for dz, drop in ((0.0, 3.0), (-3.0, 3.0)):
        xa, xb = px - side * .5, x_wall
        za, zb = z0 + H - .6 + dz, top - .4 + dz
        L = math.hypot(xa - xb, za - zb)
        ang = math.atan2(zb - za, abs(xa - xb)) * side
        P.rbox((L, .55, .5), ((xa + xb) / 2, y, (za + zb) / 2), C['w3'], (0, ang, 0), cuts=0)
    x0 = x_wall + side * .3
    return x0


def part_main():
    """中殿、十字翼、半圆后殿：空心大厅，南门可进。"""
    kit.reset()
    P, G = Mesh(), Mesh()
    NW, NL, NH = 14.0, 22.0, 17.0  # 中殿宽、长、墙高
    cy = 3.0
    y0, y1 = cy - NL / 2, cy + NL / 2  # 南 -8 北 14
    wall = .8
    # 地板
    P.rbox((NW, NL, .3), (0, cy, T + .05), C['floor'], cuts=0)
    # 东西墙
    for sx in (-1, 1):
        P.rbox((wall, NL, NH), (sx * (NW - wall) / 2, cy, T + NH / 2), C['w1'], cuts=0)
        yaw = -PI / 2 if sx > 0 else PI / 2
        for y in (-5.5, -1.5, 9.5, 13.0):
            # 高侧窗
            u = (y - cy) * (1 if sx > 0 else -1)
            lancet(P, G, 0, cy, yaw, u, T + 7.6, 1.5, 6.6, NW / 2)
            lancet(P, G, 0, cy, yaw, u, T + 2.4, 1.0, 3.4, NW / 2)
        stones(P, 0, cy, yaw, NL, T, T + NH, NW / 2, 44)
        arcade(P, 0, cy, yaw, NL - 1, T + .4, 1.8, NW / 2, 12)
        for y in (-7.5, -3.5, .5, 7.5, 11.5):
            buttress(P, G, sx * NW / 2, y, sx, T, T + NH)
        P.rbox((.6, NL + .6, .4), (sx * (NW / 2 + .1), cy, T + NH), C['band'], cuts=0)
        # 檐口的小雉堞
        for i in range(14):
            y = y0 + (i + .5) * NL / 14
            P.rbox((.3, .75, .8), (sx * (NW / 2 + .15), y, T + NH + .55), C['w3'], cuts=0)
    # 南立面：大门、玫瑰窗、山墙
    door_w, door_h = 3.8, 6.0
    panel = (NW - door_w) / 2
    for sx in (-1, 1):
        P.rbox((panel, wall, NH), (sx * (door_w + panel) / 2, y0 + wall / 2, T + NH / 2), C['w1'], cuts=0)
    P.rbox((door_w, wall, NH - door_h), (0, y0 + wall / 2, T + door_h + (NH - door_h) / 2), C['w1'], cuts=0)
    stones(P, 0, y0, 0, NW, T + door_h, T + NH, 0, 22)
    # 尖拱门的层层门券
    for lay in range(3):
        grow = lay * .5
        pts = 9
        for s in (-1, 1):
            for i in range(pts):
                t = i / (pts - 1)
                a = t * PI / 2 * .78
                R = door_w * .78 + grow
                ox = door_w / 2 + grow - R * (1 - math.cos(a))
                oz = T + door_h - door_w * .5 + R * math.sin(a)
                P.rbox((.5, .34 + lay * .1, .62), (s * ox, y0 - .06 - lay * .12, oz), C['w3' if lay % 2 == 0 else 'band'], (0, -s * (a), 0), cuts=0)
            P.rbox((.5, .34 + lay * .1, door_h - door_w * .5), (s * (door_w / 2 + grow), y0 - .06 - lay * .12, T + (door_h - door_w * .5) / 2), C['w3' if lay % 2 == 0 else 'band'], cuts=0)
    rose(P, G, 0, y0, 0, 0, T + 11.5, 3.0, 0)
    gable_wall(P, 0, y0, 0, .0, T + NH, NW, 11.0)
    lancet(P, G, 0, y0, 0, 0, T + NH + 1.8, 1.4, 5.0, .05)
    for u in (-3.3, 3.3):
        pinnacle(P, u, y0 - .2, T + NH + (NW / 2 - abs(u)) * 11.0 / (NW / 2) - 1.4, .35, 3.2)
    pinnacle(P, 0, y0 - .1, T + NH + 10.6, .45, 4.2)
    # 屋顶
    gable_roof(P, 0, cy, 0, T + NH + .1, NW, NL, 11.0)
    # 北墙
    P.rbox((NW, wall, NH), (0, y1 - wall / 2, T + NH / 2), C['w1'], cuts=0)
    gable_wall(P, 0, y1, PI, .0, T + NH, NW, 11.0)
    # 十字翼（东西两侧，山墙上有玫瑰窗）
    tcy, tw, th = 3.0, 8.0, 15.0
    for sx in (-1, 1):
        cx = sx * (NW / 2 + 3.2)
        P.rbox((6.4, tw, th), (cx, tcy, T + th / 2), C['w1'], cuts=0)
        P.rbox((6.6, tw + .4, .36), (cx, tcy, T + th), C['band'], cuts=0)
        yaw = -PI / 2 if sx > 0 else PI / 2
        rose(P, G, sx * (NW / 2 + 6.4), tcy, yaw, 0, T + 10.0, 2.2, 0)
        lancet(P, G, sx * (NW / 2 + 6.4), tcy, yaw, -2.2, T + 2.2, 1.2, 4.6, 0)
        lancet(P, G, sx * (NW / 2 + 6.4), tcy, yaw, 2.2, T + 2.2, 1.2, 4.6, 0)
        stones(P, sx * (NW / 2 + 6.4), tcy, yaw, tw, T, T + th, 0, 18)
        gable_wall(P, sx * (NW / 2 + 6.4), tcy, yaw, 0, T + th, tw, 7.5)
        gable_roof(P, cx, tcy, PI / 2, T + th + .05, tw, 6.8, 7.5)
        for sy in (-1, 1):
            pinnacle(P, sx * (NW / 2 + 6.3), tcy + sy * tw / 2, T + th - 1, .55, 4.2)
    # 后殿：多边形，放在北端
    ax, ay, ar = 0.0, y1, 6.6
    sides = 7
    for i in range(sides):
        a0 = i / sides * PI
        a1 = (i + 1) / sides * PI
        xa, ya = ax + math.cos(a0) * ar, ay + math.sin(a0) * ar
        xb, yb = ax + math.cos(a1) * ar, ay + math.sin(a1) * ar
        mx, my = (xa + xb) / 2, (ya + yb) / 2
        L = math.hypot(xa - xb, ya - yb)
        yaw = math.atan2(yb - ya, xb - xa) + PI
        P.rbox((L + .1, wall, 14.0), (mx, my, T + 7), C['w1'], rot(yaw), cuts=0)
        lancet(P, G, mx, my, yaw, 0, T + 4.5, 1.1, 7.0, .42)
        pinnacle(P, xa * 1.06, ya + (ya - ay) * .06, T + 12.8, .42, 4.0)
    for i in range(6):  # 锥形屋顶
        t0, t1 = i / 6, (i + 1) / 6
        P.cyl(ar * 1.06 * (1 - t0) + .05, ar * 1.06 * (1 - t1) + .05, 9.5 / 6, (ax, ay, T + 14 + 9.5 * (t0 + t1) / 2), C[('sl1', 'sl2', 'sl3')[i % 3]], 14)
    P.sphere(.34, (ax, ay, T + 24), C['gold1'], 8)
    # 大厅内部：两排柱子，吊灯和尽头的彩窗，让室内是亮的
    for sx in (-1, 1):
        for y in (-5.0, -1.0, 3.0, 7.0, 11.0):
            P.cyl(.6, .5, 13.0, (sx * 4.0, y, T + 6.6), C['w3'], 8)
            P.rbox((1.5, 1.5, .5), (sx * 4.0, y, T + .4), C['w2'], cuts=0)
        for y in (-3.0, 5.0, 11.0):
            G.sphere(.5, (sx * 2.4, y, T + 8.0), 'glass', 8)
            P.cyl(.04, .04, 8.5, (sx * 2.4, y, T + 12.5), C['iron'], 4)
    G.cyl(3.0, 3.0, .12, (0, y1 - .9, T + 9.5), 'star', 14, (PI / 2, 0, 0))
    P.rbox((5, 2.0, 1.0), (0, 12.0, T + .6), C['w3'], cuts=0)  # 高台
    G.sphere(.6, (0, 12.0, T + 2.2), 'p_blue', 10)
    main = P.to_object('main')
    finish([main], G, 'gothic_main', outdir, tex_size=2048)
    return preview_setup()


def part_towers():
    """西立面双塔、中央十字塔高尖顶、后方小塔。"""
    kit.reset()
    P, G = Mesh(), Mesh()
    # 南立面两座塔（高度不同，错落）
    square_tower(P, G, -9.5, -8.0, T, 27.0, 5.0, 21.0)
    square_tower(P, G, 9.5, -8.0, T, 23.0, 4.6, 19.0)
    # 钟楼的大钟面（左塔），昼夜切换的象征
    G.cyl(1.9, 1.9, .1, (-9.5, -8.0 - 2.68, T + 19.0), 'star', 18, (PI / 2, 0, 0))
    for i in range(12):
        a = i / 12 * math.tau
        P.rbox((.16, .1, .5), (-9.5 + math.cos(a) * 1.6, -10.8, T + 19 + math.sin(a) * 1.6), C['iron'], (0, -a + PI / 2, 0), cuts=0)
    P.rbox((.14, .1, 1.3), (-9.5, -10.82, T + 19.6), C['iron'], cuts=0)
    P.rbox((.14, .1, .9), (-9.2, -10.82, T + 18.8), C['iron'], (0, -.8, 0), cuts=0)
    for i in range(20):
        a = i / 20 * math.tau
        P.rbox((.75, .22, .26), (-9.5 + math.cos(a) * 2.02, -10.74, T + 19 + math.sin(a) * 2.02), C['gold1'], (0, -a + PI / 2, 0), cuts=0)
    # 中央十字塔：方形基座 → 八角灯笼层 → 整座城堡最高的尖顶
    cx, cy = 0.0, 3.0
    base_z = T + 22.0
    P.rbox((9.0, 9.0, 12.0), (cx, cy, base_z + 6.0), C['w1'], cuts=0)
    for i in range(3):
        P.rbox((9.5, 9.5, .34), (cx, cy, base_z + i * 6.0), C['band'], cuts=0)
    for yaw in (0, PI / 2, PI, -PI / 2):
        for u in (-2.6, 0, 2.6):
            lancet(P, G, cx, cy, yaw, u, base_z + 1.0, 1.25, 8.0, 4.5)
        stones(P, cx, cy, yaw, 9, base_z, base_z + 12, 4.5, 12)
    lan_z = base_z + 12.0
    P.rbox((10.0, 10.0, .5), (cx, cy, lan_z + .25), C['w3'], cuts=0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = cx + sx * 4.6, cy + sy * 4.6
            pinnacle(P, x, y, lan_z + .4, .6, 12.0)
            # 从角上撑到灯笼层的小飞扶壁
            P.rbox((.42, .42, 4.4), (cx + sx * 3.4, cy + sy * 3.4, lan_z + 3.2), C['w3'], Euler((-sy * .62, sx * .62, 0)), cuts=0)
    P.cyl(4.1, 3.7, 7.0, (cx, cy, lan_z + 3.9), C['w1'], 8, (0, 0, PI / 8))
    for i in range(8):
        a = (i + .5) / 8 * math.tau
        yaw = a + PI / 2
        x, y = cx + math.cos(a) * 3.82, cy + math.sin(a) * 3.82
        G.rbox((.95, .1, 3.8), (x, y, lan_z + 3.9), 'glass', rot(a + PI / 2), cuts=0)
        P.rbox((.12, .14, 4.2), (x + math.cos(a) * .06, y + math.sin(a) * .06, lan_z + 3.9), C['w4'], rot(a + PI / 2), cuts=0)
        ca = i / 8 * math.tau
        P.rbox((.5, .5, 7.4), (cx + math.cos(ca) * 3.95, cy + math.sin(ca) * 3.95, lan_z + 3.9), C['w3'], cuts=0)
    P.cyl(4.5, 4.3, .4, (cx, cy, lan_z + 7.6), C['band'], 8, (0, 0, PI / 8))
    spire(P, cx, cy, lan_z + 7.7, 3.2, 23.0)
    # 北侧两座细塔，让侧面和背面也有层次
    for sx in (-1, 1):
        px, py = sx * 11.0, 13.5
        P.cyl(1.9, 1.7, 22.0, (px, py, T + 11), C['w1'], 10)
        for k in range(1, 4):
            P.cyl(2.08, 2.08, .3, (px, py, T + k * 5.5), C['band'], 10)
            for a in (0, 2.1, 4.2):
                lancet(P, G, px, py, a + (k % 2) * 1.0, 0, T + k * 5.5 + 1.0, .62, 2.6, 1.76)
        spire(P, px, py, T + 22.0, 2.05, 17.0, seg=8, ribs=False)
    main = P.to_object('main')
    finish([main], G, 'gothic_towers', outdir, tex_size=2048)
    return preview_setup()


def part_wall():
    """低矮外墙、南门楼和庭院：山路走到这里进城。"""
    kit.reset()
    P, G = Mesh(), Mesh()
    R = 18.6
    sides = 16
    base = T - 3.5
    top = T + 5.0
    verts = [(math.cos(i / sides * math.tau) * R, math.sin(i / sides * math.tau) * R) for i in range(sides)]
    south = 12  # 第 12 个顶点是正南
    for i in range(sides):
        a, b = verts[i], verts[(i + 1) % sides]
        mid_a = (i + .5) / sides * math.tau
        if abs(((mid_a - 3 * PI / 2 + PI) % math.tau) - PI) < PI / sides * 1.6:
            continue  # 留给南门
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        L = math.hypot(a[0] - b[0], a[1] - b[1])
        yaw = math.atan2(b[1] - a[1], b[0] - a[0]) + PI
        P.rbox((L + .4, 1.5, top - base), (mx, my, (top + base) / 2), C['w2'], rot(yaw), cuts=0)
        P.rbox((L + .6, 1.8, .3), (mx, my, top), C['band'], rot(yaw), cuts=0)
        for k in range(5):
            u = (k + .5) / 5 * L - L / 2
            x, y = at(mx, my, yaw, u, .6)
            P.rbox((L / 5 * .55, .34, 1.0), (x, y, top + .6), C['w1'], rot(yaw), cuts=0)
        stones(P, mx, my, yaw, L, base + 2.5, top, .76, 7)
        if i % 3 == 0:  # 外墙上的小圆塔
            P.cyl(1.35, 1.2, top + 3.5 - base, (a[0] * 1.03, a[1] * 1.03, (top + 3.5 + base) / 2), C['w1'], 10)
            P.cyl(1.5, 1.5, .3, (a[0] * 1.03, a[1] * 1.03, top + 3.5), C['band'], 10)
            lancet(P, G, a[0] * 1.03, a[1] * 1.03, math.atan2(a[1], a[0]) + PI / 2, 0, top - .5, .5, 2.5, 1.26)
            spire(P, a[0] * 1.03, a[1] * 1.03, top + 3.6, 1.6, 10.0, seg=8, ribs=False)
    # 南门楼：两座门塔夹一道尖拱门
    gy = -R + .1
    for sx in (-1, 1):
        x = sx * 4.1
        P.rbox((3.0, 3.0, top + 5 - base), (x, gy, (top + 5 + base) / 2), C['w1'], cuts=0)
        P.rbox((3.5, 3.5, .3), (x, gy, top + 5), C['band'], cuts=0)
        lancet(P, G, x, gy, 0, 0, T + 5.2, .8, 3.0, 1.5)
        arcade(P, x, gy, 0, 2.6, T + 1.0, 2.2, 1.5, 3)
        spire(P, x, gy, top + 5.2, 1.75, 13.0)
        G.sphere(.34, (x - sx * 1.75, gy - 1.9, T + 3.8), 'glass', 8)  # 门灯
        P.rbox((.16, .7, .16), (x - sx * 1.75, gy - 1.6, T + 4.4), C['iron'], cuts=0)
    P.rbox((5.0, 2.4, 4.0), (0, gy, T + 7.4 + 1), C['w1'], cuts=0)
    for i in range(5):
        P.rbox((.6, .4, 1.0), (-2.0 + i, gy - 1.05, T + 10.9), C['w3'], cuts=0)
    pts = 7
    for s in (-1, 1):
        for i in range(pts):
            t = i / (pts - 1)
            a = t * PI / 2 * .78
            r_ = 3.0
            ox = 2.4 - r_ * (1 - math.cos(a))
            oz = T + 3.4 + r_ * math.sin(a)
            P.rbox((.5, 2.5, .62), (s * ox, gy, oz), C['w3'], (0, -s * a, 0), cuts=0)
    # 庭院地面（石板），刚好盖住山顶
    for i in range(70):
        a, d = rnd.uniform(0, math.tau), math.sqrt(rnd.uniform(0, 1)) * 15
        x, y = math.cos(a) * d, math.sin(a) * d
        if abs(x) < 8 and -9 < y < 16:
            continue
        P.rbox((rnd.uniform(1.0, 2.2), rnd.uniform(1.0, 2.0), .1), (x, y, T + .05), C[rnd.choice(('w2', 'w4', 'band'))], (0, 0, rnd.uniform(0, 3)), cuts=0)
    # 门内主道
    P.rbox((4.6, 10.5, .14), (0, -13.6, T + .06), C['w4'], cuts=0)
    main = P.to_object('main')
    finish([main], G, 'gothic_wall', outdir, tex_size=1024)
    return preview_setup()


PARTS = dict(gothic_main=part_main, gothic_towers=part_towers, gothic_wall=part_wall)
for name, fn in PARTS.items():
    if only and name not in only:
        continue
    cam = fn()
    shot(cam, os.path.join(outdir, name + '.png'), (10, -70, T + 22), (0, 0, T + 24), 38, (800, 900))
print('DONE')
