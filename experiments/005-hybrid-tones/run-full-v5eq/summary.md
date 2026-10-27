# Prototype summary

## Parameters

- scenes: /home/user/metapuzzle/experiments/005-hybrid-tones/scenes-v5eq.txt
- classes: /home/user/metapuzzle/experiments/005-hybrid-tones/classes-v4.json
- sizes: 20x25, 20x25, 20x25
- border: standard
- rotation: quarter
- extra_flat: 0
- mating_weight: 0.0
- max_shared_fraction: None
- seed: 0
- iters: 300000
- iters_used: 474
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

Total shared: 0; cluster penalty: 0; rotated pieces per solution: [362, 367, 347]

## Scene-level metrics

```text
maps (cols x rows): A 20x25, B 20x25, C 20x25
class histograms:
  A: L=301 M=86 DMs=26 MLs=18 DLs=16 D=12 MDc=10 MLc=9 LMc=8 DMc=6 DLc=3 DMp=2 MLp=2 LDc=1
  B: L=301 M=86 DMs=26 MLs=18 DLs=16 D=12 MDc=10 MLc=9 LMc=8 DMc=6 DLc=3 DMp=2 MLp=2 LDc=1
  C: L=301 M=86 DMs=26 MLs=18 DLs=16 D=12 MDc=10 MLc=9 LMc=8 DMc=6 DLc=3 DMp=2 MLp=2 LDc=1
largest same-class blob per class:
  A: L=297 M=81 D=6 DLs=5 DMs=5 MLs=5 LMc=2 MDc=2 MLc=2 DLc=1 DMc=1 DMp=1 LDc=1 MLp=1
  B: L=299 M=67 DLs=14 D=11 DMs=7 MLs=6 MDc=3 DLc=2 LMc=2 MLc=2 DMc=1 DMp=1 LDc=1 MLp=1
  C: L=300 M=43 D=11 MLs=10 DLs=9 DMs=7 DMc=2 LMc=2 MLc=2 DLc=1 DMp=1 LDc=1 MDc=1 MLp=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 326 (65.2%)
    same position excl. dominant L (covers 60.2% of cells, gated): 69 (44.5%)
    weighted overlap: 13.7%
    window reuse: 1x2 0.90/0.97  2x1 0.95/0.99  2x2 0.71/0.84  3x3 0.54/0.59
    transferable blob: 255 cells (51.0% of A)
  A-C: same position 342 (68.4%)
    same position excl. dominant L (covers 60.2% of cells, gated): 81 (50.9%)
    weighted overlap: 17.0%
    window reuse: 1x2 0.95/0.99  2x1 0.96/0.98  2x2 0.78/0.85  3x3 0.58/0.62
    transferable blob: 257 cells (51.4% of A)
  B-C: same position 335 (67.0%)
    same position excl. dominant L (covers 60.2% of cells, gated): 73 (45.6%)
    weighted overlap: 15.4%
    window reuse: 1x2 0.94/0.97  2x1 0.95/0.99  2x2 0.76/0.84  3x3 0.56/0.62
    transferable blob: 261 cells (52.2% of B)
scene gates: FAIL (A-B same-position excl. L 44.5% ≥ 25%; A-B 2x2 window reuse 70.8% ≥ 30%; A-B transferable blob 51.0% ≥ 10% of cells; A-C same-position excl. L 50.9% ≥ 25%; A-C 2x2 window reuse 78.3% ≥ 30%; A-C transferable blob 51.4% ≥ 10% of cells; B-C same-position excl. L 45.6% ≥ 25%; B-C 2x2 window reuse 75.7% ≥ 30%; B-C transferable blob 52.2% ≥ 10% of cells)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B same-position excl. L 44.5% ≥ 25%; A-B 2x2 window reuse 70.8% ≥ 30%; A-B transferable blob 51.0% ≥ 10% of cells; A-C same-position excl. L 50.9% ≥ 25%; A-C 2x2 window reuse 78.3% ≥ 30%; A-C transferable blob 51.4% ≥ 10% of cells; B-C same-position excl. L 45.6% ≥ 25%; B-C 2x2 window reuse 75.7% ≥ 30%; B-C transferable blob 52.2% ≥ 10% of cells)

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
