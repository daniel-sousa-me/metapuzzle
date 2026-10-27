# 08 — Subjects: "Field, Wood and Water"

Subjects for the hybrid tone-field grammar, designed to FINDINGS 12: equal tier counts and equal
boundary budgets per tier pair (transition pieces are a shared inventory). Work:
`experiments/011-subjects/`. Primary grid **27 × 38** (owner decision); 20 × 25 for comparison;
any size via `make_targets.py COLSxROWS`.

## Candidate sets

| Set | A | B | C | Verdict |
|---|---|---|---|---|
| **Field, Wood and Water** | hare at dawn (vertical) | owl at dusk (radial, moon halo) | swan at midnight (horizontal) | **pick** |
| The Coast | lighthouse by day | sailboat at night | breaching white whale | lighthouse and mast are 1–2-cell verticals (long grid-aligned runs); whale drafts read as "a creature with arms" |
| Winter Tale | raven on a post | fox in snow under a night sky | snowy owl over dark pines | depends on small appendages (beak, ears, tail tip); a howling-wolf draft read as a blob |

Why: three animals, three habitats, three times of day; the sky darkens L → M → D across the set,
which *is* the value inversion. Each silhouette is one big mass plus one long feature (the hare's
V of ears, the owl's eyes and beak framed by the moon, the swan's S-neck).

## Tonal plan (field ownership)

| Tier | A hare, dawn | B owl, dusk | C swan, midnight |
|---|---|---|---|
| D | ploughed field, lone tree | **owl** and branch | night sky |
| M | **hare** | dusk sky | lake |
| L | sky, light furrow lens | moon halo, snow | **swan**, small moon, moon glints |
| S (chips on L) | starling flock | bramble in the snow | wing feathers |
| W (M + lenses) | dawn cloud bank | cloud bars | swell |

Each tier is figure once, sky once, ground or water once (a Latin square). S is always enclosed
by L, so it needs no transition pieces. The light lenses in A's furrows and C's water are one
device read twice.

Motifs (single pieces on L cells with no foreign neighbour): per picture 1 disc, 2 flowers,
3 cloud chips, 2 leaves. A: sun, blossom, clouds, blown leaves. B: crater or cloud wisp on the
moon, snowdrops and fallen leaves on the snow. C: marks on the swan read as feather detail (the
weakest reading). Capacity at 27 × 38: 99 / 124 / 125 such cells.

## How the budgets were matched

Each figure fixes two of its picture's pair budgets; one background line is free (A horizon and
tree: D-L; B moon rim and snow: M-L; C horizon and clouds: D-M). The 20 × 25 sketches were iterated
until the figure-fixed pairs agreed (the hare's horizon is mostly hidden, so B and C were reduced
in D-L and A gained a furrow lens). A seeded annealer then moves only unlocked cells within one
cell of a background line, penalizing new islands or holes, tips, strips, pinches and straight
runs over 7. Other sizes resample the balanced 20 × 25 maps, clean anomalies and re-balance.

## Budget table, 27 × 38 (`budgets.txt`)

| Item | A hare | B owl | C swan | spread |
|---|---|---|---|---|
| cells D / M / L | 318 / 366 / 293 | 318 / 366 / 293 | 312 / 373 / 292 | 6 / 7 / 1 |
| cells S / W | 49 / 39 | 49 / 39 | 49 / 39 | 0 |
| D-M edges / corners | 63 / 55 | 58 / 52 | 62 / 58 | 5 / 6 |
| D-L edges / corners | 75 / 82 | 77 / 80 | 75 / 83 | 2 / 3 |
| M-L edges / corners | 94 / 113 | 88 / 108 | 91 / 105 | 6 / 8 |
| S-D, S-M | 0 | 0 | 0 | 0 |
| tips (1-cell caps), strips, dots, pinches | 0 | 0 | 0 | 0 |
| 45° run cells D-M / D-L / M-L | 8 / 16 / 22 | 11 / 16 / 28 | 8 / 15 / 29 | 3 / 1 / 7 |
| three-tier junction cells | 10 | 12 | 18 | 8 |
| longest straight run | 7 | 7 | 7 | 0 |

All items are within about ±4 of the mean. At 20 × 25 spreads are similar, but two drawn
junction strips and one tip remain (`20x25/budgets.txt`).

## Risks

1. **Recognition in ink is unproven.** The swan reads; the hare depends on ears about 3 cells wide
   (the cat's failure mode); the owl's tufts and eyes can read as a cat face. Blind-test
   `contours-preview.png` (T1) first.
2. **Resampled pixel art:** at 27 × 38 outlines keep 2-cell steps and are 12 % taller (aspect 0.71
   vs 0.80). Native redrawing would be smoother but needs a new balance.
3. **Junction cells** (three tiers meeting, 10–18) have no tile class; spread 8.
4. **Frames differ completely**, so no shared border pool: tray or frameless cut (07).
5. Balancer edits are one-cell bumps on background lines, not designed waves.
