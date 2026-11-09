# ---------- 公共库植被：松树、灌木（模型），青草和野花（官方贴片植物）
PLANT_TPL = {'tree': '松树01', 'bush': '翠绿灌木02', 'grass': '青草01', 'forget': '勿忘草01', 'lav': '薰衣草01', 'tail': '狼尾草02'}
prnd = random.Random(808)
road_pts = [(p[0], p[1]) for p in path]
house_pts = [(n['pos']['x'], n['pos']['z']) for n in N if n['parentId'] == 0 and n['nodeName'].startswith(('hs_', 'house_', 'witch_shop', 'windmill', 'lighthouse', 'arena_gate', 'camp', 'tent'))]
SITE_PTS = [(v['x'], v['z'], v['r']) for v in S_.values()] + [(130, 48, 7), (121, 57, 4), (160.5, 74, 7), (127, 176, 30), (165, 234, 30), (48, 150, 18)]


def slope_at(px, pz):
    e = 1.0
    return math.degrees(math.atan(math.hypot(G(px + e, pz) - G(px - e, pz), G(px, pz + e) - G(px, pz - e)) / (2 * e)))


def near_any(px, pz, pts, r):
    return any((px - a) ** 2 + (pz - b) ** 2 < r * r for a, b in pts)


def free_spot(px, pz, road_r=2.6, house_r=6.0):
    if not (4 < px < 252 and 4 < pz < 252):
        return False
    h = G(px, pz)
    if h < 28.6 or h > 78:
        return False
    if near_any(px, pz, road_pts, road_r) or near_any(px, pz, house_pts, house_r):
        return False
    if any((px - a) ** 2 + (pz - b) ** 2 < r * r for a, b, r in SITE_PTS):
        return False
    return True


def plant(kind, i, px, pz, deg, k, solid=False, shadow=False):
    tpl = one(PLANT_TPL[kind])
    n = clone(tpl, f'pl_{kind}_{i}')
    n['isActive'] = True
    y0 = G(px, pz) - (.15 if kind in ('tree', 'bush') else .02)
    set_pos(n, px, y0, pz, deg)
    base = tpl['scale']
    n['scale'] = {'x': base['x'] * k, 'y': base['y'] * k, 'z': base['z'] * k}
    # 公共库模型的子节点存的是相对缩放（1），位置是世界坐标：按模板里的偏移旋转、缩放后放回去
    tq = tpl['rot']
    t_yaw = 2 * math.atan2(tq['y'], tq['w'])
    nq = n['rot']
    n_yaw = 2 * math.atan2(nq['y'], nq['w'])
    dy = n_yaw - t_yaw
    for c, tc in zip(children.get(n['id'], []), children.get(tpl['id'], [])):
        ox, oy, oz = tc['pos']['x'] - tpl['pos']['x'], tc['pos']['y'] - tpl['pos']['y'], tc['pos']['z'] - tpl['pos']['z']
        rx = ox * math.cos(dy) + oz * math.sin(dy)
        rz = -ox * math.sin(dy) + oz * math.cos(dy)
        c['pos'] = {'x': px + rx * k, 'y': y0 + oy * k, 'z': pz + rz * k}
        c['scale'] = dict(tc['scale'])
    if not solid:
        no_collision(n)
    for c in [n] + children.get(n['id'], []):
        if c.get('appearanceData'):
            c['appearanceData']['castShadows'] = shadow
    if kind in ('grass', 'tail') and n.get('appearanceData'):
        n['appearanceData']['color'] = {'r': .74, 'g': .84, 'b': .66, 'a': 1.0}
    return n


if all(v in roots for v in PLANT_TPL.values()):
    # 松林：沿用原来的森林分布，最小间距 4 米
    trees = json.load(open(f'{ROOT}/forest2/trees.json'))
    prnd.shuffle(trees)
    occ, nt = set(), 0
    for px, pz, _y in trees:
        key = (int(px / 4), int(pz / 4))
        if key in occ or not free_spot(px, pz, 3.0, 7.0) or slope_at(px, pz) > 40:
            continue
        occ |= {(key[0] + a, key[1] + b) for a in (-1, 0, 1) for b in (-1, 0, 1)}
        ht = prnd.uniform(1.6, 2.8)          # 模型默认约 4.7 米，放大到 7.5~13 米
        plant('tree', nt, px, pz, prnd.uniform(0, 360), ht, solid=True, shadow=True)
        nt += 1
        if nt >= 300:
            break
    # 林缘灌木
    nb = 0
    for px, pz, _y in trees[::5]:
        px += prnd.uniform(-4, 4); pz += prnd.uniform(-4, 4)
        if free_spot(px, pz) and slope_at(px, pz) < 35:
            plant('bush', nb, px, pz, prnd.uniform(0, 360), prnd.uniform(.8, 1.4))
            nb += 1
            if nb >= 90:
                break
    # 青草：5 米网格抖动，平缓处才种，越靠近出生点和小路越密
    ng = nf = nl = nw = 0
    for gz in range(5, 251, 3):
        for gx in range(5, 251, 3):
            px, pz = gx + prnd.uniform(-1.4, 1.4), gz + prnd.uniform(-1.4, 1.4)
            if not free_spot(px, pz) or slope_at(px, pz) > 30:
                continue
            d_spawn = math.hypot(px - 130, pz - 60)
            keep_p = .95 if d_spawn < 80 else .7
            if prnd.random() > keep_p:
                continue
            if math.hypot(px - 150, pz - 62) < 22 and prnd.random() < .8:
                plant('lav', nl, px, pz, prnd.uniform(0, 360), prnd.uniform(1.0, 1.5)); nl += 1
                continue
            r_ = prnd.random()
            if r_ < .08:
                plant('forget', nf, px, pz, prnd.uniform(0, 360), prnd.uniform(.9, 1.4)); nf += 1
            elif r_ < .14 and G(px, pz) < 34:
                plant('tail', nw, px, pz, prnd.uniform(0, 360), prnd.uniform(.9, 1.3)); nw += 1
            else:
                plant('grass', ng, px, pz, prnd.uniform(0, 360), prnd.uniform(.8, 1.25)); ng += 1
    for v in PLANT_TPL.values():
        one(v)['isActive'] = False
    print('plants trees', nt, 'bushes', nb, 'grass', ng, 'forget', nf, 'lav', nl, 'tail', nw)
