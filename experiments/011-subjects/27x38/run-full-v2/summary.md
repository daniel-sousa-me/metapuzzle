# Prototype summary

## Parameters

- scenes: /home/user/metapuzzle/experiments/011-subjects/pipeline/v2/scenes.txt
- classes: /home/user/metapuzzle/experiments/011-subjects/pipeline/classes-v9.json
- sizes: 27x38, 27x38, 27x38
- border: tray
- rotation: quarter
- extra_flat: 0
- mating_weight: 0.0
- max_shared_fraction: None
- seed: 0
- iters: 300000
- iters_used: 430
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

Total shared: 0; cluster penalty: 0; rotated pieces per solution: [776, 781, 770]

## Scene-level metrics

```text
maps (cols x rows): A 27x38, B 27x38, C 27x38
class histograms:
  A: L=292 M=228 D=175 DLs=46 MLs=39 DMs=35 W=29 S=23 LMc=22 LDc=20 MLc=20 MWs=17 SLs=16 DLc=15 MDc=14 DMc=13 SLc=7 WLs=5 LSc=3 WLc=3 LWc=2 MWc=1 WMc=1
  B: L=292 M=228 D=175 DLs=46 MLs=39 DMs=35 W=29 S=23 LMc=22 LDc=20 MLc=20 MWs=17 SLs=16 DLc=15 MDc=14 DMc=13 SLc=7 WLs=5 LSc=3 WLc=3 LWc=2 MWc=1 WMc=1
  C: L=292 M=228 D=175 DLs=46 MLs=39 DMs=35 W=29 S=23 LMc=22 LDc=20 MLc=20 MWs=17 SLs=16 DLc=15 MDc=14 DMc=13 SLc=7 WLs=5 LSc=3 WLc=3 LWc=2 MWc=1 WMc=1
largest same-class blob per class:
  A: L=248 M=225 D=122 W=29 S=16 SLs=10 DMs=6 DLs=5 MLs=5 WLs=3 DMc=2 LMc=2 MLc=2 SLc=2 DLc=1 LDc=1 LSc=1 LWc=1 MDc=1 MWc=1 MWs=1 WLc=1 WMc=1
  B: L=162 D=161 M=112 W=29 S=23 SLs=10 DLs=9 MLs=6 DMs=5 MWs=4 LMc=3 DLc=2 LDc=2 LSc=2 MLc=2 SLc=2 DMc=1 LWc=1 MDc=1 MWc=1 WLc=1 WLs=1 WMc=1
  C: L=226 D=96 M=75 W=29 S=23 MWs=6 DLs=5 DMs=5 MLs=5 SLs=4 WLs=3 DLc=1 DMc=1 LDc=1 LMc=1 LSc=1 LWc=1 MDc=1 MLc=1 MWc=1 SLc=1 WLc=1 WMc=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 188 (18.3%)
    same position excl. dominant L (covers 28.5% of cells, not gated): 87 (16.0%)
    weighted overlap: 7.8%
    window reuse: 1x2 0.97/0.99  2x1 0.95/0.99  2x2 0.80/0.90  3x3 0.43/0.62
    transferable blob: 123 cells (12.0% of A)
  A-C: same position 75 (7.3%)
    same position excl. dominant L (covers 28.5% of cells, not gated): 29 (5.9%)
    weighted overlap: 1.4%
    window reuse: 1x2 0.96/0.98  2x1 0.93/0.98  2x2 0.78/0.87  3x3 0.38/0.53
    transferable blob: 89 cells (8.7% of A)
  B-C: same position 148 (14.4%)
    same position excl. dominant L (covers 28.5% of cells, not gated): 84 (16.6%)
    weighted overlap: 3.9%
    window reuse: 1x2 0.95/0.97  2x1 0.93/0.98  2x2 0.79/0.86  3x3 0.46/0.59
    transferable blob: 97 cells (9.5% of B)
scene gates: FAIL (A-B 2x2 window reuse 79.9% ≥ 30%; A-B transferable blob 12.0% ≥ 10% of cells; A-C 2x2 window reuse 77.9% ≥ 30%; B-C 2x2 window reuse 78.9% ≥ 30%)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B 2x2 window reuse 79.9% ≥ 30%; A-B transferable blob 12.0% ≥ 10% of cells; A-C 2x2 window reuse 77.9% ≥ 30%; B-C 2x2 window reuse 78.9% ≥ 30%)

## Connectors

Mating classes: sides forced to share one connector shape (a contact in any solution is an edge). The smallest possible class is K(3,3), 6 sides, for tab/blank (K4, 4 sides, for andro). False fits are tab-blank pairs inside a class that touch in no solution; ratio = false fits / intended contacts.

```text
non-flat sides: 4104  profiles: andro=4104
mating classes: 1
class size min / median / max: 4104 / 4104 / 4104
tabs per class min / median / max: 0 / 0 / 0
blanks per class min / median / max: 0 / 0 / 0
largest class: 4104 sides (100.0% of sides), 0 tabs, 0 blanks, 4104 other
false fits: 8407239 of 5961 intended contacts (ratio 1410.374)
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
