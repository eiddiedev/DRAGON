const THREE = require('three');

const ASSET_BRIEF = {
  identity: 'realistic-wandering-sheep',
  orientation: 'authored space: +X right, -Y forward, +Z up (rig from SHEEP reference skeleton)',
  purpose: 'A realistic domestic sheep that wanders, grazes and steps away from the player.',
  parts: [
    'WoolBody: one continuous lofted wool mass covering rump, barrel and chest',
    'WoolNeck: fluffy collar bridging chest wool and head',
    'Head: dark short-haired skull, tapered muzzle, small drooping ears, dark eyes',
    'Legs: four dark short-haired tapered legs with small hooves',
    'Tail: short woolly tail tuft following the tail bone chain',
  ],
  materials: {
    wool: 'warm off-white matte wool, single continuous mass, no separate tufts',
    skin: 'dark grey short hair on face and legs',
    hoof: 'near-black horn',
    eye: 'glossy black',
  },
  animationNotes: 'All visible meshes follow the SHEEP reference skeleton; ears and tail tuft sit on helper pivots for subtle idle sway.',
};

// Reference skeleton "sheep" from the official skeleton library (global transforms converted to parent-local).
const BONE_DEFS = [
  ['rig', null, [0, 0, 0], [0, 0, 0, 1], [1, 1, 1]],
  ['SK_Sheep', 'rig', [0, 0, 0], [0, 0, 0, 1], [1, 1, 1]],
  ['root', 'SK_Sheep', [0, 0, 0], [-0.707107, 0, 0, 0.707107], [1, 1.000001, 1.000001]],
  ['SHEEP_', 'root', [0, -0.6, 0.23], [0.500001, 0.499999, 0.499999, 0.500001], [0.999999, 0.999999, 0.999999]],
  ['SHEEP_ Pelvis', 'SHEEP_', [0, 0, 0], [-0.500001, 0.499998, -0.499999, 0.500002], [1.000001, 1.000001, 1.000002]],
  ['SHEEP_ L Thigh', 'SHEEP_ Pelvis', [0, -0.1, 0], [0.807485, -0.049792, 0.585117, 0.055914], [0.999999, 0.999999, 0.999999]],
  ['SHEEP_ L Calf', 'SHEEP_ L Thigh', [0.2815, -0.003, -0.0083], [0, 0.617398, 0.000001, 0.786651], [1, 1, 1]],
  ['SHEEP_ L HorseLink', 'SHEEP_ L Calf', [0.1539, 0.0017, -0.0012], [-0.000001, -0.504885, -0.000001, 0.863186], [1, 1, 1]],
  ['SHEEP_ L Foot', 'SHEEP_ L HorseLink', [0.1505, -0.0065, 0.0021], [-0.095899, 0.018882, 0.017924, 0.995051], [1, 1, 1]],
  ['SHEEP_ L Foot_end', 'SHEEP_ L Foot', [0.0001, 0.0006, 0.1487], [0, 0, 0, 1], [1, 1, 1]],
  ['SHEEP_ R Thigh', 'SHEEP_ Pelvis', [0, 0.1, 0], [0.807486, 0.049794, 0.585116, -0.055911], [1, 1.000001, 1]],
  ['SHEEP_ R Calf', 'SHEEP_ R Thigh', [0.2815, 0.003, -0.0083], [-0.000001, 0.617398, 0, 0.786651], [0.999999, 0.999998, 0.999998]],
  ['SHEEP_ R HorseLink', 'SHEEP_ R Calf', [0.1539, -0.0017, -0.0012], [0, -0.504886, 0, 0.863186], [1.000001, 1.000001, 1]],
  ['SHEEP_ R Foot', 'SHEEP_ R HorseLink', [0.1505, 0.0065, 0.0021], [0.095899, 0.018883, -0.017924, 0.99505], [1, 1, 1]],
  ['SHEEP_ R Foot_end', 'SHEEP_ R Foot', [0.0001, -0.0006, 0.1487], [0, 0, 0, 1], [1, 1, 1]],
  ['SHEEP_ Spine', 'SHEEP_ Pelvis', [0.15, 0, 0.08], [-0.000002, -0.000398, -0.000001, 1], [0.999999, 0.999999, 0.999997]],
  ['SHEEP_ Spine1', 'SHEEP_ Spine', [0.19, 0, -0.0002], [0, 0, 0, 1], [1, 1, 1]],
  ['SHEEP_ L Clavicle', 'SHEEP_ Spine1', [0.21, -0.02, 0.0198], [0.767908, -0.551599, 0.189722, 0.26469], [1, 1.000001, 1.000001]],
  ['SHEEP_ L UpperArm', 'SHEEP_ L Clavicle', [0.091, -0.001, 0.0037], [-0.526808, 0.009028, 0.625572, 0.575371], [1.000001, 1.000001, 1]],
  ['SHEEP_ L Forearm', 'SHEEP_ L UpperArm', [0.1571, 0.0084, 0.0074], [0, 0.375161, -0.000001, 0.92696], [1.000001, 1, 1]],
  ['SHEEP_ L Hand', 'SHEEP_ L Forearm', [0.1612, -0.002, -0.0013], [-0.719286, 0.025311, -0.004058, 0.694241], [0.999999, 0.999999, 0.999999]],
  ['SHEEP_ L Finger0', 'SHEEP_ L Hand', [0.0905, -0.0032, 0.0025], [-0.00039, 0.000084, 0.212694, 0.977119], [1, 1, 1]],
  ['SHEEP_ L Finger0_end', 'SHEEP_ L Finger0', [-0.0019, -0.0007, 0.0905], [0, 0, 0, 1], [1, 1, 1]],
  ['SHEEP_ Neck', 'SHEEP_ Spine1', [0.19, 0, -0.0302], [-0.000001, 0.124912, 0.000001, 0.992168], [1.000001, 1.000001, 1.000001]],
  ['SHEEP_ Neck1', 'SHEEP_ Neck', [0.0946, 0, -0.0068], [0.000001, 0.101367, 0, 0.994849], [0.999999, 0.999999, 0.999998]],
  ['SHEEP_ Neck2', 'SHEEP_ Neck1', [0.0984, 0, 0.0034], [0, 0.150881, 0, 0.988552], [1.000001, 1.000001, 1.000001]],
  ['SHEEP_ Head', 'SHEEP_ Neck2', [0.1058, 0, -0.0102], [-0.000001, 0.224432, 0, 0.97449], [0.999999, 0.999999, 0.999999]],
  ['SHEEP_ Queue de cheval 1', 'SHEEP_ Head', [-0.0361, 0, 0.0458], [0.000001, -0.750673, -0.000002, 0.660673], [1.000002, 1.000002, 1.000002]],
  ['SHEEP_ Queue de cheval 1_end', 'SHEEP_ Queue de cheval 1', [0.0018, 0, 0.0671], [0, 0, 0, 1], [1, 1, 1]],
  ['SHEEP_ R Clavicle', 'SHEEP_ Spine1', [0.21, 0.02, 0.0198], [0.767908, 0.551599, 0.189723, -0.264691], [1.000002, 1.000001, 1.000001]],
  ['SHEEP_ R UpperArm', 'SHEEP_ R Clavicle', [0.091, 0.001, 0.0037], [0.526808, 0.009029, -0.625571, 0.575371], [0.999999, 0.999999, 0.999999]],
  ['SHEEP_ R Forearm', 'SHEEP_ R UpperArm', [0.1571, -0.0084, 0.0074], [0, 0.375161, 0.000001, 0.92696], [1.000001, 1.000001, 1.000001]],
  ['SHEEP_ R Hand', 'SHEEP_ R Forearm', [0.1612, 0.002, -0.0013], [0.719287, 0.025311, 0.004059, 0.69424], [0.999999, 0.999999, 0.999999]],
  ['SHEEP_ R Finger0', 'SHEEP_ R Hand', [0.0908, 0.002, -0.0074], [0.000389, 0.000084, -0.212694, 0.977119], [1.000001, 1, 1.000001]],
  ['SHEEP_ R Finger0_end', 'SHEEP_ R Finger0', [-0.0027, 0.0017, 0.1004], [0, 0, 0, 1], [1, 1, 1]],
  ['SHEEP_ Tail', 'SHEEP_ Pelvis', [-0.13, 0, -0.05], [0.000002, 0.934007, 0, -0.357254], [0.999999, 0.999999, 0.999999]],
  ['SHEEP_ Tail1', 'SHEEP_ Tail', [0.0781, 0, 0.0028], [0, 0.051321, 0, 0.998682], [1.000001, 1.000001, 1]],
  ['SHEEP_ Tail2', 'SHEEP_ Tail1', [0.1063, 0, -0.002], [0, 0.05132, 0, 0.998682], [0.999999, 0.999999, 1]],
  ['SHEEP_ Tail2_end', 'SHEEP_ Tail2', [0.0051, 0, 0.108], [0, 0, 0, 1], [1, 1, 1]],
];

// World-space anchor points of the reference skeleton, used to place the visible shell.
const WORLD = {
  pelvis: [0, 0.23, 0.6],
  spine: [0, 0.08, 0.52],
  spine1: [0, -0.11, 0.52],
  neck: [0, -0.3, 0.55],
  neck1: [0, -0.39, 0.58],
  neck2: [0, -0.48, 0.62],
  head: [0, -0.55, 0.7],
  lUpperArm: [0.09, -0.35, 0.45],
  lForearm: [0.07, -0.25, 0.33],
  lHand: [0.07, -0.27, 0.17],
  lFinger: [0.07, -0.28, 0.08],
  rUpperArm: [-0.09, -0.35, 0.45],
  rForearm: [-0.07, -0.25, 0.33],
  rHand: [-0.07, -0.27, 0.17],
  rFinger: [-0.08, -0.28, 0.08],
  lThigh: [0.1, 0.23, 0.6],
  lCalf: [0.1, 0.15, 0.33],
  lHorseLink: [0.08, 0.28, 0.25],
  lFoot: [0.07, 0.27, 0.1],
  rThigh: [-0.1, 0.23, 0.6],
  rCalf: [-0.1, 0.15, 0.33],
  rHorseLink: [-0.08, 0.28, 0.25],
  rFoot: [-0.07, 0.27, 0.1],
  tail2: [0, 0.49, 0.52],
};

function vec(point) {
  return new THREE.Vector3(point[0], point[1], point[2]);
}

function woolNoise(a, b, c) {
  return Math.sin(a * 2.7 + b * 1.3 + c * 0.7) * 0.45
    + Math.sin(a * 5.9 - b * 2.1 + c * 3.3) * 0.32
    + Math.sin(b * 7.7 + c * 4.1) * 0.23;
}

function buildLoft(sections, options = {}) {
  const radialSegments = options.radialSegments || 44;
  const noiseAmp = options.noiseAmp === undefined ? 0.05 : options.noiseAmp;
  const noiseScale = options.noiseScale || 1;
  const positions = [];
  const indices = [];
  const rings = [];

  sections.forEach((section, ringIndex) => {
    const ring = [];
    for (let j = 0; j < radialSegments; j += 1) {
      const angle = (j / radialSegments) * Math.PI * 2;
      const cx = Math.cos(angle);
      const cz = Math.sin(angle);
      const wobble = section.cap
        ? 0
        : woolNoise(cx * 2.2 * noiseScale + ringIndex * 0.11, section.y * 9.5, cz * 2.2 * noiseScale);
      const k = 1 + noiseAmp * wobble;
      positions.push(cx * section.rx * k, section.y, (section.cz || 0) + cz * section.rz * k);
      ring.push(positions.length / 3 - 1);
    }
    rings.push(ring);
  });

  for (let i = 0; i < rings.length - 1; i += 1) {
    const a = rings[i];
    const b = rings[i + 1];
    for (let j = 0; j < radialSegments; j += 1) {
      const next = (j + 1) % radialSegments;
      indices.push(a[j], a[next], b[next]);
      indices.push(a[j], b[next], b[j]);
    }
  }

  const first = sections[0];
  const last = sections[sections.length - 1];
  const startCenter = positions.length / 3;
  positions.push(0, first.y, first.cz || 0);
  const endCenter = positions.length / 3;
  positions.push(0, last.y, last.cz || 0);
  const firstRing = rings[0];
  const lastRing = rings[rings.length - 1];
  for (let j = 0; j < radialSegments; j += 1) {
    const next = (j + 1) % radialSegments;
    indices.push(startCenter, firstRing[next], firstRing[j]);
    indices.push(endCenter, lastRing[j], lastRing[next]);
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}

function buildSegment(start, end, radiusStart, radiusEnd, material, name) {
  const from = vec(start);
  const to = vec(end);
  const direction = to.clone().sub(from);
  const length = direction.length();
  const geometry = new THREE.CylinderGeometry(radiusEnd, radiusStart, length, 14, 1, false);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = name;
  mesh.position.copy(from).add(to).multiplyScalar(0.5);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
  return mesh;
}

function buildEllipsoid(scale, position, material, name, detail = 20) {
  const geometry = new THREE.SphereGeometry(1, detail, Math.max(10, Math.round(detail * 0.7)));
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = name;
  mesh.position.set(position[0], position[1], position[2]);
  mesh.scale.set(scale[0], scale[1], scale[2]);
  return mesh;
}

module.exports = function previewModule(moduleRoot, runtime) {
  const { helpers, logger } = runtime;
  helpers.clearGroup(moduleRoot);

  const previewRoot = new THREE.Group();
  previewRoot.name = 'AnimatedCreaturePreviewRoot';
  previewRoot.worldplayExportRootName = 'rig';
  previewRoot.userData.worldplayExportRootName = 'rig';
  previewRoot.worldplayExportProfile = 'for_unity';
  previewRoot.userData.worldplayExportProfile = 'for_unity';
  previewRoot.userData.assetBrief = ASSET_BRIEF;
  moduleRoot.add(previewRoot);

  const boneNodes = new Map();
  for (const [name, , position, rotation, scale] of BONE_DEFS) {
    const node = new THREE.Group();
    node.name = name;
    node.position.set(position[0], position[1], position[2]);
    node.quaternion.set(rotation[0], rotation[1], rotation[2], rotation[3]);
    node.scale.set(scale[0], scale[1], scale[2]);
    boneNodes.set(name, node);
  }
  for (const [name, parentName] of BONE_DEFS) {
    const node = boneNodes.get(name);
    if (parentName) {
      boneNodes.get(parentName).add(node);
    } else {
      previewRoot.add(node);
    }
  }
  previewRoot.updateMatrixWorld(true);

  const attachToBone = (object, boneName) => {
    const bone = boneNodes.get(boneName);
    object.updateMatrixWorld(true);
    const localMatrix = new THREE.Matrix4().copy(bone.matrixWorld).invert().multiply(object.matrixWorld);
    localMatrix.decompose(object.position, object.quaternion, object.scale);
    bone.add(object);
    return object;
  };

  const woolMaterial = new THREE.MeshStandardMaterial({
    color: 0xf2e9d9,
    roughness: 0.96,
    metalness: 0,
  });
  const innerWoolMaterial = new THREE.MeshStandardMaterial({
    color: 0xe3d8c5,
    roughness: 0.98,
    metalness: 0,
  });
  const skinMaterial = new THREE.MeshStandardMaterial({
    color: 0x4e4b4c,
    roughness: 0.88,
    metalness: 0,
  });
  const muzzleMaterial = new THREE.MeshStandardMaterial({
    color: 0x454244,
    roughness: 0.9,
    metalness: 0,
  });
  const hoofMaterial = new THREE.MeshStandardMaterial({
    color: 0x2a2624,
    roughness: 0.7,
    metalness: 0,
  });
  const eyeMaterial = new THREE.MeshStandardMaterial({
    color: 0x151311,
    roughness: 0.25,
    metalness: 0.1,
  });

  // One continuous wool mass: rump, barrel and chest are a single lofted volume.
  const bodySections = [
    { y: 0.465, cz: 0.44, rx: 0.028, rz: 0.028, cap: true },
    { y: 0.44, cz: 0.445, rx: 0.105, rz: 0.105 },
    { y: 0.40, cz: 0.45, rx: 0.15, rz: 0.155 },
    { y: 0.32, cz: 0.46, rx: 0.175, rz: 0.185 },
    { y: 0.18, cz: 0.45, rx: 0.19, rz: 0.205 },
    { y: 0.02, cz: 0.44, rx: 0.19, rz: 0.21 },
    { y: -0.14, cz: 0.45, rx: 0.185, rz: 0.205 },
    { y: -0.26, cz: 0.465, rx: 0.17, rz: 0.19 },
    { y: -0.34, cz: 0.48, rx: 0.14, rz: 0.155 },
    { y: -0.395, cz: 0.495, rx: 0.07, rz: 0.08 },
    { y: -0.415, cz: 0.5, rx: 0.025, rz: 0.025, cap: true },
  ];
  const woolBody = new THREE.Mesh(buildLoft(bodySections, { radialSegments: 48, noiseAmp: 0.085, noiseScale: 0.8 }), woolMaterial);
  woolBody.name = 'WoolBody';
  attachToBone(woolBody, 'SHEEP_ Spine');

  // Fluffy neck collar bridging chest wool and the dark head.
  const neckSections = [
    { y: -0.335, cz: 0.47, rx: 0.02, rz: 0.02, cap: true },
    { y: -0.36, cz: 0.485, rx: 0.095, rz: 0.1 },
    { y: -0.41, cz: 0.52, rx: 0.115, rz: 0.12 },
    { y: -0.46, cz: 0.58, rx: 0.1, rz: 0.105 },
    { y: -0.5, cz: 0.63, rx: 0.075, rz: 0.08 },
    { y: -0.525, cz: 0.655, rx: 0.02, rz: 0.02, cap: true },
  ];
  const woolNeck = new THREE.Mesh(buildLoft(neckSections, { radialSegments: 40, noiseAmp: 0.08, noiseScale: 0.85 }), innerWoolMaterial);
  woolNeck.name = 'WoolNeck';
  attachToBone(woolNeck, 'SHEEP_ Neck1');

  // Head shell: dark short-haired skull and tapered muzzle.
  const headSections = [
    { y: -0.505, cz: 0.705, rx: 0.02, rz: 0.02, cap: true },
    { y: -0.525, cz: 0.703, rx: 0.055, rz: 0.06 },
    { y: -0.55, cz: 0.7, rx: 0.072, rz: 0.078 },
    { y: -0.59, cz: 0.692, rx: 0.066, rz: 0.072 },
    { y: -0.63, cz: 0.681, rx: 0.052, rz: 0.058 },
    { y: -0.67, cz: 0.671, rx: 0.04, rz: 0.045 },
    { y: -0.7, cz: 0.664, rx: 0.03, rz: 0.034 },
    { y: -0.712, cz: 0.661, rx: 0.012, rz: 0.014, cap: true },
  ];
  const headShell = new THREE.Mesh(buildLoft(headSections, { radialSegments: 36, noiseAmp: 0.012, noiseScale: 1.6 }), skinMaterial);
  headShell.name = 'HeadShell';
  attachToBone(headShell, 'SHEEP_ Head');

  const noseTip = buildEllipsoid([0.026, 0.022, 0.02], [0, -0.702, 0.66], muzzleMaterial, 'Nose', 16);
  attachToBone(noseTip, 'SHEEP_ Head');

  // Top tuft of fleece on the forehead, keeps the wool reading as one coat.
  const forelock = new THREE.Mesh(
    buildLoft([
      { y: -0.5, cz: 0.732, rx: 0.012, rz: 0.012, cap: true },
      { y: -0.518, cz: 0.744, rx: 0.042, rz: 0.04 },
      { y: -0.552, cz: 0.741, rx: 0.047, rz: 0.043 },
      { y: -0.585, cz: 0.729, rx: 0.032, rz: 0.028 },
      { y: -0.603, cz: 0.719, rx: 0.01, rz: 0.01, cap: true },
    ], { radialSegments: 26, noiseAmp: 0.08 }),
    woolMaterial,
  );
  forelock.name = 'Forelock';
  attachToBone(forelock, 'SHEEP_ Head');

  const eyeLeft = buildEllipsoid([0.013, 0.011, 0.011], [0.058, -0.594, 0.712], eyeMaterial, 'Eye_L', 14);
  const eyeRight = buildEllipsoid([0.013, 0.011, 0.011], [-0.058, -0.594, 0.712], eyeMaterial, 'Eye_R', 14);
  attachToBone(eyeLeft, 'SHEEP_ Head');
  attachToBone(eyeRight, 'SHEEP_ Head');

  // Small ears drooping to both sides, on helper pivots for subtle idle sway.
  const buildEar = (side) => {
    const sign = side === 'L' ? 1 : -1;
    const pivot = new THREE.Group();
    pivot.name = `EarPivot_${side}`;
    pivot.position.set(sign * 0.062, -0.535, 0.717);
    pivot.rotation.y = sign * 0.72;
    pivot.rotation.x = sign * 0.05;

    const earMesh = buildEllipsoid([0.05, 0.024, 0.015], [sign * 0.048, 0, -0.004], skinMaterial, `Ear_${side}`, 18);
    pivot.add(earMesh);
    return pivot;
  };
  attachToBone(buildEar('L'), 'SHEEP_ Head');
  attachToBone(buildEar('R'), 'SHEEP_ Head');

  // Legs: dark short-haired tapered segments following the skeleton.
  const legSegments = [
    ['SHEEP_ L UpperArm', 'SHEEP_ L Forearm', WORLD.lUpperArm, WORLD.lForearm, 0.052, 0.038, 'LegFL_Upper'],
    ['SHEEP_ L Forearm', 'SHEEP_ L Hand', WORLD.lForearm, WORLD.lHand, 0.038, 0.027, 'LegFL_Mid'],
    ['SHEEP_ L Hand', 'SHEEP_ L Finger0', WORLD.lHand, WORLD.lFinger, 0.027, 0.023, 'LegFL_Low'],
    ['SHEEP_ R UpperArm', 'SHEEP_ R Forearm', WORLD.rUpperArm, WORLD.rForearm, 0.052, 0.038, 'LegFR_Upper'],
    ['SHEEP_ R Forearm', 'SHEEP_ R Hand', WORLD.rForearm, WORLD.rHand, 0.038, 0.027, 'LegFR_Mid'],
    ['SHEEP_ R Hand', 'SHEEP_ R Finger0', WORLD.rHand, WORLD.rFinger, 0.027, 0.023, 'LegFR_Low'],
    ['SHEEP_ L Thigh', 'SHEEP_ L Calf', WORLD.lThigh, WORLD.lCalf, 0.062, 0.045, 'LegHL_Upper'],
    ['SHEEP_ L Calf', 'SHEEP_ L HorseLink', WORLD.lCalf, WORLD.lHorseLink, 0.045, 0.034, 'LegHL_Mid'],
    ['SHEEP_ L HorseLink', 'SHEEP_ L Foot', WORLD.lHorseLink, WORLD.lFoot, 0.034, 0.025, 'LegHL_Low'],
    ['SHEEP_ R Thigh', 'SHEEP_ R Calf', WORLD.rThigh, WORLD.rCalf, 0.062, 0.045, 'LegHR_Upper'],
    ['SHEEP_ R Calf', 'SHEEP_ R HorseLink', WORLD.rCalf, WORLD.rHorseLink, 0.045, 0.034, 'LegHR_Mid'],
    ['SHEEP_ R HorseLink', 'SHEEP_ R Foot', WORLD.rHorseLink, WORLD.rFoot, 0.034, 0.025, 'LegHR_Low'],
  ];
  for (const [boneName, , start, end, radiusStart, radiusEnd, meshName] of legSegments) {
    const segment = buildSegment(start, end, radiusStart, radiusEnd, skinMaterial, meshName);
    attachToBone(segment, boneName);
  }

  // Lower leg joints keep silhouette continuous while bones move.
  const jointPoints = [
    ['SHEEP_ L Forearm', [WORLD.lForearm, 0.038]],
    ['SHEEP_ L Hand', [WORLD.lHand, 0.028]],
    ['SHEEP_ R Forearm', [WORLD.rForearm, 0.038]],
    ['SHEEP_ R Hand', [WORLD.rHand, 0.028]],
    ['SHEEP_ L Calf', [WORLD.lCalf, 0.045]],
    ['SHEEP_ L HorseLink', [WORLD.lHorseLink, 0.034]],
    ['SHEEP_ R Calf', [WORLD.rCalf, 0.045]],
    ['SHEEP_ R HorseLink', [WORLD.rHorseLink, 0.034]],
  ];
  jointPoints.forEach(([boneName, [point, radius]], index) => {
    const joint = buildEllipsoid([radius, radius, radius], point, skinMaterial, `LegJoint_${index}`, 12);
    attachToBone(joint, boneName);
  });

  // Hooves sit just above the ground plane.
  const hooves = [
    ['SHEEP_ L Finger0', WORLD.lFinger, 0.07],
    ['SHEEP_ R Finger0', WORLD.rFinger, -0.08],
    ['SHEEP_ L Foot', WORLD.lFoot, 0.07],
    ['SHEEP_ R Foot', WORLD.rFoot, -0.07],
  ];
  hooves.forEach(([boneName, point, x], index) => {
    const hoof = buildSegment(
      [x, point[1] - 0.005, 0.075],
      [x, point[1] + 0.02, 0.012],
      0.026,
      0.03,
      hoofMaterial,
      `Hoof_${index}`,
    );
    attachToBone(hoof, boneName);
  });

  // Short woolly tail tuft on a sway pivot under the last tail bone.
  const tailPivot = new THREE.Group();
  tailPivot.name = 'TailPivot';
  tailPivot.position.set(...WORLD.tail2);
  const tailTuft = new THREE.Mesh(
    buildLoft([
      { y: 0.1, cz: 0.038, rx: 0.011, rz: 0.011, cap: true },
      { y: 0.075, cz: 0.026, rx: 0.034, rz: 0.032 },
      { y: 0.038, cz: 0.008, rx: 0.04, rz: 0.038 },
      { y: 0.0, cz: 0.0, rx: 0.016, rz: 0.016, cap: true },
    ], { radialSegments: 22, noiseAmp: 0.1 }),
    woolMaterial,
  );
  tailTuft.name = 'TailTuft';
  tailTuft.quaternion.setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    new THREE.Vector3(0, 0.09, 0.06).normalize(),
  );
  tailPivot.add(tailTuft);
  attachToBone(tailPivot, 'SHEEP_ Tail2');

  previewRoot.userData.assetBrief = ASSET_BRIEF;
  logger.info('Realistic sheep model ready');
};
