# Tripo approved batch — 2026-11-10

34 approved models generated and downloaded. Manifest: `assets/tripo/approved_batch/manifest.json`. No editor scene changed in this batch. Preserve all user placements and castle layout.

## Horse gait correction

`tools/models/refine_horse_animation.py` corrects the right rear hip parent, uses armature-space vertical body displacement, and bakes foot-target IK with no limb stretch. Four-beat walk uses LH → LF → RH → RF sequence; trot uses diagonal pairs. Output: `horse_refined_v1.glb` and editable `horse_animation_edit.blend`, containing Idle, Walk, Trot. Existing mesh and weights retained.

`tools/models/audit_horse_animation.py` reloads exported GLB and samples 97 times per clip. All three loops have zero first/last vertex difference. Bone scale deviation < 0.000002. Walk hoof minimum z > -0.000017 in a model approximately 0.97 units tall. Small hoof-height differences remain from the source mesh. Audit is offline, not an editor acceptance test.

Walk clip: 1.6 s, stride 0.16 model units, stance fraction 0.66. Match game movement speed to 0.151515 × model world scale × animation playback speed to avoid foot sliding. Trot: 0.9 s, stride 0.20, ground speed 0.396825 model units/s. Preview: `assets/concepts/review_v1/horse_motion/walk_refined.webp`.

## Remaining batch work

Sheep: `sheep_rigged_walk.glb` contains quadruped walk, not yet motion-reviewed. Witch: `witch_rigged_idle.glb` contains idle; Tripo Walk button did not produce an exportable walk clip, so walking remains outstanding. Do not mark all animations complete. Single leaf still needs lower face/texture budget for repeated placement. Static asset QA, editor import and actual 4000-capacity measurement remain outstanding. Rigging cost 80 credits (horse submitted twice), generation cost 1360, balance last observed 2005.

## Ghost rig added

User explicitly requested ghost bones. `shadow_spirit_rigged.glb` now has 14 joints, max 4 normalized influences per vertex, Idle (4s) and FloatMove (2.4s). Custom Blender rig includes head, chest, both arms/hands, cape and 3 tail segments. Original mesh/textures retained. Export is 915,212 bytes, +101,772 bytes versus static source. Offline skin/loop audit passed; worst local edge change 27% in flowing cloth, visually checked. Source and editable .blend retained; not yet imported into editor. Rebuild: `tools/models/rig_shadow_spirit.py`; audit: `tools/models/audit_shadow_spirit.py`; preview: `assets/concepts/review_v1/ghost_motion/idle.webp`.

## Scene placement completed via public CLI

34 approved assets installed as 61 instances, replacing 23 old model roots. Saved live project `project_lapv8fm0`; assembly root `1250625426`. Final archive and receipts: `assets/tripo/scene_install/`. `scene-final.data` is the saved snapshot. Castle shell/rooms, dragon placement and terrain unchanged; original spawn transform unchanged (editor regenerated its ID on reopen). Seven plants intersecting the new stable footprint/entrance removed.

Horse/sheep at pasture; stable beside horse; witch/staff/potion by shop; altar/runes/mushrooms/tree/boats replace old anchors; egg in sanctuary; decorations added to castle without changing layout. Ghost pool, egg stages 1–3 and single leaf are inactive templates. Existing glowing canopy remains; user places individual leaves. No new combat/egg progression/horse-riding gameplay implementation claimed.

Runtime checked horse walking, sheep walk/idle switching, witch idle, and ghost bones/idle. Witch walking still outstanding. Corrected tree roots, altar, potion, skewer and egg ground contact; placement-plan.json contains final positions. Official assembly capacity 265.305 points (249,365 faces), not whole-world capacity nor net increase. Whole-world 4000-point check remains unmeasured.

Original background instance exited before final v2 save; recovered by reopening saved v1, removing only our v1 assembly + seven plants, importing archived v2, then saving (committed; hasUnsavedChanges=false). Animation authoring operation belonged to expired instance; finish on recovered instance returned owner mismatch; no scene impact.

Final reload visually checked stable/horse and witch location; runtime stopped (status not_started). Final scene save committed with hasUnsavedChanges=false. This task’s recovered offscreen instance shut down; user foreground project untouched.
