#!/usr/bin/env python3
"""森林里的互动地点：在地形上平出空地，写 sites.json。先于 erode.py 和 world_terrain_v3.py 运行。
用法：sites.py <旧 base_heights.npy> <v3 目录>
"""
import json
import os
import sys

import numpy as np
from scipy import ndimage as nd

src, OUT = sys.argv[1:3]
H = np.load(src).astype(float)
SITES = {
    'camp': dict(x=62, z=62, r=13),        # 冒险者营地：篝火
    'mush': dict(x=86, z=98, r=12),        # 蘑菇林：弹跳
    'altar': dict(x=48, z=150, r=16),      # 唤龙祭坛：点亮三块符文石，巨龙现身
    'perch': dict(x=96, z=30, r=11),       # 飞龙驿站：骑龙飞行
}
n = H.shape[0]
zz, xx = np.mgrid[0:n, 0:n].astype(float)


def ss(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


for k, s in SITES.items():
    d = np.hypot(xx - s['x'], zz - s['z'])
    y = float(np.median(H[d < s['r']]))
    s['y'] = round(y, 2)
    w = 1 - ss(s['r'], s['r'] + 8, d)
    H = H * (1 - w) + y * w
    print(k, s)
np.save(os.path.join(OUT, 'base_heights.npy'), H)
# 林间小路
TRAILS = [
    [(130, 52), (112, 56), (92, 58), (70, 60)],          # 出生点 → 营地
    [(112, 56), (106, 42), (100, 34)],                   # 岔路 → 飞龙驿站
    [(70, 66), (78, 82), (84, 92)],                      # 营地 → 蘑菇林
    [(84, 104), (72, 118), (58, 132), (51, 142)],        # 蘑菇林 → 祭坛
]
json.dump(dict(sites=SITES, trails=TRAILS), open(os.path.join(OUT, 'sites.json'), 'w'), indent=1)
