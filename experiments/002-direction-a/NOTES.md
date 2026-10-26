# Direction A: class spec (002)

**Built.** `classes.json` holds the 15 classes from 02-piece-classes.md, keyed by the grid codes in `docs/design/scenes-8x10.txt` so the scene file works unchanged. Each class carries its snake_case ID in `_id`. Validation passes. `render_sheets.py` draws both PNGs at a 100-unit reference cell, scaled to 64 px.

**Parameters that mattered.**
- Dabs: length 0.21 to 0.26 (diameter about 1/4 of a cell), width 0.8 times length.
- `dabs` picks tones uniformly, so tone weights are encoded by repeating palette entries.
- Transitions: sky dab base plus two blotch layers of the mass colour, coverage 0.35. One blotch layer drew 1 to 3 random blobs, so some cells were nearly all sky. Two layers keep the mass on the bias side (`right` for `/`, `left` for `\`, `bottom` for HD).
- PH: two concentric window motifs, jitter 0, for a gold rim and ink interior.

**Still wrong.**
- Transition mass is a flat fill with a halo, not dappled. It shows as a seam against any dabbed neighbour.
- Edges are not pure: S/ and F/ next to SK form forbidden seams.
- HB and HL sit mid-cell, not on the horizon. HL reads as a droplet, not a sail.
- Sprigs are scattered strokes, not radiating tufts.

**Missing capabilities.**
1. Clip a texture to a blob or polygon (dappled boundaries).
2. A boundary pinned between two corners, with ragged jitter.
3. Motif offsets (cx, cy), and a sail or triangle motif.
4. Density depends on render size. Counts scale with (size/100)^2, and the renderer passes `cell_size` in px: 5 marks per cell at 40 px, 223 at 256 px. The drawer should use a fixed reference size and let the SVG scale.
5. Minor: `motif` validates `halo_color_index` even when `halo` is 0.
