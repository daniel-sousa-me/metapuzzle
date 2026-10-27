# 001: adjacency baseline

Question: how many adjacencies do the three solutions share after optimization, per board, border and rotation mode (no class maps)?
Result: 0/0/0 shared in every configuration (seed 0, under 0.5 s each); random starts share 6 to 16 pairs, which this table does not show.
Setup: `solve` with seed 0 and default iterations (300k, early stop at zero). Sizes are cols x rows. Reproduce with `python3 experiments/001-adjacency-baseline/run.py`. The solution JSON of each seed-0 run is in this folder (`<size>-<border>-<rotation>.json`).

| Board (cols x rows) | Border | Rotation | Shared AB/AC/BC | Iterations (seed 0) | Wall time s | Mean iterations, 5 seeds | Mean time s, 5 seeds |
|---|---|---|---|---|---|---|---|
| 10x8 | standard | none | 0/0/0 | 51933 | 0.42 | 18840 | 0.16 |
| 10x8 | standard | quarter | 0/0/0 | 347 | 0.01 | 264 | 0.01 |
| 10x8 | tray | none | 0/0/0 | 75 | <0.01 | 72 | <0.01 |
| 10x8 | tray | quarter | 0/0/0 | 67 | <0.01 | 74 | <0.01 |
| 25x20 | standard | none | 0/0/0 | 2226 | 0.04 | 3423 | 0.05 |
| 25x20 | standard | quarter | 0/0/0 | 175 | 0.02 | 208 | 0.02 |
| 25x20 | tray | none | 0/0/0 | 81 | 0.01 | 87 | 0.01 |
| 25x20 | tray | quarter | 0/0/0 | 108 | 0.01 | 89 | 0.01 |
| mixed 96: 8x12, 12x8, 16x6 | standard | none | 0/0/0 | 983 | 0.01 | 768 | 0.01 |
| mixed 96: 8x12, 12x8, 16x6 | standard | quarter | 0/0/0 | 150 | <0.01 | 177 | 0.01 |

Extra check (not in the table): 12x7 standard, no rotation reaches only 2/0/2 after 300k iterations (the design doc predicts a floor above zero from the 7-piece sides); adding 4 extra flat-sided pieces gives 0/0/0 in 9320 iterations, and quarter rotation gives 0/0/0 in 334.

Interpretation:
1. Every configuration reached 0/0/0 within the default iterations, so zero shared adjacency is not the binding constraint, as docs/design/05 predicted.
2. The only slow case is 10x8 standard without rotation (about 19k iterations, 0.16 s): the border is 40% of the pieces and each side is permuted in place. Larger boards are easier (25x20 needs about 3k).
3. Tray and quarter rotation remove the border lock and finish in under 400 iterations, but a swap-only baseline cannot say whether that freedom is worth the artwork cost.
4. Mixed aspect ratios (8x12, 12x8, 16x6) are also solved at 0/0/0, because surplus flat-sided pieces sit inside the smaller frames as flat-flat seams; the 12x7 check shows that flat extras or rotation are what remove the side-length floor.
5. Random starts share about 6 to 16 pairs each, which this table does not show; the next experiment should score the visual objectives rather than adjacency alone.
