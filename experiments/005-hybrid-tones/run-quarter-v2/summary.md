# Prototype summary

## Parameters

- scenes: experiments/005-hybrid-tones/scenes.txt
- classes: experiments/005-hybrid-tones/classes.json
- sizes: 20x25, 20x25, 20x25
- border: standard
- rotation: quarter
- seed: 0
- iters: 300000
- iters_used: 450
- cell: 32
- grid: none
- labels: False
- valid: yes

## Piece-level shared adjacencies

Adjacency = two pieces touching in a solution (flat seams included). Shared = touching in both solutions of the pair.

| pair | shared | fraction | clusters (3+) | largest component | familiar pieces | max familiarity | mean familiarity |
|---|---|---|---|---|---|---|---|
| AB | 0 | 0.00% | - | 0 | 0 | 0 | 0.000 |
| AC | 0 | 0.00% | - | 0 | 0 | 0 | 0.000 |
| BC | 0 | 0.00% | - | 0 | 0 | 0 | 0.000 |

Total shared: 0; cluster penalty: 0; rotated pieces per solution: [397, 389, 392]

## Scene-level metrics

```text
maps (cols x rows): A 20x25, B 20x25, C 20x25
class histograms:
  A: L=227 M=69 LM=37 LD=36 DL=31 ML=29 MD=26 DM=24 D=21
  B: L=227 M=69 LM=37 LD=36 DL=31 ML=29 MD=26 DM=24 D=21
  C: L=227 M=69 LM=37 LD=36 DL=31 ML=29 MD=26 DM=24 D=21
largest same-class blob per class:
  A: L=227 M=62 D=13 DM=10 MD=9 DL=8 LD=6 LM=6 ML=6
  B: L=227 M=68 DL=21 D=20 MD=18 LD=17 DM=14 ML=6 LM=4
  C: L=227 M=35 D=16 DL=13 ML=11 DM=9 LM=7 LD=6 MD=4
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 229 (45.8%)
    same position excl. dominant L (covers 45.4% of cells, gated): 70 (34.1%)
    weighted overlap: 25.4%
    window reuse: 1x2 0.94/0.97  2x1 0.94/0.96  2x2 0.71/0.81  3x3 0.28/0.35
    transferable blob: 156 cells (31.2% of A)
  A-C: same position 222 (44.4%)
    same position excl. dominant L (covers 45.4% of cells, gated): 63 (30.7%)
    weighted overlap: 22.3%
    window reuse: 1x2 0.99/1.00  2x1 0.99/1.00  2x2 0.75/0.85  3x3 0.36/0.44
    transferable blob: 155 cells (31.0% of A)
  B-C: same position 216 (43.2%)
    same position excl. dominant L (covers 45.4% of cells, gated): 65 (33.0%)
    weighted overlap: 21.3%
    window reuse: 1x2 0.98/0.99  2x1 0.99/0.99  2x2 0.73/0.89  3x3 0.37/0.43
    transferable blob: 128 cells (25.6% of B)
scene gates: FAIL (A-B same-position excl. L 34.1% ≥ 25%; A-B weighted overlap 25.4% ≥ 25%; A-B 2x2 window reuse 71.1% ≥ 30%; A-B transferable blob 31.2% ≥ 10% of cells; A-C same-position excl. L 30.7% ≥ 25%; A-C 2x2 window reuse 75.2% ≥ 30%; A-C transferable blob 31.0% ≥ 10% of cells; B-C same-position excl. L 33.0% ≥ 25%; B-C 2x2 window reuse 73.0% ≥ 30%; B-C transferable blob 25.6% ≥ 10% of cells)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B same-position excl. L 34.1% ≥ 25%; A-B weighted overlap 25.4% ≥ 25%; A-B 2x2 window reuse 71.1% ≥ 30%; A-B transferable blob 31.2% ≥ 10% of cells; A-C same-position excl. L 30.7% ≥ 25%; A-C 2x2 window reuse 75.2% ≥ 30%; A-C transferable blob 31.0% ≥ 10% of cells; B-C same-position excl. L 33.0% ≥ 25%; B-C 2x2 window reuse 73.0% ≥ 30%; B-C transferable blob 25.6% ≥ 10% of cells)

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
