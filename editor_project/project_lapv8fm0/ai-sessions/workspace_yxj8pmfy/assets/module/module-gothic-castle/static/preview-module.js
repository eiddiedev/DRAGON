const THREE = require('three');

const TAU = Math.PI * 2;

const ASSET_BRIEF = {
  identity: {
    objectClass: 'gothic dark castle on a stone base platform',
    confidence: 0.94,
    assumptions: [
      'player is 0.84m tall, so the front gate is 2.97m high and the great hall vault apex is 7.6m',
      'only the castle and its stone base platform are modelled, the mountain rock is left to the scene',
      'the front pointed arch leads through the 0.7m wall into a walkable great hall',
      'nothing uses a cross, lettering or real-world heraldry',
    ],
  },
  orientation: { up: '+Y', front: '+Z' },
  silhouette: {
    primaryMasses: ['BasePlatform', 'CurtainWall', 'KeepShell', 'KeepRoof', 'Towers'],
    proportions: 'about 15.6m wide, 15.4m tall, 17.3m deep with the front stair',
    identityCues: [
      'pointed front gate with three stepped archivolts',
      'round rose window above the gate',
      'two tall octagonal corner spires over two shorter round towers',
      'crenellated curtain wall with corner turrets',
      'dark purple banners with an original emblem',
    ],
  },
  parts: [
    {
      id: 'BasePlatform',
      level: 'macro',
      role: 'ground contact and courtyard floor',
      parent: 'Structure',
      topologyClass: 'stacked-solid',
      geometryStrategy: 'three chamfered plinth tiers plus a five step entry stair',
      materialRole: 'plinthSurface',
      attachment: null,
      moving: false,
      pivotStrategy: null,
    },
    {
      id: 'CurtainWall',
      level: 'macro',
      role: 'outer enclosure and first silhouette layer',
      parent: 'Structure',
      topologyClass: 'extruded-sheet-with-holes',
      geometryStrategy: 'four extruded curtain walls with a gate opening and arrow slits, crenellated coping',
      materialRole: 'weatheredStone',
      attachment: { parentId: 'BasePlatform', contactType: 'overlap', overlap: 0.02, gapTolerance: 0.002 },
      moving: false,
      pivotStrategy: null,
    },
    {
      id: 'KeepShell',
      level: 'macro',
      role: 'main readable mass with a walkable interior',
      parent: 'Structure',
      topologyClass: 'hollow-extruded-shell',
      geometryStrategy: 'four 0.7m walls with real pointed-arch, lancet and rose openings, gable ends',
      materialRole: 'weatheredStone',
      attachment: { parentId: 'BasePlatform', contactType: 'overlap', overlap: 0.02, gapTolerance: 0.002 },
      moving: false,
      pivotStrategy: null,
    },
    {
      id: 'KeepRoof',
      level: 'macro',
      role: 'steep slate roof and skyline',
      parent: 'Structure',
      topologyClass: 'solid-slab',
      geometryStrategy: 'two steep slate slabs with a ridge cap and iron cresting',
      materialRole: 'slateRoof',
      attachment: { parentId: 'KeepShell', contactType: 'overlap', overlap: 0.05, gapTolerance: 0.004 },
      moving: false,
      pivotStrategy: null,
    },
    {
      id: 'Towers',
      level: 'macro',
      role: 'staggered vertical rhythm and gothic identity',
      parent: 'Structure',
      topologyClass: 'lathed-and-cylindrical',
      geometryStrategy: 'octagonal and round tower shafts with corbelled parapets and concave spires',
      materialRole: 'weatheredStone',
      attachment: { parentId: 'KeepShell', contactType: 'overlap', overlap: 0.2, gapTolerance: 0.004 },
      moving: false,
      pivotStrategy: null,
    },
    {
      id: 'Interior',
      level: 'meso',
      role: 'walkable great hall under a pointed vault',
      parent: 'Structure',
      topologyClass: 'assembled-solid',
      geometryStrategy: 'paving, four clustered columns, rib vault and stone ribs',
      materialRole: 'warmInteriorStone',
      attachment: { parentId: 'BasePlatform', contactType: 'surface-contact', overlap: 0.01, gapTolerance: 0.002 },
      moving: false,
      pivotStrategy: null,
    },
    {
      id: 'Stonework',
      level: 'micro',
      role: 'carved detail: archivolts, tracery, crockets, corbels, crenellations',
      parent: 'Detail',
      topologyClass: 'surface-relief',
      geometryStrategy: 'merged extruded and lathed trim pieces fitted to the facades',
      materialRole: 'carvedStone',
      attachment: { parentId: 'KeepShell', contactType: 'surface-contact', overlap: 0.01, gapTolerance: 0.001 },
      moving: false,
      pivotStrategy: null,
    },
    {
      id: 'Banners',
      level: 'meso',
      role: 'purple heraldic cloth and wind read',
      parent: 'Detail',
      topologyClass: 'thin-shell',
      geometryStrategy: 'double shell cloth with a swallowtail hem on an iron crossbar',
      materialRole: 'bannerCloth',
      attachment: { parentId: 'KeepShell', contactType: 'surface-contact', overlap: 0.03, gapTolerance: 0.002 },
      moving: true,
      pivotStrategy: 'cloth hangs from its own swing group, the iron bar stays fixed',
    },
    {
      id: 'InteriorDecor',
      level: 'micro',
      role: 'warm light read inside the hall',
      parent: 'Detail',
      topologyClass: 'assembled-solid',
      geometryStrategy: 'iron chandelier with candles and wall sconces',
      materialRole: 'ironAndFlame',
      attachment: { parentId: 'Interior', contactType: 'surface-contact', overlap: 0.02, gapTolerance: 0.002 },
      moving: true,
      pivotStrategy: 'chandelier ring turns slowly around its own swing group',
    },
  ],
  details: [
    {
      id: 'RoseWindow',
      region: 'KeepShell/front-upper',
      kind: 'open-and-emissive',
      affects: 'geometry',
      mapsTo: 'Stonework_rose',
      implementation: 'circular wall hole, torus rings, twelve spokes, warm glass disc',
      scale: '2.2m diameter',
      confidence: 0.92,
    },
    {
      id: 'PointedGate',
      region: 'KeepShell/front-central',
      kind: 'opening',
      affects: 'geometry',
      mapsTo: 'Stonework_gate',
      implementation: 'real pointed arch through the wall with three stepped archivolt bands and open timber leaves',
      scale: '1.9m wide, 2.97m high',
      confidence: 0.96,
    },
    {
      id: 'WarmLancets',
      region: 'KeepShell/sides-and-back',
      kind: 'emissive',
      affects: 'material',
      mapsTo: 'Stonework_lancet',
      implementation: 'cut lancet holes with emissive glass, stone mullion and hood ring',
      scale: '0.7m wide, 2.3m high',
      confidence: 0.94,
    },
    {
      id: 'FlyingButtress',
      region: 'KeepShell/sides',
      kind: 'structure',
      affects: 'geometry',
      mapsTo: 'Structure_buttress',
      implementation: 'stepped pier with a curved arch band into the upper wall, pinnacle on top',
      scale: '1.5m span',
      confidence: 0.86,
    },
    {
      id: 'Gargoyles',
      region: 'KeepShell/cornice',
      kind: 'sculpture',
      affects: 'geometry',
      mapsTo: 'Detail_gargoyles',
      implementation: 'carved stone beast projecting from the cornice on six facades',
      scale: '0.6m projection',
      confidence: 0.8,
    },
  ],
  materialRoles: {
    weatheredStone: { baseColor: 0x4c4f53, roughness: 0.92, metalness: 0.02 },
    carvedStone: { baseColor: 0x74787e, roughness: 0.86, metalness: 0.02 },
    plinthSurface: { baseColor: 0x3c3f43, roughness: 0.95, metalness: 0.02 },
    warmInteriorStone: { baseColor: 0x5d564c, roughness: 0.92, metalness: 0.01 },
    slateRoof: { baseColor: 0x2f3b48, roughness: 0.6, metalness: 0.08 },
    ironAndFlame: { baseColor: 0x1a1c1f, roughness: 0.42, metalness: 0.86 },
    warmGlass: { baseColor: 0x6b4a25, roughness: 0.34, metalness: 0.0, emissive: 0xffa63c },
    bannerCloth: { baseColor: 0x2b1b3d, roughness: 0.94, metalness: 0.0 },
  },
  detailBudget: {
    must: [
      'pointed gate with stepped archivolts',
      'rose window',
      'steep spires with pinnacles and iron spikes',
      'crenellated curtain wall with arrow slits',
      'warm glowing lancet windows',
      'purple banners',
      'walkable interior with vault, columns and chandelier',
    ],
    optional: ['blind arcade relief', 'gargoyles', 'crockets', 'corbal table', 'floor inlay'],
  },
};

/* ------------------------------------------------------------------ */
/* small utilities                                                     */
/* ------------------------------------------------------------------ */

const unitBox = new THREE.BoxGeometry(1, 1, 1);
const unitCylinder = new THREE.CylinderGeometry(0.5, 0.5, 1, 12);
const unitCone = new THREE.ConeGeometry(0.5, 1, 8);

function createRng(seed) {
  let state = seed >>> 0;
  return function next() {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function mat4(position, rotation, scale) {
  const matrix = new THREE.Matrix4();
  matrix.compose(
    new THREE.Vector3(
      position ? position[0] : 0,
      position ? position[1] : 0,
      position ? position[2] : 0,
    ),
    new THREE.Quaternion().setFromEuler(new THREE.Euler(
      rotation ? rotation[0] : 0,
      rotation ? rotation[1] : 0,
      rotation ? rotation[2] : 0,
      'XYZ',
    )),
    new THREE.Vector3(
      scale ? scale[0] : 1,
      scale ? scale[1] : 1,
      scale ? scale[2] : 1,
    ),
  );
  return matrix;
}

function makeGroup(parent, name, position) {
  const group = new THREE.Group();
  group.name = name;
  if (position) group.position.set(position[0], position[1], position[2]);
  parent.add(group);
  return group;
}

function addMesh(parent, geometry, material, name) {
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = name;
  parent.add(mesh);
  return mesh;
}

function mergePieces(pieces) {
  const positions = [];
  const normals = [];
  const uvs = [];
  const point = new THREE.Vector3();
  const normal = new THREE.Vector3();
  const normalMatrix = new THREE.Matrix3();

  pieces.forEach((piece) => {
    const source = piece.geometry.index ? piece.geometry.toNonIndexed() : piece.geometry;
    const positionAttr = source.getAttribute('position');
    const normalAttr = source.getAttribute('normal');
    const uvAttr = source.getAttribute('uv');
    normalMatrix.getNormalMatrix(piece.matrix);
    for (let index = 0; index < positionAttr.count; index += 1) {
      point.fromBufferAttribute(positionAttr, index).applyMatrix4(piece.matrix);
      positions.push(point.x, point.y, point.z);
      normal.fromBufferAttribute(normalAttr, index).applyMatrix3(normalMatrix).normalize();
      normals.push(normal.x, normal.y, normal.z);
      if (uvAttr) {
        uvs.push(uvAttr.getX(index), uvAttr.getY(index));
      } else {
        uvs.push(0, 0);
      }
    }
  });

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
  geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geometry.computeBoundingSphere();
  return geometry;
}

/* ------------------------------------------------------------------ */
/* gothic arch helpers                                                 */
/* ------------------------------------------------------------------ */

function archRadius(halfWidth, rise) {
  if (!(halfWidth > 0) || !(rise > 0)) throw new Error('arch needs positive span');
  return (rise * rise + halfWidth * halfWidth) / (2 * halfWidth);
}

// Draws a closed pointed arch outline into a THREE.Shape or THREE.Path.
function appendArchOutline(target, width, base, spring, apex, offsetX) {
  const x = offsetX || 0;
  const halfWidth = width / 2;
  const rise = apex - spring;
  const radius = archRadius(halfWidth, rise);
  const leftCenter = x + (radius - halfWidth);
  const rightCenter = x - (radius - halfWidth);
  const leftAngle = Math.atan2(rise, halfWidth - radius);
  const rightAngle = Math.atan2(rise, radius - halfWidth);
  target.moveTo(x - halfWidth, base);
  target.lineTo(x - halfWidth, spring);
  target.absarc(leftCenter, spring, radius, Math.PI, leftAngle, true);
  target.absarc(rightCenter, spring, radius, rightAngle, 0, true);
  target.lineTo(x + halfWidth, base);
  target.closePath();
}

function pointedArchPath(options) {
  const path = new THREE.Path();
  appendArchOutline(
    path,
    options.width,
    options.base || 0,
    options.spring,
    options.apex,
    options.x || 0,
  );
  return path;
}

function archPlateGeometry(width, base, spring, apex, depth) {
  const shape = new THREE.Shape();
  appendArchOutline(shape, width, base, spring, apex, 0);
  return new THREE.ExtrudeGeometry(shape, {
    depth,
    bevelEnabled: false,
    curveSegments: 18,
  });
}

function archRingGeometry(innerWidth, outerWidth, spring, innerApex, outerApex, depth) {
  const shape = new THREE.Shape();
  appendArchOutline(shape, outerWidth, 0, spring, outerApex, 0);
  shape.holes.push(pointedArchPath({
    width: innerWidth,
    base: 0,
    spring,
    apex: innerApex,
  }));
  return new THREE.ExtrudeGeometry(shape, {
    depth,
    bevelEnabled: false,
    curveSegments: 20,
  });
}

// Sampled pointed arch line from left springing over the apex to right springing.
function archPoints(halfWidth, springY, apexY, segments) {
  const rise = apexY - springY;
  const radius = archRadius(halfWidth, rise);
  const leftCenter = radius - halfWidth;
  const points = [];
  const leftAngle = Math.atan2(rise, halfWidth - radius);
  for (let index = 0; index <= segments; index += 1) {
    const angle = Math.PI + (leftAngle - Math.PI) * (index / segments);
    points.push({
      x: leftCenter + Math.cos(angle) * radius,
      y: springY + Math.sin(angle) * radius,
    });
  }
  const rightAngle = Math.atan2(rise, radius - halfWidth);
  for (let index = 1; index <= segments; index += 1) {
    const angle = rightAngle * (1 - index / segments);
    points.push({
      x: -leftCenter + Math.cos(angle) * radius,
      y: springY + Math.sin(angle) * radius,
    });
  }
  return points;
}

function curvedBandShape(start, end, control, halfWidth, segments) {
  const outer = [];
  const inner = [];
  for (let index = 0; index <= segments; index += 1) {
    const t = index / segments;
    const x = (1 - t) * (1 - t) * start.x + 2 * (1 - t) * t * control.x + t * t * end.x;
    const y = (1 - t) * (1 - t) * start.y + 2 * (1 - t) * t * control.y + t * t * end.y;
    const dx = 2 * (1 - t) * (control.x - start.x) + 2 * t * (end.x - control.x);
    const dy = 2 * (1 - t) * (control.y - start.y) + 2 * t * (end.y - control.y);
    const length = Math.hypot(dx, dy) || 1;
    const nx = -dy / length;
    const ny = dx / length;
    outer.push(new THREE.Vector2(x + nx * halfWidth, y + ny * halfWidth));
    inner.push(new THREE.Vector2(x - nx * halfWidth, y - ny * halfWidth));
  }
  const shape = new THREE.Shape();
  shape.moveTo(outer[0].x, outer[0].y);
  for (let index = 1; index < outer.length; index += 1) {
    shape.lineTo(outer[index].x, outer[index].y);
  }
  for (let index = inner.length - 1; index >= 0; index -= 1) {
    shape.lineTo(inner[index].x, inner[index].y);
  }
  shape.closePath();
  return shape;
}

/* ------------------------------------------------------------------ */
/* procedural textures                                                 */
/* ------------------------------------------------------------------ */

function makeCanvas(width, height) {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');
  if (!context) throw new Error('Canvas 2D context is required');
  return { canvas, context };
}

function finishTexture(canvas) {
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.anisotropy = 8;
  return texture;
}

function createStoneTexture(options) {
  const size = 512;
  const { canvas, context } = makeCanvas(size, size);
  const rand = createRng(options.seed || 1);
  context.fillStyle = options.base;
  context.fillRect(0, 0, size, size);

  for (let index = 0; index < 280; index += 1) {
    const x = rand() * size;
    const y = rand() * size;
    const radius = 10 + rand() * 62;
    const gradient = context.createRadialGradient(x, y, 0, x, y, radius);
    const light = rand() > 0.5;
    gradient.addColorStop(0, light ? 'rgba(255,255,255,0.055)' : 'rgba(0,0,0,0.09)');
    gradient.addColorStop(1, 'rgba(0,0,0,0)');
    context.fillStyle = gradient;
    context.beginPath();
    context.arc(x, y, radius, 0, TAU);
    context.fill();
  }

  const rows = options.rows || 8;
  const rowHeight = size / rows;
  for (let row = 0; row < rows; row += 1) {
    const y = row * rowHeight;
    context.strokeStyle = options.mortar;
    context.lineWidth = 3;
    context.beginPath();
    context.moveTo(0, y);
    context.lineTo(size, y);
    context.stroke();
    context.strokeStyle = 'rgba(224,230,236,0.16)';
    context.lineWidth = 1.4;
    context.beginPath();
    context.moveTo(0, y + 2.5);
    context.lineTo(size, y + 2.5);
    context.stroke();

    const period = rowHeight * 2;
    const offset = row % 2 === 0 ? 0 : rowHeight;
    for (let joint = -1; joint <= 4; joint += 1) {
      const x = offset + joint * period;
      context.strokeStyle = options.mortar;
      context.lineWidth = 2.6;
      context.beginPath();
      context.moveTo(x, y);
      context.lineTo(x, y + rowHeight);
      context.stroke();
      const streak = context.createLinearGradient(0, y + rowHeight, 0, y + rowHeight * 3);
      streak.addColorStop(0, 'rgba(14,18,22,0.24)');
      streak.addColorStop(1, 'rgba(14,18,22,0)');
      context.fillStyle = streak;
      context.fillRect(x - 2, y + rowHeight, 7, rowHeight * 2);
    }
  }

  for (let index = 0; index < 520; index += 1) {
    const x = rand() * size;
    const y = rand() * size;
    const radius = 0.6 + rand() * 2.4;
    context.fillStyle = rand() > 0.45 ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.11)';
    context.beginPath();
    context.arc(x, y, radius, 0, TAU);
    context.fill();
  }

  for (let index = 0; index < 70; index += 1) {
    const x = rand() * size;
    const y = rand() * size;
    context.fillStyle = 'rgba(84,94,70,0.07)';
    context.beginPath();
    context.arc(x, y, 4 + rand() * 13, 0, TAU);
    context.fill();
  }

  return finishTexture(canvas);
}

function createSlateTexture() {
  const size = 512;
  const { canvas, context } = makeCanvas(size, size);
  const rand = createRng(24);
  context.fillStyle = '#26313d';
  context.fillRect(0, 0, size, size);
  const rowHeight = 24;
  const shingleWidth = 40;
  for (let row = 0; row * rowHeight < size + rowHeight; row += 1) {
    const y = row * rowHeight;
    const offset = (row % 2) * (shingleWidth / 2);
    for (let column = -1; column * shingleWidth < size + shingleWidth; column += 1) {
      const x = column * shingleWidth + offset;
      const shade = 38 + Math.floor(rand() * 22);
      context.fillStyle = 'rgb(' + (shade - 6) + ',' + (shade + 4) + ',' + (shade + 16) + ')';
      context.fillRect(x + 1, y + 1, shingleWidth - 2, rowHeight - 2);
      context.fillStyle = 'rgba(8,12,18,0.55)';
      context.fillRect(x, y + rowHeight - 3, shingleWidth, 2.4);
      context.fillStyle = 'rgba(190,205,220,0.07)';
      context.fillRect(x, y + 1, shingleWidth - 1, 2);
    }
  }
  for (let index = 0; index < 240; index += 1) {
    const x = rand() * size;
    const y = rand() * size;
    context.fillStyle = rand() > 0.5 ? 'rgba(210,225,240,0.05)' : 'rgba(0,0,0,0.10)';
    context.beginPath();
    context.arc(x, y, 1 + rand() * 3, 0, TAU);
    context.fill();
  }
  return finishTexture(canvas);
}

function createPavingTexture() {
  const size = 512;
  const { canvas, context } = makeCanvas(size, size);
  const rand = createRng(57);
  context.fillStyle = '#3a3d41';
  context.fillRect(0, 0, size, size);
  const cell = size / 4;
  for (let row = 0; row < 4; row += 1) {
    for (let column = 0; column < 4; column += 1) {
      const shade = 58 + Math.floor(rand() * 22);
      context.fillStyle = 'rgb(' + shade + ',' + (shade + 2) + ',' + (shade + 5) + ')';
      context.fillRect(column * cell + 3, row * cell + 3, cell - 6, cell - 6);
      context.fillStyle = 'rgba(255,255,255,0.045)';
      context.fillRect(column * cell + 6, row * cell + 6, cell - 12, 3);
    }
  }
  for (let index = 0; index < 460; index += 1) {
    const x = rand() * size;
    const y = rand() * size;
    context.fillStyle = rand() > 0.5 ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.12)';
    context.beginPath();
    context.arc(x, y, 0.7 + rand() * 2.2, 0, TAU);
    context.fill();
  }
  return finishTexture(canvas);
}

function createWoodTexture() {
  const size = 256;
  const { canvas, context } = makeCanvas(size, size);
  const rand = createRng(91);
  context.fillStyle = '#3b2c21';
  context.fillRect(0, 0, size, size);
  for (let index = 0; index < 70; index += 1) {
    const x = rand() * size;
    context.strokeStyle = rand() > 0.5 ? 'rgba(24,17,12,0.55)' : 'rgba(120,92,64,0.28)';
    context.lineWidth = 0.8 + rand() * 2.6;
    context.beginPath();
    context.moveTo(x, 0);
    context.bezierCurveTo(x + rand() * 8 - 4, size * 0.35, x + rand() * 8 - 4, size * 0.7, x + rand() * 6 - 3, size);
    context.stroke();
  }
  return finishTexture(canvas);
}

function createBannerTexture() {
  const width = 256;
  const height = 512;
  const { canvas, context } = makeCanvas(width, height);
  const gradient = context.createLinearGradient(0, 0, width, 0);
  gradient.addColorStop(0, '#1d1229');
  gradient.addColorStop(0.5, '#33204a');
  gradient.addColorStop(1, '#1d1229');
  context.fillStyle = gradient;
  context.fillRect(0, 0, width, height);

  context.strokeStyle = '#8b86ab';
  context.lineWidth = 9;
  context.strokeRect(16, 16, width - 32, height - 32);
  context.strokeStyle = 'rgba(168,162,196,0.5)';
  context.lineWidth = 3;
  context.strokeRect(32, 32, width - 64, height - 64);

  context.save();
  context.translate(width / 2, 200);
  context.strokeStyle = '#b3adcd';
  context.lineWidth = 5;
  context.beginPath();
  context.moveTo(0, -78);
  context.lineTo(62, 0);
  context.lineTo(0, 78);
  context.lineTo(-62, 0);
  context.closePath();
  context.stroke();
  context.fillStyle = 'rgba(178,172,205,0.22)';
  context.fill();
  context.beginPath();
  context.moveTo(0, -44);
  context.lineTo(34, 0);
  context.lineTo(0, 44);
  context.lineTo(-34, 0);
  context.closePath();
  context.stroke();
  context.restore();

  context.fillStyle = '#b3adcd';
  [-52, 0, 52].forEach((offset, index) => {
    const cx = width / 2 + offset;
    const cy = 96 + (index === 1 ? -14 : 0);
    context.beginPath();
    context.moveTo(cx, cy - 15);
    context.lineTo(cx + 5, cy - 4);
    context.lineTo(cx + 16, cy);
    context.lineTo(cx + 5, cy + 4);
    context.lineTo(cx, cy + 15);
    context.lineTo(cx - 5, cy + 4);
    context.lineTo(cx - 16, cy);
    context.lineTo(cx - 5, cy - 4);
    context.closePath();
    context.fill();
  });

  context.save();
  context.translate(width / 2, 342);
  context.strokeStyle = '#b3adcd';
  context.lineWidth = 9;
  context.beginPath();
  context.arc(0, 0, 46, Math.PI * 0.15, Math.PI * 0.85, false);
  context.stroke();
  context.beginPath();
  context.arc(20, -14, 42, Math.PI * 0.2, Math.PI * 1.55, false);
  context.stroke();
  context.restore();

  context.fillStyle = 'rgba(0,0,0,0.18)';
  for (let index = 0; index < 30; index += 1) {
    context.fillRect(0, 380 + index * 4, width, 1);
  }

  return finishTexture(canvas);
}

function createInlayTexture() {
  const size = 512;
  const { canvas, context } = makeCanvas(size, size);
  context.fillStyle = '#2c2b2a';
  context.fillRect(0, 0, size, size);
  const center = size / 2;
  context.strokeStyle = '#8d8574';
  context.lineWidth = 7;
  context.beginPath();
  context.arc(center, center, 214, 0, TAU);
  context.stroke();
  context.strokeStyle = 'rgba(150,142,124,0.6)';
  context.lineWidth = 3;
  context.beginPath();
  context.arc(center, center, 176, 0, TAU);
  context.stroke();
  for (let index = 0; index < 12; index += 1) {
    const angle = (index / 12) * TAU;
    context.strokeStyle = 'rgba(146,138,120,0.55)';
    context.lineWidth = 4;
    context.beginPath();
    context.moveTo(center + Math.cos(angle) * 60, center + Math.sin(angle) * 60);
    context.lineTo(center + Math.cos(angle) * 172, center + Math.sin(angle) * 172);
    context.stroke();
  }
  context.fillStyle = '#6d6454';
  context.beginPath();
  context.arc(center, center, 34, 0, TAU);
  context.fill();
  context.fillStyle = '#2c2b2a';
  context.beginPath();
  context.arc(center, center, 20, 0, TAU);
  context.fill();
  return finishTexture(canvas);
}

/* ------------------------------------------------------------------ */
/* materials                                                           */
/* ------------------------------------------------------------------ */

function cloneWithRepeat(texture, repeatU, repeatV) {
  const cloned = texture.clone();
  cloned.needsUpdate = true;
  cloned.wrapS = THREE.RepeatWrapping;
  cloned.wrapT = THREE.RepeatWrapping;
  cloned.repeat.set(repeatU, repeatV);
  cloned.anisotropy = 8;
  return cloned;
}

function standardMaterial(name, color, roughness, metalness, extra) {
  const material = new THREE.MeshStandardMaterial(Object.assign({
    color,
    roughness,
    metalness,
    side: THREE.FrontSide,
  }, extra || {}));
  material.name = name;
  return material;
}

function createMaterials() {
  const wallTexture = createStoneTexture({
    base: '#4c4f53',
    mortar: '#2c2f33',
    rows: 8,
    seed: 11,
  });
  const trimTexture = createStoneTexture({
    base: '#767a80',
    mortar: '#4d5157',
    rows: 10,
    seed: 23,
  });
  const plinthTexture = createStoneTexture({
    base: '#3b3e42',
    mortar: '#232629',
    rows: 6,
    seed: 37,
  });
  const interiorTexture = createStoneTexture({
    base: '#5f584d',
    mortar: '#3b362e',
    rows: 9,
    seed: 41,
  });
  const slateTexture = createSlateTexture();
  const pavingTexture = createPavingTexture();
  const woodTexture = createWoodTexture();
  const bannerTexture = createBannerTexture();
  const inlayTexture = createInlayTexture();

  const wallBody = standardMaterial('wall-body', 0xffffff, 0.92, 0.02, {
    map: cloneWithRepeat(wallTexture, 0.5, 0.5),
  });
  const wallTower = standardMaterial('wall-tower', 0xffffff, 0.92, 0.02, {
    map: cloneWithRepeat(wallTexture, 4, 4),
  });
  const trim = standardMaterial('carved-trim', 0xffffff, 0.86, 0.02, {
    map: cloneWithRepeat(trimTexture, 1.6, 1.6),
  });
  const plinth = standardMaterial('plinth-stone', 0xffffff, 0.95, 0.02, {
    map: cloneWithRepeat(plinthTexture, 0.9, 0.9),
  });
  const paving = standardMaterial('paving', 0xffffff, 0.94, 0.02, {
    map: cloneWithRepeat(pavingTexture, 0.5, 0.5),
  });
  const interiorStone = standardMaterial('interior-stone', 0xffffff, 0.92, 0.01, {
    map: cloneWithRepeat(interiorTexture, 0.6, 0.6),
  });
  const slate = standardMaterial('slate-roof', 0xffffff, 0.62, 0.08, {
    map: cloneWithRepeat(slateTexture, 8, 10),
  });
  const slateSpire = standardMaterial('slate-spire', 0xffffff, 0.62, 0.08, {
    map: cloneWithRepeat(slateTexture, 4, 6),
  });
  const iron = standardMaterial('iron', 0x1a1c1f, 0.42, 0.86);
  const dark = standardMaterial('dark-inset', 0x101216, 0.95, 0.04);
  const glass = standardMaterial('warm-glass', 0x6b4a25, 0.34, 0.0, {
    emissive: 0xffa63c,
    emissiveIntensity: 1.15,
  });
  const flame = standardMaterial('flame', 0xffd28a, 0.4, 0.0, {
    emissive: 0xffae4a,
    emissiveIntensity: 1.7,
  });
  const wax = standardMaterial('candle-wax', 0xd9cdb4, 0.72, 0.0);
  const cloth = standardMaterial('banner-cloth', 0xffffff, 0.94, 0.0, {
    map: cloneWithRepeat(bannerTexture, 1, 1),
  });
  const wood = standardMaterial('gate-wood', 0xffffff, 0.8, 0.0, {
    map: cloneWithRepeat(woodTexture, 1, 2),
  });
  const inlay = standardMaterial('floor-inlay', 0xffffff, 0.9, 0.02, {
    map: cloneWithRepeat(inlayTexture, 1, 1),
  });

  return {
    wallBody,
    wallTower,
    trim,
    plinth,
    paving,
    interiorStone,
    slate,
    slateSpire,
    iron,
    dark,
    glass,
    flame,
    wax,
    cloth,
    wood,
    inlay,
  };
}

/* ------------------------------------------------------------------ */
/* shared dimensions                                                   */
/* ------------------------------------------------------------------ */

const D = {
  platformTop: 0.78,
  platformHalf: 7.5,
  keepHalfX: 3.7,
  keepZ0: -6.1,
  keepZ1: 0.9,
  wallThickness: 0.7,
  keepWallTop: 8.4,
  gableApex: 11.6,
  vaultSpring: 4.4,
  vaultApex: 7.6,
  innerHalfX: 3.0,
  innerZ0: -5.4,
  innerZ1: 0.2,
  floorTop: 0.79,
};

/* ------------------------------------------------------------------ */
/* base platform                                                       */
/* ------------------------------------------------------------------ */

function chamferRectShape(halfX, halfZ, chamfer) {
  const shape = new THREE.Shape();
  shape.moveTo(-halfX + chamfer, -halfZ);
  shape.lineTo(halfX - chamfer, -halfZ);
  shape.lineTo(halfX, -halfZ + chamfer);
  shape.lineTo(halfX, halfZ - chamfer);
  shape.lineTo(halfX - chamfer, halfZ);
  shape.lineTo(-halfX + chamfer, halfZ);
  shape.lineTo(-halfX, halfZ - chamfer);
  shape.lineTo(-halfX, -halfZ + chamfer);
  shape.closePath();
  return shape;
}

function buildPlatform(parent, mats, collectors) {
  const tiers = [
    { half: 7.8, chamfer: 1.15, y0: 0, y1: 0.24 },
    { half: 7.66, chamfer: 1.08, y0: 0.24, y1: 0.5 },
    { half: 7.52, chamfer: 1.0, y0: 0.5, y1: D.platformTop },
  ];

  tiers.forEach((tier, index) => {
    const shape = chamferRectShape(tier.half, tier.half, tier.chamfer);
    const geometry = new THREE.ExtrudeGeometry(shape, {
      depth: tier.y1 - tier.y0,
      bevelEnabled: false,
      curveSegments: 2,
      steps: 1,
    });
    geometry.rotateX(-Math.PI / 2);
    geometry.translate(0, tier.y1, 0);
    const mesh = new THREE.Mesh(geometry, [mats.paving, mats.plinth]);
    mesh.name = 'PlatformTier' + (index + 1);
    parent.add(mesh);
  });

  // front entry stair (real structure so the player can climb it)
  const stair = makeGroup(parent, 'EntryStair');
  const stepCount = 5;
  for (let index = 0; index < stepCount; index += 1) {
    const top = D.platformTop - 0.13 * (index + 1);
    const zNear = 7.52 + index * 0.4;
    const width = 4.4 - index * 0.18;
    const step = addMesh(stair, new THREE.BoxGeometry(width, top, 0.42), mats.plinth, 'EntryStep' + index);
    step.position.set(0, top / 2, zNear + 0.2);
    const nosing = addMesh(stair, new THREE.BoxGeometry(width + 0.08, 0.06, 0.46), mats.trim, 'EntryNosing' + index);
    nosing.position.set(0, top - 0.03, zNear + 0.19);
  }

  // courtyard brazier bases on the platform
  [-2.7, 2.7].forEach((x, index) => {
    const name = 'Brazier' + index;
    const group = makeGroup(parent, name, [x, D.platformTop, 3.0]);
    const foot = addMesh(group, new THREE.CylinderGeometry(0.42, 0.5, 0.18, 8), mats.plinth, name + 'Foot');
    foot.position.y = 0.09;
    const stem = addMesh(group, new THREE.CylinderGeometry(0.16, 0.24, 0.95, 8), mats.trim, name + 'Stem');
    stem.position.y = 0.62;
    const bowl = addMesh(group, new THREE.CylinderGeometry(0.46, 0.26, 0.34, 12), mats.iron, name + 'Bowl');
    bowl.position.y = 1.24;
    const embers = addMesh(group, new THREE.SphereGeometry(0.34, 12, 8), mats.flame, name + 'Embers');
    embers.position.y = 1.34;
    embers.scale.y = 0.26;
  });
}

/* ------------------------------------------------------------------ */
/* curtain wall                                                        */
/* ------------------------------------------------------------------ */

function crenellateX(collector, from, to, z, yBase, thickness, skip) {
  const merlon = 0.5;
  const gap = 0.44;
  const step = merlon + gap;
  for (let x = from; x + merlon <= to + 0.001; x += step) {
    const center = x + merlon / 2;
    if (skip && center > skip[0] && center < skip[1]) continue;
    collector.push({
      geometry: unitBox,
      matrix: mat4([center, yBase + 0.26, z], [0, 0, 0], [merlon, 0.52, thickness]),
    });
  }
}

function crenellateZ(collector, from, to, x, yBase, thickness, skip) {
  const merlon = 0.5;
  const gap = 0.44;
  const step = merlon + gap;
  for (let z = from; z + merlon <= to + 0.001; z += step) {
    const center = z + merlon / 2;
    if (skip && center > skip[0] && center < skip[1]) continue;
    collector.push({
      geometry: unitBox,
      matrix: mat4([x, yBase + 0.26, center], [0, 0, 0], [thickness, 0.52, merlon]),
    });
  }
}

function addSlitHole(shape, centerX, bottom, top, halfWidth) {
  const hole = new THREE.Path();
  hole.moveTo(centerX - halfWidth, bottom);
  hole.lineTo(centerX + halfWidth, bottom);
  hole.lineTo(centerX + halfWidth, top);
  hole.lineTo(centerX - halfWidth, top);
  hole.closePath();
  shape.holes.push(hole);
}

function buildCurtainWall(parent, mats, collectors) {
  const wallTop = 3.18;
  const wallHeight = wallTop - D.platformTop;
  const thickness = 0.45;
  const outer = 7.5;
  const inner = outer - thickness;

  // front wall with gate opening and arrow slits
  const frontShape = new THREE.Shape();
  frontShape.moveTo(-outer, -0.05);
  frontShape.lineTo(outer, -0.05);
  frontShape.lineTo(outer, wallHeight);
  frontShape.lineTo(-outer, wallHeight);
  frontShape.closePath();
  frontShape.holes.push(pointedArchPath({ width: 2.0, base: 0, spring: 1.42, apex: 2.16 }));
  [-4.9, -2.6, 2.6, 4.9].forEach((x) => {
    addSlitHole(frontShape, x, 0.8, 1.75, 0.07);
  });
  const frontGeometry = new THREE.ExtrudeGeometry(frontShape, {
    depth: thickness,
    bevelEnabled: false,
    curveSegments: 16,
  });
  const frontWall = new THREE.Mesh(frontGeometry, mats.wallBody);
  frontWall.name = 'CurtainWallFront';
  frontWall.position.set(0, D.platformTop, inner);
  parent.add(frontWall);

  // outer arch ring around the courtyard gate
  const gateRing = archRingGeometry(2.0, 2.38, 1.42, 2.16, 2.36, 0.12);
  collectors.trim.push({ geometry: gateRing, matrix: mat4([0, D.platformTop, outer], [0, 0, 0], [1, 1, 1]) });
  collectors.trim.push({
    geometry: unitBox,
    matrix: mat4([0, D.platformTop + 2.22, outer + 0.02], [0, 0, 0], [2.6, 0.18, 0.2]),
  });

  // back wall with arrow slits
  const backShape = new THREE.Shape();
  backShape.moveTo(-outer, -0.05);
  backShape.lineTo(outer, -0.05);
  backShape.lineTo(outer, wallHeight);
  backShape.lineTo(-outer, wallHeight);
  backShape.closePath();
  [-4.2, -1.4, 1.4, 4.2].forEach((x) => {
    addSlitHole(backShape, x, 0.8, 1.75, 0.07);
  });
  const backGeometry = new THREE.ExtrudeGeometry(backShape, {
    depth: thickness,
    bevelEnabled: false,
    curveSegments: 16,
  });
  const backWall = new THREE.Mesh(backGeometry, mats.wallBody);
  backWall.name = 'CurtainWallBack';
  backWall.position.set(0, D.platformTop, -outer);
  parent.add(backWall);

  // side walls
  [-1, 1].forEach((side) => {
    const shape = new THREE.Shape();
    const halfLength = inner;
    shape.moveTo(-halfLength, -0.05);
    shape.lineTo(halfLength, -0.05);
    shape.lineTo(halfLength, wallHeight);
    shape.lineTo(-halfLength, wallHeight);
    shape.closePath();
    [-3.6, 0, 3.6].forEach((z) => {
      addSlitHole(shape, z, 0.8, 1.75, 0.07);
    });
    const geometry = new THREE.ExtrudeGeometry(shape, {
      depth: thickness,
      bevelEnabled: false,
      curveSegments: 16,
    });
    const mesh = new THREE.Mesh(geometry, mats.wallBody);
    mesh.name = side < 0 ? 'CurtainWallLeft' : 'CurtainWallRight';
    mesh.position.set(side * inner, D.platformTop, 0);
    mesh.rotation.y = side < 0 ? -Math.PI / 2 : Math.PI / 2;
    parent.add(mesh);
  });

  // crenellated coping
  crenellateX(collectors.trim, -outer, outer, outer - thickness / 2 + 0.02, wallTop, thickness + 0.06, [-2.4, 2.4]);
  crenellateX(collectors.trim, -outer, outer, -outer + thickness / 2, wallTop, thickness + 0.06, null);
  crenellateZ(collectors.trim, -outer + thickness, outer - thickness, -outer + thickness / 2, wallTop, thickness + 0.06, null);
  crenellateZ(collectors.trim, -outer + thickness, outer - thickness, outer - thickness / 2, wallTop, thickness + 0.06, null);

  // coping band under the merlons
  collectors.trim.push({ geometry: unitBox, matrix: mat4([0, wallTop - 0.08, outer - thickness / 2 + 0.02], [0, 0, 0], [outer * 2 + 0.16, 0.16, thickness + 0.18]) });
  collectors.trim.push({ geometry: unitBox, matrix: mat4([0, wallTop - 0.08, -outer + thickness / 2], [0, 0, 0], [outer * 2 + 0.16, 0.16, thickness + 0.18]) });
  collectors.trim.push({ geometry: unitBox, matrix: mat4([-outer + thickness / 2, wallTop - 0.08, 0], [0, 0, 0], [thickness + 0.18, 0.16, inner * 2]) });
  collectors.trim.push({ geometry: unitBox, matrix: mat4([outer - thickness / 2, wallTop - 0.08, 0], [0, 0, 0], [thickness + 0.18, 0.16, inner * 2]) });

  // gatehouse block above the gate
  const gatehouse = makeGroup(parent, 'Gatehouse', [0, wallTop, inner + 0.1]);
  const block = addMesh(gatehouse, new THREE.BoxGeometry(3.4, 1.5, 1.3), mats.wallBody, 'GatehouseBlock');
  block.position.set(0, 0.75, 0.1);
  const cap = addMesh(gatehouse, new THREE.BoxGeometry(3.6, 0.16, 1.46), mats.trim, 'GatehouseCap');
  cap.position.set(0, 1.56, 0.1);
  for (let index = 0; index < 4; index += 1) {
    const x = -1.32 + index * 0.88;
    collectors.trim.push({
      geometry: unitBox,
      matrix: mat4([x, 1.82, inner + 0.2], [0, 0, 0], [0.46, 0.5, 1.3]),
    });
  }
  [-1, 1].forEach((side) => {
    const turret = makeGroup(gatehouse, side < 0 ? 'GateTurretLeft' : 'GateTurretRight', [side * 1.85, 0, 0.72]);
    const shaft = addMesh(turret, new THREE.CylinderGeometry(0.52, 0.58, 2.3, 8), mats.wallTower, 'GateTurretShaft');
    shaft.position.y = 0.95;
    shaft.rotation.y = Math.PI / 8;
    const ring = addMesh(turret, new THREE.CylinderGeometry(0.62, 0.62, 0.16, 8), mats.trim, 'GateTurretRing');
    ring.position.y = 2.06;
    ring.rotation.y = Math.PI / 8;
    const spire = addMesh(turret, createSpireGeometry(0.62, 1.6, 8), mats.slateSpire, 'GateTurretSpire');
    spire.position.y = 2.12;
    spire.rotation.y = Math.PI / 8;
    collectors.iron.push({
      geometry: unitCone,
      matrix: mat4([side * 1.85, 3.86, inner + 0.2], [0, 0, 0], [0.07, 0.6, 0.07]),
    });
    addLancetWindow(turret, mats, collectors, {
      name: 'GateTurretWindow',
      position: [0, 1.0, 0.5],
      origin: [side * 1.85, wallTop, inner + 0.2],
      rotY: 0,
      width: 0.3,
      spring: 0.62,
      apex: 0.86,
    });
  });

  // corner turrets of the curtain wall
  const corners = [
    [-6.62, 6.62],
    [6.62, 6.62],
    [-6.62, -6.62],
    [6.62, -6.62],
  ];
  corners.forEach((corner, index) => {
    const turret = makeGroup(parent, 'WallCornerTurret' + index, [corner[0], 0, corner[1]]);
    const shaft = addMesh(turret, new THREE.CylinderGeometry(0.86, 1.0, 3.5, 12), mats.wallTower, 'WallTurretShaft');
    shaft.position.y = D.platformTop + 1.75;
    const skirt = addMesh(turret, new THREE.CylinderGeometry(1.06, 1.14, 0.5, 12), mats.plinth, 'WallTurretSkirt');
    skirt.position.y = D.platformTop + 0.25;
    const ring = addMesh(turret, new THREE.CylinderGeometry(1.02, 1.02, 0.2, 12), mats.trim, 'WallTurretRing');
    ring.position.y = D.platformTop + 3.4;
    const parapet = addMesh(turret, new THREE.CylinderGeometry(1.02, 0.98, 0.5, 12), mats.wallTower, 'WallTurretParapet');
    parapet.position.y = D.platformTop + 3.72;
    const spire = addMesh(turret, createSpireGeometry(1.0, 2.2, 12), mats.slateSpire, 'WallTurretSpire');
    spire.position.y = D.platformTop + 3.94;
    collectors.iron.push({
      geometry: unitCone,
      matrix: mat4([corner[0], D.platformTop + 6.3, corner[1]], [0, 0, 0], [0.07, 0.7, 0.07]),
    });
    addLancetWindow(turret, mats, collectors, {
      name: 'WallTurretWindow',
      position: [0, D.platformTop + 1.7, 0.94],
      origin: [corner[0], 0, corner[1]],
      rotY: 0,
      width: 0.32,
      spring: 0.7,
      apex: 0.96,
    });
  });
}

/* ------------------------------------------------------------------ */
/* lancet window                                                       */
/* ------------------------------------------------------------------ */

function addLancetWindow(parent, mats, collectors, options) {
  const origin = options.origin || [0, 0, 0];
  const basePosition = [
    options.position[0] + origin[0],
    options.position[1] + origin[1],
    options.position[2] + origin[2],
  ];
  const rotY = options.rotY || 0;
  const width = options.width;
  const spring = options.spring;
  const apex = options.apex;
  const base = mat4(basePosition, [0, rotY, 0], [1, 1, 1]);
  const local = (position, rotation, scale) => base.clone().multiply(mat4(position, rotation, scale));

  const ring = archRingGeometry(width, width + 0.3, spring, apex, apex + 0.16, 0.09);
  collectors.trim.push({ geometry: ring, matrix: local([0, 0, -0.01]) });

  const glass = archPlateGeometry(width - 0.08, 0.03, spring, apex - 0.04, 0.04);
  collectors.glass.push({ geometry: glass, matrix: local([0, 0, -0.3]) });

  collectors.trim.push({
    geometry: unitBox,
    matrix: local([0, (apex - 0.16) / 2, 0.02], null, [0.05, apex - 0.16, 0.05]),
  });

  const tracery = new THREE.TorusGeometry(0.085, 0.016, 6, 16);
  collectors.trim.push({ geometry: tracery, matrix: local([0, apex - 0.42, 0.03]) });

  collectors.trim.push({
    geometry: unitBox,
    matrix: local([0, -0.05, 0.03], null, [width + 0.34, 0.1, 0.2]),
  });
}

/* ------------------------------------------------------------------ */
/* keep shell                                                          */
/* ------------------------------------------------------------------ */

function buildKeepShell(parent, mats, collectors) {
  const halfX = D.keepHalfX;
  const wallTopLocal = D.keepWallTop - D.platformTop;
  const gableLocal = D.gableApex - D.platformTop;
  const wallDepth = D.wallThickness;

  // front facade: gate, rose window, gable oculus
  const front = new THREE.Shape();
  front.moveTo(-halfX, -0.05);
  front.lineTo(halfX, -0.05);
  front.lineTo(halfX, wallTopLocal);
  front.lineTo(0, gableLocal);
  front.lineTo(-halfX, wallTopLocal);
  front.closePath();
  front.holes.push(pointedArchPath({ width: 1.9, base: 0, spring: 1.72, apex: 2.97 }));
  const roseHole = new THREE.Path();
  roseHole.absarc(0, 5.82, 1.12, 0, TAU, false);
  front.holes.push(roseHole);
  const oculusHole = new THREE.Path();
  oculusHole.absarc(0, 8.52, 0.4, 0, TAU, false);
  front.holes.push(oculusHole);
  const frontGeometry = new THREE.ExtrudeGeometry(front, {
    depth: wallDepth,
    bevelEnabled: false,
    curveSegments: 24,
  });
  const frontMesh = new THREE.Mesh(frontGeometry, mats.wallBody);
  frontMesh.name = 'KeepFrontWall';
  frontMesh.position.set(0, D.platformTop, D.keepZ1 - wallDepth);
  parent.add(frontMesh);

  // back facade with gable and three lancets
  const back = new THREE.Shape();
  back.moveTo(-halfX, -0.05);
  back.lineTo(halfX, -0.05);
  back.lineTo(halfX, wallTopLocal);
  back.lineTo(0, gableLocal);
  back.lineTo(-halfX, wallTopLocal);
  back.closePath();
  back.holes.push(pointedArchPath({ width: 1.0, base: 1.15, spring: 2.7, apex: 3.48 }));
  [-1.75, 1.75].forEach((x) => {
    back.holes.push(pointedArchPath({ width: 0.62, base: 1.15, spring: 2.55, apex: 3.2, x }));
  });
  back.holes.push(pointedArchPath({ width: 0.44, base: 7.95, spring: 8.7, apex: 9.35 }));
  const backGeometry = new THREE.ExtrudeGeometry(back, {
    depth: wallDepth,
    bevelEnabled: false,
    curveSegments: 20,
  });
  const backMesh = new THREE.Mesh(backGeometry, mats.wallBody);
  backMesh.name = 'KeepBackWall';
  backMesh.position.set(0, D.platformTop, D.keepZ0);
  parent.add(backMesh);

  // side walls with two lancets each
  [-1, 1].forEach((side) => {
    const length = 3.3;
    const shape = new THREE.Shape();
    shape.moveTo(-length, -0.05);
    shape.lineTo(length, -0.05);
    shape.lineTo(length, wallTopLocal);
    shape.lineTo(-length, wallTopLocal);
    shape.closePath();
    [1.44, -1.44].forEach((localX) => {
      shape.holes.push(pointedArchPath({ width: 0.72, base: 1.15, spring: 2.6, apex: 3.4, x: localX }));
    });
    const geometry = new THREE.ExtrudeGeometry(shape, {
      depth: wallDepth,
      bevelEnabled: false,
      curveSegments: 18,
    });
    const mesh = new THREE.Mesh(geometry, mats.wallBody);
    mesh.name = side < 0 ? 'KeepLeftWall' : 'KeepRightWall';
    mesh.position.set(side * D.innerHalfX, D.platformTop, -2.6);
    mesh.rotation.y = side < 0 ? -Math.PI / 2 : Math.PI / 2;
    parent.add(mesh);
  });

  // base skirt of the keep
  const skirtY = D.platformTop;
  collectors.trim.push({ geometry: unitBox, matrix: mat4([0, skirtY + 0.32, D.keepZ1 + 0.02], [0, 0, 0], [7.9, 0.64, 0.26]) });
  collectors.trim.push({ geometry: unitBox, matrix: mat4([0, skirtY + 0.32, D.keepZ0 - 0.02], [0, 0, 0], [7.9, 0.64, 0.26]) });
  collectors.trim.push({ geometry: unitBox, matrix: mat4([-D.keepHalfX - 0.02, skirtY + 0.32, -2.6], [0, 0, 0], [0.26, 0.64, 7.2]) });
  collectors.trim.push({ geometry: unitBox, matrix: mat4([D.keepHalfX + 0.02, skirtY + 0.32, -2.6], [0, 0, 0], [0.26, 0.64, 7.2]) });

  // string course above the skirt
  collectors.trim.push({ geometry: unitBox, matrix: mat4([0, skirtY + 0.72, D.keepZ1 + 0.05], [0, 0, 0], [7.86, 0.14, 0.34]) });
  collectors.trim.push({ geometry: unitBox, matrix: mat4([0, skirtY + 0.72, D.keepZ0 - 0.05], [0, 0, 0], [7.86, 0.14, 0.34]) });
  collectors.trim.push({ geometry: unitBox, matrix: mat4([-D.keepHalfX - 0.05, skirtY + 0.72, -2.6], [0, 0, 0], [0.34, 0.14, 7.2]) });
  collectors.trim.push({ geometry: unitBox, matrix: mat4([D.keepHalfX + 0.05, skirtY + 0.72, -2.6], [0, 0, 0], [0.34, 0.14, 7.2]) });

  // corner pilasters
  [[-1, -1], [1, -1], [-1, 1], [1, 1]].forEach((corner) => {
    const x = corner[0] * (D.keepHalfX - 0.26);
    const z = corner[1] > 0 ? D.keepZ1 - 0.26 : D.keepZ0 + 0.26;
    collectors.trim.push({
      geometry: unitBox,
      matrix: mat4([x, D.platformTop + 3.8, z], [0, 0, 0], [0.62, 7.6, 0.62]),
    });
    collectors.trim.push({
      geometry: unitBox,
      matrix: mat4([x, D.platformTop + 7.7, z], [0, 0, 0], [0.74, 0.24, 0.74]),
    });
  });

  // cornice and corbel table
  const corniceY = D.keepWallTop - 0.22;
  collectors.trim.push({ geometry: unitBox, matrix: mat4([0, corniceY, D.keepZ1 + 0.12], [0, 0, 0], [8.0, 0.22, 0.42]) });
  collectors.trim.push({ geometry: unitBox, matrix: mat4([0, corniceY, D.keepZ0 - 0.12], [0, 0, 0], [8.0, 0.22, 0.42]) });
  collectors.trim.push({ geometry: unitBox, matrix: mat4([-D.keepHalfX - 0.12, corniceY, -2.6], [0, 0, 0], [0.42, 0.22, 7.4]) });
  collectors.trim.push({ geometry: unitBox, matrix: mat4([D.keepHalfX + 0.12, corniceY, -2.6], [0, 0, 0], [0.42, 0.22, 7.4]) });

  for (let x = -3.4; x <= 3.4; x += 0.62) {
    collectors.trim.push({ geometry: unitBox, matrix: mat4([x, corniceY - 0.2, D.keepZ1 + 0.18], [0, 0, 0], [0.22, 0.34, 0.34]) });
    collectors.trim.push({ geometry: unitBox, matrix: mat4([x, corniceY - 0.2, D.keepZ0 - 0.18], [0, 0, 0], [0.22, 0.34, 0.34]) });
  }
  for (let z = -5.8; z <= 0.6; z += 0.62) {
    collectors.trim.push({ geometry: unitBox, matrix: mat4([-D.keepHalfX - 0.18, corniceY - 0.2, z], [0, 0, 0], [0.34, 0.34, 0.22]) });
    collectors.trim.push({ geometry: unitBox, matrix: mat4([D.keepHalfX + 0.18, corniceY - 0.2, z], [0, 0, 0], [0.34, 0.34, 0.22]) });
  }

  // blind arcade relief beside the gate
  [-1, 1].forEach((side) => {
    const centerX = side * 2.46;
    const z = D.keepZ1;
    const width = 0.78;
    const spring = 1.15;
    const apex = 1.86;
    const plate = archPlateGeometry(width, 0.5, spring, apex, 0.05);
    collectors.dark.push({ geometry: plate, matrix: mat4([centerX, D.platformTop, z + 0.02], [0, 0, 0], [1, 1, 1]) });
    const frame = archRingGeometry(width, width + 0.22, spring, apex, apex + 0.12, 0.07);
    collectors.trim.push({ geometry: frame, matrix: mat4([centerX, D.platformTop, z + 0.01], [0, 0, 0], [1, 1, 1]) });
    const medallion = new THREE.TorusGeometry(0.2, 0.035, 6, 18);
    collectors.trim.push({ geometry: medallion, matrix: mat4([centerX, D.platformTop + 2.62, z + 0.05], [0, 0, 0], [1, 1, 1]) });
    const medallionCore = new THREE.CircleGeometry(0.15, 16);
    collectors.dark.push({ geometry: medallionCore, matrix: mat4([centerX, D.platformTop + 2.62, z + 0.045], [0, 0, 0], [1, 1, 1]) });
  });

  // side wall pilasters where the flying buttresses land
  [-1, 1].forEach((side) => {
    collectors.trim.push({
      geometry: unitBox,
      matrix: mat4([side * (D.keepHalfX + 0.11), D.platformTop + 3.9, -2.6], [0, 0, 0], [0.3, 7.2, 0.5]),
    });
    collectors.trim.push({
      geometry: unitBox,
      matrix: mat4([side * (D.keepHalfX + 0.14), D.platformTop + 7.1, -2.6], [0, 0, 0], [0.34, 0.4, 0.6]),
    });
  });
}

/* ------------------------------------------------------------------ */
/* gate details                                                        */
/* ------------------------------------------------------------------ */

function buildGate(parent, mats, collectors) {
  const z = D.keepZ1;
  const baseY = D.platformTop;
  const bands = [0, 1, 2];
  bands.forEach((band) => {
    const innerWidth = 1.9 + 0.36 * band;
    const innerApex = 2.97 + 0.18 * band;
    const ring = archRingGeometry(
      innerWidth,
      innerWidth + 0.36,
      1.72,
      innerApex,
      innerApex + 0.18,
      0.1 + band * 0.05,
    );
    collectors.trim.push({ geometry: ring, matrix: mat4([0, baseY, z], [0, 0, 0], [1, 1, 1]) });
  });

  // pointed hood above the outer archivolt
  const hood = new THREE.TorusGeometry(0.16, 0.03, 6, 16);
  collectors.trim.push({ geometry: hood, matrix: mat4([0, baseY + 3.5, z + 0.05], [0, 0, 0], [1, 1, 1]) });

  // open timber door leaves resting against the inner wall
  [-1, 1].forEach((side) => {
    const hinge = makeGroup(parent, side < 0 ? 'DoorLeafLeft' : 'DoorLeafRight', [
      side * 0.95,
      baseY,
      z - D.wallThickness + 0.08,
    ]);
    hinge.rotation.y = side < 0 ? (112 * Math.PI) / 180 : (-112 * Math.PI) / 180;
    const leaf = addMesh(
      hinge,
      new THREE.BoxGeometry(0.9, 2.55, 0.08),
      mats.wood,
      'DoorLeafPanel',
    );
    leaf.position.set(side < 0 ? 0.45 : -0.45, 1.28, 0);
    for (let index = 0; index < 3; index += 1) {
      const strap = addMesh(
        hinge,
        new THREE.BoxGeometry(0.82, 0.09, 0.03),
        mats.iron,
        'DoorStrap' + index,
      );
      strap.position.set(side < 0 ? 0.45 : -0.45, 0.45 + index * 0.85, side < 0 ? 0.05 : -0.05);
      const boss = addMesh(
        hinge,
        new THREE.SphereGeometry(0.045, 10, 8),
        mats.iron,
        'DoorBoss' + index,
      );
      boss.position.set(side < 0 ? 0.8 : -0.8, 0.45 + index * 0.85, side < 0 ? 0.06 : -0.06);
    }
    const ring = addMesh(hinge, new THREE.TorusGeometry(0.09, 0.02, 6, 14), mats.iron, 'DoorRing');
    ring.position.set(side < 0 ? 0.14 : -0.14, 1.15, side < 0 ? 0.07 : -0.07);
  });

  // threshold slab
  collectors.trim.push({
    geometry: unitBox,
    matrix: mat4([0, D.platformTop + 0.02, z - D.wallThickness / 2], [0, 0, 0], [1.92, 0.06, 0.78]),
  });
}

/* ------------------------------------------------------------------ */
/* rose window                                                         */
/* ------------------------------------------------------------------ */

function buildRoseWindow(parent, mats, collectors) {
  const centerY = D.platformTop + 5.82;
  const z = D.keepZ1;

  const outerRing = new THREE.TorusGeometry(1.12, 0.085, 8, 40);
  collectors.trim.push({ geometry: outerRing, matrix: mat4([0, centerY, z + 0.03], [0, 0, 0], [1, 1, 1]) });
  const innerRing = new THREE.TorusGeometry(0.52, 0.05, 6, 28);
  collectors.trim.push({ geometry: innerRing, matrix: mat4([0, centerY, z + 0.04], [0, 0, 0], [1, 1, 1]) });

  for (let index = 0; index < 12; index += 1) {
    const angle = (index / 12) * TAU;
    collectors.trim.push({
      geometry: unitBox,
      matrix: mat4([0, centerY, z + 0.03], [0, 0, angle], [0.07, 2.2, 0.1]),
    });
    const petal = new THREE.TorusGeometry(0.16, 0.026, 6, 16);
    collectors.trim.push({
      geometry: petal,
      matrix: mat4([
        Math.cos(angle) * 0.82,
        centerY + Math.sin(angle) * 0.82,
        z + 0.05,
      ], [0, 0, 0], [1, 1, 1]),
    });
  }

  const glass = new THREE.CircleGeometry(1.1, 40);
  collectors.glass.push({ geometry: glass, matrix: mat4([0, centerY, z - 0.34], [0, 0, 0], [1, 1, 1]) });
  collectors.glass.push({ geometry: glass, matrix: mat4([0, centerY, z - 0.4], [0, Math.PI, 0], [1, 1, 1]) });

  // square frame around the rose
  collectors.trim.push({ geometry: unitBox, matrix: mat4([0, centerY + 1.5, z + 0.02], [0, 0, 0], [3.24, 0.16, 0.16]) });
  collectors.trim.push({ geometry: unitBox, matrix: mat4([0, centerY - 1.5, z + 0.02], [0, 0, 0], [3.24, 0.16, 0.16]) });
  collectors.trim.push({ geometry: unitBox, matrix: mat4([-1.54, centerY, z + 0.02], [0, 0, 0], [0.16, 3.16, 0.16]) });
  collectors.trim.push({ geometry: unitBox, matrix: mat4([1.54, centerY, z + 0.02], [0, 0, 0], [0.16, 3.16, 0.16]) });
}

/* ------------------------------------------------------------------ */
/* keep windows                                                        */
/* ------------------------------------------------------------------ */

function buildKeepWindows(parent, mats, collectors) {
  const springY = D.platformTop;
  // side walls
  [-1, 1].forEach((side) => {
    [1.44, -1.44].forEach((localX) => {
      addLancetWindow(parent, mats, collectors, {
        name: 'KeepSideWindow',
        position: [side * D.keepHalfX, springY, -2.6 + localX],
        rotY: side < 0 ? -Math.PI / 2 : Math.PI / 2,
        width: 0.72,
        spring: 2.6,
        apex: 3.4,
      });
    });
  });

  // back wall
  addLancetWindow(parent, mats, collectors, {
    name: 'KeepBackWindowCenter',
    position: [0, springY, D.keepZ0],
    rotY: Math.PI,
    width: 1.0,
    spring: 2.7,
    apex: 3.48,
  });
  [-1.75, 1.75].forEach((x) => {
    addLancetWindow(parent, mats, collectors, {
      name: 'KeepBackWindowSide',
      position: [x, springY, D.keepZ0],
      rotY: Math.PI,
      width: 0.62,
      spring: 2.55,
      apex: 3.2,
    });
  });
  addLancetWindow(parent, mats, collectors, {
    name: 'KeepGableWindow',
    position: [0, springY, D.keepZ0],
    rotY: Math.PI,
    width: 0.44,
    spring: 8.7,
    apex: 9.35,
  });
}

/* ------------------------------------------------------------------ */
/* flying buttresses                                                   */
/* ------------------------------------------------------------------ */

function buildButtresses(parent, mats, collectors) {
  [-1, 1].forEach((side) => {
    const group = makeGroup(parent, side < 0 ? 'ButtressLeft' : 'ButtressRight', [side * 5.05, D.platformTop, -2.6]);

    const tier1 = addMesh(group, new THREE.BoxGeometry(0.9, 1.5, 1.0), mats.wallBody, 'ButtressTier1');
    tier1.position.y = 0.75;
    const tier2 = addMesh(group, new THREE.BoxGeometry(0.72, 1.7, 0.82), mats.wallBody, 'ButtressTier2');
    tier2.position.y = 2.35;
    const tier3 = addMesh(group, new THREE.BoxGeometry(0.56, 2.2, 0.66), mats.wallBody, 'ButtressTier3');
    tier3.position.y = 4.3;
    const cap = addMesh(group, new THREE.BoxGeometry(0.7, 0.16, 0.8), mats.trim, 'ButtressCap');
    cap.position.y = 5.46;

    const band = curvedBandShape(
      { x: -side * 0.1, y: 5.4 },
      { x: -side * 1.35, y: 7.05 },
      { x: -side * 0.45, y: 6.9 },
      0.17,
      18,
    );
    const bandGeometry = new THREE.ExtrudeGeometry(band, {
      depth: 0.42,
      bevelEnabled: false,
      curveSegments: 2,
    });
    bandGeometry.translate(0, 0, -0.21);
    const bandMesh = new THREE.Mesh(bandGeometry, mats.wallBody);
    bandMesh.name = 'ButtressArch';
    group.add(bandMesh);

    // vertical spur that carries the arch into the wall
    collectors.trim.push({
      geometry: unitBox,
      matrix: mat4([side * 3.72, D.platformTop + 6.45, -2.6], [0, 0, 0], [0.24, 0.9, 0.5]),
    });

    // pinnacle on the pier
    const pinnacleShaft = addMesh(group, new THREE.CylinderGeometry(0.2, 0.26, 1.2, 8), mats.trim, 'ButtressPinnacle');
    pinnacleShaft.position.y = 6.14;
    const pinnacleSpire = addMesh(group, createSpireGeometry(0.3, 1.0, 8), mats.slateSpire, 'ButtressPinnacleSpire');
    pinnacleSpire.position.y = 6.72;
  });
}

/* ------------------------------------------------------------------ */
/* steep roof                                                          */
/* ------------------------------------------------------------------ */

function buildRoof(parent, mats, collectors) {
  const eaveY = D.keepWallTop - 0.05;
  const halfSpan = 4.05;
  const rise = D.gableApex - eaveY;
  const angle = Math.atan2(rise, halfSpan);
  const slopeLength = Math.hypot(halfSpan, rise);
  const roofDepth = 6.0;

  [-1, 1].forEach((side) => {
    const slab = addMesh(
      parent,
      new THREE.BoxGeometry(slopeLength, 0.22, roofDepth),
      mats.slate,
      side < 0 ? 'RoofSlopeLeft' : 'RoofSlopeRight',
    );
    slab.position.set(side * (halfSpan / 2), (eaveY + D.gableApex) / 2, -2.55);
    slab.rotation.z = side < 0 ? angle : Math.PI - angle;
  });

  const ridge = addMesh(parent, new THREE.BoxGeometry(0.3, 0.26, roofDepth + 0.1), mats.slate, 'RoofRidgeCap');
  ridge.position.set(0, D.gableApex + 0.02, -2.55);

  // iron cresting along the ridge
  for (let z = -5.3; z <= 0.2; z += 0.44) {
    collectors.iron.push({
      geometry: unitCone,
      matrix: mat4([0, D.gableApex + 0.28, z], [0, 0, 0], [0.07, 0.4, 0.07]),
    });
    collectors.iron.push({
      geometry: unitBox,
      matrix: mat4([0, D.gableApex + 0.1, z], [0, 0, 0], [0.02, 0.2, 0.02]),
    });
  }

  // rake mouldings and crockets on both gables
  [-1, 1].forEach((side) => {
    const zFace = side > 0 ? D.keepZ1 + 0.04 : D.keepZ0 - 0.04;
    [-1, 1].forEach((run) => {
      const startX = run * D.keepHalfX;
      const startY = D.keepWallTop;
      const endX = 0;
      const endY = D.gableApex;
      const dx = endX - startX;
      const dy = endY - startY;
      const length = Math.hypot(dx, dy);
      const rakeAngle = Math.atan2(dy, dx);
      collectors.trim.push({
        geometry: unitBox,
        matrix: mat4(
          [startX + dx / 2, startY + dy / 2, zFace],
          [0, 0, rakeAngle],
          [length, 0.22, 0.2],
        ),
      });
      const count = 8;
      for (let index = 1; index < count; index += 1) {
        const t = index / count;
        const crocket = new THREE.ConeGeometry(0.11, 0.34, 8);
        collectors.trim.push({
          geometry: crocket,
          matrix: mat4(
            [startX + dx * t, startY + dy * t + 0.14, zFace + side * 0.02],
            [0, 0, 0],
            [1, 1, 1],
          ),
        });
      }
    });

    // gable finial
    const finial = makeGroup(parent, side > 0 ? 'FrontFinial' : 'BackFinial', [0, D.gableApex + 0.06, zFace]);
    const stem = addMesh(finial, new THREE.CylinderGeometry(0.1, 0.16, 0.5, 8), mats.trim, 'FinialStem');
    stem.position.y = 0.25;
    const ball = addMesh(finial, new THREE.SphereGeometry(0.15, 12, 10), mats.trim, 'FinialBall');
    ball.position.y = 0.58;
    const spike = addMesh(finial, new THREE.ConeGeometry(0.06, 0.55, 8), mats.iron, 'FinialSpike');
    spike.position.y = 1.0;
  });
}

/* ------------------------------------------------------------------ */
/* towers                                                              */
/* ------------------------------------------------------------------ */

function createSpireGeometry(radius, height, sides) {
  const profile = [
    [1.06, 0],
    [0.94, 0.12],
    [0.78, 0.3],
    [0.6, 0.5],
    [0.43, 0.68],
    [0.28, 0.83],
    [0.16, 0.93],
    [0.06, 0.985],
    [0, 1],
  ].map((entry) => new THREE.Vector2(entry[0] * radius, entry[1] * height));
  return new THREE.LatheGeometry(profile, sides);
}

function buildTower(parent, mats, collectors, options) {
  const group = makeGroup(parent, options.name, [options.x, 0, options.z]);
  const sides = options.sides;
  const radius = options.radius;
  const bodyTop = options.bodyTop;
  const faceTurn = Math.PI / sides;

  const shaft = addMesh(
    group,
    new THREE.CylinderGeometry(radius * 0.93, radius, bodyTop - D.platformTop, sides, 3),
    mats.wallTower,
    'TowerShaft',
  );
  shaft.position.y = (D.platformTop + bodyTop) / 2;
  shaft.rotation.y = faceTurn;

  const skirt = addMesh(group, new THREE.CylinderGeometry(radius * 1.12, radius * 1.2, 0.55, sides), mats.plinth, 'TowerSkirt');
  skirt.position.y = D.platformTop + 0.27;
  skirt.rotation.y = faceTurn;

  [3.1, 5.6].forEach((heightOffset, index) => {
    const ring = addMesh(group, new THREE.CylinderGeometry(radius * 1.05, radius * 1.05, 0.18, sides), mats.trim, 'TowerCourse' + index);
    ring.position.y = D.platformTop + heightOffset;
    ring.rotation.y = faceTurn;
  });

  const corbel = addMesh(group, new THREE.CylinderGeometry(radius * 1.3, radius * 1.0, 0.7, sides), mats.wallTower, 'TowerCorbel');
  corbel.position.y = bodyTop - 0.34;
  corbel.rotation.y = faceTurn;

  const parapet = addMesh(group, new THREE.CylinderGeometry(radius * 1.26, radius * 1.26, 0.5, sides), mats.wallTower, 'TowerParapet');
  parapet.position.y = bodyTop + 0.22;
  parapet.rotation.y = faceTurn;

  const spire = addMesh(group, createSpireGeometry(radius * 1.08, options.spireHeight, sides), mats.slateSpire, 'TowerSpire');
  spire.position.y = bodyTop + 0.42;
  spire.rotation.y = faceTurn;

  const apex = addMesh(group, new THREE.ConeGeometry(0.06, 1.1, 8), mats.iron, 'TowerApexSpike');
  apex.position.y = bodyTop + 0.42 + options.spireHeight + 0.4;

  // pinnacles around the spire base
  for (let index = 0; index < sides; index += 1) {
    const angle = faceTurn + (index / sides) * TAU;
    const px = Math.sin(angle) * radius * 1.16;
    const pz = Math.cos(angle) * radius * 1.16;
    const shaftSmall = addMesh(group, new THREE.CylinderGeometry(0.1, 0.14, 0.7, 8), mats.trim, 'PinnacleShaft' + index);
    shaftSmall.position.set(px, bodyTop + 0.72, pz);
    const capSmall = addMesh(
      group,
      new THREE.ConeGeometry(0.17, 0.85, 8),
      mats.trim,
      'PinnacleCone' + index,
    );
    capSmall.position.set(px, bodyTop + 1.5, pz);
  }

  // lancet windows on selected faces
  const apothemAt = (worldY) => {
    const span = bodyTop - D.platformTop;
    const t = Math.min(1, Math.max(0, (worldY - D.platformTop) / span));
    const localRadius = radius * (1 - 0.07 * t);
    return localRadius * Math.cos(Math.PI / sides) * 0.99;
  };

  (options.windowAngles || []).forEach((angleDegrees, index) => {
    const angle = (angleDegrees * Math.PI) / 180;
    const sill = D.platformTop + (options.windowBase || 3.6);
    const apothem = apothemAt(sill);
    addLancetWindow(group, mats, collectors, {
      name: 'TowerWindow' + index,
      position: [Math.sin(angle) * apothem, sill, Math.cos(angle) * apothem],
      origin: [options.x, 0, options.z],
      rotY: angle,
      width: 0.44,
      spring: 0.95,
      apex: 1.36,
    });
  });

  if (options.extraWindowBase) {
    const sill = D.platformTop + options.extraWindowBase;
    const apothem = apothemAt(sill);
    addLancetWindow(group, mats, collectors, {
      name: 'TowerUpperWindow',
      position: [0, sill, apothem],
      origin: [options.x, 0, options.z],
      rotY: 0,
      width: 0.36,
      spring: 0.7,
      apex: 1.02,
    });
  }

  return group;
}

function buildTowers(parent, mats, collectors) {
  buildTower(parent, mats, collectors, {
    name: 'TowerFrontLeft',
    x: -4.45,
    z: 0.55,
    radius: 1.62,
    sides: 8,
    bodyTop: 10.3,
    spireHeight: 5.2,
    windowAngles: [-45, 0, 45],
    windowBase: 3.5,
    extraWindowBase: 6.3,
  });
  buildTower(parent, mats, collectors, {
    name: 'TowerFrontRight',
    x: 4.45,
    z: 0.55,
    radius: 1.62,
    sides: 8,
    bodyTop: 10.3,
    spireHeight: 5.2,
    windowAngles: [-45, 0, 45],
    windowBase: 3.5,
    extraWindowBase: 6.3,
  });
  buildTower(parent, mats, collectors, {
    name: 'TowerBackLeft',
    x: -4.05,
    z: -5.65,
    radius: 1.34,
    sides: 20,
    bodyTop: 9.15,
    spireHeight: 4.4,
    windowAngles: [171, 189, 207, 225],
    windowBase: 3.2,
  });
  buildTower(parent, mats, collectors, {
    name: 'TowerBackRight',
    x: 4.05,
    z: -5.65,
    radius: 1.34,
    sides: 20,
    bodyTop: 9.15,
    spireHeight: 4.4,
    windowAngles: [99, 117, 135, 153],
    windowBase: 3.2,
  });
}

/* ------------------------------------------------------------------ */
/* gargoyles                                                           */
/* ------------------------------------------------------------------ */

function createGargoyleGeometry() {
  const pieces = [];
  const push = (geometry, position, rotation, scale) => {
    pieces.push({ geometry, matrix: mat4(position, rotation, scale) });
  };
  push(new THREE.CylinderGeometry(0.13, 0.19, 0.42, 10), [0, 0, 0.19], [Math.PI / 2, 0, 0], [1, 1, 1]);
  push(new THREE.SphereGeometry(0.17, 12, 10), [0, 0.02, 0.47], [0, 0, 0], [0.95, 0.9, 1.2]);
  push(new THREE.ConeGeometry(0.09, 0.26, 8), [0, -0.02, 0.65], [Math.PI / 2, 0, 0], [1, 1, 1]);
  push(new THREE.ConeGeometry(0.045, 0.18, 6), [-0.09, 0.14, 0.44], [-0.4, 0, 0.3], [1, 1, 1]);
  push(new THREE.ConeGeometry(0.045, 0.18, 6), [0.09, 0.14, 0.44], [-0.4, 0, -0.3], [1, 1, 1]);
  push(new THREE.BoxGeometry(0.04, 0.22, 0.16), [-0.16, 0.02, 0.3], [0, 0, 0.3], [1, 1, 1]);
  push(new THREE.BoxGeometry(0.04, 0.22, 0.16), [0.16, 0.02, 0.3], [0, 0, -0.3], [1, 1, 1]);
  push(new THREE.ConeGeometry(0.05, 0.4, 6), [0, -0.12, 0.02], [-1.9, 0, 0], [1, 1, 1]);
  push(new THREE.BoxGeometry(0.09, 0.16, 0.09), [-0.08, -0.18, 0.34], [0, 0, 0], [1, 1, 1]);
  push(new THREE.BoxGeometry(0.09, 0.16, 0.09), [0.08, -0.18, 0.34], [0, 0, 0], [1, 1, 1]);
  return mergePieces(pieces);
}

function buildGargoyles(parent, mats) {
  const geometry = createGargoyleGeometry();
  const spots = [
    { position: [-2.9, D.keepWallTop - 0.42, D.keepZ1 + 0.2], rotY: 0 },
    { position: [2.9, D.keepWallTop - 0.42, D.keepZ1 + 0.2], rotY: 0 },
    { position: [-D.keepHalfX - 0.2, D.keepWallTop - 0.42, -0.6], rotY: -Math.PI / 2 },
    { position: [D.keepHalfX + 0.2, D.keepWallTop - 0.42, -0.6], rotY: Math.PI / 2 },
    { position: [-D.keepHalfX - 0.2, D.keepWallTop - 0.42, -4.6], rotY: -Math.PI / 2 },
    { position: [D.keepHalfX + 0.2, D.keepWallTop - 0.42, -4.6], rotY: Math.PI / 2 },
  ];
  spots.forEach((spot, index) => {
    const mesh = new THREE.Mesh(geometry, mats.trim);
    mesh.name = 'Gargoyle' + index;
    mesh.position.set(spot.position[0], spot.position[1], spot.position[2]);
    mesh.rotation.y = spot.rotY;
    parent.add(mesh);
  });
}

/* ------------------------------------------------------------------ */
/* banners                                                             */
/* ------------------------------------------------------------------ */

function createClothGeometry(width, height, notch, thickness, folds) {
  const cols = 12;
  const rows = 18;
  const surface = (u, v) => {
    const x = (u - 0.5) * width;
    const edgeLift = Math.pow(v, 4) * notch * (1 - Math.abs(2 * u - 1)) * 0.6;
    const y = (0.5 - v) * height + edgeLift;
    const z = Math.sin(u * Math.PI * 2 + v * 0.9) * folds * (0.35 + 0.65 * v);
    return [x, y, z];
  };

  const positions = [];
  const uvs = [];
  const index = [];
  const step = cols + 1;

  const gridIndex = (i, j) => j * step + i;

  for (let j = 0; j <= rows; j += 1) {
    for (let i = 0; i <= cols; i += 1) {
      const u = i / cols;
      const v = j / rows;
      const point = surface(u, v);
      positions.push(point[0], point[1], point[2] + thickness / 2);
      uvs.push(u, 1 - v);
    }
  }
  for (let j = 0; j <= rows; j += 1) {
    for (let i = 0; i <= cols; i += 1) {
      const u = i / cols;
      const v = j / rows;
      const point = surface(u, v);
      positions.push(point[0], point[1], point[2] - thickness / 2);
      uvs.push(u, 1 - v);
    }
  }

  const backOffset = (rows + 1) * (cols + 1);
  for (let j = 0; j < rows; j += 1) {
    for (let i = 0; i < cols; i += 1) {
      const a = gridIndex(i, j);
      const b = gridIndex(i + 1, j);
      const c = gridIndex(i + 1, j + 1);
      const d = gridIndex(i, j + 1);
      index.push(a, d, c, a, c, b);
      index.push(backOffset + a, backOffset + b, backOffset + c, backOffset + a, backOffset + c, backOffset + d);
    }
  }

  // rim strips, closing the cloth shell
  const rim = (a, b) => {
    const c = backOffset + b;
    const d = backOffset + a;
    index.push(a, b, d, b, c, d);
  };
  for (let i = 0; i < cols; i += 1) {
    rim(gridIndex(i, 0), gridIndex(i + 1, 0));
    rim(gridIndex(i + 1, rows), gridIndex(i, rows));
  }
  for (let j = 0; j < rows; j += 1) {
    rim(gridIndex(cols, j), gridIndex(cols, j + 1));
    rim(gridIndex(0, j + 1), gridIndex(0, j));
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
  geometry.setIndex(index);
  geometry.computeVertexNormals();
  geometry.computeBoundingSphere();
  return geometry;
}

function buildBanners(parent, mats) {
  const defs = [
    { name: 'BannerKeepLeft', position: [-2.55, D.keepWallTop - 0.35, D.keepZ1 + 0.22], width: 0.66, height: 2.4 },
    { name: 'BannerKeepRight', position: [2.55, D.keepWallTop - 0.35, D.keepZ1 + 0.22], width: 0.66, height: 2.4 },
    { name: 'BannerGateLeft', position: [-1.02, 4.55, 7.96], width: 0.46, height: 1.55 },
    { name: 'BannerGateRight', position: [1.02, 4.55, 7.96], width: 0.46, height: 1.55 },
  ];

  defs.forEach((definition) => {
    const anchor = makeGroup(parent, definition.name, definition.position);
    const bar = addMesh(
      anchor,
      new THREE.CylinderGeometry(0.032, 0.032, definition.width + 0.55, 8),
      mats.iron,
      definition.name + 'Bar',
    );
    bar.rotation.z = Math.PI / 2;

    const swing = makeGroup(anchor, 'Swing');
    const cloth = addMesh(
      swing,
      createClothGeometry(definition.width, definition.height, 0.24, 0.022, definition.width * 0.09),
      mats.cloth,
      definition.name + 'Cloth',
    );
    cloth.position.y = -definition.height / 2 - 0.05;

    const finialLeft = addMesh(anchor, new THREE.ConeGeometry(0.05, 0.18, 8), mats.iron, definition.name + 'BarTipLeft');
    finialLeft.position.set(-(definition.width + 0.55) / 2, 0, 0);
    finialLeft.rotation.z = Math.PI / 2;
    const finialRight = addMesh(anchor, new THREE.ConeGeometry(0.05, 0.18, 8), mats.iron, definition.name + 'BarTipRight');
    finialRight.position.set((definition.width + 0.55) / 2, 0, 0);
    finialRight.rotation.z = -Math.PI / 2;
  });
}

/* ------------------------------------------------------------------ */
/* interior                                                            */
/* ------------------------------------------------------------------ */

function buildInterior(parent, mats, collectors) {
  const floor = addMesh(
    parent,
    new THREE.BoxGeometry(5.94, 0.06, 5.54),
    mats.paving,
    'HallFloor',
  );
  floor.position.set(0, D.floorTop - 0.03, -2.6);

  const inlay = addMesh(parent, new THREE.CircleGeometry(1.9, 48), mats.inlay, 'HallInlay');
  inlay.position.set(0, D.floorTop + 0.004, -2.6);
  inlay.rotation.x = -Math.PI / 2;

  // clustered columns
  const columnPositions = [
    [-2.52, -1.15],
    [2.52, -1.15],
    [-2.52, -4.15],
    [2.52, -4.15],
  ];
  columnPositions.forEach((position, index) => {
    const column = makeGroup(parent, 'HallColumn' + index, [position[0], D.floorTop, position[1]]);
    const base = addMesh(column, new THREE.CylinderGeometry(0.36, 0.42, 0.3, 8), mats.trim, 'ColumnBase');
    base.position.y = 0.15;
    const shaft = addMesh(column, new THREE.CylinderGeometry(0.25, 0.29, 3.5, 12), mats.interiorStone, 'ColumnShaft');
    shaft.position.y = 2.05;
    const collar = addMesh(column, new THREE.CylinderGeometry(0.31, 0.31, 0.14, 12), mats.trim, 'ColumnCollar');
    collar.position.y = 3.72;
    const capital = addMesh(column, new THREE.CylinderGeometry(0.42, 0.28, 0.28, 8), mats.trim, 'ColumnCapital');
    capital.position.y = 3.93;
  });

  // pointed rib vault
  const vaultPoints = archPoints(D.innerHalfX, D.vaultSpring, D.vaultApex, 22);
  const vaultShape = new THREE.Shape();
  vaultShape.moveTo(vaultPoints[0].x, vaultPoints[0].y);
  for (let index = 1; index < vaultPoints.length; index += 1) {
    vaultShape.lineTo(vaultPoints[index].x, vaultPoints[index].y);
  }
  for (let index = vaultPoints.length - 1; index >= 0; index -= 1) {
    vaultShape.lineTo(vaultPoints[index].x, vaultPoints[index].y - 0.24);
  }
  vaultShape.closePath();
  const vaultGeometry = new THREE.ExtrudeGeometry(vaultShape, {
    depth: 5.6,
    bevelEnabled: false,
    curveSegments: 4,
  });
  const vault = new THREE.Mesh(vaultGeometry, mats.interiorStone);
  vault.name = 'HallVault';
  vault.position.set(0, 0, D.innerZ0);
  parent.add(vault);

  // transverse ribs and a ridge rib
  [-5.2, -3.3, -1.4, 0.0].forEach((z, index) => {
    const ribPoints = archPoints(D.innerHalfX - 0.1, D.vaultSpring - 0.34, D.vaultApex - 0.42, 22)
      .map((point) => new THREE.Vector3(point.x, point.y, z));
    const curve = new THREE.CatmullRomCurve3(ribPoints);
    const rib = addMesh(
      parent,
      new THREE.TubeGeometry(curve, 60, 0.075, 6, false),
      mats.trim,
      'VaultRib' + index,
    );
    rib.position.y = -0.02;
  });

  const ridgeCurve = new THREE.LineCurve3(
    new THREE.Vector3(0, D.vaultApex - 0.5, D.innerZ0 + 0.02),
    new THREE.Vector3(0, D.vaultApex - 0.5, D.innerZ1 - 0.02),
  );
  const ridgeRib = addMesh(
    parent,
    new THREE.TubeGeometry(ridgeCurve, 8, 0.07, 6, false),
    mats.trim,
    'VaultRidgeRib',
  );
  ridgeRib.name = 'VaultRidgeRib';
}

function buildInteriorDecor(parent, mats, collectors) {
  // chandelier
  const chandelier = makeGroup(parent, 'Chandelier', [0, 7.28, -2.6]);
  const swing = makeGroup(chandelier, 'Swing');
  const ring = addMesh(swing, new THREE.TorusGeometry(0.86, 0.045, 8, 36), mats.iron, 'ChandelierRing');
  ring.position.y = -1.15;
  ring.rotation.x = Math.PI / 2;
  const innerRing = addMesh(swing, new THREE.TorusGeometry(0.4, 0.03, 6, 28), mats.iron, 'ChandelierInnerRing');
  innerRing.position.y = -1.02;
  innerRing.rotation.x = Math.PI / 2;

  for (let index = 0; index < 3; index += 1) {
    const angle = (index / 3) * TAU;
    const chain = addMesh(swing, new THREE.CylinderGeometry(0.014, 0.014, 1.16, 6), mats.iron, 'ChandelierChain' + index);
    chain.position.set(Math.sin(angle) * 0.56, -0.57, Math.cos(angle) * 0.56);
    chain.rotation.z = Math.sin(angle) * 0.42;
    chain.rotation.x = -Math.cos(angle) * 0.42;
  }

  for (let index = 0; index < 8; index += 1) {
    const angle = (index / 8) * TAU;
    const x = Math.sin(angle) * 0.86;
    const z = Math.cos(angle) * 0.86;
    const cup = addMesh(swing, new THREE.CylinderGeometry(0.07, 0.045, 0.09, 8), mats.iron, 'ChandelierCup' + index);
    cup.position.set(x, -1.1, z);
    const candle = addMesh(swing, new THREE.CylinderGeometry(0.032, 0.036, 0.28, 8), mats.wax, 'ChandelierCandle' + index);
    candle.position.set(x, -0.92, z);
    const flame = addMesh(swing, new THREE.ConeGeometry(0.035, 0.14, 8), mats.flame, 'ChandelierFlame' + index);
    flame.position.set(x, -0.72, z);
  }

  // wall sconces
  const sconceSpots = [
    [-2.96, 2.9, -0.4, Math.PI / 2],
    [2.96, 2.9, -0.4, -Math.PI / 2],
    [-2.96, 2.9, -4.9, Math.PI / 2],
    [2.96, 2.9, -4.9, -Math.PI / 2],
  ];
  sconceSpots.forEach((spot, index) => {
    const sconce = makeGroup(parent, 'Sconce' + index, [spot[0], spot[1], spot[2]]);
    sconce.rotation.y = spot[3];
    const plate = addMesh(sconce, new THREE.BoxGeometry(0.16, 0.3, 0.06), mats.iron, 'SconcePlate');
    const arm = addMesh(sconce, new THREE.CylinderGeometry(0.022, 0.022, 0.34, 6), mats.iron, 'SconceArm');
    arm.position.set(0, 0.04, 0.17);
    arm.rotation.x = Math.PI / 2.4;
    const cup = addMesh(sconce, new THREE.CylinderGeometry(0.08, 0.05, 0.1, 8), mats.iron, 'SconceCup');
    cup.position.set(0, 0.14, 0.32);
    const candle = addMesh(sconce, new THREE.CylinderGeometry(0.034, 0.038, 0.26, 8), mats.wax, 'SconceCandle');
    candle.position.set(0, 0.3, 0.32);
    const flame = addMesh(sconce, new THREE.ConeGeometry(0.036, 0.14, 8), mats.flame, 'SconceFlame');
    flame.position.set(0, 0.49, 0.32);
  });
}

/* ------------------------------------------------------------------ */
/* merged detail collectors                                            */
/* ------------------------------------------------------------------ */

function flushCollectors(parent, mats, collectors) {
  const group = makeGroup(parent, 'Stonework');
  const definitions = [
    { name: 'MergedStoneTrim', pieces: collectors.trim, material: mats.trim },
    { name: 'MergedWarmGlass', pieces: collectors.glass, material: mats.glass },
    { name: 'MergedIronwork', pieces: collectors.iron, material: mats.iron },
    { name: 'MergedDarkInset', pieces: collectors.dark, material: mats.dark },
  ];

  definitions.forEach((definition) => {
    if (!definition.pieces.length) return;
    const geometry = mergePieces(definition.pieces);
    const mesh = new THREE.Mesh(geometry, definition.material);
    mesh.name = definition.name;
    group.add(mesh);
  });

  return group;
}

/* ------------------------------------------------------------------ */
/* entry                                                               */
/* ------------------------------------------------------------------ */

module.exports = function previewModule(moduleRoot, runtime) {
  const helpers = runtime.helpers;
  const logger = runtime.logger;

  helpers.clearGroup(moduleRoot);

  const root = new THREE.Group();
  root.name = 'GothicCastle';
  root.userData.assetBrief = ASSET_BRIEF;
  moduleRoot.add(root);

  const mats = createMaterials();
  const collectors = {
    trim: [],
    glass: [],
    iron: [],
    dark: [],
  };

  const structure = makeGroup(root, 'Structure');
  const detail = makeGroup(root, 'Detail');

  const platform = makeGroup(structure, 'BasePlatform');
  buildPlatform(platform, mats, collectors);

  const curtain = makeGroup(structure, 'CurtainWall');
  buildCurtainWall(curtain, mats, collectors);

  const shell = makeGroup(structure, 'KeepShell');
  buildKeepShell(shell, mats, collectors);

  const towers = makeGroup(structure, 'Towers');
  buildTowers(towers, mats, collectors);

  const roof = makeGroup(structure, 'KeepRoof');
  buildRoof(roof, mats, collectors);

  const buttressGroup = makeGroup(structure, 'Buttresses');
  buildButtresses(buttressGroup, mats, collectors);

  const interior = makeGroup(structure, 'Interior');
  buildInterior(interior, mats, collectors);

  // detail layer
  const windowGroup = makeGroup(detail, 'Windows');
  buildKeepWindows(windowGroup, mats, collectors);
  buildGate(windowGroup, mats, collectors);
  buildRoseWindow(windowGroup, mats, collectors);

  const gargoyles = makeGroup(detail, 'Gargoyles');
  buildGargoyles(gargoyles, mats);

  const banners = makeGroup(detail, 'Banners');
  buildBanners(banners, mats);

  const interiorDecor = makeGroup(detail, 'InteriorDecor');
  buildInteriorDecor(interiorDecor, mats, collectors);

  flushCollectors(detail, mats, collectors);

  let meshCount = 0;
  root.traverse((object) => {
    if (!object.isMesh) return;
    object.castShadow = true;
    object.receiveShadow = true;
    meshCount += 1;
  });

  logger.info('Gothic castle built with ' + meshCount + ' meshes');
};
