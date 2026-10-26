# Prototype summary

## Parameters

- scenes: docs/design/alt-b/scenes-8x10-b.txt
- classes: experiments/006-direction-b/classes.json
- sizes: 8x10, 8x10, 8x10
- border: standard
- rotation: quarter
- seed: 0
- iters: 300000
- iters_used: 300000
- cell: 48
- grid: none
- labels: False
- valid: yes

## Piece-level shared adjacencies

Adjacency = two pieces touching in a solution (flat seams included). Shared = touching in both solutions of the pair.

| pair | shared | fraction | clusters (3+) | largest component | familiar pieces | max familiarity | mean familiarity |
|---|---|---|---|---|---|---|---|
| AB | 1 | 0.70% | - | 2 | 2 | 1 | 0.025 |
| AC | 0 | 0.00% | - | 0 | 0 | 0 | 0.000 |
| BC | 0 | 0.00% | - | 0 | 0 | 0 | 0.000 |

Total shared: 1; cluster penalty: 0; rotated pieces per solution: [48, 50, 53]

## Scene-level metrics

```text
maps (cols x rows): A 8x10, B 8x10, C 8x10
class histograms:
  A: BL=12 TE=11 NT=10 OC=9 GT=7 GB=6 GD=5 CR=4 CB=3 DK=3 DT=3 GR=3 OG=3 SU=1
  B: BL=12 TE=11 NT=10 OC=9 GT=7 GB=6 GD=5 CR=4 CB=3 DK=3 DT=3 GR=3 OG=3 SU=1
  C: BL=12 TE=11 NT=10 OC=9 GT=7 GB=6 GD=5 CR=4 CB=3 DK=3 DT=3 GR=3 OG=3 SU=1
largest same-class blob per class:
  A: OC=9 TE=8 BL=4 GT=4 NT=4 DT=2 GB=2 GD=2 GR=2 CB=1 CR=1 DK=1 OG=1 SU=1
  B: OC=9 GT=7 TE=5 BL=4 DK=2 GB=2 GD=2 NT=2 OG=2 CB=1 CR=1 DT=1 GR=1 SU=1
  C: OC=5 BL=4 NT=2 OG=2 TE=2 CB=1 CR=1 DK=1 DT=1 GB=1 GD=1 GR=1 GT=1 SU=1
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 11 (13.8%)
    window reuse: 1x2 0.67/0.79  2x1 0.56/0.74  2x2 0.16/0.27  3x3 0.00/0.00
    transferable blob: 6 cells (7.5% of A)
  A-C: same position 7 (8.8%)
    window reuse: 1x2 0.57/0.73  2x1 0.44/0.76  2x2 0.02/0.03  3x3 0.00/0.00
    transferable blob: 5 cells (6.2% of A)
  B-C: same position 7 (8.8%)
    window reuse: 1x2 0.63/0.79  2x1 0.43/0.81  2x2 0.03/0.06  3x3 0.00/0.00
    transferable blob: 4 cells (5.0% of B)
scene gates: PASS
```

## Gates

- piece gates: PASS
- scene gates: PASS

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
