# B-01 — Visual grammar: "Garden Terrazzo" (direction B)

Status: alternative proposal (direction B), 2026-10-26. It is written to be compared against the brief in `docs/design/01–06`. It shares that brief's 8×10 frame and engine constraints, and targets the problem found there: **class carry-over**.

## 0. The problem this direction is built around

A landscape trio (sky band on top, ground at the bottom in every image) puts the same class in the same cell for most of the board. Same-class pieces are interchangeable, so a player can leave those regions assembled and rework only the middle. Zero shared *piece* adjacency does not prevent this.

Direction B therefore makes three commitments:

1. **No global gravity in the vocabulary.** Every class is non-directional. There are no side-biased transitions and nothing that only works "above" something else. Only one of the three scenes (the sunset) has an up/down structure at all.
2. **Three different layout gestalts:** one radial (Sunflower), one horizontal bands (Sunset Bay), one scattered along a diagonal path (Koi Pond). They place each colour family in different regions.
3. **Every class is a material, not an object part.** Each class has a different reading in each scene. Gold dabs are petals, sunset glow and koi bodies. Ochre mosaic is a seed head, a beach and stepping stones.

Result (checked by script, see B-03): 7–11 of 80 cells carry the same class at the same position per scene pair (9–14%), against 7.7 for random placement. The largest carried-over patch is 2 cells.

## 1. Style direction: Garden Terrazzo

Terrazzo is chips of coloured stone set in a shared binder. Two slabs of different chip mixes can butt against each other and the joint reads as a change of mix, not as a crack. That is the property we need at piece boundaries. The look is close to a mid-century mosaic or a speckled risograph print: flat mid-value grounds, dense small chips, a few soft blobs, and no line work at all.

Three devices carry the style.

- **Shared binder.** Every class, without exception, ends with the same sparse speckle of paper and plum dots (the last layer of every recipe in B-02). Every piece therefore shares one micro-texture, and a seam between two classes is a change of colour proportion, not a change of texture grammar.
- **Cross-seeded chips.** Each field class carries 10–15% of the chip colour of its most common neighbours: ochre chips in gold, gold chips in ochre, paper chips in sky, sea-green chips in teal. Where two fields meet on a cut line, both sides already contain a little of the other.
- **Soft blotches as the only large shapes.** Transitions are a base field plus a second field clipped to a `blotch_mask` with `side: null`. The boundary between two materials is a wobbly blob *inside* the piece, and it works in any orientation.

## 2. Justification against HANDOFF §4–6

| Handoff item | How Garden Terrazzo answers it |
|---|---|
| §4 gradients, large uniform regions | Flat grounds always carry 150–250 chips per piece. Tone changes happen through chip proportion between classes, never as a ramp inside a piece. |
| §4 long lines, large outlines | No strokes, no outlines. The longest mark is a dab of 0.24 × side, and objects are made of blobs and chips. |
| §4 directional textures, lighting, perspective | Dabs, leaves and tesserae use random angles. Mosaic jitter is 0.25 of pitch, so it reads as stones, not a grid. There is no light direction and no horizon geometry. |
| §4 unique colour associations | Every colour appears in at least two roles in every scene (table in B-02 §3). Gold is never "only petals". |
| §4 strict orientation | All 14 classes allow all four rotations, so the same art serves the no-rotation and quarter-rotation experiments. |
| §5 piece-boundary problem | Binder and cross-seeding hide same-family seams. The scene grids are tuned so that only 6–14 of 142 internal edges per scene are "hard seams" (two plain fields of different colour families). |
| §6.1 low dependence on neighbours | No mark continues across an edge on purpose. Marks are padded past the cell edge at uniform density (primitive convention), so same-class seams vanish. |
| §6.2 context-dependent reading | Materials, not objects: one class reads as three things (B-02 §3). |
| §6.4 multi-scale | Three scales coexist: chips (1/6 of a side), blotches (2/3 of a side), and scene masses of 4–20 pieces. |
| §6.7 distributed information | The four colour families sit in different regions in each scene: the gold ring of A, the gold band of B, the gold koi scattered through C. |

## 3. Rejected alternatives

- **Gravity landscapes with side-biased horizon transitions** (my own first draft and the landscape family generally). They read beautifully, but sky-over-ground forces the same classes into the top and bottom rows of every image. My draft carried 55–60 of 80 cells between scene pairs, which defeats HANDOFF §1 (reassembly from scratch).
- **Fine pointillism or "realistic" stipple** (marks of 1/20 of a side or less). At 80–500 pieces the marks are too small to give a piece identity: every sky piece looks identical (HANDOFF §9 "indistinguishable pieces"). Pointillism also needs smooth value ramps to model form, which are gradients by another name.
- **Bold cut-paper silhouettes** (Matisse-like). They are very legible, but the shapes are large outlines that cross piece edges and require exact continuation (HANDOFF §4 rows 2–3, §5).

## 4. Palette (10 colours)

Names match the JSON class-spec palette keys.

| # | Key | Hex | Value | Role |
|---|---|---|---|---|
| 0 | `paper` | `#F2E8D5` | light | Cream ground, cloud and lily chips, light binder speck |
| 1 | `sky` | `#9EC3D6` | light | Sky / reflected sky ground |
| 2 | `teal` | `#2F5E5E` | dark | Deep water, sea and shaded-leaf ground |
| 3 | `sea` | `#4F8278` | mid-dark | Chips in teal, leaf-shape marks |
| 4 | `leaf` | `#7FA65A` | mid | Green ground and leaf blotches |
| 5 | `gold` | `#E8B23A` | mid-light | Petals, glow, koi ground (the brightest saturated colour) |
| 6 | `amber` | `#D9822B` | mid | Chips in gold and ochre, koi accents |
| 7 | `ochre` | `#B98A4E` | mid | Tesserae: seeds, sand, stones |
| 8 | `umber` | `#6E5236` | mid-dark | Mosaic gaps, the seed-head darkness |
| 9 | `plum` | `#3B2A3A` | dark | Silhouettes (bees, gulls, koi spots), dark binder speck |

The value plan is what makes the scenes legible at 8×10. Gold (bright, saturated) against teal (dark) is the main figure/ground contrast in all three scenes, but gold forms a ring, a band and scattered islands respectively. Sky and paper are the light family. Ochre and leaf are mid-tone buffers.

## 5. Mark scale (piece side = 1; the spec's `ref_size` 100 = one side)

| Mark | Size | Per piece |
|---|---|---|
| Binder specks | radius 0.006–0.014 | about 40 (grain, not counted as marks) |
| Chips (stipple) | radius 0.010–0.025 | 150–250 |
| Dabs, leaves, tesserae | 0.17–0.24 long (≈1/6–1/4) | 25–70 |
| Soft blotch (transition) | radius 0.30–0.35, 1–2 per piece (≈2/3 of the side across) | 1–2 |
| Motif (sun disc, dark leaf) | enclosing diameter 0.34–0.50 (1/3–1/2) | 1 |

## 6. How boundaries look

- **Same class:** invisible at arm's length. The marks are padded past the edge at uniform density (see `textures-demo.png`).
- **Field next to its own mix** (sky next to gold-on-blue, teal next to gold-on-teal): the ground continues across the cut. The visible boundary is the blotch edge inside the mix piece, which is ragged, round and never aligned with the grid.
- **Field next to a field of the same family** (sky next to cream, teal next to green): a soft change of chip proportion, hidden by the binder.
- **Hard seam** (two plain fields of different families meet on a cut line): the only place the grid can show. Budget: at most 10% of internal edges per scene (currently 6, 9 and 14 of 142). High-contrast pairs (gold against teal, sky against teal) should have a mix piece between them; the grids in B-03 were optimized for this.
