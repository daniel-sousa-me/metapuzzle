# Prototype summary

## Parameters

- scenes: docs/design/scenes-8x10.txt
- classes: experiments/002-direction-a/classes.json
- sizes: 8x10, 8x10, 8x10
- border: standard
- rotation: none
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
| AB | 13 | 9.15% | [6, 3] | 6 | 21 | 2 | 0.325 |
| AC | 11 | 7.75% | [3, 3, 3] | 3 | 19 | 2 | 0.275 |
| BC | 15 | 10.56% | [6, 3, 3] | 6 | 24 | 2 | 0.375 |

Total shared: 39; cluster penalty: 30; rotated pieces per solution: [0, 0, 0]

## Scene-level metrics

```text
maps (cols x rows): A 8x10, B 8x10, C 8x10
class histograms:
  A: ME=24 SK=21 DP=10 FO=9 F/=2 F\=2 HD=2 RU=2 S/=2 HB=1 HL=1 PH=1 SN=1 SU=1 S\=1
  B: ME=24 SK=21 DP=10 FO=9 F/=2 F\=2 HD=2 RU=2 S/=2 HB=1 HL=1 PH=1 SN=1 SU=1 S\=1
  C: ME=24 SK=21 DP=10 FO=9 F/=2 F\=2 HD=2 RU=2 S/=2 HB=1 HL=1 PH=1 SN=1 SU=1 S\=1
largest same-class blob per class:
  A: ME=24 SK=21 DP=6 FO=4 F/=1 F\=1 HB=1 HD=1 HL=1 PH=1 RU=1 S/=1 SN=1 SU=1 S\=1
  B: ME=24 SK=21 DP=8 FO=5 F/=1 F\=1 HB=1 HD=1 HL=1 PH=1 RU=1 S/=1 SN=1 SU=1 S\=1
  C: ME=24 SK=21 DP=10 FO=3 F/=1 F\=1 HB=1 HD=1 HL=1 PH=1 RU=1 S/=1 SN=1 SU=1 S\=1
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 53 (66.2%)
    window reuse: 1x2 0.87/0.93  2x1 0.83/0.92  2x2 0.44/0.48  3x3 0.15/0.15
    transferable blob: 22 cells (27.5% of A)
  A-C: same position 57 (71.2%)
    window reuse: 1x2 0.84/0.96  2x1 0.82/0.92  2x2 0.57/0.65  3x3 0.29/0.29
    transferable blob: 24 cells (30.0% of A)
  B-C: same position 55 (68.8%)
    window reuse: 1x2 0.81/0.97  2x1 0.90/0.93  2x2 0.51/0.52  3x3 0.04/0.04
    transferable blob: 22 cells (27.5% of B)
```

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
