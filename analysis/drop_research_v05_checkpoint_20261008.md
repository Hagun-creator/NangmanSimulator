# Drop research prototype v0.5 checkpoint — 2026-10-08

Artifact: `Nangman_Drop_Research_Prototype_v0_5.html`
Commit: `c7bb89918aba7ea649c8a34f58b481a49a01a511`
Blob SHA: `4fcad8f2bac5a8707014de6085b234c35349a90c`

## Changes
- Prototype top-level UI now exposes only `장비 시뮬레이터` and `드랍템`.
- 세수 시뮬레이터 / 캐릭터 상태 are hidden and inert in this research build.
- Shared save loading now prioritizes the embedded v3.50 equipment engine's native `handleSaveFile(file)` path.
- Literal `\\n` artifacts at HTML script/style boundaries were removed.
- Equipment view opens first; 드랍템 routes to `dropResearch`.
- v0.4 final-refine direction is preserved: shared same-ID Eds -> level-90 purple -> level-100 ascend -> CZ refine optimization -> final 3 options.

## Verification
- title/H1 both v0.5.
- top tabs: `find` / `dropResearch`.
- native `handleSaveFile` path present.
- wash/character hidden.
- parent script-boundary literal `\\n` count = 0.
