# Prototype summary

## Parameters

- scenes: experiments/004-density-fields/scenes.txt
- classes: experiments/004-density-fields/classes.json
- sizes: 20x25, 20x25, 20x25
- border: standard
- rotation: none
- seed: 0
- iters: 300000
- iters_used: 300000
- cell: 32
- grid: none
- labels: False
- valid: yes

## Piece-level shared adjacencies

Adjacency = two pieces touching in a solution (flat seams included). Shared = touching in both solutions of the pair.

| pair | shared | fraction | clusters (3+) | largest component | familiar pieces | max familiarity | mean familiarity |
|---|---|---|---|---|---|---|---|
| AB | 0 | 0.00% | - | 0 | 0 | 0 | 0.000 |
| AC | 1 | 0.10% | - | 2 | 2 | 1 | 0.004 |
| BC | 0 | 0.00% | - | 0 | 0 | 0 | 0.000 |

Total shared: 1; cluster penalty: 0; rotated pieces per solution: [0, 0, 0]

## Scene-level metrics

```text
maps (cols x rows): A 20x25, B 20x25, C 20x25
class histograms:
  A: T2=100 T3=100 T1=90 T4=90 T0=60 T5=60
  B: T2=100 T3=100 T1=90 T4=90 T0=60 T5=60
  C: T2=100 T3=100 T1=90 T4=90 T0=60 T5=60
largest same-class blob per class:
  A: T0=36 T1=15 T3=10 T4=7 T2=4 T5=4
  B: T0=51 T3=40 T5=37 T1=33 T2=21 T4=16
  C: T1=74 T2=65 T0=15 T3=14 T4=11 T5=7
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 116 (23.2%)
    window reuse: 1x2 0.97/1.00  2x1 1.00/1.00  2x2 0.44/0.68  3x3 0.00/0.02
    transferable blob: 23 cells (4.6% of A)
  A-C: same position 125 (25.0%)
    window reuse: 1x2 0.99/1.00  2x1 0.98/1.00  2x2 0.57/0.76  3x3 0.01/0.05
    transferable blob: 12 cells (2.4% of A)
  B-C: same position 85 (17.0%)
    window reuse: 1x2 1.00/1.00  2x1 0.97/1.00  2x2 0.80/0.90  3x3 0.01/0.05
    transferable blob: 20 cells (4.0% of B)
scene gates: FAIL (A-B 2x2 window reuse 44.1% ≥ 30%; A-C same-position 25.0% ≥ 25%; A-C 2x2 window reuse 57.2% ≥ 30%; B-C 2x2 window reuse 79.6% ≥ 30%)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B 2x2 window reuse 44.1% ≥ 30%; A-C same-position 25.0% ≥ 25%; A-C 2x2 window reuse 57.2% ≥ 30%; B-C 2x2 window reuse 79.6% ≥ 30%)

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
