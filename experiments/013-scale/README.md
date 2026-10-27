# 013: how much does piece count buy?

**Goal:** how recognition, surplus and solve time change with piece count (500 to 1536, placeholder scenes).
**Result:** recognition improves clearly from 750 pieces, but surplus does not shrink with size, so 27x38 (1026 pieces) became the working grid. The blind test at 27x38 names the boat (5/5) but not the cat.

The 005 pipeline at 500, 750, 1026 and 1536 pieces (cells). Code: `gridcfg.py` (`GRID=COLSxROWS`), ported scripts, `run_grid.sh COLSxROWS CELL_PX`. Outputs: `g<COLS>x<ROWS>/` (`timings.txt`, `make-targets-report.txt`, `run-full/`, `run-ink/`). At 20x25 the port matched 005 exactly before the label change (`port-check-g20x25/`).

## Changes versus 005 (all sizes)
- Tier labels are majority votes over 8x8 supersamples per cell; ties go to the lighter tier. This replaces the threshold-per-cell tiers and removes the mid ring.
- Shapes are drawn once in 005's 20x25 units. Each board therefore has a different aspect ratio (0.80 at 20x25, 0.83 at 25x30, 0.71 at 27x38, 0.67 at 32x48). Any size effect is confounded with aspect.
- Tier-count fit (`make_targets.py`, `fit_all`): a discrete search over shape sizes for dark and mid counts. The spread limit scales with cells (9 x cells/500, 3 in 005). If no combination fits the 1x window, the target window widens by the first feasible factor in (1, 1.5, 2, 3, 4). The factor used is in the table.
- `quantize.py` then moves the residual cells across the nearest threshold, so the three tier counts become exactly equal. The table reports how many cells moved per image.

## Results

| | 20x25 | 25x30 | 27x38 | 32x48 |
|---|---|---|---|---|
| pieces (cells) | 500 | 750 | 1026 | 1536 |
| cell px | 32 | 27 | 21 | 17 |
| aspect (cols/rows) | 0.80 | 0.83 | 0.71 | 0.67 |
| target window factor (make_targets) | 1 | 2 | 1.5 | 2 |
| raw dark / mid spread before equalization (limit) | 0 / 9 (9) | 7 / 8 (13.5) | 9 / 2 (18.5) | 26 / 12 (27.6) |
| cells moved by equalization cat / sailboat / tree | 6 / 3 / 7 | 10 / 6 / 10 | 5 / 7 / 11 | 19 / 13 / 27 |
| transition cells cat / sailboat / tree | 67 / 85 / 71 | 94 / 97 / 90 | 108 / 122 / 107 | 149 / 173 / 143 |
| transition cells per 100 cells (mean of 3) | 14.9 | 12.5 | 10.9 | 10.1 |
| surplus cat / sailboat / tree | 38 / 20 / 34 | 40 / 37 / 44 | 44 / 30 / 45 | 75 / 51 / 81 |
| surplus fraction (surplus / transitions) cat / sailboat / tree | 57% / 24% / 48% | 43% / 38% / 49% | 41% / 25% / 42% | 50% / 29% / 57% |
| surplus fraction, mean of 3 | 43% | 43% | 36% | 45% |
| D touching only M, interior (cat / sailboat / tree) | 6 / 27 / 14 | 13 / 31 / 17 | 11 / 31 / 19 | 17 / 62 / 33 |
| contacts mismatched (run-full / run-ink) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| shared adjacencies AB / AC / BC (full, ink) | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| piece gates | PASS | PASS | PASS | PASS |
| scene gate, same-position excl. L (A-B / A-C / B-C; gate 25%) | 42.5 / 54.3 / 45.1 | 37.2 / 50.2 / 32.1 | 41.3 / 58.0 / 38.8 | 40.1 / 56.3 / 36.4 |
| scene gate, 2x2 window reuse (A-B / A-C / B-C; gate 30%) | 55.9 / 76.5 / 66.0 | 64.1 / 86.5 / 72.0 | 71.5 / 90.2 / 81.6 | 69.0 / 88.3 / 87.3 |
| scene gate, transferable blob, % of A (A-B / A-C / B-C; gate 10%) | 47.0 / 47.2 / 48.0 | 48.5 / 49.6 / 48.9 | 49.7 / 50.9 / 50.8 | 51.7 / 53.6 / 52.3 |
| scene gates | FAIL | FAIL | FAIL | FAIL |
| make_targets / quantize / make_roles / build_scenes (s) | 54.6 / 0.3 / 1.4 / 0.2 | 85.0 / 0.4 / 2.2 / 0.2 | 111.5 / 0.3 / 3.2 / 0.2 | 177.2 / 1.0 / 6.5 / 0.2 |
| solve iterations used (cap 300000), full | 503 | 444 | 451 | 424 |
| prototype wall, full / ink (s; render dominates) | 23.2 / 2.3 | 33.3 / 3.1 | 42.8 / 4.1 | 64.3 / 6.1 |
| total pipeline (s, sum of steps) | 82 | 124 | 162 | 256 |

Definitions: "D touching only M" counts dark cells with at least one mid 4-neighbour and no light 4-neighbour, frame cells excluded (with frame cells included the counts are 7 / 28 / 15 at 20x25; the earlier table used that). Surplus is the boundary-budget count of cells that must be added in near roles, from `boundary-budgets.txt`. Scene-gate figures are the plain (unrotated) values from `scene-metrics.txt`.

Validation: all three tier counts are identical per size after equalization. `validate_scenes` passes at every size and every run reports `valid: yes`. No tracebacks in any log. Seed 0 only, one run per size.

## Visual read (triptychs; my reading, not a blind test)
- **20x25:** cat recognisable (two ears, head, body, low tail). Sail and canopy show clear stair steps at 32 px. Sky islands and ground dabs are scattered; a few olive and blue dabs sit inside the canopy and hull.
- **25x30:** cat recognisable, but the tail reads as a boxy loop. Sail steps still visible. Light holes appear in the hull and canopy.
- **27x38:** cat recognisable with ears and tail. Sail steps are finer. Canopy carries light and olive dabs, and sky islands look similar in density to 20x25 relative to the figure.
- **32x48:** cat recognisable but more broken; tail is a thin line. Sail edge is smooth. Canopy and hull are speckled with light and olive dabs in the full view and dashes in the ink view. Surplus does not shrink relative to the figure: its fraction of transitions rises back to 50 / 29 / 57%.

## Recommendation
Use **27x38 (cell 21)** as the working grid, tentatively. It has the lowest mean surplus fraction (36% against 43-45%), a readable cat, and a pipeline of 162 s against 256 s at 32x48. 32x48 adds surplus (207 cells against 119), roughly doubles the interior D-touching-M count for the sailboat, and has the highest window reuse for B-C. 25x30 has the same mean surplus fraction as 20x25 (43%) and no advantage on the other measures. Caveats:
- Scale does not fix the scene gates. They fail everywhere, and 2x2 window reuse rises with size (A-C 76% to 90%). Treat scene uniqueness as a separate problem.
- Aspect (0.71 at 27x38, 0.67 at 32x48) is confounded with size. Differences of a few points between sizes are within what one seed can show.
- The 27x38 fit needed the x1.5 window and equalization moved 23 cells in total. 20x25 needed only 16.
