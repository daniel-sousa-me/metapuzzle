# 008 mixed frames

**Question.** Can three images with different aspect ratios share one 480-piece set? A tree 20x24 (portrait), B sailboat 30x16 (landscape), C panorama 40x12.

**Setup.** `make_targets.py` draws the tone maps. `quantize.py` ranks each map into T0..T5 with counts 58/86/96/96/86/58. The brief's 60/90/100/100/90/60 sums to 500, not 480, so it was scaled. No shared frame is computed: `validate_scenes` checks border counts only for equal shapes. `scenes.txt` holds three blocks of different sizes, and `load_scenes` accepts it. Class spec: `classes.json` from 004.

**Feasibility.**
- `run-quarter/` (`--rotation quarter --cell 24`): invalid, 3 violations (one per map). Piece gates PASS, scene gates FAIL. Still 3 violations at 1M iterations.
- `run-flat/` (rotation none, 64 extra flat pieces): invalid, 41 violations. The prototype CLI has no `--extra-flat` option, so `run_flat.py` wraps `pieces_from_scenes` with `extra_flat_pieces` and calls `run_prototype`. 64 matches the surplus: 141 edge and 7 corner pieces against 84 frame cells. A scratch sweep (0/40/64/96/128/160 extras) gave 83/57/41/40/33/27 violations. 1M iterations at 64 still gave 41.
- `meta.energy` counts shared adjacencies only. Mismatches are separate, so energy 0.0 does not mean valid.

**Piece-level shared adjacencies** (both variants): AB 0, AC 0, BC 0. Neither solution is valid, so these are indicative only.

**Scene metrics** (`scene-metrics.txt`). Same-position overlap: "n/a (shapes differ)". 2x2 window reuse, plain/rotated: A-B 0.61/0.84, A-C 0.72/0.83, B-C 0.74/0.81. Transferable blob: 15 cells (3.1% of A), 11 (2.3% of A), 18 (3.8% of B). Scene gates fail on 2x2 reuse for every pair.

**Visual assessment** (`run-quarter/triptych.png`, invalid solution).
- Tree: the dark round canopy and trunk read. It is the most recognizable.
- Sailboat: the dark hull band reads, and a light patch suggests the sail. The mast is not clear.
- Panorama: a dark lower band under a light sky reads as a landscape. Peaks and sun do not read.
- Different pictures? Layouts differ, but all three share one dapple texture and mid-light blend, so they read as one family.

**Verdict.** Mixed frames run through the pipeline, but neither variant gives a valid solution. The 2x2 reuse gate fails for every pair.

## Round 2: valid solutions with seams

**Root causes of round 1.**
- Frame mismatch. The three boards have 84, 88 and 100 border slots, so the inventory must hold 100 frame pieces. In the 84- and 88-slot pictures the surplus flat-sided pieces have to sit inside, and a flat side is legal there only against another flat side (a seam). The solver started from random placements that fit slots one by one, and its single-piece swaps could not build or move a seam, so it was left with mismatches (3 in quarter mode).
- Class maps make the frame bigger. A directional frame piece has a side and a class, so the inventory holds, per side and class, the most any of the three maps needs: 153 flat-sided pieces without rotation, not 100 (127 with quarter turns). The corner classes also differ (A and B: T4/T5/T2/T2, C: T4/T4/T1/T1), so 3 corner pieces are surplus in every picture.
- No seam-aware construction or moves existed, so extras only moved violations around (83 down to 27 at 160 extras, never 0).

**Fix.** `pieces_from_scenes` adds flat edge pieces until each map's leftover flat pieces can pair into seams, choosing classes that fit all three maps (a flow over the class pairs that touch in each map; quarter mode only needs an even count). `solve` builds a valid layout per board before annealing: frame slots take their exact-fit pieces, a leftover corner piece takes two edge pieces in an L, edge pieces pair into dominoes, and plain pieces fill the rest by class. The moves then keep it valid: swap two single pieces, move a seam group to any placement (rotating it when the pieces rotate) and send the displaced plain pieces to the vacated cells, or swap two groups. `metapuzzle prototype` has `--extra-flat N` (extras beyond the automatic ones).

**Runs** (same scenes and classes, seed 0, 300k default iterations, `--cell 24`):

| run | command | valid | shared AB / AC / BC | seams A / B / C | flat pieces inside A / B / C | flat-sided pieces |
|---|---|---|---|---|---|---|
| `run-quarter-v2/` | `--rotation quarter` | yes (0 violations) | 0 / 0 / 0 (129 iterations) | 23 / 21 / 15 | 43 / 39 / 27 | 127 |
| `run-flat-v2/` | `--rotation none --extra-flat 64` | yes (0 violations) | 2 / 0 / 0 | 82 / 80 / 74 | 161 / 157 / 145 | 245 |
| scratch, not kept | `--rotation none` (no extras) | yes (0 violations) | 0 / 2 / 2 | 78 / 76 / 70 | 153 / 149 / 137 | 237 |

A seam is one flat-flat contact; a domino is one seam, an L (corner piece plus two edge pieces) is two. Seven corner pieces exist in each run (4 frame corners plus 3 surplus, which sit inside in L groups). Round 1's invalid solutions had 3 (quarter) and 41 (flat) violations while reporting 0/0/0 shared, since the energy does not count mismatches.

**Reading the numbers.**
- Quarter turns are cheaper: 127 flat-sided pieces and 15 to 23 seams per board, against 237 to 245 and 70 to 82 without rotation. Without rotation a piece keeps its side, so each side's pool must cover the largest need of any map, and the pieces left over must find an opposite-side partner of a class that touches theirs in that picture.
- Without rotation 137 to 161 of the 380 to 396 interior pieces are flat-sided, over a third. That is a lot of straight edges inside a picture. The result is valid with 2 to 4 shared adjacencies, but the seams will show in the print. Quarter mode is the better choice for these maps.
- `--extra-flat 64` made no real difference to the result (2 shared against 4); the automatic padding already covers what the seams need.
- Scene gates are unchanged (2x2 window reuse 60.6 to 73.6%, FAIL), since the class maps did not change. The visual assessment of Round 1 stands, now on valid solutions: `run-quarter-v2/triptych.png`.
- Files: `run-quarter-v2/`, `run-flat-v2/`, and the stdout of both in `run-quarter-v2-stdout.txt`, `run-flat-v2-stdout.txt`. `run_flat.py` now calls `run_prototype(extra_flat=...)`.
