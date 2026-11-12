#!/usr/bin/env python3
"""龙眠之境第二版界面贴图（2026-11-11）。

和第一版（make_ui.py，小方片 GLB）不同：这一版的图直接以 PNG/JPG 的 base64 写进 Lua，
运行时用 Texture2D.LoadImage 载入，不受编辑器导入贴图压到 1024 的限制，所以地图和字都是清楚的。

输出：
  assets/ui2/png/*.png|jpg      预览
  assets/ui2/layout.json        各小图在图集里的位置
  assets/ui2/ui2_data.lua       嵌进 dragon_world_bridge.lua 的数据段（tools/ui/embed_ui2.py 负责嵌入）
字体：思源黑体 Heavy、思源宋体 Heavy、霞鹜文楷（均为 SIL OFL）。
"""
import base64, io, json, os, re, sys, zipfile
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJ = os.path.expanduser('~/Library/Application Support/AI World Creator/projects/project_lapv8fm0')
AUTHOR = f'{PROJ}/ai-sessions/workspace_sbazsi67/wprefabs/dragon_phase1_merged'
OUT = f'{REPO}/assets/ui2'
os.makedirs(f'{OUT}/png', exist_ok=True)
F = f'{REPO}/assets/fonts'
HEAVY = f'{F}/SourceHanSansCN-Heavy.ttf'
SERIF = f'{F}/SourceHanSerifCN-Heavy.otf'
KAI = f'{F}/LXGWWenKai-Medium.otf'
INK = (46, 33, 22)
CINNABAR = (156, 43, 30)
CREAM = (243, 231, 201)
GOLD = (201, 164, 92)
SEA = 26.6


def font(path, size):
    return ImageFont.truetype(path, int(size))


def noise(h, w, scale, seed):
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, (max(2, h // scale), max(2, w // scale))).astype(np.float32)
    n = cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
    return n / (np.abs(n).max() + 1e-6)


def parchment(w, h, seed=0, burn=True, edge=1.0):
    base = np.array([234, 220, 191], np.float32)
    dark = np.array([184, 150, 104], np.float32)
    n1 = noise(h, w, 40, seed) * .5 + noise(h, w, 9, seed + 1) * .25
    fib = cv2.GaussianBlur(np.random.default_rng(seed + 2).normal(0, 1, (h, w)).astype(np.float32), (0, 0), .8)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ed = np.minimum.reduce([xx, w - 1 - xx, yy, h - 1 - yy])
    edge_n = (noise(h, w, 14, seed + 3) * 9 + noise(h, w, 4, seed + 4) * 3) * edge
    d = ed + edge_n
    burnt = np.clip(1 - (d - 6) / (34 * edge), 0, 1) ** 1.6 if burn else np.zeros_like(d)
    t = np.clip(.18 + n1 * .22 + burnt * .8, 0, 1)[..., None]
    rgb = base * (1 - t) + dark * t + fib[..., None] * 5
    rgb = rgb * (1 - .55 * np.clip(1 - (d - 2) / 8, 0, 1) ** 2)[..., None]
    a = np.clip((d - 1) * 255 / 3, 0, 255)
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a]).astype(np.uint8))


def text_w(f, s):
    b = f.getbbox(s)
    return b[2] - b[0]


def wrap(s, f, width):
    """按宽度折行；标点不落在行首。"""
    out, cur = [], ''
    for ch in s:
        if ch == '\n':
            out.append(cur); cur = ''
            continue
        if text_w(f, cur + ch) > width and cur:
            if ch in '，。、；：！？”』」）…—':
                cur += ch
                out.append(cur); cur = ''
                continue
            out.append(cur); cur = ''
        cur += ch
    if cur:
        out.append(cur)
    return out


def rough(im, seed, amt=.16):
    """墨色深浅不匀。"""
    a = np.array(im)
    k = noise(a.shape[0], a.shape[1], 5, seed) * amt + (1 - amt * .5)
    a[..., 3] = np.clip(a[..., 3] * k, 0, 255).astype(np.uint8)
    return Image.fromarray(a)


def label(text, f, color, pad=6, shadow=None, stroke=0, stroke_fill=None, spacing=0):
    """单行字，紧贴裁切。"""
    w = text_w(f, text) + pad * 2 + stroke * 2 + (4 if shadow else 0)
    asc, desc = f.getmetrics()
    h = asc + desc + pad * 2 + stroke * 2
    im = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if shadow:
        d.text((pad + stroke + 2, pad + stroke + 2), text, font=f, fill=shadow)
    d.text((pad + stroke, pad + stroke), text, font=f, fill=color + (255,) if len(color) == 3 else color, stroke_width=stroke, stroke_fill=stroke_fill)
    return im


def para(lines, f, color, lh, w, align='l', pad=6):
    h = int(len(lines) * lh + pad * 2)
    im = Image.new('RGBA', (int(w), h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        if align == 'c':
            d.text((w / 2, pad + i * lh), ln, font=f, fill=color + (255,), anchor='ma')
        else:
            d.text((pad, pad + i * lh), ln, font=f, fill=color + (255,))
    return im


def ss(draw_fn, w, h, S=3):
    """超采样画线稿，返回 RGBA。"""
    im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(im), S)
    return im.resize((w, h), Image.LANCZOS)


def line(d, pts, width, color, S=1):
    pts = [(x * S, y * S) for x, y in pts]
    d.line(pts, fill=color, width=int(width * S), joint='curve')
    r = width * S / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse([x - r, y - r, x + r, y + r], fill=color)


# =====================================================================
# 图集打包
class Atlas:
    def __init__(self, size=2048):
        self.size = size
        self.bins = []
        self.items = []
        self.rects = {}

    def add(self, name, img):
        self.items.append((name, img.convert('RGBA')))

    def pack(self):
        self.items.sort(key=lambda it: -it[1].size[1])
        shelves = []           # [bin, y, h, x]
        for name, img in self.items:
            w, h = img.size
            assert w + 2 <= self.size, name
            placed = False
            for s in shelves:
                if s[2] >= h + 2 and s[3] + w + 2 <= self.size:
                    self.rects[name] = [s[0], s[3] + 1, s[1] + 1, w, h]
                    self.bins[s[0]].paste(img, (s[3] + 1, s[1] + 1))
                    s[3] += w + 2
                    placed = True
                    break
            if placed:
                continue
            b = len(self.bins) - 1
            y = max([s[1] + s[2] for s in shelves if s[0] == b], default=0) if b >= 0 else 0
            if b < 0 or y + h + 2 > self.size:
                self.bins.append(Image.new('RGBA', (self.size, self.size), (0, 0, 0, 0)))
                b = len(self.bins) - 1
                y = 0
            shelves.append([b, y, h + 2, 0])
            s = shelves[-1]
            self.rects[name] = [b, 1, y + 1, w, h]
            self.bins[b].paste(img, (1, y + 1))
            s[3] = w + 2
        # 裁掉没用到的下半部分
        out = []
        for i, im in enumerate(self.bins):
            used = max(r[2] + r[4] for r in self.rects.values() if r[0] == i) + 2
            hh = min(self.size, int(np.ceil(used / 4) * 4))
            out.append(im.crop((0, 0, self.size, hh)))
        self.bins = out


AT = Atlas()
TEX = {}          # 名字 → (bytes, 宽, 高)


QUANT = {'atlas': 256, 'pages': 48, 'cards': 48, 'lore': 48, 'sigil': 256, 'vortex': 256}


def tex_png(name, img, quant=False):
    # 脚本包太大时编辑器保存会崩，所以贴图一律压成带透明的调色板 PNG（体积约为原来的五分之一）
    colors = next((c for k, c in QUANT.items() if name.startswith(k)), 256)
    img = img.convert('RGBA').quantize(colors=colors, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    buf = io.BytesIO()
    img.save(buf, 'PNG', optimize=True)
    img.save(f'{OUT}/png/{name}.png')
    TEX[name] = (buf.getvalue(), img.size[0], img.size[1])


def tex_jpg(name, img, q=88):
    buf = io.BytesIO()
    img.convert('RGB').save(buf, 'JPEG', quality=q, optimize=True)
    open(f'{OUT}/png/{name}.jpg', 'wb').write(buf.getvalue())
    TEX[name] = (buf.getvalue(), img.size[0], img.size[1])


# =====================================================================
# 1. 序章六页（三个对开页，透明底墨字）——按「龙魂在蛋里、龙身在雪山」的新剧情重写
PAGES = [
    ('蚀 月', ['很久以前，天空裂开了一道口子。', '人们叫它蚀月之隙。', '',
             '每到夜里，从裂隙里落下的，', '不是星光，而是影子。', '',
             '没有形状，没有声音，', '只会循着温度游荡的影灵。']),
    ('墨 曜', ['古龙墨曜从北方的山脊飞来。', '', '它没有去撕咬那些影子，',
             '而是在最高的雪峰上盘起身子，', '闭上了眼睛。', '',
             '它用自己的梦，把裂隙缝上了。', '', '从此，这片土地有了名字：', '龙眠之境。']),
    ('守 夜 人', ['龙的梦并不完美。', '夜深时，总有影灵', '从梦的缝隙里漏出来。', '',
               '于是人们点起了灯。', '灯火所及之处，影灵不敢靠近；', '灯火之外，是守夜人的夜。', '',
               '守夜人提灯走进黑暗，', '把影灵打散成月辉，', '那是龙梦的碎片。']),
    ('龙 魂', ['入睡之前，墨曜把自己的魂', '从身体里摘了下来，', '封进一枚蛋，留在西边的祭坛。', '',
             '身在雪山，压住裂隙；', '魂在蛋里，等一个人。', '',
             '月辉、火种与星露', '一同落在蛋壳上的那天，', '龙魂会醒来，飞回雪山，', '唤醒自己的身体。']),
    ('你', ['如今城堡空了，灯还亮着。', '', '你在晷石原醒来，', '手里握着一张旧地图。', '',
           '白天，这片土地属于你：', '去走，去看，去骑马，', '去喝女巫那些古怪的药水。', '',
           '夜里，如果你愿意，', '就提灯出去。', '', '#龙魂在等它的骑手。']),
]
NUM = '一二三四五六'
PS = 1.5                      # 页面贴图放大倍数（原 512×683）
PW, PH = int(512 * PS), int(683 * PS)
f_t = font(SERIF, 50 * PS)
f_b = font(KAI, 27 * PS)
f_n = font(KAI, 22 * PS)


def ink_page(title, lines, idx):
    im = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((PW / 2, 92 * PS), title, font=f_t, fill=CINNABAR + (255,), anchor='mm')
    y = 140 * PS
    d.line([(PW / 2 - 90 * PS, y), (PW / 2 - 14 * PS, y)], fill=INK + (200,), width=3)
    d.line([(PW / 2 + 14 * PS, y), (PW / 2 + 90 * PS, y)], fill=INK + (200,), width=3)
    r = 7 * PS
    d.polygon([(PW / 2, y - r), (PW / 2 + r, y), (PW / 2, y + r), (PW / 2 - r, y)], fill=CINNABAR + (230,))
    y = 186 * PS
    maxw = PW - 58 * PS - 44 * PS
    for ln in lines:
        if ln == '':
            y += 14 * PS
            continue
        red = ln.startswith('#')
        t = ln[1:] if red else ln
        f = font(KAI, 33 * PS) if red else f_b
        for seg in wrap(t, f, maxw):
            d.text((58 * PS, y), seg, font=f, fill=(CINNABAR if red else INK) + (255,))
            y += (44 if red else 38) * PS
    d.text((PW / 2, PH - 50 * PS), f'· {NUM[idx]} ·', font=f_n, fill=INK + (170,), anchor='mm')
    return rough(im, 400 + idx)


def egg_page():
    """第六页：龙魂之卵。蛋在祭坛上，一缕魂光升向雪山。"""
    def draw(d, S):
        cx, cy = PW / 2, PH / 2 + 30 * PS
        k = PS
        # 远处的雪山和山顶盘着的龙身（剪影线）
        mt = [(cx - 215 * k, 300 * k), (cx - 150 * k, 235 * k), (cx - 118 * k, 262 * k), (cx - 60 * k, 180 * k), (cx - 20 * k, 228 * k), (cx + 40 * k, 150 * k),
              (cx + 96 * k, 222 * k), (cx + 140 * k, 196 * k), (cx + 215 * k, 300 * k)]
        line(d, mt, 3 * k, INK + (170,), S)
        for a, b in (((cx + 40 * k, 150 * k), (cx + 22 * k, 190 * k)), ((cx + 40 * k, 150 * k), (cx + 62 * k, 196 * k)), ((cx - 60 * k, 180 * k), (cx - 72 * k, 214 * k))):
            line(d, [a, b], 2 * k, INK + (110,), S)
        # 龙身：山顶一道盘起的弧 + 翼尖
        body = [(cx + 4 * k, 158 * k), (cx + 18 * k, 138 * k), (cx + 44 * k, 132 * k), (cx + 66 * k, 142 * k), (cx + 78 * k, 160 * k)]
        line(d, body, 4 * k, INK + (230,), S)
        line(d, [(cx + 44 * k, 132 * k), (cx + 30 * k, 108 * k), (cx + 58 * k, 120 * k), (cx + 76 * k, 100 * k), (cx + 66 * k, 142 * k)], 2.5 * k, INK + (200,), S)
        line(d, [(cx + 4 * k, 158 * k), (cx - 10 * k, 150 * k), (cx - 4 * k, 142 * k)], 3 * k, INK + (230,), S)
        # 蛋
        ew, eh = 96 * k, 128 * k
        d.ellipse([(cx - ew) * S, (cy - eh) * S, (cx + ew) * S, (cy + eh) * S], outline=INK + (255,), width=int(4.5 * k * S))
        for row in range(-4, 5):
            yb = cy + row * 26 * k
            half = ew * np.sqrt(max(0, 1 - (row * 26 * k / eh) ** 2)) - 10 * k
            n = int(half * 2 / (30 * k))
            for i in range(n):
                x0 = cx - half + i * 30 * k + (15 * k if row % 2 else 0)
                if x0 + 26 * k < cx + half:
                    d.arc([x0 * S, (yb - 12 * k) * S, (x0 + 28 * k) * S, (yb + 12 * k) * S], 0, 180, fill=INK + (150,), width=int(2 * k * S))
        # 裂纹里透出的魂光（朱砂）
        crack = [(cx - 26 * k, cy - 100 * k), (cx - 6 * k, cy - 66 * k), (cx - 22 * k, cy - 40 * k), (cx + 4 * k, cy - 8 * k)]
        line(d, crack, 3.5 * k, CINNABAR + (235,), S)
        # 魂光：从蛋顶升起，弯向山顶
        soul = []
        for t in np.linspace(0, 1, 40):
            x = cx - 6 * k + np.sin(t * 7) * 16 * k * (1 - t) + (44 * k) * t ** 2
            y = cy - eh - 6 * k - (cy - eh - 6 * k - 168 * k) * t
            soul.append((x, y))
        for i in range(0, len(soul) - 1, 2):
            line(d, soul[i:i + 2], (3.4 - 2 * i / len(soul)) * k, CINNABAR + (int(230 - 120 * i / len(soul)),), S)
        # 祭坛石台和三根小柱
        base_y = cy + eh + 6 * k
        line(d, [(cx - 150 * k, base_y), (cx + 150 * k, base_y)], 4 * k, INK + (255,), S)
        line(d, [(cx - 120 * k, base_y + 14 * k), (cx + 120 * k, base_y + 14 * k)], 2.5 * k, INK + (170,), S)
        for px in (-175, 0, 175):
            if px == 0:
                continue
            x = cx + px * k
            d.rectangle([(x - 12 * k) * S, (base_y - 78 * k) * S, (x + 12 * k) * S, base_y * S], outline=INK + (230,), width=int(3 * k * S))
            d.polygon([((x - 9 * k) * S, (base_y - 86 * k) * S), (x * S, (base_y - 108 * k) * S), ((x + 9 * k) * S, (base_y - 86 * k) * S)], outline=CINNABAR + (220,))
    im = ss(draw, PW, PH, 2)
    d = ImageDraw.Draw(im)
    d.text((PW / 2, 80 * PS), '龙 魂 之 卵', font=f_t, fill=CINNABAR + (255,), anchor='mm')
    f2 = font(KAI, 25 * PS)
    d.text((PW / 2, PH - 112 * PS), '月辉 · 火种 · 星露', font=f2, fill=INK + (235,), anchor='mm')
    d.text((PW / 2, PH - 78 * PS), '魂归其身之日，即是结契之时', font=font(KAI, 21 * PS), fill=INK + (190,), anchor='mm')
    d.text((PW / 2, PH - 44 * PS), '· 六 ·', font=f_n, fill=INK + (170,), anchor='mm')
    return rough(im, 477)


pages = [ink_page(t, l, i) for i, (t, l) in enumerate(PAGES)] + [egg_page()]
for k in range(3):
    sheet = Image.new('RGBA', (PW * 2, PH), (0, 0, 0, 0))
    sheet.paste(pages[k * 2], (0, 0))
    sheet.paste(pages[k * 2 + 1], (PW, 0))
    tex_png(f'pages{k + 1}', sheet)

# =====================================================================
# 2. 地图：从当前存档的真实高度重画（含填平后的魔法阵），2048 像素
POI = json.load(open(f'{REPO}/docs/ui/poi.json'))
MS, MM = 6.4, 204            # 每米像素、四周留白；整图 256*6.4+408 = 2046 → 取 2048
MW = 2048


def draw_map():
    z = zipfile.ZipFile(f'{PROJ}/scene.data')
    hname = [n for n in z.namelist() if n.startswith('HeightMap_')][0]
    H = np.frombuffer(z.read(hname), '<f4').reshape(257, 257) * 256
    scene = json.loads(z.read('SerializePcgData.json'))
    rng = np.random.default_rng(7)
    W, S, M = MW, MS, MM
    L = int(256 * S)
    Hp = cv2.resize(np.flipud(H).astype(np.float32), (L, L), interpolation=cv2.INTER_CUBIC)
    land = (Hp > SEA).astype(np.uint8)
    land = cv2.morphologyEx(land, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    wp = lambda x, zz: (M + x * S, M + (256 - zz) * S)
    n_lo = cv2.resize(cv2.GaussianBlur(rng.normal(0, 1, (W // 8, W // 8)).astype(np.float32), (0, 0), 3), (W, W))
    fine = cv2.GaussianBlur(rng.normal(0, 1, (W, W)).astype(np.float32), (0, 0), 1.2)
    yy, xx = np.mgrid[0:W, 0:W] / W
    edge = np.clip(np.hypot(xx - .5, yy - .5) * 1.7, 0, 1) ** 3
    base = np.array([238, 226, 198], np.float32)
    dark = np.array([188, 160, 118], np.float32)
    t = np.clip(edge * .9 + n_lo * .06 + fine * .02, 0, 1)[..., None]
    paper = base * (1 - t) + dark * t
    img = Image.fromarray(np.clip(paper, 0, 255).astype(np.uint8)).convert('RGBA')
    full = np.ones((W, W), np.uint8)
    full[M:M + L, M:M + L] = land
    # 海：淡淡的蓝灰水色 + 岸边波纹
    sm = Image.fromarray(((1 - full) * 70).astype(np.uint8)).filter(ImageFilter.GaussianBlur(8))
    sea = Image.new('RGBA', (W, W), (96, 118, 124, 0)); sea.putalpha(sm)
    img = Image.alpha_composite(img, sea)
    # 陆地按高度淡淡分层设色（低地偏绿、山地偏褐、雪线以上留白），让图一眼能读
    hfull = np.full((W, W), 0, np.float32); hfull[M:M + L, M:M + L] = Hp
    a = np.array(img).astype(np.float32)
    lowland = np.clip((hfull - SEA) / 14, 0, 1) * np.clip((52 - hfull) / 10, 0, 1) * full
    upland = np.clip((hfull - 50) / 20, 0, 1) * np.clip((96 - hfull) / 18, 0, 1) * full
    snow = np.clip((hfull - 88) / 14, 0, 1) * full
    for mask, col, amt in ((lowland, (150, 168, 112), .34), (upland, (150, 122, 92), .30), (snow, (250, 248, 244), .65)):
        mk = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 6)[..., None] * amt
        a[..., :3] = a[..., :3] * (1 - mk) + np.array(col, np.float32) * mk
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)

    def bdist(pts):
        lo, hi = M, M + L
        return np.minimum.reduce([pts[:, 0] - lo, hi - pts[:, 0], pts[:, 1] - lo, hi - pts[:, 1]])

    def runs(pts, keep):
        out, cur = [], []
        for p_, k_ in zip(pts, keep):
            if k_:
                cur.append(tuple(p_))
            elif cur:
                out.append(cur); cur = []
        if cur:
            out.append(cur)
        return [r for r in out if len(r) > 6]

    dist = cv2.distanceTransform((1 - full).astype(np.uint8), cv2.DIST_L2, 5)
    for k, r in enumerate((9, 20, 33, 50)):
        ring = ((dist > r - 1) & (dist < r + 1)).astype(np.uint8) * 255
        cs, _ = cv2.findContours(ring, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for c in cs:
            if len(c) > 24:
                pts = c[::2, 0, :].astype(np.float32)
                for run in runs(pts, bdist(pts) > r + 5):
                    d.line(run, fill=(52, 60, 66, 130 - k * 26), width=2)
    cs, _ = cv2.findContours(full, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    for c in cs:
        if len(c) < 40:
            continue
        pts = c[:, 0, :].astype(np.float32)
        keep = bdist(pts) > 4
        pts += rng.normal(0, .7, pts.shape)
        for run in runs(pts[::2], keep[::2]):
            d.line(run, fill=INK, width=4)

    def mountain(x, y, s, a_=255):
        l, r, top = (x - s, y), (x + s, y), (x + s * .1, y - s * 1.25)
        d.line([l, top, r], fill=INK + (a_,), width=3)
        for i in range(1, 5):
            f_ = i / 5
            p = (top[0] + (r[0] - top[0]) * f_, top[1] + (r[1] - top[1]) * f_)
            d.line([p, (p[0] - s * .25, y)], fill=INK + (int(a_ * .6),), width=1)

    ys, xs = np.mgrid[0:256:4, 0:256:4]
    cand = []
    for z0, x0 in zip(ys.ravel(), xs.ravel()):
        h = H[min(z0, 256), min(x0, 256)]
        if h > 56:
            cand.append((h, x0 + rng.uniform(-1.5, 1.5), z0 + rng.uniform(-1.5, 1.5)))
    cand.sort(key=lambda c: -c[2])
    for h, x0, z0 in cand:
        if rng.random() < .55:
            continue
        u, v = wp(x0, z0)
        mountain(u, v, (6 + (h - 56) * .35) * S / 5, 230)
    for z0, x0 in zip(ys.ravel(), xs.ravel()):
        h = H[z0, x0]
        if 47 < h <= 56 and rng.random() < .35:
            u, v = wp(x0 + rng.uniform(-2, 2), z0 + rng.uniform(-2, 2))
            d.arc([u - 9, v - 6, u + 9, v + 6], 200, 340, fill=INK + (150,), width=2)
    nodes = scene['nodeTransformDatas']
    byid = {n['id']: n for n in nodes}
    for n in nodes:
        b = n['basic']
        nm = b['nodeName']
        if b['parentId'] == 0 and (nm.startswith('pl_tree') or nm.startswith('pl_bush')):
            u, v = wp(b['pos']['x'], b['pos']['z'])
            s = 5 if 'tree' in nm else 3
            d.ellipse([u - s, v - s * 1.4, u + s, v + s * .6], outline=(48, 66, 40, 215), width=2)
            d.line([(u, v + s * .6), (u, v + s * 1.6)], fill=(48, 66, 40, 215), width=2)
    # 麦田：一小撮一小撮的麦穗记号（存档 + 作者包里的全部麦簇）
    wheat = [(n['basic']['pos']['x'], n['basic']['pos']['z']) for n in nodes if n['basic']['nodeName'].startswith('golden_geometry') and byid[n['basic']['parentId']]['basic']['nodeName'] == 'WPrefab 实例']
    pf = json.load(open(f'{AUTHOR}/prefab.json'))
    wheat += [(n['basic']['pos']['x'], n['basic']['pos']['z']) for n in pf['nodeTransformDatas'] if n['basic']['nodeName'].startswith('golden_geometry')]
    for i, (x, zz) in enumerate(wheat):
        if i % 2:
            continue
        u, v = wp(x, zz)
        for k in (-4, 0, 4):
            d.line([(u + k, v + 5), (u + k * 1.4, v - 6)], fill=(150, 108, 34, 235), width=2)
    # 魔法阵：两圈 + 六芒
    u, v = wp(130.3, 19.4)
    r = 13.3 * S
    d.ellipse([u - r, v - r, u + r, v + r], outline=CINNABAR + (230,), width=3)
    d.ellipse([u - r * .8, v - r * .8, u + r * .8, v + r * .8], outline=CINNABAR + (150,), width=2)
    for k in range(2):
        pts = [(u + np.cos(np.pi * (i * 2 / 3 + k / 3) + np.pi / 2) * r * .8, v + np.sin(np.pi * (i * 2 / 3 + k / 3) + np.pi / 2) * r * .8) for i in range(4)]
        d.line(pts, fill=CINNABAR + (170,), width=2)
    # 纸边做旧
    paper_img = Image.fromarray(np.clip(paper, 0, 255).astype(np.uint8)).convert('RGBA')
    a = np.array(img).astype(np.float32)
    pp = np.array(paper_img).astype(np.float32)
    inside = np.zeros((W, W), np.uint8)
    inside[M + 8:W - M - 8, M + 8:W - M - 8] = 1
    dd = cv2.distanceTransform(inside, cv2.DIST_L2, 5)
    jit = cv2.resize(cv2.GaussianBlur(rng.normal(0, 1, (W // 16, W // 16)).astype(np.float32), (0, 0), 1.5), (W, W)) * 22
    kk = np.clip((dd + jit - 5) / 48, 0, 1)[..., None]
    img = Image.fromarray((a * kk + pp * (1 - kk)).astype(np.uint8))
    d = ImageDraw.Draw(img)
    # 地名
    f_big, f_sm, f_sea = font(SERIF, 44), font(SERIF, 35), font(KAI, 44)
    for p in POI:
        u, v = wp(p['x'], p['z'])
        big = p.get('major')
        r = 9 if big else 6
        d.ellipse([u - r, v - r, u + r, v + r], fill=CINNABAR if p.get('red') else INK)
        if big:
            d.ellipse([u - r - 5, v - r - 5, u + r + 5, v + r + 5], outline=INK, width=3)
        f_ = f_big if big else f_sm
        dx, dy = p.get('dx', 12) * S / 5, p.get('dy', -12) * S / 5
        d.text((u + dx, v + dy), p['name'], font=f_, fill=INK, stroke_width=5, stroke_fill=(236, 224, 196))
    for name, x, zz in [('蚀 月 海', 236, 200), ('雾 湾', 226, 44), ('西 境 荒 原', 20, 238)]:
        u, v = wp(x, zz)
        d.text((u, v), name, font=f_sea, fill=(60, 70, 76, 170), anchor='mm')
    # 罗盘
    cx, cy, R = M + 96, W - M - 70, 66
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=INK, width=3)
    d.ellipse([cx - R + 10, cy - R + 10, cx + R - 10, cy + R - 10], outline=INK + (110,), width=1)
    for ang, Lk in ((0, 1.25), (90, 1.0), (180, 1.0), (270, 1.0)):
        a_ = np.radians(ang)
        tip = (cx + np.sin(a_) * R * Lk, cy - np.cos(a_) * R * Lk)
        l = (cx + np.sin(a_ - 1.57) * 11, cy - np.cos(a_ - 1.57) * 11)
        r_ = (cx + np.sin(a_ + 1.57) * 11, cy - np.cos(a_ + 1.57) * 11)
        d.polygon([tip, l, (cx, cy)], fill=CINNABAR if ang == 0 else INK)
        d.polygon([tip, r_, (cx, cy)], outline=INK, fill=(236, 223, 196))
    d.text((cx, cy - R * 1.25 - 22), '北', font=font(SERIF, 34), fill=INK, anchor='mm')
    # 图名：右下角的题签（朱文印 + 隶意大字）
    tx, ty = W - M - 250, W - M - 66
    d.text((tx, ty), '龍 眠 之 境', font=font(SERIF, 76), fill=INK, anchor='mm', stroke_width=6, stroke_fill=(236, 224, 196))
    d.text((tx, ty + 62), '守 夜 人 行 旅 图', font=font(KAI, 30), fill=INK + (190,), anchor='mm')
    sx, sy = tx + 268, ty - 6
    d.rounded_rectangle([sx - 30, sy - 46, sx + 30, sy + 46], 6, fill=CINNABAR)
    d.text((sx, sy - 20), '墨', font=font(SERIF, 34), fill=(240, 226, 196), anchor='mm')
    d.text((sx, sy + 20), '曜', font=font(SERIF, 34), fill=(240, 226, 196), anchor='mm')
    # 撕边
    pa = np.array(parchment(W, W, 61, burn=True, edge=1.6)).astype(np.float32)
    m = np.array(img.convert('RGB')).astype(np.float32)
    burn = pa[..., :3] / np.array([234, 220, 191], np.float32)
    m = np.clip(m * np.clip(burn, .4, 1.04), 0, 255)
    al = pa[..., 3:4] / 255                      # 撕边外面压成和遮罩一样的近黑，整图存成 JPG
    m = m * al + np.array([6, 4, 8], np.float32) * (1 - al)
    return Image.fromarray(m.astype(np.uint8))


# 新增三个地点
NEW_POI = [
    dict(id='stable', name='马厩', x=146, z=46.5, dx=14, dy=-34),
    dict(id='wheat', name='金穗麦田', x=138, z=36, dx=14, dy=-2),
    dict(id='trial', name='影灵试炼', x=130.3, z=19.4, red=True, dx=-60, dy=74),
]
have = {p['id'] for p in POI}
POI += [p for p in NEW_POI if p['id'] not in have]
map_img = draw_map()
tex_jpg('map', map_img, 80)
map_img.resize((1024, 1024)).save(f'{OUT}/png/map_preview.jpg', quality=85)

# =====================================================================
# 3. 地点介绍卡
DESC = {
    'spawn': '时之晷立在这里，它是封印的钟。指针走进夜里，封印就松一分。你在这里醒来。',
    'castle': '守夜人的城堡，如今空了。书库里还留着他们的手稿，王座厅后面是龙巢圣所。',
    'dragon_peak': '墨曜的龙身盘在这座雪峰上。魂不归位，它不会睁眼。',
    'altar': '龙魂之卵封存在这里。献上月辉、火种与星露，龙魂就会醒来；结契之后，墨曜也在这里降落。',
    'rift_gate': '城堡脚下的古传送门。门里的漩涡通向地下试炼场。',
    'arena': '守夜人切磋的地方。两个人穿过裂隙之门，就能在这里对决，点到为止。',
    'village': '夜里最亮的地方。灯火彻夜不熄，影灵从不进村。',
    'witch': '女巫什么都肯卖，只是不保证效果。变大、变小、变成羊……都有可能。',
    'camp': '篝火彻夜不灭。看准火候把蘑菇烤熟，能得到火种；烤生了吃下去，会天旋地转。',
    'mushroom': '会发光的蘑菇林，女巫最爱的材料都长在这里。',
    'windmill': '风车慢慢转。白天看风景最好的一面坡。',
    'meadow': '羊群在这里吃草。喝了女巫的药变成羊，可以混进去。',
    'flowers': '一片紫色的花海，星露的主料就长在这里。',
    'glow_tree': '据说是墨曜第一次落地的地方，树上的光至今未散。想换一条誓约，就来这里。',
    'bridge': '跨过河谷、通往城堡的石桥。月圆时桥面会泛光。',
    'lake': '夜里，湖面上能看见蚀月之隙的倒影。',
    'lighthouse': '海边最后一盏灯，替出海的人守着归路。',
    'harbor': '帆船停在这里，靠近就能登船出海。',
    'carpet': '飞毯从这里起飞，带你看看整片土地。',
    'stable': '守夜人的马厩。马儿认生，但肯驮你走上一段。',
    'wheat': '入秋的麦田，风一过就是一片金浪。麦田南边的空地，入夜会亮起魔法阵。',
    'trial': '只在夜里亮起的魔法阵。走进去，影灵就会应战；把它们打散，能拾到月辉。',
}
CW, CH = 640, 256
f_cn, f_cd = font(SERIF, 44), font(KAI, 30)
CARD_COLS = 3
cards_sheet = Image.new('RGBA', (CW * CARD_COLS, CH * int(np.ceil(len(POI) / CARD_COLS))), (0, 0, 0, 0))
CARDS = {}
for i, p in enumerate(POI):
    c = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.text((44, 30), p['name'], font=f_cn, fill=CINNABAR + (255,))
    nw = text_w(f_cn, p['name'])
    d.line([(44 + nw + 20, 60), (CW - 44, 60)], fill=INK + (110,), width=2)
    y = 100
    for ln in wrap(DESC[p['id']], f_cd, CW - 92)[:3]:
        d.text((44, y), ln, font=f_cd, fill=INK + (255,))
        y += 44
    col, row = i % CARD_COLS, i // CARD_COLS
    cards_sheet.paste(c, (col * CW, row * CH))
    CARDS[p['id']] = [col * CW, row * CH, CW, CH]
tex_png('cards', cards_sheet)
AT.add('card_bg', parchment(CW, CH, 700, burn=True))

# =====================================================================
# 4. 手稿与碑文（8 篇，透明底墨字，每篇 560×720）
LORE = [
    ('守夜人手记 · 灯', '书库 · 西墙书架', ['入秋第三夜。', '裂隙又宽了一指。', '', '老队长说，影灵怕的不是火，', '是有人醒着。', '', '所以灯不必多亮，', '但不能灭。', '', '我把这句话抄在这里，', '免得轮到我带新人的时候，', '忘了。']),
    ('守夜人手记 · 龙', '书库 · 西墙书架', ['都说墨曜睡在山上。', '其实只有身子在那儿。', '', '它把魂摘下来，封进一枚蛋，', '托我们的祖辈放在西边的祭坛。', '', '身在山巅，压住裂隙；', '魂在蛋里，等一个人。', '', '身与魂重逢的那天，', '这场长梦才算做完。']),
    ('一封没写完的信', '书库 · 烛台下', ['阿絮：', '见字如面。', '', '今年的麦子熟得早。', '麦田南边那块洼地，夜里会亮，', '别去。那是影灵踩出来的阵。', '', '若我没回来，', '灯在门后，油是满的。', '', '替我去祭坛看看那枚蛋，', '它最近夜里……']),
    ('篝 火 谣', '守夜人营地 · 石碑', ['', '生菇三分苦，', '熟菇七分香。', '', '火候差一息，', '天地转三圈。', '', '守夜莫贪睡，', '贪睡莫守夜。', '', '留得火种在，', '不怕夜漫长。']),
    ('其一 · 月辉', '唤龙祭坛 · 南柱铭文', ['', '', '影散为辉，', '辉本龙梦。', '', '拾梦三十，', '还于其主。', '', '', '#月辉 · 三十']),
    ('其二 · 火种', '唤龙祭坛 · 东柱铭文', ['', '', '火不在柴，', '在守火的人。', '', '三枚既足，', '可暖龙魂。', '', '', '#火种 · 三枚']),
    ('其三 · 星露', '唤龙祭坛 · 西柱铭文', ['', '', '菇三花三，', '羊毛一缕。', '', '女巫之釜，', '滴露成星。', '', '', '#星露 · 一滴']),
    ('龙 契', '龙巢圣所 · 契碑', ['', '魂归其身，', '身载其骑。', '', '一人一龙，', '同梦同醒。', '', '后来的人：', '若你读到这里，', '说明灯还亮着。']),
]
LW, LH = 560, 720
lore_sheet = Image.new('RGBA', (LW * 4, LH * 2), (0, 0, 0, 0))
f_lt, f_ls, f_lb = font(SERIF, 44), font(KAI, 24), font(KAI, 31)
for i, (title, where, lines) in enumerate(LORE):
    im = Image.new('RGBA', (LW, LH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((LW / 2, 62), title, font=f_lt, fill=CINNABAR + (255,), anchor='mm')
    d.line([(LW / 2 - 110, 104), (LW / 2 + 110, 104)], fill=INK + (170,), width=2)
    d.text((LW / 2, 130), where, font=f_ls, fill=INK + (170,), anchor='mm')
    poem = i >= 3
    y = 176
    for ln in lines:
        if ln == '':
            y += 18
            continue
        red = ln.startswith('#')
        t = ln[1:] if red else ln
        if poem:
            d.text((LW / 2, y), t, font=font(KAI, 36) if not red else font(SERIF, 30), fill=(CINNABAR if red else INK) + (255,), anchor='ma')
            y += 50
        else:
            d.text((54, y), t, font=f_lb, fill=INK + (255,))
            y += 43
    lore_sheet.paste(rough(im, 800 + i), ((i % 4) * LW, (i // 4) * LH))
tex_png('lore', lore_sheet)

# =====================================================================
# 5. 漩涡（传送门中心 + 眩晕叠层共用），512 方图，黑底加色混合也能用，带透明
def vortex():
    n = 512
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    dx, dy = (xx - n / 2) / (n / 2), (yy - n / 2) / (n / 2)
    r = np.hypot(dx, dy)
    th = np.arctan2(dy, dx)
    arms = np.zeros((n, n), np.float32)
    for k, (cnt, tw, amp) in enumerate(((3, 5.5, 1.0), (5, 8.0, .55), (9, 12.0, .3))):
        arms += amp * (np.cos(cnt * th + tw * np.log(r + .04) * 1.6 + k) * .5 + .5) ** (3 + k)
    arms /= arms.max()
    fall = np.clip(1 - r, 0, 1) ** .9 * np.clip(r / .08, 0, 1)
    core = np.exp(-(r / .16) ** 2)
    a = np.clip(arms * fall * 1.25 + core * .9, 0, 1) * np.clip((1 - r) / .08, 0, 1)
    c1 = np.array([120, 70, 255], np.float32)
    c2 = np.array([90, 220, 255], np.float32)
    c3 = np.array([255, 245, 255], np.float32)
    t = np.clip(arms * .8 + (1 - r) * .2, 0, 1)[..., None]
    rgb = c1 * (1 - t) + c2 * t
    rgb = rgb * (1 - core[..., None]) + c3 * core[..., None]
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8))


tex_png('vortex', vortex())


def sigil():
    """夜里铺在平地上的魔法阵：双环、六芒、符文刻度，带一圈辉光。"""
    n, S = 1024, 2
    im = Image.new('L', (n * S, n * S), 0)
    d = ImageDraw.Draw(im)
    c = n * S / 2
    R = n * S * .47
    def circ(r, w):
        d.ellipse([c - r, c - r, c + r, c + r], outline=255, width=int(w * S))
    circ(R, 7); circ(R * .94, 3); circ(R * .70, 4); circ(R * .34, 3); circ(R * .28, 2)
    for k in range(2):
        pts = [(c + np.cos(np.pi * (i * 2 / 3 + k / 3) + np.pi / 2) * R * .70, c + np.sin(np.pi * (i * 2 / 3 + k / 3) + np.pi / 2) * R * .70) for i in range(4)]
        d.line(pts, fill=255, width=5 * S, joint='curve')
    for i in range(6):
        a = np.pi * i / 3 + np.pi / 2
        x, y = c + np.cos(a) * R * .70, c + np.sin(a) * R * .70
        r = R * .055
        d.ellipse([x - r, y - r, x + r, y + r], outline=255, width=3 * S, fill=0)
        d.line([(c + np.cos(a + np.pi / 6) * R * .34, c + np.sin(a + np.pi / 6) * R * .34), (c + np.cos(a + np.pi / 6) * R * .60, c + np.sin(a + np.pi / 6) * R * .60)], fill=255, width=2 * S)
    rr = np.random.default_rng(4)
    for i in range(36):                       # 环带里的符文：每格几笔随机短划
        a = 2 * np.pi * i / 36
        ux, uy = np.cos(a), np.sin(a)
        vx, vy = -uy, ux
        bx, by = c + ux * R * .82, c + uy * R * .82
        pts = [(bx + ux * rr.uniform(-.045, .045) * R + vx * rr.uniform(-.028, .028) * R, by + uy * rr.uniform(-.045, .045) * R + vy * rr.uniform(-.028, .028) * R) for _ in range(4)]
        d.line(pts, fill=255, width=3 * S, joint='curve')
        if i % 3 == 0:
            d.line([(c + ux * R * .94, c + uy * R * .94), (c + ux * R, c + uy * R)], fill=255, width=3 * S)
    m = np.array(im.resize((n, n), Image.LANCZOS)).astype(np.float32) / 255
    glow = cv2.GaussianBlur(m, (0, 0), 9) * 1.5 + cv2.GaussianBlur(m, (0, 0), 3) * .8
    a = np.clip(m + glow * .7, 0, 1)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    t = np.clip(np.hypot(xx - n / 2, yy - n / 2) / (n / 2), 0, 1)[..., None]
    rgb = np.array([150, 110, 255], np.float32) * (1 - t) + np.array([90, 200, 255], np.float32) * t
    rgb = rgb * (1 - m[..., None] * .55) + 255 * m[..., None] * .55
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a * 255]).astype(np.uint8))


tex_png('sigil', sigil())

# =====================================================================
# 6. 图集里的小图
def wax_seal(size, text=None, seed=1, color=(150, 36, 26), text_color=(246, 226, 196), fnt=SERIF, tscale=.5, ring=True):
    S = 3
    n = size * S
    im = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = np.random.default_rng(seed)
    ph = r.uniform(0, 6, 4)
    pts = [(n / 2 + np.cos(a) * n * (.455 + .022 * np.sin(a * 7 + ph[0]) + .015 * np.sin(a * 3 + ph[1])),
            n / 2 + np.sin(a) * n * (.455 + .022 * np.cos(a * 5 + ph[2]) + .015 * np.sin(a * 2 + ph[3]))) for a in np.linspace(0, 2 * np.pi, 90)]
    d.polygon([(x + n * .012, y + n * .02) for x, y in pts], fill=(20, 8, 6, 120))
    d.polygon(pts, fill=color + (255,))
    hi = tuple(min(255, int(c * 1.32 + 20)) for c in color)
    lo = tuple(int(c * .68) for c in color)
    if ring:
        d.ellipse([n * .16, n * .16, n * .84, n * .84], outline=lo + (255,), width=int(n * .022))
        d.arc([n * .13, n * .13, n * .87, n * .87], 200, 300, fill=hi + (200,), width=int(n * .018))
    if text:
        f_ = font(fnt, n * tscale)
        d.text((n / 2 + n * .008, n / 2 + n * .012), text, font=f_, fill=lo + (255,), anchor='mm')
        d.text((n / 2, n / 2 - n * .004), text, font=f_, fill=text_color + (255,), anchor='mm')
    return im.resize((size, size), Image.LANCZOS)


def shadowed(img, blur=6, off=(0, 4), alpha=150, pad=12):
    w, h = img.size
    out = Image.new('RGBA', (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    sh = Image.new('RGBA', out.size, (0, 0, 0, 0))
    a = img.getchannel('A').point(lambda v: v * alpha // 255)
    sh.paste((8, 5, 4), (pad + off[0], pad + off[1]), a)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    out = Image.alpha_composite(out, sh)
    out.paste(img, (pad, pad), img)
    return out


# ---- HUD 按钮：任务（摊开的书 + 羽毛笔）、唤龙（龙印）
def btn_quest():
    ic = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    cover = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(cover)
    d.rounded_rectangle([24, 62, 232, 214], 12, fill=(52, 40, 33, 255), outline=(26, 18, 14, 255), width=3)
    d.rounded_rectangle([32, 70, 224, 206], 8, outline=(110, 86, 58, 255), width=2)
    ic = Image.alpha_composite(ic, cover)
    for x0, seed in ((34, 31), (129, 32)):
        pg = parchment(93, 128, seed, burn=True, edge=.5)
        ic.paste(pg, (x0, 72), pg)
    d = ImageDraw.Draw(ic)
    d.line([(128, 74), (128, 200)], fill=(60, 44, 30, 255), width=4)
    for k in range(5):
        y = 96 + k * 19
        d.line([(48, y), (112 - (k % 2) * 14, y)], fill=INK + (190,), width=3)
        d.line([(144, y), (208 - ((k + 1) % 2) * 18, y)], fill=INK + (190,), width=3)
    d.polygon([(118, 186), (138, 186), (138, 240), (128, 228), (118, 240)], fill=CINNABAR + (255,), outline=(90, 20, 14, 255))
    # 羽毛笔
    q = ss(lambda dd, S: (dd.polygon([(196 * S, 20 * S), (236 * S, 38 * S), (176 * S, 150 * S), (162 * S, 142 * S)], fill=(238, 228, 206, 255), outline=INK + (255,)),
                          dd.line([(228 * S, 30 * S), (150 * S, 176 * S)], fill=INK + (255,), width=3 * S),
                          [dd.line([((214 - k * 7) * S, (40 + k * 14) * S), ((196 - k * 7) * S, (48 + k * 15) * S)], fill=INK + (150,), width=S) for k in range(6)]), 256, 256)
    ic = Image.alpha_composite(ic, q)
    return ic


def btn_dragon():
    ic = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    seal = wax_seal(224, '龍', seed=5, color=(126, 30, 24), tscale=.5)
    ic.paste(seal, (16, 16), seal)
    return ic


AT.add('btn_quest', shadowed(btn_quest(), pad=0))
AT.add('btn_dragon', shadowed(btn_dragon(), pad=0))
AT.add('btn_x', shadowed(wax_seal(112, '×', seed=9, fnt=HEAVY, tscale=.62), pad=8))

# ---- 白字小标签（暗背景上用）
fw = font(KAI, 30)
for key, s in (('lbl_map', '地图'), ('lbl_quest', '誓约'), ('lbl_dragon', '唤龙'), ('lbl_summoning', '龙正飞来'), ('lbl_ride', '骑上墨曜')):
    AT.add(key, label(s, fw, (246, 238, 220), shadow=(0, 0, 0, 190), stroke=2, stroke_fill=(20, 14, 10)))

# ---- 数字（白、墨两套）
for tag, col, st in (('w', (250, 244, 228), (20, 14, 10)), ('i', INK, None)):
    for ch, nm in list(zip('0123456789', '0123456789')) + [('/', 'slash'), (':', 'colon'), ('米', 'm')]:
        f_ = font(SERIF if ch != '米' else KAI, 34)
        im = Image.new('RGBA', (34 if ch == '米' else 24, 46), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.text((im.size[0] / 2, 24), ch, font=f_, fill=col + (255,), anchor='mm', stroke_width=2 if st else 0, stroke_fill=st)
        AT.add(f'd{tag}_{nm}', im)

# ---- 任务追踪条
OBJ_SHORT = ['在古书上签下誓约', '集齐材料 · 找女巫调制星露', '把蘑菇烤熟 · 攒三枚火种', '入夜迎战影灵 · 攒三十月辉', '带三样供品去唤龙祭坛', '回祭坛 · 见证龙魂苏醒', '点左侧龙印 · 唤墨曜降临']
OBJ_LONG = [
    ('在古书上签下职业誓约。', '去处 · 出生地的古书'),
    ('白天采集蘑菇三份、月见花三份、羊毛一份，交给女巫调制星露。', '去处 · 女巫药铺'),
    ('在营地的篝火上把蘑菇烤熟，攒够三枚火种。', '去处 · 守夜人营地'),
    ('入夜后走进麦田南边的魔法阵，打散影灵，攒够三十月辉。', '去处 · 影灵试炼'),
    ('月辉、火种、星露都齐了。把它们献给祭坛上的龙魂之卵。', '去处 · 唤龙祭坛'),
    ('供品已满。回到祭坛，见证龙魂苏醒。', '去处 · 唤龙祭坛'),
    ('龙契已成。点屏幕左侧的龙印，墨曜会从雪山飞到祭坛。', '去处 · 唤龙祭坛'),
]
f_o = font(KAI, 28)
for i, s in enumerate(OBJ_SHORT):
    AT.add(f'obj_{i + 1}', label(s, f_o, (250, 244, 228), shadow=(0, 0, 0, 200), stroke=2, stroke_fill=(20, 14, 10)))
trk = Image.new('RGBA', (520, 92), (0, 0, 0, 0))
ta = np.zeros((92, 520, 4), np.float32)
gx = np.linspace(0, 1, 520)[None, :]
ta[..., :3] = np.array([18, 13, 22], np.float32)
ta[..., 3] = 190 * np.clip((1 - gx) * 2.4, 0, 1) ** .8
trk = Image.fromarray(ta.astype(np.uint8))
d = ImageDraw.Draw(trk)
d.line([(0, 2), (300, 2)], fill=GOLD + (200,), width=2)
d.line([(0, 89), (220, 89)], fill=GOLD + (120,), width=2)
d.polygon([(0, 0), (8, 0), (8, 92), (0, 92)], fill=CINNABAR + (255,))
AT.add('trk_bg', trk)
AT.add('trk_head', label('当前誓约', font(KAI, 22), GOLD, shadow=(0, 0, 0, 200)))
ptr = ss(lambda dd, S: (dd.polygon([(32 * S, 4 * S), (56 * S, 56 * S), (32 * S, 44 * S), (8 * S, 56 * S)], fill=GOLD + (255,), outline=(60, 40, 14, 255)),
                        dd.polygon([(32 * S, 16 * S), (46 * S, 48 * S), (32 * S, 40 * S)], fill=(240, 214, 150, 255))), 64, 64)
AT.add('ptr', ptr)

# ---- 探访提示条 + 地点名字（白字）
tb = parchment(640, 104, 950, burn=True, edge=.6)
AT.add('toast_bg', shadowed(tb, pad=10))
AT.add('toast_new', label('探访新地点', font(KAI, 26), CINNABAR))
AT.add('toast_all', label('全境踏遍 · 行者之名', font(SERIF, 40), CINNABAR))
AT.add('toast_lore', label('新的文字已抄入誓约之书', font(KAI, 28), INK))
for p in POI:
    AT.add(f"nm_{p['id']}", label(p['name'], font(SERIF, 40), INK))

# ---- 地图上的记号
def stamp():
    def draw(d, S):
        d.ellipse([6 * S, 6 * S, 66 * S, 66 * S], outline=CINNABAR + (235,), width=5 * S)
        line(d, [(20, 37), (32, 49), (52, 24)], 7, CINNABAR + (245,), S)
    return rough(ss(draw, 72, 72), 31, .3)


AT.add('stamp', stamp())
ring = ss(lambda dd, S: [dd.ellipse([(64 - r) * S, (64 - r) * S, (64 + r) * S, (64 + r) * S], outline=CINNABAR + (a_,), width=4 * S) for r, a_ in ((50, 70), (44, 190), (40, 90))], 128, 128)
AT.add('ring', ring)
arrow = ss(lambda dd, S: (dd.polygon([(64 * S, 8 * S), (104 * S, 112 * S), (64 * S, 88 * S), (24 * S, 112 * S)], fill=CINNABAR + (255,), outline=(60, 12, 8, 255)),
                          dd.polygon([(64 * S, 30 * S), (88 * S, 96 * S), (64 * S, 82 * S)], fill=(196, 70, 50, 255))), 128, 128)
AT.add('arrow', arrow)
flag = ss(lambda dd, S: (dd.line([(20 * S, 8 * S), (20 * S, 60 * S)], fill=INK + (255,), width=4 * S),
                         dd.polygon([(22 * S, 10 * S), (58 * S, 20 * S), (22 * S, 34 * S)], fill=CINNABAR + (255,), outline=(70, 14, 10, 255)),
                         dd.ellipse([13 * S, 54 * S, 27 * S, 62 * S], fill=INK + (220,))), 64, 64)
AT.add('flag', flag)


def sun():
    def draw(d, S):
        d.ellipse([22 * S, 22 * S, 58 * S, 58 * S], outline=INK + (255,), width=4 * S, fill=(214, 160, 60, 255))
        for k in range(8):
            a = k * np.pi / 4
            line(d, [(40 + np.cos(a) * 24, 40 + np.sin(a) * 24), (40 + np.cos(a) * 34, 40 + np.sin(a) * 34)], 4, INK + (255,), S)
    return ss(draw, 80, 80)


def moon():
    def draw(d, S):
        d.ellipse([14 * S, 12 * S, 66 * S, 64 * S], fill=(230, 220, 180, 255), outline=INK + (255,), width=4 * S)
        d.ellipse([30 * S, 6 * S, 78 * S, 54 * S], fill=(0, 0, 0, 0))
        d.arc([30 * S, 6 * S, 78 * S, 54 * S], 110, 232, fill=INK + (255,), width=4 * S)
    im = ss(draw, 80, 80)
    return im


AT.add('ic_sun', sun())
AT.add('ic_moon', moon())
f_m = font(KAI, 34)
AT.add('lbl_day', label('白 昼', f_m, INK))
AT.add('lbl_night', label('夜 幕', f_m, INK))
AT.add('lbl_visit', label('已探访', f_m, INK))
AT.add('lbl_lore', label('手稿碑文', f_m, INK))
AT.add('clock_bg', shadowed(parchment(330, 150, 951, burn=True, edge=.6), pad=8))
AT.add('prog_bg', shadowed(parchment(330, 150, 952, burn=True, edge=.6), pad=8))
AT.add('seal_all', rough(wax_seal(200, '行者', seed=12, tscale=.36), 55, .2))
hint = label('点 地 名 看 介 绍 · 走 到 地 方 自 动 盖 印', font(KAI, 30), (240, 232, 214), shadow=(0, 0, 0, 180))
AT.add('hint_map', hint)
AT.add('hint_flip', label('轻 触 翻 页', font(KAI, 32), (240, 232, 214), shadow=(0, 0, 0, 180)))
AT.add('hint_read', label('轻 触 任 意 处 合 上', font(KAI, 28), (240, 232, 214), shadow=(0, 0, 0, 180)))

# ---- 职业选择
def banner_card(kind, name, sub, seed):
    w, h = 300, 440
    pg = np.array(parchment(w, h, seed, burn=True, edge=.7))
    yy, xx = np.mgrid[0:h, 0:w]
    notch = (yy > h - 46) & (np.abs(xx - w / 2) < (yy - (h - 46)) * 1.0)       # 底部燕尾
    pg[..., 3] = np.where(notch, 0, pg[..., 3])
    im = Image.fromarray(pg)

    def draw(d, S):
        d.rounded_rectangle([14 * S, 14 * S, (w - 14) * S, (h - 58) * S], 10 * S, outline=CINNABAR + (220,), width=4 * S)
        d.rounded_rectangle([24 * S, 24 * S, (w - 24) * S, (h - 68) * S], 6 * S, outline=INK + (120,), width=2 * S)
        cx, cy = w / 2, 172
        ink, red = INK + (255,), CINNABAR + (255,)
        d.ellipse([(cx - 92) * S, (cy - 92) * S, (cx + 92) * S, (cy + 92) * S], outline=INK + (90,), width=2 * S)
        if kind == 'melee':
            d.polygon([(cx * S, (cy - 104) * S), ((cx + 13) * S, (cy - 80) * S), ((cx + 10) * S, (cy + 40) * S), ((cx - 10) * S, (cy + 40) * S), ((cx - 13) * S, (cy - 80) * S)], fill=(238, 228, 206, 255), outline=ink)
            line(d, [(cx, cy - 96), (cx, cy + 36)], 2.5, INK + (150,), S)
            line(d, [(cx - 44, cy + 44), (cx + 44, cy + 44)], 10, red, S)
            line(d, [(cx - 44, cy + 44), (cx - 52, cy + 32)], 6, red, S)
            line(d, [(cx + 44, cy + 44), (cx + 52, cy + 32)], 6, red, S)
            line(d, [(cx, cy + 50), (cx, cy + 86)], 9, ink, S)
            d.ellipse([(cx - 11) * S, (cy + 84) * S, (cx + 11) * S, (cy + 106) * S], fill=red, outline=ink)
            # 身后的盾
            pts = [(cx - 70, cy - 40), (cx - 34, cy - 54), (cx - 34, cy + 12), (cx - 52, cy + 40), (cx - 70, cy + 12)]
            line(d, pts + [pts[0]], 3, INK + (170,), S)
            pts = [(cx + 70, cy - 40), (cx + 34, cy - 54), (cx + 34, cy + 12), (cx + 52, cy + 40), (cx + 70, cy + 12)]
            line(d, pts + [pts[0]], 3, INK + (170,), S)
        elif kind == 'mage':
            line(d, [(cx - 34, cy + 104), (cx + 14, cy - 44)], 8, ink, S)
            d.arc([(cx - 22) * S, (cy - 112) * S, (cx + 62) * S, (cy - 28) * S], 120, 400, fill=ink, width=7 * S)
            star = [(cx + 20 + np.cos(a) * (26 if i % 2 == 0 else 10), cy - 70 + np.sin(a) * (26 if i % 2 == 0 else 10)) for i, a in enumerate(np.linspace(-np.pi / 2, 1.5 * np.pi, 9))]
            d.polygon([(x * S, y * S) for x, y in star], fill=red, outline=ink)
            for sx, sy, sr in ((-58, -62, 9), (70, 6, 7), (-66, 28, 6), (54, 66, 8), (-30, -96, 5)):
                st = [(cx + sx + np.cos(a) * (sr if i % 2 == 0 else sr * .4), cy + sy + np.sin(a) * (sr if i % 2 == 0 else sr * .4)) for i, a in enumerate(np.linspace(-np.pi / 2, 1.5 * np.pi, 9))]
                d.polygon([(x * S, y * S) for x, y in st], fill=INK + (200,))
        else:
            d.arc([(cx - 150) * S, (cy - 100) * S, (cx + 50) * S, (cy + 100) * S], -62, 62, fill=ink, width=9 * S)
            a1, a2 = np.radians(-62), np.radians(62)
            p1 = (cx - 50 + np.cos(a1) * 100, cy + np.sin(a1) * 100)
            p2 = (cx - 50 + np.cos(a2) * 100, cy + np.sin(a2) * 100)
            line(d, [p1, (cx - 30, cy), p2], 2.5, INK + (200,), S)
            line(d, [(cx - 76, cy), (cx + 84, cy)], 5, red, S)
            d.polygon([((cx + 100) * S, cy * S), ((cx + 76) * S, (cy - 12) * S), ((cx + 76) * S, (cy + 12) * S)], fill=red, outline=ink)
            for k in range(3):
                line(d, [(cx - 70 + k * 9, cy), (cx - 84 + k * 9, cy - 12)], 3, red, S)
                line(d, [(cx - 70 + k * 9, cy), (cx - 84 + k * 9, cy + 12)], 3, red, S)
            for lx, ly in ((-70, -84), (64, -70), (72, 72)):       # 风里的叶
                d.arc([(cx + lx - 14) * S, (cy + ly - 8) * S, (cx + lx + 14) * S, (cy + ly + 8) * S], 180, 360, fill=INK + (160,), width=3 * S)
    im = Image.alpha_composite(im, ss(draw, w, h))
    d = ImageDraw.Draw(im)
    d.text((w / 2, 312), name, font=font(SERIF, 50), fill=CINNABAR + (255,), anchor='mm')
    d.text((w / 2, 358), sub, font=font(KAI, 24), fill=INK + (220,), anchor='mm')
    return im


CLASSES = [
    ('melee', '骑 士', '剑誓 · 近战', '剑誓 · 骑士', '身披铠甲，直面暗夜。以利刃驱散影灵，以护盾守住同伴。', '近战 · 心火六点',
     [('shield', '破晓守护', '震退身边的影灵，三秒不受伤'), ('spin', '回旋斩', '横扫四周'), ('judgement', '巨剑裁决', '蓄力重斩，伤害最高')]),
    ('mage', '法 师', '星誓 · 远程', '星誓 · 法师', '将散落的星火聚于掌心。用法杖唤醒魔力，让群星划破黑夜。', '远程 · 心火五点',
     [('nova', '星火爆裂', '在远处炸开一片星火'), ('frost', '霜星禁锢', '把影灵冻在原地两秒'), ('meteor', '陨星裁决', '召一颗陨星砸下')]),
    ('ranged', '游 侠', '风誓 · 远程', '风誓 · 游侠', '披林间的风，循月色而行。拉弓追逐游影，让箭羽回应誓言。', '远程 · 心火五点',
     [('volley', '月羽连射', '一口气连发五箭'), ('pierce', '贯晶箭', '一箭穿透一整排'), ('rain', '万箭齐下', '箭雨覆盖一片地面')]),
]
BT = Atlas()        # 第二张图集放书页类的大图，这里先收集到同一个 AT，由打包器自动分张


def glow_frame(w, h):
    im = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([14, 14, w + 26, h - 18], 18, outline=(255, 214, 120, 255), width=8)
    g = im.filter(ImageFilter.GaussianBlur(9))
    out = Image.alpha_composite(g, g)
    d = ImageDraw.Draw(out)
    d.rounded_rectangle([17, 17, w + 23, h - 21], 16, outline=(255, 236, 170, 255), width=3)
    return out


# 技能图标：沿用战斗脚本里的线稿形状，放大重画
def lua_shapes():
    src = open(f'{AUTHOR}/scripts/dragon_rpg.lua', encoding='utf8').read()
    out = {}
    for m in re.finditer(r'(?:shapes\.|^\s*)(\w+)=\{(\{[\d,{} ]+\})\}', src, re.M):
        segs = re.findall(r'\{(\d+),(\d+),(\d+),(\d+)\}', m.group(2))
        if segs:
            out[m.group(1)] = [tuple(map(int, s)) for s in segs]
    return out


SHAPES = lua_shapes()
# 另补两个：交叉双剑（进入战斗）、法杖（法师普攻）
SHAPES['duel'] = [(12, 52, 46, 14), (46, 14, 52, 12), (52, 12, 50, 18), (50, 18, 16, 56), (52, 52, 18, 14), (18, 14, 12, 12), (12, 12, 14, 18), (14, 18, 48, 56), (8, 44, 20, 56), (56, 44, 44, 56)]
SHAPES['staff'] = [(14, 56, 40, 22), (40, 22, 34, 12), (34, 12, 44, 6), (44, 6, 54, 12), (54, 12, 50, 24), (50, 24, 40, 22), (44, 12, 44, 18), (41, 15, 47, 15)]


def icon(key, size=128, color=CREAM, width=4.4, glow=True):
    segs = SHAPES.get(key) or SHAPES['sword']
    k = size / 64

    def draw(d, S):
        for x0, y0, x1, y1 in segs:
            line(d, [(x0 * k, y0 * k), (x1 * k, y1 * k)], width * k / 2, color + (255,), S)
    im = ss(draw, size, size)
    if glow:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        sh.paste((10, 6, 14), (0, int(3 * k / 2)), im.getchannel('A'))
        sh = sh.filter(ImageFilter.GaussianBlur(2.2 * k / 2))
        im = Image.alpha_composite(sh, im)
    return im


def ink_icon(key, size=56):
    return icon(key, size, INK, 4.6, glow=False)


for kind, name, sub, title, flavor, role, skills in CLASSES:
    AT.add(f'card_{kind}', banner_card(kind, name, sub, {'melee': 41, 'mage': 42, 'ranged': 43}[kind]))
    w, h = 500, 560
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((w / 2, 40), title, font=font(SERIF, 46), fill=CINNABAR + (255,), anchor='mm')
    d.line([(w / 2 - 120, 78), (w / 2 + 120, 78)], fill=INK + (170,), width=2)
    y = 104
    for ln in wrap(flavor, font(KAI, 29), w - 40):
        d.text((20, y), ln, font=font(KAI, 29), fill=INK + (255,))
        y += 42
    y += 8
    d.text((20, y), role, font=font(KAI, 25), fill=CINNABAR + (235,))
    y += 54
    for ik, sn, sd in skills:
        ic = ink_icon(ik, 60)
        d.ellipse([20, y, 84, y + 64], outline=INK + (200,), width=3)
        im.paste(ic, (22, y + 2), ic)
        d.text((100, y + 2), sn, font=font(SERIF, 28), fill=INK + (255,))
        d.text((100, y + 36), sd, font=font(KAI, 22), fill=INK + (200,))
        y += 82
    AT.add(f'cls_{kind}', rough(im, 60, .12))
AT.add('card_glow', glow_frame(300, 440))
im = Image.new('RGBA', (520, 124), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.text((260, 40), '守 夜 人 誓 约', font=font(SERIF, 52), fill=CINNABAR + (255,), anchor='mm')
d.text((260, 98), '择一条道路，守护龙的长梦', font=font(KAI, 27), fill=INK + (230,), anchor='mm')
AT.add('cls_title', im)
im = Image.new('RGBA', (500, 420), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
for i, ln in enumerate(['三条道路，', '同一个誓言。', '', '在左页选定职业，', '再在这里按下火漆。']):
    d.text((250, 60 + i * 56), ln, font=font(KAI, 36), fill=INK + (235,), anchor='mm')
AT.add('cls_pick', rough(im, 61, .12))
AT.add('cls_foot', label('日后可在萤光古树下重新立誓', font(KAI, 24), (110, 88, 66)))


def ribbon_button(text, w=400, h=112, color=(140, 34, 26), seed=3):
    S = 2
    im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lo = tuple(int(c * .62) for c in color)
    d.polygon([(0, 18 * S), (w * S, 18 * S), ((w - 26) * S, h * S / 2), (w * S, (h - 18) * S), (0, (h - 18) * S), (26 * S, h * S / 2)], fill=lo + (255,))
    d.rounded_rectangle([34 * S, 8 * S, (w - 34) * S, (h - 8) * S], 10 * S, fill=color + (255,), outline=(60, 12, 8, 255), width=3 * S)
    d.rounded_rectangle([44 * S, 16 * S, (w - 44) * S, (h - 16) * S], 6 * S, outline=(226, 170, 120, 170), width=2 * S)
    d.text((w * S / 2, h * S / 2 - 2 * S), text, font=font(SERIF, 44 * S), fill=(250, 234, 204, 255), anchor='mm')
    a = np.array(im.resize((w, h), Image.LANCZOS)).astype(np.float32)
    a[..., :3] *= (noise(h, w, 6, seed) * .07 + .97)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


AT.add('btn_sign', shadowed(ribbon_button('立 下 誓 约'), pad=8))
AT.add('btn_sign_off', shadowed(ribbon_button('先 选 职 业', color=(120, 104, 86)), pad=8))

# ---- 誓约之书（任务面板）
im = Image.new('RGBA', (500, 130), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.text((250, 40), '墨 曜 的 长 梦', font=font(SERIF, 50), fill=CINNABAR + (255,), anchor='mm')
d.text((250, 100), '第一章 · 守夜人的誓约', font=font(KAI, 27), fill=INK + (220,), anchor='mm')
AT.add('q_title', im)
for i, (txt, dest) in enumerate(OBJ_LONG):
    lines = wrap(txt, font(KAI, 30), 460)
    im = Image.new('RGBA', (480, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 6
    for ln in lines:
        d.text((8, y), ln, font=font(KAI, 30), fill=INK + (255,))
        y += 44
    d.text((8, y + 10), dest, font=font(KAI, 26), fill=CINNABAR + (240,))
    AT.add(f'q_obj_{i + 1}', rough(im, 70 + i, .1))
STEPS = ['签下职业誓约', '调制一滴星露', '烤出三枚火种', '攒够三十月辉', '供奉龙魂之卵', '唤墨曜同行']
for i, s in enumerate(STEPS):
    AT.add(f'q_step_{i + 1}', label(f'{NUM[i]}　{s}', font(KAI, 28), INK))
chk = ss(lambda dd, S: line(dd, [(8, 22), (18, 32), (36, 8)], 6, CINNABAR + (245,), S), 44, 40)
AT.add('q_check', chk)
AT.add('q_now', label('▶', font(HEAVY, 20), CINNABAR))
AT.add('q_offer', label('龙 魂 供 奉', font(SERIF, 40), CINNABAR))
AT.add('q_bag', label('随 身 行 囊', font(SERIF, 34), INK))
AT.add('q_hint', label('想换口味？去女巫药铺试饮未知药剂', font(KAI, 22), (110, 88, 66)))
AT.add('q_lorehead', label('已读的手稿与碑文', font(KAI, 26), INK))


def item_icon(kind):
    def draw(d, S):
        ink, red = INK + (255,), CINNABAR + (255,)
        if kind == 'moon':
            d.ellipse([10 * S, 8 * S, 54 * S, 52 * S], fill=(226, 214, 170, 255), outline=ink, width=3 * S)
            d.ellipse([24 * S, 2 * S, 64 * S, 42 * S], fill=(0, 0, 0, 0))
            d.arc([24 * S, 2 * S, 64 * S, 42 * S], 108, 236, fill=ink, width=3 * S)
        elif kind == 'ember':
            d.polygon([(32 * S, 6 * S), (48 * S, 30 * S), (44 * S, 50 * S), (32 * S, 58 * S), (20 * S, 50 * S), (16 * S, 30 * S)], fill=(206, 90, 40, 255), outline=ink)
            d.polygon([(32 * S, 26 * S), (40 * S, 40 * S), (32 * S, 52 * S), (24 * S, 40 * S)], fill=(240, 190, 90, 255))
        elif kind == 'dew':
            d.polygon([(32 * S, 6 * S), (48 * S, 36 * S), (32 * S, 58 * S), (16 * S, 36 * S)], fill=(150, 196, 214, 255), outline=ink)
            line(d, [(26, 34), (30, 44)], 3, (240, 250, 255, 255), S)
            for sx, sy in ((52, 12), (12, 16)):
                line(d, [(sx - 5, sy), (sx + 5, sy)], 2, ink, S); line(d, [(sx, sy - 5), (sx, sy + 5)], 2, ink, S)
        elif kind == 'mush':
            d.pieslice([8 * S, 8 * S, 56 * S, 56 * S], 180, 360, fill=(170, 60, 44, 255), outline=ink, width=3 * S)
            d.rounded_rectangle([25 * S, 30 * S, 39 * S, 56 * S], 5 * S, fill=(236, 224, 200, 255), outline=ink, width=3 * S)
            for sx, sy in ((22, 22), (38, 18), (44, 27)):
                d.ellipse([(sx - 3) * S, (sy - 3) * S, (sx + 3) * S, (sy + 3) * S], fill=(244, 232, 208, 255))
        elif kind == 'flower':
            for k in range(5):
                a = k * 2 * np.pi / 5 - np.pi / 2
                x, y = 32 + np.cos(a) * 14, 28 + np.sin(a) * 14
                d.ellipse([(x - 10) * S, (y - 10) * S, (x + 10) * S, (y + 10) * S], fill=(196, 176, 226, 255), outline=ink, width=2 * S)
            d.ellipse([25 * S, 21 * S, 39 * S, 35 * S], fill=(236, 200, 90, 255), outline=ink, width=2 * S)
            line(d, [(32, 42), (30, 60)], 3, ink, S)
        else:
            for x, y, r in ((22, 30, 13), (38, 24, 14), (44, 38, 12), (28, 42, 12)):
                d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(238, 232, 220, 255), outline=ink, width=3 * S)
            d.ellipse([20 * S, 22 * S, 46 * S, 46 * S], fill=(238, 232, 220, 255))
    return ss(draw, 64, 64)


for k, nm in (('moon', '月辉'), ('ember', '火种'), ('dew', '星露'), ('mush', '蘑菇'), ('flower', '月见花'), ('wool', '羊毛')):
    AT.add(f'it_{k}', item_icon(k))
    AT.add(f'nm_it_{k}', label(nm, font(KAI, 28), INK))
bar = Image.new('RGBA', (300, 16), (0, 0, 0, 0))
d = ImageDraw.Draw(bar)
d.rounded_rectangle([0, 3, 299, 12], 5, fill=INK + (46,), outline=INK + (150,), width=1)
AT.add('bar_bg', bar)
bar = Image.new('RGBA', (300, 16), (0, 0, 0, 0))
d = ImageDraw.Draw(bar)
d.rounded_rectangle([0, 2, 299, 13], 6, fill=CINNABAR + (235,))
AT.add('bar_fill', rough(bar, 5, .3))

# ---- 烤蘑菇
def roast_bg():
    w, h = 900, 470
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    base = np.array([26, 18, 16], np.float32) + noise(h, w, 30, 5)[..., None] * 6 + noise(h, w, 4, 6)[..., None] * 3
    glow = np.exp(-(((xx - w / 2) / 420) ** 2 + ((yy - h * 1.05) / 240) ** 2))[..., None]
    rgb = base + glow * np.array([120, 46, 10], np.float32)
    a = np.full((h, w), 240, np.float32)
    im = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a]).astype(np.uint8))
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([4, 4, w - 5, h - 5], 26, fill=255)
    im.putalpha(Image.composite(im.getchannel('A'), Image.new('L', (w, h), 0), mask))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, w - 5, h - 5], 26, outline=(92, 66, 36, 255), width=6)
    d.rounded_rectangle([14, 14, w - 15, h - 15], 20, outline=GOLD + (200,), width=2)
    r = np.random.default_rng(8)
    for _ in range(46):                     # 飘起的火星
        x, y, s = r.uniform(40, w - 40), r.uniform(h * .45, h - 30), r.uniform(1.5, 4)
        d.ellipse([x - s, y - s, x + s, y + s], fill=(255, int(r.uniform(120, 210)), 60, int(r.uniform(90, 220))))
    return im


AT.add('roast_bg', shadowed(roast_bg(), pad=14, blur=10))
AT.add('roast_title', label('篝 火 烤 蘑 菇', font(SERIF, 52), (255, 214, 140), shadow=(0, 0, 0, 200)))
AT.add('roast_hint', label('蘑菇串来回晃 · 晃进金色火区的一瞬按下「出锅」', font(KAI, 28), (242, 232, 210), shadow=(0, 0, 0, 200)))
AT.add('roast_hint2', label('烤熟吃了脚步轻快 · 没熟吃了天旋地转', font(KAI, 24), (214, 190, 150), shadow=(0, 0, 0, 200)))


def roast_bar():
    w, h = 720, 60
    gx = np.linspace(0, 1, w)[None, :].repeat(h, 0)
    cold = np.array([70, 84, 104], np.float32)
    hot = np.array([150, 58, 30], np.float32)
    rgb = cold * (1 - gx[..., None]) + hot * gx[..., None] + noise(h, w, 5, 9)[..., None] * 8
    im = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), np.full((h, w), 255)]).astype(np.uint8))
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], 16, fill=255)
    im.putalpha(mask)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 16, outline=(20, 12, 10, 255), width=4)
    for k in range(1, 12):
        x = k * w / 12
        d.line([(x, h - 14), (x, h - 5)], fill=(240, 226, 200, 110), width=2)
    return im


def roast_zone():
    w, h = 160, 60
    gx = np.abs(np.linspace(-1, 1, w))[None, :].repeat(h, 0)
    rgb = np.array([255, 196, 70], np.float32) * (1 - gx[..., None] * .35) + noise(h, w, 4, 10)[..., None] * 10
    a = np.clip((1 - gx) * 6, 0, 1) * 255
    im = Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a]).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.line([(8, 3), (w - 8, 3)], fill=(255, 244, 200, 255), width=3)
    d.line([(8, h - 4), (w - 8, h - 4)], fill=(255, 244, 200, 255), width=3)
    return im


def skewer():
    def draw(d, S):
        ink = (20, 12, 10, 255)
        line(d, [(48, 8), (48, 150)], 5, (150, 110, 60, 255), S)
        for cy, r, col in ((40, 26, (176, 66, 46)), (84, 22, (196, 120, 60))):
            d.pieslice([(48 - r) * S, (cy - r) * S, (48 + r) * S, (cy + r) * S], 180, 360, fill=col + (255,), outline=ink, width=3 * S)
            d.rounded_rectangle([40 * S, (cy - 2) * S, 56 * S, (cy + 20) * S], 5 * S, fill=(238, 226, 200, 255), outline=ink, width=3 * S)
            d.ellipse([(48 - 12) * S, (cy - 16) * S, (48 - 5) * S, (cy - 9) * S], fill=(250, 236, 210, 255))
        d.polygon([(40 * S, 150 * S), (56 * S, 150 * S), (48 * S, 168 * S)], fill=(255, 220, 120, 255))
    return shadowed(ss(draw, 96, 172), pad=6, blur=4)


AT.add('roast_bar', roast_bar())
AT.add('roast_zone', roast_zone())
AT.add('roast_cursor', skewer())
AT.add('roast_btn', shadowed(wax_seal(220, '出锅', seed=21, color=(186, 84, 30), tscale=.3), pad=10))
AT.add('roast_ok', label('烤熟了！脚步轻快', font(SERIF, 50), (255, 220, 140), shadow=(0, 0, 0, 220), stroke=3, stroke_fill=(40, 20, 8)))
AT.add('roast_bad', label('没烤熟……天旋地转', font(SERIF, 50), (200, 180, 255), shadow=(0, 0, 0, 220), stroke=3, stroke_fill=(24, 12, 40)))
AT.add('roast_wait', label('火候未稳，稍等片刻', font(KAI, 28), (214, 190, 150), shadow=(0, 0, 0, 200)))
AT.add('buff_speed', label('脚步轻快', font(KAI, 28), (255, 224, 150), shadow=(0, 0, 0, 200), stroke=2, stroke_fill=(30, 18, 8)))
AT.add('buff_dizzy', label('天旋地转', font(KAI, 28), (206, 186, 255), shadow=(0, 0, 0, 200), stroke=2, stroke_fill=(20, 10, 34)))

# ---- 阅读用的整张羊皮纸
AT.add('lore_bg', parchment(640, 820, 961, burn=True))

# ---- 战斗按键
def combat_base(size, tint=(46, 36, 66), rim=GOLD, inner=.86):
    S = 3
    n = size * S
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    r = np.hypot(xx - n / 2, yy - n / 2) / (n / 2)
    top = np.clip((n / 2 - yy) / n + .5, 0, 1)
    c0 = np.array(tint, np.float32)
    rgb = c0 * (.55 + .75 * top[..., None]) * (1.05 - .45 * np.clip(r, 0, 1)[..., None] ** 2)
    a = np.clip((inner - r) * n / 4, 0, 1) * 232
    out = np.dstack([np.clip(rgb, 0, 255), a]).astype(np.uint8)
    im = Image.fromarray(out)
    d = ImageDraw.Draw(im)
    w = int(n * .045)
    d.ellipse([n * (1 - inner) / 2 - w / 2, n * (1 - inner) / 2 - w / 2, n * (1 + inner) / 2 + w / 2, n * (1 + inner) / 2 + w / 2], outline=tuple(int(c * .5) for c in rim) + (255,), width=int(w * 1.5))
    d.ellipse([n * (1 - inner) / 2, n * (1 - inner) / 2, n * (1 + inner) / 2, n * (1 + inner) / 2], outline=rim + (255,), width=w)
    d.arc([n * (1 - inner) / 2 + w, n * (1 - inner) / 2 + w, n * (1 + inner) / 2 - w, n * (1 + inner) / 2 - w], 205, 335, fill=(255, 244, 214, 150), width=int(w * .5))
    for k in range(4):                    # 四个铆钉
        a_ = np.pi / 4 + k * np.pi / 2
        x, y = n / 2 + np.cos(a_) * n * inner / 2, n / 2 + np.sin(a_) * n * inner / 2
        d.ellipse([x - w * .9, y - w * .9, x + w * .9, y + w * .9], fill=(250, 226, 160, 255), outline=(70, 46, 16, 255))
    im = im.resize((size, size), Image.LANCZOS)
    return shadowed(im, pad=0, blur=5, off=(0, 5), alpha=170)


AT.add('cb_base', combat_base(200))
AT.add('cb_atk', combat_base(256, tint=(120, 34, 30)))
AT.add('cb_exit', combat_base(160, tint=(40, 40, 46), rim=(170, 170, 176)))
cd = ss(lambda dd, S: dd.ellipse([14 * S, 14 * S, 186 * S, 186 * S], fill=(8, 6, 12, 205)), 200, 200)
AT.add('cb_cd', cd)
for key in ['sword', 'staff', 'bow', 'duel', 'exit', 'shield', 'spin', 'judgement', 'volley', 'pierce', 'rain', 'nova', 'frost', 'meteor', 'book', 'prism']:
    AT.add(f'ic_{key}', icon(key, 128))
AT.add('lbl_fight', label('拔剑', fw, (246, 238, 220), shadow=(0, 0, 0, 190), stroke=2, stroke_fill=(20, 14, 10)))
AT.add('lbl_sheath', label('收剑', fw, (246, 238, 220), shadow=(0, 0, 0, 190), stroke=2, stroke_fill=(20, 14, 10)))
AT.add('lbl_duel_wait', label('等待对手穿过裂隙之门', font(KAI, 30), (246, 238, 220), shadow=(0, 0, 0, 200), stroke=2, stroke_fill=(20, 14, 10)))
AT.add('lbl_duel_go', label('对 决 开 始', font(SERIF, 64), (255, 220, 140), shadow=(0, 0, 0, 220), stroke=4, stroke_fill=(50, 16, 8)))
AT.add('lbl_duel_win', label('胜', font(SERIF, 150), (255, 220, 140), shadow=(0, 0, 0, 220), stroke=6, stroke_fill=(70, 20, 10)))
AT.add('lbl_duel_lose', label('败', font(SERIF, 150), (200, 196, 214), shadow=(0, 0, 0, 220), stroke=6, stroke_fill=(24, 20, 40)))
hpf = Image.new('RGBA', (340, 40), (0, 0, 0, 0))
d = ImageDraw.Draw(hpf)
d.rounded_rectangle([0, 0, 339, 39], 14, fill=(14, 10, 20, 215), outline=GOLD + (255,), width=3)
AT.add('hp_frame', hpf)
hpb = Image.new('RGBA', (320, 22), (0, 0, 0, 0))
d = ImageDraw.Draw(hpb)
d.rounded_rectangle([0, 0, 319, 21], 9, fill=(210, 70, 50, 255))
d.rounded_rectangle([3, 3, 316, 9], 4, fill=(255, 150, 120, 150))
AT.add('hp_fill', hpb)
AT.add('lbl_hp', label('心火', font(KAI, 26), (255, 214, 170), shadow=(0, 0, 0, 200), stroke=2, stroke_fill=(30, 10, 8)))
AT.add('lbl_foe', label('对手', font(KAI, 26), (206, 196, 255), shadow=(0, 0, 0, 200), stroke=2, stroke_fill=(16, 10, 30)))

AT.pack()
for i, b in enumerate(AT.bins):
    tex_png(f'atlas{i + 1}', b)

# =====================================================================
# 7. 排版数据与 Lua 数据段
def label_box(p):
    """地图上地名的可点区域（以地点为原点、地图贴图像素为单位）。"""
    fs = 44 if p.get('major') else 35
    dx, dy = p.get('dx', 12) * MS / 5, p.get('dy', -12) * MS / 5
    w = len(p['name']) * fs
    return [round(dx + w / 2, 1), round(-(dy + fs * .6), 1), round(w / 2 + 12, 1), round(fs / 2 + 12, 1)]


LAYOUT = dict(
    map=dict(M=MM, S=MS, size=MW),
    pages=dict(w=PW * 2, h=PH),
    cards={k: v for k, v in CARDS.items()},
    lore=dict(w=LW, h=LH, cols=4, n=len(LORE)),
    poi=[dict(id=p['id'], x=p['x'], z=p['z'], box=label_box(p)) for p in POI],
    atlas=AT.rects,
    tex={k: [v[1], v[2]] for k, v in TEX.items()},
)
json.dump(LAYOUT, open(f'{OUT}/layout.json', 'w'), ensure_ascii=False, indent=1)


def lua_val(v):
    if isinstance(v, dict):
        return '{' + ','.join(f'[{json.dumps(k, ensure_ascii=False)}]={lua_val(x)}' for k, x in v.items()) + '}'
    if isinstance(v, (list, tuple)):
        return '{' + ','.join(lua_val(x) for x in v) + '}'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    return repr(round(v, 3) if isinstance(v, float) else v)


with open(f'{OUT}/ui2_data.lua', 'w', encoding='utf8') as f:
    f.write('-- 由 tools/ui/make_ui2.py 生成，不要手改。\n')
    f.write('UI.K2L=' + lua_val({k: v for k, v in LAYOUT.items()}) + '\n')
    f.write('UI.K2B={}\n')
    for name, (data, w, h) in TEX.items():
        f.write(f'UI.K2B[{json.dumps(name)}]="{base64.b64encode(data).decode()}"\n')
tot = sum(len(v[0]) for v in TEX.values())
print('textures', {k: (v[1], v[2], len(v[0]) // 1024) for k, v in TEX.items()}, 'total KB', tot // 1024, 'atlas bins', len(AT.bins), 'sprites', len(AT.rects))
