# Drop research v0.3 implementation checkpoint — 2026-10-08

- New standalone: `Nangman_Drop_Research_Prototype_v0_3.html`
- Commit: `3a3d547155965ab23b125839842a466311da6d52`
- Generated blob: `4c430e6f7811d94dc40e1581e6e2dd29fddd6d69`
- Live `Nangman_Integrated_Simulator_v3_50.html` was not modified.

## v0.3 purpose
Focuses on level-90 purple gate equipment and the shared same-ID `Rnds.Eds[id]` affix sequence.
For each verified level-90 ID, row N means N same-ID wild drops (any color) are inserted first, then the next gate item is forced to purple and its 3 normal affixes are generated.

Verified selectable IDs:
`4009,4209,4409,4609,4809,4811,5009,5015,5209,5213,5409,5420,5609,5616`
- 5009 = 자미아대.

## Exact sequence model implemented
- `getEquipRandBetween(id,1,99999999)`: persisted `Eds[id]` becomes raw next state; returned generation value is `raw % 99999999 + 1`.
- generated object's RNG starts from that returned value.
- compatibility quality RNG consumes `[74,20,5,1]`.
- forced purple base stats scale to 108%.
- three normal ext slots use verified candidate order/config weights.
- option grade weights: `[70,25,4,1]`.
- factor ranges: `75..95 / 95..110 / 110..120 / 120..125`.
- slot multipliers: `100 / 75 / 50`.
- duplicate normal props are allowed.
- `MJSeed=floor(genSeed/10)+123`; `CZSeed=floor(genSeed/10)+456`.

## v3.50 integration
Clicking a row calls existing `showDetailTop233(equip,'dropResearch','xl')`, so the generated purple equipment opens directly in the current v3.50 detail/refine/mangjeong UI.

## Validation
- injected patch JS syntax parsed successfully.
- parent title and H1 both v0.3.
- v0.3 opens equipment/drop-research view.
- old remove-drop UI cleaner removed.
- live v3.50 unchanged.
