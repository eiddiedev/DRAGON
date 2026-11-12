#!/usr/bin/env python3
"""魔法阵洼地填平 + 麦田重排 + 麦田底色提前染黄（2026-11-11）。

读编辑器工程里的 scene.data（原生地形：HeightMap、MatCoverTex）和作者包 prefab.json，
算出：
  1. 新高度图：以魔法阵为中心的一块平地，四周平滑过渡；
  2. 东侧 110 簇麦子的新位置：并回主麦田，连成一整片；
  3. 新的地表底色图：麦田下面直接染成麦金色，魔法阵平地染成夯土色；
  4. 需要删除的草（新麦田下面、平地里面、被抬高的地面埋住的）。
plan 只算不写；apply 在工程关闭时写回 scene.data 和 prefab.json（先备份）。
"""
import io, json, os, shutil, sys, time, zipfile
import numpy as np, cv2
from PIL import Image, ImageDraw

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJ = os.path.expanduser('~/Library/Application Support/AI World Creator/projects/project_lapv8fm0')
SCENE = f'{PROJ}/scene.data'
PREFAB = f'{PROJ}/ai-sessions/workspace_sbazsi67/wprefabs/dragon_phase1_merged/prefab.json'
OUT = f'{REPO}/assets/layout_v15'
os.makedirs(OUT, exist_ok=True)

ARENA = (130.3, 19.4)
R_FLAT, R_BLEND = 15.5, 25.0
LEVEL = 35.6
SEA = 26.6
HSCALE = 256.0


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def load():
    z = zipfile.ZipFile(SCENE)
    names = z.namelist()
    hname = [n for n in names if n.startswith('HeightMap_')][0]
    cname = [n for n in names if n.startswith('MatCoverTex_')][0]
    H = np.frombuffer(z.read(hname), '<f4').reshape(257, 257).copy()
    cover = Image.open(io.BytesIO(z.read(cname))).convert('RGBA')
    scene = json.loads(z.read('SerializePcgData.json'))
    return z, hname, cname, H, cover, scene


def new_heights(H):
    zz, xx = np.mgrid[0:257, 0:257].astype(np.float32)
    r = np.hypot(xx - ARENA[0], zz - ARENA[1])
    k = smooth((r - R_FLAT) / (R_BLEND - R_FLAT))      # 0 = 平地，1 = 原地形
    old = H * HSCALE
    new = LEVEL * (1 - k) + old * k
    # 海里的格子不抬（保住海岸线），只在陆地上动
    new = np.where((old < SEA - .3) & (r > R_FLAT + 1.5), old, new)
    return (new / HSCALE).astype('<f4')


def sample(Hm, x, z):
    x = min(255.999, max(0, x)); z = min(255.999, max(0, z))
    ix, iz = int(x), int(z)
    fx, fz = x - ix, z - iz
    h = (Hm[iz, ix] * (1 - fx) + Hm[iz, ix + 1] * fx) * (1 - fz) + (Hm[iz + 1, ix] * (1 - fx) + Hm[iz + 1, ix + 1] * fx) * fz
    return float(h) * HSCALE


def plan():
    z, hname, cname, H, cover, scene = load()
    H2 = new_heights(H)
    nodes = scene['nodeTransformDatas']
    byid = {n['id']: n for n in nodes}
    west = [n for n in nodes if n['basic']['nodeName'].startswith('golden_geometry') and byid[n['basic']['parentId']]['basic']['nodeName'] == 'WPrefab 实例']
    wpos = np.array([[n['basic']['pos']['x'], n['basic']['pos']['z']] for n in west])
    prefab = json.load(open(PREFAB))
    east = [n for n in prefab['nodeTransformDatas'] if n['basic']['nodeName'].startswith('golden_geometry')]

    # 需要避开的东西：魔法阵、出生点、时之晷、马厩和马、房子
    avoid = [(ARENA[0], ARENA[1], R_FLAT + 2.2), (132.5, 49, 3.2), (121, 57, 5), (146, 46.5, 7.5), (140.5, 51, 3.5),
             (112, 44, 2.5), (166, 54, 9), (162, 44, 8), (174, 46, 8)]

    def ok(x, zv):
        if not (96 < x < 152 and 30.5 < zv < 54.5):
            return False
        for ax, az, ar in avoid:
            if (x - ax) ** 2 + (zv - az) ** 2 < ar * ar:
                return False
        h = sample(H2, x, zv)
        if h < SEA + 1.5:
            return False
        # 坡太陡的地方不种
        if abs(sample(H2, x + 1, zv) - sample(H2, x - 1, zv)) > 1.1 or abs(sample(H2, x, zv + 1) - sample(H2, x, zv - 1)) > 1.1:
            return False
        return True

    rng = np.random.default_rng(15)
    placed = [tuple(p) for p in wpos]
    cx, cz = 124.0, 42.5           # 主麦田中心
    cand = []
    for _ in range(60000):
        x, zv = rng.uniform(96, 152), rng.uniform(30.5, 54.5)
        if ok(x, zv):
            # 越靠近主田越优先，椭圆距离（东西向更长）
            cand.append((((x - cx) / 27) ** 2 + ((zv - cz) / 10.5) ** 2 + rng.uniform(0, .08), x, zv))
    cand.sort()
    new = []
    SP = 2.05
    for _, x, zv in cand:
        if len(new) >= len(east):
            break
        d = min((x - px) ** 2 + (zv - pz) ** 2 for px, pz in placed)
        if d >= SP * SP:
            placed.append((x, zv)); new.append((x, zv))
    assert len(new) == len(east), (len(new), len(east))
    moves = []
    for n, (x, zv) in zip(east, new):
        y = sample(H2, x, zv)
        moves.append(dict(id=n['id'], x=round(x, 3), y=round(y - .02, 3), z=round(zv, 3)))

    # 草：新麦子脚下、平地里面、被埋的
    allw = np.array(placed)
    kill = []
    for n in nodes:
        b = n['basic']
        if b['parentId'] != 0 or not b['nodeName'].startswith('pl_'):
            continue
        x, zv, y = b['pos']['x'], b['pos']['z'], b['pos']['y']
        if not (0 <= x <= 256 and 0 <= zv <= 256):
            continue
        r = np.hypot(x - ARENA[0], zv - ARENA[1])
        dh = sample(H2, x, zv) - sample(H, x, zv)
        near_new = min((x - px) ** 2 + (zv - pz) ** 2 for px, pz in new) < 1.6 ** 2
        is_grass = b['nodeName'].startswith('pl_grass')
        if r < R_FLAT + .5 or abs(dh) > .35 or (near_new and is_grass):
            kill.append(n['id'])

    # 底色：麦田足迹（所有 260 簇）→ 麦金；魔法阵平地 → 夯土
    W = cover.size[0]
    s = W / 256.0
    foot = np.zeros((W, W), np.float32)
    for px, pz in placed:
        cv2.circle(foot, (int(px * s), int((256 - pz) * s)), int(2.3 * s), 1.0, -1)
    foot = cv2.GaussianBlur(foot, (0, 0), 1.6 * s)
    foot = np.clip(foot * 1.5, 0, 1)
    n1 = cv2.resize(np.random.default_rng(3).normal(0, 1, (W // 24, W // 24)).astype(np.float32), (W, W), interpolation=cv2.INTER_CUBIC)
    n2 = cv2.resize(np.random.default_rng(4).normal(0, 1, (W // 4, W // 4)).astype(np.float32), (W, W), interpolation=cv2.INTER_CUBIC)
    c = np.array(cover).astype(np.float32)
    gold = np.array([176, 138, 58], np.float32) + n1[..., None] * 10 + n2[..., None] * 7
    k = (foot * .92)[..., None]
    c[..., :3] = c[..., :3] * (1 - k) + gold * k
    yy, xx = np.mgrid[0:W, 0:W].astype(np.float32)
    rr = np.hypot(xx / s - ARENA[0], (256 - yy / s) - ARENA[1])
    earth = np.array([98, 86, 78], np.float32) + n1[..., None] * 7 + n2[..., None] * 6
    ke = (1 - smooth((rr - R_FLAT + 1.2) / 3.0)) * .9
    ring = np.exp(-((rr - (R_FLAT - .6)) / .5) ** 2) * .5        # 平地边缘一圈深色石缘
    c[..., :3] = c[..., :3] * (1 - ke[..., None]) + earth * ke[..., None]
    c[..., :3] *= (1 - ring)[..., None]
    cover2 = Image.fromarray(np.clip(c, 0, 255).astype(np.uint8), 'RGBA')

    # 预览
    sc = 8
    x0, x1, z0, z1 = 85, 190, 0, 70
    im = Image.new('RGB', ((x1 - x0) * sc, (z1 - z0) * sc))
    crop = cover2.convert('RGB').crop((int(x0 * s), int((256 - z1) * s), int(x1 * s), int((256 - z0) * s))).resize(im.size)
    im.paste(crop)
    d = ImageDraw.Draw(im)
    P = lambda x, zv: ((x - x0) * sc, (z1 - zv) * sc)
    for px, pz in wpos:
        u, v = P(px, pz); d.ellipse([u - 5, v - 5, u + 5, v + 5], outline=(255, 255, 255))
    for px, pz in new:
        u, v = P(px, pz); d.ellipse([u - 5, v - 5, u + 5, v + 5], outline=(255, 60, 60))
    for ax, az, ar in avoid:
        u, v = P(ax, az); d.ellipse([u - ar * sc, v - ar * sc, u + ar * sc, v + ar * sc], outline=(80, 160, 255))
    for i in kill:
        b = byid[i]['basic']; u, v = P(b['pos']['x'], b['pos']['z']); d.point((u, v), fill=(255, 0, 255))
    im.save(f'{OUT}/plan.png')
    hp = ((H2 * HSCALE - 26) * 12).clip(0, 255).astype(np.uint8)
    Image.fromarray(np.flipud(hp)).resize((771, 771)).crop((240, 520, 620, 771)).save(f'{OUT}/plan_height.png')
    json.dump(dict(moves=moves, kill=kill, level=LEVEL, arena=ARENA, r_flat=R_FLAT, r_blend=R_BLEND), open(f'{OUT}/plan.json', 'w'), indent=1)
    np.save(f'{OUT}/heights_new.npy', H2)
    cover2.save(f'{OUT}/cover_new.png')
    print('moves', len(moves), 'kill', len(kill), 'cover', cover.size, cover.mode)
    for zz in (8, 12, 19, 26, 32):
        print(zz, [round(float(H2[zz, x]) * HSCALE, 1) for x in range(108, 154, 4)])
    return z, hname, cname, H2, cover2, moves, kill


def apply():
    z, hname, cname, H2, cover2, moves, kill = plan()
    stamp = time.strftime('%Y%m%d-%H%M%S')
    bdir = f'{REPO}/backups/before-v15-{stamp}'
    os.makedirs(bdir, exist_ok=True)
    shutil.copy2(SCENE, f'{bdir}/scene.data')
    shutil.copy2(PREFAB, f'{bdir}/prefab.json')
    buf = io.BytesIO(); cover2.save(buf, 'PNG', optimize=True)
    tmp = SCENE + '.tmp'
    with zipfile.ZipFile(tmp, 'w') as out:
        for info in z.infolist():
            data = z.read(info.filename)
            if info.filename == hname:
                data = H2.tobytes()
            elif info.filename == cname:
                data = buf.getvalue()
            ni = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            ni.compress_type = info.compress_type
            ni.external_attr = info.external_attr
            out.writestr(ni, data)
    # 校验后再替换
    chk = zipfile.ZipFile(tmp)
    assert chk.testzip() is None
    assert len(chk.read(hname)) == 257 * 257 * 4
    os.replace(tmp, SCENE)
    prefab = json.load(open(PREFAB))
    mv = {m['id']: m for m in moves}
    n = 0
    for node in prefab['nodeTransformDatas']:
        m = mv.get(node['id'])
        if m:
            node['basic']['pos'] = dict(x=m['x'], y=m['y'], z=m['z']); n += 1
    assert n == len(moves)
    json.dump(prefab, open(PREFAB, 'w'), ensure_ascii=False)
    print('applied; backup at', bdir)


if __name__ == '__main__':
    (apply if len(sys.argv) > 1 and sys.argv[1] == 'apply' else plan)()
