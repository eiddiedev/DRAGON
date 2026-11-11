# Continuous-stone tower replacements, frozen 2026-11-11 15:34

These four resources replace the corresponding v5 tower skins. They do not replace the accepted left main clock tower or entry facade; those belong to separate work packages. No scene or collision was changed here.

| File | Triangles | Normalization scale | Bytes |
|---|---:|---:|---:|
| expand_right_tower.glb | 12,286 | 45.0 | 1,237,340 |
| expand_central_tower.glb | 7,700 | 45.470001220703125 | 954,308 |
| expand_rear_towers.glb | 13,480 | 41.600006103515625 | 1,241,540 |
| expand_clock_auxiliary.glb | 6,368 | 20.283004760742188 | 566,464 |

Total: 39,834 triangles versus 59,072 previously; 3,999,652 bytes of GLBs. Full SHA-256 hashes and exact bounds are in `receipt.json`; `export-audit.json` verifies all four exports, their triangle counts, names, hashes and absence of COLOR_0.

Keep the existing transforms. The model coordinate contract is world=(127+BlenderX, BlenderZ, 176+BlenderY), with root (127,0,176), no recentering. All four are visual-only replacements: retain existing collision settings disabled on the visual skins. Each filename stem has node `stem_GI` and material `stem_GI_PBR`.

Body, pier and pinnacle surfaces now use continuous uniform grey-purple stone without per-block chamfers, grid gaps or brick color changes. Pointed and rectangular window apertures remain open. Cornices, window surrounds, shingles and metal roof ribs remain. Small circular cornices use continuous profiles with unchanged center height, maximum radius and 0.34 m total thickness. Their geometry no longer intersects the smooth cylinder as repeated triangular points.

The materials contain true diffuse COLOR + DIRECT + INDIRECT GI. Three atlases are 2048 square and the clock auxiliaries atlas is 1024 square. FLOAT_COLOR linear authoring avoids double sRGB decoding; exported vertex colors are removed. Lighting reproduces the accepted neutral world (.65,.65,.68)*.85 approximation and existing fixtures multiplied by 2.4, not the live skybox. Original castle, interior and accepted sample sources participate as occluders. The runtime exterior tone multiplier .68 is NOT baked in; retain the parent's existing display controls.

Source: `tools/models/castle_smooth_towers.py`. `towers-source.blend` is the unbaked mother; `towers-baked.blend` is the final baked mother. The source default builds all four; `--rings-only` reuses the already frozen central resource and rebakes only the other three. GI textures and separate indirect-pass evidence are retained.

Visual verification: `towers-front.png`, `towers-rear.png` and `central-close.png` show the continuous-stone full pass. The final localized circular-cornice correction is shown in `rings-close.png`, which was inspected after export; no repeated triangular marks remain there. Adjacent entry/left-clock/main-building old brick surfaces shown in these offline composites are other agents' replacement scope. The roof geometry preserves the previously accepted close-up limitation where original metal ribs intersect near the upper spire taper; this package does not claim to eliminate every old roof intersection.

The four GLBs are frozen. Parent performs editor import, matching replacement, runtime views and passage validation.
