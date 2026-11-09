const THREE = require('three');

// Animated-creature source for a realistic dark-bay horse mount. The control
// tree below is copied from the validated "zebra" reference skeleton; visible
// shell meshes are attached to the real control bones in the skeleton frame
// (Z up, -Y forward) and the export profile normalizes the final Unity axes.
const CONTROL_DEFS = [
  { name: 'rig', parentName: null, pos: [0, 0, 0], rot: [0, 0, 0, 1], scale: [1, 1, 1] },
  { name: 'SK_Zebra', parentName: 'rig', pos: [0, 0, 0], rot: [0, 0, 0, 1], scale: [1, 1, 1] },
  { name: 'root', parentName: 'SK_Zebra', pos: [0, 0, 0], rot: [-0.707107, 0, 0, 0.707107], scale: [1, 1, 1] },
  { name: 'ZEBRA_', parentName: 'root', pos: [0, -1.21, 0.65], rot: [0.5, 0.5, 0.5, 0.5], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Pelvis', parentName: 'ZEBRA_', pos: [0, 0, 0], rot: [-0.5, 0.5, -0.5, 0.5], scale: [1, 1, 1] },
  { name: 'ZEBRA_ L Thigh', parentName: 'ZEBRA_ Pelvis', pos: [0, -0.17, 0], rot: [0.729714, -0.105925, 0.666382, 0.1106], scale: [1, 1, 1] },
  { name: 'ZEBRA_ L Calf', parentName: 'ZEBRA_ L Thigh', pos: [0.4518, -0.003, -0.0014], rot: [0, 0.334678, 0, 0.942333], scale: [1, 1, 1] },
  { name: 'ZEBRA_ L HorseLink', parentName: 'ZEBRA_ L Calf', pos: [0.3601, 0.0063, 0.0031], rot: [0, -0.325929, 0, 0.945394], scale: [1, 1, 1] },
  { name: 'ZEBRA_ L Foot', parentName: 'ZEBRA_ L HorseLink', pos: [0.3014, -0.003, 0.0078], rot: [0.003356, 0.03452, 0.010009, 0.999348], scale: [1, 1, 1] },
  { name: 'ZEBRA_ L Foot_end', parentName: 'ZEBRA_ L Foot', pos: [0, 0, 0.3036], rot: [0, 0, 0, 1], scale: [1, 1, 1] },
  { name: 'ZEBRA_ R Thigh', parentName: 'ZEBRA_ Pelvis', pos: [0, 0.17, 0], rot: [0.729715, 0.105926, 0.666382, -0.110598], scale: [1, 1, 1] },
  { name: 'ZEBRA_ R Calf', parentName: 'ZEBRA_ R Thigh', pos: [0.4518, 0.003, -0.0014], rot: [0, 0.334678, 0, 0.942332], scale: [1, 1, 1] },
  { name: 'ZEBRA_ R HorseLink', parentName: 'ZEBRA_ R Calf', pos: [0.3601, -0.0063, 0.0031], rot: [0, -0.325929, 0, 0.945394], scale: [1, 1, 1] },
  { name: 'ZEBRA_ R Foot', parentName: 'ZEBRA_ R HorseLink', pos: [0.3014, 0.003, 0.0078], rot: [-0.003356, 0.03452, -0.010009, 0.999348], scale: [1, 1, 1] },
  { name: 'ZEBRA_ R Foot_end', parentName: 'ZEBRA_ R Foot', pos: [0, 0, 0.3036], rot: [0, 0, 0, 1], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Spine', parentName: 'ZEBRA_ Pelvis', pos: [0.29, 0, 0], rot: [-2e-06, -0.000398, -1e-06, 1], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Spine1', parentName: 'ZEBRA_ Spine', pos: [0.5, 0, -0.0004], rot: [0, 0, 0, 1], scale: [1, 1, 1] },
  { name: 'ZEBRA_ L Clavicle', parentName: 'ZEBRA_ Spine1', pos: [0.5, -0.04, 0.0096], rot: [-0.561141, 0.708888, -0.334876, -0.265437], scale: [1, 1, 1] },
  { name: 'ZEBRA_ L UpperArm', parentName: 'ZEBRA_ L Clavicle', pos: [0.1452, -0.0035, -0.0003], rot: [-0.563903, 0.231388, 0.244968, 0.753965], scale: [1, 1, 1] },
  { name: 'ZEBRA_ L Forearm', parentName: 'ZEBRA_ L UpperArm', pos: [0.3574, 0.0033, 0.0089], rot: [0, 0.171347, 0, 0.985211], scale: [1, 1, 1] },
  { name: 'ZEBRA_ L Hand', parentName: 'ZEBRA_ L Forearm', pos: [0.3412, 0.0012, -0.0011], rot: [-0.760453, 0.002275, -0.032165, 0.648592], scale: [1, 1, 1] },
  { name: 'ZEBRA_ L Finger0', parentName: 'ZEBRA_ L Hand', pos: [0.25, -0.0034, -0.0017], rot: [-0.000399, 6e-06, 0.01493, 0.999888], scale: [1, 1, 1] },
  { name: 'ZEBRA_ L Finger0_end', parentName: 'ZEBRA_ L Finger0', pos: [0.0017, 0.0035, 0.2408], rot: [0, 0, 0, 1], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Neck', parentName: 'ZEBRA_ Spine1', pos: [0.47, 0, 0.0096], rot: [0, 0.158978, 0, 0.987282], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Neck1', parentName: 'ZEBRA_ Neck', pos: [0.1391, 0, -0.0068], rot: [0, 0.065647, 1e-06, 0.997843], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Neck2', parentName: 'ZEBRA_ Neck1', pos: [0.1432, 0, 0.0025], rot: [0, 0.015506, 0, 0.99988], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Neck3', parentName: 'ZEBRA_ Neck2', pos: [0.143, 0, 0.0069], rot: [0, 0.083902, 0, 0.996474], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Head', parentName: 'ZEBRA_ Neck3', pos: [0.142, 0, -0.0052], rot: [0, 0.061109, 0, 0.998131], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Queue de cheval 1', parentName: 'ZEBRA_ Head', pos: [-0.0496, 0, -0.0064], rot: [1e-06, -0.732865, -2e-06, 0.680374], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Queue de cheval 1_end', parentName: 'ZEBRA_ Queue de cheval 1', pos: [-0.0027, 0, 0.0499], rot: [0, 0, 0, 1], scale: [1, 1, 1] },
  { name: 'ZEBRA_ R Clavicle', parentName: 'ZEBRA_ Spine1', pos: [0.5, 0.04, 0.0096], rot: [0.561141, 0.708887, 0.334878, -0.265438], scale: [1, 1, 1] },
  { name: 'ZEBRA_ R UpperArm', parentName: 'ZEBRA_ R Clavicle', pos: [0.1452, 0.0035, -0.0003], rot: [0.563903, 0.231388, -0.244968, 0.753965], scale: [1, 1, 1] },
  { name: 'ZEBRA_ R Forearm', parentName: 'ZEBRA_ R UpperArm', pos: [0.3574, -0.0033, 0.0089], rot: [0, 0.171347, 0, 0.985211], scale: [1, 1, 1] },
  { name: 'ZEBRA_ R Hand', parentName: 'ZEBRA_ R Forearm', pos: [0.3412, -0.0012, -0.0011], rot: [0.760452, 0.002275, 0.032165, 0.648593], scale: [1, 1, 1] },
  { name: 'ZEBRA_ R Finger0', parentName: 'ZEBRA_ R Hand', pos: [0.25, 0.0034, -0.0017], rot: [0.000399, 6e-06, -0.01493, 0.999888], scale: [1, 1, 1] },
  { name: 'ZEBRA_ R Finger0_end', parentName: 'ZEBRA_ R Finger0', pos: [0.0018, -0.0035, 0.2408], rot: [0, 0, 0, 1], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Tail', parentName: 'ZEBRA_ Pelvis', pos: [-0.2, 0, 0.02], rot: [1e-06, 0.873546, 1e-06, -0.486742], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Tail1', parentName: 'ZEBRA_ Tail', pos: [0.0996, 0, 0.0089], rot: [0, 0.000884, 0, 1], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Tail2', parentName: 'ZEBRA_ Tail1', pos: [0.1251, 0, -0.0066], rot: [0, -0.030961, 1e-06, 0.999521], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Tail3', parentName: 'ZEBRA_ Tail2', pos: [0.1278, 0, 0.0077], rot: [0, -0.00555, 0, 0.999985], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Tail4', parentName: 'ZEBRA_ Tail3', pos: [0.086, 0, -0.0004], rot: [0, -0.037694, -1e-06, 0.999289], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Tail5', parentName: 'ZEBRA_ Tail4', pos: [0.2061, 0, -0.0038], rot: [0, 0, 0, 1], scale: [1, 1, 1] },
  { name: 'ZEBRA_ Tail5_end', parentName: 'ZEBRA_ Tail5', pos: [0.0038, 0, 0.2061], rot: [0, 0, 0, 1], scale: [1, 1, 1] },
];

const ASSET_BRIEF = {
  identity: {
    objectClass: 'realistic ridden horse',
    confidence: 1,
    assumptions: [
      'Skeleton frame uses +Z up, -Y forward, +X lateral before Unity export normalization.',
      'The saddle surface and SeatAnchor are placed on the back above the Spine1 control chain.',
    ],
  },
  orientation: { up: '+Z', front: '-Y' },
  silhouette: {
    primaryMasses: ['BodyRear', 'BodyFront', 'NeckLower', 'NeckUpper', 'HeadShell'],
    proportions: 'deep-barrelled bay horse with long neck, compact head, muscular hindquarters and straight forelegs',
    identityCues: ['black mane crest', 'black tail', 'leather saddle', 'metal bit and stirrups'],
  },
  parts: [
    { id: 'BodyRear', level: 'macro', role: 'barrel and hindquarter mass', parent: 'ZEBRA_ Pelvis', topologyClass: 'loft', materialRole: 'coat' },
    { id: 'BodyFront', level: 'macro', role: 'chest and withers mass', parent: 'ZEBRA_ Spine1', topologyClass: 'loft', materialRole: 'coat' },
    { id: 'NeckLower', level: 'macro', role: 'lower neck', parent: 'ZEBRA_ Neck1', topologyClass: 'loft', materialRole: 'coat' },
    { id: 'NeckUpper', level: 'macro', role: 'upper neck and crest base', parent: 'ZEBRA_ Neck3', topologyClass: 'loft', materialRole: 'coat' },
    { id: 'HeadShell', level: 'macro', role: 'cranium and long face', parent: 'ZEBRA_ Head', topologyClass: 'loft', materialRole: 'coat' },
    { id: 'LegHindL', level: 'macro', role: 'left hind leg chain', parent: 'ZEBRA_ L Thigh', topologyClass: 'tapered segments', materialRole: 'coat' },
    { id: 'LegHindR', level: 'macro', role: 'right hind leg chain', parent: 'ZEBRA_ R Thigh', topologyClass: 'tapered segments', materialRole: 'coat' },
    { id: 'LegFrontL', level: 'macro', role: 'left foreleg chain', parent: 'ZEBRA_ L UpperArm', topologyClass: 'tapered segments', materialRole: 'coat' },
    { id: 'LegFrontR', level: 'macro', role: 'right foreleg chain', parent: 'ZEBRA_ R UpperArm', topologyClass: 'tapered segments', materialRole: 'coat' },
    { id: 'TailHair', level: 'macro', role: 'black tail hair and dock', parent: 'ZEBRA_ Tail5', topologyClass: 'loft and strands', materialRole: 'mane' },
    { id: 'ManeCrest', level: 'meso', role: 'black mane crest', parent: 'ZEBRA_ Neck3', topologyClass: 'loft and tufts', materialRole: 'mane' },
    { id: 'SaddlePad', level: 'macro', role: 'visible leather seating surface', parent: 'ZEBRA_ Spine1', topologyClass: 'rounded solid', materialRole: 'leather' },
    { id: 'Tack', level: 'meso', role: 'bridle, reins, girth and stirrups', parent: 'ZEBRA_ Head', topologyClass: 'thin straps and metal rings', materialRole: 'leatherMetal' },
  ],
  details: [
    { id: 'SaddleSeat', region: 'back', kind: 'raised pad', affects: 'geometry', mapsTo: 'SaddleSeat' },
    { id: 'SeatAnchor', region: 'saddle top', kind: 'helper', affects: 'node', mapsTo: 'SaddlePad/SeatAnchor' },
    { id: 'Bridle', region: 'head', kind: 'straps', affects: 'geometry', mapsTo: 'BridleNoseband' },
    { id: 'Bit', region: 'mouth', kind: 'metal', affects: 'geometry', mapsTo: 'BitBar' },
    { id: 'Stirrups', region: 'saddle sides', kind: 'metal', affects: 'geometry', mapsTo: 'Stirrup_L' },
  ],
  materialRoles: {
    coat: { baseColor: 0x3a2316, roughness: 0.4, metalness: 0.02 },
    mane: { baseColor: 0x0d0c0b, roughness: 0.56, metalness: 0.01 },
    leather: { baseColor: 0x4a2c19, roughness: 0.62, metalness: 0.02 },
    metal: { baseColor: 0xb9b3a7, roughness: 0.32, metalness: 0.9 },
    hoof: { baseColor: 0x1a1613, roughness: 0.34, metalness: 0.02 },
  },
  readiness: {
    pivots: CONTROL_DEFS.filter(def => def.parentName).map(def => def.name),
    sockets: ['SaddlePad/SeatAnchor'],
    anchors: ['SeatAnchor'],
    colliderIntent: [],
  },
  detailBudget: {
    must: ['horse silhouette', 'four articulated legs', 'black mane and tail', 'visible saddle with SeatAnchor', 'bridle and bit'],
    optional: ['stirrups', 'reins', 'hoof detail', 'muscle masses'],
  },
};

function makeMaterials() {
  const coat = new THREE.MeshPhysicalMaterial({
    color: 0x3a2316,
    roughness: 0.4,
    metalness: 0.02,
    clearcoat: 0.45,
    clearcoatRoughness: 0.28,
    sheen: 0.18,
    sheenColor: 0x7a5135,
    side: THREE.FrontSide,
  });
  coat.name = 'coat';

  const coatDark = new THREE.MeshPhysicalMaterial({
    color: 0x2a1a10,
    roughness: 0.42,
    metalness: 0.02,
    clearcoat: 0.36,
    clearcoatRoughness: 0.3,
    side: THREE.FrontSide,
  });
  coatDark.name = 'coatDark';

  const coatHighlight = new THREE.MeshPhysicalMaterial({
    color: 0x4a2d1c,
    roughness: 0.44,
    metalness: 0.02,
    clearcoat: 0.3,
    clearcoatRoughness: 0.34,
    side: THREE.FrontSide,
  });
  coatHighlight.name = 'coatHighlight';

  const muzzle = new THREE.MeshPhysicalMaterial({
    color: 0x24150f,
    roughness: 0.46,
    metalness: 0.01,
    clearcoat: 0.3,
    clearcoatRoughness: 0.34,
    side: THREE.FrontSide,
  });
  muzzle.name = 'muzzle';

  const mane = new THREE.MeshStandardMaterial({
    color: 0x0d0c0b,
    roughness: 0.56,
    metalness: 0.01,
    side: THREE.FrontSide,
  });
  mane.name = 'mane';

  const leather = new THREE.MeshStandardMaterial({
    color: 0x4a2c19,
    roughness: 0.62,
    metalness: 0.02,
    side: THREE.FrontSide,
  });
  leather.name = 'leather';

  const darkLeather = new THREE.MeshStandardMaterial({
    color: 0x322013,
    roughness: 0.68,
    metalness: 0.02,
    side: THREE.FrontSide,
  });
  darkLeather.name = 'darkLeather';

  const metal = new THREE.MeshStandardMaterial({
    color: 0xb9b3a7,
    roughness: 0.32,
    metalness: 0.9,
    side: THREE.FrontSide,
  });
  metal.name = 'metal';

  const hoof = new THREE.MeshStandardMaterial({
    color: 0x1a1613,
    roughness: 0.34,
    metalness: 0.02,
    side: THREE.FrontSide,
  });
  hoof.name = 'hoof';

  const eye = new THREE.MeshPhysicalMaterial({
    color: 0x050505,
    roughness: 0.08,
    metalness: 0.05,
    clearcoat: 1,
    clearcoatRoughness: 0.08,
    side: THREE.FrontSide,
  });
  eye.name = 'eye';

  const eyeShine = new THREE.MeshBasicMaterial({ color: 0xf4efe6, side: THREE.FrontSide });
  eyeShine.name = 'eyeShine';

  const stitch = new THREE.MeshStandardMaterial({
    color: 0x9a7a54,
    roughness: 0.72,
    metalness: 0.01,
    side: THREE.FrontSide,
  });
  stitch.name = 'stitch';

  return { coat, coatDark, coatHighlight, muzzle, mane, leather, darkLeather, metal, hoof, eye, eyeShine, stitch };
}

function buildControlTree() {
  const boneMap = new Map();
  for (const def of CONTROL_DEFS) {
    const group = new THREE.Group();
    group.name = def.name;
    group.position.fromArray(def.pos);
    group.quaternion.fromArray(def.rot);
    group.scale.fromArray(def.scale);
    group.userData.rigControlNode = true;
    boneMap.set(def.name, group);
  }

  let rigRoot = null;
  for (const def of CONTROL_DEFS) {
    const group = boneMap.get(def.name);
    if (def.parentName) {
      const parent = boneMap.get(def.parentName);
      if (!parent) {
        throw new Error(`Missing control parent "${def.parentName}" for "${def.name}"`);
      }
      parent.add(group);
    } else {
      rigRoot = group;
    }
  }

  if (!rigRoot) {
    throw new Error('Reference skeleton control tree has no root');
  }
  return { rigRoot, boneMap };
}

function createTubeGeometry(points, radiiX, radiiZ, radialSegments) {
  const positions = [];
  const indices = [];
  const rings = [];
  const count = points.length;
  const segments = radialSegments || 18;

  for (let index = 0; index < count; index += 1) {
    const center = new THREE.Vector3(points[index][0], points[index][1], points[index][2]);
    const prev = new THREE.Vector3(
      points[Math.max(0, index - 1)][0],
      points[Math.max(0, index - 1)][1],
      points[Math.max(0, index - 1)][2],
    );
    const next = new THREE.Vector3(
      points[Math.min(count - 1, index + 1)][0],
      points[Math.min(count - 1, index + 1)][1],
      points[Math.min(count - 1, index + 1)][2],
    );
    const tangent = next.sub(prev);
    if (tangent.lengthSq() < 1e-9) {
      tangent.set(0, -1, 0);
    }
    tangent.normalize();

    let side = new THREE.Vector3(1, 0, 0);
    let up = new THREE.Vector3().crossVectors(tangent, side);
    if (up.lengthSq() < 1e-7) {
      side = new THREE.Vector3(0, 0, 1);
      up = new THREE.Vector3().crossVectors(tangent, side);
    }
    up.normalize();
    side = new THREE.Vector3().crossVectors(up, tangent).normalize();

    rings.push({ center, side, up, rx: radiiX[index], rz: radiiZ[index] });
  }

  for (const ring of rings) {
    for (let segment = 0; segment < segments; segment += 1) {
      const angle = (segment / segments) * Math.PI * 2;
      const vertex = ring.center.clone()
        .addScaledVector(ring.side, Math.cos(angle) * ring.rx)
        .addScaledVector(ring.up, Math.sin(angle) * ring.rz);
      positions.push(vertex.x, vertex.y, vertex.z);
    }
  }

  for (let index = 0; index < rings.length - 1; index += 1) {
    for (let segment = 0; segment < segments; segment += 1) {
      const nextSegment = (segment + 1) % segments;
      const a = index * segments + segment;
      const b = index * segments + nextSegment;
      const c = (index + 1) * segments + segment;
      const d = (index + 1) * segments + nextSegment;
      indices.push(a, b, c, b, d, c);
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}

function createTubeMesh(points, radiiX, radiiZ, material, name, radialSegments) {
  const mesh = new THREE.Mesh(createTubeGeometry(points, radiiX, radiiZ, radialSegments), material);
  mesh.name = name;
  return mesh;
}

function createContourTubeGeometry(points, radiiX, radiiUp, radiiDown, radialSegments) {
  const positions = [];
  const indices = [];
  const rings = [];
  const count = points.length;
  const segments = radialSegments || 20;

  for (let index = 0; index < count; index += 1) {
    const center = new THREE.Vector3(points[index][0], points[index][1], points[index][2]);
    const prev = new THREE.Vector3(
      points[Math.max(0, index - 1)][0],
      points[Math.max(0, index - 1)][1],
      points[Math.max(0, index - 1)][2],
    );
    const next = new THREE.Vector3(
      points[Math.min(count - 1, index + 1)][0],
      points[Math.min(count - 1, index + 1)][1],
      points[Math.min(count - 1, index + 1)][2],
    );
    const tangent = next.sub(prev);
    if (tangent.lengthSq() < 1e-9) {
      tangent.set(0, -1, 0);
    }
    tangent.normalize();

    let side = new THREE.Vector3(1, 0, 0);
    let up = new THREE.Vector3().crossVectors(tangent, side);
    if (up.lengthSq() < 1e-7) {
      side = new THREE.Vector3(0, 0, 1);
      up = new THREE.Vector3().crossVectors(tangent, side);
    }
    up.normalize();
    side = new THREE.Vector3().crossVectors(up, tangent).normalize();

    rings.push({
      center,
      side,
      up,
      rx: radiiX[index],
      upRadius: radiiUp[index],
      downRadius: radiiDown[index],
    });
  }

  for (const ring of rings) {
    for (let segment = 0; segment < segments; segment += 1) {
      const angle = (segment / segments) * Math.PI * 2;
      const sin = Math.sin(angle);
      const verticalRadius = sin >= 0 ? ring.upRadius : ring.downRadius;
      const vertex = ring.center.clone()
        .addScaledVector(ring.side, Math.cos(angle) * ring.rx)
        .addScaledVector(ring.up, sin * verticalRadius);
      positions.push(vertex.x, vertex.y, vertex.z);
    }
  }

  for (let index = 0; index < rings.length - 1; index += 1) {
    for (let segment = 0; segment < segments; segment += 1) {
      const nextSegment = (segment + 1) % segments;
      const a = index * segments + segment;
      const b = index * segments + nextSegment;
      const c = (index + 1) * segments + segment;
      const d = (index + 1) * segments + nextSegment;
      indices.push(a, b, c, b, d, c);
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}

function createContourTubeMesh(points, radiiX, radiiUp, radiiDown, material, name, radialSegments) {
  const mesh = new THREE.Mesh(
    createContourTubeGeometry(points, radiiX, radiiUp, radiiDown, radialSegments),
    material,
  );
  mesh.name = name;
  return mesh;
}

function createBox(center, size, material, name) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(size[0], size[1], size[2]), material);
  mesh.name = name;
  mesh.position.set(center[0], center[1], center[2]);
  return mesh;
}

function createEllipsoid(center, radii, material, name) {
  const geometry = new THREE.SphereGeometry(1, 28, 18);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = name;
  mesh.position.set(center[0], center[1], center[2]);
  mesh.scale.set(radii[0], radii[1], radii[2]);
  return mesh;
}

function createSegment(start, end, radiusStart, radiusEnd, material, name, radialSegments) {
  const a = new THREE.Vector3(start[0], start[1], start[2]);
  const b = new THREE.Vector3(end[0], end[1], end[2]);
  const direction = b.clone().sub(a);
  const length = direction.length();
  if (length < 1e-6) {
    return new THREE.Mesh(new THREE.SphereGeometry(radiusStart, 10, 8), material);
  }
  const geometry = new THREE.CylinderGeometry(radiusEnd, radiusStart, length, radialSegments || 14, 1, false);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = name;
  mesh.position.copy(a).addScaledVector(direction, 0.5);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.clone().normalize());
  return mesh;
}

function createTorus(center, majorRadius, tubeRadius, material, name, rotations, scale) {
  const geometry = new THREE.TorusGeometry(majorRadius, tubeRadius, 10, 40);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = name;
  mesh.position.set(center[0], center[1], center[2]);
  if (rotations) {
    mesh.rotation.set(rotations[0] || 0, rotations[1] || 0, rotations[2] || 0);
  }
  if (scale) {
    mesh.scale.set(scale[0] || 1, scale[1] || 1, scale[2] || 1);
  }
  return mesh;
}

function createTuft(base, direction, length, width, material, name) {
  const geo = new THREE.ConeGeometry(width, length, 7);
  const mesh = new THREE.Mesh(geo, material);
  mesh.name = name;
  const dir = new THREE.Vector3(direction[0], direction[1], direction[2]).normalize();
  mesh.position.set(base[0], base[1], base[2]).addScaledVector(dir, length * 0.45);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
  mesh.scale.x = 0.55;
  return mesh;
}

module.exports = function previewModule(moduleRoot, runtime) {
  const helpers = runtime && runtime.helpers;
  const logger = runtime && runtime.logger;
  if (helpers && typeof helpers.clearGroup === 'function') {
    helpers.clearGroup(moduleRoot);
  }

  const root = new THREE.Group();
  root.name = 'HorseModuleRoot';
  root.userData.assetBrief = ASSET_BRIEF;
  root.worldplayExportRootName = 'rig';
  root.userData.worldplayExportRootName = 'rig';
  root.worldplayExportProfile = 'for_unity';
  root.userData.worldplayExportProfile = 'for_unity';
  moduleRoot.add(root);

  const previewRoot = new THREE.Group();
  previewRoot.name = 'AnimatedCreaturePreviewRoot';
  previewRoot.worldplayExportRootName = 'rig';
  previewRoot.userData.worldplayExportRootName = 'rig';
  previewRoot.worldplayExportProfile = 'for_unity';
  previewRoot.userData.worldplayExportProfile = 'for_unity';
  root.add(previewRoot);

  const { rigRoot, boneMap } = buildControlTree();
  previewRoot.add(rigRoot);
  previewRoot.updateMatrixWorld(true);

  const materials = makeMaterials();
  const bones = name => {
    const bone = boneMap.get(name);
    if (!bone) {
      throw new Error(`Missing reference control node "${name}"`);
    }
    return bone;
  };

  const attach = (object, bone) => {
    previewRoot.add(object);
    object.updateMatrixWorld(true);
    const inverse = new THREE.Matrix4().copy(bone.matrixWorld).invert();
    object.applyMatrix4(inverse);
    bone.add(object);
    return object;
  };

  const place = (object, boneName) => attach(object, bones(boneName));

  const addEllipsoid = (center, radii, material, name, boneName) => {
    const mesh = createEllipsoid(center, radii, material, name);
    place(mesh, boneName);
    return mesh;
  };

  const addSegment = (start, end, r0, r1, material, name, boneName, radial) => {
    const mesh = createSegment(start, end, r0, r1, material, name, radial);
    place(mesh, boneName);
    return mesh;
  };

  // ---- Torso: two overlapping lofts split at the girth line so the spine can bend. ----
  const bodyRings = [
    [1.06, 1.10, 0.10, 0.12, 0.15],
    [0.99, 1.08, 0.20, 0.22, 0.28],
    [0.90, 1.06, 0.28, 0.28, 0.33],
    [0.80, 1.04, 0.33, 0.31, 0.37],
    [0.68, 1.02, 0.355, 0.325, 0.40],
    [0.54, 1.00, 0.37, 0.335, 0.415],
    [0.38, 0.99, 0.37, 0.34, 0.415],
    [0.22, 0.99, 0.36, 0.34, 0.405],
    [0.06, 0.99, 0.345, 0.34, 0.39],
    [-0.10, 1.00, 0.325, 0.34, 0.375],
    [-0.26, 1.01, 0.30, 0.34, 0.355],
    [-0.40, 1.01, 0.27, 0.33, 0.335],
    [-0.52, 1.02, 0.235, 0.30, 0.31],
    [-0.60, 1.04, 0.19, 0.26, 0.27],
    [-0.66, 1.05, 0.14, 0.21, 0.22],
  ];
  const rearRings = bodyRings.slice(0, 10);
  const frontRings = bodyRings.slice(8);

  function addBodyPart(rings, boneName, name) {
    const points = rings.map(r => [0, r[0], r[1]]);
    const mesh = createContourTubeMesh(
      points,
      rings.map(r => r[2]),
      rings.map(r => r[3]),
      rings.map(r => r[4]),
      materials.coat,
      name,
      26,
    );
    place(mesh, boneName);
    return mesh;
  }

  addBodyPart(rearRings, 'ZEBRA_ Pelvis', 'BodyRear');
  addBodyPart(frontRings, 'ZEBRA_ Spine1', 'BodyFront');

  addEllipsoid([0, 0.00, 0.99], [0.345, 0.30, 0.36], materials.coat, 'BarrelBridge', 'ZEBRA_ Spine');
  addEllipsoid([0, 1.06, 1.10], [0.10, 0.12, 0.15], materials.coat, 'RumpCap', 'ZEBRA_ Pelvis');
  addEllipsoid([0, 0.86, 1.17], [0.10, 0.10, 0.13], materials.coat, 'TailBase', 'ZEBRA_ Pelvis');
  addEllipsoid([0, 0.24, 0.68], [0.07, 0.13, 0.07], materials.coatDark, 'Sheath', 'ZEBRA_ Pelvis');
  addEllipsoid([0, 0.80, 1.28], [0.27, 0.18, 0.065], materials.coat, 'CroupRidge', 'ZEBRA_ Pelvis');
  addEllipsoid([0, -0.22, 1.33], [0.23, 0.16, 0.06], materials.coat, 'WithersRidge', 'ZEBRA_ Spine1');
  addEllipsoid([0, 0.10, 0.615], [0.24, 0.26, 0.04], materials.coatHighlight, 'BellyRidge', 'ZEBRA_ Spine');

  for (const side of [-1, 1]) {
    const suffix = side > 0 ? 'L' : 'R';
    addEllipsoid(
      [side * 0.235, 0.62, 1.04],
      [0.14, 0.23, 0.29],
      materials.coat,
      `HaunchMass_${suffix}`,
      'ZEBRA_ Pelvis',
    );
    addEllipsoid(
      [side * 0.225, 0.55, 0.84],
      [0.10, 0.16, 0.18],
      materials.coat,
      `StifleMass_${suffix}`,
      `ZEBRA_ ${suffix} Thigh`,
    );
    addEllipsoid(
      [side * 0.21, -0.30, 1.08],
      [0.10, 0.20, 0.24],
      materials.coat,
      `ShoulderBlade_${suffix}`,
      'ZEBRA_ Spine1',
    );
    addEllipsoid(
      [side * 0.235, -0.42, 0.98],
      [0.11, 0.16, 0.20],
      materials.coat,
      `Triceps_${suffix}`,
      `ZEBRA_ ${suffix} UpperArm`,
    );
    addEllipsoid(
      [side * 0.13, -0.55, 0.93],
      [0.12, 0.13, 0.16],
      materials.coat,
      `Pectoral_${suffix}`,
      'ZEBRA_ Spine1',
    );

    for (let ridge = 0; ridge < 3; ridge += 1) {
      const points = [
        [side * (0.245 + ridge * 0.004), 0.74 - ridge * 0.055, 1.15],
        [side * (0.255 + ridge * 0.004), 0.64 - ridge * 0.055, 1.02],
        [side * (0.245 + ridge * 0.004), 0.56 - ridge * 0.045, 0.88],
      ];
      place(
        createTubeMesh(points, [0.008, 0.009, 0.006], [0.008, 0.009, 0.006], materials.coatHighlight, `HaunchLine_${suffix}_${ridge + 1}`, 6),
        'ZEBRA_ Pelvis',
      );
    }

    for (let ridge = 0; ridge < 2; ridge += 1) {
      const points = [
        [side * (0.225 + ridge * 0.006), -0.22 - ridge * 0.04, 1.18],
        [side * (0.245 + ridge * 0.006), -0.33 - ridge * 0.04, 1.06],
        [side * (0.235 + ridge * 0.006), -0.43 - ridge * 0.035, 0.94],
      ];
      place(
        createTubeMesh(points, [0.007, 0.008, 0.005], [0.007, 0.008, 0.005], materials.coatHighlight, `ShoulderLine_${suffix}_${ridge + 1}`, 6),
        'ZEBRA_ Spine1',
      );
    }
  }

  // ---- Neck: lower and upper lofts overlap under the mane crest. ----
  const neckLower = {
    points: [
      [0, -0.52, 1.12],
      [0, -0.62, 1.18],
      [0, -0.72, 1.25],
      [0, -0.82, 1.31],
    ],
    rx: [0.20, 0.19, 0.175, 0.16],
    up: [0.22, 0.235, 0.245, 0.25],
    down: [0.26, 0.26, 0.25, 0.24],
  };
  const neckUpper = {
    points: [
      [0, -0.72, 1.25],
      [0, -0.82, 1.31],
      [0, -0.92, 1.37],
      [0, -1.02, 1.43],
      [0, -1.10, 1.47],
      [0, -1.15, 1.49],
    ],
    rx: [0.175, 0.16, 0.148, 0.133, 0.12, 0.105],
    up: [0.245, 0.25, 0.245, 0.235, 0.21, 0.17],
    down: [0.25, 0.24, 0.225, 0.205, 0.18, 0.16],
  };
  place(
    createContourTubeMesh(neckLower.points, neckLower.rx, neckLower.up, neckLower.down, materials.coat, 'NeckLower', 22),
    'ZEBRA_ Neck1',
  );
  place(
    createContourTubeMesh(neckUpper.points, neckUpper.rx, neckUpper.up, neckUpper.down, materials.coat, 'NeckUpper', 22),
    'ZEBRA_ Neck3',
  );
  addEllipsoid([0, -0.55, 1.12], [0.22, 0.20, 0.28], materials.coat, 'NeckBase', 'ZEBRA_ Spine1');
  addEllipsoid([0, -0.72, 1.06], [0.13, 0.17, 0.13], materials.coat, 'ThroatLatchMass', 'ZEBRA_ Neck1');
  addEllipsoid([0, -1.12, 1.46], [0.135, 0.13, 0.15], materials.coat, 'PollMass', 'ZEBRA_ Head');

  // ---- Head: long face, jaw, muzzle, ears and eyes all follow the Head bone. ----
  addEllipsoid([0, -1.16, 1.47], [0.135, 0.15, 0.145], materials.coat, 'Cranium', 'ZEBRA_ Head');
  addEllipsoid([0, -1.23, 1.51], [0.11, 0.055, 0.045], materials.coat, 'BrowRidge', 'ZEBRA_ Head');
  const face = {
    points: [
      [0, -1.15, 1.46],
      [0, -1.24, 1.43],
      [0, -1.34, 1.39],
      [0, -1.44, 1.34],
      [0, -1.54, 1.29],
      [0, -1.62, 1.255],
      [0, -1.66, 1.235],
    ],
    rx: [0.13, 0.122, 0.108, 0.094, 0.08, 0.068, 0.058],
    up: [0.135, 0.132, 0.125, 0.115, 0.105, 0.09, 0.075],
    down: [0.145, 0.14, 0.132, 0.122, 0.112, 0.098, 0.082],
  };
  place(
    createContourTubeMesh(face.points, face.rx, face.up, face.down, materials.coat, 'HeadShell', 20),
    'ZEBRA_ Head',
  );
  addEllipsoid([0, -1.30, 1.36], [0.10, 0.17, 0.09], materials.coat, 'JawMass', 'ZEBRA_ Head');
  addEllipsoid([0.105, -1.29, 1.415], [0.065, 0.10, 0.105], materials.coat, 'Cheek_L', 'ZEBRA_ Head');
  addEllipsoid([-0.105, -1.29, 1.415], [0.065, 0.10, 0.105], materials.coat, 'Cheek_R', 'ZEBRA_ Head');
  addEllipsoid([0, -1.63, 1.255], [0.072, 0.078, 0.07], materials.muzzle, 'Muzzle', 'ZEBRA_ Head');
  addEllipsoid([0, -1.65, 1.278], [0.062, 0.06, 0.033], materials.muzzle, 'UpperLip', 'ZEBRA_ Head');
  addEllipsoid([0.045, -1.65, 1.255], [0.025, 0.028, 0.02], materials.mane, 'Nostril_L', 'ZEBRA_ Head');
  addEllipsoid([-0.045, -1.65, 1.255], [0.025, 0.028, 0.02], materials.mane, 'Nostril_R', 'ZEBRA_ Head');
  addSegment([-0.052, -1.645, 1.215], [0.052, -1.645, 1.215], 0.006, 0.006, materials.mane, 'MouthLine', 'ZEBRA_ Head', 6);

  const eyeL = addEllipsoid([0.126, -1.285, 1.475], [0.034, 0.036, 0.034], materials.eye, 'Eye_L', 'ZEBRA_ Head');
  const eyeR = addEllipsoid([-0.126, -1.285, 1.475], [0.034, 0.036, 0.034], materials.eye, 'Eye_R', 'ZEBRA_ Head');
  addEllipsoid([0.144, -1.30, 1.489], [0.010, 0.011, 0.010], materials.eyeShine, 'EyeShine_L', 'ZEBRA_ Head');
  addEllipsoid([-0.144, -1.30, 1.489], [0.010, 0.011, 0.010], materials.eyeShine, 'EyeShine_R', 'ZEBRA_ Head');
  place(createTorus([0.132, -1.285, 1.475], 0.039, 0.007, materials.coatDark, 'EyeRim_L', [0, Math.PI / 2, 0]), 'ZEBRA_ Head');
  place(createTorus([-0.132, -1.285, 1.475], 0.039, 0.007, materials.coatDark, 'EyeRim_R', [0, Math.PI / 2, 0]), 'ZEBRA_ Head');

  const earGeo = new THREE.ConeGeometry(0.047, 0.19, 12);
  const earL = new THREE.Mesh(earGeo, materials.coat);
  earL.name = 'Ear_L';
  earL.position.set(0.078, -1.17, 1.60);
  earL.rotation.set(-0.18, 0, 0.18);
  place(earL, 'ZEBRA_ Head');
  const earR = new THREE.Mesh(earGeo, materials.coat);
  earR.name = 'Ear_R';
  earR.position.set(-0.078, -1.17, 1.60);
  earR.rotation.set(-0.18, 0, -0.18);
  place(earR, 'ZEBRA_ Head');
  addEllipsoid([0.078, -1.19, 1.60], [0.024, 0.012, 0.055], materials.muzzle, 'EarInner_L', 'ZEBRA_ Head');
  addEllipsoid([-0.078, -1.19, 1.60], [0.024, 0.012, 0.055], materials.muzzle, 'EarInner_R', 'ZEBRA_ Head');

  // Forelock follows the ear-bone helper so it sways with the head.
  for (let strand = 0; strand < 5; strand += 1) {
    const offset = (strand - 2) * 0.018;
    const points = [
      [offset, -1.17, 1.59],
      [offset * 1.15, -1.22, 1.55],
      [offset * 1.35, -1.27, 1.49],
      [offset * 1.55, -1.31 + strand * 0.004, 1.435 + strand * 0.006],
    ];
    const radii = [0.015, 0.012, 0.008, 0.002];
    place(
      createTubeMesh(points, radii, radii, materials.mane, `Forelock_${strand + 1}`, 6),
      'ZEBRA_ Queue de cheval 1',
    );
  }

  // ---- Mane: a continuous black crest split across neck bones, plus layered strands. ----
  const crestStations = [
    { y: -0.52, z: 1.35, bone: 'ZEBRA_ Neck1' },
    { y: -0.62, z: 1.43, bone: 'ZEBRA_ Neck1' },
    { y: -0.72, z: 1.50, bone: 'ZEBRA_ Neck2' },
    { y: -0.82, z: 1.57, bone: 'ZEBRA_ Neck2' },
    { y: -0.92, z: 1.625, bone: 'ZEBRA_ Neck3' },
    { y: -1.02, z: 1.675, bone: 'ZEBRA_ Neck3' },
    { y: -1.10, z: 1.69, bone: 'ZEBRA_ Neck3' },
    { y: -1.16, z: 1.67, bone: 'ZEBRA_ Head' },
  ];
  const crestPoints = crestStations.map(station => [0, station.y, station.z]);
  const lowerCrest = crestPoints.slice(0, 4);
  const midCrest = crestPoints.slice(2, 6);
  const upperCrest = crestPoints.slice(4);
  place(createTubeMesh(lowerCrest, lowerCrest.map(() => 0.04), lowerCrest.map(() => 0.075), materials.mane, 'ManeCrestLower', 12), 'ZEBRA_ Neck1');
  place(createTubeMesh(midCrest, midCrest.map(() => 0.038), midCrest.map(() => 0.072), materials.mane, 'ManeCrestMid', 12), 'ZEBRA_ Neck2');
  place(createTubeMesh(upperCrest, upperCrest.map(() => 0.034), upperCrest.map(() => 0.065), materials.mane, 'ManeCrestUpper', 12), 'ZEBRA_ Neck3');

  crestStations.forEach((station, index) => {
    for (const side of [-1, 1]) {
      const points = [
        [0, station.y, station.z],
        [side * 0.018, station.y + 0.018, station.z + 0.025],
        [side * 0.040, station.y + 0.038, station.z - 0.030],
        [side * 0.056, station.y + 0.052, station.z - 0.090],
      ];
      const radii = [0.018, 0.015, 0.010, 0.002];
      place(
        createTubeMesh(points, radii, radii, materials.mane, `ManeStrand_${index + 1}_${side > 0 ? 'L' : 'R'}`, 6),
        station.bone,
      );
    }
  });

  // ---- Legs: tapered segments attached to the actual articulated bones. ----
  const legData = [
    {
      side: 'L',
      hind: true,
      hip: [0.17, 0.65, 1.21],
      knee: [0.17, 0.61, 0.76],
      hock: [0.11, 0.80, 0.46],
      fetlock: [0.11, 0.77, 0.16],
      toe: [0.13, 0.58, 0.055],
      bones: { upper: 'ZEBRA_ L Thigh', mid: 'ZEBRA_ L Calf', lower: 'ZEBRA_ L HorseLink', foot: 'ZEBRA_ L Foot' },
    },
    {
      side: 'R',
      hind: true,
      hip: [-0.17, 0.65, 1.21],
      knee: [-0.17, 0.61, 0.76],
      hock: [-0.11, 0.80, 0.46],
      fetlock: [-0.11, 0.77, 0.16],
      toe: [-0.13, 0.58, 0.055],
      bones: { upper: 'ZEBRA_ R Thigh', mid: 'ZEBRA_ R Calf', lower: 'ZEBRA_ R HorseLink', foot: 'ZEBRA_ R Foot' },
    },
    {
      side: 'L',
      hind: false,
      hip: [0.13, -0.61, 1.09],
      knee: [0.12, -0.50, 0.75],
      hock: [0.10, -0.52, 0.41],
      fetlock: [0.10, -0.52, 0.16],
      toe: [0.11, -0.58, 0.055],
      bones: { upper: 'ZEBRA_ L UpperArm', mid: 'ZEBRA_ L Forearm', lower: 'ZEBRA_ L Hand', foot: 'ZEBRA_ L Finger0' },
    },
    {
      side: 'R',
      hind: false,
      hip: [-0.13, -0.61, 1.09],
      knee: [-0.12, -0.50, 0.75],
      hock: [-0.10, -0.52, 0.41],
      fetlock: [-0.10, -0.52, 0.16],
      toe: [-0.11, -0.58, 0.055],
      bones: { upper: 'ZEBRA_ R UpperArm', mid: 'ZEBRA_ R Forearm', lower: 'ZEBRA_ R Hand', foot: 'ZEBRA_ R Finger0' },
    },
  ];

  for (const leg of legData) {
    const prefix = `${leg.hind ? 'Hind' : 'Front'}${leg.side}`;
    const upperRadii = leg.hind ? [0.18, 0.115] : [0.145, 0.095];
    const midRadii = leg.hind ? [0.115, 0.068] : [0.09, 0.058];
    const lowerRadii = leg.hind ? [0.068, 0.052] : [0.058, 0.05];

    addSegment(leg.hip, leg.knee, upperRadii[0], upperRadii[1], materials.coat, `${prefix}_Upper`, leg.bones.upper, 16);
    addEllipsoid(leg.knee, leg.hind ? [0.112, 0.112, 0.105] : [0.09, 0.09, 0.085], materials.coat, `${prefix}_Knee`, leg.bones.mid);
    addSegment(leg.knee, leg.hock, midRadii[0], midRadii[1], materials.coat, `${prefix}_Calf`, leg.bones.mid, 14);
    addEllipsoid(leg.hock, [0.072, 0.072, 0.07], materials.coat, `${prefix}_Hock`, leg.bones.lower);
    addSegment(leg.hock, leg.fetlock, lowerRadii[0], lowerRadii[1], materials.coatDark, `${prefix}_Cannon`, leg.bones.lower, 12);
    addSegment(
      [leg.hock[0], leg.hock[1] + 0.035, leg.hock[2]],
      [leg.fetlock[0], leg.fetlock[1] + 0.03, leg.fetlock[2]],
      0.016,
      0.010,
      materials.coatHighlight,
      `${prefix}_Tendon`,
      leg.bones.lower,
      8,
    );
    addEllipsoid(leg.fetlock, [0.058, 0.058, 0.056], materials.coat, `${prefix}_Fetlock`, leg.bones.foot);
    addSegment(leg.fetlock, leg.toe, 0.052, 0.074, materials.hoof, `${prefix}_Pastern`, leg.bones.foot, 12);
    addEllipsoid([leg.toe[0], leg.toe[1], 0.035], [0.075, 0.115, 0.045], materials.hoof, `${prefix}_Hoof`, leg.bones.foot);
    place(
      createTorus([leg.toe[0], leg.toe[1], 0.095], 0.062, 0.007, materials.muzzle, `${prefix}_Coronet`, null, [1, 1.3, 1]),
      leg.bones.foot,
    );
    place(
      createTorus([leg.toe[0], leg.toe[1], 0.010], 0.070, 0.005, materials.metal, `${prefix}_Horseshoe`, null, [1, 1.35, 1]),
      leg.bones.foot,
    );

    if (leg.hind) {
      addEllipsoid([leg.hip[0], leg.hip[1], leg.hip[2] - 0.03], [0.13, 0.18, 0.24], materials.coat, `${prefix}_ThighMass`, leg.bones.upper);
    }
  }

  // ---- Tail: dock segments plus long black hair. ----
  const dockUpper = [
    [0, 0.84, 1.20],
    [0, 0.91, 1.11],
    [0, 0.97, 1.00],
    [0, 1.05, 0.90],
  ];
  const dockLower = [
    [0, 1.05, 0.90],
    [0, 1.10, 0.83],
    [0, 1.23, 0.67],
    [0, 1.30, 0.72],
  ];
  place(createTubeMesh(dockUpper, dockUpper.map((_, index) => 0.07 - index * 0.012), dockUpper.map((_, index) => 0.07 - index * 0.012), materials.mane, 'TailDockUpper', 12), 'ZEBRA_ Tail2');
  place(createTubeMesh(dockLower, dockLower.map((_, index) => 0.05 - index * 0.006), dockLower.map((_, index) => 0.05 - index * 0.006), materials.mane, 'TailDockLower', 12), 'ZEBRA_ Tail4');
  place(createTubeMesh(
    [[0, 1.24, 0.68], [0, 1.32, 0.55], [0, 1.38, 0.40], [0, 1.33, 0.28]],
    [0.085, 0.075, 0.05, 0.018],
    [0.085, 0.08, 0.06, 0.025],
    materials.mane,
    'TailHairMass',
    14,
  ), 'ZEBRA_ Tail5');
  addSegment([0, 1.24, 0.68], [0, 1.30, 0.72], 0.025, 0.02, materials.mane, 'TailTip', 'ZEBRA_ Tail5', 8);
  for (let strand = 0; strand < 14; strand += 1) {
    const t = strand / 13;
    const spread = (t - 0.5) * 0.22;
    const side = spread >= 0 ? 1 : -1;
    const length = 0.40 + (strand % 5) * 0.035;
    const points = [
      [spread * 0.30, 1.26, 0.66],
      [spread * 0.55 + side * 0.008, 1.31, 0.56],
      [spread * 0.80 + side * 0.018, 1.33 + (strand % 3) * 0.01, 0.45],
      [spread, 1.30 + (t - 0.5) * 0.08, 0.64 - length + (t - 0.5) * 0.03],
    ];
    const radii = [0.026, 0.021, 0.013, 0.002];
    place(
      createTubeMesh(points, radii, radii, materials.mane, `TailStrand_${strand + 1}`, 6),
      'ZEBRA_ Tail5',
    );
  }

  // ---- Saddle: real visible leather seat; SeatAnchor is a pure child. ----
  const saddlePad = addEllipsoid([0, 0.02, 1.33], [0.34, 0.52, 0.10], materials.leather, 'SaddlePad', 'ZEBRA_ Spine1');
  addEllipsoid([0, 0.02, 1.40], [0.27, 0.33, 0.06], materials.darkLeather, 'SaddleSeat', 'ZEBRA_ Spine1');
  addEllipsoid([0, 0.34, 1.45], [0.23, 0.06, 0.08], materials.leather, 'SaddleCantle', 'ZEBRA_ Spine1');
  addEllipsoid([0, -0.28, 1.45], [0.16, 0.055, 0.07], materials.leather, 'SaddlePommel', 'ZEBRA_ Spine1');
  addEllipsoid([0.31, 0.02, 1.24], [0.035, 0.26, 0.17], materials.leather, 'SaddleFlap_L', 'ZEBRA_ Spine1');
  addEllipsoid([-0.31, 0.02, 1.24], [0.035, 0.26, 0.17], materials.leather, 'SaddleFlap_R', 'ZEBRA_ Spine1');
  place(createTorus([0, 0.02, 1.00], 0.365, 0.022, materials.darkLeather, 'Girth', [Math.PI / 2, 0, 0], [1, 1, 1.02]), 'ZEBRA_ Spine1');
  addSegment([0.315, 0.02, 1.36], [0.34, 0.02, 1.01], 0.018, 0.016, materials.leather, 'StirrupStrap_L', 'ZEBRA_ Spine1', 8);
  addSegment([-0.315, 0.02, 1.36], [-0.34, 0.02, 1.01], 0.018, 0.016, materials.leather, 'StirrupStrap_R', 'ZEBRA_ Spine1', 8);
  place(createTorus([0.34, 0.02, 0.96], 0.082, 0.012, materials.metal, 'Stirrup_L', [0, Math.PI / 2, 0]), 'ZEBRA_ Spine1');
  place(createTorus([-0.34, 0.02, 0.96], 0.082, 0.012, materials.metal, 'Stirrup_R', [0, Math.PI / 2, 0]), 'ZEBRA_ Spine1');
  place(createTorus([0, 0.02, 1.405], 0.265, 0.005, materials.stitch, 'SaddleStitch', null, [1, 1.22, 1]), 'ZEBRA_ Spine1');
  place(createTorus([0, 0.02, 1.335], 0.335, 0.006, materials.stitch, 'SaddlePadTrim', null, [1, 1.5, 1]), 'ZEBRA_ Spine1');
  place(createBox([0.34, 0.02, 1.01], [0.045, 0.032, 0.055], materials.metal, 'GirthBuckle_L'), 'ZEBRA_ Spine1');
  place(createBox([-0.34, 0.02, 1.01], [0.045, 0.032, 0.055], materials.metal, 'GirthBuckle_R'), 'ZEBRA_ Spine1');
  place(createBox([0.34, 0.02, 0.878], [0.105, 0.048, 0.016], materials.metal, 'StirrupPlate_L'), 'ZEBRA_ Spine1');
  place(createBox([-0.34, 0.02, 0.878], [0.105, 0.048, 0.016], materials.metal, 'StirrupPlate_R'), 'ZEBRA_ Spine1');
  place(
    createTubeMesh(
      [[0.22, -0.54, 1.22], [0.08, -0.63, 1.15], [0, -0.66, 1.12], [-0.08, -0.63, 1.15], [-0.22, -0.54, 1.22]],
      [0.018, 0.019, 0.019, 0.019, 0.018],
      [0.018, 0.019, 0.019, 0.019, 0.018],
      materials.darkLeather,
      'BreastCollar',
      8,
    ),
    'ZEBRA_ Spine1',
  );
  place(createTorus([0, -0.66, 1.12], 0.028, 0.007, materials.metal, 'BreastCollarRing', [Math.PI / 2, 0, 0]), 'ZEBRA_ Spine1');

  // SeatAnchor must be a direct child of the visible saddle mesh and contain no mesh.
  previewRoot.updateMatrixWorld(true);
  const seatAnchor = new THREE.Group();
  seatAnchor.name = 'SeatAnchor';
  seatAnchor.position.set(0, 0.0, 1.455);
  seatAnchor.quaternion.setFromEuler(new THREE.Euler(Math.PI / 2, 0, 0));
  previewRoot.add(seatAnchor);
  seatAnchor.updateMatrixWorld(true);
  const saddleInverse = new THREE.Matrix4().copy(saddlePad.matrixWorld).invert();
  seatAnchor.applyMatrix4(saddleInverse);
  saddlePad.add(seatAnchor);

  // ---- Bridle, bit and reins. ----
  place(createTorus([0, -1.43, 1.34], 0.102, 0.012, materials.leather, 'BridleNoseband', [Math.PI / 2, 0, 0], [1, 1, 1.08]), 'ZEBRA_ Head');
  addSegment([0.092, -1.43, 1.35], [0.072, -1.16, 1.53], 0.012, 0.011, materials.leather, 'BridleCheek_L', 'ZEBRA_ Head', 8);
  addSegment([-0.092, -1.43, 1.35], [-0.072, -1.16, 1.53], 0.012, 0.011, materials.leather, 'BridleCheek_R', 'ZEBRA_ Head', 8);
  place(createTorus([0, -1.15, 1.48], 0.122, 0.011, materials.leather, 'BridleCrown', [Math.PI / 2, 0, 0], [1, 1, 1.05]), 'ZEBRA_ Head');
  addSegment([-0.10, -1.49, 1.27], [0.10, -1.49, 1.27], 0.012, 0.012, materials.metal, 'BitBar', 'ZEBRA_ Head', 10);
  place(createTorus([0.10, -1.49, 1.27], 0.031, 0.008, materials.metal, 'BitRing_L', [0, Math.PI / 2, 0]), 'ZEBRA_ Head');
  place(createTorus([-0.10, -1.49, 1.27], 0.031, 0.008, materials.metal, 'BitRing_R', [0, Math.PI / 2, 0]), 'ZEBRA_ Head');
  place(createBox([0.105, -1.43, 1.34], [0.026, 0.030, 0.030], materials.metal, 'BridleBuckle_L'), 'ZEBRA_ Head');
  place(createBox([-0.105, -1.43, 1.34], [0.026, 0.030, 0.030], materials.metal, 'BridleBuckle_R'), 'ZEBRA_ Head');

  const reinSegments = [
    { a: [0.10, -1.48, 1.28], b: [0.135, -1.14, 1.43], bone: 'ZEBRA_ Head', name: 'ReinFront_L' },
    { a: [0.135, -1.14, 1.43], b: [0.17, -0.72, 1.36], bone: 'ZEBRA_ Neck3', name: 'ReinMid_L' },
    { a: [0.17, -0.72, 1.36], b: [0.19, -0.16, 1.43], bone: 'ZEBRA_ Spine1', name: 'ReinRear_L' },
    { a: [-0.10, -1.48, 1.28], b: [-0.135, -1.14, 1.43], bone: 'ZEBRA_ Head', name: 'ReinFront_R' },
    { a: [-0.135, -1.14, 1.43], b: [-0.17, -0.72, 1.36], bone: 'ZEBRA_ Neck3', name: 'ReinMid_R' },
    { a: [-0.17, -0.72, 1.36], b: [-0.19, -0.16, 1.43], bone: 'ZEBRA_ Spine1', name: 'ReinRear_R' },
  ];
  reinSegments.forEach(rein => {
    const mid = [
      (rein.a[0] + rein.b[0]) * 0.5,
      (rein.a[1] + rein.b[1]) * 0.5,
      (rein.a[2] + rein.b[2]) * 0.5 - 0.025,
    ];
    place(
      createTubeMesh([rein.a, mid, rein.b], [0.011, 0.012, 0.011], [0.011, 0.012, 0.011], materials.darkLeather, rein.name, 6),
      rein.bone,
    );
  });

  // A subtle brow band and throat latch add readable tack detail.
  addSegment([0.08, -1.20, 1.53], [-0.08, -1.20, 1.53], 0.010, 0.010, materials.darkLeather, 'BrowBand', 'ZEBRA_ Head', 8);
  addSegment([0.07, -1.30, 1.40], [-0.07, -1.30, 1.40], 0.009, 0.009, materials.darkLeather, 'ThroatLatch', 'ZEBRA_ Head', 8);

  root.traverse(object => {
    if (!object.isMesh) return;
    object.castShadow = true;
    object.receiveShadow = true;
  });

  if (logger && typeof logger.info === 'function') {
    logger.info('Realistic horse mount built from the zebra reference rig');
  }
};
