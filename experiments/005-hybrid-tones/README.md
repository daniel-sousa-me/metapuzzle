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
