# Prototype summary

## Parameters

- scenes: /home/user/metapuzzle/experiments/011-subjects/27x38-v2/pipeline-out-v5/scenes.txt
- classes: /home/user/metapuzzle/experiments/011-subjects/pipeline/classes-ink-v11.json
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
| AC | 1 | 0.05% | - | 2 | 2 | 1 | 0.002 |
| BC | 1 | 0.05% | - | 2 | 2 | 1 | 0.002 |

Total shared: 2; cluster penalty: 0; rotated pieces per solution: [766, 771, 755]

## Scene-level metrics

```text
maps (cols x rows): A 27x38, B 27x38, C 27x38
class histograms:
  A: D=53 DLs=49 MLs=43 DMs=40 M_c=40 M=36 Mb=36 Mc=36 Mr=36 L_f=34 M_l=34 Lb=32 Lo=32 Lr=32 Lx=32 M_s=32 L=30 L_u=30 LDc=29 L_v=28 M_d=28 L_p=26 LMc=25 DLc=23 MLc=23 D_s=22 MWs=19 W=16 D_v=14 DMc=12 D_p=12 SLs=12 WLs=12 MDc=11 D_k=10 SLc=7 DWs=6 S=5 WMc=5 WLc=4 LSc=3 LWc=3 MWc=3 H_G=2 H_I=2 H_O=2 DWc=1 H_E=1 H_N=1 H_Y=1 WDc=1
  B: D=53 DLs=49 MLs=43 DMs=40 M_c=40 M=36 Mb=36 Mc=36 Mr=36 L_f=34 M_l=34 Lb=32 Lo=32 Lr=32 Lx=32 M_s=32 L=30 L_u=30 LDc=29 L_v=28 M_d=28 L_p=26 LMc=25 DLc=23 MLc=23 D_s=22 MWs=19 W=16 D_v=14 DMc=12 D_p=12 SLs=12 WLs=12 MDc=11 D_k=10 SLc=7 DWs=6 S=5 WMc=5 WLc=4 LSc=3 LWc=3 MWc=3 H_G=2 H_I=2 H_O=2 DWc=1 H_E=1 H_N=1 H_Y=1 WDc=1
  C: D=53 DLs=49 MLs=43 DMs=40 M_c=40 M=36 Mb=36 Mc=36 Mr=36 L_f=34 M_l=34 Lb=32 Lo=32 Lr=32 Lx=32 M_s=32 L=30 L_u=30 LDc=29 L_v=28 M_d=28 L_p=26 LMc=25 DLc=23 MLc=23 D_s=22 MWs=19 W=16 D_v=14 DMc=12 D_p=12 SLs=12 WLs=12 MDc=11 D_k=10 SLc=7 DWs=6 S=5 WMc=5 WLc=4 LSc=3 LWc=3 MWc=3 H_G=2 H_I=2 H_O=2 DWc=1 H_E=1 H_N=1 H_Y=1 WDc=1
largest same-class blob per class:
  A: DLs=16 Mc=15 W=14 Mr=13 Lr=12 MWs=10 Mb=7 D=6 DMs=6 D_s=6 MLs=6 Lo=5 SLs=5 Lb=4 S=4 WLs=4 LDc=3 LMc=3 Lx=3 M=3 DLc=2 DMc=2 H_G=2 H_I=2 L=2 LSc=2 MLc=2 MWc=2 SLc=2 WLc=2 DWc=1 DWs=1 D_k=1 D_p=1 D_v=1 H_E=1 H_N=1 H_O=1 H_Y=1 LWc=1 L_f=1 L_p=1 L_u=1 L_v=1 MDc=1 M_c=1 M_d=1 M_l=1 M_s=1 WDc=1 WMc=1
  B: D=23 Mr=9 DMs=8 Lr=8 L=7 DLs=6 Lb=6 MWs=6 Mc=6 W=6 Lo=5 MLs=5 Mb=5 S=5 SLs=5 DWs=4 Lx=4 M=4 WLs=4 DLc=3 LDc=3 M_d=3 DMc=2 LMc=2 LSc=2 MLc=2 M_c=2 SLc=2 DWc=1 D_k=1 D_p=1 D_s=1 D_v=1 H_E=1 H_G=1 H_I=1 H_N=1 H_O=1 H_Y=1 LWc=1 L_f=1 L_p=1 L_u=1 L_v=1 MDc=1 MWc=1 M_l=1 M_s=1 WDc=1 WLc=1 WMc=1
  C: DLs=11 Lo=11 Lr=10 Mb=9 Mr=9 MLs=8 D=7 M=7 MWs=7 W=7 WLs=7 L=6 Lb=6 Mc=6 SLs=6 DMs=5 Lx=5 S=5 DWs=4 D_v=3 MLc=3 DLc=2 DMc=2 D_p=2 D_s=2 H_I=2 LDc=2 LMc=2 LSc=2 MDc=2 SLc=2 DWc=1 D_k=1 H_E=1 H_G=1 H_N=1 H_O=1 H_Y=1 LWc=1 L_f=1 L_p=1 L_u=1 L_v=1 MWc=1 M_c=1 M_d=1 M_l=1 M_s=1 WDc=1 WLc=1 WMc=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 12 (1.2%)
    same position excl. dominant D (covers 5.2% of cells, not gated): 12 (1.3%)
    weighted overlap: 0.8%
    window reuse: 1x2 0.71/0.87  2x1 0.73/0.87  2x2 0.11/0.22  3x3 0.00/0.00
    transferable blob: 6 cells (0.6% of A)
  A-C: same position 30 (2.9%)
    same position excl. dominant D (covers 5.2% of cells, not gated): 20 (2.2%)
    weighted overlap: 1.6%
    window reuse: 1x2 0.67/0.84  2x1 0.69/0.85  2x2 0.09/0.19  3x3 0.00/0.01
    transferable blob: 8 cells (0.8% of A)
  B-C: same position 26 (2.5%)
    same position excl. dominant D (covers 5.2% of cells, not gated): 26 (2.8%)
    weighted overlap: 1.5%
    window reuse: 1x2 0.69/0.83  2x1 0.67/0.82  2x2 0.10/0.17  3x3 0.00/0.00
    transferable blob: 7 cells (0.7% of B)
scene gates: PASS
```

## Gates

- piece gates: PASS
- scene gates: PASS

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
