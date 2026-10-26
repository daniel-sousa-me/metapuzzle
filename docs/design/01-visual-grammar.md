# 01 — Visual grammar: "Dapple Mosaic"

Status: proposal for the first prototype (8 × 10, no rotation). Owner decisions assumed: procedural art, recognizable scenes, rotation is an experiment variable (see DECISIONS.md).

## 1. The direction in one paragraph

**Dapple Mosaic** is a pointillist mosaic. Every piece is a field of small, irregular, rounded "dabs" (soft tesserae), each 1/6 to 1/3 of a cell across, drawn from a small sub-palette of 3–4 tones per material. There are no outlines, no gradients, no shading and no long strokes. Pictures are built from **materials** (sky, snow, meadow, foliage, deep water, rust) laid out at the scale of the piece grid. Region boundaries never run along a cut. Instead they run *inside* special transition pieces, along a slightly ragged line that is **pinned to the cell corners**. Think of a Roman floor mosaic seen through Seurat. At arm's length you see flat, posterlike shapes (tree, sail, peak). Up close you see a lively stochastic texture that does not care which neighbour it has.

## 2. Why this direction (against HANDOFF §4, §5, §6)

| Handoff concern | How Dapple Mosaic answers it |
|---|---|
| §4 gradients, large uniform regions | No gradients at all. A large region is a *field* of dabs whose tones vary randomly, so it is never flat. Uniformity sits in the statistics, not in the pixels. |
| §4 long lines, large outlines, precise continuation | There are no drawn lines. A shape's outline is the boundary between two dab materials. Where it crosses a cut it is pinned to a cell corner, so it always continues (see §6). |
| §4 lighting, perspective, scale | Everything is flat and frontal, with no cast shadows and no vanishing points. Depth comes only from overlap and from a cooler, darker "far" material. |
| §4 directional textures | Dab orientation is uniformly random. Directional transition pieces exist, but their direction is fixed by the scene grid, and rotation mode is out of scope for this file. |
| §4 unique colour associations | Every material has 2–3 readings across the scenes (sky/mist, snow/sail/cloud, deep = sea/lake/mountain, rust = trunk/boathouse/cabin). No colour belongs to only one subject. |
| §5 piece boundary problem | Within a material, a cut separates two samples of the same random process, so it is statistically invisible. Across materials, the cut either falls inside a transition piece (no colour change at the cut) or sits between "soft pairs" of close value (§5). |
| §6.1 independence from neighbours | Each piece is rendered from (class, seed) only. No piece reads its neighbour's pixels. |
| §6.2 context-dependent reading | Feature pieces and whole tile clusters change meaning with context (03-three-scenes.md). |
| §6.4 multi-scale | Dabs carry close-up interest, materials carry mid-scale structure, and the scene silhouette carries the global read. |
| §6.5 tolerance of discontinuity | Pointillist texture *is* discontinuity, so a mismatch reads as more texture. |

### Alternatives considered and rejected

1. **Cross-stitch / pixel sampler.** Each piece is a block of stitches, and the grid becomes the aesthetic. It is cheap and honest, but it makes the piece grid the organising structure of the image, which is exactly the §5 failure. Stair-stepped silhouettes at 8×10 also read as low-resolution icons, not as pictures.
2. **Flat paper cut-out (Matisse / Charley Harper).** Bold, very recognizable shapes. But it relies on large uniform colour areas and crisp continuous outlines (§4 rows 1–3). Every cut through a flat area shows the knob profile.
3. **Engraving / directional hatching.** Rich and multi-scale, but hatch direction encodes form and lighting, so it fails §4 "directional textures" and "lighting".
4. **Millefleur tapestry** (scattered small motifs on a dark ground). This was partly adopted: the accent sprigs in meadow and foliage come from it. On its own it gives one texture, not three scenes.

## 3. Palette

Eight named colours define the materials. Each material uses its base plus 2–3 dab tones. Values (L*) are approximate, and the ordering is what matters.

| Token | Hex | Approx L* | Role |
|---|---|---|---|
| `sky` | `#A9CBE3` | 80 | ground of SK, upper half of every skyline transition |
| `sky_dab` | `#8DB8DA` / `#C9DEEC` | 73 / 87 | dab tones in sky |
| `snow` | `#F2EDE1` | 94 | SN, white part of S/ S\, HL fleck |
| `snow_dab` | `#FFFFFF` / `#DED6C4` / `#D3DFEA` | — | dab tones in snow (the last is a sky tone, shared) |
| `meadow` | `#A9BF63` | 74 | ME ground |
| `meadow_dab` | `#8EAD4B` / `#C7CF7C` / accent `#E2C35A` | — | grass dabs, sparse yellow flower specks |
| `foliage` | `#4F7B44` | 48 | FO, lower part of F/ F\ |
| `foliage_dab` | `#3B6537` / `#6B904D` / `#2F5A50` | — | the last is a blue-green, shared with deep |
| `deep` | `#34477A` | 31 | DP, lower part of HD/HB/HL |
| `deep_dab` | `#26355F` / `#4A5F95` / `#2F5A6E` | — | the last is teal, shared with foliage; sparse glints `#DCE6EE` |
| `rust` | `#A65233` | 46 | RU, PH ground, hull in HB |
| `rust_dab` | `#8A3F28` / `#C26A43` | — | |
| `gold` | `#F2C14E` | 81 | sun disc, rim of the PH window |
| `ink` | `#2A2430` | 16 | PH window interior, the only near-black |

Material → class mapping: SK, SU → sky. SN, S/, S\ → sky + snow. ME → meadow. FO, F/, F\ → sky + foliage. DP → deep. HD, HB, HL → sky + deep (+ rust or snow accent). RU, PH → rust (+ gold, ink).

**Shared dab tones** link value neighbours: snow↔sky share `#D3DFEA`, foliage↔deep share teal-green, and meadow↔foliage share `#6B904D` and `#8EAD4B`. In every field piece about 8–12 % of dabs come from the neighbouring material's palette ("spill dabs"). This is what lets two different materials meet at a cut without looking like a seam.

### Soft pairs (the seam rule)

Two different materials may meet directly at a cut only if they are a **soft pair**:

- `sky – snow` (ΔL ≈ 14)
- `meadow – foliage` (ΔL ≈ 26, softened by shared dabs)
- `foliage – deep` (ΔL ≈ 17, softened by shared teal)

`rust` may touch anything, but only as a short object edge of 1–3 cuts (trunk, hull, cabin). Every other pair (sky–foliage, sky–deep, snow–deep, meadow–deep, snow–foliage, …) is **forbidden at a cut** and must be resolved inside a transition piece. The checker script used for 03-three-scenes.md enforces this. The three prototype scenes have **zero forbidden seams**.

## 4. Mark vocabulary

All sizes are in cell units (cell = 1.0; render each cell at 256–512 px).

| Mark | Shape | Size | Used in |
|---|---|---|---|
| **Dab** | Rounded irregular polygon: 6–9 vertices on a circle with ±25 % radial jitter, slight ellipse (aspect 1.0–1.6) at a uniformly random angle | diameter 0.16–0.30 | every material, 30–45 per cell, overlapping, painted back to front |
| **Speck** | Tiny dab | 0.04–0.07 | glints in deep, flower specks in meadow, stars of light in foliage. 0–6 per cell |
| **Sprig** | 3–5 short tapered strokes radiating from a point, at random angles | 0.12–0.20 span | meadow (grass tufts) and foliage (leaf clusters). 1–4 per cell. Never longer than 0.25 |
| **Disc** | Circle drawn as a ring of gold dabs filled with paler gold dabs | diameter 0.45–0.55 | SU only |
| **Wedge** | Small filled triangle or trapezoid made of dabs | 0.25–0.45 | HL (white fleck/sail), HB (rust hull/hut) |
| **Window** | Rounded rectangle, ink interior, gold rim of dabs | 0.28–0.36 × 0.36–0.46 | PH only |

**Mark scale rule.** The largest generic mark is at most 1/3 of a cell, so a cell always holds many marks. No cell is a single motif. Features are at most about 0.55 of a cell, always sit on full field texture, and are offset randomly from the centre (±0.15) so features do not form a lattice.

## 5. Transitions: "edges are pure, boundaries go through corners"

Every piece edge carries **one** material along its whole length. A region boundary may enter or leave a piece **only at a corner**. This gives three skyline shapes:

- `/` (left flank): the boundary runs from the bottom-left corner to the top-right corner. Sky is upper-left and mass is lower-right. Edge materials: top = sky, left = sky, right = mass, bottom = mass.
- `\` (right flank): mirror image.
- `H` (horizon): the boundary is pinned to the **top** two corners and dips into the cell as 2–4 irregular troughs (depth 0.10–0.40), touching the top edge again between troughs. Edge materials: top = sky, left/right/bottom = mass.

Because every edge is pure, **any two pieces whose shared edges carry the same material meet invisibly in material terms, whatever their seeds.** Flanks chain diagonally (`/` at (r,c) continues to (r-1,c+1)). A `/` beside an `H` continues the line at the shared top corner. A `/` beside a `\` forms a peak. The internal troughs of `H` are as deep as the corner pins, so the pins are not periodic landmarks.

The boundary line itself is a ragged polyline: 12–20 points between the two pins, perpendicular jitter ±0.06, and for flanks a random convex bulge of 0–0.12. Dabs are clipped to their side of the line, and on each side 15 % of the dabs within 0.1 of the line borrow the other side's spill tones, so the line is a "dappled" edge, not a vector edge.

## 6. Seams in practice

- **Same class:** the edge has the same ground colour on both sides and the same dab statistics. Dab centres are placed over the cell plus a 0.25 bleed (because tabs extend into the neighbour's cell), then the result is clipped to the actual piece outline. No margin, frame or vignette is ever drawn near an edge.
- **Soft pair (e.g. foliage | deep):** a change of dominant hue at roughly equal value, with spill dabs on both sides. It reads as a soft painterly edge. Because it runs along the cut, the knob profile is faintly visible, which is why soft pairs are limited to the three listed above.
- **Transition piece:** no change at the cut at all. The change happens inside the piece.
- **Rust objects:** a hard edge, deliberately limited to small objects of 1–3 cells.

## 7. What the renderer needs (summary)

`render(class_id, seed, outline) → image`. Each class is a recipe: ground colour, dab palette with weights, dab count range, optional boundary type, optional feature. A scene is a grid of class IDs plus a permutation that maps physical pieces to cells. The seam checker (edge-material table plus the soft-pair list) should run on every candidate scene. Class recipes are in 02-piece-classes.md.
