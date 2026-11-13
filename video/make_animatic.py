#!/usr/bin/env python3
"""按拍点生成「动态分镜」视频：每个镜头一张简单画面 + 字幕 + 注释，配上原音乐，直接照着剪。
用法：python3 video/make_animatic.py <音乐文件>  ，video/龙眠之境_动态分镜.mp4
"""
import os, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = sys.argv[1]
SHOTS_DIR = f'{REPO}/video/ref'
W, H, FPS = 1280, 720, 24
END = 125.0
BAR = 2.34
T0 = 6.94
F = f'{REPO}/assets/fonts'
SERIF, KAI, HEAVY = f'{F}/SourceHanSerifCN-Heavy.otf', f'{F}/LXGWWenKai-Medium.otf', f'{F}/SourceHanSansCN-Heavy.ttf'
font = lambda p, s: ImageFont.truetype(p, int(s))

# (开始秒, 段落, 画面注释, 字幕, 画面类型, 参数)
S = [
    (0.00, '开场', '黑屏淡入：夜空漩涡，镜头缓慢下摇', '', 'sky', None),
    (6.94, '开场', '主题进入：城堡剪影 + 标题出现（这一刀要准）', '', 'img', 'title'),
    (11.62, '开场', '全岛俯瞰，慢推', '', 'img', 'map'),
    (16.30, '故事书', '故事书翻开 · 第一页「蚀月」', '天空裂开了一道口子', 'img', 'book1'),
    (20.98, '故事书', '翻页 · 「墨曜」', '它用自己的梦，把裂隙缝上了', 'img', 'book1'),
    (25.66, '故事书', '翻页 · 「龙魂之卵」', '魂在蛋里，等一个人', 'img', 'book3'),
    (30.34, '地图', '地图展开，印章每两拍盖一个（共四个）', '二十二处地点', 'img', 'map'),
    (35.02, '誓约', '职业页：骑士旗亮', '剑 誓', 'img', 'class'),
    (37.36, '誓约', '职业页：法师旗亮', '星 誓', 'img', 'class'),
    (39.70, '誓约', '职业页：游侠旗亮', '风 誓', 'img', 'class'),
    (42.04, '三分屏', '音乐加厚，三分屏切入：三人普攻', '', 'split3', ('普攻', '普攻', '普攻')),
    (46.72, '三分屏', '三分屏：一技能', '', 'split3', ('守护震波', '星火爆裂', '月羽连射')),
    (51.40, '三分屏', '三分屏：二技能', '', 'split3', ('回旋斩', '霜星禁锢', '贯晶箭')),
    (56.08, '三分屏', '三分屏：同时蓄力大招，画面慢慢放大', '', 'split3', ('蓄力…', '蓄力…', '蓄力…')),
    (60.76, '夜战', '全曲最响：分屏炸开成全屏 · 陨星砸地（加一帧白闪）', '', 'card', ('陨星裁决', (120, 60, 200))),
    (63.10, '夜战', '巨剑裁决劈下', '', 'card', ('巨剑裁决', (200, 150, 60))),
    (65.44, '夜战', '万箭齐下', '', 'card', ('万箭齐下', (70, 170, 120))),
    (67.78, '夜战', '夜里魔法阵全景，影灵首领扑来', '', 'img', 'fight'),
    (70.12, '夜战', '影灵散成月辉光点', '', 'card', ('月辉', (150, 150, 220))),
    (72.46, '夜战', '天亮，阳光扫过麦田', '白天，这片土地属于你', 'card', ('天亮 · 麦田', (210, 170, 70))),
    (74.80, '快切', '快切开始（硬切，不加转场）：骑马穿麦田 ‖ 帆船出海', '', 'split2', ('骑马', '航海')),
    (77.14, '快切', '飞毯环游', '', 'card', ('飞毯', (90, 130, 200))),
    (78.31, '快切', '采蘑菇', '', 'card', ('采蘑菇', (170, 70, 60))),
    (79.48, '快切', '取羊毛', '', 'card', ('取羊毛', (200, 200, 190))),
    (80.65, '快切', '月见花海', '', 'card', ('花海', (150, 110, 210))),
    (81.82, '快切', '女巫递药水', '', 'card', ('女巫药水', (90, 160, 90))),
    (82.99, '快切', '变成羊', '', 'card', ('变羊', (220, 210, 200))),
    (84.16, '快切', '变大', '', 'card', ('变大', (210, 120, 60))),
    (85.33, '快切', '变小', '', 'card', ('变小', (60, 150, 190))),
    (86.50, '快切', '在蘑菇上蹦', '', 'card', ('蘑菇蹦跳', (190, 80, 120))),
    (87.67, '快切', '烤蘑菇出锅，吃下去画面眩晕（转场）', '', 'card', ('烤蘑菇 · 眩晕', (150, 80, 200))),
    (88.84, '城堡', '转段、放缓：城堡正门仰拍', '', 'card', ('城堡正门', (70, 70, 110))),
    (91.18, '城堡', '王座厅', '', 'card', ('王座厅', (110, 80, 60))),
    (93.52, '城堡', '书库，翻开手稿', '', 'card', ('书库手稿', (150, 120, 80))),
    (95.86, '城堡', '契碑特写', '魂归其身，身载其骑', 'card', ('契碑', (90, 90, 100))),
    (98.20, '龙魂', '祭坛全景，三根柱子亮起', '', 'card', ('唤龙祭坛', (80, 110, 160))),
    (100.54, '龙魂', '龙蛋抖动', '', 'img', 'book3'),
    (102.88, '龙魂', '魂光升起', '', 'card', ('魂光升起', (120, 200, 230))),
    (105.22, '龙魂', '魂光飞向雪山', '', 'card', ('飞向雪山', (170, 200, 230))),
    (107.56, '龙魂', '雪山上的龙睁眼', '', 'card', ('龙睁眼', (60, 40, 110))),
    (109.90, '龙魂', '龙振翅起飞', '', 'card', ('起飞', (90, 60, 150))),
    (112.24, '唤龙', '最后一次上扬：龙从雪山俯冲飞向祭坛，镜头跟拍', '', 'card', ('俯冲', (110, 70, 170))),
    (117.40, '四连击', '第一击：龙落地（硬切）', '', 'card', ('落地', (230, 90, 60))),
    (117.98, '四连击', '第二击：骑上龙背', '', 'card', ('骑上', (230, 140, 60))),
    (118.56, '四连击', '第三击：腾空', '', 'card', ('腾空', (230, 190, 80))),
    (119.16, '四连击', '第四击：飞越全岛，飞向漩涡', '', 'card', ('飞越全岛', (120, 90, 220))),
    (121.60, '收尾', '音乐收尾：黑屏，标题再现，淡出', '灯还亮着', 'end', None),
]
KEY = [6.94, 42.04, 60.76, 74.80, 88.84, 117.40, 117.98, 118.56, 119.16]


def load(name):
    for ext in ('jpg', 'png'):
        p = f'{SHOTS_DIR}/{name}.{ext}'
        if os.path.exists(p):
            im = Image.open(p).convert('RGB')
            k = max(W / im.size[0], H / im.size[1])
            im = im.resize((int(im.size[0] * k) + 1, int(im.size[1] * k) + 1), Image.LANCZOS)
            x, y = (im.size[0] - W) // 2, (im.size[1] - H) // 2
            return im.crop((x, y, x + W, y + H))
    return None


def gradient(col, seed=0):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((xx - W / 2) / W, (yy - H * .45) / H)
    k = np.clip(1 - r * 1.5, 0, 1)[..., None]
    base = np.array(col, np.float32)
    rng = np.random.default_rng(seed)
    n = cv2.resize(rng.normal(0, 1, (H // 40, W // 40)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)[..., None]
    img = base * (.18 + .75 * k) + n * 7
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def centered(d, text, y, f, fill, stroke=4):
    d.text((W / 2, y), text, font=f, fill=fill, anchor='mm', stroke_width=stroke, stroke_fill=(10, 8, 12))


def base_frame(i):
    t, sec, note, sub, kind, arg = S[i]
    if kind == 'img':
        im = load(arg) or gradient((70, 60, 110), i)
        im = Image.blend(im, Image.new('RGB', (W, H), (8, 6, 12)), .18)
    elif kind == 'sky':
        im = gradient((60, 40, 130), i)
        d = ImageDraw.Draw(im)
        rng = np.random.default_rng(3)
        for _ in range(160):
            x, y, s = rng.uniform(0, W), rng.uniform(0, H * .8), rng.uniform(.6, 2)
            d.ellipse([x - s, y - s, x + s, y + s], fill=(230, 230, 255))
        for k in range(3):
            r = 120 + k * 60
            d.arc([W / 2 - r, 150 - r * .45, W / 2 + r, 150 + r * .45], 20 + k * 40, 300 + k * 30, fill=(150, 120, 255), width=5)
    elif kind == 'card':
        im = gradient(arg[1], i)
        d = ImageDraw.Draw(im)
        centered(d, arg[0], H * .42, font(SERIF, 110), (250, 244, 228), 6)
    elif kind == 'split3':
        im = Image.new('RGB', (W, H), (0, 0, 0))
        cols = [(190, 70, 50), (110, 80, 210), (60, 160, 110)]
        names = ['骑士', '法师', '游侠']
        pw = (W - 8) // 3
        for k in range(3):
            g = gradient(cols[k], i * 3 + k).resize((pw, H))
            im.paste(g, (k * (pw + 4), 0))
            d = ImageDraw.Draw(im)
            cx = k * (pw + 4) + pw / 2
            d.text((cx, H * .32), names[k], font=font(SERIF, 70), fill=(250, 244, 228), anchor='mm', stroke_width=5, stroke_fill=(10, 8, 12))
            d.text((cx, H * .47), arg[k], font=font(KAI, 44), fill=(255, 226, 150), anchor='mm', stroke_width=4, stroke_fill=(10, 8, 12))
    elif kind == 'split2':
        im = Image.new('RGB', (W, H), (0, 0, 0))
        cols = [(200, 160, 60), (60, 130, 190)]
        pw = (W - 4) // 2
        for k in range(2):
            g = gradient(cols[k], i * 3 + k).resize((pw, H))
            im.paste(g, (k * (pw + 4), 0))
            d = ImageDraw.Draw(im)
            d.text((k * (pw + 4) + pw / 2, H * .42), arg[k], font=font(SERIF, 100), fill=(250, 244, 228), anchor='mm', stroke_width=6, stroke_fill=(10, 8, 12))
    else:
        im = Image.new('RGB', (W, H), (0, 0, 0))
        d = ImageDraw.Draw(im)
        centered(d, '龙 眠 之 境', H * .40, font(HEAVY, 120), (226, 56, 30), 8)
    d = ImageDraw.Draw(im, 'RGBA')
    # 顶部：镜号、段落、切点
    d.rectangle([0, 0, W, 54], fill=(0, 0, 0, 150))
    d.text((24, 27), f'镜 {i + 1:02d} / {len(S)}', font=font(HEAVY, 26), fill=(255, 255, 255), anchor='lm')
    d.text((210, 27), f'【{sec}】', font=font(KAI, 28), fill=(255, 214, 130), anchor='lm')
    mm, ss = int(t // 60), t % 60
    d.text((W - 24, 27), f'切点 {mm}:{ss:05.2f}', font=font(HEAVY, 26), fill=(255, 120, 100) if t in KEY else (255, 255, 255), anchor='rm')
    # 字幕（成片里要出现的字）
    if sub and kind != 'end':
        centered(d, sub, H - 205, font(SERIF, 54), (255, 255, 255), 5)
    elif sub:
        centered(d, sub, H * .62, font(KAI, 50), (240, 232, 214), 4)
    # 注释条（只给剪辑的人看）
    d.rectangle([0, H - 150, W, H - 62], fill=(0, 0, 0, 175))
    d.text((24, H - 128), '画面', font=font(HEAVY, 24), fill=(120, 210, 255), anchor='lm')
    d.text((90, H - 128), note, font=font(HEAVY, 27), fill=(245, 245, 245), anchor='lm')
    dur = (S[i + 1][0] if i + 1 < len(S) else END) - t
    d.text((24, H - 88), '时长', font=font(HEAVY, 24), fill=(120, 210, 255), anchor='lm')
    d.text((90, H - 88), f'{dur:.2f} 秒' + ('　·　字幕：' + sub if sub else '　·　无字幕'), font=font(HEAVY, 23), fill=(215, 215, 215), anchor='lm')
    return np.array(im)[..., ::-1].copy()


bases = [base_frame(i) for i in range(len(S))]
starts = [s[0] for s in S]
bars = [T0 + k * BAR for k in range(int((121.7 - T0) / BAR) + 1)]
ff = imageio_ffmpeg.get_ffmpeg_exe()
out = f'{REPO}/video/龙眠之境_动态分镜.mp4'
cmd = [ff, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
       '-i', AUDIO, '-t', str(END), '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', out]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
fnt = cv2.FONT_HERSHEY_SIMPLEX
for n in range(int(END * FPS)):
    t = n / FPS
    i = max(k for k in range(len(S)) if starts[k] <= t + 1e-6)
    fr = bases[i].copy()
    age = t - starts[i]
    if i == 0:                                   # 开场渐入
        fr = (fr * min(1, t / 5)).astype(np.uint8)
    if S[i][4] == 'end':                         # 结尾淡出
        fr = (fr * max(0, min(1, (END - t) / 2.2))).astype(np.uint8)
    if age < .12 and i > 0:                      # 每一刀：一闪白边，重点切点整屏白闪
        a = (1 - age / .12)
        if starts[i] in KEY:
            fr = cv2.addWeighted(fr, 1 - .55 * a, np.full_like(fr, 255), .55 * a, 0)
        cv2.rectangle(fr, (0, 0), (W - 1, H - 1), (255, 255, 255), int(10 * a) + 1)
    # 底部时间轴：小节线、镜头切点、当前位置
    y0 = H - 46
    cv2.rectangle(fr, (0, H - 62), (W, H), (14, 12, 18), -1)
    X = lambda tt: int(20 + (W - 40) * tt / END)
    cv2.line(fr, (20, y0 + 14), (W - 20, y0 + 14), (90, 90, 100), 2)
    for b in bars:
        cv2.line(fr, (X(b), y0 + 8), (X(b), y0 + 20), (120, 120, 130), 1)
    for s in starts[1:]:
        key = s in KEY
        cv2.line(fr, (X(s), y0 + (0 if key else 4)), (X(s), y0 + 28 - (0 if key else 4)), (90, 110, 255) if key else (230, 230, 230), 2 if key else 1)
    cv2.rectangle(fr, (20, y0 + 11), (X(t), y0 + 17), (60, 200, 255), -1)
    cv2.circle(fr, (X(t), y0 + 14), 7, (255, 255, 255), -1)
    # 小节脉冲：每个小节线亮一下，方便看拍子
    ph = ((t - T0) % BAR) if t >= T0 and t < 121.7 else 9
    if ph < .15:
        cv2.circle(fr, (W - 40, 96), int(16 * (1 - ph / .15)) + 6, (60, 200, 255), -1)
    cv2.putText(fr, f'{int(t // 60)}:{t % 60:05.2f}', (24, 100), fnt, 1.0, (0, 0, 0), 5, cv2.LINE_AA)
    cv2.putText(fr, f'{int(t // 60)}:{t % 60:05.2f}', (24, 100), fnt, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
    p.stdin.write(fr.tobytes())
p.stdin.close()
p.wait()
print('ok', out, os.path.getsize(out) // 1024, 'KB')
