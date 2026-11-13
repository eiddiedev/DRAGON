// Read-only runtime probe for an already-running isolated world.
// Do not Invoke() button callbacks: use the returned normalizedTopLeft point with
// the runtime's real pointer/touch command, then run this probe again for evidence.
const U = CS.UnityEngine;
const out = {
  probe: 'review-v27-native-interactions',
  screen: { width: U.Screen.width, height: U.Screen.height },
  actor: null, exploration: null, targets: [], buttons: [], errors: []
};
const vec = p => ({ x: p.x, y: p.y, z: p.z });
const actor = CS.DouyinActorService.GetLocalActor();
if (actor) {
  out.actor = { position: vec(actor.position), sitting: actor.IsSitting(), flying: actor.IsFlying() };
}

// Official Lua-runtime binding lookup; no hardcoded object name or component index.
try {
  const bindings = await lua.bindings();
  const bound = bindings.filter(b => b.referenceName === 'dragon_exploration.lua');
  if (bound.length === 1) {
    out.exploration = await lua.eval(bound[0].bindingKey,
      'return {status=GetStatus(),dependencies=GetDependencyDiagnostics(),loreTargets=GetLoreTargets and GetLoreTargets()or nil}');
  } else {
    out.errors.push('Expected one exploration binding; found ' + bound.length);
    out.explorationBindings = bound.map(b => ({ bindingKey: b.bindingKey, referenceName: b.referenceName }));
  }
} catch (error) { out.errors.push('Exploration diagnostics: ' + String(error)); }

const specs = [
  { name: 'holy_tree3', kind: 'tree', radius: 9, height: 4, approach: '3–5m from trunk; outside its collider', labels: ['古树 · 重新立誓'] },
  { name: 'tripo_witch', kind: 'witch', radius: 2.8, height: 4, approach: 'inside witch_shop_v2, 0.8–1.5m from witch; unobstructed', labels: ['调制星露', '饮用神秘药水'] },
  { name: 'camp', kind: 'camp', radius: 4, height: 4, approach: '1.5–2.5m from camp; closer to camp than nearby stele', labels: ['篝火 · 烤蘑菇'] },
  { name: 'tripo_camp_stele', kind: 'lore', radius: 3, height: 4, approach: '0.8–1.5m from stele; this is the camp reading entry', labels: ['读石碑'] }
];
for (const spec of [
  { name: 'tripo_castle_bookshelf_0', kind: 'lore', id: 1, radius: 3.2, height: 3, labels: ['翻阅手稿'] },
  { name: 'tripo_castle_bookshelf_1', kind: 'lore', id: 2, radius: 3.2, height: 3, labels: ['翻阅手稿'] },
  { name: '书库桌上烛光', kind: 'lore', id: 3, radius: 2.6, height: 3, labels: ['读桌上的信'] },
  { name: 'rune_0', kind: 'lore', id: 5, radius: 3.6, height: 6, labels: ['读柱上的铭文'] },
  { name: 'rune_1', kind: 'lore', id: 6, radius: 3.6, height: 6, labels: ['读柱上的铭文'] },
  { name: 'rune_2', kind: 'lore', id: 7, radius: 3.6, height: 6, labels: ['读柱上的铭文'] },
  { name: 'DragonPactMemorial', kind: 'lore', id: 8, radius: 3.2, height: 3, labels: ['读契碑'] }
]) specs.push(spec);
for (let i = 0; i <= 35; i++) specs.push({ name: i === 0 ? 'mush' : 'mush_' + i, kind: 'mushroom', radius: 3.5, height: 4, labels: ['采集蘑菇'] });
for (let i = 0; i <= 8; i++) specs.push({ name: 'sheep_' + i, kind: 'wool', radius: 3, height: 4, labels: ['取羊毛'] });
for (const spec of specs) {
  try {
    const go = U.GameObject.Find(spec.name);
    if (!go) { if (['tree', 'witch', 'camp', 'lore'].includes(spec.kind)) out.targets.push({ ...spec, found: false }); continue; }
    const p = go.transform.position;
    const distance = actor ? U.Vector3.Distance(actor.position, p) : null;
    const verticalGap = actor ? Math.abs(actor.position.y - p.y) : null;
    out.targets.push({ ...spec, found: true, position: vec(p), active: go.activeInHierarchy,
      distance, verticalGap, withinGeometryGate: distance !== null && distance < spec.radius && verticalGap < spec.height });
  } catch (error) { out.errors.push(spec.name + ': ' + String(error)); }
}
const flower = new U.Vector3(150, 40, 62);
out.targets.push({ name: '(fixed flower patch)', kind: 'flower', position: vec(flower), radius: 9, height: 6,
  labels: ['采集月见花'], distance: actor ? U.Vector3.Distance(actor.position, flower) : null,
  approach: 'within 2–4m of the fixed point, daytime' });

const relevant = /重新立誓|调制星露|饮用神秘药水|烤蘑菇|采集|取羊毛|读石碑|铭文|手稿|桌上的信|契碑|誓约|立誓|签约|出锅/;
const allButtons = U.Resources.FindObjectsOfTypeAll(puer.$typeof(U.UI.Button));
for (let i = 0; i < allButtons.Length; i++) {
  const button = allButtons.get_Item(i);
  try {
    const go = button.gameObject;
    if (!go.scene.IsValid() || !go.activeInHierarchy) continue;
    const labels = [];
    const texts = button.GetComponentsInChildren(puer.$typeof(U.UI.Text), true);
    for (let j = 0; j < texts.Length; j++) {
      const label = texts.get_Item(j);
      if (label.gameObject.activeInHierarchy && label.text) labels.push(String(label.text));
    }
    let cursor = button.transform;
    const path = [];
    while (cursor) { path.unshift(String(cursor.name)); cursor = cursor.parent; }
    const fullPath = path.join('/');
    // Include native interaction names even if label injection is not yet ready.
    
    const rt = button.transform;
    const canvas = button.GetComponentInParent(puer.$typeof(U.Canvas));
    const rootCanvas = canvas && canvas.rootCanvas ? canvas.rootCanvas : canvas;
    const overlay = !rootCanvas || rootCanvas.renderMode === U.RenderMode.ScreenSpaceOverlay;
    const camera = overlay ? null : (rootCanvas.worldCamera || U.Camera.main);
    if (!overlay && !camera) { out.errors.push(fullPath + ': no canvas camera'); continue; }
    const corners = CS.System.Array.CreateInstance(puer.$typeof(U.Vector3), 4);
    rt.GetWorldCorners(corners);
    // World corners are not screen coordinates for camera/world-space/scaled canvases.
    const points = [];
    for (let j = 0; j < 4; j++) {
      const q = U.RectTransformUtility.WorldToScreenPoint(camera, corners.get_Item(j));
      points.push({ x: q.x, y: q.y });
    }
    const left = Math.min(...points.map(p => p.x)), right = Math.max(...points.map(p => p.x));
    const bottom = Math.min(...points.map(p => p.y)), top = Math.max(...points.map(p => p.y));
    const centerX = (left + right) / 2, centerY = (bottom + top) / 2;
    const groups = [];
    cursor = rt;
    let alpha = 1, groupInteractable = true;
    while (cursor) {
      const cg = cursor.GetComponent(puer.$typeof(U.CanvasGroup));
      if (cg && cg.enabled) {
        groups.push({ name: String(cursor.name), alpha: cg.alpha, interactable: cg.interactable, blocksRaycasts: cg.blocksRaycasts });
        alpha *= cg.alpha; groupInteractable = groupInteractable && cg.interactable;
        if (cg.ignoreParentGroups) break;
      }
      cursor = cursor.parent;
    }
    out.buttons.push({ name: String(go.name), path: fullPath, labels,
      interactable: button.interactable, groupInteractable, alpha, canvasGroups: groups,
      canvas: rootCanvas ? { name: String(rootCanvas.name), renderMode: String(rootCanvas.renderMode), sortingOrder: rootCanvas.sortingOrder } : null,
      screenPxTopLeft: { x: centerX, y: U.Screen.height - centerY },
      normalizedTopLeft: { x: centerX / U.Screen.width, y: 1 - centerY / U.Screen.height },
      rectNormalizedTopLeft: [left / U.Screen.width, 1 - top / U.Screen.height, right / U.Screen.width, 1 - bottom / U.Screen.height],
      insideViewport: centerX >= 0 && centerX <= U.Screen.width && centerY >= 0 && centerY <= U.Screen.height,
      clickableCandidate: button.interactable && groupInteractable && alpha > 0.01 && centerX >= 0 && centerX <= U.Screen.width && centerY >= 0 && centerY <= U.Screen.height
    });
  } catch (error) { out.errors.push('Button ' + i + ': ' + String(error)); }
}
out.notes = [
  'Read-only: no teleport, no native button Invoke, no rewards, no model/UI changes.',
  'normalizedTopLeft uses the runtime Screen size; a top-left pointer API can use it directly.',
  'A candidate point does not prove absence of another UI raycast blocker. Send real input and compare status/panel state afterwards.',
  'For lore, exploration.loreTargets contains the authoritative transformed local anchor/horizontal gate; targets[] positions are the raw model origins.',
  'Only the nearest exploration target wins; witch must show two buttons; mounted/battle/menu states suppress exploration.',
  'Gathering needs daytime. Use the existing sundial interaction to change day rather than writing the script state.'
];
const bindings=await lua.bindings(),combat=bindings.find(b=>b.referenceName==='dragon_combat.lua');out.combat=await lua.eval(combat.bindingKey,'return {status=GetStatus(),visuals=GetShadowVisualDiagnostics()}');
const ts=U.Object.FindObjectsOfType(puer.$typeof(U.Transform),true);out.shadows=[];
for(let i=0;i<ts.Length;i++){const t=ts.get_Item(i);if(!t.gameObject.activeInHierarchy||!t.name.startsWith('BattleShadow_'))continue;const cs=t.GetComponentsInChildren(puer.$typeof(U.Transform),true),names=[];for(let j=0;j<cs.Length;j++)names.push(cs.get_Item(j).name);out.shadows.push({name:t.name,cubeChildren:names.filter(n=>n==='Cube'),healthCanvas:names.includes('HealthFill'),pos:vec(t.position)});}
return out;
