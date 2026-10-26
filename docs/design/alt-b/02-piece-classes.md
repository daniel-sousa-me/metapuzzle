# B-02 — Piece classes (direction B, 14 classes)

All recipes use the JSON class-spec model in `src/metapuzzle/classes.py`: a stack of layers, each a primitive with a palette and params, optionally clipped by a `blotch_mask`. Sizes are fractions of the piece side (`ref_size` 100). Palette keys are from B-01 §4.

`dabs`, `mosaic` and `scatter_shapes` pick mark colours uniformly, so **repeat a key to weight it**. For example, `["teal","sea","sea","sea","leaf"]` gives about 25% leaf chips.

**Every class is non-directional and allows all four rotations.**

## 0. Shared layers

- **BINDER** (last layer of every class, `background: false`): `stipple`, palette `["paper","paper","plum"]`, `density 40`, `radius [0.006, 0.014]`.
- **MIX(X over Y)**: the full layer stack of field Y, then the field layers of X with `mask: {"primitive":"blotch_mask","params":{"coverage":0.42,"side":null,"count":2}}`, then BINDER. The 0.42 coverage gives a blob of about 1/3 to 1/2 of the piece area. Seeds vary the blob count and position.

## 1. Fields (6)

**`BL` sky_blue**. Pale blue ground with fine paper chips and a few soft cloud flecks.
- Layer 1: `stipple ["sky","paper","paper","gold"] density 220 radius [0.010,0.025]`.
- Layer 2: `scatter_shapes ["sky","paper"] kinds ["blob","disc"] count 8 scale 0.08`.
- BINDER.

**`CR` cream**. Warm paper ground with sky and gold chips: a bright cloud mass, foam, or a lily blossom.
- Layer 1: `stipple ["paper","sky","sky","gold"] density 160 radius [0.010,0.030]`.
- Layer 2: `scatter_shapes ["paper","sky"] kinds ["blob"] count 6 scale 0.10`.
- BINDER.

**`GD` gold_dabs**. Dense gold ground of short broad dabs, with amber and a few ochre dabs.
- Layer 1: `dabs ["gold","amber","amber","gold","ochre"] count 70 length 0.20 width 0.07 shape "mixed"`.
- BINDER.

**`OC` ochre_mosaic**. Jittered ochre tesserae with umber gaps and the occasional gold chip.
- Layer 1: `mosaic ["umber","ochre","ochre","ochre","amber","gold"] tess 0.17 gap 0.18 jitter 0.25 shade 0.20`.
- BINDER.

**`TE` deep_teal**. Dark teal ground with sea-green ellipse dabs and rare plum and leaf dabs.
- Layer 1: `dabs ["teal","sea","sea","sea","plum","leaf"] count 60 length 0.20 width 0.06 shape "ellipse"`.
- BINDER.

**`GR` leafy_green**. Leaf-green ground scattered with sea and teal leaf shapes and a few paper flecks.
- Layer 1: `scatter_shapes ["leaf","sea","sea","teal","paper"] kinds ["leaf"] count 40 scale 0.09`.
- BINDER.

## 2. Mixes (5) and features (3)

The mixes are the transitions. They have `side: null`, so they work on any side of a mass and in any rotation.

- **`CB` cloud_on_blue**: MIX(CR over BL). A soft cream cloud in blue.
- **`GB` gold_on_blue**: MIX(GD over BL). A gold blob on a light ground.
- **`GT` gold_on_teal**: MIX(GD over TE). A gold blob on a dark ground: the highest-contrast class and the main "figure" piece.
- **`OG` ochre_gold**: MIX(GD over OC), coverage 0.35. Gold breaking into tesserae.
- **`NT` green_on_teal**: MIX(GR over TE). A leaf-green blob on dark teal.

Features are single motifs fully inside the piece (8% margin, enforced by `motif`):

- **`SU` sun_disc**. The BL layers, then `motif ["sky","paper","gold"] kind "disc" scale 0.50 halo 0.6 color_index 1 halo_color_index 2 rotation "none"`, then BINDER. A pale disc with a gold halo.
- **`DK` dark_on_gold**. The GD layers, then `scatter_shapes ["gold","plum"] kinds ["leaf","blob"] count 3 scale 0.07`, then BINDER. Two to four small plum marks on gold. The count of 3 is per 100×100, so it gives about 3 marks; vary it by seed only.
- **`DT` dark_on_teal**. The TE layers, then `motif ["teal","plum"] kind "leaf" scale 0.34 rotation "any"`, then BINDER. One dark leaf-shaped silhouette, deliberately not a fish or a boat.

## 3. What each class reads as

| Code | Count | A: Sunflower | B: Sunset Bay | C: Koi Pond |
|---|---|---|---|---|
| `BL` | 12 | open sky behind the head | high sky | sky reflected at the far bank and in the sun pool |
| `CB` | 3 | small cloud | cloud | reflected cloud |
| `CR` | 4 | bright cloud; light between leaves | sunlit cloud; shell/foam on the dunes | water-lily blossom |
| `SU` | 1 | the sun (upper right) | the setting sun on the horizon | the sun's reflection in mid-pond |
| `GD` | 5 | petals | sunset glow | koi body |
| `GB` | 6 | petal tip against sky | gilded cloud edge | koi in pale shallows |
| `GT` | 7 | petal tip over leaves | sun glitter on the sea | koi over deep water |
| `DK` | 3 | bees on the petals | gulls against the glow | spotted koi |
| `OC` | 9 | seed head | sand | stepping stones |
| `OG` | 3 | seed head where petals overlap it | wet sand catching light | stone with a koi nosing it |
| `TE` | 11 | shaded big leaves | sea | deep water |
| `NT` | 10 | leaf with lit patch | kelp shallows; dune scrub | lily pad on dark water |
| `GR` | 3 | sunlit leaf | dune grass | bankside reeds and pads |
| `DT` | 3 | curled shadowed leaf | small dark boat or rock | black koi |

Total: 80 pieces, 14 classes. The same histogram is used in all three scenes.

### Colour families

| Family | Classes | Pieces |
|---|---|---|
| sky | BL, CB, CR, SU | 20 |
| gold | GD, GB, GT, DK | 21 |
| ochre | OC, OG | 12 |
| teal/green | TE, NT, GR, DT | 27 |

### Design notes for implementers

- **Feature pieces are the context-dependent readings** HANDOFF §6.2 asks for:
  - `SU` is a source (the sun) in A and B, and a reflection in C. Surrounded by sky in A, by gold glow in B, by dark water in C.
  - `DK` marks are pollinators, birds or fish spots, depending only on whether the gold around them is a petal ring, a glow band or a fish-shaped cluster.
  - `DT` must stay generic. A drawn fish or boat would pin it to one scene, so use `leaf`, never `fish`/`boat`.
- **Class distinctness for solving.** The fields differ in hue and mark type, so a piece sorts into its class at a glance: dots (BL, CR), dabs (GD, TE), tesserae (OC), leaves (GR). Within a class, a piece is anonymous by design; its seed variation is only the blob layout of the mixes.
- **The two contrast pairs to watch** are GT (gold on teal) and GD next to TE. They create the strongest figure/ground and the most visible seams; B-03 keeps GD from touching TE.
- **Blotch shape for koi.** Round blotches read as koi only in clusters of two or three pieces. If the blind test (B-04) shows that C does not read as fish, the first fix is an optional `blotch_mask` aspect/elongation parameter (about 1.8:1, random angle) for GD-over-X mixes. Do not use `motif kind "fish"`: it would make the pieces C-only.
