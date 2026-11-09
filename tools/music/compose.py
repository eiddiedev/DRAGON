#!/usr/bin/env python3
"""龙眠之境主题曲：原创史诗管弦风。D 小调，6/8 拍的大提琴律动铺底，圆号主题层层加厚。
旋律是原创的，不引用任何现有影视配乐。用法：compose.py <score.json> """
import json
import sys

BPM_E = 244  # 每分钟八分音符数（6/8，附点四分≈81）
E_ = 60 / BPM_E
BAR = 6 * E_
tracks = {}


def tr(name, program, drum=False):
    if name not in tracks:
        tracks[name] = dict(name=name, program=program, drum=drum, notes=[])
    return tracks[name]['notes']


def note(name, program, bar, eighth, length, midi, vel, drum=False):
    tr(name, program, drum).append([(bar * 6 + eighth) * E_, length * E_, midi, vel])


# 音高
N = {n: i for i, n in enumerate(['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'])}


def m(s):
    return N[s[:-1]] + 12 * (int(s[-1]) + 1)


# 和声（每两小节）：Dm Bb F C / Dm Gm Bb A
PROG = [('D', 'F', 'A'), ('Bb', 'D', 'F'), ('F', 'A', 'C'), ('C', 'E', 'G'), ('D', 'F', 'A'), ('G', 'Bb', 'D'), ('Bb', 'D', 'F'), ('A', 'C#', 'E')]
ROOT = {'D': 38, 'Bb': 34, 'F': 41, 'C': 36, 'G': 43, 'A': 33}


def cello_ostinato(bar, chord, vel, inst='cello'):
    """6/8 的驱动音型：长-短-短-长-短-短，落在根音和五度上，是自己写的型。"""
    r = ROOT[chord[0]]
    fifth = r + 7
    third = r + (3 if chord[0] in ('D', 'G') else 4)
    pat = [(0, 2, r, 1.0), (2, 1, fifth, .72), (3, 2, r + 12, .9), (5, 1, third + 12, .7)]
    for e, l, p, k in pat:
        note(inst, 42, bar, e, l * .92, p, int(vel * k))


def pad(bar, bars, chord, vel, octave=4, name='strings', program=48):
    for c in chord:
        p = N[c] + 12 * (octave + 1)
        note(name, program, bar, 0, bars * 6 - .2, p, vel)


# 主题（小节偏移, 八分位置, 长度, 音）—— 原创旋律：先四度上跳，再级进下行收在属音
THEME_A = [(0, 0, 4, 'A4'), (0, 4, 2, 'D5'), (1, 0, 3, 'C5'), (1, 3, 1, 'Bb4'), (1, 4, 2, 'A4'),
           (2, 0, 4, 'F4'), (2, 4, 2, 'G4'), (3, 0, 6, 'A4'),
           (4, 0, 4, 'C5'), (4, 4, 2, 'F5'), (5, 0, 3, 'E5'), (5, 3, 1, 'D5'), (5, 4, 2, 'C5'),
           (6, 0, 4, 'G4'), (6, 4, 2, 'A4'), (7, 0, 6, 'G4')]
THEME_B = [(0, 0, 3, 'D5'), (0, 3, 3, 'F5'), (1, 0, 4, 'A5'), (1, 4, 2, 'G5'),
           (2, 0, 3, 'Bb5'), (2, 3, 3, 'A5'), (3, 0, 4, 'G5'), (3, 4, 2, 'F5'),
           (4, 0, 3, 'F5'), (4, 3, 3, 'E5'), (5, 0, 4, 'D5'), (5, 4, 2, 'C#5'), (6, 0, 6, 'D5'), (7, 0, 6, 'A4')]


def theme(start, T, name, program, vel, transpose=0):
    for b, e, l, p in T:
        note(name, program, start + b, e, l * .96, m(p) + transpose, vel)


def timpani(bar, v, pattern=(0, 3)):
    r = 38
    for e in pattern:
        note('timp', 47, bar, e, 1.5, r, v)


def taiko(bar, v):
    # 低沉战鼓
    for e, k in ((0, 1.0), (3, .8), (4, .55), (5, .7)):
        note('taiko', 116, bar, e, 2, 36, int(v * k))


def cymbal(bar, v):
    note('cym', 0, bar, 0, 6, 49, v, drum=True)


SEC = []
bar = 0
# ---- 引子：低音铺底，竖琴般的琶音，冷冽（8 小节）
for i in range(8):
    c = PROG[0] if i < 4 else PROG[1]
    if i % 2 == 0:
        pad(bar + i, 2, c, 58, 3, 'basses', 43)
    if i >= 2:
        cello_ostinato(bar + i, c, 62 + i * 3)
    if i >= 4:
        for k, e in enumerate((0, 1, 2, 3, 4, 5)):
            pc = c[k % 3]
            note('harp', 46, bar + i, e, 3, N[pc] + 12 * (5 + (k > 2)), 54)
    if i == 6:
        timpani(bar + i, 60, (0,))
bar += 8
# ---- A 段：圆号独奏主题（8 小节）
for i in range(8):
    c = PROG[i]
    cello_ostinato(bar + i, c, 84)
    pad(bar + i, 1, c, 54, 3, 'basses', 43)
    pad(bar + i, 1, c, 52, 4)
    if i % 2 == 0:
        timpani(bar + i, 58, (0,))
theme(bar, THEME_A, 'horn', 60, 96)
bar += 8
# ---- A' 段：小提琴接过主题，圆号八度，战鼓进入（8 小节）
for i in range(8):
    c = PROG[i]
    cello_ostinato(bar + i, c, 94)
    pad(bar + i, 1, c, 70, 3, 'basses', 43)
    pad(bar + i, 1, c, 66, 4)
    taiko(bar + i, 78)
    timpani(bar + i, 70)
theme(bar, THEME_A, 'violin', 48, 96, 12)
theme(bar, THEME_A, 'horn', 60, 90)
cymbal(bar, 62)
bar += 8
# ---- B 段：全奏，铜管齐鸣，合唱加入（16 小节）
for rep in range(2):
    for i in range(8):
        c = PROG[(i + 4) % 8]
        cello_ostinato(bar + i, c, 104)
        pad(bar + i, 1, c, 86, 3, 'basses', 43)
        pad(bar + i, 1, c, 82, 4)
        pad(bar + i, 1, c, 68 + rep * 8, 4, 'choir', 52)
        pad(bar + i, 1, c, 70 + rep * 8, 3, 'brass', 61)
        taiko(bar + i, 96)
        timpani(bar + i, 88)
        if i % 4 == 0:
            cymbal(bar + i, 88)
    theme(bar, THEME_B, 'trumpet', 56, 92 + rep * 10, -12 if rep == 0 else 0)
    theme(bar, THEME_B, 'horn', 60, 100, -12)
    theme(bar, THEME_B, 'violin', 48, 104, 0 if rep == 0 else 12)
    bar += 8
# ---- 尾声：回到律动，渐弱，接回开头可以无缝循环（8 小节）
for i in range(8):
    c = PROG[0] if i < 4 else PROG[1]
    v = int(92 - i * 5)
    cello_ostinato(bar + i, c, v)
    if i % 2 == 0:
        pad(bar + i, 2, c, max(44, 70 - i * 3), 3, 'basses', 43)
    if i < 4:
        timpani(bar + i, 66 - i * 6, (0,))
theme(bar, [(0, 0, 4, 'A4'), (0, 4, 2, 'D5'), (1, 0, 6, 'C5'), (2, 0, 6, 'A4'), (3, 0, 6, 'D4')], 'horn', 60, 74)
bar += 8
LEN = bar * BAR
json.dump(dict(tracks=list(tracks.values()), length=LEN), open(sys.argv[1], 'w'))
print('bars', bar, 'seconds', round(LEN, 1), 'tracks', list(tracks))
