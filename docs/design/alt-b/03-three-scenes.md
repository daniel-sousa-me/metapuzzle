# B-03 — Three scenes (direction B, 8 columns × 10 rows)

Machine-readable maps: `docs/design/alt-b/scenes-8x10-b.txt` (engine text format). Coordinates below are (row, col), counted from 0 at the top left.

## Legend

| Family | Codes |
|---|---|
| Sky | `BL` sky blue · `CB` cloud on blue · `CR` cream · `SU` sun disc |
| Gold | `GD` gold dabs · `GB` gold on blue · `GT` gold on teal · `DK` dark marks on gold |
| Ochre | `OC` ochre mosaic · `OG` ochre with gold |
| Teal/green | `TE` deep teal · `NT` green on teal · `GR` leafy green · `DT` dark leaf on teal |

## A — The Sunflower (radial)

```
     0  1  2  3  4  5  6  7
 0  BL BL BL CB CR BL BL BL
 1  CB BL CB GD GB BL SU TE
 2  CR GD GD DK GD DK GB BL
 3  BL GB OG OC OC OG GB BL
 4  BL GB OC OC OC OC GD GB
 5  NT GT OC OC OC OG GT NT
 6  TE GT GT DK GT GT GT GR
 7  TE TE TE TE TE CR TE TE
 8  NT NT DT TE TE NT DT DT
 9  NT NT CR GR GR NT NT NT
```

**What to recognize.** A close-up sunflower head filling the upper two-thirds:

- A 4×3 **seed head** of ochre tesserae at rows 3–5, cols 2–5. Its corners are rounded by `OG`.
- A **ring of gold petals** around it. Petal tips sit on blue in the upper half (`GB`) and on dark leaves in the lower half (`GT`).
- Big shaded **leaves** fill rows 6–9, with light gaps (`CR`).
- Sky and clouds at the top, and the sun at (1,6).

The gestalt is a bright ring around a darker textured disc, which reads at any distance. Feature readings: the three `DK` are bees on the petals, `SU` is the sun, and `DT` are curled leaves in shadow.

## B — Sunset Bay (horizontal bands)

```
     0  1  2  3  4  5  6  7
 0  BL BL CR BL BL BL CB BL
 1  BL CB BL GB BL GB CR BL
 2  BL GB GB GD GB GD GD GB
 3  CB DK GD SU GD DK DK BL
 4  TE TE GT GT DT TE TE TE
 5  TE TE TE GT GT TE TE DT
 6  NT DT GT GT GT NT NT TE
 7  NT OC OC OC OC OC OC NT
 8  CR OG OG OC OG OC OC GR
 9  NT NT GR CR NT GR NT NT
```

**What to recognize.** Five bands:

1. High sky with gilded clouds (rows 0–1).
2. A gold sunset glow (rows 2–3), with the **sun sitting on the horizon** at (3,3).
3. A dark sea (rows 4–6), with a **glitter path** of `GT` running down from the sun (cols 2–4).
4. A sand beach (rows 7–8, cols 1–6).
5. Dune scrub along the bottom.

The sea horizon is the one place where direction B *accepts* a straight cut line. A sea horizon is straight in reality, and any sky piece above any sea piece produces it, so it requires no specific neighbour. Feature readings: `DK` are gulls against the glow, `DT` are small dark boats or rocks, `SU` is the setting sun.

## C — Koi Pond (scattered, diagonal path)

```
     0  1  2  3  4  5  6  7
 0  BL CB BL BL BL CR BL BL
 1  CR GT GD BL CB OC OC DT
 2  NT TE GT GB OC OC DK GR
 3  TE GT TE TE OG TE GT GB
 4  NT GD DK OG TE GT GB BL
 5  BL NT GD OG SU CR DT TE
 6  BL TE OC OC BL GB GD NT
 7  CB GB OC DT DK TE GT BL
 8  TE OC OC GD GB GT NT TE
 9  NT GR NT NT CR NT GR NT
```

**What to recognize.** A dark pond seen from above:

- **Stepping stones** (`OC`/`OG`, 12 pieces) meander diagonally from the top right (1,5)–(1,6) to the bottom left (8,1)–(8,2).
- **Six koi** of 1–4 gold pieces each, on either side of the path, for example (1,1)–(2,3) and (3,1)–(5,2). `DK` gives them spots.
- **Three black koi** (`DT`).
- A pale **pool of reflected sky** with the sun's reflection at (5,4).
- Lily pads (`NT`), reeds (`GR`) and blossoms (`CR`) at the banks.
- The far bank (row 0) reflects the sky.

This is the only scene with no up/down. It works as a top-down view.

## Verification (scratch script plus the engine)

`scene.validate_scenes(..., strict_border=True)` passes for both `rotation="none"` and `"quarter"`.

**Histogram (identical in A, B, C; 80 pieces, 14 classes):**

| | BL | CB | CR | SU | GD | GB | GT | DK | OC | OG | TE | NT | GR | DT |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Count | 12 | 3 | 4 | 1 | 5 | 6 | 7 | 3 | 9 | 3 | 11 | 10 | 3 | 3 |

**Border class counts per side** (identical in A, B, C; corners counted on both of their sides):

| Side | Counts |
|---|---|
| Top | BL 6, CB 1, CR 1 |
| Bottom | NT 5, GR 2, CR 1 |
| Left | BL 3, NT 3, TE 2, CB 1, CR 1 |
| Right | BL 3, TE 2, NT 2, GB 1, GR 1, DT 1 |

The corners are also fixed per slot, as the engine requires: NW `BL`, NE `BL`, SW `NT`, SE `NT`.

**Class carry-over** (cells with the same class at the same position):

| Pair | Cells | Share | Border /32 | Interior /48 | Largest carried patch |
|---|---|---|---|---|---|
| A–B | 11 | 14% | 9 | 2 | 2 cells |
| A–C | 7 | 9% | 7 | 0 | 2 cells |
| B–C | 7 | 9% | 6 | 1 | 2 cells |

Random placement of this histogram gives 7.7 cells, so the scenes are near the floor. The floor comes from the four corners, which the engine fixes, plus the top row (6 of its 8 cells are `BL`).

**Colour-family carry-over** (same family at the same cell) is the honest residue: 40, 34 and 33 of 80 cells, against 21 for random placement. About 20–25 of these are on the border, where the top row is pale and the bottom row is green-teal in every scene. Pieces there are not interchangeable across classes, but a player will learn "pale pieces go on top". The interior family carry-over is near random (14–15 of 48).

**Hard seams** (two plain fields of different families on a cut line): A 9, B 6, C 14 of 142 internal edges. Gold never touches teal directly.

## How the grids were made (repeatable method)

Each scene was first drawn as a **role map**: a grid of semantic roles such as "seed head", "petal tip against sky", "sea", "stone" or "koi". Each role allows a short, ordered list of classes. A small annealer then chose one class per cell, subject to three things:

- identical histograms and border counts (the hard constraints);
- minimum class carry-over across all pairs;
- preference order within roles.

A final pass swapped classes within roles to reduce hard seams and to keep `GB` beside light cells and `GT` beside dark ones. Engineers should adopt **role maps as the authored artefact** and treat class maps as solver output. The script lives in the designer's scratchpad; porting it into the engine is a small task.

## Scaling to ~500 pieces

- **Keep the families and the materials-not-objects rule.** Scale each class count by about 6 (480 = 20×24). At this resolution the masses become shapes, not blocks: about 40 petal pieces, a 10×8 seed head, a 15-piece glitter path, 15–20 koi.
- **Add second-tier classes** (18–22 in total) by splitting the busiest fields into two densities (for example `TE`-calm and `TE`-busy). This gives solvers finer sorting cues without new hues.
- **The border share falls from 40% to 17%,** so border-driven carry-over (the main residue here) drops by more than half.
- **Re-run the role-map annealer at full size** with the adjacency optimizer.
