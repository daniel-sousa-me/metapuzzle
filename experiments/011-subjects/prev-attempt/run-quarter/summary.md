# Prototype summary

## Parameters

- scenes: experiments/011-subjects/scenes.txt
- classes: experiments/005-hybrid-tones/classes.json
- sizes: 20x25, 20x25, 20x25
- border: tray
- rotation: quarter
- extra_flat: 0
- seed: 0
- iters: 300000
- iters_used: 261
- cell: 32
- grid: none
- labels: False
- interior seams (A / B / C): 0 / 0 / 0
- valid: yes

## Piece-level shared adjacencies

Adjacency = two pieces touching in a solution (flat seams included). Shared = touching in both solutions of the pair.

| pair | shared | fraction | clusters (3+) | largest component | familiar pieces | max familiarity | mean familiarity |
|---|---|---|---|---|---|---|---|
| AB | 0 | 0.00% | - | 0 | 0 | 0 | 0.000 |
| AC | 0 | 0.00% | - | 0 | 0 | 0 | 0.000 |
| BC | 0 | 0.00% | - | 0 | 0 | 0 | 0.000 |

Total shared: 0; cluster penalty: 0; rotated pieces per solution: [427, 434, 419]

## Scene-level metrics

```text
maps (cols x rows): A 20x25, B 20x25, C 20x25
class histograms:
  A: M=73 L=69 D=63 DL=61 LD=59 DM=47 ML=47 LM=43 MD=38
  B: M=73 L=69 D=63 DL=61 LD=59 DM=47 ML=47 LM=43 MD=38
  C: M=73 L=69 D=63 DL=61 LD=59 DM=47 ML=47 LM=43 MD=38
largest same-class blob per class:
  A: M=62 L=32 D=18 DM=17 ML=15 LM=9 DL=6 LD=6 MD=6
  B: L=50 D=34 M=28 DL=16 MD=12 LD=11 DM=9 LM=9 ML=7
  C: M=67 L=56 MD=22 D=17 LD=17 ML=14 DL=11 LM=11 DM=5
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 44 (8.8%)
    same position excl. dominant M (covers 14.6% of cells, not gated): 40 (11.2%)
    weighted overlap: 9.0%
    window reuse: 1x2 0.99/0.99  2x1 0.99/0.99  2x2 0.65/0.82  3x3 0.12/0.26
    transferable blob: 22 cells (4.4% of A)
  A-C: same position 14 (2.8%)
    same position excl. dominant M (covers 14.6% of cells, not gated): 9 (2.5%)
    weighted overlap: 2.5%
    window reuse: 1x2 0.97/0.97  2x1 0.96/0.98  2x2 0.65/0.77  3x3 0.11/0.20
    transferable blob: 42 cells (8.4% of A)
  B-C: same position 29 (5.8%)
    same position excl. dominant M (covers 14.6% of cells, not gated): 29 (8.2%)
    weighted overlap: 6.5%
    window reuse: 1x2 0.96/0.98  2x1 0.97/0.98  2x2 0.66/0.86  3x3 0.10/0.27
    transferable blob: 39 cells (7.8% of B)
scene gates: FAIL (A-B 2x2 window reuse 64.7% ≥ 30%; A-C 2x2 window reuse 64.9% ≥ 30%; B-C 2x2 window reuse 66.2% ≥ 30%)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B 2x2 window reuse 64.7% ≥ 30%; A-C 2x2 window reuse 64.9% ≥ 30%; B-C 2x2 window reuse 66.2% ≥ 30%)

## Files

- `grid-faint/solution-A.png`
- `grid-faint/solution-B.png`
- `grid-faint/solution-C.png`
- `metrics.txt`
- `scene-metrics.txt`
- `solution-A.png`
- `solution-A.svg`
- `solution-B.png`
- `solution-B.svg`
- `solution-C.png`
- `solution-C.svg`
- `solution-pieces.png`
- `solution.json`
- `triptych-grid.png`
- `triptych.png`
- `summary.md` (this file)
