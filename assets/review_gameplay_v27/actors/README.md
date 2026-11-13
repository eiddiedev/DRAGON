# v27 actor audit and candidate fixes

These are candidates, not a claim that the review-client problems are fixed. No editor instance was operated, no formal scene was changed, and no Git push was performed by this subtask.

## Audited source

`editor_project/project_lapv8fm0/scene.data`, v26; full SHA-256 and actor summary are in `audit-summary.json`. All nine `sheep_0`…`sheep_8` roots, the mobile actors parent, `tripo_horse`, `dragon_v8_live`, and `dragon_peak` are active in the saved hierarchy. Sheep and snow platform were not deleted. Root transforms are preserved by every candidate.

The previously supplied review metadata saved in `assets/mobile_visual_riding_v26/new-review-metadata.json` registers separate horse/sheep/dragon external animation files under `ugc-animation/…glb`. Therefore “animations were not packaged” is not supported by this evidence. That earlier archive is not proof that the newest review client's dependencies loaded successfully.

Recorded v23 native test `assets/mobile_compat_v23/final-animations-result.json` found changing bones for horse Idle/Run, sheep Idle/Walk, and dragon clips. These data prove an earlier desktop combination worked, not that review-client playback works now. Do not change animation paths solely because graph names were renamed during archive; the recorded graph arrangement already played in that native test.

## Proven lifecycle/configuration defects

- Horse `play` short-circuits only on a string `lastClip`; it never invalidates that string when the controller rebinds. The initial Idle request happens only in `Start`, so an unmounted horse has no follow-up retry when its controller arrives late. Failure/exception has no useful bounded diagnostic.
- Sheep caches Rigidbody and animation only in `Start`. Missing body causes permanent early return. Gravity is enabled in its serialized scene before script initialization; no real ground-ready check exists with streaming enabled. The code permits falling during delayed terrain/collider load. Actual review sheep positions/logs are required before calling that the disappearance cause.
- Dragon saved default is `perch`, but `DR.updateV8` explicitly plays `idle` for the user-positioned slope pose and documents `perch` adding 6.48m of front-foot lift. Before the bridge successfully runs, the saved config and intended pose disagree. `dragon_peak` itself is present/active, at (165,0,234) scale 89.9166641. We did not move the dragon to conceal a missing support asset.

## Candidate installation

1. Replace existing horse script **8fe420a9-9b6d-488f-b707-6172cfa2fdbd** with `horse_seat_v1.lua` through the public authoring script API. It preserves v26 authoritative rider following, saddle offset, speed tiers and collision movement. Only playback lifecycle/diagnostics change.
2. Replace sheep script **5a9edffe-7c92-477d-bc9c-9865e864567e** with `tripo_sheep_motion.lua`. It preserves push/wander behavior, uses real static support before releasing gravity, and reports missing components. This must be installed **with** the initial physics change below; script-only protection cannot cover physics frames before `Start`.
3. Fresh-query handles for dragon plus sheep_0…8. Fill `HANDLE_BY_NAME` in `apply-actor-components.js` with those SDK handles. Numeric audit ids in `component-proposals.json` are only selection evidence. The operation reads current components, validates all targets, updates dragon's animation default to `idle`, and stores each sheep initially kinematic/no-gravity. It preserves all other physics/config/transform values.
4. First two real non-trigger, non-self static ground hits (0.25s apart) release each sheep to `isKinematic=false`, `useGravity=true`; it remains movable by actors. No fake plane or visual-only pushing is introduced. If the area never supplies ground, the sheep remains visible at its saved spawn with a diagnostic; the script does not pretend it has support. After 45 seconds, far sheep stop ground probes except a 5-second proximity check; nearby sheep receive a new 10-second budget. Enable/disable clears/reacquires startup support.

The shared animation helper is inlined, no `require`, scene-wide scan, new controller, replacement animation, or shared scope mutation is added. UGC lookup is confined to the exact saved actor root (a rider is temporarily parented under the horse and must never be mistaken for its animation target). Playback checks run at 0.5s while pending; component probing is at most 1Hz and stops after 60 seconds if missing. Controller identity change or object re-enable invalidates the previous clip. A successful same-state loop is not restarted.

## Verification

`python3 assets/review_gameplay_v27/actors/test_actors.py` passes Lua syntax and behavioral mocks: late Controller, false Play, same-state dedup, rebind, transition, disable/resume, lookup deadline, delayed ground, two-hit gravity release. Results in `test-results.json`.

`runtime-actor-audit.js` is a read-only native runtime probe for component readiness, actual 12-frame transform changes, actor positions, sheep physics modes and dragon platform renderer bounds. It does not force animations/teleport. It may miss inactive or streamed-out objects by design; `found:false` is not equivalent to “deleted”.

Still required in the real review build: horse idle→walk→run→idle actual bone motion; nine sheep visible after delayed loading and movable with push; dragon idle feet/support alignment (including actual platform loaded/rendered); leaving/re-entering sheep pasture; rider seat/bridge regressions. Do not mark mobile acceptance complete based on native probes or mocks.
