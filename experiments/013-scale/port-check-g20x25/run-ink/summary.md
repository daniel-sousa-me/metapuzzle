# Prototype summary

## Parameters

- scenes: /home/user/metapuzzle/experiments/013-scale/g20x25/scenes.txt
- classes: /home/user/metapuzzle/experiments/005-hybrid-tones/classes-ink.json
- sizes: 20x25, 20x25, 20x25
- border: standard
- rotation: quarter
- extra_flat: 0
- mating_weight: 0.0
- max_shared_fraction: None
- seed: 0
- iters: 300000
- iters_used: 315
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

Total shared: 0; cluster penalty: 0; rotated pieces per solution: [359, 350, 349]

## Scene-level metrics

```text
maps (cols x rows): A 20x25, B 20x25, C 20x25
class histograms:
  A: L=287 M=76 DMs=41 MLs=24 MLc=17 DLs=16 MDc=11 D=10 DMc=8 LMc=6 DMp=2 MDd=1 MLp=1
  B: L=287 M=76 DMs=41 MLs=24 MLc=17 DLs=16 MDc=11 D=10 DMc=8 LMc=6 DMp=2 MDd=1 MLp=1
  C: L=287 M=76 DMs=41 MLs=24 MLc=17 DLs=16 MDc=11 D=10 DMc=8 LMc=6 DMp=2 MDd=1 MLp=1
largest same-class blob per class:
  A: L=284 M=75 DMs=7 MLs=7 DLs=5 D=4 MDc=4 DMc=2 MLc=2 DMp=1 LMc=1 MDd=1 MLp=1
  B: L=287 M=56 DLs=16 DMs=14 D=6 MLs=6 DMc=2 DMp=2 MDc=2 MLc=2 LMc=1 MDd=1 MLp=1
  C: L=287 M=38 DLs=10 DMs=8 MLs=8 D=6 MDc=2 MLc=2 DMc=1 DMp=1 LMc=1 MDd=1 MLp=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 297 (59.4%)
    same position excl. dominant L (covers 57.4% of cells, gated): 64 (40.3%)
    weighted overlap: 15.5%
    window reuse: 1x2 0.89/0.95  2x1 0.93/0.96  2x2 0.66/0.73  3x3 0.37/0.39
    transferable blob: 233 cells (46.6% of A)
  A-C: same position 296 (59.2%)
    same position excl. dominant L (covers 57.4% of cells, gated): 63 (39.6%)
    weighted overlap: 14.3%
    window reuse: 1x2 0.93/0.97  2x1 0.91/0.97  2x2 0.74/0.80  3x3 0.42/0.43
    transferable blob: 230 cells (46.0% of A)
  B-C: same position 293 (58.6%)
    same position excl. dominant L (covers 57.4% of cells, gated): 59 (36.9%)
    weighted overlap: 15.6%
    window reuse: 1x2 0.92/0.94  2x1 0.91/0.95  2x2 0.69/0.80  3x3 0.43/0.45
    transferable blob: 234 cells (46.8% of B)
scene gates: FAIL (A-B same-position excl. L 40.3% ≥ 25%; A-B 2x2 window reuse 65.8% ≥ 30%; A-B transferable blob 46.6% ≥ 10% of cells; A-C same-position excl. L 39.6% ≥ 25%; A-C 2x2 window reuse 74.3% ≥ 30%; A-C transferable blob 46.0% ≥ 10% of cells; B-C same-position excl. L 36.9% ≥ 25%; B-C 2x2 window reuse 68.6% ≥ 30%; B-C transferable blob 46.8% ≥ 10% of cells)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B same-position excl. L 40.3% ≥ 25%; A-B 2x2 window reuse 65.8% ≥ 30%; A-B transferable blob 46.6% ≥ 10% of cells; A-C same-position excl. L 39.6% ≥ 25%; A-C 2x2 window reuse 74.3% ≥ 30%; A-C transferable blob 46.0% ≥ 10% of cells; B-C same-position excl. L 36.9% ≥ 25%; B-C 2x2 window reuse 68.6% ≥ 30%; B-C transferable blob 46.8% ≥ 10% of cells)

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
