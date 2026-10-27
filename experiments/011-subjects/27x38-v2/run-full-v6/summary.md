# Prototype summary

## Parameters

- scenes: /home/user/metapuzzle/experiments/011-subjects/27x38-v2/pipeline-out-v6/scenes.txt
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

Total shared: 2; cluster penalty: 0; rotated pieces per solution: [767, 776, 741]

## Scene-level metrics

```text
maps (cols x rows): A 27x38, B 27x38, C 27x38
class histograms:
  A: D=101 M=52 Mb=52 Mc=52 Mr=52 DLs=49 L=44 Lb=44 Lo=44 Lr=44 Lx=44 MLs=43 DMs=40 LDc=29 LMc=25 DLc=23 MLc=23 MWs=19 W=16 DMc=12 SLs=12 WLs=12 MDc=11 SLc=7 DWs=6 M_c_a=6 M_c_b=6 M_c_c=6 M_d_a=6 M_l_a=6 M_l_b=6 M_l_c=6 M_s_a=6 M_s_b=6 M_s_c=6 L_p_a=5 L_p_b=5 L_u_a=5 L_u_b=5 L_u_c=5 L_v_a=5 L_v_b=5 L_v_c=5 M_d_b=5 M_d_c=5 S=5 WMc=5 L_f_a=4 L_f_b=4 L_f_c=4 L_p_c=4 WLc=4 LSc=3 LWc=3 MWc=3 D_s_a=2 H_G=2 H_I=2 H_O=2 DWc=1 D_k_a=1 D_k_b=1 D_p_a=1 D_p_b=1 D_s_b=1 D_s_c=1 D_v_a=1 D_v_b=1 H_E=1 H_N=1 H_Y=1 WDc=1
  B: D=101 M=52 Mb=52 Mc=52 Mr=52 DLs=49 L=44 Lb=44 Lo=44 Lr=44 Lx=44 MLs=43 DMs=40 LDc=29 LMc=25 DLc=23 MLc=23 MWs=19 W=16 DMc=12 SLs=12 WLs=12 MDc=11 SLc=7 DWs=6 M_c_a=6 M_c_b=6 M_c_c=6 M_d_a=6 M_l_a=6 M_l_b=6 M_l_c=6 M_s_a=6 M_s_b=6 M_s_c=6 L_p_a=5 L_p_b=5 L_u_a=5 L_u_b=5 L_u_c=5 L_v_a=5 L_v_b=5 L_v_c=5 M_d_b=5 M_d_c=5 S=5 WMc=5 L_f_a=4 L_f_b=4 L_f_c=4 L_p_c=4 WLc=4 LSc=3 LWc=3 MWc=3 D_s_a=2 H_G=2 H_I=2 H_O=2 DWc=1 D_k_a=1 D_k_b=1 D_p_a=1 D_p_b=1 D_s_b=1 D_s_c=1 D_v_a=1 D_v_b=1 H_E=1 H_N=1 H_Y=1 WDc=1
  C: D=101 M=52 Mb=52 Mc=52 Mr=52 DLs=49 L=44 Lb=44 Lo=44 Lr=44 Lx=44 MLs=43 DMs=40 LDc=29 LMc=25 DLc=23 MLc=23 MWs=19 W=16 DMc=12 SLs=12 WLs=12 MDc=11 SLc=7 DWs=6 M_c_a=6 M_c_b=6 M_c_c=6 M_d_a=6 M_l_a=6 M_l_b=6 M_l_c=6 M_s_a=6 M_s_b=6 M_s_c=6 L_p_a=5 L_p_b=5 L_u_a=5 L_u_b=5 L_u_c=5 L_v_a=5 L_v_b=5 L_v_c=5 M_d_b=5 M_d_c=5 S=5 WMc=5 L_f_a=4 L_f_b=4 L_f_c=4 L_p_c=4 WLc=4 LSc=3 LWc=3 MWc=3 D_s_a=2 H_G=2 H_I=2 H_O=2 DWc=1 D_k_a=1 D_k_b=1 D_p_a=1 D_p_b=1 D_s_b=1 D_s_c=1 D_v_a=1 D_v_b=1 H_E=1 H_N=1 H_Y=1 WDc=1
largest same-class blob per class:
  A: Mb=44 L=39 Mc=32 Mr=30 Lr=27 M=25 D=20 Lo=18 Lb=17 DLs=16 Lx=14 W=14 MWs=10 DMs=6 MLs=6 SLs=5 S=4 WLs=4 LDc=3 LMc=3 DLc=2 DMc=2 DWs=2 H_G=2 H_I=2 LSc=2 MLc=2 MWc=2 SLc=2 WLc=2 DWc=1 D_k_a=1 D_k_b=1 D_p_a=1 D_p_b=1 D_s_a=1 D_s_b=1 D_s_c=1 D_v_a=1 D_v_b=1 H_E=1 H_N=1 H_O=1 H_Y=1 LWc=1 L_f_a=1 L_f_b=1 L_f_c=1 L_p_a=1 L_p_b=1 L_p_c=1 L_u_a=1 L_u_b=1 L_u_c=1 L_v_a=1 L_v_b=1 L_v_c=1 MDc=1 M_c_a=1 M_c_b=1 M_c_c=1 M_d_a=1 M_d_b=1 M_d_c=1 M_l_a=1 M_l_b=1 M_l_c=1 M_s_a=1 M_s_b=1 M_s_c=1 WDc=1 WMc=1
  B: D=84 Lx=30 Mb=26 Mr=26 Mc=19 M=15 Lb=12 L=11 Lr=11 DMs=8 Lo=8 MWs=8 DLs=6 W=6 MLs=5 S=5 SLs=5 DWs=4 WLs=4 DLc=3 LDc=3 DMc=2 LMc=2 LSc=2 MLc=2 SLc=2 DWc=1 D_k_a=1 D_k_b=1 D_p_a=1 D_p_b=1 D_s_a=1 D_s_b=1 D_s_c=1 D_v_a=1 D_v_b=1 H_E=1 H_G=1 H_I=1 H_N=1 H_O=1 H_Y=1 LWc=1 L_f_a=1 L_f_b=1 L_f_c=1 L_p_a=1 L_p_b=1 L_p_c=1 L_u_a=1 L_u_b=1 L_u_c=1 L_v_a=1 L_v_b=1 L_v_c=1 MDc=1 MWc=1 M_c_a=1 M_c_b=1 M_c_c=1 M_d_a=1 M_d_b=1 M_d_c=1 M_l_a=1 M_l_b=1 M_l_c=1 M_s_a=1 M_s_b=1 M_s_c=1 WDc=1 WLc=1 WMc=1
  C: Mr=30 L=27 Lx=25 D=23 Lb=22 Lr=21 Mc=18 M=17 Mb=16 DLs=11 Lo=11 MLs=8 MWs=7 W=7 WLs=7 SLs=6 DMs=5 S=5 DWs=4 MLc=3 DLc=2 DMc=2 H_I=2 LDc=2 LMc=2 LSc=2 MDc=2 SLc=2 DWc=1 D_k_a=1 D_k_b=1 D_p_a=1 D_p_b=1 D_s_a=1 D_s_b=1 D_s_c=1 D_v_a=1 D_v_b=1 H_E=1 H_G=1 H_N=1 H_O=1 H_Y=1 LWc=1 L_f_a=1 L_f_b=1 L_f_c=1 L_p_a=1 L_p_b=1 L_p_c=1 L_u_a=1 L_u_b=1 L_u_c=1 L_v_a=1 L_v_b=1 L_v_c=1 MWc=1 M_c_a=1 M_c_b=1 M_c_c=1 M_d_a=1 M_d_b=1 M_d_c=1 M_l_a=1 M_l_b=1 M_l_c=1 M_s_a=1 M_s_b=1 M_s_c=1 WDc=1 WLc=1 WMc=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 6 (0.6%)
    same position excl. dominant D (covers 9.8% of cells, not gated): 4 (0.5%)
    weighted overlap: 0.3%
    window reuse: 1x2 0.68/0.84  2x1 0.70/0.86  2x2 0.20/0.39  3x3 0.00/0.01
    transferable blob: 11 cells (1.1% of A)
  A-C: same position 23 (2.2%)
    same position excl. dominant D (covers 9.8% of cells, not gated): 6 (0.7%)
    weighted overlap: 0.5%
    window reuse: 1x2 0.72/0.85  2x1 0.70/0.87  2x2 0.17/0.37  3x3 0.00/0.01
    transferable blob: 14 cells (1.4% of A)
  B-C: same position 18 (1.8%)
    same position excl. dominant D (covers 9.8% of cells, not gated): 17 (2.1%)
    weighted overlap: 0.8%
    window reuse: 1x2 0.74/0.87  2x1 0.70/0.86  2x2 0.21/0.35  3x3 0.00/0.01
    transferable blob: 14 cells (1.4% of B)
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
