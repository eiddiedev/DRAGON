#!/usr/bin/env python3
"""生成龙眠之境的全部 UI 贴图，并各自打包成一个带贴图的小方片 GLB（导入编辑器后由脚本取走贴图）。
输出：assets/ui/png/*.png（预览）、assets/ui/glb/ui_*.glb、assets/ui/layout.json（脚本要用的排版数据）。
字体全部是 SIL OFL 开源字体：思源黑体 Heavy、思源宋体 Heavy、霞鹜文楷。"""
import json, os, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = '/Users/bytedance/Documents/ChatGPT/DRAGON'
sys.path.insert(0, f'{ROOT}/tools/models')
from glbw import Geo, write_glb  # noqa: E402

OUT = f'{ROOT}/assets/ui'
os.makedirs(f'{OUT}/png', exist_ok=True)
os.makedirs(f'{OUT}/glb', exist_ok=True)
F = f'{ROOT}/assets/fonts'
HEAVY = f'{F}/SourceHanSansCN-Heavy.ttf'
SERIF = f'{F}/SourceHanSerifCN-Heavy.otf'
KAI = f'{F}/LXGWWenKai-Medium.otf'
KAIB = f'{F}/LXGWWenKai-Medium.otf'
INK = (46, 33, 22)
CINNABAR = (156, 43, 30)
rng = np.random.default_rng(11)
LAYOUT = {}


def noise(h, w, scale, seed):
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, (max(2, h // scale), max(2, w // scale))).astype(np.float32)
    n = cv2.resize(n, (w, h), interpolation=cv2.INTER_CUBIC)
    return n / (np.abs(n).max() + 1e-6)


def parchment(w, h, seed=0, burn=True):
    """羊皮纸：旧化斑、纤维、焦边。返回 RGBA 数组，边缘不规则透明。"""
    base = np.array([234, 220, 191], np.float32)
    dark = np.array([184, 150, 104], np.float32)
    n1 = noise(h, w, 40, seed) * .5 + noise(h, w, 9, seed + 1) * .25
    fib = cv2.GaussianBlur(np.random.default_rng(seed + 2).normal(0, 1, (h, w)).astype(np.float32), (0, 0), .8)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ed = np.minimum.reduce([xx, w - 1 - xx, yy, h - 1 - yy])
    edge_n = noise(h, w, 14, seed + 3) * 9 + noise(h, w, 4, seed + 4) * 3
    d = ed + edge_n
    burnt = np.clip(1 - (d - 6) / 34, 0, 1) ** 1.6 if burn else np.zeros_like(d)
    t = np.clip(.18 + n1 * .22 + burnt * .8, 0, 1)[..., None]
    rgb = base * (1 - t) + dark * t + fib[..., None] * 5
    rgb = rgb * (1 - .55 * np.clip(1 - (d - 2) / 8, 0, 1) ** 2)[..., None]   # 焦黑的最外缘
    a = np.clip((d - 1) * 255 / 3, 0, 255)
    return np.dstack([np.clip(rgb, 0, 255), a]).astype(np.uint8)


def save(name, img):
    img.save(f'{OUT}/png/{name}.png')


def pack(name, img):
    """贴图做成一个 1×1 米的竖直方片 GLB（双面、透明）。"""
    g = Geo([[(0, '#ffffff'), (1, '#ffffff')]])
    g.P, g.N, g.T, g.J, g.W = [], [], [], [], []
    w, h = img.size
    ar = h / w
    corners = [(-.5, 0, 0), (.5, 0, 0), (.5, 0, ar), (-.5, 0, ar)]
    uvs = [(0, 1), (1, 1), (1, 0), (0, 0)]
    for tri in ((0, 1, 2), (0, 2, 3)):
        for i in tri:
            g.P.append(np.array(corners[i], float))
            g.N.append(np.array((0, -1, 0), float))
            g.T.append(uvs[i])
            g.J.append((0, 0, 0, 0))
            g.W.append((255, 0, 0, 0))
    write_glb(f'{OUT}/glb/{name}.glb', g, name=name, image=img, alpha=True, rough=1)
    save(name, img)


def text_w(f, s):
    return f.getbbox(s)[2] - f.getbbox(s)[0]


# =====================================================================
# 1. 标题：「龙眠之境」朱红手绘字 + 黑描边，三帧抖动；底部一行副标题
def title_frame(seed):
    W, Hh = 1024, 300
    S = 2   # 超采样
    canvas = np.zeros((Hh * S, W * S), np.uint8)
    im = Image.fromarray(canvas)
    d = ImageDraw.Draw(im)
    chars = '龙眠之境'
    r = np.random.default_rng(100)        # 版式固定，帧之间只变笔触
    x = 70 * S
    for i, ch in enumerate(chars):
        size = int((228 if i in (0, 3) else 200) * S * r.uniform(.96, 1.04))
        f = ImageFont.truetype(HEAVY, size)
        g = Image.new('L', (size * 2, size * 2))
        ImageDraw.Draw(g).text((size // 2, size // 2), ch, font=f, fill=255)
        g = g.rotate(r.uniform(-7, 7), resample=Image.BICUBIC)
        bb = g.getbbox()
        g = g.crop(bb)
        y = int((Hh * S - g.size[1]) / 2 + r.uniform(-14, 14) * S)
        im.paste(255, (x, y), g)
        x += g.size[0] + int(r.uniform(4, 16) * S)
    m = np.array(im).astype(np.float32) / 255
    # 整体比例：把字居中
    cols = np.where(m.max(0) > 0)[0]
    shift = int((W * S - (cols[0] + cols[-1])) / 2)
    m = np.roll(m, shift, 1)
    # 低频摆动（帧间几乎不变）+ 高频抖边（每帧不同）
    hh, ww = m.shape
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    lo_x, lo_y = noise(hh, ww, 110, 5) * 13 * S + noise(hh, ww, 36, 7) * 4 * S, noise(hh, ww, 110, 6) * 13 * S + noise(hh, ww, 36, 8) * 4 * S
    hi_x, hi_y = noise(hh, ww, 12, seed) * 3.2 * S, noise(hh, ww, 12, seed + 50) * 3.2 * S
    m = cv2.remap(m, xx + lo_x + hi_x, yy + lo_y + hi_y, cv2.INTER_LINEAR)
    # 笔画加粗一点、边缘圆润不齐
    m = cv2.GaussianBlur(m, (0, 0), 4.0 * S)
    fill = (m + noise(hh, ww, 7, seed + 9) * .10 + noise(hh, ww, 50, 33) * .08 > .40).astype(np.float32)
    fill = cv2.GaussianBlur(fill, (0, 0), .9 * S)
    outline_src = cv2.GaussianBlur(m, (0, 0), 3.0 * S)
    outline = (outline_src + noise(hh, ww, 8, seed + 20) * .06 > .16).astype(np.float32)
    outline = cv2.GaussianBlur(outline, (0, 0), .9 * S)
    # 颜色：朱红里带一点笔刷深浅
    red = np.array([226, 56, 30], np.float32)
    redd = np.array([196, 36, 22], np.float32)
    k = np.clip(noise(hh, ww, 30, 77) * .5 + .5, 0, 1)[..., None] * .5
    col = red * (1 - k) + redd * k
    black = np.array([14, 11, 10], np.float32)
    a = np.clip(np.maximum(fill, outline), 0, 1)
    rgb = black * (1 - fill[..., None]) + col * fill[..., None]
    out = np.dstack([rgb, a * 255]).astype(np.uint8)
    out = cv2.resize(out, (W, Hh), interpolation=cv2.INTER_AREA)
    return out


title = np.zeros((1024, 1024, 4), np.uint8)
for i in range(3):
    title[i * 300:(i + 1) * 300] = title_frame(300 + i * 17)
sub = Image.new('RGBA', (1024, 124), (0, 0, 0, 0))
ds = ImageDraw.Draw(sub)
fs = ImageFont.truetype(KAIB, 46)
s = '轻 触 任 意 处  ·  入 梦'
ds.text((512 + 2, 64 + 2), s, font=fs, fill=(0, 0, 0, 160), anchor='mm')
ds.text((512, 64), s, font=fs, fill=(244, 238, 222, 255), anchor='mm')
title[900:1024] = np.array(sub)
pack('ui_title', Image.fromarray(title))
LAYOUT['title'] = dict(frames=[[0, 1 - (i + 1) * 300 / 1024, 1, 300 / 1024] for i in range(3)],
                       sub=[0, 0, 1, 124 / 1024], aspect=1024 / 300, sub_aspect=1024 / 124)

# =====================================================================
# 2. 古书（空白摊开）：皮革封面 + 铜角 + 两页羊皮纸
BW, BH = 1024, 680
book = np.zeros((BH, BW, 4), np.float32)
yy, xx = np.mgrid[0:BH, 0:BW].astype(np.float32)
# 封面
lc = np.array([46, 37, 31], np.float32)
lk = noise(BH, BW, 12, 3)[..., None] * 9 + noise(BH, BW, 3, 4)[..., None] * 5
cover = np.clip(lc + lk, 0, 255)
r_ = 26
inside = ((xx > 8) & (xx < BW - 8) & (yy > 14) & (yy < BH - 8)).astype(np.float32)
book[..., :3] = cover
book[..., 3] = inside * 255
# 压花描线
im = Image.fromarray(book.astype(np.uint8))
d = ImageDraw.Draw(im)
d.rounded_rectangle([20, 26, BW - 20, BH - 20], 18, outline=(92, 72, 52, 255), width=3)
d.rounded_rectangle([30, 36, BW - 30, BH - 30], 14, outline=(70, 54, 40, 255), width=1)
for k in range(0, BW, 34):   # 上下缘的藤蔓压花
    for yb in (24, BH - 22):
        d.arc([k, yb - 7, k + 20, yb + 7], 0, 180 if yb < 100 else 360, fill=(104, 82, 58, 255), width=2)
book = np.array(im).astype(np.float32)
# 书页（左右两页 + 页边叠层）
PL = (64, 44, 508, 640)    # 左页 x0,y0,x1,y1
PR = (516, 44, 960, 640)
for (x0, y0, x1, y1), seed, side in ((PL, 21, -1), (PR, 22, 1)):
    for k in range(5, 0, -1):   # 页边叠层（在下方和外侧露出一点）
        ox = side * k * 2.2
        pg = parchment(x1 - x0, y1 - y0 + 6, seed + k * 7, burn=True).astype(np.float32)
        pg[..., :3] *= .78 - k * .03
        sl = book[y0 + k * 2:y1 + 6 + k * 2, int(x0 + ox):int(x1 + ox)]
        a = pg[..., 3:4] / 255
        sl[..., :3] = sl[..., :3] * (1 - a) + pg[..., :3] * a
    pg = parchment(x1 - x0, y1 - y0, seed, burn=True).astype(np.float32)
    # 靠书脊处变暗（纸页弯曲）
    gx = np.linspace(0, 1, x1 - x0)[None, :]
    curve = (1 - gx) if side < 0 else gx
    shade = .62 + .38 * np.clip(curve * 3.2, 0, 1) ** .6
    shade *= .95 + .05 * np.clip(1 - curve, 0, 1)
    pg[..., :3] *= shade[..., None]
    sl = book[y0:y1, x0:x1]
    a = pg[..., 3:4] / 255
    sl[..., :3] = sl[..., :3] * (1 - a) + pg[..., :3] * a
# 书脊阴影
spine = np.exp(-((xx - 512) / 10) ** 2)[..., None]
book[..., :3] *= 1 - .55 * spine * (yy[..., None] > 40)
# 铜角
im = Image.fromarray(np.clip(book, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(im)
for cx, cy, sx, sy in ((10, 16, 1, 1), (BW - 10, 16, -1, 1), (10, BH - 10, 1, -1), (BW - 10, BH - 10, -1, -1)):
    pts = [(cx, cy), (cx + sx * 78, cy), (cx + sx * 58, cy + sy * 16), (cx + sx * 16, cy + sy * 58), (cx, cy + sy * 78)]
    d.polygon(pts, fill=(138, 106, 58, 255), outline=(70, 50, 26, 255))
    d.line([(cx + sx * 10, cy + sy * 50), (cx + sx * 50, cy + sy * 10)], fill=(186, 150, 92, 255), width=3)
    d.ellipse([cx + sx * 18 - 5, cy + sy * 18 - 5, cx + sx * 18 + 5, cy + sy * 18 + 5], fill=(196, 160, 100, 255))
# 书签丝带（朱砂）
d.polygon([(520, 630), (538, 630), (538, 676), (529, 666), (520, 676)], fill=(140, 36, 28, 255))
pack('ui_book', im)
LAYOUT['book'] = dict(aspect=BW / BH, left=[PL[0] / BW, 1 - PL[3] / BH, (PL[2] - PL[0]) / BW, (PL[3] - PL[1]) / BH],
                      right=[PR[0] / BW, 1 - PR[3] / BH, (PR[2] - PR[0]) / BW, (PR[3] - PR[1]) / BH])

# =====================================================================
# 3. 序章正文页（每张贴图两页，透明底，只有墨字）
PAGES = [
    ('蚀 月', ['很久以前，天空裂开了一道口子。', '人们叫它蚀月之隙。', '',
             '每到夜里，从裂隙里落下的，', '不是星光，而是影子。', '',
             '没有形状，没有声音，', '只会循着温度游荡的影灵。']),
    ('墨 曜', ['古龙墨曜从北方的山脊飞来。', '', '它没有去撕咬那些影子，',
             '而是在最高的山峰上盘起身子，', '闭上了眼睛。', '',
             '它用自己的梦，把裂隙缝上了。', '', '从此，这片土地有了名字：', '龙眠之境。']),
    ('守 夜 人', ['龙的梦并不完美。', '夜深时，总有影灵从梦的缝隙里漏出来。', '',
               '于是人们点起了灯。', '灯火所及之处，影灵不敢靠近；', '灯火之外，是守夜人的夜。', '',
               '守夜人提灯走进黑暗，', '把影灵打散成月辉，', '那是龙梦的碎片。']),
    ('龙 蛋', ['墨曜入睡前，', '在城堡深处留下了一枚蛋。', '',
             '守夜人相信，只要月辉、篝火与星露', '一同落在蛋壳上，', '龙就会认出它的守护者。', '',
             '一代代守夜人老去，', '蛋始终没有醒。']),
    ('你', ['如今城堡空了，灯还亮着。', '', '你在晷石原醒来，', '手里握着一张旧地图。', '',
           '白天，这片土地属于你：', '去走，去看，去骑马，', '去喝女巫那些古怪的药水。', '',
           '夜里，如果你愿意，', '就提灯出去。', '', '#墨曜在等。']),
]
NUM = '一二三四五六'
PW, PH = 512, 683
f_t = ImageFont.truetype(SERIF, 50)
f_b = ImageFont.truetype(KAI, 27)
f_n = ImageFont.truetype(KAI, 22)


def ink_page(title, lines, idx):
    im = Image.new('RGBA', (PW * 2, PH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox = 0
    d.text((ox + PW / 2, 92), title, font=f_t, fill=CINNABAR + (255,), anchor='mm')
    # 标题下的小饰线：两段短线夹一个菱形
    y = 140
    d.line([(ox + PW / 2 - 90, y), (ox + PW / 2 - 14, y)], fill=INK + (200,), width=2)
    d.line([(ox + PW / 2 + 14, y), (ox + PW / 2 + 90, y)], fill=INK + (200,), width=2)
    d.polygon([(ox + PW / 2, y - 7), (ox + PW / 2 + 7, y), (ox + PW / 2, y + 7), (ox + PW / 2 - 7, y)], fill=CINNABAR + (230,))
    y = 186
    for ln in lines:
        if ln == '':
            y += 14
            continue
        red = ln.startswith('#')
        t = ln[1:] if red else ln
        f = ImageFont.truetype(KAIB, 34) if red else f_b
        d.text((ox + 58, y), t, font=f, fill=(CINNABAR if red else INK) + (255,))
        y += 44 if red else 38
    d.text((ox + PW / 2, PH - 50), f'· {NUM[idx]} ·', font=f_n, fill=INK + (170,), anchor='mm')
    a = np.array(im)
    # 墨色深浅不匀
    k = (noise(PH, PW * 2, 5, 400 + idx) * .18 + .9)
    a[..., 3] = np.clip(a[..., 3] * k, 0, 255).astype(np.uint8)
    return Image.fromarray(a).crop((0, 0, PW, PH))


def egg_page():
    """第六页：墨曜之卵的墨线插画。"""
    im = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = PW / 2, PH / 2 - 30
    d.text((cx, 92), '墨曜之卵', font=f_t, fill=CINNABAR + (255,), anchor='mm')
    # 月牙
    d.arc([cx - 196, 150, cx - 116, 230], 90, 270, fill=INK + (220,), width=3)
    d.arc([cx - 182, 156, cx - 130, 224], 90, 270, fill=INK + (220,), width=2)
    # 蛋
    ew, eh = 120, 160
    d.ellipse([cx - ew, cy - eh, cx + ew, cy + eh], outline=INK + (255,), width=4)
    for row in range(-5, 6):   # 鳞纹
        yb = cy + row * 26
        half = ew * np.sqrt(max(0, 1 - (row * 26 / eh) ** 2)) - 10
        n = int(half * 2 / 30)
        for k in range(n):
            x0 = cx - half + k * 30 + (15 if row % 2 else 0)
            if x0 + 26 < cx + half:
                d.arc([x0, yb - 12, x0 + 28, yb + 12], 0, 180, fill=INK + (150,), width=2)
    # 裂纹
    d.line([(cx - 30, cy - 120), (cx - 8, cy - 80), (cx - 26, cy - 50), (cx + 4, cy - 14)], fill=CINNABAR + (230,), width=3)
    # 底座的火焰与光点
    for k in range(-2, 3):   # 蛋下三团小火苗
        fx = cx + k * 46
        d.polygon([(fx - 12, cy + eh + 34), (fx, cy + eh + 6 - abs(k) * 4), (fx + 12, cy + eh + 34)], outline=CINNABAR + (200,), fill=None)
    f2 = ImageFont.truetype(KAI, 26)
    d.text((cx, PH - 120), '月辉 · 火种 · 星露', font=f2, fill=INK + (230,), anchor='mm')
    d.text((cx, PH - 50), '· 六 ·', font=f_n, fill=INK + (170,), anchor='mm')
    return im


pages = [ink_page(t, l, i) for i, (t, l) in enumerate(PAGES)] + [egg_page()]
for k in range(3):
    sheet = Image.new('RGBA', (PW * 2, PH), (0, 0, 0, 0))
    sheet.paste(pages[k * 2], (0, 0))
    sheet.paste(pages[k * 2 + 1], (PW, 0))
    pack(f'ui_pages{k + 1}', sheet)

# =====================================================================
# 4. 地图（底稿缩到 1024，四边撕边透明 → 引擎按无损 ARGB32 存，墨线不糊）
mp = Image.open(f'{ROOT}/docs/ui/map_base.png').convert('RGB').resize((1024, 1024), Image.LANCZOS)
pa = parchment(1024, 1024, 61, burn=True)
m = np.array(mp).astype(np.float32)
a = pa[..., 3:4].astype(np.float32) / 255
burn = (pa[..., :3].astype(np.float32) / np.array([234, 220, 191], np.float32))
m = np.clip(m * np.clip(burn, .35, 1.05), 0, 255)
pack('ui_map', Image.fromarray(np.dstack([m, a[..., 0] * 255]).astype(np.uint8)))
POI = json.load(open(f'{ROOT}/docs/ui/poi.json'))
LAYOUT['map'] = dict(M=120, S=5, size=1520)

# =====================================================================
# 5. 地点介绍卡（两张图集，每张 10 张卡，512×204）
DESC = {
    'spawn': '时之晷立在这里，它是封印的钟。指针走进夜里，封印就松一分。你在这里醒来。',
    'castle': '守夜人的城堡，如今空了。王座厅、书库、军械库、厨房、宴会厅和龙巢圣所都还在。',
    'dragon_peak': '墨曜沉睡的山巅。别吵醒它——除非你已经结了龙契。',
    'altar': '结了龙契的人站在这里，墨曜的梦身才会从山顶飞下来。',
    'rift_gate': '城堡脚下的古传送门。入夜后被蚀月之隙撑开，影灵从这里涌出。',
    'arena': '守夜人切磋的地方。两人对决，点到为止。',
    'village': '夜里最亮的地方。灯火彻夜不熄，影灵从不进村。',
    'witch': '女巫什么都肯卖，只是不保证效果。变大、变小、变成羊……都有可能。',
    'camp': '篝火彻夜不灭。在这里烤一串完美的蘑菇，能得到火种。',
    'mushroom': '会发光的蘑菇林，女巫最爱的材料都长在这里。',
    'windmill': '风车慢慢转。白天看风景最好的一面坡。',
    'meadow': '羊群在这里吃草。喝了女巫的药变成羊，可以混进去。',
    'flowers': '一片紫色的花海，星露的主料就长在这里。',
    'glow_tree': '据说是墨曜第一次落地的地方，树上的光至今未散。',
    'bridge': '跨过河谷、通往城堡的石桥。月圆时桥面会泛光。',
    'lake': '夜里，湖面上能看见蚀月之隙的倒影。',
    'lighthouse': '海边最后一盏灯，替出海的人守着归路。',
    'harbor': '帆船停在这里，靠近就能登船出海。',
    'carpet': '飞毯从这里起飞，带你看看整片土地。',
}
CW, CH = 512, 204
f_cn = ImageFont.truetype(SERIF, 36)
f_cd = ImageFont.truetype(KAI, 25)


def wrap(s, f, width):
    out, cur = [], ''
    for ch in s:
        if text_w(f, cur + ch) > width and cur:
            out.append(cur)
            cur = ''
        cur += ch
    if cur:
        out.append(cur)
    return out


cards = []
for i, p in enumerate(POI):
    c = Image.fromarray(parchment(CW, CH, 700 + i, burn=True))
    d = ImageDraw.Draw(c)
    d.text((34, 26), p['name'], font=f_cn, fill=CINNABAR + (255,))
    nw = text_w(f_cn, p['name'])
    d.line([(34 + nw + 16, 48), (CW - 34, 48)], fill=INK + (110,), width=2)
    y = 82
    for ln in wrap(DESC[p['id']], f_cd, CW - 70)[:3]:
        d.text((34, y), ln, font=f_cd, fill=INK + (255,))
        y += 36
    cards.append(c)
card_uv = {}
for sheet_i in range(2):
    sheet = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    for k in range(10):
        idx = sheet_i * 10 + k
        if idx >= len(cards):
            break
        col, row = k % 2, k // 2
        sheet.paste(cards[idx], (col * CW, row * CH))
        card_uv[POI[idx]['id']] = [sheet_i + 1, col * CW / 1024, 1 - (row + 1) * CH / 1024, CW / 1024, CH / 1024]
    pack(f'ui_cards{sheet_i + 1}', sheet)

# =====================================================================
# 6. 杂项图集：地图按钮、玩家箭头、跳过/收起、提示、地点光圈、暗角
atlas = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
A = {}


def put(name, img, x, y):
    atlas.paste(img, (x, y), img)
    w, h = img.size
    A[name] = [x / 1024, 1 - (y + h) / 1024, w / 1024, h / 1024]


# 地图按钮：卷起的羊皮纸 + 朱砂蜡封
ic = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
d = ImageDraw.Draw(ic)
roll = Image.fromarray(parchment(200, 120, 900, burn=True))
roll = roll.rotate(-18, expand=True, resample=Image.BICUBIC)
ic.paste(roll, (14, 50), roll)
d.ellipse([22, 108, 62, 188], fill=(196, 168, 120, 255), outline=INK + (255,), width=3)   # 卷轴端头
d.ellipse([34, 128, 50, 168], fill=(150, 120, 80, 255))
d.line([(70, 92), (210, 140)], fill=INK + (120,), width=2)
d.line([(70, 150), (200, 190)], fill=INK + (90,), width=2)
d.line([(150, 70), (150, 230)], fill=(120, 80, 40, 255), width=4)   # 系绳
seal = Image.new('RGBA', (90, 90), (0, 0, 0, 0))
sd = ImageDraw.Draw(seal)
pts = [(45 + np.cos(a_) * (40 + 3 * np.sin(a_ * 7)), 45 + np.sin(a_) * (40 + 3 * np.cos(a_ * 5))) for a_ in np.linspace(0, 2 * np.pi, 40)]
sd.polygon(pts, fill=(150, 36, 26, 255))
sd.ellipse([18, 18, 72, 72], outline=(110, 22, 16, 255), width=3)
for k in range(3):   # 龙爪纹：三道弧
    sd.arc([26 + k * 9, 24, 52 + k * 9, 66], 200, 330, fill=(220, 120, 90, 255), width=3)
ic.paste(seal, (124, 118), seal)
put('mapbtn', ic, 0, 0)

# 玩家箭头（朱砂，带毛笔感）
ar = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
d = ImageDraw.Draw(ar)
d.polygon([(64, 8), (104, 112), (64, 88), (24, 112)], fill=CINNABAR + (255,), outline=(60, 12, 8, 255))
d.polygon([(64, 30), (88, 96), (64, 82)], fill=(196, 70, 50, 255))
put('arrow', ar, 256, 0)

# 地点光圈
ring = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
d = ImageDraw.Draw(ring)
for r, a_ in ((50, 70), (44, 180), (40, 90)):
    d.ellipse([64 - r, 64 - r, 64 + r, 64 + r], outline=CINNABAR + (a_,), width=4)
put('ring', ring, 384, 0)


def tag(text, w, h, seed, size=40):
    t = Image.fromarray(parchment(w, h, seed, burn=True))
    d = ImageDraw.Draw(t)
    d.text((w / 2, h / 2 + 1), text, font=ImageFont.truetype(KAIB, size), fill=INK + (255,), anchor='mm')
    return t


put('skip', tag('跳 过', 224, 84, 910), 512, 0)
put('close', tag('收 起', 224, 84, 911), 768, 0)
# 提示（白字带阴影，用在暗背景上）
hint = Image.new('RGBA', (512, 64), (0, 0, 0, 0))
d = ImageDraw.Draw(hint)
fh = ImageFont.truetype(KAI, 32)
d.text((258, 34), '轻 触 翻 页', font=fh, fill=(0, 0, 0, 170), anchor='mm')
d.text((256, 32), '轻 触 翻 页', font=fh, fill=(240, 232, 214, 255), anchor='mm')
put('hint_flip', hint, 0, 256)
hint2 = Image.new('RGBA', (512, 64), (0, 0, 0, 0))
d = ImageDraw.Draw(hint2)
d.text((258, 34), '点 地 名 看 介 绍', font=fh, fill=(0, 0, 0, 170), anchor='mm')
d.text((256, 32), '点 地 名 看 介 绍', font=fh, fill=(240, 232, 214, 255), anchor='mm')
put('hint_map', hint2, 512, 256)
# 暗角（中心透明、四周黑）
vg = np.zeros((256, 256, 4), np.uint8)
yy, xx = np.mgrid[0:256, 0:256] / 255.0
rr = np.hypot((xx - .5) * 1.0, (yy - .5) * 1.15)
vg[..., 3] = (np.clip((rr - .28) / .45, 0, 1) ** 1.6 * 255).astype(np.uint8)
put('vignette', Image.fromarray(vg), 0, 384)
# 胶片颗粒（256 方块，脚本里平铺）
gr = np.random.default_rng(5).random((256, 256))
gimg = np.zeros((256, 256, 4), np.uint8)
v = (gr > .5).astype(np.uint8) * 255
gimg[..., 0] = gimg[..., 1] = gimg[..., 2] = v
gimg[..., 3] = (np.abs(gr - .5) * 2 * 150).astype(np.uint8)
put('grain', Image.fromarray(gimg), 256, 384)
pack('ui_atlas', atlas)
LAYOUT['atlas'] = A
LAYOUT['cards'] = card_uv
LAYOUT['card_aspect'] = CW / CH
def label(p):
    fs = 34 if p.get('major') else 28
    dx, dy = p.get('dx', 12), p.get('dy', -12)
    w = len(p['name']) * fs
    k = 1000 / 1520
    return dict(lx=round((dx + w / 2) * k, 1), ly=round(-(dy + fs * .6) * k, 1), lw=round(w * k / 2 + 10, 1), lh=round(fs * k / 2 + 10, 1))


LAYOUT['poi'] = [dict(id=p['id'], x=p['x'], z=p['z'], **label(p)) for p in POI]
json.dump(LAYOUT, open(f'{OUT}/layout.json', 'w'), ensure_ascii=False, indent=1)
print('ok', sorted(os.listdir(f'{OUT}/glb')))
