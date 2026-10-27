# Prototype summary

## Parameters

- scenes: /home/user/metapuzzle/experiments/013-scale/g25x30/scenes.txt
- classes: /home/user/metapuzzle/experiments/005-hybrid-tones/classes-v4.json
- sizes: 25x30, 25x30, 25x30
- border: standard
- rotation: quarter
- extra_flat: 0
- mating_weight: 0.0
- max_shared_fraction: None
- seed: 0
- iters: 300000
- iters_used: 444
- cell: 27
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

Total shared: 0; cluster penalty: 0; rotated pieces per solution: [556, 525, 542]

## Scene-level metrics

```text
maps (cols x rows): A 25x30, B 25x30, C 25x30
class histograms:
  A: L=448 M=115 D=53 DLs=35 DMs=29 MLs=18 LDc=13 DLc=11 LMc=9 MLc=8 DMc=4 MDc=4 MLp=2 DLp=1
  B: L=448 M=115 D=53 DLs=35 DMs=29 MLs=18 LDc=13 DLc=11 LMc=9 MLc=8 DMc=4 MDc=4 MLp=2 DLp=1
  C: L=448 M=115 D=53 DLs=35 DMs=29 MLs=18 LDc=13 DLc=11 LMc=9 MLc=8 DMc=4 MDc=4 MLp=2 DLp=1
largest same-class blob per class:
  A: L=441 M=115 D=52 MLs=8 DLs=6 DMs=4 DLc=3 DMc=2 LDc=2 MDc=2 DLp=1 LMc=1 MLc=1 MLp=1
  B: L=447 M=75 D=52 DMs=19 DLs=17 MLs=3 DLc=1 DLp=1 DMc=1 LDc=1 LMc=1 MDc=1 MLc=1 MLp=1
  C: L=448 M=60 D=52 DMs=13 MLs=9 DLs=7 DLc=1 DLp=1 DMc=1 LDc=1 LMc=1 MDc=1 MLc=1 MLp=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 445 (59.3%)
    same position excl. dominant L (covers 59.7% of cells, gated): 81 (37.2%)
    weighted overlap: 12.5%
    window reuse: 1x2 0.91/0.95  2x1 0.92/0.96  2x2 0.64/0.74  3x3 0.39/0.47
    transferable blob: 364 cells (48.5% of A)
  A-C: same position 496 (66.1%)
    same position excl. dominant L (covers 59.7% of cells, gated): 117 (50.2%)
    weighted overlap: 17.5%
    window reuse: 1x2 0.95/0.97  2x1 0.96/0.97  2x2 0.86/0.89  3x3 0.58/0.61
    transferable blob: 372 cells (49.6% of A)
  B-C: same position 438 (58.4%)
    same position excl. dominant L (covers 59.7% of cells, gated): 71 (32.1%)
    weighted overlap: 12.0%
    window reuse: 1x2 0.90/0.94  2x1 0.92/0.96  2x2 0.72/0.88  3x3 0.44/0.54
    transferable blob: 367 cells (48.9% of B)
scene gates: FAIL (A-B same-position excl. L 37.2% ≥ 25%; A-B 2x2 window reuse 64.1% ≥ 30%; A-B transferable blob 48.5% ≥ 10% of cells; A-C same-position excl. L 50.2% ≥ 25%; A-C 2x2 window reuse 86.5% ≥ 30%; A-C transferable blob 49.6% ≥ 10% of cells; B-C same-position excl. L 32.1% ≥ 25%; B-C 2x2 window reuse 72.0% ≥ 30%; B-C transferable blob 48.9% ≥ 10% of cells)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B same-position excl. L 37.2% ≥ 25%; A-B 2x2 window reuse 64.1% ≥ 30%; A-B transferable blob 48.5% ≥ 10% of cells; A-C same-position excl. L 50.2% ≥ 25%; A-C 2x2 window reuse 86.5% ≥ 30%; A-C transferable blob 49.6% ≥ 10% of cells; B-C same-position excl. L 32.1% ≥ 25%; B-C 2x2 window reuse 72.0% ≥ 30%; B-C transferable blob 48.9% ≥ 10% of cells)

## Connectors

Mating classes: sides forced to share one connector shape (a contact in any solution is an edge). The smallest possible class is K(3,3), 6 sides, for tab/blank (K4, 4 sides, for andro). False fits are tab-blank pairs inside a class that touch in no solution; ratio = false fits / intended contacts.

```text
non-flat sides: 2890  profiles: andro=2890
mating classes: 2
class size min / median / max: 212 / 1445 / 2678
tabs per class min / median / max: 0 / 0 / 0
blanks per class min / median / max: 0 / 0 / 0
largest class: 2678 sides (92.7% of sides), 0 tabs, 0 blanks, 2678 other
false fits: 3598564 of 4335 intended contacts (ratio 830.119)
contacts: 4335 edges, 0 flat contacts, 0 mismatched
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
