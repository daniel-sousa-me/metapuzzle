# 004 density-field mosaic

**Goal:** three tone maps (cat, sailboat, tree) at 20x25 that share one exact class histogram from six rank-quantized classes.
**Result:** quarter rotation gives 0/0/0 shared and distinctiveness 4/5; the tree is recognized, the cat is not, and the grid is fully visible (5/5).

**Idea.** Every piece is a mixture of non-directional stipple dapples. The picture is a tone map, like a halftone. Six classes T0 (darkest) to T5 (lightest) step from navy and charcoal to khaki, sky and cream. Neighbours share mark colours. Three targets share one exact class histogram by rank-based quantization.

**Targets** (`make_targets.py`, 25 x 20): cat (dark sitting silhouette, ears, curled tail, light ground), sailboat (light sky, mid sea, dark hull, light sail), tree (dark round canopy and trunk, light sky, mid ground band).

**Quantization** (`quantize.py`). Every map has counts 60/90/100/100/90/60. Ties in flat regions are broken by a seeded random key. The validator also needs a shared frame: one class per corner and one histogram per side. Interior cells are ranked separately, so global counts stay exact.

**Piece-level shared adjacencies** (summary.md)
- quarter: AB 0, AC 0, BC 0.
- none: AB 0, AC 1, BC 0.

**Scene metrics** (`scene-metrics.txt`; exit 3 because gates fail)

| pair | same-position | 2x2 reuse plain/rot | transferable blob |
|---|---|---|---|
| A-B cat/sailboat | 23.2% | 0.44 / 0.68 | 23 cells (4.6% of A) |
| A-C cat/tree | 25.0% | 0.57 / 0.76 | 12 cells (2.4% of A) |
| B-C sailboat/tree | 17.0% | 0.80 / 0.90 | 20 cells (4.0% of B) |

Piece gates pass. Scene gates fail: 2x2 reuse is above the 30% limit for all pairs, and A-C same-position sits at the 25% limit.

**Visual assessment** (`run-quarter/triptych.png`, `quantized-preview.png`)
- Tree: recognizable at a glance.
- Sailboat: sail, mast and hull read, but the sea/sky boundary is ragged.
- Cat: not recognizable at a glance. The dark mass and tail show, but the ears and head dissolve into the dithered light ground.
- Different pictures? Tree and sailboat clearly differ. All three share the same dapple texture and light-ground mix, so they look related.

Verdict: the rank rule keeps the dark masses but spreads each light ground over four classes. The idea needs graded targets, or a different rule for flat regions.
