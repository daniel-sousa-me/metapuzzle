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
- iters_used: 503
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

Total shared: 0; cluster penalty: 0; rotated pieces per solution: [354, 361, 348]

## Scene-level metrics

```text
maps (cols x rows): A 20x25, B 20x25, C 20x25
class histograms:
  A: L=288 M=84 DLs=27 D=23 DMs=23 MLs=15 DLc=10 LDc=8 MLc=7 LMc=6 DMc=4 DLp=2 MDc=2 MLp=1
  B: L=288 M=84 DLs=27 D=23 DMs=23 MLs=15 DLc=10 LDc=8 MLc=7 LMc=6 DMc=4 DLp=2 MDc=2 MLp=1
  C: L=288 M=84 DLs=27 D=23 DMs=23 MLs=15 DLc=10 LDc=8 MLc=7 LMc=6 DMc=4 DLp=2 MDc=2 MLp=1
largest same-class blob per class:
  A: L=284 M=83 D=11 DLs=7 DMs=4 MLs=4 DLc=3 DLp=1 DMc=1 LDc=1 LMc=1 MDc=1 MLc=1 MLp=1
  B: L=288 M=69 D=22 DLs=15 DMs=11 MLs=4 LDc=2 MLc=2 DLc=1 DLp=1 DMc=1 LMc=1 MDc=1 MLp=1
  C: L=288 M=43 D=21 DLs=12 DMs=8 MLs=8 LDc=2 MLc=2 DLc=1 DLp=1 DMc=1 LMc=1 MDc=1 MLp=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 304 (60.8%)
    same position excl. dominant L (covers 57.6% of cells, gated): 68 (42.5%)
    weighted overlap: 13.7%
    window reuse: 1x2 0.86/0.95  2x1 0.89/0.96  2x2 0.56/0.67  3x3 0.24/0.33
    transferable blob: 235 cells (47.0% of A)
  A-C: same position 329 (65.8%)
    same position excl. dominant L (covers 57.6% of cells, gated): 89 (54.3%)
    weighted overlap: 20.1%
    window reuse: 1x2 0.94/0.97  2x1 0.94/0.97  2x2 0.77/0.80  3x3 0.48/0.50
    transferable blob: 236 cells (47.2% of A)
  B-C: same position 314 (62.8%)
    same position excl. dominant L (covers 57.6% of cells, gated): 74 (45.1%)
    weighted overlap: 16.2%
    window reuse: 1x2 0.91/0.93  2x1 0.87/0.92  2x2 0.66/0.77  3x3 0.32/0.34
    transferable blob: 240 cells (48.0% of B)
scene gates: FAIL (A-B same-position excl. L 42.5% ≥ 25%; A-B 2x2 window reuse 55.9% ≥ 30%; A-B transferable blob 47.0% ≥ 10% of cells; A-C same-position excl. L 54.3% ≥ 25%; A-C 2x2 window reuse 76.5% ≥ 30%; A-C transferable blob 47.2% ≥ 10% of cells; B-C same-position excl. L 45.1% ≥ 25%; B-C 2x2 window reuse 66.0% ≥ 30%; B-C transferable blob 48.0% ≥ 10% of cells)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B same-position excl. L 42.5% ≥ 25%; A-B 2x2 window reuse 55.9% ≥ 30%; A-B transferable blob 47.0% ≥ 10% of cells; A-C same-position excl. L 54.3% ≥ 25%; A-C 2x2 window reuse 76.5% ≥ 30%; A-C transferable blob 47.2% ≥ 10% of cells; B-C same-position excl. L 45.1% ≥ 25%; B-C 2x2 window reuse 66.0% ≥ 30%; B-C transferable blob 48.0% ≥ 10% of cells)

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
