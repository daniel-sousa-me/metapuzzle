# 10 — Motif vocabulary for background pieces

About 70% of the pieces are plain, and connector shapes cannot tell them apart (FINDINGS 25). The
remedy is small self-contained motifs assigned by region per picture, as in the reference images.
Files are in `experiments/011-subjects/motifs/` and align with `27x38-v2/tiers-*.txt`.

## Rules

- One glyph per piece, in the central 70% (margin ≥ 15%), never touching a cut, about a third of
  the piece's area, in the palette (cream, olive, navy, rust, pale blue).
- Only on **plain** cells: no lighter tier in the 8-neighbourhood. The darker cell carries every
  transition (`run_from_tiers_v4.py`), so every L cell is plain. Far cells come first; near
  cells are already anchored by a transition neighbour. No same-class motifs side by side.
- **Rotation-proof:** pieces turn between solutions, so each glyph reads at any quarter turn.
  That rules out ripple lines and gives spirals, diagonal streaks and V birds.
- One season, late winter, so the three readings belong to one world.

## Vocabulary (9 regular motifs, 6 heroes)

| Code | Motif, drawing | Tier | A hare at dawn | B owl at dusk | C swan at midnight |
|---|---|---|---|---|---|
| s | star: cream four-point sparkle | D | frost glint | owl spot; frosted branch | star |
| | | M | dew on the fur | evening star | moon-path glint |
| p | pebbles: three dots (pale blue on D, navy on L) | D | stones | wing speckles | star cluster; shore pebbles |
| | | L | flock stragglers | hare tracks in the snow | droplets on the neck |
| k | streak: cream diagonal dash with head dot | D | frost-lit furrow ridge | breast streak | meteor |
| v | chevron: small V (cream on D, navy on L) | D | seedling or rook track | belly barring | goose in a skein |
| | | L | gull | bird track in the snow | feather scallop |
| c | curl: cream spiral | M | fur whorl | wind curl | eddy; curl in the cloud |
| l | leaf: rust almond leaf with midrib | M | tawny fur flame | falling leaf | floating leaf |
| d | seed head: cream dot with eight rays | M | burr in the fur | thistledown | thistledown afloat |
| u | cloud puff: pale-blue three-lobed blob | L | cloudlet | lunar sea | lunar sea; shadow under the wing |
| f | snowflake: pale-blue six-arm flake | L | flurry; puddle frost | falling snow | snow on the back and ice floes |

Heroes (one-off pieces, counts trivially equal):

| Code | Hero | Piece class, n | A | B | C |
|---|---|---|---|---|---|
| I | amber wedge | plain L, 2 | sun's rim above the horizon | owl's irises | swan's bill tip |
| G | catchlight | D-L convex corner, 2 | frost on the hedge-tree | owl's pupils | two stars hugging the moon |
| O | crater ring | plain L, 2 | pale daytime moon; its reflection in a puddle | moon craters | moon craters |
| E | amber eye | D-on-M dot, 1 | hare's eye | crow at the sky's edge | coot on the lake |
| Y | eye glint | D-on-L dot, 1 | rook in the dawn sky | blackbird on the snow | swan's eye |
| N | beak or nose | plain M, 1 | hare's nose | owl's beak | bill reflected in the lake |

Five-petal flowers are rejected: olive is the hare and navy is the owl, so no tier lets them
read in all three pictures.

## Motif maps

**A, hare at dawn.** Sky (L): starling stragglers (p) by the flock on the left, gulls (v) over the
ears, cloudlets (u) round the cloud bank, flurries (f) in the low sky and on the puddles. Field (D):
frost (s) on the horizon and hedge-tree, furrow ridges (k) on the left, seedlings (v) on the right
strip, pebbles (p) in the foreground. Hare (M): dew (s) on the ears and head, tawny flames (l) on the
back, whorls (c) on the haunch, burrs (d) on the belly.

**B, owl at dusk.** Sky (M): evening stars (s) dense at the top, leaves (l) beside the owl, wind
curls (c) low on the sides, thistledown (d) along the snow line. Owl (D): spots (s) on the crown,
shoulders and branch, streaks (k) on the breast, barring (v) on the belly, speckles (p) on the
wings. Moon and snow (L): seas (u) on the moon, snowflakes (f) in the halo and snow, bird tracks
(v) on the left, hare tracks (p) on the right.

**C, swan at midnight.** Sky (D): stars (s) dense at the top and thinning down, a cluster (p) top
left, meteors (k) mid-sky, geese (v) round the moon, pebbles (p) on the shore. Lake (M): curls (c) in
the cloud and beside the swan, the moon path (s) lower right, leaves (l) lower left, thistledown
(d) at the bottom. Swan and moon (L): droplets (p) on the head and neck, scallops (v) on the near
wing, snow (f) on the back and the ice floes, seas (u) on the moon and under the wing.

## Class counts (identical by construction; `motif-counts.txt`)

| Class | A | B | C | | Class | A | B | C |
|---|---|---|---|---|---|---|---|---|
| s D | 22 | 22 | 22 | | c M | 40 | 40 | 40 |
| p D | 12 | 12 | 12 | | l M | 34 | 34 | 34 |
| k D | 10 | 10 | 10 | | d M | 28 | 28 | 28 |
| v D | 14 | 14 | 14 | | u L | 30 | 30 | 30 |
| s M | 32 | 32 | 32 | | v L | 28 | 28 | 28 |
| p L | 26 | 26 | 26 | | f L | 34 | 34 | 34 |
| heroes I, G, O | 2 each | | | | heroes E, Y, N | 1 each | | |

That gives 319 motif pieces per picture (31%). All land in their intended regions, except three
owl spots that fall elsewhere on the owl, where they read the same. The script checks that each
hero sits on the same piece class in A, B and C. For the role solver, each (motif, tier) pair is a
sub-class of plain D, M or L, like the v4 chips. The maps are its region preferences, and the
faint chips can stay on unmarked pieces.

## How solving changes

1. **Sort by tier, then by motif.** There are 12 piles of 10–40 pieces (plus heroes) instead of three of 100–300.
2. **Pile to region.** Each pile names a place in the picture being built: curls go to the haunch,
   the low dusk sky or the swan's eddies, and meteors to the middle sky. Heroes go in at once.
3. **Within a region, shape decides.** The cut against neighbours already placed settles the
   piece, and the motif pieces become a scaffold.
4. **Plain pieces go in last.** 85% of the remaining plain pieces have at least two distinctive
   neighbours (a motif or transition piece). They fill holes instead of being built up as open
   patches. The largest motif-free patch is 48 / 32 / 23 cells (the hare's flank, the owl's belly,
   the swan's neck), against more than 200 before.

**What stays plain:** 404 / 396 / 372 pieces (39 / 39 / 36%), down from about 70%. About half of
them touch a transition piece, and the hard core (no other tier nearby) is about 19%. The residual
ambiguity is a swap of two same-class pieces inside one region. Count variants (one to three
glyphs, which also gives C's star gradient) or colour variants, matched the same way, would cut it
further.

## Risks

- Density: the hare carries 135 marks (46% of its plain cells). Check its figure-ground reading in
  the blind test (T1) before adding more.
- The weakest readings are burrs on the hare, the crow, the coot and the droplets on the swan.
- These maps use the unequalized tiers. Rerun the script on `tiers-eq-*` before the role solve.
