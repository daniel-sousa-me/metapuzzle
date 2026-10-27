# 013: scale study (incomplete)

Only the 20x25 reference grid completed. Three larger grids failed in `make_targets.py`.

## Setup

The 005 pipeline is ported with `GRID=COLSxROWS` and `run_grid.sh COLSxROWS CELL_PX`. Planned sizes: 20x25 (cell 32), 25x30 (27), 27x38 (21), 32x48 (17). Outputs are in `g<COLS>x<ROWS>/`.

Two changes versus 005:
1. Label tiers by majority vote over supersampled samples (`make_targets.py`).
2. Ties go to the lighter tier.

Aspect-ratio confound: shapes are defined once in 005's 20x25 reference units (`gridcfg.py`), so larger boards are taller. Any size effect is confounded with this change in aspect.

## Failure

For 25x30, 27x38 and 32x48, `fit_all` in `make_targets.py` exits with "no size combination matches the tier counts within +-13.5 / +-18.468 / +-27.648". The tier targets scale with cell count, but no shape-size combination met the spread limit. `run_grid.sh` chains runs with `;`, so the completion marker was written anyway. These sizes have no downstream output.

## Table (20x25 only)

| Size | Transition cells cat / sailboat / tree | Surplus cat / sailboat / tree | Surplus fraction | D touching M, no L (cat / sailboat / tree) | Shared pieces | Piece gates | Scene gates | Make targets / prototype full / ink (s) |
|---|---|---|---|---|---|---|---|---|
| 20x25 | 67 / 85 / 71 | 38 / 20 / 34 | 57% / 24% / 48% | 6 / 27 / 14 | 0 | PASS | FAIL | 49.6 / 22.7 / 2.2 |
| 25x30 to 32x48 | none | | | | | | | |

005 gives transitions 86 / 94 / 83 and surplus 41 / 33 / 44. The 013 20x25 run does not reproduce 005 exactly (tier totals 84 / 113 / 303 versus 76 / 123 / 301), because the fit picked a different shape size within tolerance.

## Visual read (20x25)

- Cat: recognisable (two ear peaks, head, body outline; tail a low lump). No comparison with other sizes.
- Sailboat and tree: clear.
- Sail and canopy: stair-stepping visible at 32 px cells.
- Foreign-colour patches: scattered olive and blue dabs in sky and grass. No comparison possible.

## Recommendation

Keep 20x25 as the working grid. The larger sizes need `fit_all` fixed before the scale question can be answered.
