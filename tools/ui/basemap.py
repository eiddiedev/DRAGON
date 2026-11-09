#!/usr/bin/env python3
"""从原生地形高度画一张中世纪羊皮纸风格的底图，给 Codex 做地图 UI 的参考和底稿。
输出 docs/ui/map_base.png（带地名，给人看）和 docs/ui/map_base_clean.png（无地名，给 Codex 用作底图）。
坐标换算：世界 (x, z) ∈ [0,256] → 图上 u = M + x*S, v = M + (256-z)*S（北在上）。
"""
import json, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = '/Users/a1234/Documents/awesomeWRLD'
OUT = f'{ROOT}/docs/ui'
os.makedirs(OUT, exist_ok=True)
SEA = 26.6
S = 5.0            # 每米像素
M = 120            # 四周留白
W = int(256 * S + 2 * M)
INK = (52, 38, 26)
INK_SOFT = (52, 38, 26, 110)
RED = (142, 38, 26)
rng = np.random.default_rng(7)

H = np.fromfile(f'{ROOT}/assets/terrain/native/heights.f32', '<f4').reshape(257, 257) * 256
# 放大到像素网格（北在上：行 0 = z 256）
Hp = cv2.resize(np.flipud(H).astype(np.float32), (int(256 * S), int(256 * S)), interpolation=cv2.INTER_CUBIC)
land = (Hp > SEA).astype(np.uint8)
land = cv2.morphologyEx(land, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))


def wp(x, z):
    return (M + x * S, M + (256 - z) * S)


# ---------- 羊皮纸
noise = rng.normal(0, 1, (W // 8, W // 8)).astype(np.float32)
noise = cv2.resize(cv2.GaussianBlur(noise, (0, 0), 3), (W, W))
fine = cv2.GaussianBlur(rng.normal(0, 1, (W, W)).astype(np.float32), (0, 0), 1.2)
yy, xx = np.mgrid[0:W, 0:W] / W
edge = np.clip(np.hypot(xx - .5, yy - .5) * 1.7, 0, 1) ** 3
base = np.array([236, 223, 196], np.float32)
dark = np.array([186, 160, 120], np.float32)
t = np.clip(edge * .9 + noise * .06 + fine * .02, 0, 1)[..., None]
paper = base * (1 - t) + dark * t
img = Image.fromarray(np.clip(paper, 0, 255).astype(np.uint8)).convert('RGBA')

# ---------- 海：陆地稍亮，海略深；海岸线外画几圈波纹线（老地图手法）
def layer():
    return Image.new('RGBA', (W, W), (0, 0, 0, 0))

full = np.ones((W, W), np.uint8)   # 地形外面当陆地算，只画真正的海岸
full[M:M + land.shape[0], M:M + land.shape[1]] = land
sea_tint = layer()
sm = Image.fromarray(((1 - full) * 38).astype(np.uint8))
sea_tint.putalpha(sm.filter(ImageFilter.GaussianBlur(6)))
sea_tint_rgb = Image.new('RGBA', (W, W), (120, 96, 66, 0))
sea_tint_rgb.putalpha(sea_tint.getchannel('A'))
img = Image.alpha_composite(img, sea_tint_rgb)

def bdist(pts):   # 到地形方框边的距离（像素）
    lo, hi = M, M + land.shape[0]
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
d = ImageDraw.Draw(img)
for k, r in enumerate((7, 15, 25, 38)):
    ring = ((dist > r - .8) & (dist < r + .8)).astype(np.uint8) * 255
    cs, _ = cv2.findContours(ring, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    a = 120 - k * 25
    for c in cs:
        if len(c) > 20:
            pts = c[::2, 0, :].astype(np.float32)
            for run in runs(pts, bdist(pts) > r + 4):
                d.line(run, fill=INK[:3] + (a,), width=1)

# 海岸线：粗墨线 + 内侧一道细线
cs, _ = cv2.findContours(full, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
for c in cs:
    if len(c) < 30:
        continue
    pts = c[:, 0, :].astype(np.float32)
    keep = bdist(pts) > 3
    pts += rng.normal(0, .6, pts.shape)
    for run in runs(pts[::2], keep[::2]):
        d.line(run, fill=INK, width=3)

# ---------- 山：高处按坡向画「人」字山形 + 阴影排线
def mountain(x, y, s, a=255):
    l, r, top = (x - s, y), (x + s, y), (x + s * .1, y - s * 1.25)
    d.line([l, top, r], fill=INK[:3] + (a,), width=2)
    for i in range(1, 5):   # 右坡阴影
        f = i / 5
        p = (top[0] + (r[0] - top[0]) * f, top[1] + (r[1] - top[1]) * f)
        d.line([p, (p[0] - s * .25, y)], fill=INK[:3] + (int(a * .6),), width=1)

ys, xs = np.mgrid[0:256:4, 0:256:4]
cand = []
for z0, x0 in zip(ys.ravel(), xs.ravel()):
    h = H[min(z0, 256), min(x0, 256)]
    if h > 56:
        cand.append((h, x0 + rng.uniform(-1.5, 1.5), z0 + rng.uniform(-1.5, 1.5)))
cand.sort(key=lambda c: -c[2])   # 先画北边（远处），南边的压在上面
for h, x0, z0 in cand:
    if rng.random() < .55:
        continue
    u, v = wp(x0, z0)
    mountain(u, v, 6 + (h - 56) * .35, 230)

# 丘陵：中等高度画小弧
for z0, x0 in zip(ys.ravel(), xs.ravel()):
    h = H[z0, x0]
    if 47 < h <= 56 and rng.random() < .35:
        u, v = wp(x0 + rng.uniform(-2, 2), z0 + rng.uniform(-2, 2))
        d.arc([u - 7, v - 5, u + 7, v + 5], 200, 340, fill=INK[:3] + (150,), width=1)

# ---------- 树林：用场景里真实的树位置
import zipfile
_proj = os.path.expanduser('~/Library/Application Support/AI World Creator/projects/project_lapv8fm0/scene.data')
if not os.path.exists(_proj):
    _proj = f'{ROOT}/editor_project/project_lapv8fm0/scene.data'
scene = json.loads(zipfile.ZipFile(_proj).read('SerializePcgData.json'))
roots = [n for n in scene['nodeTransformDatas'] if n['parentId'] == 0]
for n in roots:
    if n['nodeName'].startswith('pl_tree') or n['nodeName'].startswith('pl_bush'):
        u, v = wp(n['pos']['x'], n['pos']['z'])
        s = 4 if 'tree' in n['nodeName'] else 2.5
        d.ellipse([u - s, v - s * 1.4, u + s, v + s * .6], outline=INK[:3] + (200,), width=1)
        d.line([(u, v + s * .6), (u, v + s * 1.6)], fill=INK[:3] + (200,), width=1)

paper_img = Image.fromarray(np.clip(paper, 0, 255).astype(np.uint8)).convert('RGBA')


def fade(im):
    a = np.array(im).astype(np.float32)
    pp = np.array(paper_img).astype(np.float32)
    inside = np.zeros((W, W), np.uint8)
    inside[M + 6:W - M - 6, M + 6:W - M - 6] = 1
    dd = cv2.distanceTransform(inside, cv2.DIST_L2, 5)
    jitter = cv2.resize(cv2.GaussianBlur(rng.normal(0, 1, (W // 16, W // 16)).astype(np.float32), (0, 0), 1.5), (W, W)) * 18
    k = np.clip((dd + jitter - 4) / 38, 0, 1)[..., None]
    return Image.fromarray((a * k + pp * (1 - k)).astype(np.uint8))


img = fade(img)
d = ImageDraw.Draw(img)
clean = img.copy()

# ---------- 地名与地标
FONT = '/System/Library/Fonts/Supplemental/Songti.ttc'
f_big = ImageFont.truetype(FONT, 34, index=1)
f_sm = ImageFont.truetype(FONT, 28, index=1)
f_sea = ImageFont.truetype(FONT, 34, index=1)
f_title = ImageFont.truetype(FONT, 64, index=1)

POI = json.load(open(f'{OUT}/poi.json'))
for p in POI:
    u, v = wp(p['x'], p['z'])
    big = p.get('major')
    r = 7 if big else 4
    d.ellipse([u - r, v - r, u + r, v + r], fill=RED if p.get('red') else INK)
    if big:
        d.ellipse([u - r - 4, v - r - 4, u + r + 4, v + r + 4], outline=INK, width=2)
    f = f_big if big else f_sm
    dx, dy = p.get('dx', 12), p.get('dy', -12)
    d.text((u + dx, v + dy), p['name'], font=f, fill=INK, stroke_width=4, stroke_fill=(234, 221, 192))

for name, x, z in [('蚀 月 海', 236, 200), ('雾 湾', 225, 40), ('西 境 荒 原', 18, 240)]:
    u, v = wp(x, z)
    d.text((u, v), name, font=f_sea, fill=INK[:3] + (150,), anchor='mm')

# 罗盘
cx, cy, R = M + 70, W - M - 40, 52
d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=INK, width=2)
d.ellipse([cx - R + 8, cy - R + 8, cx + R - 8, cy + R - 8], outline=INK_SOFT, width=1)
for ang, L in ((0, 1.25), (90, 1.0), (180, 1.0), (270, 1.0)):
    a = np.radians(ang)
    tip = (cx + np.sin(a) * R * L, cy - np.cos(a) * R * L)
    l = (cx + np.sin(a - 1.57) * 9, cy - np.cos(a - 1.57) * 9)
    r = (cx + np.sin(a + 1.57) * 9, cy - np.cos(a + 1.57) * 9)
    d.polygon([tip, l, (cx, cy)], fill=INK)
    d.polygon([tip, r, (cx, cy)], outline=INK, fill=(236, 223, 196))
d.text((cx, cy - R * 1.25 - 16), '北', font=f_sm, fill=INK, anchor='mm')

d.text((W / 2, W - 60), '龍 眠 之 境', font=f_title, fill=INK, anchor='mm')

img.convert('RGB').save(f'{OUT}/map_base.png')
clean.convert('RGB').save(f'{OUT}/map_base_clean.png')
print('ok', W)
