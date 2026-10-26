# Prototype Evaluation Protocol

## 1. Purpose

Every prototype run is scored the same way, so runs and design directions can be compared. A run passes only when every check below passes. Counts assume the 8x10 layout (80 cells, 142 adjacencies per solution).

## 2. Automatic metrics and gates

From the run's `summary.md`. Check scene-level gates on the scene file before rendering:

    metapuzzle scene-metrics FILE

| Metric | Gate |
|---|---|
| Piece-level shared adjacency, per pair | < 5%; stretch 0 |
| Largest shared cluster | < 4 pieces |
| Scene-level same-position overlap, per pair | < 25% |
| 2x2 window reuse, per pair (larger of plain and rotated) | < 30% |
| Transferable blob, per pair | < 10% of cells |

## 3. Blind recognition test (T1)

Run by a fresh agent or person not told the subjects. The evaluator opens only `solution-A.png`, `solution-B.png` and `solution-C.png`.

Prompt:

> Three images, A, B and C, are made from the same pieces. Open only the three files named. For each image give: (1) first impression, in one or two sentences; (2) nameable objects, each with confidence 1-5 (5 = certain), or "unclear"; (3) composition, in plain terms; (4) artifacts: seams, rectangles, grids or unexplained shapes. Then compare: (5) mutual distinctiveness, 1-5 (1 = one picture rearranged, 5 = three unrelated pictures); (6) tile-grid score, 1-5 (1 = one continuous picture, 5 = a grid of tiles).

**Pass:** each intended subject named or closely paraphrased at confidence 3+; distinctiveness 4+; tile-grid 2 or lower.

## 4. Grid visibility review (T2)

Run by a fresh agent on all three solutions; report the worst result. An 8x10 layout has 16 interior grid lines.

Step 1, plain image (`solution-X.png`):

> Treat this as a finished artwork. Note any straight edges, rectangular blocks or abrupt colour changes that look like a regular cut pattern.

Step 2, faint-grid variant (`grid-faint/solution-X.png`), shown after step 1 is answered:

> Same image with faint interior grid lines. For each line, say whether any part was visible in the plain image, and count the invisible lines. Classify each visible edge on a line as (a) a colour or class boundary on the cut, (b) a same-texture seam, or (c) a shape cut off at the cut. Give a verdict 1-5 (1 = not perceptible at normal viewing distance, 5 = reads as a grid of tiles).

**Pass:** verdict 2 or lower, and at least 70% of lines invisible (12 of 16).

## 5. Carry-over solve test (T7)

No simulation exists yet. Use the section 2 proxies per pair: same-position overlap (the ceiling on pieces that can stay put) and transferable blob (the largest group that can move as a unit).

Manual check: a player who has finished solution A is shown the reference for B and names the groups of pieces they would keep in place. If one group holds more than 10% of pieces, the blob gate is too loose.

## 6. Recording

- `experiments/NNN-name/blind-test-N.md` and `grid-visibility-N.md`: raw answers, invisible count, classified edges, pass or fail per criterion.
- Scorecard: one table in the experiment README (or `NOTES.md` where there is none).

| Check | Gate | Value | Result |
|---|---|---|---|
| Piece adjacency AB / AC / BC | < 5% each | | |
| Largest shared cluster | < 4 | | |
| Same-position overlap AB / AC / BC | < 25% each | | |
| 2x2 window reuse | < 30% | | |
| Transferable blob | < 10% | | |
| T1 blind test | subjects 3+, distinct 4+, grid 2 or lower | | |
| T2 grid visibility | verdict 2 or lower, 70%+ invisible | | |

Record failures too. Use a new N rather than overwriting a result.
