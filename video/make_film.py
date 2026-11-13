#!/usr/bin/env python3
"""成片合成：按拍点把运镜序列帧、界面合成动画、玩法录屏拼起来，配上音乐。
用法：python3 video/make_film.py <音乐文件>   → video/龙眠之境_宣传片.mp4

每个镜头的画面来源（按顺序找，找到就用）：
  1. video/clips/<镜头键>.mp4|mov   —— 你录的玩法素材（带声音的话会压在音乐下面）
  2. video/frames/<序列名>/          —— film.py 逐帧拍的运镜
  3. 程序合成（故事书 / 地图 / 职业页 / 片尾）
  4. 都没有 → 占位卡，写着「待补素材」
"""
import glob, json, os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = sys.argv[1]
W, H, FPS = 1920, 1080, 24
END = 125.0
F = f'{REPO}/assets/fonts'
SERIF, KAI, HEAVY = f'{F}/SourceHanSerifCN-Heavy.otf', f'{F}/LXGWWenKai-Medium.otf', f'{F}/SourceHanSansCN-Heavy.ttf'
font = lambda p, s: ImageFont.truetype(p, int(s))
UI2 = f'{REPO}/assets/ui2'
L = json.load(open(f'{UI2}/layout.json'))
ATL = {}

# (开始秒, 镜头键, 字幕, 来源, 参数)
S = [
    (0.00, 'sky', '', 'seq', 'sky_tilt'),
    (6.94, 'title', '', 'title', 'title_bg'),
    (11.62, 'island', '', 'seq', 'island'),
    (16.30, 'book1', '天空裂开了一道口子', 'book', (1, 'L')),
    (20.98, 'book2', '它用自己的梦，把裂隙缝上了', 'book', (1, 'R')),
    (25.66, 'book3', '魂在蛋里，等一个人', 'book', (3, 'R')),
    (30.34, 'map', '二十二处地点', 'map', None),
    (35.02, 'class1', '剑 誓', 'class', 'melee'),
    (37.36, 'class2', '星 誓', 'class', 'mage'),
    (39.70, 'class3', '风 誓', 'class', 'ranged'),
    (42.04, 'split_a', '', 'split3', ('melee_attack', 'mage_attack', 'ranged_attack')),
    (46.72, 'split_b', '', 'split3', ('melee_skill1', 'mage_skill1', 'ranged_skill1')),
    (51.40, 'split_c', '', 'split3', ('melee_skill2', 'mage_skill2', 'ranged_skill2')),
    (56.08, 'split_d', '', 'split3', ('melee_charge', 'mage_charge', 'ranged_charge')),
    (60.76, 'ult_mage', '', 'clip', '陨星裁决'),
    (63.10, 'ult_melee', '', 'clip', '巨剑裁决'),
    (65.44, 'ult_ranged', '', 'clip', '万箭齐下'),
    (67.78, 'arena', '', 'clip', '魔法阵夜战'),
    (70.12, 'moon', '', 'clip', '影灵散成月辉'),
    (72.46, 'dawn', '白天，这片土地属于你', 'clip', '天亮 · 麦田'),
    (74.80, 'ride_sail', '', 'split2', ('horse', 'boat')),
    (77.14, 'carpet', '', 'clip', '飞毯'),
    (78.31, 'mushroom', '', 'clip', '采蘑菇'),
    (79.48, 'wool', '', 'clip', '取羊毛'),
    (80.65, 'flowers', '', 'clip', '花海'),
    (81.82, 'witch', '', 'clip', '女巫药水'),
    (82.99, 'sheep', '', 'clip', '变羊'),
    (84.16, 'grow', '', 'clip', '变大'),
    (85.33, 'shrink', '', 'clip', '变小'),
    (86.50, 'bounce', '', 'clip', '蘑菇蹦跳'),
    (87.67, 'roast', '', 'clip', '烤蘑菇 · 眩晕'),
    (88.84, 'castle', '', 'seq', 'castle'),
    (93.52, 'library', '', 'clip', '书库手稿'),
    (95.86, 'stele', '魂归其身，身载其骑', 'clip', '契碑'),
    (98.20, 'altar', '', 'seq', 'altar'),
    (100.54, 'egg', '', 'clip', '龙蛋抖动'),
    (102.88, 'soul', '', 'clip', '魂光升起'),
    (105.22, 'soul_fly', '', 'clip', '魂光飞向雪山'),
    (107.56, 'dragon', '', 'seq', 'dragon'),
    (112.24, 'dive', '', 'clip', '龙俯冲飞向祭坛'),
    (117.40, 'land', '', 'clip', '落地'),
    (117.98, 'mount', '', 'clip', '骑上'),
    (118.56, 'rise', '', 'clip', '腾空'),
    (119.16, 'ending', '', 'seq', 'ending'),
    (121.60, 'end', '灯还亮着', 'end', None),
]
KEY = [6.94, 42.04, 60.76, 74.80, 88.84, 117.40, 117.98, 118.56, 119.16]
starts = [s[0] for s in S]


def sprite(name):
    b, x, y, w, h = L['atlas'][name]
    if b not in ATL:
        ATL[b] = Image.open(f'{UI2}/png/atlas{b + 1}.png').convert('RGBA')
    return ATL[b].crop((x, y, x + w, y + h))


def fit(im, w, h):
    k = max(w / im.shape[1], h / im.shape[0])
    im = cv2.resize(im, (int(im.shape[1] * k) + 1, int(im.shape[0] * k) + 1), interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_LINEAR)
    x, y = (im.shape[1] - w) // 2, (im.shape[0] - h) // 2
    return im[y:y + h, x:x + w]


SEQ = {}


def seq_frame(name, u):
    """序列帧（8fps 拍的）按进度 u∈[0,1] 取帧，相邻两帧线性混合。"""
    if name not in SEQ:
        files = sorted(glob.glob(f'{REPO}/video/frames/{name}/*.jpg'))
        SEQ[name] = [cv2.imread(f) for f in files]
    fr = SEQ[name]
    if not fr:
        return None
    f = u * (len(fr) - 1)
    i = min(int(f), len(fr) - 1)
    j = min(i + 1, len(fr) - 1)
    t = f - i
    a = fr[i] if t < .02 else cv2.addWeighted(fr[i], 1 - t, fr[j], t, 0)
    return cv2.resize(a, (W, H)) if a.shape[1] != W else a


CLIPS = {}


def clip_frame(key, age):
    if key not in CLIPS:
        c = None
        for ext in ('mp4', 'mov', 'MP4', 'MOV'):
            p = f'{REPO}/video/clips/{key}.{ext}'
            if os.path.exists(p):
                c = cv2.VideoCapture(p)
        CLIPS[key] = c
    c = CLIPS[key]
    if c is None:
        return None
    c.set(cv2.CAP_PROP_POS_MSEC, age * 1000)
    ok, f = c.read()
    return fit(f, W, H) if ok else None


def pil2cv(im):
    return np.array(im.convert('RGB'))[..., ::-1].copy()


def paste(base, im, cx, cy, scale=1.0, alpha=1.0):
    """把 RGBA 小图按中心点贴到 PIL 底图上。"""
    if scale != 1.0:
        im = im.resize((max(1, int(im.size[0] * scale)), max(1, int(im.size[1] * scale))), Image.LANCZOS)
    if alpha < 1:
        a = im.getchannel('A').point(lambda v: int(v * alpha))
        im = im.copy(); im.putalpha(a)
    base.alpha_composite(im, (int(cx - im.size[0] / 2), int(cy - im.size[1] / 2)))


def placeholder(label, seed):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((xx - W / 2) / W, (yy - H * .45) / H)
    rng = np.random.default_rng(seed)
    col = np.array([40 + rng.integers(60), 40 + rng.integers(60), 70 + rng.integers(80)], np.float32)
    img = Image.fromarray(np.clip(col * (.2 + .7 * np.clip(1 - r * 1.5, 0, 1)[..., None]), 0, 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(img)
    d.text((W / 2, H * .44), label, font=font(SERIF, 130), fill=(250, 244, 228), anchor='mm', stroke_width=7, stroke_fill=(10, 8, 12))
    d.text((W / 2, H * .60), '待补素材', font=font(KAI, 54), fill=(255, 214, 130), anchor='mm', stroke_width=4, stroke_fill=(10, 8, 12))
    return pil2cv(img)


BG = {}


def dim_bg(name='title_bg'):
    """界面段落的底：一帧运镜画面，虚化压暗。"""
    if name not in BG:
        f = seq_frame(name, .6)
        if f is None:
            f = np.zeros((H, W, 3), np.uint8); f[:] = (30, 16, 22)
        f = cv2.GaussianBlur(f, (0, 0), 14)
        BG[name] = Image.fromarray((f[..., ::-1] * .38).astype(np.uint8)).convert('RGBA')
    return BG[name].copy()


BOOK = Image.open(f'{REPO}/assets/ui/png/ui_book.png').convert('RGBA')
BH = 900; BW = int(BH * BOOK.size[0] / BOOK.size[1])
BOOK = BOOK.resize((BW, BH), Image.LANCZOS)
PAGES = {k: Image.open(f'{UI2}/png/pages{k}.png').convert('RGBA') for k in (1, 2, 3)}
PL = (.0625, .058824, .433594, .876471)     # x, y(自下), w, h —— 与游戏里一致
PR = (.503906, .058824, .433594, .876471)


def book_base():
    im = dim_bg()
    im.alpha_composite(BOOK, ((W - BW) // 2, (H - BH) // 2 - 10))
    return im


def put_page(im, spread, side, alpha=1.0):
    pg = PAGES[spread]
    half = pg.size[0] // 2
    src = pg.crop((0, 0, half, pg.size[1])) if side == 'L' else pg.crop((half, 0, pg.size[0], pg.size[1]))
    r = PL if side == 'L' else PR
    w, h = int(r[2] * BW), int(r[3] * BH)
    src = src.resize((w, h), Image.LANCZOS)
    x = (W - BW) // 2 + int(r[0] * BW)
    y = (H - BH) // 2 - 10 + int((1 - r[1] - r[3]) * BH)
    if alpha < 1:
        a = src.getchannel('A').point(lambda v: int(v * alpha)); src.putalpha(a)
    im.alpha_composite(src, (x, y))


def book_frame(arg, age, idx):
    spread, focus = arg
    im = book_base()
    a = min(1, age / .35)
    put_page(im, spread, 'L', a if (idx == 3 or focus == 'L') and idx != 4 else 1)
    put_page(im, spread, 'R', a if idx != 4 or True else 1)
    fr = pil2cv(im)
    # 慢慢推向正在讲的那一页
    z = 1.0 + .10 * min(1, age / 4.68)
    cx = W / 2 + (-150 if focus == 'L' else 150) * min(1, age / 4.68)
    M = np.float32([[z, 0, (1 - z) * cx], [0, z, (1 - z) * H / 2]])
    return cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_LINEAR)


MAP = Image.open(f'{UI2}/png/map.jpg').convert('RGBA').resize((1000, 1000), Image.LANCZOS)
STAMP_AT = [0.0, 1.17, 2.34, 3.51]
STAMP_POI = ['spawn', 'wheat', 'village', 'castle', 'altar', 'dragon_peak']


def map_frame(arg, age, idx):
    im = dim_bg()
    k = .9 + .1 * min(1, age / .4)
    m = MAP if k >= 1 else MAP.resize((int(1000 * k), int(1000 * k)), Image.LANCZOS)
    ox, oy = (W - m.size[0]) // 2, (H - m.size[1]) // 2
    im.alpha_composite(m, (ox, oy))
    mp = L['map']
    st = sprite('stamp')
    pois = {p['id']: p for p in L['poi']}
    for i, t0 in enumerate(STAMP_AT + [4.1, 4.4]):
        if age < t0:
            continue
        p = pois[STAMP_POI[i]]
        u = (mp['M'] + p['x'] * mp['S']) / mp['size']
        v = (mp['M'] + (256 - p['z']) * mp['S']) / mp['size']
        pop = 1 + 1.2 * max(0, 1 - (age - t0) / .18)
        paste(im, st, ox + u * m.size[0], oy + v * m.size[1], .9 * pop)
    return pil2cv(im)


def class_frame(kind, age, idx):
    im = book_base()
    cx0, cy0 = W / 2, H / 2 - 10
    lx, rx = cx0 - 299, cx0 + 299
    paste(im, sprite('cls_title'), lx, cy0 - 300)
    order = ['melee', 'mage', 'ranged']
    cur = order.index(kind)
    for i, k in enumerate(order):
        x = lx + (i - 1) * 188
        sel = i == cur
        s = 176 / 300 * (1.12 if sel else 1.0)
        if sel:
            paste(im, sprite('card_glow'), x, cy0 - 40 - 13, 200 / 340 * 1.12, min(1, age / .2))
        paste(im, sprite(f'card_{k}'), x, cy0 - 40, s, 1.0 if (sel or i < cur) else .55)
    paste(im, sprite(f'cls_{kind}'), rx, cy0 - 66, 1.0, min(1, age / .3))
    paste(im, sprite('btn_sign'), rx, cy0 + 296, 380 / 416)
    paste(im, sprite('cls_foot'), lx, cy0 + 268)
    return pil2cv(im)


TITLE = Image.open(f'{REPO}/assets/ui/png/ui_title.png').convert('RGBA')


def title_frame(arg, age, idx):
    bg = seq_frame(arg, min(1, age / 4.68))
    if bg is None:
        bg = np.zeros((H, W, 3), np.uint8)
    im = Image.fromarray(bg[..., ::-1]).convert('RGBA')
    k = int(age * 8) % 3                       # 标题三帧抖动，和游戏里一样每秒 8 帧
    t = TITLE.crop((0, k * 300, 1024, k * 300 + 300))
    paste(im, t, W / 2, H / 2 - 60, 1240 / 1024 * (1 + .03 * min(1, age / 4.68)), min(1, age / .25))
    return pil2cv(im)


def end_frame(arg, age, idx):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    t = TITLE.crop((0, 0, 1024, 300))
    paste(im, t, W / 2, H / 2 - 70, 1.0, min(1, age / .5))
    d = ImageDraw.Draw(im)
    a = int(255 * min(1, max(0, (age - .5) / .6)))
    d.text((W / 2, H / 2 + 150), '灯 还 亮 着', font=font(KAI, 60), fill=(240, 232, 214, a), anchor='mm')
    return pil2cv(im)


PH = {}


def shot_frame(i, age, dur):
    t0, key, sub, kind, arg = S[i]
    f = clip_frame(key, age)
    if f is None:
        if kind == 'seq':
            f = seq_frame(arg, min(1, age / dur))
        elif kind == 'title':
            f = title_frame(arg, age, i)
        elif kind == 'book':
            f = book_frame(arg, age, i)
        elif kind == 'map':
            f = map_frame(arg, age, i)
        elif kind == 'class':
            f = class_frame(arg, age, i)
        elif kind == 'end':
            f = end_frame(arg, age, i)
        elif kind in ('split3', 'split2'):
            n = len(arg)
            pw = (W - 6 * (n - 1)) // n
            f = np.zeros((H, W, 3), np.uint8)
            names = {'melee': '骑士', 'mage': '法师', 'ranged': '游侠', 'horse': '骑马', 'boat': '航海'}
            for k, ck in enumerate(arg):
                c = clip_frame(ck, age)
                if c is None:
                    if ck not in PH:
                        PH[ck] = placeholder(names.get(ck.split('_')[0], ck), hash(ck) % 1000)
                    c = PH[ck]
                x = k * (pw + 6)
                # 取素材中间一条
                cx = (c.shape[1] - pw) // 2
                f[:, x:x + pw] = c[:, cx:cx + pw]
    if f is None:
        if key not in PH:
            PH[key] = placeholder(arg if isinstance(arg, str) else key, i)
        f = PH[key]
    return f


def subtitle(fr, text, age, low=False):
    if not text:
        return fr
    im = Image.fromarray(fr[..., ::-1]).convert('RGBA')
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    a = int(255 * min(1, age / .3))
    d.text((W / 2, H - (46 if low else 120)), text, font=font(SERIF, 46 if low else 62), fill=(255, 255, 255, a), anchor='mm', stroke_width=5, stroke_fill=(10, 8, 12, a))
    im.alpha_composite(ov)
    return pil2cv(im)


ff = imageio_ffmpeg.get_ffmpeg_exe()
out = f'{REPO}/video/龙眠之境_宣传片.mp4'
cmd = [ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
       '-i', AUDIO, '-t', str(END), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', out]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
missing = set()
for n in range(int(END * FPS)):
    t = n / FPS
    i = max(k for k in range(len(S)) if starts[k] <= t + 1e-6)
    age = t - starts[i]
    dur = (starts[i + 1] if i + 1 < len(S) else END) - starts[i]
    fr = shot_frame(i, age, dur)
    if S[i][3] not in ('end', 'book', 'map', 'class', 'title'):
        fr = subtitle(fr, S[i][2], age)
    elif S[i][3] in ('book', 'map', 'class'):
        fr = subtitle(fr, S[i][2], age, True)
    if i == 0:
        fr = (fr * min(1, t / 4.5)).astype(np.uint8)
    if S[i][3] == 'end':
        fr = (fr * max(0, min(1, (END - t) / 2.0))).astype(np.uint8)
    if age < .1 and starts[i] in KEY:              # 重点切点一帧白闪
        a = .6 * (1 - age / .1)
        fr = cv2.addWeighted(fr, 1 - a, np.full_like(fr, 255), a, 0)
    p.stdin.write(np.ascontiguousarray(fr).tobytes())
p.stdin.close(); p.wait()
todo = [f'{s[1]}（{s[4] if isinstance(s[4], str) else "/".join(s[4])}）' for s in S if s[3] in ('clip', 'split3', 'split2') and CLIPS.get(s[1]) is None]
print('ok', out, os.path.getsize(out) // 1024, 'KB')
print('待补素材：', len(todo))
