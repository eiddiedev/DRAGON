const THREE = require('three');

// 黑色西方龙坐骑：直立蹲坐、长颈、四足、巨翼与长尾刃尖。
const ASSET_BRIEF = {
  identity: {
    objectClass: 'western-dragon-mount',
    confidence: 0.94,
    assumptions: [
      'Single reference view; far-side wing, far-side legs and back surface are mirrored.',
      'A low-profile black riding pad is added because the module is rideable.',
    ],
  },
  orientation: { up: '+Y', front: '+Z' },
  silhouette: {
    primaryMasses: ['TorsoLoft', 'NeckLoft', 'WingLeftRoot', 'WingRightRoot', 'TailLoft'],
    proportions: 'Upright sitting quadruped, deep chest, narrow waist, long S-curved neck, huge swept-back bat wings, long rising tail with blade tip.',
    identityCues: ['Long narrow skull', 'Swept-back horns', 'Amber slit eyes', 'Dark segmented belly scutes', 'Scalloped bat-wing membranes', 'Blade cluster tail tip'],
  },
  parts: [
    { id: 'TorsoLoft', level: 'macro', role: 'continuous torso from hips to neck base', parent: 'VisualRoot', topologyClass: 'continuous-sculpt', geometryStrategy: '16-station oval loft with narrow waist', materialRole: 'hide', moving: false },
    { id: 'NeckLoft', level: 'macro', role: 'long S-curved neck', parent: 'VisualRoot', topologyClass: 'continuous-sculpt', geometryStrategy: '7-station oval loft', materialRole: 'hide', moving: true, pivotStrategy: 'root pivot at chest' },
    { id: 'HeadRoot', level: 'macro', role: 'narrow skull, snout, horns and eyes', parent: 'NeckRoot', topologyClass: 'continuous-sculpt', geometryStrategy: 'tapered skull loft, jaw loft and curved horn lofts', materialRole: 'hide', moving: true },
    { id: 'WingLeftRoot', level: 'macro', role: 'left bat wing', parent: 'VisualRoot', topologyClass: 'conforming-shell', geometryStrategy: 'thick curved membrane with four finger bones', materialRole: 'membrane', moving: true, pivotStrategy: 'hinge pivot at shoulder' },
    { id: 'WingRightRoot', level: 'macro', role: 'right bat wing', parent: 'VisualRoot', topologyClass: 'conforming-shell', geometryStrategy: 'mirrored thick curved membrane with four finger bones', materialRole: 'membrane', moving: true, pivotStrategy: 'hinge pivot at shoulder' },
    { id: 'TailLoft', level: 'macro', role: 'long rising tail with blade tip', parent: 'VisualRoot', topologyClass: 'continuous-sculpt', geometryStrategy: '9-station tapered loft with J-curve', materialRole: 'hide', moving: true, pivotStrategy: 'root pivot at hips' },
    { id: 'LegFL', level: 'macro', role: 'front left leg', parent: 'VisualRoot', topologyClass: 'assembled-solid', geometryStrategy: 'tapered limb lofts with joint masses and clawed foot', materialRole: 'hide', moving: false },
    { id: 'LegFR', level: 'macro', role: 'front right leg', parent: 'VisualRoot', topologyClass: 'assembled-solid', geometryStrategy: 'tapered limb lofts with joint masses and clawed foot', materialRole: 'hide', moving: false },
    { id: 'LegBL', level: 'macro', role: 'hind left leg', parent: 'VisualRoot', topologyClass: 'assembled-solid', geometryStrategy: 'heavy folded thigh and thin shin with clawed foot', materialRole: 'hide', moving: false },
    { id: 'LegBR', level: 'macro', role: 'hind right leg', parent: 'VisualRoot', topologyClass: 'assembled-solid', geometryStrategy: 'heavy folded thigh and thin shin with clawed foot', materialRole: 'hide', moving: false },
    { id: 'Saddle', level: 'meso', role: 'low-profile riding pad and seat anchor', parent: 'VisualRoot', topologyClass: 'assembled-solid', geometryStrategy: 'baked-scale leather pad with cantle', materialRole: 'saddleLeather', moving: false },
  ],
  details: [
    { id: 'BellyScutes', region: 'throat, chest and belly front', kind: 'ridge', affects: 'geometry', mapsTo: 'BellyScutes', implementation: 'embedded curved scute bands', scale: '0.2-0.34 m wide', confidence: 0.9 },
    { id: 'DorsalSpikes', region: 'neck and spine ridge', kind: 'ridge', affects: 'geometry', mapsTo: 'DorsalSpikes', implementation: 'tapered bone cones', scale: '0.12-0.26 m', confidence: 0.8 },
    { id: 'AmberEyes', region: 'head', kind: 'emissive', affects: 'material', mapsTo: 'Head_Eye', implementation: 'amber emissive sphere with dark slit', scale: '0.06 m', confidence: 0.95 },
    { id: 'Horns', region: 'skull', kind: 'silhouette-break', affects: 'geometry', mapsTo: 'Head_Horn', implementation: 'curved tapered lofts', scale: '0.45-0.65 m', confidence: 0.9 },
    { id: 'TailBlade', region: 'tail tip', kind: 'silhouette-break', affects: 'geometry', mapsTo: 'TailBlade', implementation: 'dark bone blades around a dark red fin', scale: '0.55-0.8 m', confidence: 0.85 },
  ],
  materialRoles: {
    hide: { baseColor: 0x202227, roughness: 0.58, metalness: 0.04 },
    hideDark: { baseColor: 0x141519, roughness: 0.7, metalness: 0.02 },
    hideMid: { baseColor: 0x2b2e34, roughness: 0.62, metalness: 0.03 },
    bellyPlate: { baseColor: 0x2e3239, roughness: 0.6, metalness: 0.03 },
    membrane: { baseColor: 0x2a2b33, roughness: 0.84, metalness: 0.0 },
    bone: { baseColor: 0x3b3a36, roughness: 0.5, metalness: 0.05 },
    wingBone: { baseColor: 0x4d4942, roughness: 0.48, metalness: 0.06 },
    claw: { baseColor: 0x5f5c54, roughness: 0.36, metalness: 0.1 },
    eye: { baseColor: 0xd6a02c, roughness: 0.24, metalness: 0.0 },
    pupil: { baseColor: 0x08080a, roughness: 0.4, metalness: 0.0 },
    saddleLeather: { baseColor: 0x211813, roughness: 0.82, metalness: 0.02 },
    saddleMetal: { baseColor: 0x7c6438, roughness: 0.36, metalness: 0.78 },
    bladeRed: { baseColor: 0x22070a, roughness: 0.6, metalness: 0.04 },
  },
  readiness: {
    pivots: ['WingLeftRoot', 'WingRightRoot', 'TailRoot', 'NeckRoot'],
    sockets: ['Saddle/SeatAnchor'],
    anchors: ['Saddle/SeatAnchor'],
    colliderIntent: [{ partId: 'TorsoLoft', type: 'convex', size: [1.3, 4.3, 7.2] }],
  },
};

function makeMaterials() {
  const materials = {};
  Object.entries(ASSET_BRIEF.materialRoles).forEach(([id, role]) => {
    const material = new THREE.MeshStandardMaterial({
      color: role.baseColor,
      roughness: role.roughness,
      metalness: role.metalness,
      side: THREE.FrontSide,
    });
    material.name = id;
    materials[id] = material;
  });
  materials.eye.emissive = new THREE.Color(0x8a5a08);
  materials.eye.emissiveIntensity = 0.9;
  materials.bladeRed.emissive = new THREE.Color(0x250607);
  materials.bladeRed.emissiveIntensity = 0.35;
  return materials;
}

function makeGroup(parent, name, position, rotation) {
  const group = new THREE.Group();
  group.name = name;
  if (position) group.position.set(position[0], position[1], position[2]);
  if (rotation) group.rotation.set(rotation[0], rotation[1], rotation[2]);
  parent.add(group);
  return group;
}

function addMesh(parent, name, geometry, material) {
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = name;
  parent.add(mesh);
  return mesh;
}

function addEllipsoid(parent, name, material, position, scale, segments, rings) {
  const geometry = new THREE.SphereGeometry(1, segments || 20, rings || 14);
  const mesh = addMesh(parent, name, geometry, material);
  mesh.position.set(position[0], position[1], position[2]);
  mesh.scale.set(scale[0], scale[1], scale[2]);
  return mesh;
}

const UP_AXIS = new THREE.Vector3(0, 1, 0);
const FORWARD_AXIS = new THREE.Vector3(0, 0, 1);

function addSegment(parent, name, material, start, end, radiusStart, radiusEnd, radialSegments) {
  const direction = new THREE.Vector3().subVectors(end, start);
  const length = direction.length();
  if (!isFinite(length) || length <= 0) return null;
  const geometry = new THREE.CylinderGeometry(
    Math.max(radiusEnd, 0.001),
    Math.max(radiusStart, 0.001),
    length,
    radialSegments || 10,
    1,
    false,
  );
  const mesh = addMesh(parent, name, geometry, material);
  mesh.position.copy(start).add(end).multiplyScalar(0.5);
  mesh.quaternion.setFromUnitVectors(UP_AXIS, direction.clone().normalize());
  return mesh;
}

function addCone(parent, name, material, start, end, radius, radialSegments) {
  return addSegment(parent, name, material, start, end, radius, 0.003, radialSegments || 8);
}

function addLoft(parent, name, material, sections, radialSegments, capStart, capEnd) {
  const count = sections.length;
  const radial = radialSegments || 14;
  const positions = [];
  const indices = [];
  const points = sections.map((s) => new THREE.Vector3(s.p[0], s.p[1], s.p[2]));

  for (let i = 0; i < count; i += 1) {
    const before = points[Math.max(0, i - 1)];
    const after = points[Math.min(count - 1, i + 1)];
    const tangent = new THREE.Vector3().subVectors(after, before);
    if (tangent.lengthSq() < 1e-8) tangent.set(0, 1, 0);
    tangent.normalize();

    const reference = Math.abs(tangent.dot(UP_AXIS)) > 0.92 ? FORWARD_AXIS : UP_AXIS;
    let right = new THREE.Vector3().crossVectors(reference, tangent);
    if (right.lengthSq() < 1e-6) right.set(1, 0, 0);
    right.normalize();
    const up = new THREE.Vector3().crossVectors(tangent, right).normalize();

    const rx = Math.max(sections[i].rx, 0.001);
    const ry = Math.max(sections[i].ry, 0.001);
    for (let j = 0; j < radial; j += 1) {
      const angle = (j / radial) * Math.PI * 2;
      const offset = new THREE.Vector3()
        .addScaledVector(right, Math.cos(angle) * rx)
        .addScaledVector(up, Math.sin(angle) * ry);
      positions.push(points[i].x + offset.x, points[i].y + offset.y, points[i].z + offset.z);
    }
  }

  for (let i = 0; i < count - 1; i += 1) {
    for (let j = 0; j < radial; j += 1) {
      const next = (j + 1) % radial;
      const a = i * radial + j;
      const b = i * radial + next;
      const c = (i + 1) * radial + j;
      const d = (i + 1) * radial + next;
      indices.push(a, b, c);
      indices.push(b, d, c);
    }
  }

  if (capStart !== false) {
    const centerIndex = positions.length / 3;
    positions.push(points[0].x, points[0].y, points[0].z);
    for (let j = 0; j < radial; j += 1) {
      const next = (j + 1) % radial;
      indices.push(centerIndex, next, j);
    }
  }
  if (capEnd !== false) {
    const centerIndex = positions.length / 3;
    positions.push(points[count - 1].x, points[count - 1].y, points[count - 1].z);
    const base = (count - 1) * radial;
    for (let j = 0; j < radial; j += 1) {
      const next = (j + 1) % radial;
      indices.push(centerIndex, base + j, base + next);
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return addMesh(parent, name, geometry, material);
}

function samplePolyline(points, t) {
  const lengths = [];
  let total = 0;
  for (let i = 0; i < points.length - 1; i += 1) {
    const length = points[i].distanceTo(points[i + 1]);
    lengths.push(length);
    total += length;
  }
  let distance = Math.max(0, Math.min(1, t)) * total;
  for (let i = 0; i < lengths.length; i += 1) {
    if (distance <= lengths[i] || i === lengths.length - 1) {
      const local = lengths[i] > 1e-6 ? distance / lengths[i] : 0;
      return points[i].clone().lerp(points[i + 1], Math.min(1, local));
    }
    distance -= lengths[i];
  }
  return points[points.length - 1].clone();
}

function addWingSurface(parent, name, material, leading, trailing, thickness, spans, chords) {
  const front = [];
  const back = [];
  for (let i = 0; i <= spans; i += 1) {
    const t = i / spans;
    const leadingPoint = samplePolyline(leading, t);
    const trailingPoint = samplePolyline(trailing, t);
    for (let j = 0; j <= chords; j += 1) {
      const s = j / chords;
      const point = leadingPoint.clone().lerp(trailingPoint, s);
      // 后掠翼膜向后方鼓起，并在下垂方向轻微下坠。
      point.z -= 0.18 * Math.sin(Math.PI * s) * (0.35 + 0.65 * Math.sin(Math.PI * t));
      point.y -= 0.035 * Math.sin(Math.PI * s) * Math.sin(Math.PI * t);
      front.push(point.clone().setZ(point.z + thickness * 0.5));
      back.push(point.clone().setZ(point.z - thickness * 0.5));
    }
  }

  const stride = chords + 1;
  const indices = [];
  for (let i = 0; i < spans; i += 1) {
    for (let j = 0; j < chords; j += 1) {
      const a = i * stride + j;
      const b = (i + 1) * stride + j;
      const c = (i + 1) * stride + (j + 1);
      const d = i * stride + (j + 1);
      indices.push(a, d, b);
      indices.push(b, d, c);
    }
  }
  const count = front.length;
  for (let i = 0; i < spans; i += 1) {
    for (let j = 0; j < chords; j += 1) {
      const a = i * stride + j;
      const b = (i + 1) * stride + j;
      const c = (i + 1) * stride + (j + 1);
      const d = i * stride + (j + 1);
      indices.push(count + a, count + b, count + d);
      indices.push(count + b, count + c, count + d);
    }
  }

  const positions = [];
  front.forEach((p) => positions.push(p.x, p.y, p.z));
  back.forEach((p) => positions.push(p.x, p.y, p.z));

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return addMesh(parent, name, geometry, material);
}

function buildTorso(parent, materials) {
  const sections = [
    { p: [0, 1.16, -1.18], rx: 0.38, ry: 0.42 },
    { p: [0, 1.28, -0.90], rx: 0.50, ry: 0.56 },
    { p: [0, 1.40, -0.55], rx: 0.54, ry: 0.62 },
    { p: [0, 1.50, -0.20], rx: 0.45, ry: 0.58 },
    { p: [0, 1.60, 0.15], rx: 0.43, ry: 0.56 },
    { p: [0, 1.72, 0.45], rx: 0.51, ry: 0.62 },
    { p: [0, 1.83, 0.72], rx: 0.58, ry: 0.62 },
    { p: [0, 1.91, 0.92], rx: 0.48, ry: 0.54 },
    { p: [0, 1.98, 1.06], rx: 0.37, ry: 0.42 },
  ];
  addLoft(parent, 'TorsoLoft', materials.hide, sections, 18, true, true);
  addEllipsoid(parent, 'Torso_ShoulderMassL', materials.hide, [0.45, 1.82, 0.50], [0.24, 0.27, 0.31], 20, 14);
  addEllipsoid(parent, 'Torso_ShoulderMassR', materials.hide, [-0.45, 1.82, 0.50], [0.24, 0.27, 0.31], 20, 14);
  addEllipsoid(parent, 'Torso_HipMassL', materials.hide, [0.45, 1.30, -0.88], [0.28, 0.32, 0.34], 20, 14);
  addEllipsoid(parent, 'Torso_HipMassR', materials.hide, [-0.45, 1.30, -0.88], [0.28, 0.32, 0.34], 20, 14);
}

function buildBellyScutes(parent, materials) {
  const group = makeGroup(parent, 'BellyScutes');
  const scutes = [
    [0, 2.05, 1.00, 0.23, 0.035, 0.085],
    [0, 1.90, 1.07, 0.27, 0.04, 0.09],
    [0, 1.75, 1.10, 0.30, 0.04, 0.09],
    [0, 1.58, 1.09, 0.30, 0.04, 0.09],
    [0, 1.41, 1.04, 0.28, 0.04, 0.09],
    [0, 1.24, 0.96, 0.25, 0.035, 0.085],
    [0, 1.08, 0.85, 0.21, 0.032, 0.075],
    [0, 0.94, 0.72, 0.17, 0.03, 0.065],
  ];
  scutes.forEach((scute, index) => {
    addEllipsoid(group, `BellyScutes_${index + 1}`, materials.bellyPlate,
      [scute[0], scute[1], scute[2]], [scute[3], scute[4], scute[5]], 18, 10);
  });
  return group;
}

function buildDorsalSpikes(parent, materials) {
  const group = makeGroup(parent, 'DorsalSpikes');
  const spikes = [
    [0, 2.32, 0.78, 0.20],
    [0, 2.40, 0.55, 0.22],
    [0, 2.42, 0.31, 0.22],
    [0, 2.36, 0.07, 0.21],
    [0, 2.20, -0.20, 0.18],
    [0, 2.00, -0.50, 0.16],
    [0, 1.78, -0.85, 0.14],
    [0, 1.52, -1.10, 0.12],
  ];
  spikes.forEach((spike, index) => {
    addCone(group, `DorsalSpikes_${index + 1}`, materials.bone,
      new THREE.Vector3(spike[0], spike[1], spike[2]),
      new THREE.Vector3(spike[0], spike[1] + spike[3], spike[2] - spike[3] * 0.9),
      0.052, 8);
  });
  return group;
}

function buildNeck(parent, materials) {
  const neckRoot = makeGroup(parent, 'NeckRoot', [0, 1.96, 0.92]);
  const sections = [
    { p: [0, 0.00, 0.00], rx: 0.33, ry: 0.35 },
    { p: [0, 0.22, 0.14], rx: 0.29, ry: 0.31 },
    { p: [0, 0.44, 0.25], rx: 0.26, ry: 0.27 },
    { p: [0, 0.66, 0.32], rx: 0.23, ry: 0.24 },
    { p: [0, 0.88, 0.34], rx: 0.205, ry: 0.215 },
    { p: [0, 1.08, 0.30], rx: 0.19, ry: 0.20 },
    { p: [0, 1.26, 0.22], rx: 0.185, ry: 0.195 },
  ];
  addLoft(neckRoot, 'NeckLoft', materials.hide, sections, 16, true, true);

  // 颈背棘刺
  const spikePositions = [
    [0, 0.20, -0.26, 0.13],
    [0, 0.44, -0.19, 0.14],
    [0, 0.68, -0.13, 0.14],
    [0, 0.90, -0.09, 0.12],
    [0, 1.08, -0.07, 0.11],
    [0, 1.22, -0.06, 0.09],
  ];
  spikePositions.forEach((spike, index) => {
    addCone(neckRoot, `NeckSpike_${index + 1}`, materials.bone,
      new THREE.Vector3(spike[0], spike[1], spike[2]),
      new THREE.Vector3(spike[0], spike[1] + spike[3], spike[2] - spike[3] * 0.8),
      0.045, 8);
  });

  // 喉部甲片
  const throat = [
    [0, 0.16, 0.30, 0.20, 0.075],
    [0, 0.40, 0.36, 0.18, 0.07],
    [0, 0.64, 0.38, 0.165, 0.06],
    [0, 0.88, 0.36, 0.15, 0.055],
    [0, 1.08, 0.32, 0.14, 0.05],
  ];
  throat.forEach((plate, index) => {
    addEllipsoid(neckRoot, `NeckThroatPlate_${index + 1}`, materials.bellyPlate,
      [plate[0], plate[1], plate[2]], [plate[3], 0.045, plate[4]], 16, 10);
  });

  const headRoot = makeGroup(neckRoot, 'HeadRoot', [0, 1.22, 0.26], [0.10, 0, 0]);
  buildHead(headRoot, materials);
  return neckRoot;
}

function buildHead(parent, materials) {
  const group = makeGroup(parent, 'HeadDisplay');
  const skull = [
    { p: [0, 0.04, -0.22], rx: 0.17, ry: 0.19 },
    { p: [0, 0.07, -0.02], rx: 0.23, ry: 0.23 },
    { p: [0, 0.05, 0.20], rx: 0.21, ry: 0.20 },
    { p: [0, 0.02, 0.42], rx: 0.16, ry: 0.15 },
    { p: [0, -0.01, 0.64], rx: 0.115, ry: 0.105 },
    { p: [0, -0.03, 0.84], rx: 0.075, ry: 0.07 },
    { p: [0, -0.04, 0.96], rx: 0.045, ry: 0.04 },
  ];
  addLoft(group, 'Head_Skull', materials.hide, skull, 16, true, true);

  // 鼻梁与鼻角
  addEllipsoid(group, 'Head_NoseBridge', materials.hideDark, [0, 0.115, 0.40], [0.085, 0.045, 0.28], 16, 10);
  addCone(group, 'Head_NoseHorn', materials.bone,
    new THREE.Vector3(0, 0.145, 0.50),
    new THREE.Vector3(0, 0.20, 0.72), 0.045, 8);

  const jaw = [
    { p: [0, -0.10, 0.08], rx: 0.14, ry: 0.055 },
    { p: [0, -0.11, 0.40], rx: 0.12, ry: 0.05 },
    { p: [0, -0.11, 0.70], rx: 0.075, ry: 0.035 },
    { p: [0, -0.10, 0.92], rx: 0.045, ry: 0.022 },
  ];
  addLoft(group, 'Head_LowerJaw', materials.hideDark, jaw, 12, true, true);

  // 眉骨与眼
  addEllipsoid(group, 'Head_BrowL', materials.hideDark, [0.155, 0.205, 0.18], [0.105, 0.045, 0.15], 16, 10);
  addEllipsoid(group, 'Head_BrowR', materials.hideDark, [-0.155, 0.205, 0.18], [0.105, 0.045, 0.15], 16, 10);
  addEllipsoid(group, 'Head_EyeL', materials.eye, [0.176, 0.135, 0.235], [0.036, 0.034, 0.038], 16, 12);
  addEllipsoid(group, 'Head_EyeR', materials.eye, [-0.176, 0.135, 0.235], [0.036, 0.034, 0.038], 16, 12);
  addEllipsoid(group, 'Head_PupilL', materials.pupil, [0.198, 0.138, 0.258], [0.008, 0.024, 0.014], 10, 8);
  addEllipsoid(group, 'Head_PupilR', materials.pupil, [-0.198, 0.138, 0.258], [0.008, 0.024, 0.014], 10, 8);

  // 后掠角
  const hornSections = (side, baseX, baseY, baseZ, midX, midY, midZ, endX, endY, endZ, r0) => [
    { p: [baseX * side, baseY, baseZ], rx: r0, ry: r0 },
    { p: [midX * side, midY, midZ], rx: r0 * 0.55, ry: r0 * 0.55 },
    { p: [endX * side, endY, endZ], rx: 0.006, ry: 0.006 },
  ];
  addLoft(group, 'Head_HornL', materials.bone,
    hornSections(1, 0.13, 0.22, -0.06, 0.24, 0.34, -0.30, 0.35, 0.43, -0.58, 0.082), 8, true, true);
  addLoft(group, 'Head_HornR', materials.bone,
    hornSections(-1, 0.13, 0.22, -0.06, 0.24, 0.34, -0.30, 0.35, 0.43, -0.58, 0.082), 8, true, true);
  addLoft(group, 'Head_HornL2', materials.bone,
    hornSections(1, 0.18, 0.06, 0.00, 0.30, 0.12, -0.23, 0.38, 0.16, -0.44, 0.052), 8, true, true);
  addLoft(group, 'Head_HornR2', materials.bone,
    hornSections(-1, 0.18, 0.06, 0.00, 0.30, 0.12, -0.23, 0.38, 0.16, -0.44, 0.052), 8, true, true);

  // 头两侧的小棘
  const crown = [
    [0.12, 0.17, -0.14, 0.13],
    [-0.12, 0.17, -0.14, 0.13],
  ];
  crown.forEach((spike, index) => {
    addCone(group, `Head_CrownSpike${index + 1}`, materials.bone,
      new THREE.Vector3(spike[0], spike[1], spike[2]),
      new THREE.Vector3(spike[0] * 1.7, spike[1] + spike[3] * 0.6, spike[2] - spike[3] * 1.8),
      0.03, 6);
  });

  // 面颊棘刺
  const cheek = [
    [0.21, 0.02, 0.08, 0.35, -0.04, -0.18],
    [0.23, -0.02, 0.20, 0.37, -0.08, -0.04],
    [0.20, -0.05, 0.32, 0.31, -0.10, 0.10],
  ];
  cheek.forEach((spike, index) => {
    addCone(group, `Head_CheekSpike${index + 1}`, materials.bone,
      new THREE.Vector3(spike[0], spike[1], spike[2]),
      new THREE.Vector3(spike[3], spike[4], spike[5]), 0.032, 8);
    addCone(group, `Head_CheekSpikeMirror${index + 1}`, materials.bone,
      new THREE.Vector3(-spike[0], spike[1], spike[2]),
      new THREE.Vector3(-spike[3], spike[4], spike[5]), 0.032, 8);
  });

  // 上颌獠牙
  const teeth = [
    [0.055, -0.05, 0.88], [-0.055, -0.05, 0.88],
    [0.07, -0.055, 0.74], [-0.07, -0.055, 0.74],
    [0.085, -0.06, 0.58], [-0.085, -0.06, 0.58],
    [0.10, -0.065, 0.42], [-0.10, -0.065, 0.42],
  ];
  teeth.forEach((tooth, index) => {
    addCone(group, `Head_Tooth${index + 1}`, materials.claw,
      new THREE.Vector3(tooth[0], tooth[1], tooth[2]),
      new THREE.Vector3(tooth[0], tooth[1] - 0.075, tooth[2] + 0.01), 0.015, 6);
  });
  return group;
}

function buildWing(parent, materials, side) {
  const suffix = side > 0 ? 'Left' : 'Right';
  const root = makeGroup(parent, `Wing${suffix}Root`, [0.58 * side, 1.98, 0.34]);
  // 翼面整体后掠，避免从侧面看只剩一条薄片；扇动仍由外层 WingRoot 绕 Z 驱动。
  const sweep = makeGroup(root, `Wing${suffix}Sweep`, [0, 0, 0], [0, side * 0.22, 0]);
  const display = makeGroup(sweep, `Wing${suffix}Display`);

  // 肩部肌肉
  addEllipsoid(display, `Wing${suffix}_ShoulderMass`, materials.hide,
    [0.03 * side, 0.02, 0.02], [0.21, 0.23, 0.25], 16, 12);

  const elbow = new THREE.Vector3(0.62 * side, 1.08, -0.08);
  const wrist = new THREE.Vector3(1.30 * side, 1.98, -0.18);
  addSegment(display, `Wing${suffix}_Humerus`, materials.hide,
    new THREE.Vector3(0, 0, 0), elbow, 0.18, 0.12, 12);
  addEllipsoid(display, `Wing${suffix}_Elbow`, materials.hide,
    [elbow.x, elbow.y, elbow.z], [0.125, 0.125, 0.125], 14, 10);
  addSegment(display, `Wing${suffix}_Forearm`, materials.hide,
    elbow, wrist, 0.12, 0.085, 12);
  addEllipsoid(display, `Wing${suffix}_Wrist`, materials.hide,
    [wrist.x, wrist.y, wrist.z], [0.09, 0.09, 0.09], 14, 10);

  const leading = [
    new THREE.Vector3(0, 0, 0),
    elbow,
    wrist,
    new THREE.Vector3(2.45 * side, 2.55, -0.35),
  ];
  const trailing = [
    new THREE.Vector3(0.10 * side, -0.55, -0.45),
    new THREE.Vector3(0.30 * side, -0.75, -0.62),
    new THREE.Vector3(1.28 * side, -0.05, -1.08),
    new THREE.Vector3(1.52 * side, 0.34, -0.98),
    new THREE.Vector3(1.84 * side, 0.55, -1.18),
    new THREE.Vector3(2.04 * side, 0.98, -0.82),
    new THREE.Vector3(2.24 * side, 1.30, -0.95),
    new THREE.Vector3(2.32 * side, 1.88, -0.55),
    new THREE.Vector3(2.45 * side, 2.55, -0.35),
  ];
  addWingSurface(display, `Wing${suffix}Root_Wing${suffix}Membrane`, materials.membrane,
    leading, trailing, 0.05, 26, 8);

  // 腕部延伸出的长指骨
  const fingerTips = [
    [2.45 * side, 2.55, -0.35],
    [2.24 * side, 1.30, -0.95],
    [1.84 * side, 0.55, -1.18],
    [1.28 * side, -0.05, -1.08],
  ];
  fingerTips.forEach((tip, index) => {
    addSegment(display, `Wing${suffix}_Finger${index + 1}`, materials.wingBone,
      new THREE.Vector3(wrist.x, wrist.y, wrist.z + 0.04),
      new THREE.Vector3(tip[0], tip[1], tip[2] + 0.04),
      index === 0 ? 0.086 : 0.072, 0.015, 8);
  });

  // 腕部拇指爪
  addCone(display, `Wing${suffix}_ThumbClaw`, materials.wingBone,
    new THREE.Vector3(wrist.x, wrist.y, wrist.z + 0.02),
    new THREE.Vector3(wrist.x + 0.10 * side, wrist.y + 0.28, wrist.z - 0.12), 0.055, 8);

  // 翼膜内侧的骨脊
  addSegment(display, `Wing${suffix}_RootRib`, materials.wingBone,
    new THREE.Vector3(0.18 * side, 0.08, -0.10),
    new THREE.Vector3(0.86 * side, -0.30, -0.78), 0.045, 0.016, 8);

  return root;
}

function buildLeg(parent, materials, side, front) {
  const suffix = `${front ? 'F' : 'B'}${side > 0 ? 'L' : 'R'}`;
  const root = makeGroup(parent, `Leg${suffix}`);

  if (front) {
    const shoulder = [0.60 * side, 1.80, 0.55];
    const elbow = [0.70 * side, 1.15, 0.72];
    const wrist = [0.74 * side, 0.46, 0.84];
    const foot = [0.76 * side, 0.13, 1.02];

    addEllipsoid(root, `Leg${suffix}_Shoulder`, materials.hide, shoulder, [0.27, 0.30, 0.30], 18, 12);
    addLoft(root, `Leg${suffix}_Upper`, materials.hide, [
      { p: shoulder, rx: 0.30, ry: 0.32 },
      { p: [(shoulder[0] + elbow[0]) * 0.5, (shoulder[1] + elbow[1]) * 0.5, (shoulder[2] + elbow[2]) * 0.5], rx: 0.25, ry: 0.26 },
      { p: elbow, rx: 0.20, ry: 0.21 },
    ], 12, true, true);
    addEllipsoid(root, `Leg${suffix}_Elbow`, materials.hide, elbow, [0.20, 0.20, 0.20], 14, 10);
    addLoft(root, `Leg${suffix}_Lower`, materials.hide, [
      { p: elbow, rx: 0.19, ry: 0.20 },
      { p: [(elbow[0] + wrist[0]) * 0.5, (elbow[1] + wrist[1]) * 0.5, (elbow[2] + wrist[2]) * 0.5], rx: 0.155, ry: 0.165 },
      { p: wrist, rx: 0.125, ry: 0.13 },
    ], 12, true, true);
    addEllipsoid(root, `Leg${suffix}_Wrist`, materials.hide, wrist, [0.135, 0.135, 0.135], 14, 10);
    addLoft(root, `Leg${suffix}_Pastern`, materials.hide, [
      { p: wrist, rx: 0.095, ry: 0.10 },
      { p: [(wrist[0] + foot[0]) * 0.5, (wrist[1] + foot[1]) * 0.5 + 0.02, (wrist[2] + foot[2]) * 0.5], rx: 0.105, ry: 0.11 },
      { p: [foot[0], foot[1] + 0.075, foot[2] - 0.02], rx: 0.125, ry: 0.12 },
    ], 12, true, true);
    addEllipsoid(root, `Leg${suffix}_FootJoint`, materials.hideMid, [foot[0], foot[1] + 0.06, foot[2] - 0.02], [0.135, 0.10, 0.135], 14, 10);
    addEllipsoid(root, `Leg${suffix}_Foot`, materials.hideMid, foot, [0.18, 0.095, 0.29], 18, 12);
    buildToes(root, materials, suffix, foot, side, 1.0);
  } else {
    const hip = [0.52 * side, 1.28, -0.90];
    const knee = [0.78 * side, 0.68, -0.30];
    const ankle = [0.82 * side, 0.23, -0.88];
    const foot = [0.82 * side, 0.13, -0.42];

    addEllipsoid(root, `Leg${suffix}_Hip`, materials.hide, hip, [0.29, 0.33, 0.35], 18, 12);
    addLoft(root, `Leg${suffix}_Thigh`, materials.hide, [
      { p: hip, rx: 0.30, ry: 0.32 },
      { p: [(hip[0] + knee[0]) * 0.5, (hip[1] + knee[1]) * 0.5, (hip[2] + knee[2]) * 0.5], rx: 0.25, ry: 0.27 },
      { p: knee, rx: 0.20, ry: 0.21 },
    ], 12, true, true);
    addEllipsoid(root, `Leg${suffix}_Knee`, materials.hide, knee, [0.21, 0.21, 0.21], 14, 10);
    addLoft(root, `Leg${suffix}_Shin`, materials.hide, [
      { p: knee, rx: 0.19, ry: 0.20 },
      { p: [(knee[0] + ankle[0]) * 0.5, (knee[1] + ankle[1]) * 0.5, (knee[2] + ankle[2]) * 0.5], rx: 0.155, ry: 0.16 },
      { p: ankle, rx: 0.11, ry: 0.115 },
    ], 12, true, true);
    addEllipsoid(root, `Leg${suffix}_Ankle`, materials.hide, ankle, [0.12, 0.12, 0.12], 14, 10);
    addLoft(root, `Leg${suffix}_Pastern`, materials.hide, [
      { p: ankle, rx: 0.105, ry: 0.11 },
      { p: [(ankle[0] + foot[0]) * 0.5, (ankle[1] + foot[1]) * 0.5 + 0.03, (ankle[2] + foot[2]) * 0.5], rx: 0.115, ry: 0.12 },
      { p: [foot[0], foot[1] + 0.085, foot[2] - 0.02], rx: 0.135, ry: 0.13 },
    ], 12, true, true);
    addEllipsoid(root, `Leg${suffix}_FootJoint`, materials.hideMid, [foot[0], foot[1] + 0.065, foot[2] - 0.02], [0.15, 0.11, 0.15], 14, 10);
    addEllipsoid(root, `Leg${suffix}_Foot`, materials.hideMid, foot, [0.20, 0.105, 0.34], 18, 12);
    buildToes(root, materials, suffix, foot, side, 1.0);
    // 后脚跟爪
    addCone(root, `Leg${suffix}_HeelClaw`, materials.claw,
      new THREE.Vector3(foot[0], foot[1] - 0.02, foot[2] - 0.28),
      new THREE.Vector3(foot[0], foot[1] - 0.06, foot[2] - 0.48), 0.035, 6);
  }
  return root;
}

function buildToes(parent, materials, suffix, foot, side, scale) {
  const toeOffsets = [-0.11, 0, 0.11];
  toeOffsets.forEach((offset, index) => {
    const base = [foot[0] + offset, foot[1] - 0.01, foot[2] + 0.18];
    const tip = [foot[0] + offset * 1.6, foot[1] - 0.07, foot[2] + 0.38];
    addCone(parent, `Leg${suffix}_Toe${index + 1}`, materials.hideMid,
      new THREE.Vector3(base[0], base[1], base[2]),
      new THREE.Vector3(tip[0], tip[1], tip[2]), 0.065, 8);
    addCone(parent, `Leg${suffix}_Claw${index + 1}`, materials.claw,
      new THREE.Vector3(tip[0], tip[1], tip[2]),
      new THREE.Vector3(tip[0] + offset * 0.4, tip[1] - 0.035, tip[2] + 0.13), 0.028, 6);
  });
}

function buildTail(parent, materials) {
  const tailRoot = makeGroup(parent, 'TailRoot', [0, 1.08, -1.22]);
  const sections = [
    { p: [0, 0.00, 0.00], rx: 0.42, ry: 0.44 },
    { p: [0, -0.08, -0.55], rx: 0.37, ry: 0.38 },
    { p: [0, -0.20, -1.15], rx: 0.31, ry: 0.32 },
    { p: [0, -0.30, -1.75], rx: 0.255, ry: 0.265 },
    { p: [0, -0.30, -2.35], rx: 0.205, ry: 0.215 },
    { p: [0, -0.18, -2.90], rx: 0.16, ry: 0.17 },
    { p: [0, 0.05, -3.38], rx: 0.125, ry: 0.13 },
    { p: [0, 0.40, -3.76], rx: 0.095, ry: 0.10 },
    { p: [0, 0.82, -4.04], rx: 0.07, ry: 0.075 },
    { p: [0, 1.25, -4.18], rx: 0.05, ry: 0.055 },
  ];
  addLoft(tailRoot, 'TailLoft', materials.hide, sections, 14, true, true);

  // 尾脊骨刺
  const spikes = [
    [0.36, -0.25, 0.22],
    [0.22, -0.75, 0.20],
    [0.07, -1.25, 0.18],
    [-0.05, -1.75, 0.16],
    [-0.095, -2.25, 0.15],
    [-0.02, -2.75, 0.14],
    [0.15, -3.15, 0.13],
    [0.38, -3.45, 0.12],
  ];
  spikes.forEach((spike, index) => {
    addCone(tailRoot, `TailSpike_${index + 1}`, materials.bone,
      new THREE.Vector3(0, spike[0], spike[1]),
      new THREE.Vector3(0, spike[0] + spike[2], spike[1] - spike[2] * 0.55), 0.045, 6);
  });

  const blade = makeGroup(tailRoot, 'TailBlade', [0, 1.25, -4.18]);
  buildTailBlade(blade, materials);
  return tailRoot;
}

function buildTailBlade(parent, materials) {
  const finShape = new THREE.Shape();
  finShape.moveTo(0, 0);
  finShape.lineTo(0.16, 0.16);
  finShape.lineTo(0.34, 0.82);
  finShape.lineTo(0.10, 0.64);
  finShape.lineTo(-0.03, 0.96);
  finShape.lineTo(-0.18, 0.58);
  finShape.lineTo(-0.30, 0.22);
  finShape.closePath();
  const finGeometry = new THREE.ExtrudeGeometry(finShape, {
    depth: 0.04,
    steps: 1,
    bevelEnabled: false,
  });
  finGeometry.translate(0, 0, -0.02);
  const fin = addMesh(parent, 'TailBlade_RedFin', finGeometry, materials.bladeRed);
  fin.rotation.y = Math.PI * 0.5;
  fin.scale.set(0.58, 0.58, 0.58);

  const blades = [
    [[0, 0.00, 0.00], [0, 1.04, -0.18], 0.18],
    [[0.02, 0.00, 0.00], [0.58, 0.72, -0.20], 0.13],
    [[-0.02, 0.00, 0.00], [-0.58, 0.72, -0.20], 0.13],
    [[0, -0.01, 0.00], [0.20, -0.46, -0.30], 0.09],
  ];
  blades.forEach((blade, index) => {
    addCone(parent, `TailBlade_Spike${index + 1}`, materials.bone,
      new THREE.Vector3(blade[0][0], blade[0][1], blade[0][2]),
      new THREE.Vector3(blade[1][0], blade[1][1], blade[1][2]), blade[2], 10);
  });
}

function buildSaddle(parent, materials) {
  const saddleGeometry = new THREE.SphereGeometry(1, 24, 14);
  saddleGeometry.scale(0.27, 0.055, 0.38);
  const saddle = addMesh(parent, 'Saddle', saddleGeometry, materials.saddleLeather);
  saddle.position.set(0, 2.12, -0.40);

  addEllipsoid(saddle, 'Saddle_Cantle', materials.saddleLeather, [0, 0.03, -0.26], [0.20, 0.06, 0.08], 18, 10);
  addEllipsoid(saddle, 'Saddle_Pommel', materials.saddleLeather, [0, 0.025, 0.26], [0.17, 0.045, 0.06], 18, 10);

  const strapPositions = [0.30, -0.30];
  strapPositions.forEach((x, index) => {
    const strap = addEllipsoid(saddle, `Saddle_Strap${index + 1}`, materials.saddleLeather,
      [x, -0.30, -0.04], [0.045, 0.34, 0.045], 12, 8);
    strap.rotation.z = x > 0 ? -0.30 : 0.30;
    addEllipsoid(saddle, `Saddle_Buckle${index + 1}`, materials.saddleMetal,
      [x * 0.82, -0.56, -0.04], [0.045, 0.038, 0.024], 12, 8);
  });

  const seatAnchor = new THREE.Group();
  seatAnchor.name = 'SeatAnchor';
  seatAnchor.position.set(0, 0.085, 0.03);
  saddle.add(seatAnchor);
  return saddle;
}

module.exports = function previewModule(moduleRoot, runtime) {
  const { helpers, logger } = runtime;
  helpers.clearGroup(moduleRoot);

  const root = new THREE.Group();
  root.name = 'DragonRoot';
  root.userData.assetBrief = ASSET_BRIEF;
  moduleRoot.add(root);

  const visualRoot = makeGroup(root, 'VisualRoot');
  const materials = makeMaterials();

  buildTorso(visualRoot, materials);
  buildBellyScutes(visualRoot, materials);
  buildDorsalSpikes(visualRoot, materials);
  buildNeck(visualRoot, materials);
  buildWing(visualRoot, materials, 1);
  buildWing(visualRoot, materials, -1);
  buildTail(visualRoot, materials);
  buildLeg(visualRoot, materials, 1, true);
  buildLeg(visualRoot, materials, -1, true);
  buildLeg(visualRoot, materials, 1, false);
  buildLeg(visualRoot, materials, -1, false);
  buildSaddle(visualRoot, materials);

  root.traverse((object) => {
    if (!object.isMesh) return;
    object.castShadow = true;
    object.receiveShadow = true;
  });

  logger.info('Black dragon mount rebuilt with lofted anatomy');
};
