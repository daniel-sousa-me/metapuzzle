# Prototype summary

## Parameters

- scenes: /home/user/metapuzzle/experiments/011-subjects/27x38-v2/pipeline-out-v7/scenes.txt
- classes: /home/user/metapuzzle/experiments/011-subjects/pipeline/classes-v12.json
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
- cross-class seams (A / B / C): 0 / 0 / 0
- valid: yes

## Piece-level shared adjacencies

Adjacency = two pieces touching in a solution (flat seams included). Shared = touching in both solutions of the pair.

| pair | shared | fraction | clusters (3+) | largest component | familiar pieces | max familiarity | mean familiarity |
|---|---|---|---|---|---|---|---|
| AB | 1 | 0.05% | - | 2 | 2 | 1 | 0.002 |
| AC | 1 | 0.05% | - | 2 | 2 | 1 | 0.002 |
| BC | 0 | 0.00% | - | 0 | 0 | 0 | 0.000 |

Total shared: 2; cluster penalty: 0; rotated pieces per solution: [780, 771, 764]

## Scene-level metrics

```text
maps (cols x rows): A 27x38, B 27x38, C 27x38
class histograms:
  A: D=110 Mb=68 Mc=68 Mr=68 M=67 Lb=55 Lo=55 Lr=55 Lx=55 L=53 DLs=49 MLs=43 DMs=40 LDc=29 LMc=25 DLc=23 MLc=23 MWs=19 W=16 DMc=12 SLs=12 WLs=12 MDc=11 SLc=7 DWs=6 S=5 WMc=5 WLc=4 LSc=3 LWc=3 MWc=3 H_G=2 H_I=2 H_O=2 DWc=1 D_s_a=1 H_E=1 H_N=1 H_Y=1 L_f_a=1 L_p_a=1 L_v_a=1 M_c_a=1 M_d_a=1 M_d_b=1 M_l_a=1 M_l_b=1 M_s_a=1 M_s_b=1 WDc=1
  B: D=110 Mb=68 Mc=68 Mr=68 M=67 Lb=55 Lo=55 Lr=55 Lx=55 L=53 DLs=49 MLs=43 DMs=40 LDc=29 LMc=25 DLc=23 MLc=23 MWs=19 W=16 DMc=12 SLs=12 WLs=12 MDc=11 SLc=7 DWs=6 S=5 WMc=5 WLc=4 LSc=3 LWc=3 MWc=3 H_G=2 H_I=2 H_O=2 DWc=1 D_s_a=1 H_E=1 H_N=1 H_Y=1 L_f_a=1 L_p_a=1 L_v_a=1 M_c_a=1 M_d_a=1 M_d_b=1 M_l_a=1 M_l_b=1 M_s_a=1 M_s_b=1 WDc=1
  C: D=110 Mb=68 Mc=68 Mr=68 M=67 Lb=55 Lo=55 Lr=55 Lx=55 L=53 DLs=49 MLs=43 DMs=40 LDc=29 LMc=25 DLc=23 MLc=23 MWs=19 W=16 DMc=12 SLs=12 WLs=12 MDc=11 SLc=7 DWs=6 S=5 WMc=5 WLc=4 LSc=3 LWc=3 MWc=3 H_G=2 H_I=2 H_O=2 DWc=1 D_s_a=1 H_E=1 H_N=1 H_Y=1 L_f_a=1 L_p_a=1 L_v_a=1 M_c_a=1 M_d_a=1 M_d_b=1 M_l_a=1 M_l_b=1 M_s_a=1 M_s_b=1 WDc=1
largest same-class blob per class:
  A: Mr=65 Mc=57 Lr=53 Mb=52 L=51 M=48 D=41 Lo=31 Lb=19 Lx=18 DLs=16 W=14 MWs=10 DMs=7 MLs=6 SLs=5 S=4 WLs=4 LDc=3 LMc=3 DLc=2 DMc=2 DWs=2 H_G=2 H_I=2 LSc=2 MLc=2 MWc=2 SLc=2 WLc=2 DWc=1 D_s_a=1 H_E=1 H_N=1 H_O=1 H_Y=1 LWc=1 L_f_a=1 L_p_a=1 L_v_a=1 MDc=1 M_c_a=1 M_d_a=1 M_d_b=1 M_l_a=1 M_l_b=1 M_s_a=1 M_s_b=1 WDc=1 WMc=1
  B: D=93 Mr=60 L=50 Mb=34 M=32 Lo=28 Lr=28 Mc=26 Lx=23 Lb=15 DMs=8 MWs=8 DLs=6 W=6 MLs=5 S=5 SLs=5 DWs=4 WLs=4 DLc=3 LDc=3 DMc=2 LMc=2 LSc=2 MLc=2 SLc=2 DWc=1 D_s_a=1 H_E=1 H_G=1 H_I=1 H_N=1 H_O=1 H_Y=1 LWc=1 L_f_a=1 L_p_a=1 L_v_a=1 MDc=1 MWc=1 M_c_a=1 M_d_a=1 M_d_b=1 M_l_a=1 M_l_b=1 M_s_a=1 M_s_b=1 WDc=1 WLc=1 WMc=1
  C: D=61 Mb=58 Mc=43 Mr=43 Lx=37 Lo=35 L=31 Lr=26 Lb=25 M=17 DLs=11 MLs=8 MWs=7 W=7 WLs=7 SLs=6 DMs=5 S=5 DWs=4 MLc=3 DLc=2 DMc=2 H_I=2 LDc=2 LMc=2 LSc=2 MDc=2 SLc=2 DWc=1 D_s_a=1 H_E=1 H_G=1 H_N=1 H_O=1 H_Y=1 LWc=1 L_f_a=1 L_p_a=1 L_v_a=1 MWc=1 M_c_a=1 M_d_a=1 M_d_b=1 M_l_a=1 M_l_b=1 M_s_a=1 M_s_b=1 WDc=1 WLc=1 WMc=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 6 (0.6%)
    same position excl. dominant D (covers 10.7% of cells, not gated): 4 (0.5%)
    weighted overlap: 0.5%
    window reuse: 1x2 0.81/0.89  2x1 0.82/0.90  2x2 0.37/0.55  3x3 0.01/0.05
    transferable blob: 26 cells (2.5% of A)
  A-C: same position 26 (2.5%)
    same position excl. dominant D (covers 10.7% of cells, not gated): 6 (0.7%)
    weighted overlap: 0.7%
    window reuse: 1x2 0.85/0.92  2x1 0.81/0.92  2x2 0.33/0.54  3x3 0.02/0.06
    transferable blob: 30 cells (2.9% of A)
  B-C: same position 15 (1.5%)
    same position excl. dominant D (covers 10.7% of cells, not gated): 14 (1.7%)
    weighted overlap: 0.8%
    window reuse: 1x2 0.86/0.93  2x1 0.79/0.91  2x2 0.37/0.53  3x3 0.03/0.05
    transferable blob: 31 cells (3.0% of B)
scene gates: FAIL (A-B 2x2 window reuse 36.7% ≥ 30%; A-C 2x2 window reuse 32.6% ≥ 30%; B-C 2x2 window reuse 36.9% ≥ 30%)
```

## Gates

- piece gates: PASS
- scene gates: FAIL (A-B 2x2 window reuse 36.7% ≥ 30%; A-C 2x2 window reuse 32.6% ≥ 30%; B-C 2x2 window reuse 36.9% ≥ 30%)

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
