# Direction B (Garden Terrazzo) class spec

Source: `docs/design/alt-b/02-piece-classes.md`. Codes match `scenes-8x10-b.txt`. All 14 classes are non-directional with four rotations. The BINDER (paper/plum stipple, background false) is the last layer of every class.

## Parameter choices
- Mixes (CB, GB, GT, NT): coverage 0.30 with 3 blobs (was 0.42 and 2). Larger blobs clipped the piece edge too often. OG keeps 0.35.
- Mosaic (OC, OG): jitter 0.32 (was 0.25). At 0.25 the tesserae read as a tile grid.
- CB drops the cream blob-scatter layer, which cannot share the stipple's mask.
- DT palette has a third entry, since motif's default `halo_color_index` is 2.
- Chips: dabs (0.20 long) and tesserae (0.17 pitch) sit in the 1/6 to 1/3 range. Stipple chips follow 02 (radius 0.010 to 0.030, about 1/20 to 1/50 of a side). 01 §2 says 1/6, so the docs conflict.
- Pairs: 8th place is a tie at 10 (DK|GD, DT|TE). DK|GD kept.

## Still wrong
- Blob centres are uniform over the cell, so blobs clip the piece edge. Same-class neighbours show a hard cut, worst on GT, milder on GB, NT, OG.
- BL|GB and GT|TE read as stuck-on blobs, not a change of mix.

## Missing capabilities
- `blotch_mask` with an inset margin, as `motif` has. This would remove the same-class seams.
- One mask shared across a layer stack.
