# Prototype summary

## Parameters

- scenes: /home/user/metapuzzle/experiments/008-mixed-frames/scenes.txt
- classes: /home/user/metapuzzle/experiments/008-mixed-frames/classes.json
- sizes: 20x24, 30x16, 40x12
- border: standard
- rotation: none
- seed: 0
- iters: 300000
- iters_used: 300000
- cell: 24
- grid: none
- labels: False
- valid: no (41 violation(s))
  - violation: A: pieces 21 and 88 touch with sides that do not mate
  - violation: A: pieces 7 and 120 touch with sides that do not mate
  - violation: A: pieces 5 and 18 touch with sides that do not mate
  - violation: A: pieces 182 and 130 touch with sides that do not mate
  - violation: A: pieces 180 and 289 touch with sides that do not mate

## Piece-level shared adjacencies

Adjacency = two pieces touching in a solution (flat seams included). Shared = touching in both solutions of the pair.

| pair | shared | fraction | clusters (3+) | largest component | familiar pieces | max familiarity | mean familiarity |
|---|---|---|---|---|---|---|---|
| AB | 0 | 0.00% | - | 0 | 0 | 0 | 0.000 |
| AC | 0 | 0.00% | - | 0 | 0 | 0 | 0.000 |
| BC | 0 | 0.00% | - | 0 | 0 | 0 | 0.000 |

Total shared: 0; cluster penalty: 0; rotated pieces per solution: [0, 0, 0]

## Scene-level metrics

```text
maps (cols x rows): A 20x24, B 30x16, C 40x12
class histograms:
  A: T2=96 T3=96 T1=86 T4=86 T0=58 T5=58
  B: T2=96 T3=96 T1=86 T4=86 T0=58 T5=58
  C: T2=96 T3=96 T1=86 T4=86 T0=58 T5=58
largest same-class blob per class:
  A: T1=62 T2=56 T0=14 T4=11 T3=8 T5=7
  B: T0=37 T5=26 T1=24 T3=17 T2=15 T4=11
  C: T5=19 T4=16 T3=15 T1=13 T2=11 T0=5
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position n/a (shapes differ)
    window reuse: 1x2 0.96/1.00  2x1 1.00/1.00  2x2 0.61/0.84  3x3 0.02/0.02
    transferable blob: 15 cells (3.1% of A)
  A-C: same position n/a (shapes differ)
    window reuse: 1x2 0.93/0.98  2x1 0.95/0.99  2x2 0.72/0.83  3x3 0.00/0.01
    transferable blob: 11 cells (2.3% of A)
  B-C: same position n/a (shapes differ)
    window reuse: 1x2 0.95/1.00  2x1 0.93/0.96  2x2 0.74/0.81  3x3 0.03/0.05
    transferable blob: 18 cells (3.8% of B)
scene gates: FAIL (A-B 2x2 window reuse 60.6% ≥ 30%; A-C 2x2 window reuse 71.6% ≥ 30%; B-C 2x2 window reuse 73.6% ≥ 30%)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B 2x2 window reuse 60.6% ≥ 30%; A-C 2x2 window reuse 71.6% ≥ 30%; B-C 2x2 window reuse 73.6% ≥ 30%)

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
