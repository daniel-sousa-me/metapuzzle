# Prototype summary

## Parameters

- scenes: /home/user/metapuzzle/experiments/013-scale/g32x48/scenes.txt
- classes: /home/user/metapuzzle/experiments/005-hybrid-tones/classes-ink.json
- sizes: 32x48, 32x48, 32x48
- border: standard
- rotation: quarter
- extra_flat: 0
- mating_weight: 0.0
- max_shared_fraction: None
- seed: 0
- iters: 300000
- iters_used: 424
- cell: 17
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

Total shared: 0; cluster penalty: 0; rotated pieces per solution: [1107, 1121, 1100]

## Scene-level metrics

```text
maps (cols x rows): A 32x48, B 32x48, C 32x48
class histograms:
  A: L=939 M=257 D=116 DLs=65 DMs=54 MLs=25 LDc=19 DLc=14 MLc=14 MDc=13 LMc=7 DMc=6 DLp=3 DMp=2 MLp=2
  B: L=939 M=257 D=116 DLs=65 DMs=54 MLs=25 LDc=19 DLc=14 MLc=14 MDc=13 LMc=7 DMc=6 DLp=3 DMp=2 MLp=2
  C: L=939 M=257 D=116 DLs=65 DMs=54 MLs=25 LDc=19 DLc=14 MLc=14 MDc=13 LMc=7 DMc=6 DLp=3 DMp=2 MLp=2
largest same-class blob per class:
  A: L=939 M=257 D=114 MLs=12 DLs=10 DMs=5 DLc=2 LDc=2 DLp=1 DMc=1 DMp=1 LMc=1 MDc=1 MLc=1 MLp=1
  B: L=939 M=169 D=115 DLs=31 DMs=26 MLs=11 DMp=2 LDc=2 DLc=1 DLp=1 DMc=1 LMc=1 MDc=1 MLc=1 MLp=1
  C: L=939 M=131 D=84 DMs=23 DLs=12 MLs=12 DLc=1 DLp=1 DMc=1 DMp=1 LDc=1 LMc=1 MDc=1 MLc=1 MLp=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 978 (63.7%)
    same position excl. dominant L (covers 61.1% of cells, gated): 182 (40.1%)
    weighted overlap: 12.3%
    window reuse: 1x2 0.95/0.97  2x1 0.89/0.97  2x2 0.69/0.79  3x3 0.50/0.56
    transferable blob: 794 cells (51.7% of A)
  A-C: same position 1094 (71.2%)
    same position excl. dominant L (covers 61.1% of cells, gated): 271 (56.3%)
    weighted overlap: 17.1%
    window reuse: 1x2 0.98/0.98  2x1 0.97/0.99  2x2 0.88/0.92  3x3 0.64/0.67
    transferable blob: 823 cells (53.6% of A)
  B-C: same position 971 (63.2%)
    same position excl. dominant L (covers 61.1% of cells, gated): 168 (36.4%)
    weighted overlap: 11.5%
    window reuse: 1x2 0.96/0.98  2x1 0.95/0.98  2x2 0.87/0.94  3x3 0.64/0.74
    transferable blob: 803 cells (52.3% of B)
scene gates: FAIL (A-B same-position excl. L 40.1% ≥ 25%; A-B 2x2 window reuse 69.0% ≥ 30%; A-B transferable blob 51.7% ≥ 10% of cells; A-C same-position excl. L 56.3% ≥ 25%; A-C 2x2 window reuse 88.3% ≥ 30%; A-C transferable blob 53.6% ≥ 10% of cells; B-C same-position excl. L 36.4% ≥ 25%; B-C 2x2 window reuse 87.3% ≥ 30%; B-C transferable blob 52.3% ≥ 10% of cells)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B same-position excl. L 40.1% ≥ 25%; A-B 2x2 window reuse 69.0% ≥ 30%; A-B transferable blob 51.7% ≥ 10% of cells; A-C same-position excl. L 56.3% ≥ 25%; A-C 2x2 window reuse 88.3% ≥ 30%; A-C transferable blob 53.6% ≥ 10% of cells; B-C same-position excl. L 36.4% ≥ 25%; B-C 2x2 window reuse 87.3% ≥ 30%; B-C transferable blob 52.3% ≥ 10% of cells)

## Connectors

Mating classes: sides forced to share one connector shape (a contact in any solution is an edge). The smallest possible class is K(3,3), 6 sides, for tab/blank (K4, 4 sides, for andro). False fits are tab-blank pairs inside a class that touch in no solution; ratio = false fits / intended contacts.

```text
non-flat sides: 5984  profiles: andro=5984
mating classes: 2
class size min / median / max: 312 / 2992 / 5672
tabs per class min / median / max: 0 / 0 / 0
blanks per class min / median / max: 0 / 0 / 0
largest class: 5672 sides (94.8% of sides), 0 tabs, 0 blanks, 5672 other
false fits: 16114060 of 8976 intended contacts (ratio 1795.238)
contacts: 8976 edges, 0 flat contacts, 0 mismatched
edge identity (edges = intended - flat): OK
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
