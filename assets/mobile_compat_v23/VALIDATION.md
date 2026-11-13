# Mobile compatibility v23 — 2026-11-12

Phone evidence: user confirmed the geometry-only horse is visible and ridable; original embedded-animation horse invisible, createWLRD reference monster visible. This verifies the alternate loading/instantiation path, not a definitive decoder root cause.

Candidate preserves geometry, textures, skeletons, external animations, current world placement, battle rules, and effect appearance. No Git push, savegame, unlimited resources, or blanket quality reduction.

## Installed candidates
- Actors: bjst3odovfmkvqc1.wprefab; main wrapper -535980144. Horse, dragon, carpet, witch and 9 sheep replace the original 13 roots.
- Gameplay: nb9tr05c6t4tmdvh.wprefab; main wrapper -806676290. Explicit shadow/wheat geometry hierarchy, cached script dependencies, bounded loading, lightweight vegetation updates, pooled projectile effects, explicit ground-color texture dependency.
- Original scene backup: main-before.scene.data. Only public Scene SDK/CLI mutations used.

## Confirmed native results
- Horse Idle/Run, sheep Idle/Walk, witch idle, carpet ripple, dragon perch/takeoff/fly/land: playback succeeds and transforms change.
- Shadow Idle/FloatMove now each animate 14 transforms; intermediate opaque source animated zero.
- Horse, sheep, witch, carpet, dragon, wheat, shadow all have enabled meshes and authored material shader.
- Ground texture donor binds in one attempt; desktop already had correct terrain texture, so zero desktop patches expected.
- Projectile mock: 50 sequential shots create 1 instance, reuse 49; capacity, idle expiry, teardown pass. Native earlier candidate observed actual projectile reuse and zero effect-play failures. Does not establish phone crash resolution.
- No temporary runtime hooks remain.

## Not yet accepted
- Phone main-scene visibility, animation and interaction beyond the tested horse fixture.
- Phone skill crash / 20-minute stability / FPS.
- White plant bases on phone (specific ground texture binding fix is a hypothesis).
- Actual challenge entry/spawn: source mesh and animation ready, join test was blocked by the opening-menu state; not a successful combat end-to-end test.
- Native log contains a sheep convex-mesh hull warning despite capsule replacement; collider lifecycle still needs investigation. Other platform UI/debug warnings also remain. No claim of error-free platform logs.

Test-only class selection and teleport occurred in the disposable native preview. No test materials or progress were serialized into the scene. Runtime was stopped before saving.

Save receipt: `final-save.json`, committed and no unsaved changes. Saved scene SHA256 `9b8f3983771035f50d79b2b331802dfa591ee706f27621c2a69009e3657ce54a`. Task-owned offscreen instance stopped. Foreground main opened for phone QR. Serialized common-node transform differences are 54 animated bone/body nodes; see retained-transform-diff.json, not broad layout replacement. Scene ZIP 5.08 MB is scene data only, **not** the complete phone dependency download.
