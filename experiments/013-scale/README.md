# 013: how much does piece count buy?

The 005 pipeline at 500, 750, 1026 and 1536 pieces. Code: `gridcfg.py` (`GRID=COLSxROWS`), ported scripts, `run_grid.sh COLSxROWS CELL`. Outputs: `g<COLS>x<ROWS>/`. At 20x25 the port matched 005 exactly before the label change (`port-check-g20x25/`).

## Changes versus 005 (all sizes)
- Tiers are majority-vote labels per cell (ties to the lighter tier), which removes the mid ring. The 2-2 neighbour tie in the classifier also goes to the lighter tier.
- Shapes are drawn once in 005's units, so each board has a different aspect (0.83, 0.71, 0.67 against 0.80). This confounds recognition.
- Tier-count fit: spread limit 9 x cells/500 (3 in 005), and the target window widens by the first feasible factor in (1, 1.5, 2, 3, 4).
- Renders use the working-tree `textures.py`, which has uncommitted edits.

## Results

| | 20x25 | 25x30 | 27x38 | 32x48 |
|---|---|---|---|---|
| pieces | 500 | 750 | 1026 | 1536 |
| cell px (height about 800) | 32 | 27 | 21 | 17 |
| transition cells cat / sailboat / tree | 67 / 85 / 71 | 94 / 97 / 90 | 108 / 122 / 107 | 149 / 173 / 143 |
| surplus cat / sailboat / tree | 38 / 20 / 34 | 40 / 37 / 44 | 44 / 30 / 45 | 75 / 51 / 81 |
| D touching only M (cat / sailboat / tree) | 7 / 28 / 15 | 13 / 31 / 18 | 11 / 31 / 20 | 17 / 63 / 34 |
| unexplained edge mismatches | 0 | 0 | 0 | 0 |
| target window factor | 1 | 2 | 1.5 | 2 |
| shared adjacencies AB/AC/BC | 0 | 0 | 0 | 0 |
| piece gates | PASS | PASS | PASS | PASS |
| same-position A-B excl. L (gate 25%) | 42.5% | 37.2% | 41.3% | 40.1% |
| make_targets / make_roles / build_scenes (s) | 54.6 / 1.4 / 0.2 | 85.0 / 2.2 / 0.2 | 111.5 / 3.2 / 0.2 | 177.2 / 6.5 / 0.2 |
| solve (s, full) | 0.04 | 0.05 | 0.06 | 0.08 |
| prototype wall, full / ink (s; render dominates) | 23.2 / 2.3 | 33.3 / 3.1 | 42.8 / 4.1 | 64.3 / 6.1 |

`validate_scenes` passes at every size. Scene gates fail at every size, as in 005.

## Visual read (downscaled triptychs; not a blind test)
- **Cat:** ears and body at 20x25. From 25x30 up, the ear pair and tail curl read in the full view. The ink view stays weak.
- **Surplus:** small sky islands persist. At 32x48 the holes inside the canopy and hull are more numerous, so surplus does not visibly shrink relative to the figure.
- **Grid rhythm:** the ink views show no regular rhythm. The full views keep short ground dashes, finer at 32x48.
