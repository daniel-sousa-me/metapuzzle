# Prototype summary

## Parameters

- scenes: experiments/005-hybrid-tones/scenes-v3.txt
- classes: experiments/005-hybrid-tones/classes.json
- sizes: 20x25, 20x25, 20x25
- border: standard
- rotation: quarter
- extra_flat: 0
- mating_weight: 0.0
- max_shared_fraction: None
- seed: 0
- iters: 300000
- iters_used: 646
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

Total shared: 0; cluster penalty: 0; rotated pieces per solution: [347, 335, 345]

## Scene-level metrics

```text
maps (cols x rows): A 20x25, B 20x25, C 20x25
class histograms:
  A: L=234 M=83 LD=33 LM=33 DL=31 DM=23 D=22 ML=22 MD=19
  B: L=234 M=83 LD=33 LM=33 DL=31 DM=23 D=22 ML=22 MD=19
  C: L=234 M=83 LD=33 LM=33 DL=31 DM=23 D=22 ML=22 MD=19
largest same-class blob per class:
  A: L=233 M=80 D=20 DM=10 DL=9 LD=9 LM=7 ML=6 MD=5
  B: L=234 M=83 D=21 DL=21 DM=17 LD=17 MD=12 LM=10 ML=4
  C: L=234 M=42 D=21 DL=15 DM=9 LD=8 ML=8 LM=7 MD=4
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 290 (58.0%)
    same position excl. dominant L (covers 46.8% of cells, gated): 105 (48.4%)
    weighted overlap: 33.5%
    window reuse: 1x2 0.94/0.97  2x1 0.93/0.96  2x2 0.67/0.75  3x3 0.43/0.45
    transferable blob: 185 cells (37.0% of A)
  A-C: same position 265 (53.0%)
    same position excl. dominant L (covers 46.8% of cells, gated): 86 (40.8%)
    weighted overlap: 24.9%
    window reuse: 1x2 0.99/1.00  2x1 0.99/1.00  2x2 0.76/0.87  3x3 0.45/0.53
    transferable blob: 179 cells (35.8% of A)
  B-C: same position 263 (52.6%)
    same position excl. dominant L (covers 46.8% of cells, gated): 88 (42.5%)
    weighted overlap: 25.5%
    window reuse: 1x2 0.97/0.99  2x1 0.96/0.99  2x2 0.76/0.86  3x3 0.47/0.54
    transferable blob: 175 cells (35.0% of B)
scene gates: FAIL (A-B same-position excl. L 48.4% ≥ 25%; A-B weighted overlap 33.5% ≥ 25%; A-B 2x2 window reuse 67.3% ≥ 30%; A-B transferable blob 37.0% ≥ 10% of cells; A-C same-position excl. L 40.8% ≥ 25%; A-C 2x2 window reuse 75.7% ≥ 30%; A-C transferable blob 35.8% ≥ 10% of cells; B-C same-position excl. L 42.5% ≥ 25%; B-C weighted overlap 25.5% ≥ 25%; B-C 2x2 window reuse 76.1% ≥ 30%; B-C transferable blob 35.0% ≥ 10% of cells)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B same-position excl. L 48.4% ≥ 25%; A-B weighted overlap 33.5% ≥ 25%; A-B 2x2 window reuse 67.3% ≥ 30%; A-B transferable blob 37.0% ≥ 10% of cells; A-C same-position excl. L 40.8% ≥ 25%; A-C 2x2 window reuse 75.7% ≥ 30%; A-C transferable blob 35.8% ≥ 10% of cells; B-C same-position excl. L 42.5% ≥ 25%; B-C weighted overlap 25.5% ≥ 25%; B-C 2x2 window reuse 76.1% ≥ 30%; B-C transferable blob 35.0% ≥ 10% of cells)

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
