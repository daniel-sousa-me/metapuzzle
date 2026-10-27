# Prototype summary

## Parameters

- scenes: experiments/005-hybrid-tones/scenes-v5.txt
- classes: experiments/005-hybrid-tones/classes-ink.json
- sizes: 20x25, 20x25, 20x25
- border: standard
- rotation: quarter
- extra_flat: 0
- mating_weight: 0.0
- max_shared_fraction: None
- seed: 0
- iters: 300000
- iters_used: 402
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

Total shared: 0; cluster penalty: 0; rotated pieces per solution: [356, 356, 358]

## Scene-level metrics

```text
maps (cols x rows): A 20x25, B 20x25, C 20x25
class histograms:
  A: L=223 DMs=79 M=48 MLs=36 DLs=32 MLc=29 MDc=20 DMc=9 LMc=9 DLc=7 D=2 DMp=2 LDc=1 MDd=1 MDp=1 MLp=1
  B: L=223 DMs=79 M=48 MLs=36 DLs=32 MLc=29 MDc=20 DMc=9 LMc=9 DLc=7 D=2 DMp=2 LDc=1 MDd=1 MDp=1 MLp=1
  C: L=223 DMs=79 M=48 MLs=36 DLs=32 MLc=29 MDc=20 DMc=9 LMc=9 DLc=7 D=2 DMp=2 LDc=1 MDd=1 MDp=1 MLp=1
largest same-class blob per class:
  A: L=223 M=47 DMs=37 MLs=14 DLs=10 MDc=3 MLc=2 D=1 DLc=1 DMc=1 DMp=1 LDc=1 LMc=1 MDd=1 MDp=1 MLp=1
  B: L=223 M=39 DLs=32 DMs=26 MLs=6 MDc=5 DLc=3 DMc=3 MLc=2 D=1 DMp=1 LDc=1 LMc=1 MDd=1 MDp=1 MLp=1
  C: L=223 DMs=31 M=25 DLs=19 MLs=14 MDc=3 MLc=2 D=1 DLc=1 DMc=1 DMp=1 LDc=1 LMc=1 MDd=1 MDp=1 MLp=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 233 (46.6%)
    same position excl. dominant L (covers 44.6% of cells, gated): 71 (32.9%)
    weighted overlap: 16.6%
    window reuse: 1x2 0.85/0.94  2x1 0.89/0.93  2x2 0.55/0.64  3x3 0.22/0.29
    transferable blob: 161 cells (32.2% of A)
  A-C: same position 256 (51.2%)
    same position excl. dominant L (covers 44.6% of cells, gated): 85 (37.8%)
    weighted overlap: 16.0%
    window reuse: 1x2 0.93/0.97  2x1 0.93/0.97  2x2 0.73/0.77  3x3 0.31/0.37
    transferable blob: 172 cells (34.4% of A)
  B-C: same position 231 (46.2%)
    same position excl. dominant L (covers 44.6% of cells, gated): 67 (30.7%)
    weighted overlap: 13.4%
    window reuse: 1x2 0.92/0.96  2x1 0.93/0.95  2x2 0.68/0.72  3x3 0.23/0.25
    transferable blob: 160 cells (32.0% of B)
scene gates: FAIL (A-B same-position excl. L 32.9% ≥ 25%; A-B 2x2 window reuse 55.0% ≥ 30%; A-B transferable blob 32.2% ≥ 10% of cells; A-C same-position excl. L 37.8% ≥ 25%; A-C 2x2 window reuse 72.6% ≥ 30%; A-C transferable blob 34.4% ≥ 10% of cells; B-C same-position excl. L 30.7% ≥ 25%; B-C 2x2 window reuse 68.2% ≥ 30%; B-C transferable blob 32.0% ≥ 10% of cells)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B same-position excl. L 32.9% ≥ 25%; A-B 2x2 window reuse 55.0% ≥ 30%; A-B transferable blob 32.2% ≥ 10% of cells; A-C same-position excl. L 37.8% ≥ 25%; A-C 2x2 window reuse 72.6% ≥ 30%; A-C transferable blob 34.4% ≥ 10% of cells; B-C same-position excl. L 30.7% ≥ 25%; B-C 2x2 window reuse 68.2% ≥ 30%; B-C transferable blob 32.0% ≥ 10% of cells)

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
