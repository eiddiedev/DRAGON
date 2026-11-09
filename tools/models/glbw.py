"""不依赖 Blender 的 GLB 写入器：真实几何体、调色板贴图、蒙皮和骨骼动画。
设计坐标 (东 E, 北 N, 上 U)，导出时转成 glTF (E, U, -N)，和其他模型一致。"""
import io
import json
import struct

import numpy as np
from PIL import Image


def palette_image(rows, width=256, rowh=16):
    """rows: 每行是 [(位置, '#rrggbb'), ...] 的渐变。一行占 rowh 像素，避免 mipmap 串色。"""
    H = max(16, len(rows)) * rowh
    # 补成 2 的幂
    h = 16
    while h < H:
        h *= 2
    img = np.zeros((h, width, 3), np.uint8)
    for r, stops in enumerate(rows):
        xs = [s[0] for s in stops]
        cs = np.array([[int(s[1][i:i + 2], 16) for i in (1, 3, 5)] for s in stops], float)
        t = np.linspace(0, 1, width)
        col = np.stack([np.interp(t, xs, cs[:, k]) for k in range(3)], 1)
        img[r * rowh:(r + 1) * rowh] = col.astype(np.uint8)
    return Image.fromarray(img), h, rowh


class Geo:
    def __init__(self, rows, width=256, rowh=16):
        self.img, self.h, self.rowh = palette_image(rows, width, rowh)
        self.width = width
        self.P, self.N, self.T, self.J, self.W = [], [], [], [], []
        self.skin = (0, 0, 0.0)

    def uv(self, tone, row):
        tone = min(max(tone, .01), .99)
        return (tone, (row + .5) * self.rowh / self.h)

    def tri(self, a, b, c, tone=.5, row=0, ref=None, skin=None, normals=None):
        """平面着色三角形。ref：法线要背向的参考点（通常是物体中心）。tone 可以是 3 元组。"""
        a, b, c = np.asarray(a, float), np.asarray(b, float), np.asarray(c, float)
        n = np.cross(b - a, c - a)
        ln = np.linalg.norm(n)
        if ln < 1e-9:
            return
        n = n / ln
        if ref is not None and np.dot(n, (a + b + c) / 3 - np.asarray(ref, float)) < 0:
            b, c = c, b
            n = -n
            if isinstance(tone, tuple):
                tone = (tone[0], tone[2], tone[1])
            if isinstance(skin, list):
                skin = [skin[0], skin[2], skin[1]]
            if normals is not None:
                normals = [normals[0], normals[2], normals[1]]
        if ref is None and normals is not None and np.dot(n, normals[0]) < 0:
            b, c = c, b
            n = -n
            normals = [normals[0], normals[2], normals[1]]
            if isinstance(tone, tuple):
                tone = (tone[0], tone[2], tone[1])
            if isinstance(skin, list):
                skin = [skin[0], skin[2], skin[1]]
        tones = tone if isinstance(tone, tuple) else (tone, tone, tone)
        sk = skin if skin is not None else self.skin
        sks = sk if isinstance(sk, list) else [sk, sk, sk]
        for i, p in enumerate((a, b, c)):
            self.P.append(p)
            self.N.append(n if normals is None else normals[i])
            self.T.append(self.uv(tones[i], row))
            j0, j1, w = sks[i]
            self.J.append((j0, j1, 0, 0))
            w1 = int(round(w * 255))
            self.W.append((255 - w1, w1, 0, 0))

    def quad(self, a, b, c, d, tone=.5, row=0, ref=None, skin=None):
        if isinstance(tone, tuple):
            t = tone
            self.tri(a, b, c, (t[0], t[1], t[2]), row, ref, None if skin is None else [skin[0], skin[1], skin[2]] if isinstance(skin, list) else skin)
            self.tri(a, c, d, (t[0], t[2], t[3]), row, ref, None if skin is None else [skin[0], skin[2], skin[3]] if isinstance(skin, list) else skin)
        else:
            self.tri(a, b, c, tone, row, ref, None if skin is None else [skin[0], skin[1], skin[2]] if isinstance(skin, list) else skin)
            self.tri(a, c, d, tone, row, ref, None if skin is None else [skin[0], skin[2], skin[3]] if isinstance(skin, list) else skin)

    def loft(self, rings, tone=.5, row=0, centers=None, skins=None, tone_fn=None, cap=True):
        """rings: [n 个点] 的列表，相邻环连成四边形。centers: 每环中心，用于确定法线朝外。"""
        rings = [np.asarray(r, float) for r in rings]
        m = len(rings[0])
        if centers is None:
            centers = [r.mean(0) for r in rings]
        for i in range(len(rings) - 1):
            ref = (np.asarray(centers[i]) + np.asarray(centers[i + 1])) / 2
            for k in range(m):
                k2 = (k + 1) % m
                sk = None if skins is None else [skins[i], skins[i + 1], skins[i + 1], skins[i]]
                t = tone_fn(i, k) if tone_fn else tone
                self.quad(rings[i][k], rings[i + 1][k], rings[i + 1][k2], rings[i][k2], t, row, ref, sk)
        if cap:
            for idx, sgn in ((0, -1), (-1, 1)):
                r = rings[idx]
                c = r.mean(0)
                sk = None if skins is None else skins[idx]
                out = c + (c - rings[idx + (1 if idx == 0 else -1)].mean(0))
                for k in range(m):
                    self.tri(c, r[k], r[(k + 1) % m], tone if not isinstance(tone, tuple) else .5, row, ref=rings[idx + (1 if idx == 0 else -1)].mean(0), skin=sk)

    def cone(self, base, tip, radius, up=None, seg=5, tone=.5, row=0, skin=None, curve=None, n=1, tip_tone=None):
        """水晶锥/尖角。curve: 弯曲偏移向量，n: 分段。"""
        base, tip = np.asarray(base, float), np.asarray(tip, float)
        d = tip - base
        u = np.cross(d, up if up is not None else (0.3, .2, 1))
        if np.linalg.norm(u) < 1e-6:
            u = np.cross(d, (1, 0, 0))
        u = u / np.linalg.norm(u)
        v = np.cross(d, u)
        v = v / np.linalg.norm(v)
        rings, ctrs = [], []
        for i in range(n):
            t = i / n
            c = base + d * t + (0 if curve is None else np.asarray(curve) * np.sin(t * np.pi / 2 * 2) * 1.0)
            r = radius * (1 - t) ** .8
            rings.append([c + (u * np.cos(a) + v * np.sin(a)) * r for a in np.linspace(0, np.pi * 2, seg, endpoint=False)])
            ctrs.append(c)
        for i in range(n - 1):
            ref = (ctrs[i] + ctrs[i + 1]) / 2
            for k in range(seg):
                k2 = (k + 1) % seg
                self.quad(rings[i][k], rings[i + 1][k], rings[i + 1][k2], rings[i][k2], tone + .05 * (k % 2), row, ref, skin)
        for k in range(seg):
            self.tri(rings[-1][k], rings[-1][(k + 1) % seg], tip, (tone, tone, tip_tone if tip_tone is not None else min(.95, tone + .3)), row, ctrs[-1], skin)

    def box(self, c, u, v, w, tone=.5, row=0, skin=None, taper=1.0):
        """中心 c，半轴向量 u,v,w（w 朝上）。taper 收顶。"""
        c, u, v, w = [np.asarray(x, float) for x in (c, u, v, w)]
        b = [c - w + a * u + e * v for a, e in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        t = [c + w + a * u * taper + e * v * taper for a, e in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        for i in range(4):
            j = (i + 1) % 4
            self.quad(b[i], b[j], t[j], t[i], tone, row, c, skin)
        self.quad(t[0], t[1], t[2], t[3], min(.99, tone + .08), row, c, skin)
        self.quad(b[0], b[1], b[2], b[3], max(.01, tone - .1), row, c, skin)

    def tris_count(self):
        return len(self.P) // 3


def _conv_pos(p):
    p = np.asarray(p, np.float32)
    return np.stack([p[..., 0], p[..., 2], -p[..., 1]], -1)


def _conv_quat(q):
    """设计坐标四元数 (w,x,y,z) → glTF (x,y,z,w)"""
    q = np.asarray(q, np.float32)
    return np.stack([q[..., 1], q[..., 3], -q[..., 2], q[..., 0]], -1)


def write_glb(path, geo, joints=None, clips=None, name='model', rough=.55, metal=0.0, image=None, emissive=None, alpha=False):
    """joints: [(名字, 静止位置)]，全部挂在根节点下，静止旋转为单位。
    clips: {片段名: dict(times=[...], pos=数组(帧,骨,3), rot=数组(帧,骨,4 wxyz), scale=可选数组(帧,骨))}"""
    P = _conv_pos(np.array(geo.P))
    N = _conv_pos(np.array(geo.N))
    T = np.array(geo.T, np.float32)
    bin_ = bytearray()
    views, accs = [], []

    def add(arr, ctype, comp, target=None, norm=False, minmax=False):
        nonlocal bin_
        while len(bin_) % 4:
            bin_ += b'\0'
        off = len(bin_)
        raw = arr.tobytes()
        bin_ += raw
        v = dict(buffer=0, byteOffset=off, byteLength=len(raw))
        if target:
            v['target'] = target
        views.append(v)
        count = arr.shape[0]
        a = dict(bufferView=len(views) - 1, componentType=comp, count=count, type=ctype)
        if norm:
            a['normalized'] = True
        if minmax:
            flat = arr.reshape(count, -1)
            a['min'] = [float(x) for x in flat.min(0)]
            a['max'] = [float(x) for x in flat.max(0)]
        accs.append(a)
        return len(accs) - 1

    attrs = dict(POSITION=add(P, 'VEC3', 5126, 34962, minmax=True), NORMAL=add(N, 'VEC3', 5126, 34962), TEXCOORD_0=add(T, 'VEC2', 5126, 34962))
    if joints:
        attrs['JOINTS_0'] = add(np.array(geo.J, np.uint8), 'VEC4', 5121, 34962)
        attrs['WEIGHTS_0'] = add(np.array(geo.W, np.uint8), 'VEC4', 5121, 34962, norm=True)
    idx = add(np.arange(len(P), dtype=np.uint32), 'SCALAR', 5125, 34963)
    buf = io.BytesIO()
    (image or geo.img).save(buf, 'PNG', optimize=True)
    while len(bin_) % 4:
        bin_ += b'\0'
    off = len(bin_)
    bin_ += buf.getvalue()
    views.append(dict(buffer=0, byteOffset=off, byteLength=len(buf.getvalue())))
    img_view = len(views) - 1
    nodes = [dict(name=name, mesh=0)] if not joints else [dict(name='rig', children=[]), dict(name=name, mesh=0, skin=0)]
    g = dict(asset=dict(version='2.0', generator='awesomeWRLD'), scene=0, scenes=[dict(nodes=[0])], nodes=nodes,
             meshes=[dict(name=name, primitives=[dict(attributes=attrs, indices=idx, material=0)])],
             materials=[dict(name=name, pbrMetallicRoughness=dict(baseColorTexture=dict(index=0), roughnessFactor=rough, metallicFactor=metal))],
             textures=[dict(sampler=0, source=0)], images=[dict(bufferView=img_view, mimeType='image/png', name=name + '_pal')],
             samplers=[dict(magFilter=9729, minFilter=9987, wrapS=33071, wrapT=33071)], accessors=accs, bufferViews=views)
    if alpha:
        g['materials'][0]['alphaMode'] = 'BLEND'
        g['materials'][0]['doubleSided'] = True
    if emissive is not None:
        g['materials'][0]['emissiveTexture'] = dict(index=0)
        g['materials'][0]['emissiveFactor'] = list(emissive)
    if joints:
        nodes[0]['children'].append(1)
        jidx = []
        ibm = np.zeros((len(joints), 16), np.float32)
        for i, (nm, p) in enumerate(joints):
            gp = _conv_pos(np.array(p))
            nodes.append(dict(name=nm, translation=[float(x) for x in gp]))
            jidx.append(len(nodes) - 1)
            nodes[0]['children'].append(len(nodes) - 1)
            m = np.eye(4, dtype=np.float32)
            m[3, :3] = -gp  # 列主序：平移在最后一列
            ibm[i] = m.reshape(-1)
        ia = add(ibm, 'MAT4', 5126)
        g['skins'] = [dict(name='skin', joints=jidx, inverseBindMatrices=ia, skeleton=0)]
        if clips:
            g['animations'] = []
            for cname, c in clips.items():
                times = add(np.array(c['times'], np.float32), 'SCALAR', 5126, minmax=True)
                samplers, channels = [], []
                pos, rot = np.asarray(c['pos']), np.asarray(c['rot'])
                scale = c.get('scale')
                for j, node in enumerate(jidx):
                    a = add(_conv_pos(pos[:, j]), 'VEC3', 5126)
                    samplers.append(dict(input=times, output=a, interpolation='LINEAR'))
                    channels.append(dict(sampler=len(samplers) - 1, target=dict(node=node, path='translation')))
                    q = _conv_quat(rot[:, j])
                    a = add(q, 'VEC4', 5126)
                    samplers.append(dict(input=times, output=a, interpolation='LINEAR'))
                    channels.append(dict(sampler=len(samplers) - 1, target=dict(node=node, path='rotation')))
                    if scale is not None:
                        s = np.repeat(np.asarray(scale)[:, j, None], 3, 1).astype(np.float32)
                        a = add(s, 'VEC3', 5126)
                        samplers.append(dict(input=times, output=a, interpolation='LINEAR'))
                        channels.append(dict(sampler=len(samplers) - 1, target=dict(node=node, path='scale')))
                g['animations'].append(dict(name=cname, samplers=samplers, channels=channels))
    while len(bin_) % 4:
        bin_ += b'\0'
    g['buffers'] = [dict(byteLength=len(bin_))]
    js = json.dumps(g, separators=(',', ':')).encode()
    js += b' ' * ((4 - len(js) % 4) % 4)
    with open(path, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A) + js)
        f.write(struct.pack('<II', len(bin_), 0x004E4942) + bytes(bin_))
    return len(P) // 3


# ---------- 四元数工具（wxyz，设计坐标）
def q_axis(axis, ang):
    axis = np.asarray(axis, float)
    axis = axis / (np.linalg.norm(axis) + 1e-12)
    s = np.sin(ang / 2)
    return np.array([np.cos(ang / 2), axis[0] * s, axis[1] * s, axis[2] * s])


def q_mul(a, b):
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    return np.array([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2])


def q_rot(q, v):
    u = np.asarray(q[1:])
    w = q[0]
    v = np.asarray(v, float)
    return v + 2 * np.cross(u, np.cross(u, v) + w * v)


def q_between(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    c = np.cross(a, b)
    d = np.dot(a, b)
    q = np.array([1 + d, c[0], c[1], c[2]])
    n = np.linalg.norm(q)
    return q / n if n > 1e-8 else np.array([1., 0, 0, 0])


class Rigid:
    """绕静止位置转的刚体变换：x' = R(x) + t"""

    def __init__(self, q=None, t=None):
        self.q = np.array([1., 0, 0, 0]) if q is None else q
        self.t = np.zeros(3) if t is None else np.asarray(t, float)

    def apply(self, x):
        return q_rot(self.q, x) + self.t

    def then(self, other):
        """先 self 再 other"""
        return Rigid(q_mul(other.q, self.q), other.apply(self.t))

    @staticmethod
    def about(point, axis, ang):
        q = q_axis(axis, ang)
        p = np.asarray(point, float)
        return Rigid(q, p - q_rot(q, p))
