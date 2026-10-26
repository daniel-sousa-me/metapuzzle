# Experiment 002: Direction A, first end-to-end render

## Goal

First end-to-end render of design direction A ("Dapple Mosaic") with its three scenes: The Lone Tree (A), Isle and Sail (B), Snow Peak (C). Board is 8x10 (80 pieces), no rotation, standard border.

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
