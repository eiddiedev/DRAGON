#!/usr/bin/env python3
"""摆放之后的补丁，可重复运行。用法：post_place_fixes.py <输入 scene.data> <输出 scene.data>
- 城门地板：外侧高架坡道顶和门内坡道之间有 1.3 米断差，玩家跳不上去，用一块石板接平。
- 古龙白模占位先隐藏，等正式的龙做好再换。
- 天空：穹顶、漩涡、月亮摆好，关掉碰撞和投影（否则穹顶会把月光全挡住）。
- 地形块临时压暗，地形贴图重画后去掉。
"""
import copy
import json
import random
import sys
import zipfile

src, out = sys.argv[1:3]
z = zipfile.ZipFile(src)
d = json.loads(z.read('SerializePcgData.json'))
N = d['nodeTransformDatas']
FLOOR = '城门地板'
TOP = 58.3
THICK = .9
if not any(n['nodeName'] == FLOOR for n in N):
    tpl = next(n for n in N if n['nodeName'] == '方块' and n['parentId'] == 0)
    used = {n['id'] for n in N}
    rnd = random.Random(165)
    nid = rnd.randint(1, 2 ** 31 - 1)
    while nid in used:
        nid = rnd.randint(1, 2 ** 31 - 1)
    c = copy.deepcopy(tpl)
    c.update(id=nid, nodeName=FLOOR, isActive=True, isStatic=True)
    c['pos'] = {'x': 151.25, 'y': TOP - THICK / 2, 'z': 165.0}
    c['scale'] = {'x': 5.5, 'y': THICK, 'z': 10.0}
    c['appearanceData']['color'] = {'r': .77, 'g': .70, 'b': .60, 'a': 1.0}
    N.append(c)
    print('added', FLOOR)
for n in N:
    if n['nodeName'] == '白模_古龙龙巢' and n['parentId'] == 0:
        n['isActive'] = False
        print('hid', n['nodeName'])
# ---------- 天空。模型导入时最长边归一成 1 米，所以缩放等于直径。
FLIP = {'x': 0.0, 'y': 1.0, 'z': 0.0, 'w': 0.0}  # 和其他模型一样转回来
SKY = {
    'sky_dome2': ((128.0, 30.0, 128.0), 1240.0),
    'sky_moon2': ((-70.0, 205.0, 480.0), 165.0),  # 最远，云能从它前面飘过
    'sky_swirl_a': ((128.0, 235.0, 455.0), 560.0),
    'sky_swirl_b': ((128.0, 235.0, 440.0), 470.0),
    'sky_swirl_c': ((128.0, 235.0, 425.0), 330.0),
}
OLD_SKY = {'sky_dome', 'sky_swirl', 'sky_moon'}
N = [n for n in N if not (n['parentId'] == 0 and n['nodeName'] in OLD_SKY)]
d['nodeTransformDatas'] = N
for n in N:
    if n['nodeName'] in SKY and n['parentId'] == 0:
        (x, y, z_), size = SKY[n['nodeName']]
        n['pos'] = {'x': x, 'y': y, 'z': z_}
        n['rot'] = dict(FLIP)
        n['scale'] = {'x': size, 'y': size, 'z': size}
        n['isStatic'] = not n['nodeName'].startswith('sky_swirl')
        n['physicsColliderData']['enableCollision'] = False
        n['appearanceData']['castShadows'] = False
        print('placed', n['nodeName'])
# ---------- 地形块临时压暗
TINT = {'r': .50, 'g': .58, 'b': .62, 'a': 1.0}
for n in N:
    name = n['nodeName']
    if n['parentId'] == 0 and len(name) == 8 and name[0] == 't' and name[4] == '_':
        n['appearanceData']['color'] = dict(TINT)
        n['appearanceData']['isModified'] = True
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as w:
    for i in z.infolist():
        data = z.read(i.filename)
        if i.filename == 'SerializePcgData.json':
            data = json.dumps(d, ensure_ascii=False, separators=(',', ':')).encode()
        ni = zipfile.ZipInfo(i.filename, i.date_time)
        ni.compress_type = zipfile.ZIP_DEFLATED
        ni.external_attr = i.external_attr
        w.writestr(ni, data)
print('nodes', len(N))
