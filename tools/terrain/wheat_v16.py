#!/usr/bin/env python3
"""v16 麦田：加密（作者包里新增麦簇）+ 全部麦簇按脚下最低的地面贴坡 + 新麦簇脚下补染麦金色。
直接改 scene.data 和作者包 prefab.json，只能在编辑器关闭时运行；先备份到 backups/before-v16-*。"""
import copy, io, json, os, shutil, sys, time, zipfile
import numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arena_wheat as A

ADD = 95
z = zipfile.ZipFile(A.SCENE)
names = z.namelist()
hname = [n for n in names if n.startswith('HeightMap_')][0]
cname = [n for n in names if n.startswith('MatCoverTex_')][0]
H = np.frombuffer(z.read(hname), '<f4').reshape(257, 257)
cover = Image.open(io.BytesIO(z.read(cname))).convert('RGBA')
scene = json.loads(z.read('SerializePcgData.json'))
nodes = scene['nodeTransformDatas']
byid = {n['id']: n for n in nodes}
kids = {}
for n in nodes:
    kids.setdefault(n['basic']['parentId'], []).append(n)


def foot_y(x, zv, r=1.15):
    """麦簇脚下一圈里最低的地面，再往下埋一点，坡上不会悬空。"""
    pts = [(x, zv)] + [(x + np.cos(a) * r, zv + np.sin(a) * r) for a in np.linspace(0, 2 * np.pi, 8, endpoint=False)]
    return min(A.sample(H, px, pz) for px, pz in pts) - .04


def shift(n, dy):
    n['basic']['pos']['y'] += dy
    for c in kids.get(n['id'], []):
        shift(c, dy)


west = [n for n in nodes if n['basic']['nodeName'].startswith('golden_geometry') and byid[n['basic']['parentId']]['basic']['nodeName'] == 'WPrefab 实例']
moved = 0
for n in west:
    p = n['basic']['pos']
    dy = foot_y(p['x'], p['z']) - p['y']
    if abs(dy) > .01:
        shift(n, dy); moved += 1
prefab = json.load(open(A.PREFAB))
pn = prefab['nodeTransformDatas']
east = [n for n in pn if n['basic']['nodeName'].startswith('golden_geometry')]
for n in east:
    p = n['basic']['pos']
    p['y'] = round(foot_y(p['x'], p['z']), 3)
placed = [(n['basic']['pos']['x'], n['basic']['pos']['z']) for n in west] + [(n['basic']['pos']['x'], n['basic']['pos']['z']) for n in east]
# 只在现有麦田里面补空：候选点必须挨着已有麦簇
rng = np.random.default_rng(16)
avoid = [(A.ARENA[0], A.ARENA[1], A.R_FLAT + 2.0), (132.5, 49, 3.0), (121, 57, 5), (146, 46.5, 7.5), (140.5, 51, 3.5), (112, 44, 2.3)]
arr = np.array(placed)
new = []
tries = 0
while len(new) < ADD and tries < 200000:
    tries += 1
    x, zv = rng.uniform(arr[:, 0].min(), arr[:, 0].max()), rng.uniform(arr[:, 1].min(), arr[:, 1].max())
    if any((x - ax) ** 2 + (zv - az) ** 2 < ar * ar for ax, az, ar in avoid):
        continue
    d = np.hypot(arr[:, 0] - x, arr[:, 1] - zv)
    near = np.sort(d)[:3]
    if near[0] < 1.45 or near[2] > 3.4:          # 不压在别的麦簇上，也不跑到田外
        continue
    if new and min((x - a) ** 2 + (zv - b) ** 2 for a, b in new) < 1.45 ** 2:
        continue
    new.append((x, zv))
assert len(new) >= 70, len(new)
nid = max(n['id'] for n in pn) + 1
idx = len(placed)
for x, zv in new:
    src = east[int(rng.integers(len(east)))]
    c = copy.deepcopy(src)
    c['id'] = nid; nid += 1
    b = c['basic']
    b['nodeName'] = f'golden_geometry_{idx}'; idx += 1
    b['pos'] = dict(x=round(x, 3), y=round(foot_y(x, zv), 3), z=round(zv, 3))
    a = rng.uniform(0, np.pi)
    b['rot'] = dict(x=0, y=float(np.sin(a)), z=0, w=float(np.cos(a)))
    s = rng.uniform(1.15, 1.5)
    b['scale'] = dict(x=s, y=rng.uniform(.75, 1.05), z=s)
    pn.append(c)
# 底色
W = cover.size[0]; sc = W / 256.0
foot = np.zeros((W, W), np.float32)
for x, zv in new:
    cv2.circle(foot, (int(x * sc), int((256 - zv) * sc)), int(2.3 * sc), 1.0, -1)
foot = np.clip(cv2.GaussianBlur(foot, (0, 0), 1.6 * sc) * 1.5, 0, 1)
n1 = cv2.resize(np.random.default_rng(3).normal(0, 1, (W // 24, W // 24)).astype(np.float32), (W, W), interpolation=cv2.INTER_CUBIC)
c = np.array(cover).astype(np.float32)
gold = np.array([176, 138, 58], np.float32) + n1[..., None] * 10
k = (foot * .9)[..., None]
c[..., :3] = c[..., :3] * (1 - k) + gold * k
cover2 = Image.fromarray(np.clip(c, 0, 255).astype(np.uint8))

stamp = time.strftime('%Y%m%d-%H%M%S')
bdir = f'{A.REPO}/backups/before-v16-{stamp}'
os.makedirs(bdir, exist_ok=True)
shutil.copy2(A.SCENE, f'{bdir}/scene.data'); shutil.copy2(A.PREFAB, f'{bdir}/prefab.json')
buf = io.BytesIO(); cover2.save(buf, 'PNG', optimize=True)
tmp = A.SCENE + '.tmp'
with zipfile.ZipFile(tmp, 'w') as out:
    for info in z.infolist():
        data = z.read(info.filename)
        if info.filename == cname:
            data = buf.getvalue()
        elif info.filename == 'SerializePcgData.json':
            data = json.dumps(scene, ensure_ascii=False, separators=(',', ':')).encode('utf8')
        ni = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        ni.compress_type = info.compress_type; ni.external_attr = info.external_attr
        out.writestr(ni, data)
chk = zipfile.ZipFile(tmp); assert chk.testzip() is None
assert len(json.loads(chk.read('SerializePcgData.json'))['nodeTransformDatas']) == len(nodes)
os.replace(tmp, A.SCENE)
json.dump(prefab, open(A.PREFAB, 'w'), ensure_ascii=False)
print('west re-seated', moved, 'east', len(east), 'added', len(new), 'total names', idx, 'backup', bdir)
