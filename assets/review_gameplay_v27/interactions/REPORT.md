# Review v27 — delayed interaction readiness

Source: `editor_project/project_lapv8fm0/scripts/modules/imported/prefab_20`. The exploration and progress source SHA-256 were compared with installed formal project `project-55a43370-8734-4825-92a8-b0de824a45e2`; both exactly matched before these candidate changes. Registered script/source IDs are preserved. Only this candidate directory was written; no editor operations or main-project mutation occurred.

## Confirmed code defects

1. Exploration `discover()` resets targets then unconditionally creates fixed-position flower/bed/lore entries. `Update()` calls discovery only while `#targets == 0`. Consequently the first scan irrevocably ends discovery, even when the witch, tree, campfire, mushrooms or sheep have not loaded. A model arriving after this scan can never acquire its interaction entry.
2. Seven scripts overwrite `scope.GetScript` on the shared scope returned by `official.core.runtime_scope.from(self)`. Each wrapper permanently returns nil after 30 unsuccessful attempts. The official implementation explicitly does not cache absence because later calls may observe script readiness; multiple installed wrappers can intercept each other. This blocks the exploration module even when resources later become ready.
3. Exploration requires a successful book/UI build before it discovers or registers any native gameplay entry. Further, `buildUI()` assigns `root` before construction completes; a mid-build exception leaves `root` non-nil and the next update falsely accepts the half-built UI as ready.
4. `OnDisable` disables the exploration canvas, but there is no `OnEnable` restoring it.
5. The mystery-potion submit callback clears `potionBusy` only after `applyPotion`. An effect/clone API exception can leave this button permanently busy.
6. Daycycle resolves `main` and `exploration` inside `if not main`. When the bridge resolves first, a late exploration module is never rechecked, disabling its battle guard.

These are source-level defects with reproducing fixtures, **not a claim that every C-end symptom shares one confirmed root cause**.

## Candidate behavior

- All seven scripts use private, script-local dependency caching. They call the official `scope:GetScript(name)` / `runtimeScope:GetScript(name)` without changing the method. Fast retry: one lookup per dependency/second for the first 30 attempts. Afterwards: one lookup/five seconds, allowing recovery without per-frame scans. Successful dependencies are memoized, diagnostics retained, references released on destroy.
- Exploration keeps stable target objects. Every 0.25 seconds it performs at most eight exact-name queries; missing targets back off to a ten-second retry. Found objects aren't repeatedly searched. Destroyed/replaced objects can be reacquired. Static fallback targets do not terminate discovery.
- Inactive egg stages are obtained from the loaded stage's parent subtree rather than `Resources.FindObjectsOfTypeAll` across the editor/world. This limited traversal runs only while stages are missing, at most once per ten seconds. Late stages reapply the current personal visual stage.
- Native tree, witch and gathering entries can register before book atlases finish. Page-based interactions explicitly report not-ready instead of silently failing. A partial UI construction is destroyed before retry; a re-enabled component restores its complete canvas.
- Native-click ownership remains stable during discovery; the existing deferred dispatch/debounce remains. Re-contract lifecycle is preserved. Optional potion VFX failure does not block the potion; other potion failures restore state and release the button for retry.
- Daycycle independently retries bridge/exploration readiness. No combat rule, clone path, outfit, weapon geometry, model transform placement, quest recipe or reward amount was redesigned.

## Tests run

`python3 assets/review_gameplay_v27/interactions/test_delayed_interactions.py`

Passes:

- all seven complete Lua files parse with the installed Lua runtime;
- a dependency arriving at 75 seconds recovers, including after 30 initial failed checks;
- official scope method identity and colon/self semantics remain intact;
- late tree/witch/camp/mushroom/sheep/stele models register despite already-present fixed-position targets;
- no batch exceeds eight named queries; target records remain identical; replacement objects reacquire;
- late inactive egg siblings register and force visual-stage application;
- deferred native clicks and duplicate-dispatch debounce;
- five consecutive re-contracts, duplicate completion suppression and failed-open rollback;
- a partial canvas is removed and rebuilt on later readiness;
- a failed potion effect releases the native button;
- daycycle acquires a late exploration battle guard;
- for the additional five scripts, code below the helper is byte-for-byte unchanged except dependency call sites the explicitly approved daycycle two-line readiness split, and the modal cancellation lifecycle fix below. Clone/animation/combat implementations are preserved.

## Still requiring actual review-channel acceptance

- This cannot prove C-end native-button callback delivery, world resources/atlas registration or the server's actual loading order. A new review artifact must be inspected and tested; local preview alone is not acceptance.
- Witch interior line-of-sight rejection still follows the existing house collider behavior. If only witch remains unavailable after the general fixes, test inside the house and inspect its collider hit chain.
- Reader/camp UI still needs the actual registered book/atlas resources; this patch retries and reports readiness but cannot fabricate missing packaged assets.
- All seven same-scope wrappers must be replaced together. Leaving one old shared override can reintroduce the 30-attempt poison.
- Horse animation, sheep visual loading, water collision, dragon grounding, foliage material quality and tree glow are assigned to other v27 work and are not claimed fixed here.

## Modal lifecycle review follow-up

The initial OnEnable restoration required one additional correction: disabling the root does not reset activeSelf on the dim/book/roast/reader children. Exploration OnDisable now explicitly hides every modal child and the buff HUD, clears the native target/current pointer and invalidates the class completion token. RPG adds CancelContract, which hides its independently owned contract/backdrop, drops the pending continuation/selection and releases immobilization without treating cancellation as successful signing. Both exploration-owned interruption and RPG OnDisable invoke the cancellation path.

Additional passing tests execute tasks/cook/lore/class open → disable → enable; no modal remains visible, input is unlocked, a stale interrupted class callback cannot continue the prior flow, and a fresh subsequent re-contract succeeds. This follow-up changes exactly exploration and RPG candidates; synchronize both, not only exploration.

## Responsive combat controls and all manuscript entries

Confirmed overlap causes: only the old exit button respected the right/bottom safe-area inset, while skills retained screen-edge offsets; exit size also inherited the native hand button size. Native slot sizing divided by parent scale only, omitting its own local scale and noncentral pivot. All five combat hit rectangles now share one safe-area origin and a fitted right-hand cluster; exit keeps the established upper-right direction and its own design size. Native slot physical dimensions include complete transform scale/pivot. Existing sprites, callbacks, skills and cooldown rules remain unchanged. No combat/world-model files were modified for this fix.

The eight lore entries now have explicit references: bookshelf 0, bookshelf 1, library tabletop candle (with castle_gi_library local-space fallback), camp stele, rune 0/1/2, and DragonPactMemorial. Prior entries 1/2/3/8 were fixed world coordinates. Library radii of 1.9m/1.5m combined full 3D distance with their height offsets, shrinking the reachable walking area further; the candidate uses practical horizontal reach with a separate 3m floor gate. References are discovered through the existing bounded late-load queue and move with their models. GetLoreTargets exposes all eight positions/readiness/current IDs for real native-input acceptance.

Additional tests pass: test_combat_layout.py exercises nine desktop/mobile/aspect/safe-area profiles, every pair of attack/three-skills/exit hit rectangles, left-joystick exclusion, native parent/local scales and noncentral pivots. test_lore_entries.py executes all eight targets through the native deferred callback into the actual interact/readLore functions and corresponding atlas page, including delayed object arrival, moved shelves/library, re-reading without double counting and floor separation. Full earlier delayed-load/lifecycle tests pass again. These are code/geometry tests; the latest responsive layout and library entries still require current-runtime screenshot and actual review-phone touch validation. Synchronize only dragon_rpg.lua and dragon_exploration.lua for this follow-up, normalizing their registered IDs for the author context.
