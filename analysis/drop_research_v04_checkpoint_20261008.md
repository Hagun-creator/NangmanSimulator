# Drop research v0.4 checkpoint — 2026-10-08

## Artifact
- `Nangman_Drop_Research_Prototype_v0_4.html`
- commit `b32f04a65ca54d12f292aef3fd2cf5fc0f14ffad`
- blob `1de6da48acdb987e2fbf653e970143c65b723faf`
- live v3.50 remains `46eeae46f173a63d88ddadef2020084a940f2d80`

## Correct target
For each shared same-ID `Rnds.Eds[id]` position:
1. generate the level-90 purple drop
2. ascend it to the level-100 equipment using v3.50 logic
3. run its CZSeed refinement sequence
4. optimize preservation for the selected target property inside the user-set refining-mud budget
5. show the FINAL refined three options as the primary result
6. continue from that final equipment into the existing mangjeong/detail UI

## Sequence rule
- Same equipment ID shares one Eds sequence across wild/gate sources.
- Wild drop color does not create a separate sequence.
- One same-ID item generation consumes one Eds position.
- Gate/dungeon name does not create a separate same-ID option sequence.

## v0.4 UI
- equipment ID
- refine target property
- refining mud budget, default 500
- sequence count, default 30
- each result row shows final refined 3 options, target total/grade and mud used
- original purple drop options and Eds/MJSeed/CZSeed are collapsed reference data

## Engine reuse
Uses current embedded v3.50 functions:
- `rkAscendForRefine218`
- `rkXlCurve237`
- `rkXilianPlanNative233`
- `toWasmEquip`
- `rkGradeBadge256`
- existing detail/mangjeong UI

v0.3 is now only an intermediate checkpoint; v0.4 is the correct user-facing direction.
