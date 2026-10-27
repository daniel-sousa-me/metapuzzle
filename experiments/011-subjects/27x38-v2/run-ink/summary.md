# Prototype summary

## Parameters

- scenes: /home/user/metapuzzle/experiments/011-subjects/27x38-v2/pipeline-out/scenes.txt
- classes: /home/user/metapuzzle/experiments/011-subjects/pipeline/classes-ink-v9.json
- sizes: 27x38, 27x38, 27x38
- border: tray
- rotation: quarter
- extra_flat: 0
- mating_weight: 0.0
- max_shared_fraction: None
- seed: 0
- iters: 300000
- iters_used: 300000
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
| BC | 1 | 0.05% | - | 2 | 2 | 1 | 0.002 |

Total shared: 1; cluster penalty: 0; rotated pieces per solution: [794, 785, 753]

## Scene-level metrics

```text
maps (cols x rows): A 27x38, B 27x38, C 27x38
class histograms:
  A: L=280 M=279 D=111 DLs=49 MLs=43 DMs=40 LDc=29 DLc=25 LMc=25 MLc=23 MWs=19 W=16 DMc=12 SLs=12 WLs=12 MDc=11 SLc=7 DWs=6 S=5 WMc=5 WLc=4 LSc=3 LWc=3 MWc=3 DWc=1 LDd=1 MDd=1 WDc=1
  B: L=280 M=279 D=111 DLs=49 MLs=43 DMs=40 LDc=29 DLc=25 LMc=25 MLc=23 MWs=19 W=16 DMc=12 SLs=12 WLs=12 MDc=11 SLc=7 DWs=6 S=5 WMc=5 WLc=4 LSc=3 LWc=3 MWc=3 DWc=1 LDd=1 MDd=1 WDc=1
  C: L=280 M=279 D=111 DLs=49 MLs=43 DMs=40 LDc=29 DLc=25 LMc=25 MLc=23 MWs=19 W=16 DMc=12 SLs=12 WLs=12 MDc=11 SLc=7 DWs=6 S=5 WMc=5 WLc=4 LSc=3 LWc=3 MWc=3 DWc=1 LDd=1 MDd=1 WDc=1
largest same-class blob per class:
  A: M=279 L=244 D=41 DLs=16 W=14 MWs=10 DMs=7 MLs=6 SLs=5 S=4 WLs=4 LDc=3 LMc=3 DLc=2 DMc=2 DWs=2 LSc=2 LWc=2 MLc=2 MWc=2 SLc=2 WLc=2 DWc=1 LDd=1 MDc=1 MDd=1 WDc=1 WMc=1
  B: M=273 L=145 D=94 DMs=8 DLs=6 W=6 MLs=5 MWs=5 S=5 SLs=5 DLc=4 DWs=4 WLs=4 LDc=3 DMc=2 LMc=2 LSc=2 MLc=2 SLc=2 DWc=1 LDd=1 LWc=1 MDc=1 MDd=1 MWc=1 WDc=1 WLc=1 WMc=1
  C: L=213 M=209 D=62 DLs=11 MLs=8 MWs=7 W=7 WLs=7 SLs=6 DMs=5 S=5 DWs=4 MLc=3 DLc=2 DMc=2 LDc=2 LMc=2 LSc=2 MDc=2 SLc=2 DWc=1 LDd=1 LWc=1 MDd=1 MWc=1 WDc=1 WLc=1 WMc=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 136 (13.3%)
    same position excl. dominant L (covers 27.3% of cells, not gated): 58 (10.7%)
    weighted overlap: 2.3%
    window reuse: 1x2 0.94/0.96  2x1 0.93/0.96  2x2 0.71/0.84  3x3 0.36/0.55
    transferable blob: 106 cells (10.3% of A)
  A-C: same position 162 (15.8%)
    same position excl. dominant L (covers 27.3% of cells, not gated): 88 (16.3%)
    weighted overlap: 3.3%
    window reuse: 1x2 0.93/0.97  2x1 0.91/0.98  2x2 0.64/0.82  3x3 0.27/0.44
    transferable blob: 118 cells (11.5% of A)
  B-C: same position 177 (17.3%)
    same position excl. dominant L (covers 27.3% of cells, not gated): 122 (23.4%)
    weighted overlap: 3.5%
    window reuse: 1x2 0.95/0.97  2x1 0.91/0.97  2x2 0.68/0.82  3x3 0.24/0.38
    transferable blob: 85 cells (8.3% of B)
scene gates: FAIL (A-B 2x2 window reuse 71.3% ≥ 30%; A-B transferable blob 10.3% ≥ 10% of cells; A-C 2x2 window reuse 64.3% ≥ 30%; A-C transferable blob 11.5% ≥ 10% of cells; B-C 2x2 window reuse 68.3% ≥ 30%)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B 2x2 window reuse 71.3% ≥ 30%; A-B transferable blob 10.3% ≥ 10% of cells; A-C 2x2 window reuse 64.3% ≥ 30%; A-C transferable blob 11.5% ≥ 10% of cells; B-C 2x2 window reuse 68.3% ≥ 30%)

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
