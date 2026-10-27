# Experiment 002: Direction A, first end-to-end render

## Goal

First end-to-end render of design direction A ("Dapple Mosaic") with its three scenes: The Lone Tree (A), Isle and Sail (B), Snow Peak (C). Board is 8x10 (80 pieces), no rotation, standard border.

**Result:** run-quarter passes the piece gate (2.8 to 3.5% shared) but fails the scene gates, and distinctiveness is 2/5. Retired.

## Setup

- `classes.json`: the 15 classes from 02-piece-classes.md, keyed to `docs/design/scenes-8x10.txt`. `NOTES.md` covers how it was built.
- `run-none/`: the output. `summary.md` holds parameters and metrics; also solutions (SVG/PNG), `triptych.png`, `grid-faint/`, `metrics.txt`, `scene-metrics.txt`.
- `blind-test-1.md`, `grid-visibility-1.md`: reviews of run-none.

Command (parameters from `run-none/summary.md`):

```
metapuzzle prototype --scenes docs/design/scenes-8x10.txt \
  --classes experiments/002-direction-a/classes.json \
  --out experiments/002-direction-a/run-none \
  --sizes 8x10,8x10,8x10 --border standard --rotation none \
  --seed 0 --iters 300000 --cell 48
```

The run was valid: 0 violations.

## Results

**Piece-level shared adjacencies** (target: under 5% initial, 0 stretch). All pairs miss.

| Pair | Shared | Fraction | Clusters (3+) | Largest |
|---|---|---|---|---|
| A-B | 13 | 9.15% | 6, 3 | 6 |
| A-C | 11 | 7.75% | 3, 3, 3 | 3 |
| B-C | 15 | 10.56% | 6, 3, 3 | 6 |

**Scene-level carry-over**

| Pair | Same position | 2x2 window reuse (plain / rotated) | Transferable blob |
|---|---|---|---|
| A-B | 53 (66.2%) | 0.44 / 0.48 | 22 cells (27.5% of A) |
| A-C | 57 (71.2%) | 0.57 / 0.65 | 24 cells (30.0% of A) |
| B-C | 55 (68.8%) | 0.51 / 0.52 | 22 cells (27.5% of B) |

**Blind test.** A was read as a tree on a clifftop with sun and cloud. B and C were not recognized; they were called "variations of one picture" (distinctiveness 3/5).

**Grid visibility.** 7 of 16 interior grid lines (44%) show nothing; the rest show partly or fully. Visible causes are colour boundaries and shapes ending on piece edges. No same-texture seams. Verdicts: A 3/5, C 4/5 (worse).

## Interpretation

- The pipeline works end to end, and its output is valid.
- Textures join without visible seams in review. `NOTES.md` still flags flat transition fills as seams, which masked transitions should fix.
- The three scenes read as one picture rearranged. The shared class layout gives 66–71% same-position overlap.
- Piece-level overlap rose above 5% because class regions constrain the permutation.
- Hard class boundaries on cut lines make the grid visible. Only a few pairs have in-piece transitions.
- Only scene A is recognized. B's and C's hero structures are 3–4 cells across and reuse A's crown pieces.
- Hero structures are too small at 80 pieces to carry meaning.
- The scene-level metrics predicted the blind-test failure. They should gate future scene designs before rendering.

## Next

- Re-render after texture fixes: masked transitions, size-independent density, motif offsets.
- Evaluate alternative scene strategies (`docs/design/07`, not yet written) and a density-field grammar (`experiments/004`, not yet created).
- Compare with direction B.
- Resolve the forbidden S/ and F/ next to SK seams noted in `NOTES.md`.


## Round 2: after texture fixes

**Changes:** masked two-material transitions, size-independent drawing, motif offsets. Scenes and classes unchanged. `run-quarter` differs from `run-none-v2` only by `--rotation quarter`.

| Run | AB | AC | BC | Largest cluster | Piece gates | Scene gates |
|---|---|---|---|---|---|---|
| run-none | 9.15% (13) | 7.75% (11) | 10.56% (15) | 6 | FAIL | FAIL |
| run-none-v2 | 7.04% (10) | 9.15% (13) | 9.86% (14) | 6 | FAIL | FAIL |
| run-quarter | 2.82% (4) | 3.52% (5) | 2.82% (4) | 3 | PASS | FAIL |

Scene-level values match across runs: same-position 66–71%, 2x2 window reuse 48–65%, transferable blob 27.5–30%.

**Scorecard: run-quarter**

| Check | Gate | Value | Result |
|---|---|---|---|
| Piece adjacency AB / AC / BC | < 5% each | 2.82% / 3.52% / 2.82% | PASS |
| Largest shared cluster | < 4 | 3 | PASS |
| Same-position overlap AB / AC / BC | < 25% each | 66.2% / 71.2% / 68.8% | FAIL |
| 2x2 window reuse | < 30% | 48% / 65% / 52% | FAIL |
| Transferable blob | < 10% | 27.5% / 30.0% / 27.5% | FAIL |
| T1 blind test | subjects 3+, distinct 4+, grid 2 or lower | Tree 2/5; B, C unnamed; distinct 2; grid 3/4/3 | FAIL |
| T2 grid visibility | verdict 2 or lower, 70%+ invisible | Not run | Not run |

**Blind test 2 (run-quarter):** Fails T1. A reads as a landscape; the tree is named at 2/5. B and C are unnamed. Distinctiveness fell from 3/5 to 2/5.

**Grid visibility 2 (run-none-v2):** Fails T2. About 44% of interior lines are invisible, as in review 1. Verdicts A 3/5, B 4/5. Run-quarter was not reviewed.

**Conclusion**

- Quarter rotation alone brings piece-level overlap under the 5% gate (7.0–9.9% down to 2.8–3.5%).
- Texture fixes do not change recognizability or distinctiveness: A is still not read as a tree, and distinctiveness fell to 2/5, though rotation may explain that drop.
- Direction A's scene set is retired as a scene design, but its lexicon and transition mechanism remain useful.
