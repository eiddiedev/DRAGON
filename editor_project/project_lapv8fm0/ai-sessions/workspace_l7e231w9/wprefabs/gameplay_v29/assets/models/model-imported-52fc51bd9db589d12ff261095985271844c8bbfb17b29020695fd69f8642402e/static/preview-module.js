const THREE = require('three');

// ---------------------------------------------------------------------------
// Asset brief: three class outfits worn by a 0.84 m round-bodied chibi avatar.
// Authored in glTF space: +Y up, +Z forward, origin at the feet of each set.
// Arm pieces use a limb-aligned local frame (+Z down the limb, +Y outward).
// ---------------------------------------------------------------------------
const ASSET_BRIEF = {
  identity: {
    objectClass: 'three class outfits for a chibi avatar',
    confidence: 1,
    assumptions: [
      'A 0.84 m avatar has its Hips bone near y=0.30 and its Head bone near y=0.64, so the authored Hips-to-Head reference is 0.34 m.',
      'Garments stop below the chin and above the ground; they never model body, hands, head, hair, shoes or weapons.',
    ],
  },
  orientation: { up: '+Y', front: '+Z' },
  silhouette: {
    primaryMasses: ['WarriorSet', 'ArcherSet', 'MageSet'],
    proportions: 'three complete outfit shells laid side by side at x=-0.6 / 0 / +0.6 with their own foot-level origins',
    identityCues: [
      'Warrior: segmented steel cuirass, triple pauldrons, dark red tabard, aged gold edging',
      'Archer: gray-green wool coat with cream lapels, leather belt and pouches, forked back hem',
      'Mage: deep indigo open-front robe and cloak, cream lining, glowing gem clasp, low hood at the nape',
    ],
  },
  parts: [
    {
      id: 'Chest',
      level: 'macro',
      role: 'torso shell and neckline of each outfit',
      parent: 'SetRoot',
      topologyClass: 'assembled-shells',
      geometryStrategy: 'station-driven hollow garment shells with real thickness, layered plates and trim',
      materialRole: 'classTorso',
      attachment: null,
      moving: true,
      pivotStrategy: 'pivot at the Chest bone, canonical torso frame (+Y up, +Z front)',
    },
    {
      id: 'Hips',
      level: 'macro',
      role: 'waistband, faulds and hip hardware',
      parent: 'SetRoot',
      topologyClass: 'assembled-shells',
      geometryStrategy: 'belt shell plus overlapping waist lames with gold rims',
      materialRole: 'classWaist',
      attachment: { parentId: 'Chest', contactType: 'overlap', overlap: 0.02, gapTolerance: 0.002 },
      moving: true,
      pivotStrategy: 'pivot at the Hips bone, canonical torso frame',
    },
    {
      id: 'ShoulderL/R',
      level: 'macro',
      role: 'shoulder armor, mantle or sleeve cap',
      parent: 'SetRoot',
      topologyClass: 'arc-shells',
      geometryStrategy: 'layered arc shells around the upper-arm axis',
      materialRole: 'classShoulder',
      attachment: { parentId: 'Chest', contactType: 'overlap', overlap: 0.01, gapTolerance: 0.002 },
      moving: true,
      pivotStrategy: 'pivot at the upper-arm root, +Z down the limb, +Y outward',
    },
    {
      id: 'BracerL/R',
      level: 'meso',
      role: 'forearm protection or cuffs',
      parent: 'SetRoot',
      topologyClass: 'tube-shells',
      geometryStrategy: 'tapered hollow shells with flared cuffs, straps and rivets',
      materialRole: 'classBracer',
      attachment: { parentId: 'ShoulderL/R', contactType: 'surface-contact', overlap: 0.02, gapTolerance: 0.003 },
      moving: true,
      pivotStrategy: 'pivot at the forearm centre, +Z down the forearm, +Y outward',
    },
    {
      id: 'TabardFront/TabardBack',
      level: 'meso',
      role: 'warrior short dark-red cloth panels',
      parent: 'SetRoot',
      topologyClass: 'cloth-panels',
      geometryStrategy: 'folded cloth slabs with gold edging and stitch runs',
      materialRole: 'clothRed',
      attachment: { parentId: 'Hips', contactType: 'stitched', overlap: 0.012, gapTolerance: 0.002 },
      moving: true,
      pivotStrategy: 'pivot at the belt, geometry hangs down in the torso frame',
    },
    {
      id: 'HemFrontL/R / HemBackL/R',
      level: 'meso',
      role: 'archer split coat skirt',
      parent: 'SetRoot',
      topologyClass: 'cloth-panels',
      geometryStrategy: 'four tapered cloth panels with a forked back hem and cream lining edges',
      materialRole: 'clothGreen',
      attachment: { parentId: 'Hips', contactType: 'stitched', overlap: 0.012, gapTolerance: 0.002 },
      moving: true,
      pivotStrategy: 'pivot at the belt, geometry hangs down in the torso frame',
    },
    {
      id: 'CloakBackL/R / CloakSideL/R / HoodBack',
      level: 'macro',
      role: 'mage cloak volume and low hood',
      parent: 'SetRoot',
      topologyClass: 'cloth-panels',
      geometryStrategy: 'long folded cloak panels with cream lining, gold trim and a nape cowl',
      materialRole: 'clothIndigo',
      attachment: { parentId: 'Chest', contactType: 'stitched', overlap: 0.012, gapTolerance: 0.002 },
      moving: true,
      pivotStrategy: 'pivot at the shoulder yoke, geometry hangs down in the torso frame',
    },
  ],
  materialRoles: {
    steel: 'brushed armor plate',
    steelDark: 'recessed plate and inner armor shadow',
    goldOld: 'aged gold edging, rivet heads and buckle frames',
    leather: 'belts, straps and harness',
    clothRed: 'warrior tabard cloth',
    clothGreen: 'archer wool coat',
    linen: 'cream collars, lapels and lining',
    clothIndigo: 'mage robe and cloak',
    gem: 'glowing violet chest gem',
  },
  detailBudget: {
    must: [
      'real garment thickness and visible lining',
      'trim or piping on every exposed hem',
      'stitch runs on cloth seams',
      'rivets or buckles on every strap',
    ],
    optional: ['enamel crest', 'chain links', 'extra fold ridges'],
  },
  readiness: {
    pivots: ['Chest', 'Hips', 'ShoulderL', 'ShoulderR', 'BracerL', 'BracerR'],
    sockets: [],
    anchors: [],
    colliderIntent: [],
  },
};

// ---------------------------------------------------------------------------
// Body reference used to place garment parts on the 0.84 m chibi silhouette.
// ---------------------------------------------------------------------------
const BODY = {
  hipsY: 0.300,
  chestY: 0.490,
  headY: 0.640,
  shoulderY: 0.552,
  shoulderX: 0.150,
  elbow: [0.238, 0.402, 0.020],
  wrist: [0.296, 0.282, 0.038],
};

const UP = new THREE.Vector3(0, 1, 0);
const FORWARD = new THREE.Vector3(0, 0, 1);

// ---------------------------------------------------------------------------
// Materials
// ---------------------------------------------------------------------------
function createMaterials() {
  const standard = (name, color, roughness, metalness, extra) => {
    const material = new THREE.MeshStandardMaterial({
      color,
      roughness,
      metalness,
      side: THREE.FrontSide,
      ...extra,
    });
    material.name = name;
    return material;
  };

  return {
    steel: standard('clothSteelPlate', 0x8e959c, 0.42, 0.82),
    steelDark: standard('clothSteelRecess', 0x565d66, 0.56, 0.72),
    steelPolished: standard('clothSteelEdge', 0xb3b9bd, 0.26, 0.9),
    goldOld: standard('clothAgedGold', 0xa8864a, 0.44, 0.78),
    goldBright: standard('clothBrightGold', 0xd2b165, 0.3, 0.85),
    iron: standard('clothIronRivet', 0x6b6259, 0.48, 0.72),
    leather: standard('clothDarkLeather', 0x4a3325, 0.72, 0.06),
    leatherBrown: standard('clothSaddleLeather', 0x6d4b31, 0.66, 0.08),
    leatherTan: standard('clothTanLeather', 0x8a6544, 0.62, 0.05),
    clothRed: standard('clothDarkRedWool', 0x6b2023, 0.9, 0.02),
    clothGreen: standard('clothSageWool', 0x59614b, 0.92, 0.02),
    clothOlive: standard('clothOliveCanvas', 0x6c6952, 0.94, 0.02),
    linen: standard('clothCreamLinen', 0xd6cdb4, 0.88, 0.01),
    clothIndigo: standard('clothDeepIndigo', 0x232a52, 0.86, 0.03),
    clothIndigoLight: standard('clothIndigoHighlight', 0x333c6b, 0.82, 0.03),
    gem: standard('clothVioletGem', 0x9a78ff, 0.18, 0.12, {
      emissive: 0x5b33dd,
      emissiveIntensity: 0.85,
    }),
    enamel: standard('clothDarkEnamel', 0x3a1217, 0.36, 0.15),
  };
}

// ---------------------------------------------------------------------------
// Geometry builder with explicit face orientation
// ---------------------------------------------------------------------------
class GeoBuilder {
  constructor() {
    this.positions = [];
    this.indices = [];
  }

  vertex(point) {
    this.positions.push(point.x, point.y, point.z);
    return this.positions.length / 3 - 1;
  }

  pointAt(index) {
    const offset = index * 3;
    return new THREE.Vector3(
      this.positions[offset],
      this.positions[offset + 1],
      this.positions[offset + 2],
    );
  }

  triangle(ia, ib, ic, hint) {
    const a = this.pointAt(ia);
    const b = this.pointAt(ib);
    const c = this.pointAt(ic);
    const normal = new THREE.Vector3().crossVectors(b.sub(a), c.sub(a));
    if (normal.lengthSq() > 1e-14 && normal.dot(hint) < 0) {
      this.indices.push(ia, ic, ib);
    } else {
      this.indices.push(ia, ib, ic);
    }
  }

  quad(ia, ib, ic, id, hint) {
    this.triangle(ia, ib, ic, hint);
    this.triangle(ia, ic, id, hint);
  }

  geometry({ harden = false } = {}) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(this.positions, 3));
    geometry.setIndex(this.indices);
    if (harden) {
      const flat = geometry.toNonIndexed();
      geometry.dispose();
      flat.computeVertexNormals();
      flat.computeBoundingSphere();
      return flat;
    }
    geometry.computeVertexNormals();
    geometry.computeBoundingSphere();
    return geometry;
  }

  buildMesh(material, name, options) {
    const mesh = new THREE.Mesh(this.geometry(options), material);
    mesh.name = name;
    return mesh;
  }
}

// ---------------------------------------------------------------------------
// Ring helpers
// ---------------------------------------------------------------------------
function makeRingY({
  y,
  halfX,
  frontZ,
  backZ,
  cx = 0,
  cz = 0,
  segments = 28,
  power = 0.86,
  foldAmp = 0,
  foldFreq = 0,
  phase = 0,
  startAngle = 0,
}) {
  const points = [];
  for (let i = 0; i < segments; i += 1) {
    const angle = startAngle + (i / segments) * Math.PI * 2;
    const sin = Math.sin(angle);
    const cos = Math.cos(angle);
    const x = Math.sign(sin) * Math.pow(Math.abs(sin), power) * halfX;
    const depth = cos >= 0 ? frontZ : backZ;
    const z = Math.sign(cos) * Math.pow(Math.abs(cos), power) * depth;
    const modulation = 1 + foldAmp * Math.cos(foldFreq * angle + phase);
    points.push(new THREE.Vector3(cx + x * modulation, y, cz + z * modulation));
  }
  return points;
}

function makeRingZ({
  z,
  rx,
  ry,
  cx = 0,
  cy = 0,
  segments = 24,
  power = 0.9,
  foldAmp = 0,
  foldFreq = 0,
  phase = 0,
  startAngle = 0,
}) {
  const points = [];
  for (let i = 0; i < segments; i += 1) {
    const angle = startAngle + (i / segments) * Math.PI * 2;
    const sin = Math.sin(angle);
    const cos = Math.cos(angle);
    const x = Math.sign(sin) * Math.pow(Math.abs(sin), power) * rx;
    const y = Math.sign(cos) * Math.pow(Math.abs(cos), power) * ry;
    const modulation = 1 + foldAmp * Math.cos(foldFreq * angle + phase);
    points.push(new THREE.Vector3(cx + x * modulation, cy + y * modulation, z));
  }
  return points;
}

function scaleRing(points, center, scale) {
  return points.map((point) => center.clone().add(point.clone().sub(center).multiplyScalar(scale)));
}

// ---------------------------------------------------------------------------
// Hollow garment shell
// ---------------------------------------------------------------------------
function addHollowShell(builder, stations, {
  thickness = 0.007,
  axis = 'y',
  rimStart = true,
  rimEnd = true,
  skip = null,
} = {}) {
  const ringSize = stations[0].points.length;
  const outer = [];
  const inner = [];
  const axisVector = axis === 'y' ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(0, 0, 1);

  stations.forEach((station) => {
    const outerRow = [];
    const innerRow = [];
    station.points.forEach((point) => {
      const radial = point.clone().sub(station.center);
      radial.sub(axisVector.clone().multiplyScalar(radial.dot(axisVector)));
      if (radial.lengthSq() < 1e-10) radial.set(0, 0, 1);
      radial.normalize();
      outerRow.push(builder.vertex(point));
      innerRow.push(builder.vertex(point.clone().sub(radial.multiplyScalar(thickness))));
    });
    outer.push(outerRow);
    inner.push(innerRow);
  });

  const skipped = (index) => skip !== null && index >= skip.from && index < skip.to;

  for (let s = 0; s < stations.length - 1; s += 1) {
    for (let i = 0; i < ringSize; i += 1) {
      if (skipped(i)) continue;
      const j = (i + 1) % ringSize;
      const mid = stations[s].points[i].clone()
        .add(stations[s].points[j])
        .add(stations[s + 1].points[j])
        .add(stations[s + 1].points[i])
        .multiplyScalar(0.25);
      const hint = mid.clone().sub(stations[s].center.clone().lerp(stations[s + 1].center, 0.5));
      hint.sub(axisVector.clone().multiplyScalar(hint.dot(axisVector)));
      if (hint.lengthSq() < 1e-10) hint.set(0, 0, 1);
      hint.normalize();

      builder.quad(outer[s][i], outer[s][j], outer[s + 1][j], outer[s + 1][i], hint);
      builder.quad(inner[s][i], inner[s][j], inner[s + 1][j], inner[s + 1][i], hint.clone().negate());
    }
  }

  if (skip !== null) {
    const boundaries = [
      { index: skip.from % ringSize, sign: 1 },
      { index: skip.to % ringSize, sign: -1 },
    ];
    boundaries.forEach(({ index, sign }) => {
      const prev = (index - 1 + ringSize) % ringSize;
      const next = (index + 1) % ringSize;
      for (let s = 0; s < stations.length - 1; s += 1) {
        const tangent = stations[s].points[next].clone().sub(stations[s].points[prev]);
        if (tangent.lengthSq() < 1e-10) continue;
        tangent.normalize().multiplyScalar(sign);
        builder.quad(outer[s][index], outer[s + 1][index], inner[s + 1][index], inner[s][index], tangent);
      }
    });
  }

  const rimHint = (start) => {
    const hint = axisVector.clone().multiplyScalar(start ? -1 : 1);
    return hint;
  };

  if (rimStart) {
    for (let i = 0; i < ringSize; i += 1) {
      if (skipped(i)) continue;
      const j = (i + 1) % ringSize;
      builder.quad(outer[0][i], outer[0][j], inner[0][j], inner[0][i], rimHint(true));
    }
  }
  if (rimEnd) {
    const last = stations.length - 1;
    for (let i = 0; i < ringSize; i += 1) {
      if (skipped(i)) continue;
      const j = (i + 1) % ringSize;
      builder.quad(outer[last][i], outer[last][j], inner[last][j], inner[last][i], rimHint(false));
    }
  }
}

// ---------------------------------------------------------------------------
// Open arc shell (pauldrons, shoulder mantles, cuffs)
// ---------------------------------------------------------------------------
function addArcShell(builder, stations, { segments = 14, thickness = 0.006 } = {}) {
  const outer = [];
  const inner = [];

  stations.forEach((station) => {
    const outerRow = [];
    const innerRow = [];
    for (let i = 0; i <= segments; i += 1) {
      const angle = station.a0 + (station.a1 - station.a0) * (i / segments);
      const radial = new THREE.Vector3(
        Math.sin(angle) * station.rx,
        Math.cos(angle) * station.ry,
        0,
      );
      const point = new THREE.Vector3(radial.x, radial.y, station.z).add(station.center || new THREE.Vector3());
      const direction = radial.clone().normalize();
      outerRow.push(builder.vertex(point));
      innerRow.push(builder.vertex(point.clone().sub(direction.multiplyScalar(thickness))));
    }
    outer.push(outerRow);
    inner.push(innerRow);
  });

  for (let s = 0; s < stations.length - 1; s += 1) {
    for (let i = 0; i < segments; i += 1) {
      const angle = stations[s].a0 + (stations[s].a1 - stations[s].a0) * ((i + 0.5) / segments);
      const hint = new THREE.Vector3(Math.sin(angle), Math.cos(angle), 0);
      builder.quad(outer[s][i], outer[s][i + 1], outer[s + 1][i + 1], outer[s + 1][i], hint);
      builder.quad(inner[s][i], inner[s][i + 1], inner[s + 1][i + 1], inner[s + 1][i], hint.clone().negate());
    }
  }

  // Side rims along the arc ends.
  for (const side of [0, segments]) {
    const sign = side === 0 ? -1 : 1;
    for (let s = 0; s < stations.length - 1; s += 1) {
      const station = stations[Math.min(s + 1, stations.length - 1)];
      const angle = side === 0 ? station.a0 : station.a1;
      const tangent = new THREE.Vector3(Math.cos(angle), -Math.sin(angle), 0).multiplyScalar(sign);
      builder.quad(outer[s][side], outer[s + 1][side], inner[s + 1][side], inner[s][side], tangent);
    }
  }

  // End rims across the arc.
  const firstStation = 0;
  const lastStation = stations.length - 1;
  for (let i = 0; i < segments; i += 1) {
    builder.quad(outer[firstStation][i], outer[firstStation][i + 1], inner[firstStation][i + 1], inner[firstStation][i], new THREE.Vector3(0, 0, -1));
    builder.quad(outer[lastStation][i], outer[lastStation][i + 1], inner[lastStation][i + 1], inner[lastStation][i], new THREE.Vector3(0, 0, 1));
  }
}


// ---------------------------------------------------------------------------
// Slab (collars, lapels, flaps) and Y-axis cowl (hoods, stand collars)
// ---------------------------------------------------------------------------
function addSlab(builder, corners, { thickness = 0.005, normal = new THREE.Vector3(0, 0, 1) } = {}) {
  const n = normal.clone().normalize();
  const front = corners.map((point) => builder.vertex(point.clone().addScaledVector(n, thickness * 0.5)));
  const back = corners.map((point) => builder.vertex(point.clone().addScaledVector(n, -thickness * 0.5)));
  const center = new THREE.Vector3();
  corners.forEach((point) => center.add(point));
  center.multiplyScalar(1 / corners.length);

  builder.quad(front[0], front[1], front[2], front[3], n);
  builder.quad(back[3], back[2], back[1], back[0], n.clone().negate());
  for (let i = 0; i < corners.length; i += 1) {
    const j = (i + 1) % corners.length;
    const mid = corners[i].clone().add(corners[j]).multiplyScalar(0.5);
    const outward = mid.clone().sub(center);
    outward.sub(n.clone().multiplyScalar(outward.dot(n)));
    if (outward.lengthSq() < 1e-10) outward.copy(n);
    builder.quad(front[i], front[j], back[j], back[i], outward.normalize());
  }
}

function addCowlShell(builder, stations, {
  segments = 18,
  thickness = 0.005,
  arcFrom = 0,
  arcTo = Math.PI * 2,
} = {}) {
  const outer = [];
  const inner = [];

  stations.forEach((station) => {
    const outerRow = [];
    const innerRow = [];
    for (let i = 0; i <= segments; i += 1) {
      const angle = arcFrom + (arcTo - arcFrom) * (i / segments);
      const dip = station.yDip ? station.yDip * (0.5 + 0.5 * Math.cos(angle - Math.PI)) : 0;
      const point = new THREE.Vector3(
        Math.sin(angle) * station.rx,
        station.y - dip,
        Math.cos(angle) * station.rz,
      );
      const radial = new THREE.Vector3(Math.sin(angle), 0, Math.cos(angle));
      outerRow.push(builder.vertex(point));
      innerRow.push(builder.vertex(point.clone().addScaledVector(radial, -thickness)));
    }
    outer.push(outerRow);
    inner.push(innerRow);
  });

  for (let s = 0; s < stations.length - 1; s += 1) {
    for (let i = 0; i < segments; i += 1) {
      const angle = arcFrom + (arcTo - arcFrom) * ((i + 0.5) / segments);
      const hint = new THREE.Vector3(Math.sin(angle), 0, Math.cos(angle));
      builder.quad(outer[s][i], outer[s][i + 1], outer[s + 1][i + 1], outer[s + 1][i], hint);
      builder.quad(inner[s][i], inner[s][i + 1], inner[s + 1][i + 1], inner[s + 1][i], hint.clone().negate());
    }
  }

  for (const side of [0, segments]) {
    const sign = side === 0 ? -1 : 1;
    const angle = side === 0 ? arcFrom : arcTo;
    const tangent = new THREE.Vector3(Math.cos(angle), 0, -Math.sin(angle)).multiplyScalar(sign);
    for (let s = 0; s < stations.length - 1; s += 1) {
      builder.quad(outer[s][side], outer[s + 1][side], inner[s + 1][side], inner[s][side], tangent);
    }
  }

  const last = stations.length - 1;
  for (let i = 0; i < segments; i += 1) {
    builder.quad(outer[0][i], outer[0][i + 1], inner[0][i + 1], inner[0][i], new THREE.Vector3(0, -1, 0));
    builder.quad(outer[last][i], outer[last][i + 1], inner[last][i + 1], inner[last][i], new THREE.Vector3(0, 1, 0));
  }
}

// ---------------------------------------------------------------------------
// Cloth panel (hanging garment slab with folds)
// ---------------------------------------------------------------------------
function addClothPanel(builder, {
  widthTop,
  widthBottom,
  height,
  rows = 12,
  cols = 9,
  facing = 1,
  curve = 0.012,
  foldAmp = 0.004,
  foldFreq = 2,
  phase = 0,
  thickness = 0.006,
  taper = 0,
  hemSlant = 0,
  sideCurve = 0,
  yaw = 0,
}) {
  const yawAxis = new THREE.Vector3(0, 1, 0);
  const grid = [];
  for (let r = 0; r < rows; r += 1) {
    const v = r / (rows - 1);
    const row = [];
    for (let c = 0; c < cols; c += 1) {
      const u = c / (cols - 1);
      const halfWidth = (widthTop + (widthBottom - widthTop) * v) * 0.5 * (1 - taper * v * v);
      const x = (u * 2 - 1) * halfWidth;
      const y = -height * v + hemSlant * (u - 0.5) * v;
      const z = facing * (
        curve * Math.pow(v, 1.35)
        + foldAmp * Math.sin(foldFreq * Math.PI * 2 * u + phase) * Math.pow(v, 0.8)
        + sideCurve * Math.pow(u * 2 - 1, 2) * v
      );
      const point = new THREE.Vector3(x, y, z);
      if (yaw !== 0) point.applyAxisAngle(yawAxis, yaw);
      row.push(point);
    }
    grid.push(row);
  }

  const front = grid.map((row) => row.map((point) => builder.vertex(point)));
  const back = grid.map((row, r) => row.map((point, c) => builder.vertex(new THREE.Vector3(
    point.x,
    point.y,
    grid[r][c].z - facing * thickness,
  ))));

  const yawQuaternion = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), yaw);
  const hint = (x, y, z) => new THREE.Vector3(x, y, z).applyQuaternion(yawQuaternion);
  const faceHint = hint(0, 0, facing);
  for (let r = 0; r < rows - 1; r += 1) {
    for (let c = 0; c < cols - 1; c += 1) {
      builder.quad(front[r][c], front[r][c + 1], front[r + 1][c + 1], front[r + 1][c], faceHint);
      builder.quad(back[r][c], back[r][c + 1], back[r + 1][c + 1], back[r + 1][c], faceHint.clone().negate());
    }
  }

  // Edges: top, bottom, sides.
  for (let c = 0; c < cols - 1; c += 1) {
    builder.quad(front[0][c], front[0][c + 1], back[0][c + 1], back[0][c], new THREE.Vector3(0, 1, 0));
    builder.quad(front[rows - 1][c], front[rows - 1][c + 1], back[rows - 1][c + 1], back[rows - 1][c], new THREE.Vector3(0, -1, 0));
  }
  for (let r = 0; r < rows - 1; r += 1) {
    builder.quad(front[r][0], front[r + 1][0], back[r + 1][0], back[r][0], hint(-1, 0, 0));
    builder.quad(front[r][cols - 1], front[r + 1][cols - 1], back[r + 1][cols - 1], back[r][cols - 1], hint(1, 0, 0));
  }

  return {
    grid,
    facing,
    yaw,
    topRow: grid[0],
    bottomRow: grid[rows - 1],
    leftEdge: grid.map((row) => row[0]),
    rightEdge: grid.map((row) => row[cols - 1]),
    innerLeftEdge: grid.map((row) => row[1]),
    innerRightEdge: grid.map((row) => row[cols - 2]),
    innerBottomRow: grid[rows - 2],
  };
}

// ---------------------------------------------------------------------------
// Trim, stitching and hardware
// ---------------------------------------------------------------------------
function addRibbon(builder, points, { width = 0.012, thickness = 0.004, normal = new THREE.Vector3(0, 0, 1) } = {}) {
  if (points.length < 2) return;
  const fixedNormal = typeof normal === 'function' ? null : normal.clone().normalize();
  const rings = points.map((point, index) => {
    const previous = points[Math.max(0, index - 1)];
    const next = points[Math.min(points.length - 1, index + 1)];
    const tangent = next.clone().sub(previous);
    if (tangent.lengthSq() < 1e-10) tangent.set(0, -1, 0);
    tangent.normalize();
    const localNormal = fixedNormal === null ? normal(point, index).clone().normalize() : fixedNormal;
    const binormal = new THREE.Vector3().crossVectors(localNormal, tangent).normalize();
    const halfW = width * 0.5;
    const halfT = thickness * 0.5;
    return {
      tangent,
      binormal,
      normal: localNormal,
      corners: [
        builder.vertex(point.clone().addScaledVector(binormal, halfW).addScaledVector(localNormal, halfT)),
        builder.vertex(point.clone().addScaledVector(binormal, -halfW).addScaledVector(localNormal, halfT)),
        builder.vertex(point.clone().addScaledVector(binormal, -halfW).addScaledVector(localNormal, -halfT)),
        builder.vertex(point.clone().addScaledVector(binormal, halfW).addScaledVector(localNormal, -halfT)),
      ],
    };
  });

  for (let i = 0; i < rings.length - 1; i += 1) {
    const a = rings[i];
    const b = rings[i + 1];
    const mid = a.tangent.clone().add(b.tangent).normalize();
    builder.quad(a.corners[0], a.corners[1], b.corners[1], b.corners[0], a.normal.clone().add(b.normal));
    builder.quad(a.corners[2], a.corners[3], b.corners[3], b.corners[2], a.normal.clone().add(b.normal).negate());
    builder.quad(a.corners[1], a.corners[2], b.corners[2], b.corners[1], a.binormal.clone().negate());
    builder.quad(a.corners[3], a.corners[0], b.corners[0], b.corners[3], a.binormal);
    builder.quad(a.corners[0], a.corners[3], b.corners[3], b.corners[0], mid);
  }

  const first = rings[0];
  const last = rings[rings.length - 1];
  builder.quad(first.corners[0], first.corners[3], first.corners[2], first.corners[1], first.tangent.clone().negate());
  builder.quad(last.corners[0], last.corners[1], last.corners[2], last.corners[3], last.tangent);
}

function samplePolyline(points, spacing) {
  const samples = [];
  for (let i = 0; i < points.length - 1; i += 1) {
    const a = points[i];
    const b = points[i + 1];
    const length = a.distanceTo(b);
    const steps = Math.max(1, Math.round(length / spacing));
    for (let s = 0; s < steps; s += 1) {
      const t = s / steps;
      samples.push({
        point: a.clone().lerp(b, t),
        tangent: b.clone().sub(a).normalize(),
      });
    }
  }
  const last = points[points.length - 1];
  const previous = points[points.length - 2];
  samples.push({ point: last.clone(), tangent: last.clone().sub(previous).normalize() });
  return samples;
}

function addStitchRun(builder, points, {
  normal = new THREE.Vector3(0, 0, 1),
  spacing = 0.011,
  length = 0.008,
  width = 0.0018,
  lift = 0.0016,
} = {}) {
  const n = normal.clone().normalize();
  const samples = samplePolyline(points, spacing);
  samples.forEach(({ point, tangent }) => {
    const along = tangent.clone().normalize();
    const side = new THREE.Vector3().crossVectors(n, along).normalize();
    const center = point.clone().addScaledVector(n, lift);
    addOrientedBox(builder, center, along.multiplyScalar(length * 0.5), n.clone().multiplyScalar(0.0012), side.multiplyScalar(width * 0.5));
  });
}

function addOrientedBox(builder, center, ax, ay, az) {
  const corners = [];
  for (const sx of [-1, 1]) {
    for (const sy of [-1, 1]) {
      for (const sz of [-1, 1]) {
        corners.push(builder.vertex(center.clone().addScaledVector(ax, sx).addScaledVector(ay, sy).addScaledVector(az, sz)));
      }
    }
  }
  // index order: x, y, z bits -> 0:(-,-,-) 1:(-,-,+) 2:(-,+,-) 3:(-,+,+) 4:(+,-,-) 5:(+,-,+) 6:(+,+,-) 7:(+,+,+)
  builder.quad(corners[0], corners[1], corners[3], corners[2], ax.clone().negate());
  builder.quad(corners[4], corners[6], corners[7], corners[5], ax);
  builder.quad(corners[0], corners[4], corners[5], corners[1], ay.clone().negate());
  builder.quad(corners[2], corners[3], corners[7], corners[6], ay);
  builder.quad(corners[0], corners[2], corners[6], corners[4], az.clone().negate());
  builder.quad(corners[1], corners[5], corners[7], corners[3], az);
}

function addRivet(builder, center, normal, radius = 0.0055, segments = 8) {
  const n = normal.clone().normalize();
  const reference = Math.abs(n.y) > 0.9 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 1, 0);
  const ax = new THREE.Vector3().crossVectors(reference, n).normalize();
  const ay = new THREE.Vector3().crossVectors(n, ax).normalize();
  const base = [];
  const mid = [];
  for (let i = 0; i < segments; i += 1) {
    const angle = (i / segments) * Math.PI * 2;
    const dir = ax.clone().multiplyScalar(Math.cos(angle)).addScaledVector(ay, Math.sin(angle));
    base.push(builder.vertex(center.clone().addScaledVector(dir, radius)));
    mid.push(builder.vertex(center.clone().addScaledVector(dir, radius * 0.55).addScaledVector(n, radius * 0.55)));
  }
  const apex = builder.vertex(center.clone().addScaledVector(n, radius * 0.9));
  for (let i = 0; i < segments; i += 1) {
    const j = (i + 1) % segments;
    const angle = ((i + 0.5) / segments) * Math.PI * 2;
    const hint = ax.clone().multiplyScalar(Math.cos(angle)).addScaledVector(ay, Math.sin(angle));
    builder.quad(base[i], base[j], mid[j], mid[i], hint);
    builder.triangle(mid[i], mid[j], apex, hint);
  }
}

function createPlateMesh(materials, materialName, shape, depth, bevel = 0.002) {
  const geometry = new THREE.ExtrudeGeometry(shape, {
    depth,
    bevelEnabled: bevel > 0,
    bevelThickness: bevel,
    bevelSize: bevel * 0.9,
    bevelSegments: 2,
    curveSegments: 10,
  });
  geometry.computeVertexNormals();
  const mesh = new THREE.Mesh(geometry, materials[materialName]);
  return mesh;
}

function roundedRectShape(width, height, radius) {
  const shape = new THREE.Shape();
  const left = -width / 2;
  const right = width / 2;
  const bottom = -height / 2;
  const top = height / 2;
  shape.moveTo(left + radius, bottom);
  shape.lineTo(right - radius, bottom);
  shape.quadraticCurveTo(right, bottom, right, bottom + radius);
  shape.lineTo(right, top - radius);
  shape.quadraticCurveTo(right, top, right - radius, top);
  shape.lineTo(left + radius, top);
  shape.quadraticCurveTo(left, top, left, top - radius);
  shape.lineTo(left, bottom + radius);
  shape.quadraticCurveTo(left, bottom, left + radius, bottom);
  return shape;
}

function createBuckleMesh(materials, width = 0.048, height = 0.036) {
  const outer = roundedRectShape(width, height, 0.008);
  const hole = new THREE.Path();
  const inner = roundedRectShape(width - 0.014, height - 0.014, 0.005);
  hole.curves = inner.curves;
  outer.holes.push(hole);
  return createPlateMesh(materials, 'goldBright', outer, 0.006, 0.0015);
}

// ---------------------------------------------------------------------------
// Shared garment details
// ---------------------------------------------------------------------------
function addGoldRingTrim(builder, ring, center, yOffset, { height = 0.008, radialScale = 1.012, thickness = 0.004 } = {}) {
  const lower = scaleRing(ring, center, radialScale).map((point) => point.clone().setY(point.y + yOffset - height * 0.5));
  const upper = scaleRing(ring, center, radialScale).map((point) => point.clone().setY(point.y + yOffset + height * 0.5));
  addHollowShell(builder, [
    { center: center.clone().setY(center.y + yOffset - height * 0.5), points: lower },
    { center: center.clone().setY(center.y + yOffset + height * 0.5), points: upper },
  ], { thickness, axis: 'y' });
}

function addArmorBand(group, materials, {
  yTop,
  yBottom,
  halfTop,
  frontTop,
  backTop,
  halfBottom,
  frontBottom,
  backBottom,
  segments = 28,
  thickness = 0.008,
  name,
  goldRim = true,
}) {
  const builder = new GeoBuilder();
  const rings = [
    { y: yBottom, halfX: halfBottom, frontZ: frontBottom, backZ: backBottom },
    {
      y: (yTop + yBottom) * 0.5,
      halfX: (halfTop + halfBottom) * 0.5 + 0.002,
      frontZ: (frontTop + frontBottom) * 0.5 + 0.002,
      backZ: (backTop + backBottom) * 0.5 + 0.002,
    },
    { y: yTop, halfX: halfTop, frontZ: frontTop, backZ: backTop },
  ];
  const stations = rings.map((ring) => {
    const points = makeRingY({ ...ring, segments });
    return { center: new THREE.Vector3(0, ring.y, 0), points };
  });
  addHollowShell(builder, stations, { thickness, axis: 'y' });

  if (goldRim) {
    addGoldRingTrim(builder, rings[0].y === undefined ? [] : makeRingY({ ...rings[0], segments }), new THREE.Vector3(0, yBottom, 0), 0.002, {
      height: 0.008,
      radialScale: 1.015,
      thickness: 0.004,
    });
  }

  // Rivets along the upper edge.
  const rivetRing = makeRingY({ ...rings[2], segments });
  [-64, -28, 28, 64, 116, 180, 244].forEach((degrees) => {
    const index = Math.round(((degrees + 360) % 360) / 360 * segments) % segments;
    const point = rivetRing[index];
    const normal = new THREE.Vector3(point.x, 0, point.z).normalize();
    addRivet(builder, point.clone().addScaledVector(normal, 0.001), normal, 0.0052);
  });

  const mesh = builder.buildMesh(materials.steel, name, { harden: true });
  group.add(mesh);
  return mesh;
}

// ---------------------------------------------------------------------------
// Warrior: steel cuirass, layered pauldrons, bracers, waist armor, tabard
// ---------------------------------------------------------------------------
function buildWarriorChest(group, materials) {
  // Geometry is authored in character-space heights; the pivot sits on the Chest bone.
  const content = new THREE.Group();
  content.name = 'Warrior_ChestBody';
  content.position.y = -BODY.chestY;
  group.add(content);

  addArmorBand(content, materials, {
    yTop: 0.566, yBottom: 0.516,
    halfTop: 0.134, frontTop: 0.106, backTop: 0.102,
    halfBottom: 0.153, frontBottom: 0.119, backBottom: 0.113,
    name: 'Warrior_CuirassUpperBand',
  });
  addArmorBand(content, materials, {
    yTop: 0.512, yBottom: 0.466,
    halfTop: 0.156, frontTop: 0.121, backTop: 0.115,
    halfBottom: 0.163, frontBottom: 0.124, backBottom: 0.118,
    name: 'Warrior_CuirassMiddleBand',
  });
  addArmorBand(content, materials, {
    yTop: 0.462, yBottom: 0.414,
    halfTop: 0.163, frontTop: 0.124, backTop: 0.118,
    halfBottom: 0.170, frontBottom: 0.128, backBottom: 0.121,
    name: 'Warrior_CuirassLowerBand',
  });

  // Gorget: low standing collar with a leather inner lining.
  const gorget = new GeoBuilder();
  const gorgetRingTop = makeRingY({ y: 0.612, halfX: 0.086, frontZ: 0.080, backZ: 0.077, segments: 28 });
  const gorgetRingMid = makeRingY({ y: 0.592, halfX: 0.096, frontZ: 0.089, backZ: 0.086, segments: 28 });
  const gorgetRingBottom = makeRingY({ y: 0.568, halfX: 0.108, frontZ: 0.098, backZ: 0.094, segments: 28 });
  addHollowShell(gorget, [
    { center: new THREE.Vector3(0, 0.568, 0), points: gorgetRingBottom },
    { center: new THREE.Vector3(0, 0.592, 0), points: gorgetRingMid },
    { center: new THREE.Vector3(0, 0.612, 0), points: gorgetRingTop },
  ], { thickness: 0.007, axis: 'y' });
  addGoldRingTrim(gorget, gorgetRingTop, new THREE.Vector3(0, 0.612, 0), -0.002, {
    height: 0.008, radialScale: 1.02, thickness: 0.004,
  });
  const gorgetMesh = gorget.buildMesh(materials.steelDark, 'Warrior_Gorget', { harden: true });
  content.add(gorgetMesh);

  // Collar lining ring (dark leather) so the opening reads as padded.
  const lining = new GeoBuilder();
  const liningTop = makeRingY({ y: 0.612, halfX: 0.081, frontZ: 0.075, backZ: 0.072, segments: 24 });
  const liningBottom = makeRingY({ y: 0.582, halfX: 0.091, frontZ: 0.085, backZ: 0.082, segments: 24 });
  addHollowShell(lining, [
    { center: new THREE.Vector3(0, 0.582, 0), points: liningBottom },
    { center: new THREE.Vector3(0, 0.612, 0), points: liningTop },
  ], { thickness: 0.004, axis: 'y', rimStart: false, rimEnd: true });
  content.add(lining.buildMesh(materials.leather, 'Warrior_CollarLining', { harden: false }));

  // Chest straps over both shoulders with buckles at the front.
  const strap = new GeoBuilder();
  const strapRivet = new GeoBuilder();
  [-1, 1].forEach((side) => {
    const x = side * 0.101;
    const points = [
      new THREE.Vector3(x, 0.505, 0.128),
      new THREE.Vector3(x, 0.540, 0.113),
      new THREE.Vector3(x, 0.570, 0.072),
      new THREE.Vector3(x, 0.580, 0.006),
      new THREE.Vector3(x, 0.570, -0.062),
      new THREE.Vector3(x, 0.538, -0.103),
    ];
    addRibbon(strap, points, {
      width: 0.030,
      thickness: 0.007,
      normal: (point) => new THREE.Vector3(point.x * 0.9, (point.y - 0.49) * 1.35, point.z).normalize(),
    });
    for (let i = 0; i < points.length; i += 1) {
      const point = points[i];
      const normal = new THREE.Vector3(point.x * 0.9, (point.y - 0.49) * 1.35, point.z).normalize();
      addRivet(strapRivet, point.clone().addScaledVector(normal, 0.0045), normal, 0.0048, 8);
    }
  });
  content.add(strap.buildMesh(materials.leather, 'Warrior_ShoulderHarness', { harden: true }));
  content.add(strapRivet.buildMesh(materials.iron, 'Warrior_HarnessRivets', { harden: true }));

  [-1, 1].forEach((side) => {
    const buckle = createBuckleMesh(materials, 0.040, 0.030);
    buckle.name = side < 0 ? 'Warrior_HarnessBuckleL' : 'Warrior_HarnessBuckleR';
    buckle.position.set(side * 0.101, 0.512, 0.131);
    buckle.rotation.x = -0.12;
    content.add(buckle);
  });

  // Sternum crest: gold rim, dark red enamel and a small steel boss.
  const crestRim = createPlateMesh(materials, 'goldOld', roundedRectShape(0.072, 0.060, 0.014), 0.010, 0.002);
  crestRim.name = 'Warrior_CrestFrame';
  crestRim.position.set(0, 0.497, 0.1225);
  content.add(crestRim);

  const crestEnamel = createPlateMesh(materials, 'enamel', roundedRectShape(0.052, 0.042, 0.010), 0.006, 0.0015);
  crestEnamel.name = 'Warrior_CrestEnamel';
  crestEnamel.position.set(0, 0.497, 0.1265);
  content.add(crestEnamel);

  const crestBuilder = new GeoBuilder();
  addRivet(crestBuilder, new THREE.Vector3(0, 0.497, 0.1345), new THREE.Vector3(0, 0, 1), 0.010, 10);
  content.add(crestBuilder.buildMesh(materials.steelPolished, 'Warrior_CrestBoss', { harden: false }));
}

function buildWarriorHips(group, materials) {
  const content = new THREE.Group();
  content.name = 'Warrior_HipsBody';
  content.position.y = -BODY.hipsY;
  group.add(content);

  // Belt shell.
  const belt = new GeoBuilder();
  const beltBottom = makeRingY({ y: 0.314, halfX: 0.158, frontZ: 0.120, backZ: 0.114, segments: 28 });
  const beltTop = makeRingY({ y: 0.348, halfX: 0.156, frontZ: 0.118, backZ: 0.112, segments: 28 });
  addHollowShell(belt, [
    { center: new THREE.Vector3(0, 0.314, 0), points: beltBottom },
    { center: new THREE.Vector3(0, 0.348, 0), points: beltTop },
  ], { thickness: 0.010, axis: 'y' });
  content.add(belt.buildMesh(materials.leather, 'Warrior_Belt', { harden: false }));

  // Waist lames.
  addArmorBand(content, materials, {
    yTop: 0.310, yBottom: 0.262,
    halfTop: 0.164, frontTop: 0.124, backTop: 0.118,
    halfBottom: 0.173, frontBottom: 0.131, backBottom: 0.124,
    name: 'Warrior_FauldUpper',
  });
  addArmorBand(content, materials, {
    yTop: 0.267, yBottom: 0.222,
    halfTop: 0.168, frontTop: 0.127, backTop: 0.121,
    halfBottom: 0.177, frontBottom: 0.135, backBottom: 0.128,
    name: 'Warrior_FauldMiddle',
  });
  addArmorBand(content, materials, {
    yTop: 0.227, yBottom: 0.182,
    halfTop: 0.172, frontTop: 0.130, backTop: 0.124,
    halfBottom: 0.182, frontBottom: 0.139, backBottom: 0.132,
    name: 'Warrior_FauldLower',
  });

  // Belt buckle.
  const buckle = createBuckleMesh(materials, 0.070, 0.052);
  buckle.name = 'Warrior_BeltBuckle';
  buckle.position.set(0, 0.331, 0.1215);
  content.add(buckle);

  const tongue = createPlateMesh(materials, 'steelPolished', roundedRectShape(0.016, 0.050, 0.005), 0.005, 0.001);
  tongue.name = 'Warrior_BuckleTongue';
  tongue.position.set(0, 0.331, 0.1275);
  content.add(tongue);

  // Side hanging straps with buckles.
  [-1, 1].forEach((side) => {
    const strapBuilder = new GeoBuilder();
    const x = side * 0.163;
    const points = [
      new THREE.Vector3(x, 0.330, 0.028),
      new THREE.Vector3(x * 1.02, 0.292, 0.030),
      new THREE.Vector3(x * 1.03, 0.258, 0.030),
    ];
    addRibbon(strapBuilder, points, { width: 0.026, thickness: 0.007, normal: new THREE.Vector3(side, 0, 0.05).normalize() });
    const strapMesh = strapBuilder.buildMesh(materials.leatherBrown, side < 0 ? 'Warrior_SideStrapL' : 'Warrior_SideStrapR', { harden: true });
    content.add(strapMesh);

    const sideBuckle = createBuckleMesh(materials, 0.034, 0.026);
    sideBuckle.name = side < 0 ? 'Warrior_SideBuckleL' : 'Warrior_SideBuckleR';
    sideBuckle.position.set(x * 1.04, 0.274, 0.034);
    sideBuckle.rotation.y = side * Math.PI * 0.5;
    content.add(sideBuckle);
  });
}

function buildWarriorTabard(group, materials, facing) {
  const builder = new GeoBuilder();
  const trim = new GeoBuilder();
  const stitches = new GeoBuilder();
  const front = facing > 0;
  const panel = addClothPanel(builder, {
    widthTop: front ? 0.196 : 0.206,
    widthBottom: front ? 0.222 : 0.234,
    height: front ? 0.154 : 0.172,
    rows: 11,
    cols: 10,
    facing,
    curve: front ? 0.016 : 0.018,
    foldAmp: 0.0045,
    foldFreq: 2,
    phase: front ? 0.4 : 1.9,
    thickness: 0.006,
    taper: 0.02,
    sideCurve: 0.006,
  });

  const normal = new THREE.Vector3(0, 0, facing);
  const lift = (points, amount) => points.map((point) => point.clone().addScaledVector(normal, amount));
  addRibbon(trim, lift(panel.bottomRow, 0.0022), { width: 0.014, thickness: 0.005, normal });
  addRibbon(trim, lift(panel.leftEdge, 0.0018), { width: 0.010, thickness: 0.004, normal });
  addRibbon(trim, lift(panel.rightEdge, 0.0018), { width: 0.010, thickness: 0.004, normal });

  addStitchRun(stitches, lift(panel.innerLeftEdge, 0.0026), { normal, spacing: 0.012, length: 0.008 });
  addStitchRun(stitches, lift(panel.innerRightEdge, 0.0026), { normal, spacing: 0.012, length: 0.008 });
  addStitchRun(stitches, lift(panel.innerBottomRow, 0.0026), { normal, spacing: 0.012, length: 0.008 });

  const clothMesh = builder.buildMesh(materials.clothRed, front ? 'Warrior_TabardFrontCloth' : 'Warrior_TabardBackCloth', { harden: false });
  group.add(clothMesh);
  group.add(trim.buildMesh(materials.goldOld, front ? 'Warrior_TabardFrontTrim' : 'Warrior_TabardBackTrim', { harden: true }));
  group.add(stitches.buildMesh(materials.linen, front ? 'Warrior_TabardFrontStitch' : 'Warrior_TabardBackStitch', { harden: true }));

  // Leather belt loops connect the panel to the waistband.
  const loops = new GeoBuilder();
  [-0.080, 0.080].forEach((x) => {
    const points = [
      new THREE.Vector3(x, 0.022, -0.014 * facing),
      new THREE.Vector3(x, 0.010, 0.001 * facing),
      new THREE.Vector3(x, -0.006, 0.005 * facing),
    ];
    addRibbon(loops, points, { width: 0.017, thickness: 0.005, normal: new THREE.Vector3(0, 0, facing) });
  });
  group.add(loops.buildMesh(materials.leatherBrown, front ? 'Warrior_TabardFrontLoops' : 'Warrior_TabardBackLoops', { harden: true }));

  if (front) {
    const emblem = createPlateMesh(materials, 'goldOld', roundedRectShape(0.046, 0.052, 0.010), 0.006, 0.0015);
    emblem.name = 'Warrior_TabardEmblem';
    emblem.position.set(0, -0.048, 0.0045);
    emblem.rotation.x = 0.06;
    group.add(emblem);

    const emblemCore = createPlateMesh(materials, 'enamel', roundedRectShape(0.022, 0.028, 0.006), 0.004, 0.001);
    emblemCore.name = 'Warrior_TabardEmblemCore';
    emblemCore.position.set(0, -0.048, 0.0105);
    emblemCore.rotation.x = 0.06;
    group.add(emblemCore);
  }
}

function buildWarriorBracer(group, materials, side) {
  const builder = new GeoBuilder();
  const rivets = new GeoBuilder();
  const rings = [
    { z: -0.058, rx: 0.043, ry: 0.043 },
    { z: -0.020, rx: 0.047, ry: 0.047 },
    { z: 0.030, rx: 0.049, ry: 0.049 },
    { z: 0.066, rx: 0.052, ry: 0.052 },
    { z: 0.094, rx: 0.060, ry: 0.056 },
  ].map((ring) => ({
    center: new THREE.Vector3(0, 0, ring.z),
    points: makeRingZ({ ...ring, segments: 24, power: 0.92 }),
  }));
  addHollowShell(builder, rings, { thickness: 0.006, axis: 'z' });

  // Gold cuffs at both ends.
  const cuffTop = rings[rings.length - 1];
  const cuffBottom = rings[0];
  addTubeBand(builder, cuffTop.points, 0.012, 0.006, 1.03);
  addTubeBand(builder, cuffBottom.points, 0.010, 0.005, 1.03);

  // Outer steel plate.
  const plateStations = [
    { z: -0.030, rx: 0.050, ry: 0.050, a0: -0.9, a1: 0.9, center: new THREE.Vector3() },
    { z: 0.012, rx: 0.053, ry: 0.053, a0: -0.95, a1: 0.95, center: new THREE.Vector3() },
    { z: 0.052, rx: 0.055, ry: 0.055, a0: -1.0, a1: 1.0, center: new THREE.Vector3() },
  ];
  addArcShell(builder, plateStations, { segments: 10, thickness: 0.006 });

  [-0.045, 0.012, 0.062].forEach((z) => {
    const ring = makeRingZ({ z, rx: 0.054, ry: 0.054, segments: 20 });
    [0.6, 1.6, -0.6].forEach((angle) => {
      const index = Math.round(((angle + Math.PI * 2) % (Math.PI * 2)) / (Math.PI * 2) * 20) % 20;
      const point = ring[index];
      const normal = new THREE.Vector3(point.x, point.y, 0).normalize();
      addRivet(rivets, point.clone().addScaledVector(normal, 0.001), normal, 0.0046, 8);
    });
  });

  // Leather straps beneath the plate.
  const straps = new GeoBuilder();
  [0.000, 0.042].forEach((z) => {
    const strapRing = makeRingZ({ z, rx: 0.050, ry: 0.050, segments: 20 });
    const lower = scaleRing(strapRing, new THREE.Vector3(0, 0, z), 1.02).map((p) => p.clone().setZ(z - 0.008));
    const upper = scaleRing(strapRing, new THREE.Vector3(0, 0, z), 1.02).map((p) => p.clone().setZ(z + 0.008));
    addHollowShell(straps, [
      { center: new THREE.Vector3(0, 0, z - 0.008), points: lower },
      { center: new THREE.Vector3(0, 0, z + 0.008), points: upper },
    ], { thickness: 0.003, axis: 'z' });
  });

  const mesh = builder.buildMesh(materials.steelDark, side === 'L' ? 'Warrior_BracerShellL' : 'Warrior_BracerShellR', { harden: true });
  group.add(mesh);
  group.add(rivets.buildMesh(materials.iron, side === 'L' ? 'Warrior_BracerRivetsL' : 'Warrior_BracerRivetsR', { harden: true }));
  group.add(straps.buildMesh(materials.leather, side === 'L' ? 'Warrior_BracerStrapsL' : 'Warrior_BracerStrapsR', { harden: false }));
}

function addTubeBand(builder, baseRing, width, thickness, scale = 1.02) {
  const centerZ = baseRing[0].z;
  const lower = scaleRing(baseRing, new THREE.Vector3(0, 0, centerZ), scale).map((p) => p.clone().setZ(centerZ - width * 0.5));
  const upper = scaleRing(baseRing, new THREE.Vector3(0, 0, centerZ), scale).map((p) => p.clone().setZ(centerZ + width * 0.5));
  addHollowShell(builder, [
    { center: new THREE.Vector3(0, 0, centerZ - width * 0.5), points: lower },
    { center: new THREE.Vector3(0, 0, centerZ + width * 0.5), points: upper },
  ], { thickness, axis: 'z' });
}

function buildWarriorPauldron(group, materials, side) {
  const builder = new GeoBuilder();
  const rivets = new GeoBuilder();
  const layers = [
    { z0: -0.010, z1: 0.030, rx: 0.076, ry: 0.070, arc: 2.02 },
    { z0: 0.034, z1: 0.068, rx: 0.082, ry: 0.075, arc: 1.96 },
    { z0: 0.072, z1: 0.110, rx: 0.087, ry: 0.079, arc: 1.90 },
  ];

  layers.forEach((layer, index) => {
    const stations = [
      {
        z: layer.z0,
        rx: layer.rx * 0.94,
        ry: layer.ry * 0.94,
        a0: -layer.arc * 0.5,
        a1: layer.arc * 0.5,
        center: new THREE.Vector3(),
      },
      {
        z: layer.z0 + (layer.z1 - layer.z0) * 0.45,
        rx: layer.rx,
        ry: layer.ry,
        a0: -layer.arc * 0.5 - 0.05,
        a1: layer.arc * 0.5 + 0.05,
        center: new THREE.Vector3(),
      },
      {
        z: layer.z1,
        rx: layer.rx * 1.02,
        ry: layer.ry * 1.01,
        a0: -layer.arc * 0.5 - 0.09,
        a1: layer.arc * 0.5 + 0.09,
        center: new THREE.Vector3(),
      },
    ];
    addArcShell(builder, stations, { segments: 16, thickness: 0.006 });

    // Gold piped rim on the lower edge of each lame.
    const rimRing = [];
    const count = 17;
    for (let i = 0; i < count; i += 1) {
      const angle = -layer.arc * 0.5 - 0.09 + (layer.arc + 0.18) * (i / (count - 1));
      rimRing.push(new THREE.Vector3(
        Math.sin(angle) * layer.rx * 1.03,
        Math.cos(angle) * layer.ry * 1.02,
        layer.z1 + 0.002,
      ));
    }
    addRibbon(builder, rimRing, { width: 0.010, thickness: 0.0035, normal: new THREE.Vector3(0, 0, 1) });

    // Rivets along the upper edge.
    const rivetCount = 5;
    for (let i = 0; i < rivetCount; i += 1) {
      const angle = -layer.arc * 0.44 + (layer.arc * 0.88) * (i / (rivetCount - 1));
      const normal = new THREE.Vector3(Math.sin(angle), Math.cos(angle), 0).normalize();
      const point = new THREE.Vector3(
        normal.x * layer.rx * 0.99,
        normal.y * layer.ry * 0.99,
        layer.z0 + (layer.z1 - layer.z0) * 0.28,
      );
      addRivet(rivets, point, normal, 0.0048, 8);
    }
  });

  // Leather padding visible between the lames.
  const padding = new GeoBuilder();
  const padStations = [
    { z: -0.016, rx: 0.066, ry: 0.062, a0: -1.08, a1: 1.08, center: new THREE.Vector3() },
    { z: 0.072, rx: 0.072, ry: 0.067, a0: -1.08, a1: 1.08, center: new THREE.Vector3() },
    { z: 0.118, rx: 0.077, ry: 0.071, a0: -1.08, a1: 1.08, center: new THREE.Vector3() },
  ];
  addArcShell(padding, padStations, { segments: 14, thickness: 0.005 });
  group.add(padding.buildMesh(materials.leather, side === 'L' ? 'Warrior_PauldronPaddingL' : 'Warrior_PauldronPaddingR', { harden: false }));

  group.add(builder.buildMesh(materials.steel, side === 'L' ? 'Warrior_PauldronPlatesL' : 'Warrior_PauldronPlatesR', { harden: true }));
  group.add(rivets.buildMesh(materials.iron, side === 'L' ? 'Warrior_PauldronRivetsL' : 'Warrior_PauldronRivetsR', { harden: true }));
}


// ---------------------------------------------------------------------------
// Archer: sage wool coat, cream lapels, leather belt and pouches, forked hems
// ---------------------------------------------------------------------------
function buildArcherChest(group, materials) {
  const content = new THREE.Group();
  content.name = 'Archer_ChestBody';
  content.position.y = -BODY.chestY;
  group.add(content);

  const coat = new GeoBuilder();
  const coatStations = [
    { y: 0.352, halfX: 0.166, frontZ: 0.130, backZ: 0.124 },
    { y: 0.400, halfX: 0.168, frontZ: 0.132, backZ: 0.126 },
    { y: 0.460, halfX: 0.164, frontZ: 0.129, backZ: 0.123 },
    { y: 0.515, halfX: 0.154, frontZ: 0.122, backZ: 0.117 },
    { y: 0.558, halfX: 0.134, frontZ: 0.109, backZ: 0.105 },
    { y: 0.588, halfX: 0.106, frontZ: 0.092, backZ: 0.089 },
  ].map((station) => ({
    center: new THREE.Vector3(0, station.y, 0),
    points: makeRingY({ ...station, segments: 32, foldAmp: 0.0035, foldFreq: 8 }),
  }));
  addHollowShell(coat, coatStations, { thickness: 0.006, axis: 'y' });
  content.add(coat.buildMesh(materials.clothGreen, 'Archer_CoatBody', { harden: false }));

  const hemBuilder = new GeoBuilder();
  const hemRing = makeRingY({ y: 0.356, halfX: 0.169, frontZ: 0.133, backZ: 0.127, segments: 32 });
  addRibbon(hemBuilder, hemRing.concat([hemRing[0]]), {
    width: 0.015,
    thickness: 0.005,
    normal: (point) => new THREE.Vector3(point.x, 0, point.z).normalize(),
  });
  content.add(hemBuilder.buildMesh(materials.leatherBrown, 'Archer_CoatHemBand', { harden: true }));

  // Cream stand collar, open toward the front so it never rises over the chin.
  const collar = new GeoBuilder();
  addCowlShell(collar, [
    { y: 0.552, rx: 0.118, rz: 0.104 },
    { y: 0.582, rx: 0.106, rz: 0.098 },
    { y: 0.606, rx: 0.096, rz: 0.092 },
  ], { segments: 18, thickness: 0.004, arcFrom: 0.42, arcTo: Math.PI * 2 - 0.42 });
  content.add(collar.buildMesh(materials.linen, 'Archer_CreamCollar', { harden: false }));

  // Folded lapels.
  const lapels = new GeoBuilder();
  const lapelStitch = new GeoBuilder();
  [-1, 1].forEach((side) => {
    const corners = [
      new THREE.Vector3(side * 0.106, 0.585, 0.074),
      new THREE.Vector3(side * 0.026, 0.588, 0.100),
      new THREE.Vector3(side * 0.004, 0.492, 0.128),
      new THREE.Vector3(side * 0.104, 0.508, 0.098),
    ];
    addSlab(lapels, corners, { thickness: 0.006, normal: new THREE.Vector3(0, 0, 1) });
    addStitchRun(lapelStitch, [
      new THREE.Vector3(side * 0.030, 0.578, 0.105),
      new THREE.Vector3(side * 0.010, 0.500, 0.131),
    ], { normal: new THREE.Vector3(0, 0, 1), spacing: 0.012, length: 0.007 });
  });
  content.add(lapels.buildMesh(materials.linen, 'Archer_CreamLapels', { harden: true }));
  content.add(lapelStitch.buildMesh(materials.leatherTan, 'Archer_LapelStitch', { harden: true }));

  // Front placket, coat edges and buttons.
  const placketPoints = [
    new THREE.Vector3(0, 0.578, 0.096),
    new THREE.Vector3(0, 0.540, 0.116),
    new THREE.Vector3(0, 0.500, 0.127),
    new THREE.Vector3(0, 0.460, 0.132),
    new THREE.Vector3(0, 0.420, 0.134),
    new THREE.Vector3(0, 0.382, 0.132),
    new THREE.Vector3(0, 0.356, 0.128),
  ];
  const placket = new GeoBuilder();
  addRibbon(placket, placketPoints, { width: 0.040, thickness: 0.004, normal: new THREE.Vector3(0, 0, 1) });
  content.add(placket.buildMesh(materials.linen, 'Archer_FrontPlacket', { harden: true }));

  const placketStitch = new GeoBuilder();
  addStitchRun(placketStitch, placketPoints.map((point) => new THREE.Vector3(point.x - 0.016, point.y, point.z + 0.003)), {
    normal: new THREE.Vector3(0, 0, 1), spacing: 0.012, length: 0.007,
  });
  addStitchRun(placketStitch, placketPoints.map((point) => new THREE.Vector3(point.x + 0.016, point.y, point.z + 0.003)), {
    normal: new THREE.Vector3(0, 0, 1), spacing: 0.012, length: 0.007,
  });
  content.add(placketStitch.buildMesh(materials.leatherTan, 'Archer_PlacketStitch', { harden: true }));

  const coatEdge = new GeoBuilder();
  [-1, 1].forEach((side) => {
    addRibbon(coatEdge, placketPoints.map((point) => new THREE.Vector3(side * 0.024, point.y, point.z + 0.0015)), {
      width: 0.012,
      thickness: 0.004,
      normal: new THREE.Vector3(0, 0, 1),
    });
  });
  content.add(coatEdge.buildMesh(materials.clothOlive, 'Archer_CoatEdges', { harden: true }));

  const buttons = new GeoBuilder();
  [0.545, 0.505, 0.465, 0.425, 0.390].forEach((y, index) => {
    const point = placketPoints[Math.min(index + 1, placketPoints.length - 2)];
    addRivet(buttons, new THREE.Vector3(0, y, point.z + 0.005), new THREE.Vector3(0, 0, 1), 0.0055, 8);
  });
  content.add(buttons.buildMesh(materials.iron, 'Archer_CoatButtons', { harden: true }));

  // Diagonal leather chest strap with buckle and rivets.
  const strap = new GeoBuilder();
  const strapRivets = new GeoBuilder();
  const strapPoints = [
    new THREE.Vector3(-0.098, 0.556, 0.100),
    new THREE.Vector3(-0.060, 0.522, 0.125),
    new THREE.Vector3(0, 0.474, 0.136),
    new THREE.Vector3(0.060, 0.428, 0.137),
    new THREE.Vector3(0.103, 0.392, 0.130),
  ];
  addRibbon(strap, strapPoints, { width: 0.030, thickness: 0.006, normal: new THREE.Vector3(0, 0, 1) });
  [0.10, 0.30, 0.70, 0.90].forEach((t) => {
    const index = Math.min(strapPoints.length - 2, Math.floor(t * (strapPoints.length - 1)));
    const localT = t * (strapPoints.length - 1) - index;
    const point = strapPoints[index].clone().lerp(strapPoints[index + 1], localT);
    addRivet(strapRivets, point.clone().add(new THREE.Vector3(0, 0, 0.005)), new THREE.Vector3(0, 0, 1), 0.0046, 8);
  });
  content.add(strap.buildMesh(materials.leatherBrown, 'Archer_ChestStrap', { harden: true }));
  content.add(strapRivets.buildMesh(materials.iron, 'Archer_StrapRivets', { harden: true }));

  const strapBuckle = createBuckleMesh(materials, 0.040, 0.030);
  strapBuckle.name = 'Archer_StrapBuckle';
  strapBuckle.position.set(0, 0.478, 0.140);
  strapBuckle.rotation.z = 0.9;
  content.add(strapBuckle);
}

function buildArcherHem(group, materials, {
  facing = 1,
  widthTop = 0.104,
  widthBottom = 0.124,
  height = 0.146,
  hemSlant = 0,
  phase = 0,
  name = 'Hem',
  innerSide = 'left',
} = {}) {
  const builder = new GeoBuilder();
  const trim = new GeoBuilder();
  const stitch = new GeoBuilder();
  const panel = addClothPanel(builder, {
    widthTop,
    widthBottom,
    height,
    rows: 11,
    cols: 9,
    facing,
    curve: 0.012,
    foldAmp: 0.0045,
    foldFreq: 2,
    phase,
    thickness: 0.006,
    taper: 0.02,
    hemSlant,
    sideCurve: 0.004,
  });

  const normal = new THREE.Vector3(0, 0, facing);
  const lift = (points, amount) => points.map((point) => point.clone().addScaledVector(normal, amount));
  addRibbon(trim, lift(panel.bottomRow, 0.002), { width: 0.013, thickness: 0.004, normal });
  addRibbon(trim, lift(panel.leftEdge, 0.0016), { width: 0.009, thickness: 0.0035, normal });
  addRibbon(trim, lift(panel.rightEdge, 0.0016), { width: 0.009, thickness: 0.0035, normal });

  const stitchEdge = innerSide === 'left' ? panel.innerLeftEdge : panel.innerRightEdge;
  addStitchRun(stitch, lift(stitchEdge, 0.0026), { normal, spacing: 0.013, length: 0.008 });
  addStitchRun(stitch, lift(panel.innerBottomRow, 0.0026), { normal, spacing: 0.013, length: 0.008 });

  group.add(builder.buildMesh(materials.clothGreen, `${name}Cloth`, { harden: false }));
  group.add(trim.buildMesh(materials.linen, `${name}Lining`, { harden: true }));
  group.add(stitch.buildMesh(materials.linen, `${name}Stitch`, { harden: true }));
}

function buildArcherHips(group, materials) {
  const content = new THREE.Group();
  content.name = 'Archer_HipsBody';
  content.position.y = -BODY.hipsY;
  group.add(content);

  const belt = new GeoBuilder();
  const beltBottom = makeRingY({ y: 0.310, halfX: 0.166, frontZ: 0.129, backZ: 0.123, segments: 28 });
  const beltTop = makeRingY({ y: 0.354, halfX: 0.163, frontZ: 0.127, backZ: 0.121, segments: 28 });
  addHollowShell(belt, [
    { center: new THREE.Vector3(0, 0.310, 0), points: beltBottom },
    { center: new THREE.Vector3(0, 0.354, 0), points: beltTop },
  ], { thickness: 0.010, axis: 'y' });
  content.add(belt.buildMesh(materials.leatherBrown, 'Archer_Belt', { harden: false }));

  const loops = new GeoBuilder();
  [-1.05, -0.35, 0.35, 1.05].forEach((angle) => {
    const x = Math.sin(angle) * 0.164;
    const z = Math.cos(angle) * 0.127;
    const normal = new THREE.Vector3(x, 0, z).normalize();
    const points = [
      new THREE.Vector3(x, 0.312, z).addScaledVector(normal, 0.001),
      new THREE.Vector3(x, 0.332, z).addScaledVector(normal, 0.009),
      new THREE.Vector3(x, 0.353, z).addScaledVector(normal, 0.001),
    ];
    addRibbon(loops, points, { width: 0.014, thickness: 0.004, normal });
  });
  content.add(loops.buildMesh(materials.leather, 'Archer_BeltLoops', { harden: true }));

  const buckle = createBuckleMesh(materials, 0.052, 0.038);
  buckle.name = 'Archer_BeltBuckle';
  buckle.position.set(0, 0.332, 0.132);
  content.add(buckle);

  // Right-hip pouch (character right = glTF -X).
  const pouch = createPlateMesh(materials, 'leatherBrown', roundedRectShape(0.085, 0.092, 0.014), 0.044, 0.004);
  pouch.name = 'Archer_PouchBody';
  pouch.position.set(-0.150, 0.282, 0.058);
  pouch.rotation.y = -Math.PI * 0.5;
  content.add(pouch);

  const pouchFlap = createPlateMesh(materials, 'leatherTan', roundedRectShape(0.090, 0.050, 0.012), 0.008, 0.002);
  pouchFlap.name = 'Archer_PouchFlap';
  pouchFlap.position.set(-0.196, 0.306, 0.058);
  pouchFlap.rotation.y = -Math.PI * 0.5;
  content.add(pouchFlap);

  const pouchStuds = new GeoBuilder();
  addRivet(pouchStuds, new THREE.Vector3(-0.206, 0.294, 0.058), new THREE.Vector3(-1, 0, 0), 0.006, 8);
  content.add(pouchStuds.buildMesh(materials.goldOld, 'Archer_PouchStud', { harden: true }));

  // Left-hip utility pouch.
  const smallPouch = createPlateMesh(materials, 'leatherTan', roundedRectShape(0.058, 0.070, 0.010), 0.028, 0.003);
  smallPouch.name = 'Archer_SmallPouch';
  smallPouch.position.set(0.152, 0.288, 0.086);
  smallPouch.rotation.y = Math.PI * 0.5;
  content.add(smallPouch);

  const smallFlap = createPlateMesh(materials, 'leatherBrown', roundedRectShape(0.062, 0.036, 0.009), 0.006, 0.002);
  smallFlap.name = 'Archer_SmallPouchFlap';
  smallFlap.position.set(0.181, 0.308, 0.086);
  smallFlap.rotation.y = Math.PI * 0.5;
  content.add(smallFlap);
}

function buildArcherShoulder(group, materials, side) {
  const plates = new GeoBuilder();
  const studs = new GeoBuilder();
  const layers = [
    { z0: -0.020, z1: 0.030, rx: 0.072, ry: 0.066, arc: 1.92 },
    { z0: 0.034, z1: 0.076, rx: 0.078, ry: 0.071, arc: 1.82 },
  ];
  layers.forEach((layer) => {
    addArcShell(plates, [
      { z: layer.z0, rx: layer.rx * 0.96, ry: layer.ry * 0.96, a0: -layer.arc * 0.5, a1: layer.arc * 0.5, center: new THREE.Vector3() },
      { z: layer.z1, rx: layer.rx, ry: layer.ry, a0: -layer.arc * 0.5 - 0.04, a1: layer.arc * 0.5 + 0.04, center: new THREE.Vector3() },
    ], { segments: 14, thickness: 0.005 });
    const rim = [];
    for (let i = 0; i <= 14; i += 1) {
      const angle = -layer.arc * 0.5 - 0.04 + (layer.arc + 0.08) * (i / 14);
      rim.push(new THREE.Vector3(Math.sin(angle) * layer.rx * 1.02, Math.cos(angle) * layer.ry * 1.01, layer.z1 + 0.001));
    }
    addRibbon(plates, rim, { width: 0.008, thickness: 0.003, normal: new THREE.Vector3(0, 0, 1) });
    for (let i = 0; i < 4; i += 1) {
      const angle = -layer.arc * 0.4 + layer.arc * 0.8 * (i / 3);
      const normal = new THREE.Vector3(Math.sin(angle), Math.cos(angle), 0).normalize();
      addRivet(studs, new THREE.Vector3(normal.x * layer.rx * 0.99, normal.y * layer.ry * 0.99, layer.z0 + 0.012), normal, 0.0042, 8);
    }
  });
  group.add(plates.buildMesh(materials.leatherBrown, side === 'L' ? 'Archer_ShoulderCapL' : 'Archer_ShoulderCapR', { harden: true }));
  group.add(studs.buildMesh(materials.iron, side === 'L' ? 'Archer_ShoulderStudsL' : 'Archer_ShoulderStudsR', { harden: true }));
}

function buildArcherSleeve(group, materials, side) {
  const builder = new GeoBuilder();
  const rings = [
    { z: -0.058, rx: 0.060, ry: 0.060 },
    { z: -0.012, rx: 0.064, ry: 0.064 },
    { z: 0.044, rx: 0.068, ry: 0.068 },
    { z: 0.074, rx: 0.072, ry: 0.072 },
  ].map((ring) => ({
    center: new THREE.Vector3(0, 0, ring.z),
    points: makeRingZ({ ...ring, segments: 24, foldAmp: 0.006, foldFreq: 6 }),
  }));
  addHollowShell(builder, rings, { thickness: 0.005, axis: 'z' });

  const cuff = new GeoBuilder();
  const cuffLower = makeRingZ({ z: 0.068, rx: 0.074, ry: 0.074, segments: 24 });
  const cuffUpper = makeRingZ({ z: 0.086, rx: 0.076, ry: 0.076, segments: 24 });
  addHollowShell(cuff, [
    { center: new THREE.Vector3(0, 0, 0.068), points: cuffLower },
    { center: new THREE.Vector3(0, 0, 0.086), points: cuffUpper },
  ], { thickness: 0.005, axis: 'z' });

  group.add(builder.buildMesh(materials.clothGreen, side === 'L' ? 'Archer_SleeveL' : 'Archer_SleeveR', { harden: false }));
  group.add(cuff.buildMesh(materials.linen, side === 'L' ? 'Archer_SleeveCuffL' : 'Archer_SleeveCuffR', { harden: false }));
}

function buildArcherBracer(group, materials, side) {
  const builder = new GeoBuilder();
  const straps = new GeoBuilder();
  const rings = [
    { z: -0.056, rx: 0.043, ry: 0.043 },
    { z: -0.014, rx: 0.046, ry: 0.046 },
    { z: 0.036, rx: 0.048, ry: 0.048 },
    { z: 0.078, rx: 0.052, ry: 0.052 },
    { z: 0.098, rx: 0.058, ry: 0.056 },
  ].map((ring) => ({
    center: new THREE.Vector3(0, 0, ring.z),
    points: makeRingZ({ ...ring, segments: 22 }),
  }));
  addHollowShell(builder, rings, { thickness: 0.004, axis: 'z' });

  // Light tan edge band at the wrist.
  const edge = new GeoBuilder();
  addTubeBand(edge, rings[rings.length - 1].points, 0.014, 0.004, 1.02);

  [0.004, 0.050].forEach((z) => {
    const strapRing = makeRingZ({ z, rx: 0.051, ry: 0.051, segments: 20 });
    const lower = scaleRing(strapRing, new THREE.Vector3(0, 0, z), 1.03).map((p) => p.clone().setZ(z - 0.007));
    const upper = scaleRing(strapRing, new THREE.Vector3(0, 0, z), 1.03).map((p) => p.clone().setZ(z + 0.007));
    addHollowShell(straps, [
      { center: new THREE.Vector3(0, 0, z - 0.007), points: lower },
      { center: new THREE.Vector3(0, 0, z + 0.007), points: upper },
    ], { thickness: 0.003, axis: 'z' });
  });

  const studs = new GeoBuilder();
  [0.35, 1.2, -0.5].forEach((angle) => {
    const normal = new THREE.Vector3(Math.sin(angle), Math.cos(angle), 0).normalize();
    addRivet(studs, new THREE.Vector3(normal.x * 0.052, normal.y * 0.052, 0.02), normal, 0.0042, 8);
  });

  group.add(builder.buildMesh(materials.leatherBrown, side === 'L' ? 'Archer_BracerL' : 'Archer_BracerR', { harden: true }));
  group.add(edge.buildMesh(materials.leatherTan, side === 'L' ? 'Archer_BracerEdgeL' : 'Archer_BracerEdgeR', { harden: true }));
  group.add(straps.buildMesh(materials.leather, side === 'L' ? 'Archer_BracerStrapsL' : 'Archer_BracerStrapsR', { harden: false }));
  group.add(studs.buildMesh(materials.iron, side === 'L' ? 'Archer_BracerStudsL' : 'Archer_BracerStudsR', { harden: true }));
}

// ---------------------------------------------------------------------------
// Mage: open indigo robe, cream lining, gold trim, glowing clasp, long cloak
// ---------------------------------------------------------------------------
function buildMageChest(group, materials) {
  const content = new THREE.Group();
  content.name = 'Mage_ChestBody';
  content.position.y = -BODY.chestY;
  group.add(content);

  const underRobe = new GeoBuilder();
  addHollowShell(underRobe, [
    { y: 0.360, halfX: 0.150, frontZ: 0.118, backZ: 0.112 },
    { y: 0.430, halfX: 0.152, frontZ: 0.120, backZ: 0.114 },
    { y: 0.500, halfX: 0.148, frontZ: 0.117, backZ: 0.111 },
    { y: 0.550, halfX: 0.132, frontZ: 0.106, backZ: 0.101 },
    { y: 0.585, halfX: 0.104, frontZ: 0.090, backZ: 0.087 },
  ].map((station) => ({
    center: new THREE.Vector3(0, station.y, 0),
    points: makeRingY({ ...station, segments: 28, foldAmp: 0.002, foldFreq: 6 }),
  })), { thickness: 0.004, axis: 'y' });
  content.add(underRobe.buildMesh(materials.linen, 'Mage_UnderRobe', { harden: false }));

  const robeStations = [
    { y: 0.352, halfX: 0.158, frontZ: 0.124, backZ: 0.118 },
    { y: 0.410, halfX: 0.163, frontZ: 0.128, backZ: 0.122 },
    { y: 0.470, halfX: 0.159, frontZ: 0.125, backZ: 0.119 },
    { y: 0.525, halfX: 0.149, frontZ: 0.118, backZ: 0.113 },
    { y: 0.565, halfX: 0.129, frontZ: 0.105, backZ: 0.101 },
    { y: 0.588, halfX: 0.104, frontZ: 0.091, backZ: 0.088 },
  ].map((station) => ({
    center: new THREE.Vector3(0, station.y, 0),
    points: makeRingY({ ...station, segments: 32, foldAmp: 0.0035, foldFreq: 7, startAngle: -Math.PI * 0.5 }),
  }));

  const robe = new GeoBuilder();
  addHollowShell(robe, robeStations, { thickness: 0.007, axis: 'y', skip: { from: 6, to: 10 } });
  content.add(robe.buildMesh(materials.clothIndigo, 'Mage_OpenRobe', { harden: false }));

  // Gold piping down both open front edges.
  const trim = new GeoBuilder();
  [6, 10].forEach((index) => {
    const edge = robeStations.map((station) => station.points[index].clone());
    addRibbon(trim, edge, {
      width: 0.013,
      thickness: 0.004,
      normal: (point) => new THREE.Vector3(point.x * 1.6, 0, point.z).normalize(),
    });
  });
  content.add(trim.buildMesh(materials.goldOld, 'Mage_RobeOpeningTrim', { harden: true }));

  // Cream stand collar with gold edging.
  const collar = new GeoBuilder();
  addCowlShell(collar, [
    { y: 0.558, rx: 0.110, rz: 0.101 },
    { y: 0.588, rx: 0.099, rz: 0.094 },
    { y: 0.612, rx: 0.090, rz: 0.087 },
  ], { segments: 18, thickness: 0.004, arcFrom: 0.55, arcTo: Math.PI * 2 - 0.55 });
  content.add(collar.buildMesh(materials.linen, 'Mage_CreamCollar', { harden: false }));

  const collarTrim = new GeoBuilder();
  const collarTop = [];
  for (let i = 0; i <= 18; i += 1) {
    const angle = 0.55 + (Math.PI * 2 - 1.1) * (i / 18);
    collarTop.push(new THREE.Vector3(Math.sin(angle) * 0.091, 0.613, Math.cos(angle) * 0.088));
  }
  addRibbon(collarTrim, collarTop, {
    width: 0.009,
    thickness: 0.003,
    normal: (point) => new THREE.Vector3(Math.sin(Math.atan2(point.x, point.z)), 0, Math.cos(Math.atan2(point.x, point.z))),
  });
  content.add(collarTrim.buildMesh(materials.goldOld, 'Mage_CollarTrim', { harden: true }));

  // Glowing gem clasp.
  const setting = new THREE.Mesh(new THREE.TorusGeometry(0.026, 0.006, 10, 22), materials.goldBright);
  setting.name = 'Mage_GemSetting';
  setting.position.set(0, 0.505, 0.120);
  content.add(setting);

  const gem = new THREE.Mesh(new THREE.IcosahedronGeometry(0.021, 0), materials.gem);
  gem.name = 'Mage_Gem';
  gem.position.set(0, 0.505, 0.127);
  gem.scale.set(1, 1.15, 0.85);
  content.add(gem);

  const claws = new GeoBuilder();
  [[-0.022, 0], [0.022, 0], [0, -0.022], [0, 0.022]].forEach(([dx, dy]) => {
    addRivet(claws, new THREE.Vector3(dx, 0.505 + dy, 0.127), new THREE.Vector3(0, 0, 1), 0.005, 7);
  });
  content.add(claws.buildMesh(materials.goldBright, 'Mage_GemClaws', { harden: true }));

  const chains = new GeoBuilder();
  [-1, 1].forEach((side) => {
    addRibbon(chains, [
      new THREE.Vector3(side * 0.020, 0.515, 0.125),
      new THREE.Vector3(side * 0.062, 0.532, 0.118),
      new THREE.Vector3(side * 0.100, 0.550, 0.104),
      new THREE.Vector3(side * 0.122, 0.566, 0.086),
    ], { width: 0.006, thickness: 0.003, normal: new THREE.Vector3(0, 0, 1) });
  });
  content.add(chains.buildMesh(materials.goldOld, 'Mage_ClaspChains', { harden: true }));
}

function buildMageShoulder(group, materials, side) {
  const cloth = new GeoBuilder();
  const trim = new GeoBuilder();
  const layers = [
    { z0: -0.035, z1: 0.073, rx: 0.086, ry: 0.079, arc: 2.16 },
    { z0: 0.077, z1: 0.130, rx: 0.096, ry: 0.087, arc: 2.00 },
  ];
  layers.forEach((layer) => {
    addArcShell(cloth, [
      { z: layer.z0, rx: layer.rx * 0.93, ry: layer.ry * 0.93, a0: -layer.arc * 0.5, a1: layer.arc * 0.5, center: new THREE.Vector3() },
      { z: layer.z0 + (layer.z1 - layer.z0) * 0.5, rx: layer.rx, ry: layer.ry, a0: -layer.arc * 0.5 - 0.05, a1: layer.arc * 0.5 + 0.05, center: new THREE.Vector3() },
      { z: layer.z1, rx: layer.rx * 1.02, ry: layer.ry * 1.01, a0: -layer.arc * 0.5 - 0.10, a1: layer.arc * 0.5 + 0.10, center: new THREE.Vector3() },
    ], { segments: 16, thickness: 0.006 });
  });

  const rim = [];
  const lastLayer = layers[layers.length - 1];
  for (let i = 0; i <= 16; i += 1) {
    const angle = -lastLayer.arc * 0.5 - 0.10 + (lastLayer.arc + 0.20) * (i / 16);
    rim.push(new THREE.Vector3(Math.sin(angle) * lastLayer.rx * 1.03, Math.cos(angle) * lastLayer.ry * 1.02, lastLayer.z1 + 0.002));
  }
  addRibbon(trim, rim, { width: 0.010, thickness: 0.0035, normal: new THREE.Vector3(0, 0, 1) });

  const lining = new GeoBuilder();
  addArcShell(lining, [
    { z: lastLayer.z1 + 0.002, rx: lastLayer.rx * 1.02, ry: lastLayer.ry * 1.01, a0: -lastLayer.arc * 0.5 - 0.10, a1: lastLayer.arc * 0.5 + 0.10, center: new THREE.Vector3() },
    { z: lastLayer.z1 + 0.016, rx: lastLayer.rx * 1.02, ry: lastLayer.ry * 1.01, a0: -lastLayer.arc * 0.5 - 0.10, a1: lastLayer.arc * 0.5 + 0.10, center: new THREE.Vector3() },
  ], { segments: 16, thickness: 0.004 });

  const clasp = new GeoBuilder();
  addRivet(clasp, new THREE.Vector3(0, lastLayer.ry * 0.98, -0.020), new THREE.Vector3(0, 1, 0), 0.010, 10);

  group.add(cloth.buildMesh(materials.clothIndigo, side === 'L' ? 'Mage_MantleClothL' : 'Mage_MantleClothR', { harden: false }));
  group.add(lining.buildMesh(materials.linen, side === 'L' ? 'Mage_MantleLiningL' : 'Mage_MantleLiningR', { harden: false }));
  group.add(trim.buildMesh(materials.goldOld, side === 'L' ? 'Mage_MantleTrimL' : 'Mage_MantleTrimR', { harden: true }));
  group.add(clasp.buildMesh(materials.goldBright, side === 'L' ? 'Mage_MantleClaspL' : 'Mage_MantleClaspR', { harden: true }));
}

function buildMageBracer(group, materials, side) {
  const cloth = new GeoBuilder();
  const rings = [
    { z: -0.060, rx: 0.050, ry: 0.050 },
    { z: -0.010, rx: 0.054, ry: 0.054 },
    { z: 0.042, rx: 0.056, ry: 0.056 },
    { z: 0.074, rx: 0.061, ry: 0.060 },
    { z: 0.100, rx: 0.068, ry: 0.065 },
  ].map((ring) => ({
    center: new THREE.Vector3(0, 0, ring.z),
    points: makeRingZ({ ...ring, segments: 24, foldAmp: 0.004, foldFreq: 6 }),
  }));
  addHollowShell(cloth, rings, { thickness: 0.005, axis: 'z' });

  const lining = new GeoBuilder();
  addTubeBand(lining, rings[rings.length - 1].points, 0.016, 0.004, 1.02);

  const band = new GeoBuilder();
  const goldLower = makeRingZ({ z: 0.040, rx: 0.061, ry: 0.061, segments: 24 });
  const goldUpper = makeRingZ({ z: 0.052, rx: 0.060, ry: 0.060, segments: 24 });
  addHollowShell(band, [
    { center: new THREE.Vector3(0, 0, 0.040), points: goldLower },
    { center: new THREE.Vector3(0, 0, 0.052), points: goldUpper },
  ], { thickness: 0.004, axis: 'z' });

  group.add(cloth.buildMesh(materials.clothIndigo, side === 'L' ? 'Mage_BellCuffL' : 'Mage_BellCuffR', { harden: false }));
  group.add(lining.buildMesh(materials.linen, side === 'L' ? 'Mage_CuffLiningL' : 'Mage_CuffLiningR', { harden: true }));
  group.add(band.buildMesh(materials.goldOld, side === 'L' ? 'Mage_CuffBandL' : 'Mage_CuffBandR', { harden: true }));
}

function buildMageHips(group, materials) {
  const content = new THREE.Group();
  content.name = 'Mage_HipsBody';
  content.position.y = -BODY.hipsY;
  group.add(content);

  const sash = new GeoBuilder();
  const sashBottom = makeRingY({ y: 0.312, halfX: 0.163, frontZ: 0.127, backZ: 0.121, segments: 28 });
  const sashTop = makeRingY({ y: 0.352, halfX: 0.160, frontZ: 0.125, backZ: 0.119, segments: 28 });
  addHollowShell(sash, [
    { center: new THREE.Vector3(0, 0.312, 0), points: sashBottom },
    { center: new THREE.Vector3(0, 0.352, 0), points: sashTop },
  ], { thickness: 0.009, axis: 'y' });
  content.add(sash.buildMesh(materials.clothIndigoLight, 'Mage_Sash', { harden: false }));

  const cord = new GeoBuilder();
  const cordRing = makeRingY({ y: 0.334, halfX: 0.164, frontZ: 0.128, backZ: 0.122, segments: 28 });
  addRibbon(cord, cordRing.concat([cordRing[0]]), {
    width: 0.008,
    thickness: 0.003,
    normal: (point) => new THREE.Vector3(point.x, 0, point.z).normalize(),
  });
  content.add(cord.buildMesh(materials.goldOld, 'Mage_SashCord', { harden: true }));

  const tassel = new GeoBuilder();
  [-0.016, 0, 0.016].forEach((offset) => {
    addRibbon(tassel, [
      new THREE.Vector3(0.090 + offset, 0.330, 0.126),
      new THREE.Vector3(0.096 + offset * 1.2, 0.300, 0.132),
      new THREE.Vector3(0.088 + offset * 1.4, 0.272, 0.134),
    ], { width: 0.006, thickness: 0.003, normal: new THREE.Vector3(0.15, 0, 1) });
  });
  content.add(tassel.buildMesh(materials.goldOld, 'Mage_Tassel', { harden: true }));

  // Long robe skirt, above the knee so it never traps the legs.
  const skirt = new GeoBuilder();
  addHollowShell(skirt, [
    { y: 0.170, halfX: 0.198, frontZ: 0.150, backZ: 0.146 },
    { y: 0.240, halfX: 0.182, frontZ: 0.140, backZ: 0.136 },
    { y: 0.320, halfX: 0.162, frontZ: 0.126, backZ: 0.120 },
  ].map((station) => ({
    center: new THREE.Vector3(0, station.y, 0),
    points: makeRingY({ ...station, segments: 32, foldAmp: 0.006, foldFreq: 9 }),
  })), { thickness: 0.007, axis: 'y' });
  content.add(skirt.buildMesh(materials.clothIndigo, 'Mage_RobeSkirt', { harden: false }));

  const skirtHem = new GeoBuilder();
  const skirtRing = makeRingY({ y: 0.176, halfX: 0.200, frontZ: 0.152, backZ: 0.148, segments: 32 });
  addRibbon(skirtHem, skirtRing.concat([skirtRing[0]]), {
    width: 0.014,
    thickness: 0.004,
    normal: (point) => new THREE.Vector3(point.x, 0, point.z).normalize(),
  });
  content.add(skirtHem.buildMesh(materials.goldOld, 'Mage_SkirtHem', { harden: true }));
}

function buildMageCloakHalf(group, materials, side) {
  const builder = new GeoBuilder();
  const gold = new GeoBuilder();
  const cream = new GeoBuilder();
  const stitch = new GeoBuilder();

  const panel = addClothPanel(builder, {
    widthTop: 0.140,
    widthBottom: 0.170,
    height: 0.442,
    rows: 16,
    cols: 11,
    facing: -1,
    curve: 0.050,
    foldAmp: 0.009,
    foldFreq: 2,
    phase: side === 'L' ? 0.3 : 2.2,
    thickness: 0.007,
    sideCurve: 0.004,
  });

  const normal = new THREE.Vector3(0, 0, -1);
  const lift = (points, amount) => points.map((point) => point.clone().addScaledVector(normal, amount));
  const innerEdge = side === 'L' ? panel.leftEdge : panel.rightEdge;
  const outerEdge = side === 'L' ? panel.rightEdge : panel.leftEdge;

  addRibbon(cream, lift(innerEdge, 0.0022), { width: 0.016, thickness: 0.004, normal });
  addRibbon(cream, lift(panel.bottomRow, 0.0022), { width: 0.014, thickness: 0.004, normal });
  addRibbon(gold, lift(outerEdge, 0.002), { width: 0.010, thickness: 0.0035, normal });
  addRibbon(gold, lift(panel.topRow, 0.002), { width: 0.012, thickness: 0.0035, normal });
  const stitchEdge = side === 'L' ? panel.innerLeftEdge : panel.innerRightEdge;
  addStitchRun(stitch, lift(stitchEdge, 0.0028), { normal, spacing: 0.014, length: 0.008 });
  addStitchRun(stitch, lift(panel.innerBottomRow, 0.0028), { normal, spacing: 0.014, length: 0.008 });

  group.add(builder.buildMesh(materials.clothIndigo, side === 'L' ? 'Mage_CloakL' : 'Mage_CloakR', { harden: false }));
  group.add(cream.buildMesh(materials.linen, side === 'L' ? 'Mage_CloakLiningL' : 'Mage_CloakLiningR', { harden: true }));
  group.add(gold.buildMesh(materials.goldOld, side === 'L' ? 'Mage_CloakTrimL' : 'Mage_CloakTrimR', { harden: true }));
  group.add(stitch.buildMesh(materials.linen, side === 'L' ? 'Mage_CloakStitchL' : 'Mage_CloakStitchR', { harden: true }));
}

function buildMageCloakSide(group, materials, side) {
  const builder = new GeoBuilder();
  const trim = new GeoBuilder();
  const yaw = side === 'L' ? Math.PI * 0.5 : -Math.PI * 0.5;
  const panel = addClothPanel(builder, {
    widthTop: 0.108,
    widthBottom: 0.152,
    height: 0.310,
    rows: 12,
    cols: 9,
    facing: 1,
    curve: 0.020,
    foldAmp: 0.006,
    foldFreq: 2,
    phase: side === 'L' ? 1.1 : 2.6,
    thickness: 0.006,
    yaw,
  });

  const normal = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw));
  const lift = (points, amount) => points.map((point) => point.clone().addScaledVector(normal, amount));
  const frontEdge = side === 'L' ? panel.leftEdge : panel.rightEdge;
  const backEdge = side === 'L' ? panel.rightEdge : panel.leftEdge;

  addRibbon(trim, lift(panel.bottomRow, 0.002), { width: 0.012, thickness: 0.0035, normal });
  addRibbon(trim, lift(frontEdge, 0.0018), { width: 0.009, thickness: 0.003, normal });
  addRibbon(trim, lift(backEdge, 0.0018), { width: 0.014, thickness: 0.0035, normal });

  group.add(builder.buildMesh(materials.clothIndigo, side === 'L' ? 'Mage_SideCloakL' : 'Mage_SideCloakR', { harden: false }));
  group.add(trim.buildMesh(materials.linen, side === 'L' ? 'Mage_SideCloakLiningL' : 'Mage_SideCloakLiningR', { harden: true }));
}

function buildMageHood(group, materials) {
  // Geometry is authored around the nape in character space; the pivot sits on the Chest offset.
  const content = new THREE.Group();
  content.name = 'Mage_HoodBody';
  content.position.set(0, -0.608, 0.086);
  group.add(content);

  const outer = new GeoBuilder();
  addCowlShell(outer, [
    { y: 0.505, rx: 0.116, rz: 0.106, yDip: 0.018 },
    { y: 0.555, rx: 0.106, rz: 0.099, yDip: 0.010 },
    { y: 0.600, rx: 0.089, rz: 0.086 },
    { y: 0.616, rx: 0.080, rz: 0.079 },
  ], { segments: 20, thickness: 0.006, arcFrom: 1.75, arcTo: Math.PI * 2 - 1.75 });
  content.add(outer.buildMesh(materials.clothIndigo, 'Mage_HoodOuter', { harden: false }));

  const lining = new GeoBuilder();
  addCowlShell(lining, [
    { y: 0.507, rx: 0.109, rz: 0.099, yDip: 0.018 },
    { y: 0.556, rx: 0.099, rz: 0.092, yDip: 0.010 },
    { y: 0.599, rx: 0.083, rz: 0.080 },
    { y: 0.612, rx: 0.075, rz: 0.074 },
  ], { segments: 20, thickness: 0.003, arcFrom: 1.80, arcTo: Math.PI * 2 - 1.80 });
  content.add(lining.buildMesh(materials.linen, 'Mage_HoodLining', { harden: false }));

  const trim = new GeoBuilder();
  const topEdge = [];
  for (let i = 0; i <= 20; i += 1) {
    const angle = 1.75 + (Math.PI * 2 - 3.5) * (i / 20);
    topEdge.push(new THREE.Vector3(Math.sin(angle) * 0.081, 0.617, Math.cos(angle) * 0.080));
  }
  addRibbon(trim, topEdge, {
    width: 0.009,
    thickness: 0.003,
    normal: (point) => new THREE.Vector3(Math.sin(Math.atan2(point.x, point.z)), 0, Math.cos(Math.atan2(point.x, point.z))),
  });
  content.add(trim.buildMesh(materials.goldOld, 'Mage_HoodTrim', { harden: true }));
}

// ---------------------------------------------------------------------------
// Part pivots
// ---------------------------------------------------------------------------
function makePart(set, name, position) {
  const group = new THREE.Group();
  group.name = name;
  group.position.copy(position);
  set.add(group);
  return group;
}

function armQuaternion(side) {
  const shoulder = new THREE.Vector3(BODY.shoulderX, BODY.shoulderY, 0.004);
  const elbow = new THREE.Vector3(BODY.elbow[0], BODY.elbow[1], BODY.elbow[2]);
  if (side === 'R') {
    shoulder.x *= -1;
    elbow.x *= -1;
  }
  const zAxis = elbow.clone().sub(shoulder).normalize();
  const outward = side === 'L'
    ? new THREE.Vector3().crossVectors(FORWARD, zAxis)
    : new THREE.Vector3().crossVectors(zAxis, FORWARD);
  outward.normalize();
  const yAxis = outward.clone().sub(zAxis.clone().multiplyScalar(outward.dot(zAxis))).normalize();
  const xAxis = new THREE.Vector3().crossVectors(yAxis, zAxis).normalize();
  const basis = new THREE.Matrix4().makeBasis(xAxis, yAxis, zAxis);
  return new THREE.Quaternion().setFromRotationMatrix(basis);
}

function forearmQuaternion(side) {
  const elbow = new THREE.Vector3(BODY.elbow[0], BODY.elbow[1], BODY.elbow[2]);
  const wrist = new THREE.Vector3(BODY.wrist[0], BODY.wrist[1], BODY.wrist[2]);
  if (side === 'R') {
    elbow.x *= -1;
    wrist.x *= -1;
  }
  const zAxis = wrist.clone().sub(elbow).normalize();
  const outward = side === 'L'
    ? new THREE.Vector3().crossVectors(FORWARD, zAxis)
    : new THREE.Vector3().crossVectors(zAxis, FORWARD);
  outward.normalize();
  const yAxis = outward.clone().sub(zAxis.clone().multiplyScalar(outward.dot(zAxis))).normalize();
  const xAxis = new THREE.Vector3().crossVectors(yAxis, zAxis).normalize();
  const basis = new THREE.Matrix4().makeBasis(xAxis, yAxis, zAxis);
  return new THREE.Quaternion().setFromRotationMatrix(basis);
}

function upperArmMidpoint(side) {
  const shoulder = new THREE.Vector3(BODY.shoulderX, BODY.shoulderY, 0.004);
  const elbow = new THREE.Vector3(BODY.elbow[0], BODY.elbow[1], BODY.elbow[2]);
  if (side === 'R') {
    shoulder.x *= -1;
    elbow.x *= -1;
  }
  return shoulder.lerp(elbow, 0.36);
}

function forearmMidpoint(side) {
  const elbow = new THREE.Vector3(BODY.elbow[0], BODY.elbow[1], BODY.elbow[2]);
  const wrist = new THREE.Vector3(BODY.wrist[0], BODY.wrist[1], BODY.wrist[2]);
  if (side === 'R') {
    elbow.x *= -1;
    wrist.x *= -1;
  }
  return elbow.lerp(wrist, 0.5);
}

const SET_OFFSETS = { warrior: -0.95, archer: 0, mage: 0.95 };

function buildWarriorSet(materials) {
  const set = new THREE.Group();
  set.name = 'WarriorSet';
  set.position.set(SET_OFFSETS.warrior, 0, 0);

  const chest = makePart(set, 'Chest', new THREE.Vector3(0, BODY.chestY, 0));
  buildWarriorChest(chest, materials);

  const hips = makePart(set, 'Hips', new THREE.Vector3(0, BODY.hipsY, 0));
  buildWarriorHips(hips, materials);

  ['L', 'R'].forEach((side) => {
    const sign = side === 'L' ? 1 : -1;
    const shoulder = makePart(set, `Shoulder${side}`, new THREE.Vector3(sign * BODY.shoulderX, BODY.shoulderY, 0.004));
    shoulder.quaternion.copy(armQuaternion(side));
    buildWarriorPauldron(shoulder, materials, side);

    const bracer = makePart(set, `Bracer${side}`, forearmMidpoint(side));
    bracer.quaternion.copy(forearmQuaternion(side));
    buildWarriorBracer(bracer, materials, side);
  });

  const tabardFront = makePart(set, 'TabardFront', new THREE.Vector3(0, 0.334, 0.133));
  buildWarriorTabard(tabardFront, materials, 1);

  const tabardBack = makePart(set, 'TabardBack', new THREE.Vector3(0, 0.334, -0.142));
  buildWarriorTabard(tabardBack, materials, -1);

  return set;
}


function buildArcherSet(materials) {
  const set = new THREE.Group();
  set.name = 'ArcherSet';
  set.position.set(SET_OFFSETS.archer, 0, 0);

  const chest = makePart(set, 'Chest', new THREE.Vector3(0, BODY.chestY, 0));
  buildArcherChest(chest, materials);

  const hips = makePart(set, 'Hips', new THREE.Vector3(0, BODY.hipsY, 0));
  buildArcherHips(hips, materials);

  ['L', 'R'].forEach((side) => {
    const sign = side === 'L' ? 1 : -1;
    const shoulder = makePart(set, `Shoulder${side}`, new THREE.Vector3(sign * BODY.shoulderX, BODY.shoulderY, 0.004));
    shoulder.quaternion.copy(armQuaternion(side));
    buildArcherShoulder(shoulder, materials, side);

    const sleeve = makePart(set, `Sleeve${side}`, upperArmMidpoint(side));
    sleeve.quaternion.copy(armQuaternion(side));
    buildArcherSleeve(sleeve, materials, side);

    const bracer = makePart(set, `Bracer${side}`, forearmMidpoint(side));
    bracer.quaternion.copy(forearmQuaternion(side));
    buildArcherBracer(bracer, materials, side);
  });

  const hemFrontL = makePart(set, 'HemFrontL', new THREE.Vector3(0.058, 0.300, 0.128));
  buildArcherHem(hemFrontL, materials, {
    facing: 1, widthTop: 0.100, widthBottom: 0.120, height: 0.116,
    hemSlant: 0.012, phase: 0.3, name: 'Archer_HemFrontL', innerSide: 'left',
  });
  const hemFrontR = makePart(set, 'HemFrontR', new THREE.Vector3(-0.058, 0.300, 0.128));
  buildArcherHem(hemFrontR, materials, {
    facing: 1, widthTop: 0.100, widthBottom: 0.120, height: 0.116,
    hemSlant: -0.012, phase: 2.1, name: 'Archer_HemFrontR', innerSide: 'right',
  });
  const hemBackL = makePart(set, 'HemBackL', new THREE.Vector3(0.058, 0.300, -0.138));
  buildArcherHem(hemBackL, materials, {
    facing: -1, widthTop: 0.106, widthBottom: 0.132, height: 0.178,
    hemSlant: 0.045, phase: 0.9, name: 'Archer_HemBackL', innerSide: 'left',
  });
  const hemBackR = makePart(set, 'HemBackR', new THREE.Vector3(-0.058, 0.300, -0.138));
  buildArcherHem(hemBackR, materials, {
    facing: -1, widthTop: 0.106, widthBottom: 0.132, height: 0.178,
    hemSlant: -0.045, phase: 2.8, name: 'Archer_HemBackR', innerSide: 'right',
  });

  return set;
}

function buildMageSet(materials) {
  const set = new THREE.Group();
  set.name = 'MageSet';
  set.position.set(SET_OFFSETS.mage, 0, 0);

  const chest = makePart(set, 'Chest', new THREE.Vector3(0, BODY.chestY, 0));
  buildMageChest(chest, materials);

  const hips = makePart(set, 'Hips', new THREE.Vector3(0, BODY.hipsY, 0));
  buildMageHips(hips, materials);

  ['L', 'R'].forEach((side) => {
    const sign = side === 'L' ? 1 : -1;
    const shoulder = makePart(set, `Shoulder${side}`, new THREE.Vector3(sign * BODY.shoulderX, BODY.shoulderY, 0.004));
    shoulder.quaternion.copy(armQuaternion(side));
    buildMageShoulder(shoulder, materials, side);

    const bracer = makePart(set, `Bracer${side}`, forearmMidpoint(side));
    bracer.quaternion.copy(forearmQuaternion(side));
    buildMageBracer(bracer, materials, side);
  });

  const cloakL = makePart(set, 'CloakBackL', new THREE.Vector3(0.095, 0.546, -0.132));
  buildMageCloakHalf(cloakL, materials, 'L');
  const cloakR = makePart(set, 'CloakBackR', new THREE.Vector3(-0.095, 0.546, -0.132));
  buildMageCloakHalf(cloakR, materials, 'R');

  const sideL = makePart(set, 'CloakSideL', new THREE.Vector3(0.166, 0.500, -0.012));
  buildMageCloakSide(sideL, materials, 'L');
  const sideR = makePart(set, 'CloakSideR', new THREE.Vector3(-0.166, 0.500, -0.012));
  buildMageCloakSide(sideR, materials, 'R');

  const hood = makePart(set, 'HoodBack', new THREE.Vector3(0, 0.608, -0.086));
  buildMageHood(hood, materials);

  return set;
}

// ---------------------------------------------------------------------------
// Hosted factory
// ---------------------------------------------------------------------------
module.exports = function previewModule(moduleRoot, runtime) {
  const { helpers, logger } = runtime;
  helpers.clearGroup(moduleRoot);
  const materials = createMaterials();

  const root = new THREE.Group();
  root.name = 'ClasswearRoot';
  root.userData.assetBrief = ASSET_BRIEF;
  moduleRoot.add(root);

  const sourceSets = new THREE.Group();
  sourceSets.name = 'SourceSets';
  root.add(sourceSets);

  sourceSets.add(buildWarriorSet(materials));
  sourceSets.add(buildArcherSet(materials));
  sourceSets.add(buildMageSet(materials));

  root.traverse((object) => {
    if (!object.isMesh) return;
    object.castShadow = true;
    object.receiveShadow = true;
  });

  logger.info('Classwear outfits built');
};
