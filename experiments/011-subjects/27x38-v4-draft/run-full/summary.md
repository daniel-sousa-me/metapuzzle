# Prototype summary

## Parameters

- scenes: /home/user/metapuzzle/experiments/011-subjects/27x38-v4-draft/pipeline-out-v6/scenes.txt
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
| AC | 2 | 0.10% | - | 2 | 4 | 1 | 0.004 |
| BC | 3 | 0.15% | - | 2 | 6 | 1 | 0.006 |

Total shared: 6; cluster penalty: 0; rotated pieces per solution: [756, 778, 749]

## Scene-level metrics

```text
maps (cols x rows): A 27x38, B 27x38, C 27x38
class histograms:
  A: D=91 DMs=65 W=62 DLs=48 L=48 Lb=46 Lo=46 Lr=46 Lx=46 Mb=30 Mc=30 Mr=30 DWs=29 M=28 DLc=26 MLs=25 MWs=25 LDc=24 DMc=23 MDc=22 WLs=20 WDc=12 LMc=10 WMc=10 DWc=7 MLc=6 MWc=6 M_c_a=6 M_c_b=6 M_c_c=6 M_d_a=6 M_l_a=6 M_l_b=6 M_l_c=6 M_s_a=6 M_s_b=6 M_s_c=6 SLs=6 LWc=5 L_p_a=5 L_p_b=5 L_u_a=5 L_u_b=5 L_u_c=5 L_v_a=5 L_v_b=5 L_v_c=5 M_d_b=5 M_d_c=5 L_f_a=4 L_f_b=4 L_f_c=4 L_p_c=4 SLc=4 WLc=4 D_s_a=2 H_G=2 H_I=2 H_O=2 D_k_a=1 D_k_b=1 D_p_a=1 D_p_b=1 D_s_b=1 D_s_c=1 D_v_a=1 D_v_b=1 H_E=1 H_N=1 H_Y=1 LDd=1
  B: D=91 DMs=65 W=62 DLs=48 L=48 Lb=46 Lo=46 Lr=46 Lx=46 Mb=30 Mc=30 Mr=30 DWs=29 M=28 DLc=26 MLs=25 MWs=25 LDc=24 DMc=23 MDc=22 WLs=20 WDc=12 LMc=10 WMc=10 DWc=7 MLc=6 MWc=6 M_c_a=6 M_c_b=6 M_c_c=6 M_d_a=6 M_l_a=6 M_l_b=6 M_l_c=6 M_s_a=6 M_s_b=6 M_s_c=6 SLs=6 LWc=5 L_p_a=5 L_p_b=5 L_u_a=5 L_u_b=5 L_u_c=5 L_v_a=5 L_v_b=5 L_v_c=5 M_d_b=5 M_d_c=5 L_f_a=4 L_f_b=4 L_f_c=4 L_p_c=4 SLc=4 WLc=4 D_s_a=2 H_G=2 H_I=2 H_O=2 D_k_a=1 D_k_b=1 D_p_a=1 D_p_b=1 D_s_b=1 D_s_c=1 D_v_a=1 D_v_b=1 H_E=1 H_N=1 H_Y=1 LDd=1
  C: D=91 DMs=65 W=62 DLs=48 L=48 Lb=46 Lo=46 Lr=46 Lx=46 Mb=30 Mc=30 Mr=30 DWs=29 M=28 DLc=26 MLs=25 MWs=25 LDc=24 DMc=23 MDc=22 WLs=20 WDc=12 LMc=10 WMc=10 DWc=7 MLc=6 MWc=6 M_c_a=6 M_c_b=6 M_c_c=6 M_d_a=6 M_l_a=6 M_l_b=6 M_l_c=6 M_s_a=6 M_s_b=6 M_s_c=6 SLs=6 LWc=5 L_p_a=5 L_p_b=5 L_u_a=5 L_u_b=5 L_u_c=5 L_v_a=5 L_v_b=5 L_v_c=5 M_d_b=5 M_d_c=5 L_f_a=4 L_f_b=4 L_f_c=4 L_p_c=4 SLc=4 WLc=4 D_s_a=2 H_G=2 H_I=2 H_O=2 D_k_a=1 D_k_b=1 D_p_a=1 D_p_b=1 D_s_b=1 D_s_c=1 D_v_a=1 D_v_b=1 H_E=1 H_N=1 H_Y=1 LDd=1
largest same-class blob per class:
  A: D=53 Lr=45 W=39 Lo=26 Lx=26 Lb=21 Mr=20 L=15 M=14 DMs=10 Mc=8 DLs=6 DWs=6 MLs=6 SLs=6 MWs=5 Mb=5 DLc=3 DMc=3 LDc=3 MDc=3 DWc=2 SLc=2 WDc=2 WLs=2 D_k_a=1 D_k_b=1 D_p_a=1 D_p_b=1 D_s_a=1 D_s_b=1 D_s_c=1 D_v_a=1 D_v_b=1 H_E=1 H_G=1 H_I=1 H_N=1 H_O=1 H_Y=1 LDd=1 LMc=1 LWc=1 L_f_a=1 L_f_b=1 L_f_c=1 L_p_a=1 L_p_b=1 L_p_c=1 L_u_a=1 L_u_b=1 L_u_c=1 L_v_a=1 L_v_b=1 L_v_c=1 MLc=1 MWc=1 M_c_a=1 M_c_b=1 M_c_c=1 M_d_a=1 M_d_b=1 M_d_c=1 M_l_a=1 M_l_b=1 M_l_c=1 M_s_a=1 M_s_b=1 M_s_c=1 WLc=1 WMc=1
  B: D=76 Lx=40 DLs=19 L=19 Lr=14 Mc=14 W=12 DMs=11 Lb=10 Mr=10 Lo=9 M=8 DMc=7 DWs=7 SLs=6 WLs=6 Mb=5 MWs=4 MLs=3 DLc=2 LDc=2 LMc=2 LWc=2 MLc=2 SLc=2 WLc=2 DWc=1 D_k_a=1 D_k_b=1 D_p_a=1 D_p_b=1 D_s_a=1 D_s_b=1 D_s_c=1 D_v_a=1 D_v_b=1 H_E=1 H_G=1 H_I=1 H_N=1 H_O=1 H_Y=1 LDd=1 L_f_a=1 L_f_b=1 L_f_c=1 L_p_a=1 L_p_b=1 L_p_c=1 L_u_a=1 L_u_b=1 L_u_c=1 L_v_a=1 L_v_b=1 L_v_c=1 MDc=1 MWc=1 M_c_a=1 M_c_b=1 M_c_c=1 M_d_a=1 M_d_b=1 M_d_c=1 M_l_a=1 M_l_b=1 M_l_c=1 M_s_a=1 M_s_b=1 M_s_c=1 WDc=1 WMc=1
  C: W=31 Lx=30 Lo=21 D=19 L=19 WLs=17 Mb=14 Mr=13 Lb=12 Lr=11 DLs=8 DMs=7 MWs=6 SLs=6 M=5 Mc=5 DWs=3 MDc=3 MLs=3 DLc=2 DMc=2 DWc=2 LDc=2 SLc=2 WDc=2 D_k_a=1 D_k_b=1 D_p_a=1 D_p_b=1 D_s_a=1 D_s_b=1 D_s_c=1 D_v_a=1 D_v_b=1 H_E=1 H_G=1 H_I=1 H_N=1 H_O=1 H_Y=1 LDd=1 LMc=1 LWc=1 L_f_a=1 L_f_b=1 L_f_c=1 L_p_a=1 L_p_b=1 L_p_c=1 L_u_a=1 L_u_b=1 L_u_c=1 L_v_a=1 L_v_b=1 L_v_c=1 MLc=1 MWc=1 M_c_a=1 M_c_b=1 M_c_c=1 M_d_a=1 M_d_b=1 M_d_c=1 M_l_a=1 M_l_b=1 M_l_c=1 M_s_a=1 M_s_b=1 M_s_c=1 WLc=1 WMc=1
same-position gate: where the pair's dominant class covers more than 40% of the cells, the gate reads same position excl. that class; otherwise the plain line
pairs (window reuse shown as plain/rotated, window = rows x cols):
  A-B: same position 20 (1.9%)
    same position excl. dominant D (covers 8.9% of cells, not gated): 16 (1.9%)
    weighted overlap: 0.5%
    window reuse: 1x2 0.66/0.82  2x1 0.65/0.82  2x2 0.14/0.24  3x3 0.00/0.00
    transferable blob: 17 cells (1.7% of A)
  A-C: same position 54 (5.3%)
    same position excl. dominant D (covers 8.9% of cells, not gated): 13 (1.5%)
    weighted overlap: 1.3%
    window reuse: 1x2 0.72/0.86  2x1 0.73/0.87  2x2 0.17/0.30  3x3 0.00/0.01
    transferable blob: 19 cells (1.9% of A)
  B-C: same position 39 (3.8%)
    same position excl. dominant D (covers 8.9% of cells, not gated): 36 (4.3%)
    weighted overlap: 1.7%
    window reuse: 1x2 0.71/0.86  2x1 0.67/0.83  2x2 0.14/0.28  3x3 0.00/0.00
    transferable blob: 16 cells (1.6% of B)
scene gates: PASS
```

## Gates

- piece gates: PASS
- scene gates: PASS

## Connectors

Mating classes: sides forced to share one connector shape (a contact in any solution is an edge). The smallest possible class is K(3,3), 6 sides, for tab/blank (K4, 4 sides, for andro). False fits are tab-blank pairs inside a class that touch in no solution; ratio = false fits / intended contacts.

```text
non-flat sides: 4104  profiles: andro=4104
mating classes: 3
class size min / median / max: 6 / 20 / 4078
tabs per class min / median / max: 0 / 0 / 0
blanks per class min / median / max: 0 / 0 / 0
largest class: 4078 sides (99.4% of sides), 0 tabs, 0 blanks, 4078 other
false fits: 8301139 of 5961 intended contacts (ratio 1392.575)
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
