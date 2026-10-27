# Prototype summary

## Parameters

- scenes: /home/user/metapuzzle/experiments/011-subjects/pipeline/scenes.txt
- classes: /home/user/metapuzzle/experiments/005-hybrid-tones/classes-v4.json
- sizes: 27x38, 27x38, 27x38
- border: tray
- rotation: quarter
- extra_flat: 0
- mating_weight: 0.0
- max_shared_fraction: None
- seed: 0
- iters: 300000
- iters_used: 510
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

Total shared: 0; cluster penalty: 0; rotated pieces per solution: [767, 781, 771]

## Scene-level metrics

```text
maps (cols x rows): A 27x38, B 27x38, C 27x38
class histograms:
  A: L=292 M=228 D=175 S=49 DLs=44 DMs=37 MLs=37 W=29 LMc=23 LDc=21 MLc=21 MWs=17 DLc=16 MDc=13 DMc=12 WLs=5 WLc=3 LWc=2 MWc=1 WMc=1
  B: L=292 M=228 D=175 S=49 DLs=44 DMs=37 MLs=37 W=29 LMc=23 LDc=21 MLc=21 MWs=17 DLc=16 MDc=13 DMc=12 WLs=5 WLc=3 LWc=2 MWc=1 WMc=1
  C: L=292 M=228 D=175 S=49 DLs=44 DMs=37 MLs=37 W=29 LMc=23 LDc=21 MLc=21 MWs=17 DLc=16 MDc=13 DMc=12 WLs=5 WLc=3 LWc=2 MWc=1 WMc=1
largest same-class blob per class:
  A: L=248 M=225 D=121 S=49 W=29 DMs=6 MLs=6 DLs=5 DMc=2 LMc=2 MLc=2 WLs=2 DLc=1 LDc=1 LWc=1 MDc=1 MWc=1 MWs=1 WLc=1 WMc=1
  B: L=163 D=160 M=110 S=49 W=29 DLs=5 DMs=5 MLs=5 MWs=5 LMc=3 DLc=2 LDc=2 MLc=2 WLc=2 DMc=1 LWc=1 MDc=1 MWc=1 WLs=1 WMc=1
  C: L=229 M=148 D=98 S=49 W=29 MLs=7 MWs=6 DMs=5 DLs=4 WLs=3 DLc=2 LDc=2 WLc=2 DMc=1 LMc=1 LWc=1 MDc=1 MLc=1 MWc=1 WMc=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 184 (17.9%)
    same position excl. dominant L (covers 28.5% of cells, not gated): 83 (15.3%)
    weighted overlap: 7.9%
    window reuse: 1x2 0.98/0.99  2x1 0.97/0.98  2x2 0.81/0.92  3x3 0.44/0.66
    transferable blob: 127 cells (12.4% of A)
  A-C: same position 75 (7.3%)
    same position excl. dominant L (covers 28.5% of cells, not gated): 30 (6.2%)
    weighted overlap: 1.5%
    window reuse: 1x2 0.97/0.99  2x1 0.95/0.99  2x2 0.81/0.90  3x3 0.44/0.57
    transferable blob: 94 cells (9.2% of A)
  B-C: same position 149 (14.5%)
    same position excl. dominant L (covers 28.5% of cells, not gated): 81 (15.9%)
    weighted overlap: 3.9%
    window reuse: 1x2 0.96/0.98  2x1 0.94/0.99  2x2 0.82/0.89  3x3 0.53/0.64
    transferable blob: 93 cells (9.1% of B)
scene gates: FAIL (A-B 2x2 window reuse 80.8% ≥ 30%; A-B transferable blob 12.4% ≥ 10% of cells; A-C 2x2 window reuse 81.1% ≥ 30%; B-C 2x2 window reuse 82.0% ≥ 30%)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B 2x2 window reuse 80.8% ≥ 30%; A-B transferable blob 12.4% ≥ 10% of cells; A-C 2x2 window reuse 81.1% ≥ 30%; B-C 2x2 window reuse 82.0% ≥ 30%)

## Connectors

Mating classes: sides forced to share one connector shape (a contact in any solution is an edge). The smallest possible class is K(3,3), 6 sides, for tab/blank (K4, 4 sides, for andro). False fits are tab-blank pairs inside a class that touch in no solution; ratio = false fits / intended contacts.

```text
non-flat sides: 4103  profiles: andro=4103
mating classes: 1
class size min / median / max: 4103 / 4103 / 4103
tabs per class min / median / max: 0 / 0 / 0
blanks per class min / median / max: 0 / 0 / 0
largest class: 4103 sides (100.0% of sides), 0 tabs, 0 blanks, 4103 other
false fits: 8403139 of 5961 intended contacts (ratio 1409.686)
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
