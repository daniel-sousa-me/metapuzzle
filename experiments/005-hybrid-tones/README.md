# 005 hybrid tones

**Idea.** Each cell has a tier: D (tone < 0.35), M (0.35 to 0.65), L (> 0.65). A tier-boundary cell carries its own tier plus the neighbour's tier on one side, so the boundary falls inside a piece. One rotatable class serves all four sides.

**Targets** (`make_targets.py`): cat in profile on a mid floor, sailboat with mid sea, tree with mid ground. Shape sizes are searched in code until counts match.

**Tier counts** (D / M / L): cat 76 / 124 / 300; sailboat 76 / 124 / 300; tree 76 / 124 / 300.

**Transition cells**: cat 140 (62 multi-sided), sailboat 120 (18), tree 136 (46).

**Equalization** (`quantize.py`, log in `quantize-report.txt`)
- Tiers already exact, so no cell moved (nearest-threshold rule in code).
- Rule (i) cannot apply as written: a plain cell has no other-tier neighbour to swap to. Applied instead: a multi-sided transition may take another side if its tone difference is at least 0.1. Swaps: cat 0, sailboat 4, tree 2.
- Rule (ii): classes ignore the side; scene tokens carry it as `@rotation`.
- **Not achieved:** the nine class histograms differ. Pairwise L1: cat-sailboat 126, cat-tree 10, sailboat-tree 124. The sailboat hull covers the horizon and its mast sits on sky.

**Scene metrics** (`scene-metrics.txt`, gates fail): same-position 63.0 / 58.2 / 58.0% (A-B, A-C, B-C); 2x2 reuse plain/rotated 0.77/0.86, 0.83/0.89, 0.82/0.91. Light cells (60%) drive these.

**Class codes** (`@0` neighbour top, `@90` right, `@180` bottom, `@270` left)
- `D`, `M`, `L`: plain cell.
- `DM`: dark cell, mid neighbour at the canonical side.
- `DL`: dark cell, light neighbour.
- `MD`: mid cell, dark neighbour.
- `ML`: mid cell, light neighbour.
- `LD`: light cell, dark neighbour.
- `LM`: light cell, mid neighbour.


## Step 2

**Solve.** `make_roles.py` turns `scenes.txt` into `roles.txt` and `roles-spec.json`. Frame cells take their plain tier. Interior plain cells may take their tier's transition classes (texture). Interior transitions keep their orientation as `@deg`. No target counts. `roles-to-scenes --rotation quarter --restarts 8` finds a common histogram in about 1 s; `validate_scenes` passes.

**Histogram (all three images):** D 21, DM 24, DL 31; M 69, MD 26, ML 29; L 227, LD 36, LM 37.

**Frame.** The quarter border rule needs common edge and corner pools, so `quantize.py` step 2b equalizes their tiers (edge 1/30/55, corners 0/2/2). It shifted 8, 8 and 4 cells (`quantize-report.txt`).

**Interior transitions** (cat / sailboat / tree): 134 / 123 / 128 on edge roles; 49 / 60 / 55 texture.

**Boundaries on cuts.** Interior: 0. Frame: 28 (10 / 8 / 10), coded plain. Limitation: `validate_scenes` rejects suffixes on frame cells; fix in the engine later.

**Scene metrics** (`scene-metrics.txt`, gates fail). Same position A-B / A-C / B-C: 45.8 / 44.4 / 43.2%, or 34.1 / 30.7 / 33.0% excluding the dominant light class. 2x2 reuse plain/rotated: 0.71/0.81, 0.75/0.85, 0.73/0.89.

Light cells (45% of each map) dominate same-position overlap. Proposal: count matches only over cells whose class is not the most common class of either map, dividing by that count.

## Step 3: first render and evaluation

**Command** (`run-quarter/summary.md` parameters; repo root):

`metapuzzle prototype --scenes experiments/005-hybrid-tones/scenes.txt --classes experiments/005-hybrid-tones/classes.json --out experiments/005-hybrid-tones/run-quarter --sizes 20x25,20x25,20x25 --border standard --rotation quarter --seed 0 --iters 300000 --cell 32`

**Scorecard** (EVALUATION.md format, `run-quarter`)

| Check | Gate | Value | Result |
|---|---|---|---|
| Piece adjacency AB / AC / BC | < 5% each | 0.00 / 0.00 / 0.00% | PASS |
| Largest shared cluster | < 4 | 0 | PASS |
| Same-position overlap AB / AC / BC | < 25% each | 45.8 / 44.4 / 43.2% (excl. dominant L: 34.1 / 30.7 / 33.0%) | FAIL, indicator |
| 2x2 window reuse | < 30% | larger of plain/rotated: 81 / 85 / 89% | FAIL, indicator |
| Transferable blob | < 10% | 31.2 / 31.0 / 25.6% | FAIL, indicator |
| T1 blind test | subjects 3+, distinct 4+, grid 2 or lower | cat unnamed, boat unnamed, tree 4/5; distinct 4/5; grid 4 / 4 / 3 | FAIL |
| T2 grid visibility | verdict 2 or lower, 70%+ invisible | C 2/5 (about 90% invisible), A 3/5 (worst), B not recorded | FAIL |

**Interpretation**
- Passes the piece-level gate at 500 pieces with zero shared adjacencies, as 004 did. Scene-level gates fail.
- Only the tree is recognized (canopy and trunk 4/5). The cat is not named, and the sail is light on light, so the boat is lost.
- Transition lobes form a regular rhythm of white holes along silhouettes, which makes the grid faintly visible.
- Frame cells stay plain, leaving square olive and navy blocks at the edges.
- Scene-level numbers are difficulty indicators, not hard gates, per `docs/DECISIONS.md`.

**Next**
- Rougher, edge-spanning transition masks: `run-quarter-v2`.
- Subject fixes (bigger cat head and ears; mid-tone sail): `scenes-v2`.
- Frame-cell transitions in the engine.


## Step 2b: subject fixes

Suffix `-v2` on `make_targets.py`, `quantize.py` (report to `quantize-report-v2.txt`) and `make_roles.py`; then `roles-to-scenes roles-v2.txt --spec roles-spec-v2.json --out scenes-v2.txt --rotation quarter --restarts 8`. v1 files are unchanged.

- Sail is mid tone; horizon row 19.6. Tree unchanged. Cat head radius 3.4 cells, taller ears.
- Tiers before equalization (D/M/L): cat 76/122/302, sailboat 76/123/301, tree 76/124/300. After: 76/123/301 each.
- Histogram: D 14, DM 42, DL 20; M 60, MD 37, ML 26; L 230, LD 30, LM 41.
- Scene metrics (gates still fail): same position excl. L A-B/A-C/B-C 28.9/26.1/24.6%; 2x2 reuse plain/rotated A-B 0.71/0.82, A-C 0.78/0.87, B-C 0.77/0.93; transferable blob 32.0/34.8/27.0%.

## Step 4: minimal, localized surplus

**Solve.** `make_roles_v3.py` rebuilds the codes from `roles.txt`, because `scenes.txt` now holds the solver output (texture transitions included). `target_counts` per code is the max over the three images of its boundary cells: DM 23, DL 31, MD 19, ML 22, LD 33, LM 33. Plain tiers take the rest (D 22, M 83, L 234). Each image adds 27 / 38 / 33 surplus pieces, down from 49 to 60 texture.

**Localized.** Interior plain cells next to a same-tier transition are `near` (own tier plus its transitions, weights 1/3/3). Others are `far` (plain only). All surplus lands in `near`; `roles-to-scenes --restarts 8` solves in 13 s.

**Result.** Histogram identical across maps. Scene gates still fail, and same-position overlap is higher (excl. L 48 / 41 / 43%). Every surplus piece touches another transition.

## Step 5: marching tiles (scenes only)

`quantize_v4.py` (8-neighbour masks; report `quantize-report-v4.txt`), `make_roles_v4.py`. Codes `<own><nbr><s|c|i|p>`; `d` is `<nbr><own>d`.

**Patterns** (cat / sailboat / tree): s 99 / 134 / 88, c 24 / 22 / 33, i 30 / 22 / 35, p 4 / 0 / 0, d 1 / 0 / 0. Approximations (strip / s+diag / c+diag / i+multi): 6 / 10 / 1 / 3; 1 / 5 / 1 / 0; 0 / 7 / 0 / 0.

**Common histogram** (max): DLs 16, DMc 8, DMi 11, DMp 2, DMs 41, MDd 1, LDc 1, LDi 7, LDs 19, LMc 6, LMi 16, LMs 24, MDc 12, MDi 4, MDp 1, MDs 38, MLc 13, MLi 3, MLp 1, MLs 13. Surplus: 79 / 59 / 81.

**Infeasible.** Own-D codes need 79 cells; each map has 76 D cells (target -3), so `roles-to-scenes` rejects it. No `scenes-v4.txt` or metrics. Near capacity also fails (cat D: 30 surplus, 19 near cells). Rotation-0 transitions (36 / 39 / 35) are unconstrained.

**Class codes:** D, M, L, DLs, DMc, DMi, DMp, DMs, MDd, LDc, LDi, LDs, LMc, LMi, LMs, MDc, MDi, MDp, MDs, MLc, MLi, MLp, MLs.

## Step 6: merged classes and boundary budgets

**Classes** (`quantize_v5.py`, log `quantize-report-v5.txt`). Straights `PQs` (darker P first, lighter Q half on the boundary side); corners `PQc` (quarter tier first; a `QPi` corner is the same piece rotated); caps `PQp`; dots keep v4 naming (`MDd`). Specs: `classes-v4.json` gains `MDd` (`gen_classes_v4.py`); `classes-ink.json` regenerated.

**Budgets** (`boundary-budgets-v5.txt`). Surplus (max minus own) for cat / sailboat / tree: DM 50 / 19 / 57, DL 0 / 5 / 8, ML 19 / 25 / 6; total 69 / 49 / 71.

**Roles** (`make_roles_v5.py`). Edges fixed. Surplus goes to 8-isolated far cells (2+ from any transition): 25 / 26 / 26. The rest goes to near cells, plain otherwise (42 / 23 / 41), then 2 / 0 / 4 residue to non-isolated far cells. Near-only placement would leave 6 pieces unplaced (cat D 2; tree D 2, M 2).

**Scenes** (`build_scenes_v5.py`). `roles-to-scenes` did not finish: `roles._hall` enumerates every subset of the roles in the interior (about 2^28), and the run was killed after 15 minutes. It fixes the histogram to `target_counts` and reuses the library's placement and annealing. Maps match the target and pass `validate_scenes`.

**Metrics** (`scene-metrics-v5.txt`, gates fail). Same position excluding L: 32.9 / 37.8 / 30.7%; 2x2 reuse: 55 / 73 / 68%; transferable blob: 32 / 34 / 32%.

## Step 6b: rotation and host fix (v5 renders)

**Bug.** Step 6 had two faults, found by an edge check (section 5 of `quantize-report-v5.txt`). Symmetric ink strokes hid both.
1. Lighter-own straights were not turned 180 degrees (`FLIP_LIGHT_STRAIGHTS = False`), so the lighter tier sat on the darker side of the boundary.
2. Both cells of a tier edge hosted the transition. Each drew the other tier as a half strip, so the strips zigzagged (D|L|D|L) inside dark bodies.

**Convention.** A merged straight `PQs` has the darker P as base at the bottom and Q as mass on top. `@deg` is the side that holds the neighbour's mass (v4). `render.py` rotates clockwise: a marker at the top left goes to the top right under `rotate(90)`. Corners and caps keep v4's canonical geometry, so their rotations carry over (the `i` mapping is a constant shift).

**Host rule.** `HOST = "darker"`: a cell counts only lighter neighbours, so the darker cell of each tier edge hosts it and the lighter cell stays plain. `HOST = "both"` reproduces v4 cell by cell (checked).

**Edge check** (`verify_edges`, 955 shared edges per image; a mismatch is a shared edge whose halves disagree)

| config | other | junction | approx | cap | frame |
|---|---|---|---|---|---|
| v4 hosts, flip off (before) | 164 | 217 | 74 | 1 | 33 |
| v4 hosts, flip on | 91 | 218 | 79 | 2 | 29 |
| darker host, flip on (now) | **0** | 64 | 53 | 4 | 22 |

Categories: other = unexplained (must be 0); junction = three-tier corner, where one tier is dropped; cap = a `p` piece's split side meets a plain neighbour; frame = tier cut on a frame cell (coded plain, as in step 2b); approx = the four v4 approximations.

**Results.** Transition cells per image (cat / sailboat / tree): 86 / 94 / 83, was 158 / 178 / 156; surplus 41 / 33 / 44. `make_roles_v5.py` and `build_scenes_v5.py` (defaults) ran with no shortfall; `validate_scenes` passes. Scene gates still fail and are worse: same position excl. L 40 / 40 / 37% (was 33 / 38 / 31); 2x2 reuse (larger of plain and rotated) 73 / 80 / 80% (was 55 / 73 / 68); transferable blob 47 / 46 / 47% (was 32 / 34 / 32). Plain L is now 287 of 500 cells.

**Renders** (`--rotation quarter --cell 32`, `run-full-v5` with `classes-v4.json`, `run-ink-v5` with `classes-ink.json`): piece gates pass with 0 shared adjacencies. Dark bodies are solid with ragged edges and an olive ring; the ground band has a ragged top.

## Step 8: diagonal and tip tiles

`quantize_v6.py` (tie rule, diag g, tip t), `gen_classes_v7.py` (110 classes), `gen_classes_ink_v7.py`, `make_roles_v6.py`, `build_scenes_v6.py`. Outputs use `-v6`; renders in `run-full-v6/` and `run-ink-v6/`.

- **Ties:** a 2-2 tie between two tiers goes to the lighter one. 20 cells change (cat 10, sailboat 1, tree 9), all dark cells.
- **Diag (g):** 14 tiles, all in the tree canopy (6 runs). Cat and sailboat runs fail the side check. The sail edge slopes about 2.5 rows per column, so it has no 45-degree run and stays a staircase. Diag sides may meet a three-tier junction (v5's "junction"). Clearing the corner-only quarters on the base side removed 8 tree transition cells (83 to 75).
- **Tips (t):** cat 3, sailboat 0, tree 0. Caps: 0.
- **Bump, notch (b, n):** 0. A straight cannot span a one-row step.
- **Edge check:** 0 unexplained mismatches.
- **Surplus:** cat 47, sailboat 39, tree 58 (v5: 41 / 33 / 44).
- **Scene gates** still fail. Same position excluding L: 41.5 / 40.6 / 35.2% (v5 40.3 / 39.6 / 36.9%).
- **Visual:** the tree octagon edges are diagonal in the ink render; the sail hypotenuse is still a staircase.
