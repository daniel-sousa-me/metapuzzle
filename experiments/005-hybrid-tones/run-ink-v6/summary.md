# Prototype summary

## Parameters

- scenes: experiments/005-hybrid-tones/scenes-v6.txt
- classes: experiments/005-hybrid-tones/classes-ink-v7.json
- sizes: 20x25, 20x25, 20x25
- border: standard
- rotation: quarter
- extra_flat: 0
- mating_weight: 0.0
- max_shared_fraction: None
- seed: 0
- iters: 300000
- iters_used: 377
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

Total shared: 0; cluster penalty: 0; rotated pieces per solution: [339, 339, 355]

## Scene-level metrics

```text
maps (cols x rows): A 20x25, B 20x25, C 20x25
class histograms:
  A: L=287 M=74 DMs=40 MLs=24 DLs=19 MLc=10 MLg=10 MDc=8 D=6 LMc=6 DMc=4 DMg=4 LDc=4 DMt=2 MDd=1 MLt=1
  B: L=287 M=74 DMs=40 MLs=24 DLs=19 MLc=10 MLg=10 MDc=8 D=6 LMc=6 DMc=4 DMg=4 LDc=4 DMt=2 MDd=1 MLt=1
  C: L=287 M=74 DMs=40 MLs=24 DLs=19 MLc=10 MLg=10 MDc=8 D=6 LMc=6 DMc=4 DMg=4 LDc=4 DMt=2 MDd=1 MLt=1
largest same-class blob per class:
  A: L=284 M=73 DMs=15 MLs=7 DLs=5 D=3 MDc=3 DMg=2 MLc=2 DMc=1 DMt=1 LDc=1 LMc=1 MDd=1 MLg=1 MLt=1
  B: L=287 M=54 DLs=16 DMs=13 MLs=6 MDc=2 MLc=2 D=1 DMc=1 DMg=1 DMt=1 LDc=1 LMc=1 MDd=1 MLg=1 MLt=1
  C: L=287 M=38 DMs=15 DLs=11 MLs=8 D=5 MLc=2 DMc=1 DMg=1 DMt=1 LDc=1 LMc=1 MDc=1 MDd=1 MLg=1 MLt=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 299 (59.8%)
    same position excl. dominant L (covers 57.4% of cells, gated): 66 (41.5%)
    weighted overlap: 13.8%
    window reuse: 1x2 0.86/0.93  2x1 0.91/0.95  2x2 0.62/0.67  3x3 0.36/0.39
    transferable blob: 233 cells (46.6% of A)
  A-C: same position 299 (59.8%)
    same position excl. dominant L (covers 57.4% of cells, gated): 65 (40.6%)
    weighted overlap: 11.4%
    window reuse: 1x2 0.91/0.93  2x1 0.89/0.93  2x2 0.74/0.77  3x3 0.33/0.35
    transferable blob: 232 cells (46.4% of A)
  B-C: same position 289 (57.8%)
    same position excl. dominant L (covers 57.4% of cells, gated): 56 (35.2%)
    weighted overlap: 11.0%
    window reuse: 1x2 0.91/0.93  2x1 0.92/0.95  2x2 0.70/0.74  3x3 0.43/0.45
    transferable blob: 233 cells (46.6% of B)
scene gates: FAIL (A-B same-position excl. L 41.5% ≥ 25%; A-B 2x2 window reuse 62.1% ≥ 30%; A-B transferable blob 46.6% ≥ 10% of cells; A-C same-position excl. L 40.6% ≥ 25%; A-C 2x2 window reuse 73.7% ≥ 30%; A-C transferable blob 46.4% ≥ 10% of cells; B-C same-position excl. L 35.2% ≥ 25%; B-C 2x2 window reuse 69.5% ≥ 30%; B-C transferable blob 46.6% ≥ 10% of cells)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B same-position excl. L 41.5% ≥ 25%; A-B 2x2 window reuse 62.1% ≥ 30%; A-B transferable blob 46.6% ≥ 10% of cells; A-C same-position excl. L 40.6% ≥ 25%; A-C 2x2 window reuse 73.7% ≥ 30%; A-C transferable blob 46.4% ≥ 10% of cells; B-C same-position excl. L 35.2% ≥ 25%; B-C 2x2 window reuse 69.5% ≥ 30%; B-C transferable blob 46.6% ≥ 10% of cells)

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
