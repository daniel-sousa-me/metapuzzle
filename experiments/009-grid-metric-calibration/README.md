# 009 Grid metric calibration

Automatic grid visibility: `metapuzzle grid-metric RUN_DIR` (`src/metapuzzle/grid_metric.py`).

Method, as implemented: the metric reads `solution-{A,B,C}.png` (no grid overlay), cell size from
`summary.md`, board sizes from `solution.json`, and margin 8 px (render.py default; not recorded in
run folders). Each interior edge segment is compared by CIE76 colour difference between the 3 px
strips on either side, averaged along the edge. A segment is visible when that contrast exceeds
2x the median within-cell contrast (middle lines, same orientation). Score bands on the visible
fraction: <=0.15 -> 1, <=0.30 -> 2, <=0.50 -> 3, <=0.70 -> 4, above -> 5.

## Human verdicts

Grid visibility, 1 = invisible, 5 = strong. The human mean is over every recorded grid score for the run.

| run | sources and scores | human mean |
|---|---|---|
| 002 run-none | grid-visibility-1: A 3, C 4; blind-test-1 ("tile-grid score"): A 1, B 4, C 3 | 3.0 |
| 002 run-none-v2 | grid-visibility-2: A 3, B 4 | 3.5 |
| 006 run-quarter | grid-visibility-1: A 3, C 5; blind-test-1: A 3, B 4, C 5 | 4.0 |
| 004 run-quarter | blind-test-1: A 5, B 5, C 5 | 5.0 |

Two sources disagree for 002 run-none (A scored 3 in grid-visibility-1 and 1 in blind-test-1). Both are kept.

## Metric

| run | visible A / B / C | line fraction A / B / C | score A / B / C | mean visible | within-cell median (A, v / h), dE |
|---|---|---|---|---|---|
| 002 run-none | 0.648 / 0.634 / 0.627 | 0.625 / 0.562 / 0.625 | 4 / 4 / 4 | 0.636 | 1.0 / 1.2 |
| 002 run-none-v2 | 0.599 / 0.613 / 0.606 | 0.562 / 0.562 / 0.625 | 4 / 4 / 4 | 0.606 | 3.5 / 3.1 |
| 006 run-quarter | 0.535 / 0.563 / 0.725 | 0.500 / 0.500 / 0.938 | 4 / 4 / 5 | 0.608 | 9.7 / 10.6 |
| 004 run-quarter | 0.523 / 0.360 / 0.417 | 0.558 / 0.186 / 0.349 | 4 / 3 / 3 | 0.433 | 10.1 / 10.4 |

## Ordering

- Humans: 004 (5.0) > 006 (4.0) > 002 v2 (3.5) > 002 v1 (3.0).
- Metric (mean visible): 002 v1 (0.636) > 006 (0.608) ~ 002 v2 (0.606) > 004 (0.433).

The metric does not order the runs like the humans did. Of the six pairs, one agrees (006 over 002 v2),
and that pair differs by 0.002. The metric ranks 004 last, while humans ranked it first.

## Threshold check (not adopted)

Mean visible fraction when the visibility ratio is changed (the specified rule is 2.0):

| ratio | 002 v1 | 002 v2 | 006 | 004 |
|---|---|---|---|---|
| 1.0 | 0.791 | 0.955 | 0.906 | 0.854 |
| 1.5 | 0.718 | 0.789 | 0.721 | 0.613 |
| 2.0 (specified) | 0.636 | 0.606 | 0.608 | 0.433 |
| 3.0 | 0.526 | 0.415 | 0.462 | 0.221 |

No ratio puts 004 first. The score bands are monotone in the visible fraction, so they cannot change the
order either. The thresholds were therefore left as specified.

## Diagnosis

- 004 pieces carry dense speckle inside each piece. The within-cell median (about 10 dE) is set by the
  speckle, so a 2x rule needs steps of about 20 dE. Most of the colour steps between its blocks are smaller.
- 002 v1 pieces are nearly flat (median about 1 dE), so sub-perceptual differences between similar sky and
  foliage colours count as visible.
- Scratch check, not in the module: comparing the whole-edge mean colour instead of per-row contrast drops
  004's reference to about 3 dE. Adding a 5 dE absolute floor gives 002 at 0.36 to 0.43, 006 at 0.71 and
  004 at 0.66. That puts 002 last, as the humans did, but 004 still falls below 006. This changes the
  statistic and is fitted to four runs, so it is recorded here as a lead only.

## Conclusion

The metric is not yet a valid stand-in for the human verdict and should not gate designs. Next steps: collect
more human verdicts on more runs with the same protocol, then choose the statistic (per-row or whole-edge,
with or without a perceptual floor) against that larger set.

## Reproduce

    metapuzzle grid-metric experiments/002-direction-a/run-none
    metapuzzle grid-metric experiments/002-direction-a/run-none-v2
    metapuzzle grid-metric experiments/006-direction-b/run-quarter
    metapuzzle grid-metric experiments/004-density-fields/run-quarter
