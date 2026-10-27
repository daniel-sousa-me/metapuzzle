# Prototype summary

## Parameters

- scenes: /home/user/metapuzzle/experiments/005-hybrid-tones/scenes-v5eq2.txt
- classes: /home/user/metapuzzle/experiments/005-hybrid-tones/classes-v4.json
- sizes: 20x25, 20x25, 20x25
- border: standard
- rotation: quarter
- extra_flat: 0
- mating_weight: 0.0
- max_shared_fraction: None
- seed: 0
- iters: 300000
- iters_used: 493
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

Total shared: 0; cluster penalty: 0; rotated pieces per solution: [360, 356, 356]

## Scene-level metrics

```text
maps (cols x rows): A 20x25, B 20x25, C 20x25
class histograms:
  A: L=300 M=86 DMs=23 DLs=18 MLs=17 D=14 MLc=14 DMc=10 MDc=9 LMc=5 LDc=2 DLc=1 MLp=1
  B: L=300 M=86 DMs=23 DLs=18 MLs=17 D=14 MLc=14 DMc=10 MDc=9 LMc=5 LDc=2 DLc=1 MLp=1
  C: L=300 M=86 DMs=23 DLs=18 MLs=17 D=14 MLc=14 DMc=10 MDc=9 LMc=5 LDc=2 DLc=1 MLp=1
largest same-class blob per class:
  A: L=295 M=84 D=7 DLs=6 DMs=4 MDc=3 MLs=3 DMc=2 LMc=2 MLc=2 DLc=1 LDc=1 MLp=1
  B: L=300 M=58 DLs=15 D=13 DMs=4 MLs=4 DMc=2 MDc=2 MLc=2 DLc=1 LDc=1 LMc=1 MLp=1
  C: L=300 M=46 D=12 DLs=11 MLs=8 DMs=7 LMc=2 MLc=2 DLc=1 DMc=1 LDc=1 MDc=1 MLp=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 318 (63.6%)
    same position excl. dominant L (covers 60.0% of cells, gated): 63 (40.6%)
    weighted overlap: 14.7%
    window reuse: 1x2 0.90/0.97  2x1 0.93/0.98  2x2 0.74/0.81  3x3 0.56/0.60
    transferable blob: 255 cells (51.0% of A)
  A-C: same position 339 (67.8%)
    same position excl. dominant L (covers 60.0% of cells, gated): 81 (51.3%)
    weighted overlap: 16.9%
    window reuse: 1x2 0.90/0.97  2x1 0.95/0.98  2x2 0.73/0.80  3x3 0.56/0.59
    transferable blob: 253 cells (50.6% of A)
  B-C: same position 318 (63.6%)
    same position excl. dominant L (covers 60.0% of cells, gated): 60 (38.0%)
    weighted overlap: 14.2%
    window reuse: 1x2 0.92/0.95  2x1 0.93/0.96  2x2 0.71/0.81  3x3 0.52/0.56
    transferable blob: 258 cells (51.6% of B)
scene gates: FAIL (A-B same-position excl. L 40.6% ≥ 25%; A-B 2x2 window reuse 74.1% ≥ 30%; A-B transferable blob 51.0% ≥ 10% of cells; A-C same-position excl. L 51.3% ≥ 25%; A-C 2x2 window reuse 73.0% ≥ 30%; A-C transferable blob 50.6% ≥ 10% of cells; B-C same-position excl. L 38.0% ≥ 25%; B-C 2x2 window reuse 70.6% ≥ 30%; B-C transferable blob 51.6% ≥ 10% of cells)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B same-position excl. L 40.6% ≥ 25%; A-B 2x2 window reuse 74.1% ≥ 30%; A-B transferable blob 51.0% ≥ 10% of cells; A-C same-position excl. L 51.3% ≥ 25%; A-C 2x2 window reuse 73.0% ≥ 30%; A-C transferable blob 50.6% ≥ 10% of cells; B-C same-position excl. L 38.0% ≥ 25%; B-C 2x2 window reuse 70.6% ≥ 30%; B-C transferable blob 51.6% ≥ 10% of cells)

## Connectors

Mating classes: sides forced to share one connector shape (a contact in any solution is an edge). The smallest possible class is K(3,3), 6 sides, for tab/blank (K4, 4 sides, for andro). False fits are tab-blank pairs inside a class that touch in no solution; ratio = false fits / intended contacts.

```text
non-flat sides: 1910  profiles: andro=1910
mating classes: 2
class size min / median / max: 172 / 955 / 1738
tabs per class min / median / max: 0 / 0 / 0
blanks per class min / median / max: 0 / 0 / 0
largest class: 1738 sides (91.0% of sides), 0 tabs, 0 blanks, 1738 other
false fits: 1518724 of 2865 intended contacts (ratio 530.096)
contacts: 2865 edges, 0 flat contacts, 0 mismatched
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
