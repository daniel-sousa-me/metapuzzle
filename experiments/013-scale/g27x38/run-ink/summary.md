# Prototype summary

## Parameters

- scenes: /home/user/metapuzzle/experiments/013-scale/g27x38/scenes.txt
- classes: /home/user/metapuzzle/experiments/005-hybrid-tones/classes-ink.json
- sizes: 27x38, 27x38, 27x38
- border: standard
- rotation: quarter
- extra_flat: 0
- mating_weight: 0.0
- max_shared_fraction: None
- seed: 0
- iters: 300000
- iters_used: 451
- cell: 21
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

Total shared: 0; cluster penalty: 0; rotated pieces per solution: [769, 748, 738]

## Scene-level metrics

```text
maps (cols x rows): A 27x38, B 27x38, C 27x38
class histograms:
  A: L=619 M=177 D=78 DLs=45 DMs=27 MLs=19 DLc=15 LDc=14 MLc=11 LMc=9 DMc=5 MDc=4 DLp=2 MLp=1
  B: L=619 M=177 D=78 DLs=45 DMs=27 MLs=19 DLc=15 LDc=14 MLc=11 LMc=9 DMc=5 MDc=4 DLp=2 MLp=1
  C: L=619 M=177 D=78 DLs=45 DMs=27 MLs=19 DLc=15 LDc=14 MLc=11 LMc=9 DMc=5 MDc=4 DLp=2 MLp=1
largest same-class blob per class:
  A: L=610 M=177 D=77 MLs=9 DLs=7 DMs=4 DLc=3 LDc=2 DLp=1 DMc=1 LMc=1 MDc=1 MLc=1 MLp=1
  B: L=619 M=123 D=77 DLs=22 DMs=19 MLs=6 LDc=2 MLc=2 DLc=1 DLp=1 DMc=1 LMc=1 MDc=1 MLp=1
  C: L=619 M=89 D=71 MLs=10 DLs=9 DMs=9 DLc=1 DLp=1 DMc=1 LDc=1 LMc=1 MDc=1 MLc=1 MLp=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 636 (62.0%)
    same position excl. dominant L (covers 60.3% of cells, gated): 124 (41.3%)
    weighted overlap: 12.3%
    window reuse: 1x2 0.92/0.96  2x1 0.91/0.97  2x2 0.72/0.78  3x3 0.44/0.51
    transferable blob: 510 cells (49.7% of A)
  A-C: same position 716 (69.8%)
    same position excl. dominant L (covers 60.3% of cells, gated): 185 (58.0%)
    weighted overlap: 17.4%
    window reuse: 1x2 0.97/0.99  2x1 0.97/0.98  2x2 0.90/0.93  3x3 0.68/0.71
    transferable blob: 522 cells (50.9% of A)
  B-C: same position 641 (62.5%)
    same position excl. dominant L (covers 60.3% of cells, gated): 120 (38.8%)
    weighted overlap: 13.2%
    window reuse: 1x2 0.93/0.96  2x1 0.95/0.98  2x2 0.82/0.92  3x3 0.58/0.69
    transferable blob: 521 cells (50.8% of B)
scene gates: FAIL (A-B same-position excl. L 41.3% ≥ 25%; A-B 2x2 window reuse 71.5% ≥ 30%; A-B transferable blob 49.7% ≥ 10% of cells; A-C same-position excl. L 58.0% ≥ 25%; A-C 2x2 window reuse 90.2% ≥ 30%; A-C transferable blob 50.9% ≥ 10% of cells; B-C same-position excl. L 38.8% ≥ 25%; B-C 2x2 window reuse 81.6% ≥ 30%; B-C transferable blob 50.8% ≥ 10% of cells)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B same-position excl. L 41.3% ≥ 25%; A-B 2x2 window reuse 71.5% ≥ 30%; A-B transferable blob 49.7% ≥ 10% of cells; A-C same-position excl. L 58.0% ≥ 25%; A-C 2x2 window reuse 90.2% ≥ 30%; A-C transferable blob 50.9% ≥ 10% of cells; B-C same-position excl. L 38.8% ≥ 25%; B-C 2x2 window reuse 81.6% ≥ 30%; B-C transferable blob 50.8% ≥ 10% of cells)

## Connectors

Mating classes: sides forced to share one connector shape (a contact in any solution is an edge). The smallest possible class is K(3,3), 6 sides, for tab/blank (K4, 4 sides, for andro). False fits are tab-blank pairs inside a class that touch in no solution; ratio = false fits / intended contacts.

```text
non-flat sides: 3974  profiles: andro=3974
mating classes: 2
class size min / median / max: 252 / 1987 / 3722
tabs per class min / median / max: 0 / 0 / 0
blanks per class min / median / max: 0 / 0 / 0
largest class: 3722 sides (93.7% of sides), 0 tabs, 0 blanks, 3722 other
false fits: 6944920 of 5961 intended contacts (ratio 1165.060)
contacts: 5961 edges, 0 flat contacts, 0 mismatched
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
