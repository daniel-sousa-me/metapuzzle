# B-06 — Aspect-ratio variants (direction B, 96 pieces)

The owner allows each image its own frame, with the same piece count. 96 = 8×12 (portrait) = 12×8 (landscape) = 16×6 (panorama).

## Which scene wants which frame

| Scene | Best frame | Why |
|---|---|---|
| A Sunflower | **8×12 portrait** | A head over stem and leaves is a tall subject. The extra rows hold the stem and leaf mass below a larger head (about 7×6). |
| B Sunset Bay | **16×6 panorama** | Horizontal bands are what a panorama is for. A long horizon, a longer glitter path, and room for several boats and a headland. |
| C Koi Pond | **12×8 landscape** | Top-down, no up/down. The diagonal path gains length, and the koi gain horizontal swimming room (fish are wider than tall). |

Three different frames also strengthen distinctness (B-04 risk 2): A and B no longer share a silhouette, and a player cannot reuse "the frame" as a template.

## Border implications

Perimeters differ:

| Frame | Border pieces | Interior pieces |
|---|---|---|
| 8×12 | 36 | 60 |
| 12×8 | 36 | 60 |
| 16×6 | 40 | 56 |

Flat-edged pieces cannot match in number across the three frames, so the strict per-side check no longer applies (`strict_border=False`). Two workable options, ranked:

1. **Flat-sided interior pieces** (IDEAS.md): give the inventory 40 flat-sided pieces. In 8×12 and 12×8, the four surplus pieces sit inside the picture as flat-to-flat seams. Direction B suits this because no class is "a top-edge class". A flat seam inside the pond or the sea is hidden by blotch-mix pieces on both sides.
2. **Rotation for edge pieces only.** Since every class allows all four rotations, edge pieces can move between sides. This pools the border by class instead of by side, so side counts need only match in total.

Neither option recreates the pale-top/green-bottom family carry-over: in the panorama the long top edge is sky, but in the landscape pond the long edges are bank and water.

## Suggested inventory (96)

Scale the 80-piece histogram by 1.2, rounding toward the panorama's needs: +3 `TE`, +2 `GT` (glitter), +2 `BL`, +2 `NT`, +1 `DT`, +1 `OC`, +1 `GD`, +2 `GB`, +2 `CR` (= 16 extra). Re-run the role-map annealer with the three frames. Corner carry-over (4 cells per pair today) remains in no-rotation mode, because a corner piece keeps its corner. It disappears only if corners may rotate, which also enables the corner-order keying in IDEAS.md.
